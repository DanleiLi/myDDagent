"""Schema coverage checker and gap flag persistence.

Two strictly separated concerns:
  check_coverage  — READ-ONLY, called by agent tools.
  persist_gaps    — WRITE, called only by the orchestrator post-turn.
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DDSchema, FlagType, GapFlag
from app.services.rag_service import retrieve

logger = structlog.get_logger(__name__)

COVERAGE_THRESHOLD = 0.4


@dataclass
class GapFinding:
    field_name: str
    flag_type: str  # "gap" | "missing"
    description: str


async def check_coverage(
    project_id: str,
    db: AsyncSession,
) -> list[GapFinding]:
    """Read-only: check each required schema field for evidence in the document chunks.

    Returns a list of GapFinding. Does NOT write to the database.
    """
    result = await db.execute(
        select(DDSchema).where(DDSchema.project_id == project_id)
    )
    schema = result.scalar_one_or_none()
    if schema is None:
        logger.debug("no schema defined for project", project_id=project_id)
        return []

    findings: list[GapFinding] = []

    for field in schema.fields:
        if not field.get("required", True):
            continue

        field_name: str = field["name"]
        description: str = field.get("description", "")
        query = f"{field_name} {description}".strip()

        chunks = await retrieve(query, project_id, db, top_k=1)

        if not chunks or chunks[0].score < COVERAGE_THRESHOLD:
            findings.append(
                GapFinding(
                    field_name=field_name,
                    flag_type="gap",
                    description=(
                        f"No sufficient evidence for required field '{field_name}'"
                        + (f": {description}" if description else "")
                    ),
                )
            )

    logger.info(
        "coverage check complete",
        project_id=project_id,
        fields_checked=len(schema.fields),
        gaps_found=len(findings),
    )
    return findings


async def persist_gaps(
    findings: list[GapFinding],
    project_id: str,
    db: AsyncSession,
) -> None:
    """Write: upsert GapFlag rows.

    Skips any field that is already flagged with an unresolved gap — avoids duplicates.
    """
    added = 0
    for finding in findings:
        existing = (
            await db.execute(
                select(GapFlag).where(
                    GapFlag.project_id == project_id,
                    GapFlag.field_name == finding.field_name,
                    GapFlag.resolved.is_(False),
                )
            )
        ).scalar_one_or_none()

        if existing is None:
            db.add(
                GapFlag(
                    project_id=project_id,
                    field_name=finding.field_name,
                    flag_type=FlagType(finding.flag_type),
                    description=finding.description,
                )
            )
            added += 1

    await db.commit()
    logger.info("gaps persisted", project_id=project_id, new=added, skipped=len(findings) - added)
