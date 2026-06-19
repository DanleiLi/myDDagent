"""Async document processing pipeline: convert → chunk → embed → store."""

import asyncio
from pathlib import Path

import structlog
from openai import AsyncOpenAI

from app.config import settings
from app.database.models import Document, DocumentChunk, DocumentStatus
from app.database.session import async_session_factory
from app.database.supabase import get_admin_client

logger = structlog.get_logger(__name__)

_openai: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai


# ── Docling singleton ────────────────────────────────────────────────────────

_converter: "DocumentConverter | None" = None


def _get_converter() -> "DocumentConverter":
    global _converter
    if _converter is None:
        from docling.document_converter import DocumentConverter
        _converter = DocumentConverter()
    return _converter


# ── Conversion ───────────────────────────────────────────────────────────────


def _convert_to_markdown(file_path: Path) -> str:
    converter = _get_converter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()


# ── Chunking ─────────────────────────────────────────────────────────────────


def _chunk_text(text: str) -> list[str]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    return splitter.split_text(text)


# ── Embedding ─────────────────────────────────────────────────────────────────


async def _embed_chunks(chunks: list[str]) -> list[list[float]]:
    client = _get_openai()
    batch_size = 100
    all_embeddings: list[list[float]] = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        response = await client.embeddings.create(
            input=batch,
            model=settings.embedding_model,
        )
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings


# ── Pipeline ──────────────────────────────────────────────────────────────────


async def process_document(
    document_id: str,
    file_path: Path,
    mime_type: str,
    project_id: str,
) -> None:
    """Background task: convert, chunk, embed and store a document."""
    log = logger.bind(document_id=document_id, project_id=project_id)

    async with async_session_factory() as db:
        try:
            # ── 1. Mark as chunking ──────────────────────────────────────────
            from sqlalchemy import select

            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one()
            document.status = DocumentStatus.chunking
            await db.commit()

            # ── 2. Convert to Markdown (blocking — docling loads ML models) ──
            log.info("converting to markdown")
            markdown_text = await asyncio.to_thread(_convert_to_markdown, file_path)

            # ── 3. Save converted Markdown to disk ───────────────────────────
            log.info("saving markdown")
            converted_dir = settings.converted_dir / project_id / document_id
            await asyncio.to_thread(lambda: converted_dir.mkdir(parents=True, exist_ok=True))
            md_path = converted_dir / (file_path.stem + ".md")
            await asyncio.to_thread(md_path.write_text, markdown_text, "utf-8")
            document.converted_path = str(md_path)
            await db.commit()

            # ── 4. Chunk ─────────────────────────────────────────────────────
            log.info("chunking")
            chunks = await asyncio.to_thread(_chunk_text, markdown_text)
            if not chunks:
                log.warning("no chunks produced")

            # ── 5. Embed ─────────────────────────────────────────────────────
            log.info("embedding", num_chunks=len(chunks))
            document.status = DocumentStatus.embedded
            await db.commit()

            embeddings = await _embed_chunks(chunks)

            # ── 6. Bulk insert chunks ────────────────────────────────────────
            log.info("inserting chunks", num_chunks=len(chunks))
            chunk_rows = [
                DocumentChunk(
                    document_id=document_id,
                    project_id=project_id,
                    content=chunk,
                    embedding=embedding,
                    metadata_={"filename": file_path.name, "chunk_index": idx},
                    chunk_index=idx,
                )
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]
            db.add_all(chunk_rows)
            await db.commit()

            # ── 7. Upload raw file to Supabase Storage (best-effort) ─────────
            log.info("uploading to storage")
            storage_path = f"{project_id}/{document_id}/{file_path.name}"
            try:
                file_bytes = await asyncio.to_thread(file_path.read_bytes)
                admin = get_admin_client()
                await asyncio.to_thread(
                    admin.storage.from_("documents").upload,
                    storage_path,
                    file_bytes,
                    {"content-type": mime_type},
                )
                document.storage_path = storage_path
            except Exception:
                log.warning("storage upload failed — document will still be ready for RAG")

            # ── 8. Mark ready ────────────────────────────────────────────────
            document.status = DocumentStatus.ready
            await db.commit()
            log.info("document ready")

        except Exception:
            log.exception("document processing failed")
            try:
                await db.rollback()
                result = await db.execute(
                    select(Document).where(Document.id == document_id)
                )
                document = result.scalar_one_or_none()
                if document:
                    document.status = DocumentStatus.error
                    await db.commit()
            except Exception:
                log.exception("failed to set error status")
