from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.database.models import GapFlag, Project
from app.database.schemas import GapFlagRead
from app.database.session import get_db_session

router = APIRouter(prefix="/api/gaps", tags=["gaps"])


@router.get("/{project_id}", response_model=list[GapFlagRead])
async def list_gap_flags(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[GapFlagRead]:
    await _verify_ownership(project_id, current_user.id, db)
    rows = (
        await db.execute(
            select(GapFlag)
            .where(GapFlag.project_id == project_id)
            .order_by(GapFlag.resolved, GapFlag.field_name)
        )
    ).scalars().all()
    return [GapFlagRead.model_validate(r) for r in rows]


@router.patch("/{gap_id}/resolve", response_model=GapFlagRead)
async def resolve_gap_flag(
    gap_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> GapFlagRead:
    flag = await db.get(GapFlag, gap_id)
    if flag is None:
        raise HTTPException(status_code=404, detail="Gap flag not found")
    await _verify_ownership(str(flag.project_id), current_user.id, db)
    flag.resolved = True
    await db.commit()
    await db.refresh(flag)
    return GapFlagRead.model_validate(flag)


async def _verify_ownership(project_id: str, user_id: str, db: AsyncSession) -> None:
    if (
        await db.execute(
            select(Project.id).where(
                Project.id == project_id,
                Project.user_id == user_id,
            )
        )
    ).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")
