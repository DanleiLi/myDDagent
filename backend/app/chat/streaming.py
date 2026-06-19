"""SSE event formatters.

Every function returns a plain dict that is JSON-serialised by the orchestrator
before being pushed to the client as a Server-Sent Event data payload.
"""

from __future__ import annotations

from app.services.gap_detector import GapFinding


def text_delta_event(delta: str) -> dict:
    return {"type": "text_delta", "delta": delta}


def tool_use_event(tool_name: str, tool_input: dict) -> dict:
    return {"type": "tool_use", "tool": tool_name, "input": tool_input}


def gap_flag_event(gap: GapFinding) -> dict:
    return {
        "type": "gap_flag",
        "field_name": gap.field_name,
        "flag_type": gap.flag_type,
        "description": gap.description,
    }


def done_event(message_id: str) -> dict:
    return {"type": "done", "message_id": message_id}


def error_event(message: str) -> dict:
    return {"type": "error", "message": message}
