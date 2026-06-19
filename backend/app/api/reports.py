"""Report API — generate, inspect, and resolve evidence citations."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.database.models import AnalysisOutput, AnalysisStatus, Project
from app.database.schemas import (
    AnalysisOutputRead,
    ReportCitationRead,
    ReportCitationLookupRead,
    ReportDetailRead,
)
from app.database.session import get_db_session
from app.services.report_service import (
    GeneratedReport,
    generate_final_report,
    load_report_citations,
    resolve_citation_chunk,
)
from app.services.template_service import TemplateService

router = APIRouter(prefix="/api", tags=["reports"])

_REPORT_SCRIPT_NAME = "generate_final_report"


@router.post("/projects/{project_id}/reports", response_model=ReportDetailRead, status_code=201)
async def create_report(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ReportDetailRead:
    await _verify_project_ownership(project_id, current_user.id, db)

    generated = await generate_final_report(
        project_id,
        db,
        template_service=TemplateService(db),
    )

    record = AnalysisOutput(
        project_id=project_id,
        script_name=_REPORT_SCRIPT_NAME,
        output_path=str(generated.output_path),
        status=AnalysisStatus.complete,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return _to_report_detail(record, generated)


@router.get("/reports/{report_id}", response_model=ReportDetailRead)
async def get_report(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ReportDetailRead:
    record = await _get_owned_report(report_id, current_user.id, db)
    output_path = Path(record.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk")

    report_text = output_path.read_text(encoding="utf-8")
    citations = load_report_citations(output_path)
    return ReportDetailRead(
        **AnalysisOutputRead.model_validate(record).model_dump(),
        report_text=report_text,
        citations=[_citation_to_read(citation) for citation in citations],
    )


@router.get("/reports/{report_id}/citations/{citation_id}", response_model=ReportCitationLookupRead)
async def get_report_citation(
    report_id: str,
    citation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ReportCitationLookupRead:
    record = await _get_owned_report(report_id, current_user.id, db)
    output_path = Path(record.output_path)
    citations = load_report_citations(output_path)
    citation = next((item for item in citations if item.citation_id == citation_id), None)
    if citation is None:
        raise HTTPException(status_code=404, detail="Citation not found")

    chunks = await resolve_citation_chunk(record.project_id, citation, db)
    if not chunks:
        raise HTTPException(status_code=404, detail="Evidence chunk not found")

    return ReportCitationLookupRead(
        report_id=report_id,
        citation=_citation_to_read(citation),
        chunks=chunks,
    )


async def _verify_project_ownership(project_id: str, user_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(Project.id).where(Project.id == project_id, Project.user_id == user_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")


async def _get_owned_report(report_id: str, user_id: str, db: AsyncSession) -> AnalysisOutput:
    result = await db.execute(
        select(AnalysisOutput)
        .join(Project, AnalysisOutput.project_id == Project.id)
        .where(
            AnalysisOutput.id == report_id,
            AnalysisOutput.script_name == _REPORT_SCRIPT_NAME,
            Project.user_id == user_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return record


def _citation_to_read(citation) -> ReportCitationRead:
    return ReportCitationRead(
        citation_id=citation.citation_id,
        filename=citation.filename,
        chunk_index=citation.chunk_index,
        chunk_id=citation.chunk_id,
        document_id=citation.document_id,
        label=citation.label,
    )


def _to_report_detail(record: AnalysisOutput, generated: GeneratedReport) -> ReportDetailRead:
    return ReportDetailRead(
        **AnalysisOutputRead.model_validate(record).model_dump(),
        report_text=generated.report_text,
        citations=[_citation_to_read(citation) for citation in generated.citations],
    )
