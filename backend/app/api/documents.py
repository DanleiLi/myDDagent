"""Document upload and management endpoints."""

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.config import settings
from app.database.models import Document, DocumentChunk, DocumentStatus, Project
from app.database.schemas import DocumentRead
from app.database.session import get_db_session
from app.services.document_pipeline import process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


async def _get_owned_document(
    document_id: str, user_id: str, db: AsyncSession
) -> Document:
    """Fetch a document, verifying the caller owns the parent project."""
    result = await db.execute(
        select(Document)
        .join(Project, Document.project_id == Project.id)
        .where(Document.id == document_id, Project.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/upload", response_model=DocumentRead, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    project_id: str = Form(...),
    file: UploadFile = ...,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    # Verify the project belongs to the current user
    result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Save uploaded file to disk
    dest_dir = settings.data_dir / "documents" / project_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    original_name = file.filename or "upload"
    # Deduplicate filenames by prepending a short UUID segment
    unique_name = f"{uuid.uuid4().hex[:8]}_{original_name}"
    dest_path = dest_dir / unique_name

    content = await file.read()
    dest_path.write_bytes(content)

    mime_type = file.content_type or "application/octet-stream"

    # Create DB record
    document = Document(
        project_id=project_id,
        filename=original_name,
        mime_type=mime_type,
        status=DocumentStatus.uploading,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Schedule processing as a background task
    background_tasks.add_task(
        process_document,
        document.id,
        dest_path,
        mime_type,
        project_id,
    )

    return DocumentRead.model_validate(document)


@router.get("/{project_id}", response_model=list[DocumentRead])
async def list_documents(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[DocumentRead]:
    # Verify ownership
    proj_result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == current_user.id
        )
    )
    if proj_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Document).where(Document.project_id == project_id)
    )
    return [DocumentRead.model_validate(d) for d in result.scalars().all()]


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    doc = await _get_owned_document(document_id, current_user.id, db)
    return {"document_id": doc.id, "status": doc.status}


@router.get("/{document_id}/preview")
async def preview_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    doc = await _get_owned_document(document_id, current_user.id, db)
    if doc.status not in {DocumentStatus.embedded, DocumentStatus.ready}:
        raise HTTPException(
            status_code=409,
            detail=f"Document is not yet processed (status: {doc.status})",
        )

    # Pull first chunks ordered by index and concatenate up to 2000 chars
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .limit(10)
    )
    chunks = result.scalars().all()
    text = " ".join(c.content for c in chunks)[:2000]
    return {"document_id": doc.id, "filename": doc.filename, "preview": text}
