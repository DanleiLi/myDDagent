"""Analysis API — list outputs and stream file downloads."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.models import AnalysisOutput
from app.database.schemas import AnalysisOutputRead
from app.database.session import get_db_session

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{project_id}", response_model=list[AnalysisOutputRead])
async def list_analysis_outputs(
    project_id: str,
    db: AsyncSession = Depends(get_db_session),
    _user=Depends(get_current_user),
) -> list[AnalysisOutput]:
    """List all analysis outputs for a project."""
    rows = (
        await db.execute(
            select(AnalysisOutput)
            .where(AnalysisOutput.project_id == project_id)
            .order_by(AnalysisOutput.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


@router.get("/{output_id}/download")
async def download_analysis_output(
    output_id: str,
    db: AsyncSession = Depends(get_db_session),
    _user=Depends(get_current_user),
) -> FileResponse:
    """Stream the output file for an analysis run."""
    row = (
        await db.execute(
            select(AnalysisOutput).where(AnalysisOutput.id == output_id)
        )
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Analysis output not found")

    output_path = Path(row.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found on disk")

    return FileResponse(
        path=str(output_path),
        filename=output_path.name,
        media_type="application/octet-stream",
    )
