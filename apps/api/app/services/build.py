from __future__ import annotations

import json
import os
import shutil
import subprocess
from uuid import UUID

from app.models import WebsiteBuildPlan, WebsiteBuildStatus, WebsiteExecutionState
from app.services.docker_workspace import (
    create_workspace_volume,
    populate_workspace_volume,
    remove_workspace_volume,
)
from app.store import Repository


ALLOWED_DEPENDENCIES = {
    "next": "15.5.21",
    "react": "19.1.9",
    "react-dom": "19.1.9",
}

DEFAULT_INSTALL_TIMEOUT_SECONDS = 300
DEFAULT_BUILD_TIMEOUT_SECONDS = 180
MAX_TIMEOUT_SECONDS = 600


ALLOWED_DEV_DEPENDENCIES = {
    "typescript": "5.8.2",
    "@types/react": "19.1.10",
    "@types/node": "20.17.6",
}


class WebsiteBuildService:
    """Plans and executes generated-site builds inside disposable Docker sandboxes.

    Dependency installation gets a larger budget because a cold Docker/npm cache
    can legitimately take a few minutes; the offline production build gets a
    separate, tighter budget.
    """

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
                diagnostics=[
                    "Website Generation is not in an executable lifecycle state."
                ],
                files=[f.path for f in generation.files],
            )

        diagnostics: list[str] = []
        paths = [f.path for f in generation.files]

        if "package.json" not in paths:
            diagnostics.append("Generated artifact is missing package.json.")

        if not any(p.startswith("app/") for p in paths):
            diagnostics.append(
                "Generated artifact contains no Next.js App Router files."
            )

        package = next(
            (f.content for f in generation.files if f.path == "package.json"),
            None,
        )

        if package:
            try:
                manifest = json.loads(package)
                dependencies = manifest.get("dependencies", {})
                unsupported = sorted(
                    f"{name}@{version}"
                    for name, version in dependencies.items()
                    if name not in ALLOWED_DEPENDENCIES
                    or str(version) != ALLOWED_DEPENDENCIES[name]
                )
                if unsupported:
                    diagnostics.append(
                        "Unsupported runtime dependencies: "
                        + ", ".join(unsupported)
                    )

                dev_dependencies = manifest.get("devDependencies", {})
                unsupported_dev = sorted(
                    f"{name}@{version}"
                    for name, version in dev_dependencies.items()
                    if name not in ALLOWED_DEV_DEPENDENCIES
                    or str(version) != ALLOWED_DEV_DEPENDENCIES[name]
                )
                if unsupported_dev:
                    diagnostics.append(
                        "Unsupported development dependencies: "
                        + ", ".join(unsupported_dev)
                    )
            except json.JSONDecodeError:
                diagnostics.append("Generated package.json is not valid JSON.")

        return WebsiteBuildPlan(
            project_id=project_id,
            generation_version=generation.version,
            status=(
                WebsiteBuildStatus.PLANNED
                if not diagnostics
                else WebsiteBuildStatus.REJECTED
            ),
            isolation="sandbox-required",
            runtime="nextjs-app-router",
            workspace_strategy="docker-volume",
            allowed_commands=["npm install", "next build", "next start"],
            network_access="build-install-only",
            diagnostics=diagnostics,
            files=paths,
        )

    async def execute(
        self,
        project_id: UUID,
        install_timeout_seconds: int = DEFAULT_INSTALL_TIMEOUT_SECONDS,
        build_timeout_seconds: int = DEFAULT_BUILD_TIMEOUT_SECONDS,
    ) -> dict[str, object]:
        from app.services.execution import build_execution_provider, ExecutionProviderError

        plan = await self.plan(project_id)
        if plan.status != WebsiteBuildStatus.PLANNED:
            result = {"status": "rejected", "plan": plan.model_dump(mode="json")}
            prior = await self.repository.get_execution_state(project_id) or WebsiteExecutionState(project_id=project_id)
            await self.repository.save_execution_state(prior.model_copy(update={"generation_version": plan.generation_version, "build_status": "rejected", "build_result": result}, deep=True))
            return result
        generation = await self.repository.get_generation(project_id)
        assert generation is not None
        try:
            provider = build_execution_provider()
            result = await provider.execute(project_id, generation, plan, self, install_timeout_seconds, build_timeout_seconds)
            result.setdefault("execution_provider", provider.name)
            prior = await self.repository.get_execution_state(project_id) or WebsiteExecutionState(project_id=project_id)
            await self.repository.save_execution_state(prior.model_copy(update={
                "generation_version": generation.version, "build_status": str(result.get("status")), "build_result": result
            }, deep=True))
            return result
        except ExecutionProviderError as exc:
            result = {"status": "unavailable", "reason": str(exc), "execution_provider": os.getenv("AWE_BUILD_EXECUTION_PROVIDER", "local-docker"), "plan": plan.model_dump(mode="json")}
            prior = await self.repository.get_execution_state(project_id) or WebsiteExecutionState(project_id=project_id)
            await self.repository.save_execution_state(prior.model_copy(update={"generation_version": generation.version, "build_status": "unavailable", "build_result": result}, deep=True))
            return result

    async def _execute_local_docker(
        self,
        project_id: UUID,
        install_timeout_seconds: int = DEFAULT_INSTALL_TIMEOUT_SECONDS,
        build_timeout_seconds: int = DEFAULT_BUILD_TIMEOUT_SECONDS,
    ) -> dict[str, object]:
        plan = await self.plan(project_id)

        if not 1 <= install_timeout_seconds <= MAX_TIMEOUT_SECONDS:
            raise ValueError(
                f"install_timeout_seconds must be between 1 and {MAX_TIMEOUT_SECONDS}."
            )
        if not 1 <= build_timeout_seconds <= MAX_TIMEOUT_SECONDS:
            raise ValueError(
                f"build_timeout_seconds must be between 1 and {MAX_TIMEOUT_SECONDS}."
            )

        if plan.status != WebsiteBuildStatus.PLANNED:
            return {
                "status": "rejected",
                "plan": plan.model_dump(mode="json"),
            }

        generation = await self.repository.get_generation(project_id)
        assert generation is not None

        if shutil.which("docker") is None:
            return {
                "status": "unavailable",
                "reason": "Docker is required for isolated execution.",
                "plan": plan.model_dump(mode="json"),
            }

        volume_name = create_workspace_volume("awe-build")

        try:
            populate_workspace_volume(
                volume_name,
                [(generated.path, generated.content) for generated in generation.files],
            )

            install = self._docker_run(
                volume_name,
                [
                    "npm",
                    "install",
                    "--ignore-scripts",
                    "--no-audit",
                    "--no-fund",
                    "--cache",
                    "/tmp/npm-cache",
                ],
                network="bridge",
                timeout=install_timeout_seconds,
            )

            if install.returncode != 0:
                return {
                    "status": "failed",
                    "phase": "dependency-install",
                    "stdout": install.stdout[-4000:],
                    "stderr": install.stderr[-4000:],
                    "isolation": "docker",
                    "workspace": "docker-volume",
                    "plan": plan.model_dump(mode="json"),
                }

            build = self._docker_run(
                volume_name,
                ["npm", "run", "build"],
                network="none",
                timeout=build_timeout_seconds,
            )

            return {
                "status": "succeeded" if build.returncode == 0 else "failed",
                "phase": "build",
                "stdout": build.stdout[-4000:],
                "stderr": build.stderr[-4000:],
                "isolation": "docker",
                "network_during_build": "none",
                "workspace": "docker-volume",
                "plan": plan.model_dump(mode="json"),
            }

        except ValueError as exc:
            return {
                "status": "rejected",
                "phase": "configuration",
                "stdout": "",
                "stderr": str(exc),
                "isolation": "docker",
                "workspace": "docker-volume",
                "plan": plan.model_dump(mode="json"),
            }
        except RuntimeError as exc:
            return {
                "status": "failed",
                "phase": "workspace",
                "stdout": "",
                "stderr": str(exc),
                "isolation": "docker",
                "workspace": "docker-volume",
                "plan": plan.model_dump(mode="json"),
            }

        finally:
            remove_workspace_volume(volume_name)

    @staticmethod
    def _docker_run(
        volume_name: str,
        command: list[str],
        network: str,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        docker_command = [
            "docker",
            "run",
            "--rm",
            "--network",
            network,
            "--cpus",
            "1",
            "--memory",
            "768m",
            "--pids-limit",
            "128",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,noexec",
            "-e",
            "NEXT_TELEMETRY_DISABLED=1",
            "-v",
            f"{volume_name}:/workspace:rw",
            "-w",
            "/workspace",
            "node:22-alpine",
            *command,
        ]

        try:
            return subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(
                docker_command,
                124,
                exc.stdout or "",
                f"Execution timed out after {timeout}s",
            )
