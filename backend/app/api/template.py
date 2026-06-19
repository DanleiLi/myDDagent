"""Template API — GET and PUT per-project report templates."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.session import get_db_session
from app.services.template_service import TemplateService

router = APIRouter(prefix="/api/template", tags=["template"])


class TemplateRead(BaseModel):
    project_id: str
    content: str


class TemplateUpdate(BaseModel):
    content: str


@router.get("/{project_id}", response_model=TemplateRead)
async def get_template(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    _user=Depends(get_current_user),
) -> TemplateRead:
    """Return the current template for the project (seeds from default on first access)."""
    service = TemplateService(db)
    content = await service.get_template(project_id)
    return TemplateRead(project_id=project_id, content=content)


@router.put("/{project_id}", response_model=TemplateRead)
async def update_template(
    project_id: str,
    body: TemplateUpdate,
    db: AsyncSession = Depends(get_db_session),
    _user=Depends(get_current_user),
) -> TemplateRead:
    """Save a modified template for the project."""
    service = TemplateService(db)
    await service.update_template(project_id, body.content)
    return TemplateRead(project_id=project_id, content=body.content)
