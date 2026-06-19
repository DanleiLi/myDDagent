"""End-to-end RAG + gap detection test.

Uploads AFSL copy.pdf into a temporary project, then tests:
  1. Hybrid retrieval for 3 queries (semantic + FTS + RRF)
  2. Schema coverage check  (check_coverage)
  3. Gap persistence        (persist_gaps, idempotency)

Usage (from backend/):
    uv run python scripts/test_rag.py

The temporary project is deleted at the end.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import settings
from app.database.models import Document, DocumentStatus, GapFlag, Project, ProjectStatus
from app.database.session import async_session_factory
from app.services.document_pipeline import process_document
from app.services.gap_detector import check_coverage, persist_gaps
from app.services.rag_service import retrieve

FILE_PATH = settings.data_dir / "documents" / "AFSL copy.pdf"

TEST_QUERIES = [
    "AFSL licence number and authorised financial services",
    "investment management and financial products authorised",
    "compliance obligations and regulatory requirements",
]

# Minimal DD schema with a mix of covered and likely-missing fields
TEST_SCHEMA_FIELDS = [
    {"name": "AFSL licence number", "description": "Australian Financial Services Licence number", "required": True},
    {"name": "Authorised services", "description": "List of financial services the licensee is authorised to provide", "required": True},
    {"name": "AUM", "description": "Total assets under management", "required": True},
    {"name": "Performance track record", "description": "Historical returns and benchmark comparison", "required": True},
]


async def main() -> None:
    if not FILE_PATH.exists():
        print(f"ERROR: {FILE_PATH} not found")
        sys.exit(1)

    project_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    # ── Setup: insert test project + document ─────────────────────────────────
    async with async_session_factory() as db:
        from app.database.models import DDSchema
        db.add(Project(id=project_id, name="[TEST] RAG", user_id="test-rag-script", status=ProjectStatus.collecting))
        db.add(Document(id=document_id, project_id=project_id, filename=FILE_PATH.name, mime_type="application/pdf", status=DocumentStatus.uploading))
        db.add(DDSchema(project_id=project_id, fields=TEST_SCHEMA_FIELDS))
        await db.commit()

    print(f"Project: {project_id}\n")

    # ── Run document pipeline ─────────────────────────────────────────────────
    print("Running pipeline (Docling models cached after first run)...")
    await process_document(document_id=document_id, file_path=FILE_PATH, mime_type="application/pdf", project_id=project_id)
    print("Pipeline complete.\n")

    async with async_session_factory() as db:

        # ── Test 1: Retrieval ─────────────────────────────────────────────────
        print("=" * 65)
        print("TEST 1 — Hybrid retrieval (semantic + FTS + RRF)")
        print("=" * 65)
        all_scores: list[float] = []

        for query in TEST_QUERIES:
            print(f"\nQuery: {query!r}")
            chunks = await retrieve(query, project_id, db, top_k=5)
            for i, c in enumerate(chunks):
                print(f"  [{i+1}] score={c.score:.4f}  file={c.filename}  chunk={c.chunk_index}")
                print(f"       {c.content[:120].strip()!r}")
                all_scores.append(c.score)

        above_threshold = sum(1 for s in all_scores if s > 0.3)
        print(f"\nResult: {above_threshold}/{len(all_scores)} chunks scored > 0.3")

        # ── Test 2: Coverage check ────────────────────────────────────────────
        print("\n" + "=" * 65)
        print("TEST 2 — Schema coverage (check_coverage)")
        print("=" * 65)
        findings = await check_coverage(project_id, db)
        if findings:
            for f in findings:
                print(f"  GAP  [{f.flag_type}] {f.field_name}")
                print(f"       {f.description}")
        else:
            print("  All required fields covered.")
        print(f"\nResult: {len(findings)} gap(s) detected out of {len(TEST_SCHEMA_FIELDS)} fields")

        # ── Test 3: Persist + idempotency ─────────────────────────────────────
        print("\n" + "=" * 65)
        print("TEST 3 — persist_gaps (idempotency)")
        print("=" * 65)

        await persist_gaps(findings, project_id, db)
        count_after_first = (
            await db.execute(select(GapFlag).where(GapFlag.project_id == project_id))
        ).scalars().all()

        await persist_gaps(findings, project_id, db)  # second call — should not duplicate
        count_after_second = (
            await db.execute(select(GapFlag).where(GapFlag.project_id == project_id))
        ).scalars().all()

        print(f"  After 1st persist_gaps call : {len(count_after_first)} row(s)")
        print(f"  After 2nd persist_gaps call : {len(count_after_second)} row(s)")
        idempotent = len(count_after_first) == len(count_after_second)
        print(f"  Idempotent: {'YES' if idempotent else 'NO (BUG)'}")

    # ── Cleanup ────────────────────────────────────────────────────────────────
    async with async_session_factory() as db:
        proj = await db.get(Project, project_id)
        if proj:
            await db.delete(proj)
            await db.commit()
    print("\nTest project cleaned up.")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("SUMMARY")
    print("=" * 65)
    print(f"  Retrieval scores > 0.3 : {above_threshold}/{len(all_scores)}")
    print(f"  Gaps detected          : {len(findings)}/{len(TEST_SCHEMA_FIELDS)} fields")
    print(f"  Idempotency            : {'PASS' if idempotent else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
