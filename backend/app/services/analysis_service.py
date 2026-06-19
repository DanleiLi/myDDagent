"""Analysis service — validates and runs quantitative analysis scripts.

enqueue()   — validates script name against the allowlist; returns (job_id, output_path).
run_script() — executes the script as a subprocess; called from background task.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

ALLOWED_SCRIPTS: frozenset[str] = frozenset(
    {"fee_analysis", "portfolio_metrics", "risk_analysis"}
)

_SCRIPT_EXTENSION: dict[str, str] = {
    "fee_analysis": ".xlsx",
    "portfolio_metrics": ".xlsx",
    "risk_analysis": ".xlsx",
}


class AnalysisService:
    def enqueue(
        self,
        script_name: str,
        params: dict,
        project_id: str,
    ) -> tuple[str, Path]:
        """Validate the requested script and return (job_id, output_path).

        Raises ValueError for unknown script names.
        The actual execution and DB record creation are handled by the orchestrator.
        """
        if script_name not in ALLOWED_SCRIPTS:
            raise ValueError(
                f"Unknown script '{script_name}'. Allowed: {sorted(ALLOWED_SCRIPTS)}"
            )

        job_id = str(uuid.uuid4())
        ext = _SCRIPT_EXTENSION.get(script_name, ".xlsx")
        output_path = settings.outputs_dir / f"{project_id}_{script_name}_{job_id}{ext}"
        return job_id, output_path

    async def run_script(
        self,
        script_name: str,
        params: dict,
        project_id: str,
        output_path: Path,
    ) -> None:
        """Run the named script as a subprocess.

        Raises RuntimeError if the process exits with a non-zero code.
        """
        script_path = settings.scripts_dir / f"{script_name}.py"
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        logger.info(
            "running analysis script",
            script=script_name,
            project_id=project_id,
            output=str(output_path),
        )

        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            "--params", json.dumps(params),
            "--output", str(output_path),
            "--project", project_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err = stderr.decode(errors="replace")
            logger.error(
                "analysis script failed",
                script=script_name,
                project_id=project_id,
                returncode=proc.returncode,
                stderr=err[:500],
            )
            raise RuntimeError(f"Script '{script_name}' failed (exit {proc.returncode}): {err}")

        logger.info(
            "analysis script completed",
            script=script_name,
            project_id=project_id,
            output=str(output_path),
        )
