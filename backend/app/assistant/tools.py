"""Pydantic-AI tool functions for the Dossier agent.

All tools are read-only — no DB writes — except:
  - generate_final_report writes one output file to disk.
Tool functions are imported and registered on the agent in agent.py.
"""

from __future__ import annotations

import json

import structlog
from pydantic_ai import RunContext

from app.assistant.deps import DossierAgentDeps
from app.services.gap_detector import check_coverage
from app.services.rag_service import retrieve
from app.services.report_service import generate_final_report as generate_project_report

logger = structlog.get_logger(__name__)


# ── helpers ──────────────────────────────────────────────────────────────────


def _fmt_chunks(chunks) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        source_label = f"{c.filename}, chunk {c.chunk_index}"
        if getattr(c, "chunk_index_end", None) is not None and c.chunk_index_end != c.chunk_index:
            source_label = f"{c.filename}, chunk {c.chunk_index}-{c.chunk_index_end}"
        if getattr(c, "expanded", False):
            source_label += " (expanded context)"
        lines.append(
            f"[{i}] Source: {source_label} (score {c.score:.3f})\n{c.content}"
        )
    return "\n\n".join(lines)


# ── tools ─────────────────────────────────────────────────────────────────────


async def retrieve_context(
    ctx: RunContext[DossierAgentDeps],
    query: str,
    top_k: int = 5,
) -> str:
    """Search uploaded documents for passages relevant to *query*.

    Returns numbered source passages with filename and chunk index.
    Call this before making any factual statement.
    """
    await ctx.deps.event_queue.put({"type": "tool_use", "tool": "retrieve_context", "input": {"query": query, "top_k": top_k}})

    chunks = await retrieve(query, ctx.deps.project_id, ctx.deps.db, top_k=top_k)

    if not chunks:
        return "No relevant passages found for this query."

    logger.debug("retrieve_context", query=query[:60], hits=len(chunks))
    return _fmt_chunks(chunks)


async def check_schema_coverage(ctx: RunContext[DossierAgentDeps]) -> str:
    """Check which required DD schema fields lack sufficient evidence in the uploaded documents.

    Returns a JSON summary of gaps. Does NOT write to the database.
    """
    await ctx.deps.event_queue.put({"type": "tool_use", "tool": "check_schema_coverage", "input": {}})

    findings = await check_coverage(ctx.deps.project_id, ctx.deps.db)

    if not findings:
        return json.dumps({"status": "all_covered", "gaps": []})

    gaps = [
        {"field": f.field_name, "flag_type": f.flag_type, "description": f.description}
        for f in findings
    ]
    return json.dumps({"status": "gaps_found", "gaps": gaps}, indent=2)


async def draft_report_section(
    ctx: RunContext[DossierAgentDeps],
    section_name: str,
) -> str:
    """Retrieve evidence for a named report section (e.g. 'Fees and Costs', 'Risk Management').

    Returns up to 10 relevant source passages. Use the passages to draft or review the section.
    """
    await ctx.deps.event_queue.put({"type": "tool_use", "tool": "draft_report_section", "input": {"section_name": section_name}})

    chunks = await retrieve(section_name, ctx.deps.project_id, ctx.deps.db, top_k=10)

    if not chunks:
        return f"No evidence found for section '{section_name}'."

    return f"Evidence for '{section_name}':\n\n" + _fmt_chunks(chunks)


async def generate_final_report(ctx: RunContext[DossierAgentDeps]) -> str:
    """Generate the complete due diligence report using the shared report service."""
    await ctx.deps.event_queue.put({"type": "tool_use", "tool": "generate_final_report", "input": {}})

    if ctx.deps.template_service is None:
        return "ERROR: template_service is not available."

    generated = await generate_project_report(
        ctx.deps.project_id,
        ctx.deps.db,
        template_service=ctx.deps.template_service,
    )

    logger.info(
        "generated final report",
        project_id=ctx.deps.project_id,
        path=str(generated.output_path),
        citations=len(generated.citations),
    )

    await ctx.deps.event_queue.put(
        {
            "type": "report_generated",
            "output_path": str(generated.output_path),
            "project_id": ctx.deps.project_id,
        }
    )

    return generated.report_text


async def run_analysis_script(
    ctx: RunContext[DossierAgentDeps],
    script_name: str,
    params: dict,
) -> str:
    """Enqueue a quantitative analysis script to run in the background.

    Allowed scripts: fee_analysis, portfolio_metrics, risk_analysis.
    Returns a job reference string. The orchestrator launches the script and tracks progress.
    """
    await ctx.deps.event_queue.put({"type": "tool_use", "tool": "run_analysis_script", "input": {"script_name": script_name}})

    if ctx.deps.analysis_service is None:
        return "ERROR: analysis_service is not available."

    try:
        job_id, output_path = ctx.deps.analysis_service.enqueue(
            script_name, params, ctx.deps.project_id
        )
    except ValueError as exc:
        return f"ERROR: {exc}"

    # Signal orchestrator to create AnalysisOutput DB record and launch the script
    await ctx.deps.event_queue.put({
        "type": "analysis_enqueued",
        "job_id": job_id,
        "script_name": script_name,
        "params": params,
        "output_path": str(output_path),
        "project_id": ctx.deps.project_id,
    })

    return f"Analysis job enqueued. Job ID: {job_id}. Script: {script_name}. Results will be saved to {output_path.name}."
