"""Dependency container passed to every pydantic-ai tool call."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.services.analysis_service import AnalysisService
    from app.services.template_service import TemplateService


@dataclass
class DossierAgentDeps:
    project_id: str
    user_id: str
    db: AsyncSession
    # Tools push SSE events here; orchestrator drains the queue while streaming text.
    event_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    # Populated by orchestrator before agent.run()
    template_service: TemplateService | None = field(default=None)
    analysis_service: AnalysisService | None = field(default=None)
