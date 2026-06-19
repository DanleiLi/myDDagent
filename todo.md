# Dossier — Due Diligence Agent: Step-by-Step Build Plan

## Project Overview

Build "Dossier" — a three-pane due diligence web app where an AI agent RAGs over uploaded documents, flags data gaps against a user-defined schema, and produces formatted reports. The agent is strictly read-only (no DB writes); only the orchestrator persists data.

**Tech stack:** FastAPI + Python 3.12 + pydantic-ai (backend) · React + TypeScript + Vite (frontend) · Supabase PostgreSQL + pgvector + Storage · Anthropic claude-sonnet-4-6 + OpenAI text-embedding-3-small

**Working directory:** `c:\Users\Sara\Downloads\agent-project`

---

## Stage 1 — Backend Foundation

**Goal:** Get a running FastAPI server with configuration, dependencies, and a health check endpoint.

**Steps:**

1. **Extend `backend/pyproject.toml`**
   Add `hatchling` as build backend (enables editable imports). Add missing dependencies:
   ```toml
   "pymupdf>=1.23",
   "python-docx>=1.1",
   "pandas>=2.2",
   "openpyxl>=3.1",
   "aiofiles>=23.2",
   "langchain-text-splitters>=0.3",
   "anthropic>=0.50",
   ```
   Add dev dependencies: `pytest`, `pytest-asyncio`, `ruff`, `httpx`.
   Run: `cd backend && uv sync`

2. **Create `backend/app/__init__.py`** (empty)

3. **Create `backend/app/config.py`**
   Pydantic `BaseSettings` reading from `backend/.env`. Fields:
   - `supabase_url`, `supabase_anon_key`, `supabase_service_key`
   - `database_url` (pooler — for app), `database_url_direct` (session URL — for Alembic only)
   - `openai_api_key`, `anthropic_api_key`
   - `embedding_model: str = "text-embedding-3-small"`, `embedding_dims: int = 1536`
   - `data_dir: Path`, `scripts_dir: Path`, `outputs_dir: Path`, `templates_dir: Path`
   - `allowed_origins: list[str] = ["http://localhost:5173"]`
   
   Add `DATABASE_URL_DIRECT` to `backend/.env` — derive from Supabase project ref:
   `postgresql://postgres.{ref}:{password}@db.{ref}.supabase.co:5432/postgres`

4. **Create `backend/app/main.py`**
   FastAPI app with `lifespan` context manager, CORS middleware using `settings.allowed_origins`, and `GET /health` route returning `{"status": "ok"}`. No business logic yet.

