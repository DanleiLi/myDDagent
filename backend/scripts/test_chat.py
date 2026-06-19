"""Stage 6 smoke test — runs one agent turn end-to-end.

Creates a temporary project with the AFSL copy.pdf already processed,
sends a single chat message, prints all SSE events, then cleans up.

Usage (from backend/):
    uv run python scripts/test_chat.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database.models import DDSchema, Document, DocumentStatus, Project, ProjectStatus
from app.database.session import async_session_factory
from app.services.document_pipeline import process_document
from app.chat.orchestrator import run_turn

FILE_PATH = settings.data_dir / "documents" / "AFSL copy.pdf"

TEST_SCHEMA = [
    {"name": "AFSL licence number", "description": "Australian Financial Services Licence number", "required": True},
    {"name": "Authorised services", "description": "Financial services the licensee is authorised to provide", "required": True},
    {"name": "AUM", "description": "Total assets under management", "required": True},
]


async def main() -> None:
    if not FILE_PATH.exists():
        print(f"ERROR: {FILE_PATH} not found — run test_pipeline.py first")
        sys.exit(1)

    project_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())

    # Setup
    async with async_session_factory() as db:
        db.add(Project(id=project_id, name="[TEST] Chat", user_id="test-chat-script", status=ProjectStatus.collecting))
        db.add(Document(id=document_id, project_id=project_id, filename=FILE_PATH.name, mime_type="application/pdf", status=DocumentStatus.uploading))
        db.add(DDSchema(project_id=project_id, fields=TEST_SCHEMA))
        await db.commit()

    print(f"Project: {project_id}\n")
    print("Processing document...")
    await process_document(document_id=document_id, file_path=FILE_PATH, mime_type="application/pdf", project_id=project_id)
    print("Pipeline complete.\n")

    # Run one agent turn
    query = "What is the AFSL licence number and what services are authorised?"
    print(f"User: {query!r}\n")
    print("-" * 60)

    events = []
    async with async_session_factory() as db:
        async for event in run_turn(project_id, "test-chat-script", query, db):
            events.append(event)
            t = event.get("type")
            if t == "text_delta":
                print(event["delta"], end="", flush=True)
            elif t == "tool_use":
                print(f"\n[TOOL] {event['tool']} {event['input']}")
            elif t == "gap_flag":
                print(f"\n[GAP] {event['field_name']}: {event['description']}")
            elif t == "done":
                print(f"\n\n[DONE] message_id={event['message_id']}")
            elif t == "error":
                print(f"\n[ERROR] {event['message']}")

    print("\n" + "-" * 60)
    print(f"Total events: {len(events)}")
    print(f"  text_delta : {sum(1 for e in events if e['type'] == 'text_delta')}")
    print(f"  tool_use   : {sum(1 for e in events if e['type'] == 'tool_use')}")
    print(f"  gap_flag   : {sum(1 for e in events if e['type'] == 'gap_flag')}")
    print(f"  done       : {sum(1 for e in events if e['type'] == 'done')}")

    # Cleanup
    async with async_session_factory() as db:
        proj = await db.get(Project, project_id)
        if proj:
            await db.delete(proj)
            await db.commit()
    print("\nTest project cleaned up.")


if __name__ == "__main__":
    asyncio.run(main())
