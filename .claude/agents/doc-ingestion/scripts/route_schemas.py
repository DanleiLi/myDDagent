"""
Schema router for the doc-ingestion agent.

Given a preprocessed.json file (output of preprocess.py), reports which
.claude/dataset/*.json target(s) each section/table should feed.

Routing is data-driven: it walks every .claude/schema/*.schema.json, extracts
each schema's distinctive vocabulary (field names + enums + descriptions), and
scores every section/table in the preprocessed payload against every schema.
Top scorers are suggested. The agent verifies before writing.

CLI:
    python route_schemas.py <preprocessed.json>

Output (stdout, JSON):
{
  "source": "<preprocessed.json path>",
  "schema_dataset_map": { "modelportfolio": "modelportfolio.json", ... },
  "suggestions": [
    {
      "location": "table:Sheet1" | "section:body",
      "ranked": [{"schema": "IM", "score": 12, "matched": ["abn", "afsl"]}, ...]
    }
  ],
  "schema_coverage": { "IM": 17, "modelportfolio": 4, ... }   # total hits per schema
}
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parents[3]
SCHEMA_DIR = BASE_DIR / ".claude" / "schema"
DATASET_DIR = BASE_DIR / ".claude" / "dataset"

STOPWORDS = {
    "type", "string", "number", "integer", "boolean", "array", "object", "null",
    "items", "properties", "required", "format", "description", "enum", "pattern",
    "minimum", "maximum", "minlength", "maxlength", "additionalproperties", "ref",
    "definitions", "schema", "title", "metadata", "true", "false", "date", "value",
    "name", "id", "list", "any", "all", "the", "and", "or", "of", "to", "in",
    "for", "with", "as", "an", "a", "is", "be", "by", "on", "at", "if", "not",
    "may", "must", "from", "this", "that", "these", "those", "field", "data",
    "agent", "manager", "platform", "fund", "portfolio", "managed", "north", "amp",
    "populated", "edit", "manually", "template", "only", "never", "write", "file",
    "should", "must", "shall", "minitems",
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+")


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text or "") if len(t) > 2}


def _walk_schema_keys(node, out: set[str]):
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str) and len(k) > 2:
                out.add(k.lower())
            if k in {"description", "title"} and isinstance(v, str):
                out.update(_tokens(v))
            if k == "enum" and isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        out.update(_tokens(item))
            _walk_schema_keys(v, out)
    elif isinstance(node, list):
        for item in node:
            _walk_schema_keys(item, out)


def load_schema_signatures() -> dict[str, set[str]]:
    sigs: dict[str, set[str]] = {}
    for schema_path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        try:
            doc = json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        keys: set[str] = set()
        _walk_schema_keys(doc, keys)
        keys -= STOPWORDS
        schema_name = schema_path.name.removesuffix(".schema.json")
        sigs[schema_name] = keys
    return sigs


def schema_dataset_map() -> dict[str, str]:
    return {p.name.removesuffix(".schema.json"): p.name.removesuffix(".schema.json") + ".json"
            for p in sorted(SCHEMA_DIR.glob("*.schema.json"))}


def section_text(section: dict) -> str:
    return section.get("content", "")


def table_text(table: dict) -> str:
    parts = [table.get("name", "")]
    for row in table.get("rows", []):
        parts.extend(str(c) for c in row)
    return " ".join(parts)


def score_location(location_text: str, sigs: dict[str, set[str]]) -> list[dict]:
    toks = _tokens(location_text)
    ranked = []
    for schema_name, keys in sigs.items():
        matched = sorted(toks & keys)
        if matched:
            ranked.append({"schema": schema_name, "score": len(matched), "matched": matched[:10]})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked


def route(preprocessed_path: Path) -> dict:
    payload = json.loads(preprocessed_path.read_text(encoding="utf-8"))
    sigs = load_schema_signatures()

    suggestions = []
    coverage: dict[str, int] = {s: 0 for s in sigs}

    for section in payload.get("sections", []):
        ranked = score_location(section_text(section), sigs)
        suggestions.append({"location": f"section:{section.get('name', '?')}", "ranked": ranked[:3]})
        for r in ranked:
            coverage[r["schema"]] = coverage.get(r["schema"], 0) + r["score"]

    for table in payload.get("tables", []):
        ranked = score_location(table_text(table), sigs)
        suggestions.append({"location": f"table:{table.get('name', '?')}", "ranked": ranked[:3]})
        for r in ranked:
            coverage[r["schema"]] = coverage.get(r["schema"], 0) + r["score"]

    return {
        "source": str(preprocessed_path),
        "schema_dataset_map": schema_dataset_map(),
        "suggestions": suggestions,
        "schema_coverage": dict(sorted(coverage.items(), key=lambda kv: kv[1], reverse=True)),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: route_schemas.py <preprocessed.json>", file=sys.stderr)
        return 2
    p = Path(argv[0]).resolve()
    if not p.exists():
        print(f"NOT FOUND: {p}", file=sys.stderr)
        return 1
    result = route(p)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
