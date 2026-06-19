# PRD & Spec - DD Agent Web App (3-Step Review Flow)

## 1. Context

The existing frontend is a React + Vite + TypeScript app using Tailwind, shadcn/Radix components, and Lucide icons. It talks to a FastAPI backend through the `http` wrapper in `frontend/src/lib/http.ts`, with Supabase auth handled in `frontend/src/lib/supabase.ts`.

The current experience is chat-driven: the workspace centers on conversation, the right panel shows documents and gap flags, and there is already a working template editor. This spec redesigns the post-login experience into a guided 3-step flow: Upload -> Data Quality Review -> Report + Evidence.

Goal: give analysts a low-friction workflow that keeps the current agent and document pipeline intact, while making the review and report process easier to follow and audit.

## 2. Out of scope

- Login / auth screens stay as-is.
- Underlying agent logic, prompts, and document pipeline do not change.
- Do not remove or disable the existing template editor. It remains available as part of the workspace.
- Settings remains a placeholder unless the team later defines actual settings behavior.

## 3. Information architecture

```text
App shell
├── Left nav (collapsible, hover or click to expand)
│   ├── Reports (active)
│   ├── Templates (opens existing template editor / template workflow)
│   └── Settings (placeholder, disabled if not implemented)
├── Report list panel (visible when Reports is active)
│   └── Project list: name, created date, status, sort controls, new/delete
└── Main workspace
    ├── Step 1: Upload
    ├── Step 2: Data quality review
    └── Step 3: Report + evidence panel
```

## 4. API gap analysis

| Capability | Status | Existing reference | Action needed |
|---|---|---|---|
| Upload | Built | `backend/app/api/documents.py:36` | Reuse as-is |
| Document processing status | Built | `backend/app/api/documents.py:111` | Frontend should poll this endpoint until `ready` or `error` |
| Gap flags list | Built | `backend/app/api/gaps.py:13` | Reuse as-is |
| Mark gap resolved | Built | `backend/app/api/gaps.py:30` | Reuse existing one-way resolve endpoint |
| Project list | Built | `backend/app/api/projects.py:14` | Reuse as-is |
| Project create/delete | Built | `backend/app/api/projects.py:27`, `:67` | Reuse as-is |
| Report generation | Built, chat-driven | `backend/app/assistant/tools.py:107` | Add standalone endpoint if the UI needs a direct button |
| Report output retrieval | Built | `backend/app/api/analysis.py:20`, `:37` | Reuse for list/download |
| Evidence chunks | Internal only | `backend/app/services/document_pipeline.py:1`, `backend/app/services/rag_service.py:1` | Add a public citation lookup endpoint if clickable evidence is required |
| Chat | Built (SSE) | `backend/app/api/chat.py:1` | Reuse and relocate in the UI |

## 5. Backend changes required

### 5.1 Document processing status

**Current state:** the backend already exposes `GET /api/documents/{document_id}/status`, and the document pipeline transitions through `uploading -> chunking -> embedded -> ready` or `error`.

**Spec:**
- Use the existing status endpoint for Step 1.
- Poll every 2 seconds per document until the status becomes `ready` or `error`.
- Do not add SSE for this flow unless the team wants to optimize later.
- Keep the existing status values exactly as defined by the backend.

### 5.2 Data quality flags

**Current state:** `GET /api/gaps/{project_id}` returns the current flags, and `PATCH /api/gaps/{gap_id}/resolve` marks a flag as resolved.

**Spec:**
- Build the Step 2 summary cards in the frontend from existing data.
- Use `GET /api/schema/{project_id}` to count required schema fields for `criteria_checked`.
- Compute `passed` and `needs_review` client-side from the schema and unresolved flags.
- Group flags by `flag_type` (`gap`, `conflict`, `missing`), not by severity, because severity is not part of the current model.
- The checkbox interaction should be one-way: checking a flag marks it resolved. If unresolve is needed later, that requires a new backend endpoint.

### 5.3 Report generation

**Current state:** the report is generated inside the chat tool flow via `generate_final_report`, which writes a Markdown file and results in an `AnalysisOutput` record.

**Spec:**
- Add `POST /api/projects/{project_id}/reports` as a wrapper around the same report-generation service used by `generate_final_report`.
- Keep the output as a Markdown artifact on disk, backed by an `AnalysisOutput` record.
- Return enough metadata for the UI to show generation state and navigate to the report.
- Do not assume structured report sections exist today.
- If the team wants inline rendering from an API response, add a small report-detail or preview endpoint that returns the generated Markdown text.

### 5.4 Evidence lookup

**Current state:** `DocumentChunk` rows exist and are used internally for retrieval, but there is no public API for evidence-by-citation.

**Spec:**
- If clickable evidence is required in Step 3, add a citation map during report generation.
- Add `GET /api/reports/{report_id}/citations/{citation_id}` to return the matching chunks.
- If citation IDs are not available yet, Step 3 should degrade gracefully and still render the report output plus chat.

## 6. Frontend spec

### 6.1 Tech constraints

- Use the existing stack: React + Vite + TypeScript, Tailwind, shadcn/Radix, Lucide.
- Keep using the current `http` wrapper and Supabase bearer token flow.
- Do not introduce React Query unless the repo already adopts it later; follow the existing custom hook pattern.
- Reuse the existing `useChat.ts` SSE hook for chat.

### 6.2 Left nav

