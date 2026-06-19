"""Turn orchestrator — the ONLY place that writes to the database.

Sequence per turn:
  1. Persist user message.
  2. Load prior message history (pydantic-ai format).
  3. Run agent to completion (tools execute via deps.event_queue).
  4. Drain tool-use events from queue → yield as SSE events.
     • analysis_enqueued: create AnalysisOutput record + launch background task.
     • report_generated: create AnalysisOutput record (complete).
     • all other events: yield to caller as SSE.
  5. Yield full agent response as a single text_delta event.
  6. Persist assistant message + pydantic-ai history JSON.
  7. Run gap detection and persist any new findings.
  8. Emit gap_flag events for new findings.
  9. Emit done event.

Note on streaming: pydantic-ai's run_stream() only yields text from the CURRENT
model response, not from subsequent responses after tool calls. Since our agent
always calls tools before answering, we use agent.run() to get the full result
and then emit it as a single text_delta. Tool events are emitted in-order via
the queue (populated during agent.run() execution).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import structlog
from pydantic_ai.messages import ModelMessagesTypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.agent import agent
from app.assistant.deps import DossierAgentDeps
from app.chat.streaming import done_event, error_event, gap_flag_event, text_delta_event
from app.database.models import AnalysisOutput, AnalysisStatus, Message, MessageRole
from app.database.session import async_session_factory
from app.services.analysis_service import AnalysisService
from app.services.gap_detector import check_coverage, persist_gaps
from app.services.template_service import TemplateService

logger = structlog.get_logger(__name__)


async def run_turn(
    project_id: str,
    user_id: str,
    message: str,
    db: AsyncSession,
) -> AsyncIterator[dict]:
    """Async generator that yields SSE event dicts for a single conversation turn."""

    # 1. Persist user message
    user_msg = Message(project_id=project_id, role=MessageRole.user, content=message)
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # 2. Load pydantic-ai message history from previous assistant turns
    prev_messages = await _load_history(project_id, db)

    # 3. Build deps with a fresh event queue and services
    event_queue: asyncio.Queue[dict] = asyncio.Queue()
    deps = DossierAgentDeps(
        project_id=project_id,
        user_id=user_id,
        db=db,
        event_queue=event_queue,
        template_service=TemplateService(db),
        analysis_service=AnalysisService(),
    )

    # 4. Run agent to completion (tools fire events into the queue during execution)
    try:
        result = await agent.run(
            message,
            deps=deps,
            message_history=prev_messages,
        )
        full_text: str = result.output
        new_msgs_json = ModelMessagesTypeAdapter.dump_json(result.new_messages()).decode()
    except Exception as exc:
        logger.exception("agent run failed", project_id=project_id, error=str(exc))
        yield error_event(str(exc))
        return

    # 5. Drain event queue — handle special events, yield the rest as SSE
    background_jobs: list[tuple[str, dict]] = []  # list of (output_id, job_meta)
    while not event_queue.empty():
        evt = event_queue.get_nowait()

        if evt["type"] == "analysis_enqueued":
            # Create AnalysisOutput record; launch script as background task
            record = AnalysisOutput(
                project_id=project_id,
                script_name=evt["script_name"],
                output_path=evt["output_path"],
                status=AnalysisStatus.running,
            )
            db.add(record)
            await db.commit()
            await db.refresh(record)
            background_jobs.append((record.id, evt))

        elif evt["type"] == "report_generated":
            # Create AnalysisOutput record for the generated report
            record = AnalysisOutput(
                project_id=project_id,
                script_name="generate_final_report",
                output_path=evt["output_path"],
                status=AnalysisStatus.complete,
            )
            db.add(record)
            await db.commit()

        else:
            yield evt  # tool_use, gap_flag, etc.

    # 6. Emit the full response text
    yield text_delta_event(full_text)

    # 7. Persist assistant message
    asst_msg = Message(
        project_id=project_id,
        role=MessageRole.assistant,
        content=full_text,
        tool_calls={"pydantic_ai_json": new_msgs_json},
    )
    db.add(asst_msg)
    await db.commit()
    await db.refresh(asst_msg)

    # 8. Gap detection + persistence (orchestrator-only write)
    try:
        findings = await check_coverage(project_id, db)
        if findings:
            await persist_gaps(findings, project_id, db)
            for gap in findings:
                yield gap_flag_event(gap)
    except Exception as exc:
        logger.warning("gap detection failed", project_id=project_id, error=str(exc))

    # 9. Done
    yield done_event(asst_msg.id)

    # 10. Launch background analysis tasks (after yielding done so the response is already sent)
    analysis_svc = AnalysisService()
    for output_id, job in background_jobs:
        asyncio.create_task(
            _run_analysis_job(
                output_id=output_id,
                script_name=job["script_name"],
                params=job["params"],
                project_id=project_id,
                output_path=Path(job["output_path"]),
                analysis_svc=analysis_svc,
            )
        )


async def _run_analysis_job(
    output_id: str,
    script_name: str,
    params: dict,
    project_id: str,
    output_path: Path,
    analysis_svc: AnalysisService,
) -> None:
    """Background task: run the analysis script and update the AnalysisOutput status."""
    async with async_session_factory() as db:
        try:
            await analysis_svc.run_script(script_name, params, project_id, output_path)
            status = AnalysisStatus.complete
        except Exception as exc:
            logger.error(
                "analysis job failed",
                output_id=output_id,
                script=script_name,
                error=str(exc),
            )
            status = AnalysisStatus.error

        # Update status in DB
        row = (await db.execute(select(AnalysisOutput).where(AnalysisOutput.id == output_id))).scalar_one_or_none()
        if row:
            row.status = status
            await db.commit()


async def _load_history(project_id: str, db: AsyncSession):
    """Return all prior pydantic-ai messages for the project, oldest first."""
    rows = (
        await db.execute(
            select(Message)
            .where(
                Message.project_id == project_id,
                Message.role == MessageRole.assistant,
            )
            .order_by(Message.created_at)
        )
    ).scalars().all()

    history = []
    for row in rows:
        if row.tool_calls and "pydantic_ai_json" in row.tool_calls:
            try:
                msgs = ModelMessagesTypeAdapter.validate_json(row.tool_calls["pydantic_ai_json"])
                history.extend(msgs)
            except Exception as exc:
                logger.warning("could not deserialise message history", row_id=row.id, error=str(exc))
    return history
