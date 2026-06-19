"""Chat streaming endpoint.

POST /api/chat/stream  →  text/event-stream (Server-Sent Events)

Each event data payload is a JSON object with a `type` field:
  text_delta  — partial assistant response text
  tool_use    — agent is calling a tool
  gap_flag    — a new DD schema gap was detected after the turn
  done        — turn complete; includes the persisted message_id
  error       — something went wrong
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.auth.dependencies import CurrentUser, get_current_user
from app.chat.orchestrator import run_turn
from app.chat.streaming import error_event
from app.database.models import Project
from app.database.schemas import ChatRequest
from app.database.session import get_db_session

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> EventSourceResponse:
    """Stream an agent response as Server-Sent Events."""
    await _verify_ownership(request.project_id, current_user.id, db)

    async def event_generator():
        try:
            async for event in run_turn(
                project_id=request.project_id,
                user_id=current_user.id,
                message=request.message,
                db=db,
            ):
                yield {"data": json.dumps(event)}
        except Exception as exc:
            yield {"data": json.dumps(error_event(str(exc)))}

    return EventSourceResponse(event_generator())


async def _verify_ownership(project_id: str, user_id: str, db: AsyncSession) -> None:
    from fastapi import HTTPException

    if (
        await db.execute(
            select(Project.id).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )
    ).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")
