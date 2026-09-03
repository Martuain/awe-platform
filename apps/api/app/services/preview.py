from __future__ import annotations

import shutil
import subprocess
from uuid import UUID

from app.models import WebsitePreview, WebsitePreviewStatus
from app.services.build import (
    DEFAULT_BUILD_TIMEOUT_SECONDS,
    DEFAULT_INSTALL_TIMEOUT_SECONDS,
    WebsiteBuildService,
)
from app.services.docker_workspace import (
    create_workspace_volume,
    populate_workspace_volume,
    remove_workspace_volume,
)
from app.store import Repository


class WebsitePreviewService:
    """Starts a disposable local preview from an already generated website."""

    _sessions: dict[str, WebsitePreview] = {}
    _workspaces: dict[str, str] = {}

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def start(self, project_id: UUID) -> WebsitePreview:
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError("generation")

        plan = await WebsiteBuildService(self.repository).plan(project_id)

        if plan.status.value != "planned":
            return WebsitePreview(
                project_id=project_id,
                generation_version=generation.version,
                status=WebsitePreviewStatus.FAILED,
                diagnostics=plan.diagnostics,
            )

        if shutil.which("docker") is None:
            return WebsitePreview(
                project_id=project_id,
                generation_version=generation.version,
                status=WebsitePreviewStatus.UNAVAILABLE,
                diagnostics=[
                    "Docker is required for the disposable preview runtime."
                ],
            )

        key = str(project_id)
        await self.stop(project_id)

        volume_name = create_workspace_volume("awe-preview")

        try:
            populate_workspace_volume(
                volume_name,
                [(generated.path, generated.content) for generated in generation.files],
            )

            install = self._run(
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
                timeout=DEFAULT_INSTALL_TIMEOUT_SECONDS,
            )

            if install.returncode != 0:
                remove_workspace_volume(volume_name)
                return WebsitePreview(
                    project_id=project_id,
                    generation_version=generation.version,
                    status=WebsitePreviewStatus.FAILED,
                    diagnostics=[
                        install.stderr[-4000:]
                        or "Dependency installation failed."
                    ],
                )

            build = self._run(
                volume_name,
                ["npm", "run", "build"],
                network="none",
                timeout=DEFAULT_BUILD_TIMEOUT_SECONDS,
            )

            if build.returncode != 0:
                remove_workspace_volume(volume_name)
                return WebsitePreview(
                    project_id=project_id,
                    generation_version=generation.version,
                    status=WebsitePreviewStatus.FAILED,
                    diagnostics=[
                        build.stderr[-4000:] or "Preview build failed."
                    ],
                )

            command = [
                "docker",
                "run",
                "-d",
                "--rm",
                "--network",
                "bridge",
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
                "-p",
                "127.0.0.1::3000",
                "-v",
                f"{volume_name}:/workspace:rw",
                "-w",
                "/workspace",
                "node:22-alpine",
                "npm",
                "run",
                "start",
                "--",
                "-H",
                "0.0.0.0",
                "-p",
                "3000",
            ]

            started = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if started.returncode != 0:
                remove_workspace_volume(volume_name)
                return WebsitePreview(
                    project_id=project_id,
                    generation_version=generation.version,
                    status=WebsitePreviewStatus.FAILED,
                    diagnostics=[
                        started.stderr[-4000:]
                        or "Preview runtime failed to start."
                    ],
                )

            container_id = started.stdout.strip()

            port = subprocess.run(
                ["docker", "port", container_id, "3000/tcp"],
                capture_output=True,
                text=True,
                check=False,
            )

            mapping = (
                port.stdout.strip().splitlines()[0]
                if port.stdout.strip()
                else ""
            )
            host_port = mapping.rsplit(":", 1)[-1] if mapping else ""

            if not host_port.isdigit():
                subprocess.run(
                    ["docker", "rm", "-f", container_id],
                    capture_output=True,
                    check=False,
                )
                remove_workspace_volume(volume_name)
                return WebsitePreview(
                    project_id=project_id,
                    generation_version=generation.version,
                    status=WebsitePreviewStatus.FAILED,
                    diagnostics=["Docker did not expose a preview port."],
                )

            preview = WebsitePreview(
                project_id=project_id,
                generation_version=generation.version,
                status=WebsitePreviewStatus.STARTED,
                url=f"http://127.0.0.1:{host_port}",
                container_id=container_id,
            )

            self._sessions[key] = preview
            self._workspaces[key] = volume_name

            return preview

        except subprocess.TimeoutExpired as exc:
            remove_workspace_volume(volume_name)
            phase = "dependency installation" if "install" in str(exc.cmd) else "production build"
            return WebsitePreview(
                project_id=project_id,
                generation_version=generation.version,
                status=WebsitePreviewStatus.FAILED,
                diagnostics=[f"Preview {phase} timed out after {exc.timeout}s."],
            )
        except (RuntimeError, ValueError) as exc:
            remove_workspace_volume(volume_name)
            return WebsitePreview(
                project_id=project_id,
                generation_version=generation.version,
                status=WebsitePreviewStatus.FAILED,
                diagnostics=[str(exc)],
            )

    async def stop(self, project_id: UUID) -> WebsitePreview | None:
        key = str(project_id)
        existing = self._sessions.pop(key, None)

        if not existing:
            volume_name = self._workspaces.pop(key, None)
            if volume_name:
                remove_workspace_volume(volume_name)
            return None

        if existing.container_id:
            subprocess.run(
                ["docker", "rm", "-f", existing.container_id],
                capture_output=True,
                check=False,
            )

        volume_name = self._workspaces.pop(key, None)
        if volume_name:
            remove_workspace_volume(volume_name)

        existing.status = WebsitePreviewStatus.STOPPED
        return existing

    @staticmethod
    def _run(
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

        return subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
