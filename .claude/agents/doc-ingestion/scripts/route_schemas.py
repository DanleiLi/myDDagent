"""
Schema router for the doc-ingestion agent.

Given a preprocessed.json file (output of preprocess.py), reports which
.codex/dataset/*.json target(s) each section/table should feed.

Routing is data-driven: it walks every .codex/schema/*.schema.json, extracts
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
SCHEMA_DIR = BASE_DIR / ".codex" / "schema"
DATASET_DIR = BASE_DIR / ".codex" / "dataset"

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


def load_schema_signatures(allowed: set[str] | None = None) -> dict[str, set[str]]:
    sigs: dict[str, set[str]] = {}
    for schema_path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema_name = schema_path.name.removesuffix(".schema.json")
        if allowed is not None and schema_name not in allowed:
            continue
        try:
            doc = json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        keys: set[str] = set()

        # Weight _meta.description heavily (highest signal of schema purpose)
        meta = doc.get("_meta", {})
        if isinstance(meta, dict) and "description" in meta:
            meta_desc = meta["description"]
            if isinstance(meta_desc, str):
                keys.update(_tokens(meta_desc))

        # Walk remaining schema keys (field names, descriptions, enums)
        _walk_schema_keys(doc, keys)
        keys -= STOPWORDS
        sigs[schema_name] = keys
    return sigs


def schema_dataset_map(allowed: set[str] | None = None) -> dict[str, str]:
    result = {}
    for p in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema_name = p.name.removesuffix(".schema.json")
        if allowed is not None and schema_name not in allowed:
            continue
        result[schema_name] = schema_name + ".json"
    return result


def extract_document_keywords(payload: dict) -> set[str]:
    """Extract document-level keyword fingerprint from all sections and tables."""
    all_text = []

    # Aggregate all section content
    for section in payload.get("sections", []):
        if section.get("name"):
            all_text.append(section["name"])
        if section.get("content"):
            all_text.append(section["content"])

    # Aggregate all table content
    for table in payload.get("tables", []):
        if table.get("name"):
            all_text.append(table["name"])
        for row in table.get("rows", []):
            all_text.extend(str(c) for c in row if c)

    combined = " ".join(all_text)
    keywords = _tokens(combined)
    return keywords


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
    MIN_COVERAGE_SCORE = 2  # Threshold for including a schema

    payload = json.loads(preprocessed_path.read_text(encoding="utf-8"))
    sigs = load_schema_signatures()

    # Extract document-level keyword fingerprint
    doc_keywords = extract_document_keywords(payload)

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

    # Apply threshold filter: only include schemas above MIN_COVERAGE_SCORE
    relevant_schemas = {s for s, score in coverage.items() if score >= MIN_COVERAGE_SCORE}
    # Safety fallback: always include at least the top scorer to avoid empty results
    if not relevant_schemas and coverage:
        relevant_schemas = {max(coverage, key=coverage.get)}

    filtered_by_threshold = len(relevant_schemas) < len(coverage)

    return {
        "source": str(preprocessed_path),
        "schema_dataset_map": schema_dataset_map(allowed=relevant_schemas),
        "suggestions": suggestions,
        "schema_coverage": dict(sorted(coverage.items(), key=lambda kv: kv[1], reverse=True)),
        "filtered_by_threshold": filtered_by_threshold,
        "min_coverage_score_used": MIN_COVERAGE_SCORE,
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
