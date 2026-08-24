from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import UUID

from app.models import WebsiteBuildPlan, WebsiteBuildStatus
from app.store import Repository


ALLOWED_DEPENDENCIES = {
    "next": "15.5.21",
    "react": "19.1.9",
    "react-dom": "19.1.9",
}


class WebsiteBuildService:
    """Plans and executes generated-site builds inside disposable Docker sandboxes."""

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def plan(self, project_id: UUID) -> WebsiteBuildPlan:
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError("generation")
        if generation.status.value not in {"generated", "validated"}:
            return WebsiteBuildPlan(
                project_id=project_id,
                generation_version=generation.version,
                status=WebsiteBuildStatus.REJECTED,
                diagnostics=["Website Generation is not in an executable lifecycle state."],
                files=[f.path for f in generation.files],
            )
        diagnostics: list[str] = []
        paths = [f.path for f in generation.files]
        if "package.json" not in paths:
            diagnostics.append("Generated artifact is missing package.json.")
        if not any(p.startswith("app/") for p in paths):
            diagnostics.append("Generated artifact contains no Next.js App Router files.")
        package = next((f.content for f in generation.files if f.path == "package.json"), None)
        if package:
            try:
                manifest = json.loads(package)
                dependencies = manifest.get("dependencies", {})
                unsupported = sorted(
                    f"{name}@{version}" for name, version in dependencies.items()
                    if name not in ALLOWED_DEPENDENCIES or str(version) != ALLOWED_DEPENDENCIES[name]
                )
                if unsupported:
                    diagnostics.append(f"Unsupported runtime dependencies: {', '.join(unsupported)}")
            except json.JSONDecodeError:
                diagnostics.append("Generated package.json is not valid JSON.")
        return WebsiteBuildPlan(
            project_id=project_id,
            generation_version=generation.version,
            status=WebsiteBuildStatus.PLANNED if not diagnostics else WebsiteBuildStatus.REJECTED,
            diagnostics=diagnostics,
            files=paths,
        )

    async def execute(self, project_id: UUID, timeout_seconds: int = 120) -> dict[str, object]:
        plan = await self.plan(project_id)
        if plan.status != WebsiteBuildStatus.PLANNED:
            return {"status": "rejected", "plan": plan.model_dump(mode="json")}
        generation = await self.repository.get_generation(project_id)
        assert generation is not None
        if shutil.which("docker") is None:
            return {"status": "unavailable", "reason": "Docker is required for isolated execution.", "plan": plan.model_dump(mode="json")}

        with tempfile.TemporaryDirectory(prefix="awe-build-") as temp:
            workspace = Path(temp)
            for generated in generation.files:
                target = workspace / generated.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(generated.content, encoding="utf-8")

            # Dependency acquisition is intentionally constrained and scripts are disabled.
            install = self._docker_run(
                workspace,
                ["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund"],
                network="bridge",
                timeout=timeout_seconds,
            )
            if install.returncode != 0:
                return {"status": "failed", "phase": "dependency-install", "stdout": install.stdout[-4000:], "stderr": install.stderr[-4000:], "plan": plan.model_dump(mode="json")}

            build = self._docker_run(
                workspace,
                ["npm", "run", "build"],
                network="none",
                timeout=timeout_seconds,
            )
            result: dict[str, object] = {
                "status": "succeeded" if build.returncode == 0 else "failed",
                "phase": "build",
                "stdout": build.stdout[-4000:],
                "stderr": build.stderr[-4000:],
                "isolation": "docker",
                "network_during_build": "none",
                "workspace": "ephemeral",
                "plan": plan.model_dump(mode="json"),
            }
            return result

    @staticmethod
    def _docker_run(workspace: Path, command: list[str], network: str, timeout: int) -> subprocess.CompletedProcess[str]:
        docker_command = [
            "docker", "run", "--rm",
            "--network", network,
            "--cpus", "1",
            "--memory", "768m",
            "--pids-limit", "128",
            "--read-only",
            "--tmpfs", "/tmp:rw,nosuid,nodev,noexec",
            "-e", "NEXT_TELEMETRY_DISABLED=1",
            "-v", f"{workspace}:/workspace:rw",
            "-w", "/workspace",
            "node:22-alpine",
            *command,
        ]
        try:
            return subprocess.run(docker_command, capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(docker_command, 124, exc.stdout or "", f"Execution timed out after {timeout}s")
