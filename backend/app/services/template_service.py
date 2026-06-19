"""Template service — reads/writes per-project report templates.

Templates are NEVER chunked or embedded; always read in full.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import ReportTemplate

logger = structlog.get_logger(__name__)

_DEFAULT_TEMPLATE_PATH = settings.templates_dir / "default_report_template.md"


class TemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_template(self, project_id: str) -> str:
        """Return the project's template, seeding from the default on first access."""
        row = (
            await self._db.execute(
                select(ReportTemplate).where(ReportTemplate.project_id == project_id)
            )
        ).scalar_one_or_none()

        if row:
            return row.content

        # First access — seed from default file
        content = _DEFAULT_TEMPLATE_PATH.read_text(encoding="utf-8")
        record = ReportTemplate(project_id=project_id, content=content)
        self._db.add(record)
        await self._db.commit()
        logger.info("seeded default template", project_id=project_id)
        return content

    async def update_template(self, project_id: str, content: str) -> None:
        """Persist updated template to DB and mirror to disk."""
        row = (
            await self._db.execute(
                select(ReportTemplate).where(ReportTemplate.project_id == project_id)
            )
        ).scalar_one_or_none()

        if row:
            row.content = content
            row.updated_at = datetime.now(timezone.utc)
        else:
            row = ReportTemplate(project_id=project_id, content=content)
            self._db.add(row)

        await self._db.commit()

        # Mirror to disk for external access
        file_path = settings.templates_dir / f"{project_id}_template.md"
        file_path.write_text(content, encoding="utf-8")
        logger.info("updated template", project_id=project_id, path=str(file_path))