5. **Retire `backend/app.py`** (old Flask file — rename to `backend/app_legacy.py` so it's not deleted but not imported)

**Success criteria:**
- `cd backend && uv run uvicorn app.main:app --reload` starts without errors
- `curl http://localhost:8000/health` returns `{"status": "ok"}`
- `uv run python -c "from app.config import settings; print(settings.supabase_url)"` prints the Supabase URL

---

## Stage 2 — Database Schema & Migrations

**Goal:** All 8 Supabase tables exist, pgvector and FTS indexes are created, and RLS policies are set.

**Steps:**

1. **Create `backend/app/database/__init__.py`** (empty)

2. **Create `backend/app/database/models.py`**
   SQLAlchemy 2.0 `DeclarativeBase` with 8 mapped tables:

   | Table | Key columns |
   |---|---|
   | `projects` | `id uuid PK`, `name text`, `status enum(collecting/reviewing/complete)`, `user_id text`, `created_at` |
   | `documents` | `id uuid PK`, `project_id uuid FK`, `filename`, `storage_path`, `mime_type`, `status enum(uploading/chunking/embedded/ready/error)` |
   | `document_chunks` | `id uuid PK`, `document_id FK`, `project_id FK`, `content text`, `embedding VECTOR(1536)`, `metadata jsonb`, `chunk_index int` |
   | `messages` | `id uuid PK`, `project_id FK`, `role enum(user/assistant)`, `content text`, `tool_calls jsonb`, `created_at` |
   | `dd_schema` | `id uuid PK`, `project_id FK UNIQUE`, `fields jsonb` |
   | `gap_flags` | `id uuid PK`, `project_id FK`, `field_name text`, `flag_type enum(gap/conflict/missing)`, `description text`, `resolved bool DEFAULT false` |
   | `portfolio_profiles` | `id uuid PK`, `project_id FK`, `portfolio_id text`, `portfolio_name text`, `investment_manager_name text`, `menu enum(off-the-shelf/customised)`, `series_name text`, `inception_date datetime`, `asset_class text` |
   | `report_templates` | `id uuid PK`, `project_id FK UNIQUE`, `content text`, `updated_at` |

   UUID PKs use `server_default=text("gen_random_uuid()")`. `embedding` uses `pgvector.sqlalchemy.VECTOR(1536)`. Status fields use Python `enum.Enum`.

3. **Create `backend/app/database/session.py`**
   `create_async_engine` with `settings.database_url` (scheme: `postgresql+psycopg://`). Expose `async_session_factory` and `get_db_session()` FastAPI dependency.

4. **Create `backend/app/database/supabase.py`**
   Two lazy singletons: `get_anon_client()` (anon key) and `get_admin_client()` (service key). Admin client used for Storage; never expose service key to frontend.

5. **Set up Alembic**
   - Create `backend/alembic.ini` (standard config, `sqlalchemy.url` left blank)
   - Create `backend/alembic/env.py` — imports `target_metadata` from `app.database.models`, uses `settings.database_url_direct` (direct, not pooler)
   - Create `backend/alembic/versions/001_initial_schema.py`:
     - `CREATE EXTENSION IF NOT EXISTS vector`
     - `CREATE EXTENSION IF NOT EXISTS pg_trgm`
     - `CREATE TABLE` for all 8 tables
     - Add `search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED` on `document_chunks`
     - `CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)`
     - `CREATE INDEX ... USING gin (search_vector)`
     - Enable RLS on all user-data tables
     - RLS policy on `projects`: `user_id = auth.uid()::text`
     - RLS policy on all other tables: `project_id IN (SELECT id FROM projects WHERE user_id = auth.uid()::text)`

6. **Run migration:**
   `cd backend && uv run alembic upgrade head`

7. **Create Supabase Storage bucket:**
   Supabase dashboard → Storage → New bucket → name: `documents` → Private

**Success criteria:**
- `uv run alembic upgrade head` completes without errors
- Supabase dashboard → Table Editor shows all 8 tables
- pgvector extension visible under Database → Extensions
- `documents` storage bucket exists and is private
- `uv run python -c "from app.database.models import Project; print('models ok')"` runs without error

---

## Stage 3 — Auth & Project Management API

**Goal:** Users can authenticate via Supabase JWT and create, list, and manage DD projects through the API.

**Steps:**

1. **Create `backend/app/auth/__init__.py`** (empty)

2. **Create `backend/app/auth/dependencies.py`**
   `get_current_user` FastAPI dependency:
   - Extracts `Authorization: Bearer <token>` from request headers
   - Calls `anon_client.auth.get_user(token)` to verify
   - Returns `CurrentUser(id: str, email: str)` dataclass
   - Raises `HTTPException(401)` on missing or invalid token

3. **Create `backend/app/database/schemas.py`**
   Pydantic v2 models for all API request/response shapes. Pattern: `{Model}Base` → `{Model}Create` (POST body) → `{Model}Read` (response adds `id`, `created_at`). Include `ProjectCreate`, `ProjectRead`, `DocumentRead`, `MessageRead`, `GapFlagRead`, `AnalysisOutputRead`.

4. **Create `backend/app/api/__init__.py`** (empty)

5. **Create `backend/app/api/projects.py`**
   Router prefix `/api/projects`:
   - `GET /` — list projects for `current_user.id`, ordered by `created_at DESC`
   - `POST /` — create project, set `user_id = current_user.id`
   - `GET /{project_id}` — get single (verify ownership)
   - `PATCH /{project_id}` — update name or status
   - `DELETE /{project_id}` — delete (cascade to related tables)
   
   All routes: `async def`, inject `current_user = Depends(get_current_user)` and `db: AsyncSession = Depends(get_db_session)`. Always filter by `user_id`.

6. **Create `backend/app/api/schema.py`**
   Router prefix `/api/schema`:
   - `GET /{project_id}` — get DD schema for project
   - `POST /{project_id}` — create/replace schema (`fields: list[{name, description, required, expected_type}]`)
   - Also mirrors schema to `data/schemas/{project_id}.json` for script access

7. **Register routers in `backend/app/main.py`** — include projects and schema routers.

8. **Set up Supabase Auth:**
   Supabase dashboard → Authentication → Providers → Email → Enabled. Disable "Confirm email" for development.

**Success criteria:**
- Sign up a test user via Supabase dashboard → get JWT token
- `POST /api/projects` with `Authorization: Bearer <token>` creates a project, returns `ProjectRead` JSON
- `GET /api/projects` lists the created project
- `POST /api/projects` without token returns `401`
- `GET /api/projects` with wrong user's token returns empty list (RLS isolation)

---

## Stage 4 — Document Upload & Processing Pipeline

**Goal:** Users can upload documents via the API; they are cleaned, chunked, embedded, and stored in pgvector ready for retrieval.

**Steps:**

1. **Create data directories:**
   Ensure `data/documents/`, `data/outputs/`, `data/schemas/`, `data/templates/` exist.

2. **Create `backend/app/services/__init__.py`** (empty)

3. **Create `backend/app/services/document_pipeline.py`**
   Async background task `process_document(document_id, file_path, mime_type, project_id, db)`:
   - Status → `chunking`
   - Extract text (all blocking, run via `asyncio.to_thread`):
     - PDF → `fitz.open(file_path)` → `page.get_text()` per page
     - CSV/Excel → `pandas.read_csv/read_excel` → `.to_string()`
     - DOCX → `python-docx Document` → join `paragraph.text`
   - Clean: strip repeated whitespace, remove lines shorter than 20 chars at page boundaries (header/footer heuristic)
   - Chunk: `RecursiveCharacterTextSplitter(chunk_size=800, overlap=100)`
   - Embed: async OpenAI client, batch ≤100 chunks per call, model = `settings.embedding_model`
   - Bulk insert `DocumentChunk` rows via SQLAlchemy
   - Upload raw binary to Supabase Storage bucket `documents` at path `{project_id}/{document_id}/{filename}` using admin client
   - Status → `ready`; on any exception → status → `error` + log with structlog

4. **Create `backend/app/api/documents.py`**
   Router prefix `/api/documents`:
   - `POST /upload` — accepts `project_id: UUID` (form field) + `file: UploadFile`. Saves temp file to `data/documents/{project_id}/`. Creates `Document` DB record (status `uploading`). Schedules `BackgroundTasks.add_task(process_document, ...)`. Returns `DocumentRead`.
   - `GET /{project_id}` — list documents for project
   - `GET /{document_id}/status` — returns current status (for frontend polling)
   - `GET /{document_id}/preview` — returns first 2000 chars of extracted text

5. **Register documents router** in `backend/app/main.py`.

**Success criteria:**
- `POST /api/documents/upload` with a PDF and valid project_id returns `DocumentRead` with status `uploading`
- After ~10–30 seconds: `GET /api/documents/{document_id}/status` returns `ready`
- Supabase dashboard → Table Editor → `document_chunks` shows rows with non-null embeddings
- Supabase Storage → `documents` bucket shows the uploaded file
- `GET /api/documents/{document_id}/preview` returns readable extracted text

---

## Stage 5 — RAG, Schema Coverage & Gap Detection

**Goal:** The system can retrieve relevant document chunks for a query using hybrid search, and detect data gaps against the DD schema.

**Steps:**

1. **Create `backend/app/services/rag_service.py`**
   `retrieve(query, project_id, top_k=5) -> list[RetrievedChunk]`:
   - Embed the query with OpenAI
   - **Semantic search:** pgvector cosine similarity (`1 - cosine_distance`), top_k×2 results
   - **Full-text search:** `tsvector @@ plainto_tsquery(query)`, ranked by `ts_rank_cd`, top_k×2 results
   - **RRF fusion in Python:** `score = 1/(60 + rank)`, sum scores for shared chunks, return top_k by combined score
   
   `RetrievedChunk` dataclass: `chunk_id`, `document_id`, `filename`, `content`, `score`, `chunk_index`.

2. **Create `backend/app/services/gap_detector.py`** — two separate methods, no mixing:
   ```python
   # READ-ONLY — called by agent tool only
   async def check_coverage(project_id, db) -> list[GapFinding]:
       # For each required field in schema, retrieve top-1 chunk
       # If score < COVERAGE_THRESHOLD (0.4): add GapFinding
       # Returns findings list — NO DB writes

   # WRITE — called only by orchestrator post-turn
   async def persist_gaps(findings, project_id, db) -> None:
       # Upsert GapFlag rows (skip if already flagged and unresolved)
   ```
   `GapFinding` is a plain dataclass (not an ORM model) — the agent operates on these, never on DB models directly.

3. **Create `backend/app/api/gaps.py`** (for frontend to read/update flags)
   Router prefix `/api/gaps`:
   - `GET /{project_id}` — list unresolved + resolved gap flags
   - `PATCH /{gap_id}/resolve` — mark a flag as resolved

4. **Register gaps router** in `backend/app/main.py`.

5. **Write a manual test script** `backend/scripts/test_rag.py` (dev-only, not part of the app):
   Hard-code a `project_id` with uploaded documents and print retrieval results for 3 test queries.

**Success criteria:**
- `test_rag.py` returns 5 chunks for a test query, with scores > 0.3
- RRF results visually look more relevant than semantic-only results
- `check_coverage()` returns at least one `GapFinding` when a required schema field has no evidence
- `persist_gaps()` writes `GapFlag` rows to the DB; calling it twice for same field does not create duplicates
- `GET /api/gaps/{project_id}` returns the written flags

---

## Stage 6 — Agent & Streaming Chat

**Goal:** The chat endpoint streams agent responses that use RAG tools to answer questions about uploaded documents, with all DB persistence handled by the orchestrator (not the agent tools).

**Steps:**

1. **Create `backend/app/assistant/__init__.py`** (empty)

2. **Create `backend/app/assistant/deps.py`**
   ```python
   @dataclass
   class DossierAgentDeps:
       project_id: UUID
       user_id: str
       db: AsyncSession
       rag: RagService
       gap_detector: GapDetector
       analysis_service: AnalysisService   # stub for now, complete in Stage 7
       template_service: TemplateService   # stub for now, complete in Stage 7
   ```

3. **Create `backend/app/assistant/instructions.md`**
   System prompt contract:
   - Always call `retrieve_context` before making factual claims
   - Call `check_schema_coverage` when asked about completeness or gaps
   - Never fabricate numbers or facts not found in retrieved context; cite source
   - Mark insufficient evidence as `[INSUFFICIENT DATA]`
   - When asked for the final report: call `generate_final_report` (Stage 7)
   - **You are read-only.** You retrieve and generate. You do not create, update, or delete records.

4. **Create `backend/app/assistant/tools.py`** — register tools on the agent:
   - `retrieve_context(ctx, query: str, top_k: int = 5) -> str` — calls `ctx.deps.rag.retrieve()`, formats chunks as numbered source passages with filename
   - `check_schema_coverage(ctx) -> str` — calls `ctx.deps.gap_detector.check_coverage()` (read-only), returns JSON gap summary. Does NOT write to DB.
   - `draft_report_section(ctx, section_name: str) -> str` — retrieves 10 relevant chunks, constructs prompt, returns drafted text for one section. No DB writes.

5. **Create `backend/app/assistant/agent.py`**
   ```python
   from pydantic_ai import Agent
   from .deps import DossierAgentDeps
   from . import tools

   agent = Agent[DossierAgentDeps, str](
       model="anthropic:claude-sonnet-4-6",
       system_prompt=Path("assistant/instructions.md").read_text(),
       retries=2,
   )
   ```
   Module-level singleton.

6. **Create `backend/app/chat/__init__.py`** (empty)

7. **Create `backend/app/chat/streaming.py`** — SSE event formatters:
   - `text_delta_event(delta: str) -> dict`
   - `tool_use_event(tool_name: str, tool_input: dict) -> dict`
   - `gap_flag_event(gap: GapFinding) -> dict`
   - `done_event(message_id: UUID) -> dict`
   - `error_event(message: str) -> dict`

8. **Create `backend/app/chat/orchestrator.py`**
   `run_turn(project_id, user_id, message, db) -> AsyncIterator[SSEEvent]`:
   - **Orchestrator writes user message to DB** (not the agent)
   - Builds `DossierAgentDeps`
   - Streams agent via `agent.iter(message, deps=deps)`, yielding SSE events per node type
   - On `End` node: **orchestrator writes assistant message to DB**; **orchestrator calls `gap_detector.persist_gaps()`** as background task
   - Yields `done_event`

9. **Add to `backend/app/database/schemas.py`:**
   `ChatRequest(project_id: UUID, message: str)` and `SSEEvent` discriminated union.

10. **Create `backend/app/api/chat.py`**
    ```python
    @router.post("/stream")
    async def stream_chat(request: ChatRequest, ...) -> EventSourceResponse:
        async def event_generator():
            async for event in orchestrator.run_turn(...):
                yield {"data": json.dumps(event)}
        return EventSourceResponse(event_generator())
    ```

11. **Register chat router** in `backend/app/main.py`.

**Success criteria:**
- `POST /api/chat/stream` with a message returns an SSE stream (Content-Type: `text/event-stream`)
- Streaming response contains `text_delta` events that form a coherent answer
- When asking a factual question about an uploaded document, the response cites the source
- When asking "what data is missing?", a `tool_use` event appears for `check_schema_coverage` followed by a text response listing gaps
- After the turn, `messages` table has a `user` row and an `assistant` row
- Agent tool functions do NOT write any DB rows directly (verify by checking no `db.add()` / `db.commit()` calls in `tools.py`)

---

## Stage 7 — Analysis Scripts & Template-Based Report Generation

**Goal:** The agent can run quantitative analysis scripts and produce a formatted DD report using a per-project template injected in full into the context window.

**Steps:**

1. **Create `data/templates/default_report_template.md`**
   Default DD report template with 8 sections:
   ```markdown
   # Due Diligence Report — [Investment Manager Name]

   ## 1. Executive Summary
   <!-- Summarise the investment manager, strategy, and overall recommendation in 2-3 paragraphs -->

   ## 2. Investment Manager Overview
   <!-- Firm history, AUM, team structure, key personnel -->

   ## 3. Investment Strategy & Philosophy
   <!-- Strategy description, asset classes, investment process, benchmark -->

   ## 4. Fees and Costs
   <!-- Management fees, performance fees, indirect costs, total effective fee -->

   ## 5. Risk Management
   <!-- Risk framework, concentration limits, drawdown controls -->

   ## 6. Governance & Compliance
   <!-- AFSL status, regulatory history, compliance framework -->

   ## 7. Portfolio Holdings Analysis
   <!-- Current holdings, asset allocation, concentration analysis -->

   ## 8. Recommendation
   <!-- Approved / Conditional Approval / Not Approved with rationale -->
   ```

2. **Create `backend/app/services/template_service.py`**
   - `get_template(project_id, db) -> str` — reads from `report_templates` table; seeds from `default_report_template.md` on first access
   - `update_template(project_id, content, db) -> None` — writes to DB + mirrors to `data/templates/{project_id}_template.md`
   - Template is NEVER chunked or embedded — always read in full

3. **Create `backend/app/api/template.py`**
   Router prefix `/api/template`:
   - `GET /{project_id}` — returns current template content (or default if not yet customised)
   - `PUT /{project_id}` — accepts `{"content": "..."}`, saves via `template_service.update_template()`

4. **Add `generate_final_report` tool to `backend/app/assistant/tools.py`**
   ```python
   @agent.tool
   async def generate_final_report(ctx: RunContext[DossierAgentDeps]) -> str:
       # 1. Read full template — never chunk this
       template = await ctx.deps.template_service.get_template(ctx.deps.project_id)
       # 2. Retrieve broad evidence (top_k=20)
       chunks = await ctx.deps.rag.retrieve("due diligence overview", ctx.deps.project_id, top_k=20)
       # 3. Build prompt injecting template + evidence in same context window
       prompt = f"Template:\n{template}\n\nEvidence:\n{format_chunks(chunks)}\n\nProduce the report."
       # 4. Single LLM call
       response = await llm_client.complete(prompt)
       # 5. Write output file — the ONE allowed write for this tool
       output_path = settings.outputs_dir / f"{ctx.deps.project_id}_report.md"
       output_path.write_text(response.text)
       return response.text
       # Orchestrator creates AnalysisOutput DB record after tool returns
   ```

5. **Create `backend/app/services/analysis_service.py`**
   - `enqueue(script_name, params, project_id) -> str` — validates script name against allowlist, returns a `job_id` string. Actual execution and DB record creation done by orchestrator.
   - `run_script(script_name, params, project_id, output_path) -> None` — runs script via `asyncio.create_subprocess_exec` with `--params`, `--output`, `--project` args.

6. **Add `run_analysis_script` tool to `backend/app/assistant/tools.py`**
   - Calls `analysis_service.enqueue()`, returns job reference to orchestrator
   - Orchestrator creates `AnalysisOutput` DB record and launches `run_script()` as background task

7. **Create `backend/app/api/analysis.py`**
   Router prefix `/api/analysis`:
   - `GET /{project_id}` — list analysis outputs
   - `GET /{output_id}/download` — stream the output file

8. **Create analysis scripts in `data/scripts/`** — each follows the standard CLI interface (`--params`, `--output`, `--project`):
   - `fee_analysis.py` — reads fee data from chunks/CSV, calculates effective fees after GST/RITC, writes Excel with Fee Summary + Benchmark Comparison sheets
   - `portfolio_metrics.py` — asset class allocation, concentration ratios, writes Excel with openpyxl charts
   - `risk_analysis.py` — concentration risk flags, volatility proxies, writes CSV + Excel detail

9. **Update `instructions.md`** to add: when user asks to generate final report, call `generate_final_report`.

10. **Register template and analysis routers** in `backend/app/main.py`.

**Success criteria:**
- `GET /api/template/{project_id}` returns the default template for a new project
- `PUT /api/template/{project_id}` saves a modified template; subsequent GET returns the modified version
- New project gets its own fresh copy of the default (modifying one project's template does not affect others)
- Asking agent "generate the final report" triggers `generate_final_report` tool, streams the report text, and creates a file in `data/outputs/`
- The generated report contains section headings matching the template structure
- `GET /api/analysis/{project_id}` lists the output; `GET /api/analysis/{output_id}/download` downloads the `.md` file
- `fee_analysis.py` run standalone (`python fee_analysis.py --params '{}' --output test.xlsx --project abc`) produces a valid Excel file

---

## Stage 8 — Frontend Scaffold & Layout

**Goal:** A working three-pane UI shell with OpenAI colour theme renders correctly at `localhost:5173`. No live data yet — use placeholder content.

**Steps:**

1. **Scaffold Vite project** in `frontend/`:
   ```bash
   pnpm create vite . --template react-ts
   pnpm install
   pnpm add react-router-dom @supabase/supabase-js react-markdown remark-gfm
   pnpm add -D tailwindcss @tailwindcss/vite
   pnpm dlx shadcn@latest init
   ```
   shadcn/ui components needed: `Button`, `Badge`, `Checkbox`, `ScrollArea`, `Separator`, `Dialog`.

2. **Create `frontend/src/styles/globals.css`** with OpenAI colour variables:
   ```css
   :root {
     --bg-primary: #212121;
     --bg-sidebar: #171717;
     --bg-user-bubble: #2f2f2f;
     --accent: #10a37f;
     --text-primary: #ececec;
     --text-secondary: #8e8ea0;
     --font-sans: 'Inter', sans-serif;
   }
   ```
   Extend Tailwind config with these as colour tokens.

3. **Create `frontend/src/lib/env.ts`**
   Validates `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` at load time. Throws if missing.

4. **Create `frontend/src/lib/supabase.ts`**
   `createClient(env.supabaseUrl, env.supabaseAnonKey)`. Export `getAccessToken()` helper.

5. **Create `frontend/src/lib/http.ts`**
   Fetch wrapper that prepends `VITE_API_BASE_URL`, injects `Authorization: Bearer ${token}`, converts non-2xx to typed errors.

6. **Create `frontend/src/components/layout/AppShell.tsx`**
   Three-column CSS grid: `260px 1fr 340px`, full viewport height, all columns fixed height with internal scroll. Render placeholder `<div>` for each pane with label text.

7. **Create `frontend/src/components/layout/Sidebar.tsx`**
   Left pane. Hardcoded placeholder project list for now. "New Project" button. Active item highlighted with `--accent` left border.

8. **Create `frontend/src/components/layout/RightPanel.tsx`**
   Right pane split: top 60% (gap panel placeholder) + bottom 40% (upload panel placeholder).

9. **Update `frontend/.env`:**
   ```
   VITE_API_BASE_URL=http://localhost:8000
   VITE_SUPABASE_URL=<from existing frontend/.env>
   VITE_SUPABASE_ANON_KEY=<from existing frontend/.env>
   ```

10. **Create `frontend/src/pages/WorkspacePage.tsx`** — renders `AppShell` with sidebar and right panel.
    Create `frontend/src/App.tsx` with React Router: route `/` → `WorkspacePage`.

**Success criteria:**
- `pnpm dev` starts without errors
- App loads at `http://localhost:5173`
- Three-pane layout is visible: sidebar (dark `#171717`), main area (`#212121`), right panel (`#212121`)
- Background colours match OpenAI theme exactly
- Sidebar shows placeholder project items with correct font and colours
- `pnpm tsc --noEmit` passes with no type errors

---

## Stage 9 — Frontend: Chat, Documents & Project Management

**Goal:** Users can authenticate, create projects, upload documents, and chat with the agent — all live, streaming from the real backend.

**Steps:**

1. **Create `frontend/src/lib/api.ts`** — product-level API calls:
   - `listProjects()`, `createProject(name)`, `deleteProject(id)`
   - `listDocuments(projectId)`, `uploadDocument(projectId, file)`, `getDocumentStatus(documentId)`
   - `listGapFlags(projectId)`, `resolveGapFlag(gapId)`
   - `listAnalysisOutputs(projectId)`, `downloadAnalysisOutput(outputId)`
   - `getTemplate(projectId)`, `updateTemplate(projectId, content)`

2. **Create `frontend/src/hooks/useProjects.ts`**
   Fetches `listProjects()`, exposes `{ projects, createProject, loading }`.

3. **Wire `Sidebar.tsx`** to `useProjects` — real project list with name, `created_at`, status `Badge` (Collecting=blue / Reviewing=yellow / Complete=green). Click sets `activeProjectId` in page state.

4. **Create `frontend/src/hooks/useChat.ts`**
   SSE streaming hook using `fetch()` + `ReadableStream` (POST, not `EventSource`):
   - Sends `POST /api/chat/stream`
   - Reads response body line by line, parses `data: {...}\n\n` SSE lines
   - Dispatches by `type`: `text_delta` → append to last assistant message; `tool_use` → set `activeToolCall`; `gap_flag` → append to local gap state; `done` → finalize
   - Exposes `{ messages, sendMessage, isStreaming, activeToolCall }`

5. **Create chat components:**
   - `ChatPane.tsx` — container with `MessageList` + `ChatInput`
   - `MessageList.tsx` — `ScrollArea`, auto-scrolls to bottom on new message
   - `MessageBubble.tsx` — user: `bg-user-bubble` rounded pill; assistant: plain on dark with `MarkdownRenderer`
   - `MarkdownRenderer.tsx` — `react-markdown` + `remark-gfm`, custom `code` renderer (copy button), `a` (new tab)
   - `ToolIndicator.tsx` — spinner chip between messages: `retrieve_context`→"Searching documents", `run_analysis_script`→"Running analysis", `check_schema_coverage`→"Checking coverage", `generate_final_report`→"Generating report"
   - `ChatInput.tsx` — textarea, Enter submits, Shift+Enter newline, disabled while streaming

6. **Create document upload components:**
   - `UploadZone.tsx` — HTML5 drag events + file `<input>`. On drop/select: calls `api.uploadDocument()`, then polls `getDocumentStatus()` every 2s until `ready` or `error`
   - `DocumentCard.tsx` — filename, upload time, status pill matching document status enum colours

7. **Wire `RightPanel.tsx` bottom** to show `UploadZone` + `DocumentCard[]` list from `useDocuments(activeProjectId)`.

8. **Create `frontend/src/pages/AuthPage.tsx`** — email/password sign-in and sign-up using `supabase.auth.signInWithPassword` / `signUp`. On success, route to `/`. Add auth guard: redirect to `/auth` if no session.

**Success criteria:**
- Sign up a new user → redirected to workspace
- Create a new project → appears in sidebar with "Collecting" badge
- Upload a PDF → `DocumentCard` shows uploading → chunking → embedded → ready progression in real-time
- Type a question about the document in the chat input → streaming response appears word-by-word
- `ToolIndicator` chip "Searching documents" briefly appears during retrieval
- Switching to a different project → chat history is empty (no cross-conversation memory)
- Refreshing the page → previous messages for the active project are loaded from DB

---

## Stage 10 — Frontend: Gap Panel & Template Editor

**Goal:** Gap flags appear live in the right panel as the agent detects them; users can view, resolve, and edit the report template.

**Steps:**

1. **Create `frontend/src/hooks/useGapFlags.ts`**
   Fetches `listGapFlags(projectId)`. Polls every 5 seconds or uses Supabase Realtime subscription on `gap_flags` table for live updates. Exposes `{ flags, unresolvedCount, resolveFlag }`.

2. **Create gap components:**
   - `GapPanel.tsx` — right pane top 60%. Header: "Follow-up Questions" + unresolved count badge. `ScrollArea` with `GapItem[]`. Empty state: "No gaps detected yet".
   - `GapItem.tsx` — `Checkbox` + gap description text. Checked = `api.resolveGapFlag()` + optimistic update. Resolved items: dimmed and struck-through.

3. **Wire `RightPanel.tsx` top** to `GapPanel` using `useGapFlags(activeProjectId)`.

4. **Create `TemplateEditor.tsx`**
   Triggered by "Edit Template" button in the chat header. Opens as a modal `Dialog`:
   - Left half: Markdown `<textarea>` (monospace font, full height), pre-loaded from `api.getTemplate(projectId)`
   - Right half: Live preview using `MarkdownRenderer`
   - "Save" button: calls `api.updateTemplate(projectId, content)`, closes modal
   - "Reset to Default" button: replaces content with the default template text

5. **Add "Edit Template" button** to `ChatPane` header (top right). Opens `TemplateEditor`.

6. **Wire analysis output downloads** — after agent calls `generate_final_report`, a download card appears in the document section. Uses `api.downloadAnalysisOutput(outputId)`.

7. **Wiring final checks:**
   - Verify "Generate the final report" flow end-to-end: chat message → `generate_final_report` tool indicator → streaming report text → download card appears
   - Verify gap resolution persists across page refresh
   - Verify editing template in one project does not affect another project's template

**Success criteria:**
- After asking agent "what data is missing?", gap flags appear in the right panel within 5 seconds
- Checking a gap flag marks it resolved; unchecked items remain visible
- "Edit Template" button opens the modal with the current template pre-loaded
- Editing the template and saving persists the change (verified by reopening the editor)
- Asking agent "generate the final report" produces a report that follows the saved template structure, downloads correctly
- A new project starts with the default template (not a previously edited one)

---

## Final Folder Structure

```
agent-project/
├── backend/
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/001_initial_schema.py
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── projects.py
│   │   │   ├── documents.py
│   │   │   ├── chat.py
│   │   │   ├── analysis.py
│   │   │   ├── schema.py
│   │   │   ├── template.py
│   │   │   └── gaps.py
│   │   ├── auth/dependencies.py
│   │   ├── assistant/
│   │   │   ├── agent.py
│   │   │   ├── deps.py
│   │   │   ├── tools.py
│   │   │   └── instructions.md
│   │   ├── services/
│   │   │   ├── document_pipeline.py
│   │   │   ├── rag_service.py
│   │   │   ├── analysis_service.py
│   │   │   ├── gap_detector.py
│   │   │   └── template_service.py
│   │   ├── chat/
│   │   │   ├── orchestrator.py
│   │   │   └── streaming.py
│   │   └── database/
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── session.py
│   │       └── supabase.py
│   └── pyproject.toml
│
├── frontend/
│   └── src/
│       ├── lib/{env,supabase,http,api}.ts
│       ├── hooks/{useProjects,useDocuments,useChat,useGapFlags}.ts
│       ├── components/
│       │   ├── layout/{AppShell,Sidebar,RightPanel}.tsx
│       │   ├── chat/{ChatPane,MessageList,MessageBubble,MarkdownRenderer,ToolIndicator,ChatInput}.tsx
│       │   ├── documents/{UploadZone,DocumentCard}.tsx
│       │   ├── gaps/{GapPanel,GapItem}.tsx
│       │   └── template/TemplateEditor.tsx
│       └── pages/{AuthPage,WorkspacePage}.tsx
│
└── data/
    ├── documents/
    ├── outputs/
    ├── schemas/
    ├── templates/default_report_template.md
    └── scripts/
        ├── fee_analysis.py
        ├── portfolio_metrics.py
        └── risk_analysis.py
```

---

## Key Architectural Constraints (carry through all stages)

1. **Agent is read-only.** `tools.py` has zero `db.add()` / `db.commit()` calls. The only write permissions are: writing `data/outputs/*.md` report files.
2. **Orchestrator owns all DB persistence.** Message writes, gap flag writes, analysis output records — all in `orchestrator.py` post-turn.
3. **Template is never chunked.** `get_template()` always returns the full string. It is injected directly into the LLM prompt via `generate_final_report`, not retrieved via RAG.
4. **No cross-conversation memory.** Each project is a fully isolated context. RAG queries always filter by `project_id`. There is no shared memory table.
5. **`config.py` is the only file that reads `.env`.** Never use `os.getenv()` elsewhere.
6. **Alembic uses `database_url_direct`.** The pooler URL cannot be used for schema migrations.
