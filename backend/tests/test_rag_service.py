from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services import rag_service


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeDB:
    def __init__(self, responses):
        self._responses = responses
        self.calls = 0

    async def execute(self, statement, params=None):  # noqa: ARG002
        rows = self._responses[self.calls]
        self.calls += 1
        return _FakeResult(rows)


class _FakeEmbeddings:
    async def create(self, input, model):  # noqa: ARG002
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])]
        )


class _FakeOpenAI:
    def __init__(self):
        self.embeddings = _FakeEmbeddings()


def _row(chunk_id: str, document_id: str, filename: str, content: str, chunk_index: int, score: float = 0.9):
    return SimpleNamespace(
        chunk_id=chunk_id,
        document_id=document_id,
        filename=filename,
        content=content,
        chunk_index=chunk_index,
        score=score,
    )


@pytest.mark.asyncio
async def test_retrieve_expands_table_span_and_anchors_to_first_chunk(monkeypatch):
    monkeypatch.setattr(rag_service, "_get_openai", lambda: _FakeOpenAI())

    project_id = "project-1"
    document_id = "doc-1"
    filename = "holdings.md"

    seed_rows = [_row("seed-8", document_id, filename, "Holdings by portfolio", 8, 0.95)]
    window_rows = [
        _row("c-8", document_id, filename, "Holdings by portfolio", 8),
        _row("c-9", document_id, filename, "| Portfolio | Holdings |", 9),
        _row("c-10", document_id, filename, "| Alpha | 12 |", 10),
        _row("c-11", document_id, filename, "| Beta | 8 |", 11),
        _row("c-12", document_id, filename, "| Gamma | 15 |", 12),
    ]
    db = _FakeDB([seed_rows, [], window_rows])

    chunks = await rag_service.retrieve("how many holdings are there in each portfolio?", project_id, db, top_k=1)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.expanded is True
    assert chunk.chunk_index == 8
    assert chunk.chunk_index_end == 12
    assert "Holdings by portfolio" in chunk.content
    assert "| Alpha | 12 |" in chunk.content
    assert "| Gamma | 15 |" in chunk.content


@pytest.mark.asyncio
async def test_retrieve_dedupes_overlapping_table_spans(monkeypatch):
    monkeypatch.setattr(rag_service, "_get_openai", lambda: _FakeOpenAI())

    project_id = "project-1"
    document_id = "doc-1"
    filename = "holdings.md"

    sem_rows = [
        _row("seed-10", document_id, filename, "| Alpha | 12 |", 10, 0.98),
        _row("seed-11", document_id, filename, "| Beta | 8 |", 11, 0.97),
    ]
    window_rows = [
        _row("c-9", document_id, filename, "| Portfolio | Holdings |", 9),
        _row("c-10", document_id, filename, "| Alpha | 12 |", 10),
        _row("c-11", document_id, filename, "| Beta | 8 |", 11),
        _row("c-12", document_id, filename, "| Gamma | 15 |", 12),
    ]
    db = _FakeDB([sem_rows, [], window_rows, window_rows])

    chunks = await rag_service.retrieve("how many holdings are there in each portfolio?", project_id, db, top_k=2)

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 9
    assert chunks[0].chunk_index_end == 12


@pytest.mark.asyncio
async def test_retrieve_leaves_non_table_chunks_unchanged(monkeypatch):
    monkeypatch.setattr(rag_service, "_get_openai", lambda: _FakeOpenAI())

    project_id = "project-1"
    document_id = "doc-1"
    filename = "overview.md"

    sem_rows = [_row("seed-2", document_id, filename, "This section summarises the portfolio.", 2, 0.77)]
    window_rows = [
        _row("c-0", document_id, filename, "Introduction", 0),
        _row("c-1", document_id, filename, "This section summarises the portfolio.", 1),
        _row("c-2", document_id, filename, "It covers fees and governance.", 2),
    ]
    db = _FakeDB([sem_rows, [], window_rows])

    chunks = await rag_service.retrieve("portfolio overview", project_id, db, top_k=1)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.expanded is False
    assert chunk.chunk_index_end is None
    assert chunk.content == "This section summarises the portfolio."
