"""Test the document processing pipeline end-to-end.

Usage (from backend/):
    uv run python scripts/test_pipeline.py

What it does:
  1. Inserts a test Project + Document row directly in the DB
  2. Runs process_document() on data/documents/AFSL copy.pdf
  3. Reports final status, converted path, chunk count, and a content preview
  4. Cleans up the test rows afterward
"""

import asyncio
import sys
import uuid
from pathlib import Path

# psycopg3 async requires SelectorEventLoop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Allow running from backend/ or backend/scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import settings
from app.database.models import Document, DocumentChunk, DocumentStatus, Project, ProjectStatus
from app.database.session import async_session_factory
from app.services.document_pipeline import process_document

FILE_PATH = settings.data_dir / "documents" / "AFSL copy.pdf"


async def main() -> None:
    if not FILE_PATH.exists():
        print(f"ERROR: file not found — {FILE_PATH}")
        sys.exit(1)

    project_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    # ── 1. Insert test rows ──────────────────────────────────────────────────
    async with async_session_factory() as db:
        db.add(Project(
            id=project_id,
            name="[TEST] AFSL Pipeline",
            user_id="test-pipeline-script",
            status=ProjectStatus.collecting,
        ))
        db.add(Document(
            id=document_id,
            project_id=project_id,
            filename=FILE_PATH.name,
            mime_type="application/pdf",
            status=DocumentStatus.uploading,
        ))
        await db.commit()
        print(f"Created  project_id={project_id}")
        print(f"Created  document_id={document_id}")

    # ── 2. Run pipeline ──────────────────────────────────────────────────────
    print(f"\nProcessing: {FILE_PATH}")
    print("(Docling conversion may take 30–90 s on first run while models load)\n")

    await process_document(
        document_id=document_id,
        file_path=FILE_PATH,
        mime_type="application/pdf",
        project_id=project_id,
    )

    # ── 3. Report results ────────────────────────────────────────────────────
    async with async_session_factory() as db:
        doc_result = await db.execute(select(Document).where(Document.id == document_id))
        doc = doc_result.scalar_one()

        chunks_result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        chunks = chunks_result.scalars().all()

    print("-- Result ----------------------------------------------------------")
    print(f"Status         : {doc.status.value}")
    print(f"Converted path : {doc.converted_path}")
    print(f"Chunks created : {len(chunks)}")
    if chunks:
        has_embedding = chunks[0].embedding is not None
        print(f"Has embeddings : {has_embedding}")
        print(f"\nChunk 0 preview:\n{chunks[0].content[:400]}")
    print("--------------------------------------------------------------------")

    # ── 4. Cleanup ────────────────────────────────────────────────────────────
    async with async_session_factory() as db:
        proj = await db.get(Project, project_id)
        if proj:
            await db.delete(proj)   # cascades to document + chunks
            await db.commit()
    print("\nTest rows cleaned up.")


if __name__ == "__main__":
    asyncio.run(main())
