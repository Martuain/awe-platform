from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import UUID

from app.models import WebsitePreview, WebsitePreviewStatus
from app.services.build import ALLOWED_DEPENDENCIES, WebsiteBuildService
from app.store import Repository


class WebsitePreviewService:
    """Starts a disposable local preview from an already generated website."""

    _sessions: dict[str, WebsitePreview] = {}
    _workspaces: dict[str, tempfile.TemporaryDirectory[str]] = {}

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def start(self, project_id: UUID) -> WebsitePreview:
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError("generation")
        plan = await WebsiteBuildService(self.repository).plan(project_id)
        if plan.status.value != "planned":
            return WebsitePreview(project_id=project_id, generation_version=generation.version,
                                  status=WebsitePreviewStatus.FAILED, diagnostics=plan.diagnostics)
        if shutil.which("docker") is None:
            return WebsitePreview(project_id=project_id, generation_version=generation.version,
                                  status=WebsitePreviewStatus.UNAVAILABLE,
                                  diagnostics=["Docker is required for the disposable preview runtime."])

        key = str(project_id)
        await self.stop(project_id)
        holder = tempfile.TemporaryDirectory(prefix="awe-preview-")
        workspace = Path(holder.name)
        for generated in generation.files:
            target = workspace / generated.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(generated.content, encoding="utf-8")

        install = self._run(workspace, ["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund"], network="bridge")
        if install.returncode != 0:
            holder.cleanup()
            return WebsitePreview(project_id=project_id, generation_version=generation.version,
                                  status=WebsitePreviewStatus.FAILED,
                                  diagnostics=[install.stderr[-4000:] or "Dependency installation failed."])
        build = self._run(workspace, ["npm", "run", "build"], network="none")
        if build.returncode != 0:
            holder.cleanup()
            return WebsitePreview(project_id=project_id, generation_version=generation.version,
                                  status=WebsitePreviewStatus.FAILED,
                                  diagnostics=[build.stderr[-4000:] or "Preview build failed."])

        command = [
            "docker", "run", "-d", "--rm", "--network", "bridge",
            "--cpus", "1", "--memory", "768m", "--pids-limit", "128",
            "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec",
            "-e", "NEXT_TELEMETRY_DISABLED=1", "-p", "127.0.0.1::3000",
            "-v", f"{workspace}:/workspace:rw", "-w", "/workspace", "node:22-alpine",
            "npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000",
        ]
        started = subprocess.run(command, capture_output=True, text=True, check=False)
        if started.returncode != 0:
            holder.cleanup()
            return WebsitePreview(project_id=project_id, generation_version=generation.version,
                                  status=WebsitePreviewStatus.FAILED,
                                  diagnostics=[started.stderr[-4000:] or "Preview runtime failed to start."])
        container_id = started.stdout.strip()
        port = subprocess.run(["docker", "port", container_id, "3000/tcp"], capture_output=True, text=True, check=False)
        mapping = port.stdout.strip().splitlines()[0] if port.stdout.strip() else ""
        host_port = mapping.rsplit(":", 1)[-1] if mapping else ""
        if not host_port.isdigit():
            subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False)
            holder.cleanup()
            return WebsitePreview(project_id=project_id, generation_version=generation.version,
                                  status=WebsitePreviewStatus.FAILED,
                                  diagnostics=["Docker did not expose a preview port."])
        preview = WebsitePreview(project_id=project_id, generation_version=generation.version,
                                 status=WebsitePreviewStatus.STARTED,
                                 url=f"http://127.0.0.1:{host_port}", container_id=container_id)
        self._sessions[key] = preview
        self._workspaces[key] = holder
        return preview

    async def stop(self, project_id: UUID) -> WebsitePreview | None:
        key = str(project_id)
        existing = self._sessions.pop(key, None)
        if not existing:
            return None
        if existing.container_id:
            subprocess.run(["docker", "rm", "-f", existing.container_id], capture_output=True, check=False)
        holder = self._workspaces.pop(key, None)
        if holder:
            holder.cleanup()
        existing.status = WebsitePreviewStatus.STOPPED
        return existing

    @staticmethod
    def _run(workspace: Path, command: list[str], network: str) -> subprocess.CompletedProcess[str]:
        docker_command = [
            "docker", "run", "--rm", "--network", network,
            "--cpus", "1", "--memory", "768m", "--pids-limit", "128",
            "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec",
            "-e", "NEXT_TELEMETRY_DISABLED=1", "-v", f"{workspace}:/workspace:rw",
            "-w", "/workspace", "node:22-alpine", *command,
        ]
        return subprocess.run(docker_command, capture_output=True, text=True, timeout=120, check=False)
