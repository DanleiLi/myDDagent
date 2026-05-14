"""
LLM-based JSON Restructurer
Uses Claude API to transform raw spreadsheet JSON into meaningful semantic structure.
"""

import json
import os
import sys
from typing import Any

try:
    import anthropic
except ImportError:
    anthropic = None


_PROMPT = """You are a data analyst. You have been given a raw JSON dump extracted from an Excel worksheet named "{sheet_name}".

Common problems in this dump:
- Columns are named Unnamed: 0, Unnamed: 1, etc. (no real headers detected)
- NaN and null values mixed in
- Section headers embedded as data rows
- Multiple entities (e.g. portfolios) spread across many columns in a single row

Your job: return clean, well-structured JSON that accurately reflects the real content.

Rules:
1. Identify the actual semantic structure (questionnaire Q&A, table, multi-portfolio comparison, etc.)
2. Use meaningful field names derived from the data itself — never keep "Unnamed: X" keys
3. Strip all null/NaN/empty values from the output
4. For questionnaire format: group by section, use question text as key, answer as value
5. For multi-entity tables (e.g. multiple portfolios per row): produce an array of objects, one per entity
6. Do NOT fabricate, infer, or alter any actual data values — preserve them exactly as-is
7. Output ONLY valid JSON — no markdown fences, no explanation

Raw data:
{raw_data}"""


class LLMRestructurer:
    """Sends raw spreadsheet JSON to Claude and returns a semantically meaningful structure."""

    def __init__(self):
        if anthropic is None:
            raise ImportError("anthropic package required. Install with: pip install anthropic")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=api_key)

    def restructure(self, raw_data: Any, sheet_name: str) -> Any:
        """Call Claude to restructure raw JSON into a semantic form."""
        raw_json = json.dumps(raw_data, ensure_ascii=False, indent=2, default=str)

        # Guard against very large payloads
        if len(raw_json) > 60000:
            raw_json = raw_json[:60000] + "\n... [truncated for length]"

        prompt = _PROMPT.format(sheet_name=sheet_name, raw_data=raw_json)

        message = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text.strip()

        # Strip accidental markdown fences
        if text.startswith("```"):
            lines = text.splitlines()
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines).strip()

        return json.loads(text)
