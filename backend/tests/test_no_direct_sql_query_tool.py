from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_SNIPPETS = [
    "query_database",
    "sql_query_tool",
    "is_safe_select_query",
    "Only SELECT statements are permitted",
]


def test_legacy_sql_query_entrypoints_are_removed() -> None:
    assert not (ROOT / "main.py").exists()
    assert not (ROOT / "backend" / "app_legacy.py").exists()


def test_active_agent_code_no_longer_mentions_direct_sql_querying() -> None:
    text_files = [
        ROOT / "backend" / "app" / "assistant" / "agent.py",
        ROOT / "backend" / "app" / "assistant" / "instructions.md",
        ROOT / "backend" / "app" / "assistant" / "tools.py",
        ROOT / "todo.md",
        ROOT / "backend" / "CLAUDE.md",
    ]

    for path in text_files:
        text = path.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_SNIPPETS:
            assert snippet not in text, f"{snippet!r} still present in {path}"
