"""Hybrid RAG retrieval: pgvector cosine similarity + full-text search, fused with RRF.

Retrieval only — no DB writes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import structlog
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = structlog.get_logger(__name__)

_openai: AsyncOpenAI | None = None

_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")
_MAX_TABLE_WINDOW = 5
_MAX_TABLE_CHUNKS = 8
_MAX_TABLE_CHARS = 6000


def _get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    filename: str
    content: str
    score: float
    chunk_index: int
    chunk_index_end: int | None = None
    expanded: bool = False


@dataclass(slots=True)
class _ChunkRecord:
    chunk_id: str
    document_id: str
    filename: str
    content: str
    chunk_index: int
    score: float


def _looks_like_table(content: str) -> bool:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return False

    if any(line.count("|") >= 2 for line in lines):
        return True

    pipe_lines = [line for line in lines if "|" in line]
    if len(pipe_lines) >= 2:
        return True

    if any(_TABLE_SEPARATOR_RE.match(line) for line in lines) and pipe_lines:
        return True

    if content.count("|") >= 4 and len(lines) <= 4:
        return True

    return False


def _looks_like_heading(content: str) -> bool:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return False
    return len(lines) <= 4 and len(content) <= 250 and "|" not in content


def _join_context(rows: list[_ChunkRecord]) -> str:
    return "\n\n".join(row.content.strip() for row in rows if row.content.strip())


async def _fetch_chunk_window(
    db: AsyncSession,
    project_id: str,
    document_id: str,
    start_index: int,
    end_index: int,
) -> list[_ChunkRecord]:
    result = (
        await db.execute(
            text("""
                SELECT
                    dc.id::text        AS chunk_id,
                    dc.document_id::text,
                    dc.content,
                    dc.chunk_index,
                    d.filename
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE dc.project_id = :project_id
                  AND dc.document_id = :document_id
                  AND dc.chunk_index BETWEEN :start_index AND :end_index
                ORDER BY dc.chunk_index
            """),
            {
                "project_id": project_id,
                "document_id": document_id,
                "start_index": start_index,
                "end_index": end_index,
            },
        )
    ).fetchall()

    return [
        _ChunkRecord(
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            filename=row.filename,
            content=row.content,
            chunk_index=row.chunk_index,
            score=0.0,
        )
        for row in result
    ]


def _pick_table_span(
    rows: list[_ChunkRecord],
    seed_index: int,
) -> tuple[int, int] | None:
    if not rows:
        return None

    by_index = {row.chunk_index: row for row in rows}
    table_indices = [row.chunk_index for row in rows if _looks_like_table(row.content)]
    if not table_indices:
        return None

    if seed_index in by_index and _looks_like_table(by_index[seed_index].content):
        anchor_index = seed_index
    else:
        anchor_index = min(
            table_indices,
            key=lambda idx: (abs(idx - seed_index), idx),
        )

    start = anchor_index
    end = anchor_index

    while start - 1 in by_index and _looks_like_table(by_index[start - 1].content):
        start -= 1
        if end - start + 1 >= _MAX_TABLE_CHUNKS:
            break

    while end + 1 in by_index and _looks_like_table(by_index[end + 1].content):
        end += 1
        if end - start + 1 >= _MAX_TABLE_CHUNKS:
            break

    if start > seed_index and seed_index in by_index and _looks_like_heading(by_index[seed_index].content):
        start = seed_index

    return start, end


async def _expand_seed_chunk(
    db: AsyncSession,
    project_id: str,
    seed: _ChunkRecord,
) -> tuple[list[_ChunkRecord], int | None]:
    window_start = max(0, seed.chunk_index - _MAX_TABLE_WINDOW)
    window_end = seed.chunk_index + _MAX_TABLE_WINDOW
    rows = await _fetch_chunk_window(
        db,
        project_id,
        seed.document_id,
        window_start,
        window_end,
    )
    if not rows:
        return [seed], None

    span = _pick_table_span(rows, seed.chunk_index)
    if span is None:
        return [seed], None

    start, end = span
    span_rows = [row for row in rows if start <= row.chunk_index <= end]
    merged = _join_context(span_rows)
    if not merged or len(merged) > _MAX_TABLE_CHARS:
        return [seed], None

    return span_rows, end


async def retrieve(
    query: str,
    project_id: str,
    db: AsyncSession,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Hybrid search: pgvector cosine + FTS, fused with Reciprocal Rank Fusion."""
    # 1. Embed the query
    resp = await _get_openai().embeddings.create(
        input=[query],
        model=settings.embedding_model,
    )
    emb_literal = "[" + ",".join(str(v) for v in resp.data[0].embedding) + "]"

    # 2. Semantic search — cosine similarity via pgvector
    sem_rows = (
        await db.execute(
            text(f"""
                SELECT
                    dc.id::text                                              AS chunk_id,
                    dc.document_id::text,
                    dc.content,
                    dc.chunk_index,
                    d.filename,
                    1 - (dc.embedding <=> '{emb_literal}'::vector)          AS score
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE dc.project_id = :project_id
                  AND dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> '{emb_literal}'::vector
                LIMIT :lim
            """),
            {"project_id": project_id, "lim": top_k * 2},
        )
    ).fetchall()

    # 3. Full-text search — tsvector with ts_rank_cd
    fts_rows = (
        await db.execute(
            text("""
                SELECT
                    dc.id::text                                                          AS chunk_id,
                    dc.document_id::text,
                    dc.content,
                    dc.chunk_index,
                    d.filename,
                    ts_rank_cd(dc.search_vector, plainto_tsquery('english', :q))         AS score
                FROM document_chunks dc
                JOIN documents d ON d.id = dc.document_id
                WHERE dc.project_id = :project_id
                  AND dc.search_vector @@ plainto_tsquery('english', :q)
                ORDER BY score DESC
                LIMIT :lim
            """),
            {"q": query, "project_id": project_id, "lim": top_k * 2},
        )
    ).fetchall()

    # 4. RRF fusion — rank using Σ 1/(60 + rank), but expose cosine similarity as score
    rrf: dict[str, float] = {}
    sem_score: dict[str, float] = {}  # cosine similarity from semantic search
    data: dict[str, object] = {}

    for rank, row in enumerate(sem_rows):
        cid = row.chunk_id
        rrf[cid] = rrf.get(cid, 0.0) + 1.0 / (60 + rank + 1)
        sem_score[cid] = float(row.score)  # cosine similarity 0-1
        data[cid] = row

    for rank, row in enumerate(fts_rows):
        cid = row.chunk_id
        rrf[cid] = rrf.get(cid, 0.0) + 1.0 / (60 + rank + 1)
        data.setdefault(cid, row)

    top = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]
    seen_spans: set[tuple[str, int, int | None]] = set()
    results: list[RetrievedChunk] = []

    for cid, _ in top:
        row = data[cid]
        seed = _ChunkRecord(
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            filename=row.filename,
            content=row.content,
            chunk_index=row.chunk_index,
            score=sem_score.get(cid, 0.0),
        )
        span_rows, chunk_index_end = await _expand_seed_chunk(db, project_id, seed)
        anchor_row = span_rows[0]
        chunk_index = anchor_row.chunk_index
        chunk_id = anchor_row.chunk_id
        expanded_content = _join_context(span_rows)
        span_key = (seed.document_id, chunk_index, chunk_index_end)
        if span_key in seen_spans:
            continue
        seen_spans.add(span_key)
        results.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                document_id=seed.document_id,
                filename=anchor_row.filename,
                content=expanded_content,
                score=seed.score,  # cosine similarity; 0.0 for FTS-only hits
                chunk_index=chunk_index,
                chunk_index_end=chunk_index_end,
                expanded=chunk_index_end is not None,
            )
        )

    logger.debug(
        "retrieved",
        query=query[:60],
        project_id=project_id,
        semantic_hits=len(sem_rows),
        fts_hits=len(fts_rows),
        returned=len(results),
    )

    return results