- Collapsible sidebar, 52px collapsed / 140px expanded, hover or click to expand.
- Three items:
  - Reports, active and functional.
  - Templates, opens the existing template editor or template workflow.
  - Settings, placeholder/disabled until implemented.
- Use shadcn `Tooltip` for disabled or explanatory states.

### 6.3 Project list panel

- Load projects from `GET /api/projects`.
- Default sort is `created_at` descending.
- Client-side sort controls: Name / Created / Status.
- New project uses the existing create flow: prompt for a name, then `POST /api/projects` with `{ name }`.
- Delete uses the existing `DELETE /api/projects/{project_id}` endpoint with confirmation.

### 6.4 Step indicator

- Show a pill-style stepper in the workspace header: `1. Upload - 2. Data quality - 3. Report`.
- Step 2 unlocks when all uploaded documents are `ready`.
- Step 3 unlocks when a report output exists for the project.
- Use a clear active-state badge for the current step.

### 6.5 Step 1 - Upload

- Provide a drag-and-drop zone plus click-to-browse upload.
- Upload uses the existing document upload endpoint.
- After upload, show each file with:
  - filename
  - status badge
  - simple indeterminate progress state while processing
- Status values should match the backend: `uploading`, `chunking`, `embedded`, `ready`, `error`.
- Use polling against `GET /api/documents/{document_id}/status`.
- The continue button stays disabled until every file is `ready`.
- If a file errors, show a retry action that re-uploads the file.

### 6.6 Step 2 - Data quality review

- Show three metric cards:
  - Criteria checked
  - Passed
  - Needs review
- Derive these counts from the schema and unresolved gap flags.
- Group flags into collapsible sections by `flag_type`:
  - gap
  - conflict
  - missing
- Each flag row includes:
  - checkbox or resolved state control
  - field name
  - description
  - optional extra detail if present
- Resolving a flag calls `PATCH /api/gaps/{gap_id}/resolve`.
- The `Generate report` button triggers the report-generation endpoint and then moves the user to Step 3.

### 6.7 Step 3 - Report + evidence

- Use a two-column layout:
  - report content on the left
  - evidence / chat panel on the right
- Render the report output as Markdown from the generated analysis artifact.
- If citation metadata exists, make highlighted facts clickable and load matching evidence chunks into the panel.
- If citation metadata does not exist yet, the panel should show an empty state rather than failing.
- Keep chat available in the right panel using the existing `useChat.ts` hook scoped to `project_id`.
- Export/download should use the existing analysis download endpoint.

### 6.8 State management

Use the repo's current hook-first pattern:

- `useProjects()` for project list and create/delete flows.
- `useDocuments(projectId)` for upload and document status polling.
- `useGaps(projectId)` for schema and flag data, plus resolve mutation.
- `useReport(projectId)` for report creation, status, and selection of the current report.
- `useCitation(reportId, citationId)` for evidence lookup if citation endpoints are added.

## 7. Open questions

1. Step 3 render the report directly from a Markdown artifact.
2. Citation IDs generated at report-write time.
3. Should the Templates entry open the current modal editor.

## 8. Suggested build order

1. Rebuild the app shell and stepper around the existing project, document, and gap APIs.
2. Implement Step 1 polling and the document upload view.
3. Implement Step 2 summary and resolved-state handling using the current gap endpoints.
4. Add the standalone report-generation endpoint if the UI needs a direct button.
5. Add citation lookup only if Step 3 needs clickable evidence.
6. Move chat into the Step 3 side panel and wire export/download to the existing analysis endpoint.

## 9. Validation and success criteria

For every change, do the implementation first, then run a validation step immediately after it. The validation step should be a focused test or check that confirms the specific change works before moving to the next item.

### 9.1 Rebuild the app shell and stepper

- [ ] App shell shows the new 3-step workflow layout.
- [ ] Left nav remains usable and matches the new IA.
- [ ] Stepper reflects the active step correctly.
- [ ] Validation run confirms the shell renders without layout regressions.

### 9.2 Step 1 document processing status

- [ ] Uploaded documents appear in the file list.
- [ ] Status updates from `uploading` to `chunking`, `embedded`, `ready`, or `error`.
- [ ] Continue button stays disabled until all documents are `ready`.
- [ ] Validation run confirms the document status polling or refresh flow works end to end.

### 9.3 Step 2 data quality review

- [ ] Criteria checked, passed, and needs review counts are displayed.
- [ ] Flags are grouped by current `flag_type`.
- [ ] Resolving a flag updates the UI and persists through refresh.
- [ ] Validation run confirms the gap list and resolve flow work against the backend.

### 9.4 Report generation

- [ ] The report generation action creates or updates the current report output.
- [ ] The UI can navigate to the report state after generation.
- [ ] Validation run confirms the report endpoint or existing chat-driven flow completes successfully.

### 9.5 Evidence lookup

- [ ] Report content can expose clickable evidence where citation metadata exists.
- [ ] Matching chunks load into the evidence panel when a citation is selected.
- [ ] Validation run confirms the citation lookup endpoint or fallback behavior works as expected.

### 9.6 Step 3 chat and export

- [ ] Chat is visible in the Step 3 side panel.
- [ ] Existing SSE chat flow still streams correctly.
- [ ] Export/download uses the current analysis download endpoint.
- [ ] Validation run confirms chat and download still work after the layout move.
