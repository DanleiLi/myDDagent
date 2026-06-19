"""Pydantic-AI agent singleton for the Dossier due diligence assistant."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from app.assistant.deps import DossierAgentDeps
from app.assistant.tools import (
    check_schema_coverage,
    draft_report_section,
    generate_final_report,
    retrieve_context,
    run_analysis_script,
)
from app.config import settings

_instructions = (Path(__file__).parent / "instructions.md").read_text(encoding="utf-8")

agent: Agent[DossierAgentDeps, str] = Agent(
    AnthropicModel("claude-sonnet-4-6", provider=AnthropicProvider(api_key=settings.anthropic_api_key)),
    deps_type=DossierAgentDeps,
    system_prompt=_instructions,
    tools=[
        retrieve_context,
        check_schema_coverage,
        draft_report_section,
        generate_final_report,
        run_analysis_script,
    ],
    retries=2,
    end_strategy="exhaustive",
)
