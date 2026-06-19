"""Shared report generation and report artifact helpers."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import structlog
from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import Document, DocumentChunk
from app.services.rag_service import RetrievedChunk, retrieve
from app.services.template_service import TemplateService

logger = structlog.get_logger(__name__)

_anthropic: AsyncAnthropic | None = None

_CITATION_RE = re.compile(
    r"\[Source:\s*(?P<filename>[^,\]]+),\s*chunk\s+(?P<chunk_index>\d+)(?:-(?P<chunk_index_end>\d+))?\]",
    re.IGNORECASE,
)


def _get_anthropic() -> AsyncAnthropic:
    global _anthropic
    if _anthropic is None:
        _anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic


@dataclass(slots=True)
class ReportCitation:
    citation_id: str
    filename: str
    chunk_index: int
    chunk_index_end: int | None
    chunk_id: str | None
    document_id: str | None
    label: str


@dataclass(slots=True)
class GeneratedReport:
    output_path: Path
    report_text: str
    citations: list[ReportCitation]


def _format_chunks(chunks: list[RetrievedChunk]) -> str:
    lines: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        source_label = f"{chunk.filename}, chunk {chunk.chunk_index}"
        if chunk.chunk_index_end is not None and chunk.chunk_index_end != chunk.chunk_index:
            source_label = f"{chunk.filename}, chunk {chunk.chunk_index}-{chunk.chunk_index_end}"
        if chunk.expanded:
            source_label += " (expanded context)"
        lines.append(
            f"[{i}] Source: {source_label} (score {chunk.score:.3f})\n{chunk.content}"
        )
    return "\n\n".join(lines)


def _build_citations(
    report_text: str,
    chunks: list[RetrievedChunk],
) -> list[ReportCitation]:
    chunk_lookup: dict[tuple[str, int], RetrievedChunk] = {
        (chunk.filename.lower(), chunk.chunk_index): chunk for chunk in chunks
    }
    citations: list[ReportCitation] = []
    seen: set[tuple[str, int]] = set()

    for match in _CITATION_RE.finditer(report_text):
        filename = match.group("filename").strip()
        chunk_index = int(match.group("chunk_index"))
        chunk_index_end = match.group("chunk_index_end")
        chunk_index_end_int = int(chunk_index_end) if chunk_index_end else None
        key = (filename.lower(), chunk_index)
        if key in seen:
            continue
        seen.add(key)

        chunk = chunk_lookup.get(key)
        citations.append(
            ReportCitation(
                citation_id=f"citation-{len(citations) + 1}",
                filename=filename,
                chunk_index=chunk_index,
                chunk_index_end=chunk_index_end_int,
                chunk_id=chunk.chunk_id if chunk else None,
                document_id=chunk.document_id if chunk else None,
                label=(
                    f"Source: {filename}, chunk {chunk_index}"
                    + (f"-{chunk_index_end_int}" if chunk_index_end_int else "")
                ),
            )
        )

    return citations


def _write_citation_sidecar(output_path: Path, citations: list[ReportCitation]) -> None:
    sidecar_path = output_path.with_suffix(".citations.json")
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_path": str(output_path),
        "citations": [
            {
                "citation_id": citation.citation_id,
                "filename": citation.filename,
                "chunk_index": citation.chunk_index,
                "chunk_index_end": citation.chunk_index_end,
                "chunk_id": citation.chunk_id,
                "document_id": citation.document_id,
                "label": citation.label,
            }
            for citation in citations
        ],
    }
    sidecar_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_citation_sidecar(output_path: Path) -> list[ReportCitation]:
    sidecar_path = output_path.with_suffix(".citations.json")
    if not sidecar_path.exists():
        return []

    try:
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("could not read report citation sidecar", path=str(sidecar_path))
        return []

    citations: list[ReportCitation] = []
    for item in payload.get("citations", []):
        chunk_index_end = item.get("chunk_index_end")
        citations.append(
            ReportCitation(
                citation_id=str(item.get("citation_id", "")),
                filename=str(item.get("filename", "")),
                chunk_index=int(item.get("chunk_index", 0)),
                chunk_index_end=int(chunk_index_end) if chunk_index_end is not None else None,
                chunk_id=item.get("chunk_id"),
                document_id=item.get("document_id"),
                label=str(item.get("label", "")),
            )
        )
    return citations


async def generate_final_report(
    project_id: str,
    db: AsyncSession,
    template_service: TemplateService | None = None,
) -> GeneratedReport:
    """Generate the project report and persist the markdown + citation sidecar."""
    if template_service is None:
        template_service = TemplateService(db)

    template = await template_service.get_template(project_id)

    chunks = await retrieve(
        "due diligence overview investment manager fees risk governance",
        project_id,
        db,
        top_k=20,
    )
    evidence_text = _format_chunks(chunks) if chunks else "No documents uploaded for this project."

    prompt = (
        "You are a due diligence report writer. "
        "Using ONLY the evidence passages below, complete every section of the template. "
        "Where evidence is insufficient, write [INSUFFICIENT DATA] and explain what is missing. "
        "Cite sources after each factual claim using the format [Source: filename, chunk N].\n\n"
        f"Template:\n{template}\n\n"
        f"Evidence:\n{evidence_text}\n\n"
        "Produce the completed report in Markdown."
    )

    response = await _get_anthropic().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    report_text: str = response.content[0].text  # type: ignore[union-attr]

    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    report_run_id = uuid.uuid4().hex
    output_path = settings.outputs_dir / f"{project_id}_report_{report_run_id}.md"
    output_path.write_text(report_text, encoding="utf-8")

    citations = _build_citations(report_text, chunks)
    _write_citation_sidecar(output_path, citations)

    logger.info(
        "generated final report",
        project_id=project_id,
        path=str(output_path),
        citations=len(citations),
    )

    return GeneratedReport(
        output_path=output_path,
        report_text=report_text,
        citations=citations,
    )


def load_report_citations(output_path: Path) -> list[ReportCitation]:
    return _read_citation_sidecar(output_path)


async def resolve_citation_chunk(
    project_id: str,
    citation: ReportCitation,
    db: AsyncSession,
) -> list[dict]:
    """Resolve a citation to the matching chunk rows."""
    if citation.chunk_id:
        if citation.chunk_index_end is not None and citation.chunk_index_end != citation.chunk_index:
            query = select(DocumentChunk).where(
                DocumentChunk.project_id == project_id,
                DocumentChunk.document_id == citation.document_id,
                DocumentChunk.chunk_index >= citation.chunk_index,
                DocumentChunk.chunk_index <= citation.chunk_index_end,
            )
            result = await db.execute(query)
            rows = result.scalars().all()
        else:
            result = await db.execute(
                select(DocumentChunk).where(
                    DocumentChunk.id == citation.chunk_id,
                    DocumentChunk.project_id == project_id,
                )
            )
            rows = result.scalars().all()
    else:
        result = await db.execute(
            select(DocumentChunk, Document.filename)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                DocumentChunk.project_id == project_id,
                DocumentChunk.chunk_index == citation.chunk_index,
            )
        )
        rows = []
        for chunk, filename in result.all():
            if filename == citation.filename:
                rows.append(chunk)

    return [
        {
            "id": row.id,
            "document_id": row.document_id,
            "project_id": row.project_id,
            "filename": citation.filename,
            "chunk_index": row.chunk_index,
            "chunk_index_end": citation.chunk_index_end,
            "content": row.content,
        }
        for row in rows
    ]
