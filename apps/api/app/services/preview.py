from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
from uuid import UUID

from app.models import DeploymentLifecycleRole, DeploymentStatus, WebsiteContentStatus, WebsitePreview, WebsitePreviewStatus, WebsiteExecutionState
from app.services.build import (
    DEFAULT_BUILD_TIMEOUT_SECONDS,
    DEFAULT_INSTALL_TIMEOUT_SECONDS,
    WebsiteBuildService,
)
from app.services.docker_workspace import (
    create_workspace_volume,
    populate_workspace_volume,
    remove_workspace_volume,
    create_deployment_snapshot,
    deployment_snapshot_volume,
    restore_deployment_snapshot,
)
from app.store import Repository


class WebsitePreviewService:
    """Starts a disposable local preview from an already generated website."""

    _sessions: dict[str, WebsitePreview] = {}
    _workspaces: dict[str, str] = {}
    # Serialize live-deployment restore/reconciliation per deployment. The API
    # can receive concurrent navigation/asset requests for the same stable URL.
    _deployment_restore_locks: dict[str, asyncio.Lock] = {}

    @classmethod
    def _deployment_restore_lock(cls, deployment_id: UUID) -> asyncio.Lock:
        key = str(deployment_id)
        lock = cls._deployment_restore_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            cls._deployment_restore_locks[key] = lock
        return lock

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def _persist_preview_state(self, preview: WebsitePreview) -> WebsitePreview:
        prior = await self.repository.get_execution_state(preview.project_id) or WebsiteExecutionState(project_id=preview.project_id)
        await self.repository.save_execution_state(prior.model_copy(update={
            "generation_version": preview.generation_version,
            "preview_status": preview.status.value,
            "preview": preview,
        }, deep=True))
        return preview

    async def start(self, project_id: UUID, *, preserve_deployment: bool = True) -> WebsitePreview:
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError("generation")

        plan = await WebsiteBuildService(self.repository).plan(project_id)

        if plan.status.value != "planned":
            return await self._persist_preview_state(WebsitePreview(
                project_id=project_id, generation_version=generation.version,
                status=WebsitePreviewStatus.FAILED, diagnostics=plan.diagnostics,
            ))

        if shutil.which("docker") is None:
            return await self._persist_preview_state(WebsitePreview(
                project_id=project_id, generation_version=generation.version,
                status=WebsitePreviewStatus.UNAVAILABLE, diagnostics=["Docker is required for the disposable preview runtime."],
            ))

        # Docker/npm work is deliberately moved off FastAPI's event loop. A
        # preview may legitimately take several minutes on a cold cache; the
        # API must remain responsive while that work is in progress.
        published = await self.repository.list_content(project_id, status=WebsiteContentStatus.PUBLISHED)
        preview = await asyncio.to_thread(
            self._start_runtime, project_id, generation, published, preserve_deployment,
        )
        return await self._persist_preview_state(preview)

    @staticmethod
    def _published_content_fingerprint(items) -> str:
        """Stable fingerprint for the exact published CAP-035 content set."""
        rows = sorted(
            (
                str(item.page),
                str(item.key),
                str(item.content_type),
                str(item.value),
                str(item.version),
                str(item.published_at or ""),
            )
            for item in items
        )
        return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _start_runtime(self, project_id: UUID, generation, published_content, preserve_deployment: bool = True) -> WebsitePreview:
        key = str(project_id)
        content_fingerprint = self._published_content_fingerprint(published_content)

        # Starting preview is idempotent only when both the generated artifact
        # and the published CAP-035 content match. A generation number alone is
        # insufficient because content edits deliberately do not regenerate the
        # website.
        # prevents repeated button clicks/retries from creating orphaned
        # disposable containers.
        existing = self._sessions.get(key)
        if (
            existing
            and existing.status == WebsitePreviewStatus.STARTED
            and existing.generation_version == generation.version
            and existing.container_id
            and self._container_running(existing.container_id)
            and not self._container_is_deployment(existing.container_id)
        ):
            # CAP-035 content is dynamic. Keep the current-generation runtime
            # and update only awe-content.json instead of rebuilding because
            # the published-content fingerprint changed.
            self._write_content_file(existing.container_id, published_content)
            return existing

        self._stop_sync(project_id, preserve_deployment=preserve_deployment)
        volume_name = create_workspace_volume("awe-preview")

        try:
            populate_workspace_volume(
                volume_name,
                [(generated.path, generated.content) for generated in generation.files],
            )
            self._write_content_volume(volume_name, published_content)

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
                return self._failed(
                    project_id,
                    generation.version,
                    install.stderr[-4000:] or "Dependency installation failed.",
                )

            build = self._run(
                volume_name,
                ["npm", "run", "build"],
                network="none",
                timeout=DEFAULT_BUILD_TIMEOUT_SECONDS,
            )

            if build.returncode != 0:
                remove_workspace_volume(volume_name)
                return self._failed(
                    project_id,
                    generation.version,
                    build.stderr[-4000:] or "Preview build failed.",
                )

            command = [
                "docker", "run", "-d", "--rm", "--network", os.getenv("AWE_PREVIEW_NETWORK", "awe-platform"),
                "--label", "com.awe.preview=true",
                "--label", f"com.awe.project_id={project_id}",
                "--label", f"com.awe.generation_version={generation.version}",
                "--label", f"com.awe.content_fingerprint={content_fingerprint}",
                "--label", f"com.awe.preview.volume={volume_name}",
                "--cpus", "1", "--memory", "768m", "--pids-limit", "128",
                "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec",
                "-e", "NEXT_TELEMETRY_DISABLED=1",
                "-p", "127.0.0.1::3000",
                "-v", f"{volume_name}:/workspace:rw",
                "-w", "/workspace",
                "node:22-alpine", "npm", "run", "start", "--",
                "-H", "0.0.0.0", "-p", "3000",
            ]

            started = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            if started.returncode != 0:
                remove_workspace_volume(volume_name)
                return self._failed(
                    project_id,
                    generation.version,
                    started.stderr[-4000:] or "Preview runtime failed to start.",
                )

            container_id = started.stdout.strip()
            port = subprocess.run(
                ["docker", "port", container_id, "3000/tcp"],
                capture_output=True,
                text=True,
                check=False,
            )

            mapping = port.stdout.strip().splitlines()[0] if port.stdout.strip() else ""
            host_port = mapping.rsplit(":", 1)[-1] if mapping else ""

            if not host_port.isdigit():
                subprocess.run(
                    ["docker", "rm", "-f", container_id],
                    capture_output=True,
                    check=False,
                )
                remove_workspace_volume(volume_name)
                return self._failed(
                    project_id,
                    generation.version,
                    "Docker did not expose a preview port.",
                )

            # Do not expose a runtime to Studio until Next.js is actually
            # accepting HTTP requests. Docker reports the container as
            # running before the application is ready, which otherwise
            # creates a transient iframe/proxy 502 immediately after Start.
            if not self._wait_for_runtime_ready(container_id):
                subprocess.run(
                    ["docker", "rm", "-f", container_id],
                    capture_output=True,
                    check=False,
                )
                remove_workspace_volume(volume_name)
                return self._failed(
                    project_id,
                    generation.version,
                    "Preview runtime started but did not become HTTP-ready.",
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
            phase = (
                "dependency installation"
                if "install" in str(exc.cmd)
                else "production build"
            )
            return self._failed(
                project_id,
                generation.version,
                f"Preview {phase} timed out after {exc.timeout}s.",
            )
        except (RuntimeError, ValueError) as exc:
            remove_workspace_volume(volume_name)
            return self._failed(project_id, generation.version, str(exc))

    async def restore_deployment(self, project_id: UUID, deployment_id: UUID) -> WebsitePreview:
        """Restore one deployment snapshot, reusing an existing runtime when possible.

        Deployment runtimes are independent from disposable Preview runtimes. In
        particular, restoring a historical deployment must never stop the current
        live deployment. Concurrent requests for the same deployment are serialized
        so they converge on one runtime.
        """
        deployment = await self.repository.get_deployment(deployment_id)
        if not deployment or deployment.project_id != project_id:
            raise KeyError("deployment")
        if deployment.status not in {DeploymentStatus.DEPLOYED, DeploymentStatus.STOPPED}:
            raise KeyError("Deployment is not restorable")
        snapshot = deployment_snapshot_volume(str(deployment.deployment_id))
        if not await asyncio.to_thread(self._volume_exists, snapshot):
            raise KeyError("Deployment snapshot is unavailable")

        async with self._deployment_restore_lock(deployment_id):
            container_id = await asyncio.to_thread(
                self._deployment_runtime_for_deployment, project_id, deployment_id
            )
            if container_id:
                return await asyncio.to_thread(
                    self._preview_model_for_container, project_id, deployment.generation_version, container_id
                )
            # A deployment snapshot is immutable. Do not overlay current published
            # content here: that would silently turn a historical deployment into
            # the current draft/published website.
            return await asyncio.to_thread(
                self._restore_runtime_sync, project_id, deployment, snapshot
            )

    async def restore_latest_deployment(self, project_id: UUID) -> WebsitePreview:
        """Restore the project's canonical latest deployed version."""
        deployments = await self.repository.list_deployments(project_id)
        latest = next(
            (item for item in sorted(deployments, key=lambda x: x.created_at, reverse=True)
             if item.lifecycle_role == DeploymentLifecycleRole.CURRENT),
            None,
        )
        # Backward compatibility for repositories/fixtures created before
        # CAP-037: deployed rows without an explicit role still resolve to the
        # latest successful version. Persisted databases are backfilled by 0010.
        if latest is None:
            latest = next(
                (item for item in sorted(deployments, key=lambda x: x.created_at, reverse=True)
                 if item.status == DeploymentStatus.DEPLOYED),
                None,
            )
        if not latest:
            raise KeyError("No deployed deployment is available for this project")
        return await self.restore_deployment(project_id, latest.deployment_id)

    @staticmethod
    def _volume_exists(volume_name: str) -> bool:
        result = subprocess.run(["docker", "volume", "inspect", volume_name], capture_output=True, text=True, check=False, timeout=10)
        return result.returncode == 0

    def _restore_runtime_sync(self, project_id, deployment, snapshot) -> WebsitePreview:
        key = str(project_id)
        # Only replace an existing runtime for this exact deployment. Historical
        # deployment restores must coexist with the current live deployment.
        self._stop_deployment_runtime_sync(project_id, deployment.deployment_id)
        volume_name = restore_deployment_snapshot(snapshot)
        try:
            command = [
                "docker", "run", "-d", "--rm", "--network", os.getenv("AWE_PREVIEW_NETWORK", "awe-platform"),
                "--label", "com.awe.preview=true", "--label", f"com.awe.project_id={project_id}",
                "--label", f"com.awe.generation_version={deployment.generation_version}",
                "--label", f"com.awe.preview.volume={volume_name}", "--label", f"com.awe.deployment_id={deployment.deployment_id}",
                "--cpus", "1", "--memory", "768m", "--pids-limit", "128",
                "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec", "-e", "NEXT_TELEMETRY_DISABLED=1",
                "-p", "127.0.0.1::3000", "-v", f"{volume_name}:/workspace:rw", "-w", "/workspace",
                "node:22-alpine", "npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000",
            ]
            started = subprocess.run(command, capture_output=True, text=True, check=False)
            if started.returncode != 0:
                raise RuntimeError(started.stderr[-4000:] or "Restored deployment runtime failed to start.")
            container_id = started.stdout.strip()
            port = subprocess.run(["docker", "port", container_id, "3000/tcp"], capture_output=True, text=True, check=False)
            mapping = port.stdout.strip().splitlines()[0] if port.stdout.strip() else ""
            host_port = mapping.rsplit(":", 1)[-1] if mapping else ""
            if not host_port.isdigit():
                subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False)
                raise RuntimeError("Docker did not expose a restored deployment port.")
            if not self._wait_for_runtime_ready(container_id):
                subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False)
                raise RuntimeError("Restored deployment runtime did not become HTTP-ready.")
            preview = WebsitePreview(project_id=project_id, generation_version=deployment.generation_version,
                status=WebsitePreviewStatus.STARTED, url=f"http://127.0.0.1:{host_port}", container_id=container_id)
            self._sessions[key] = preview
            self._workspaces[key] = volume_name
            return preview
        except Exception:
            remove_workspace_volume(volume_name)
            raise

    @staticmethod
    def _content_payload(items) -> str:
        payload: dict[str, dict[str, str]] = {}
        for item in items:
            payload.setdefault(item.page, {})[item.key] = item.value
        return json.dumps(payload, ensure_ascii=False)

    @classmethod
    def _write_content_volume(cls, volume_name: str, items) -> None:
        payload = cls._content_payload(items).encode("utf-8")
        result = subprocess.run(
            ["docker", "run", "--rm", "-i", "-v", f"{volume_name}:/workspace:rw", "alpine:3.22", "sh", "-c", "cat > /workspace/awe-content.json"],
            input=payload, capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("Failed to synchronize website content into the preview workspace.")

    @classmethod
    def _write_content_file(cls, container_id: str, items) -> None:
        payload = cls._content_payload(items).encode("utf-8")
        result = subprocess.run(
            ["docker", "exec", "-i", container_id, "sh", "-c", "cat > /workspace/awe-content.json"],
            input=payload, capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("Failed to synchronize website content into the live preview.")

    @classmethod
    async def sync_published_content(cls, repository: Repository, project_id: UUID) -> bool:
        items = await repository.list_content(project_id, status=WebsiteContentStatus.PUBLISHED)
        return await asyncio.to_thread(cls._sync_published_content_sync, project_id, items)

    @classmethod
    def _sync_published_content_sync(cls, project_id: UUID, items) -> bool:
        container_ids = cls._preview_container_ids(project_id)
        if not container_ids:
            return False
        for container_id in container_ids:
            inspect = subprocess.run(
                ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.deployment_id"}}', container_id],
                capture_output=True, text=True, check=False, timeout=10,
            )
            if inspect.returncode == 0 and inspect.stdout.strip():
                continue
            try:
                cls._write_content_file(container_id, items)
            except RuntimeError:
                return False
        return True

    async def refresh_published_content(self, project_id: UUID) -> WebsitePreview:
        """Make Live Preview reflect the latest published content without rebuilding unnecessarily.

        CAP-035 content is read dynamically from /workspace/awe-content.json, so a
        healthy Preview runtime for the current generation can be updated in-place.
        If no such runtime exists, prefer cloning the latest compatible deployment
        snapshot (already installed/built) and overlay the current published content.
        Only fall back to npm install + build when no compatible built snapshot exists.
        """
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError("generation")
        plan = await WebsiteBuildService(self.repository).plan(project_id)
        if plan.status.value != "planned":
            return await self._persist_preview_state(WebsitePreview(
                project_id=project_id, generation_version=generation.version,
                status=WebsitePreviewStatus.FAILED, diagnostics=plan.diagnostics,
            ))
        if shutil.which("docker") is None:
            return await self._persist_preview_state(WebsitePreview(
                project_id=project_id, generation_version=generation.version,
                status=WebsitePreviewStatus.UNAVAILABLE, diagnostics=["Docker is required for the disposable preview runtime."],
            ))
        published = await self.repository.list_content(
            project_id, status=WebsiteContentStatus.PUBLISHED
        )


        # Fast path: keep the current Preview process and replace only dynamic
        # content. This avoids minutes of npm install/build work on every publish.

        container_id = await asyncio.to_thread(
            self._current_generation_preview_container, project_id, generation.version
        )


        if container_id:
            try:
                await asyncio.to_thread(self._write_content_file, container_id, published)
                preview = await asyncio.to_thread(
                    self._preview_model_for_container, project_id, generation.version, container_id
                )
                return await self._persist_preview_state(preview)
            except (RuntimeError, ValueError):
                # The container may have disappeared between selection and sync.
                # Fall through to a fresh runtime rather than surfacing a transient
                # synchronization error to the iframe.
                pass


        # Cold fast path: a deployment snapshot already contains node_modules and
        # the production build. Clone it into an independent Preview workspace,
        # overlay the current CAP-035 content, and start it without rebuilding.
        deployments = await self.repository.list_deployments(project_id)
        compatible = next(
            (item for item in sorted(deployments, key=lambda x: x.created_at, reverse=True)
             if item.status in {DeploymentStatus.DEPLOYED, DeploymentStatus.STOPPED}
             and item.generation_version == generation.version),
            None,
        )
        if compatible:
            snapshot = deployment_snapshot_volume(str(compatible.deployment_id))
            if await asyncio.to_thread(self._volume_exists, snapshot):
                try:
                    preview = await asyncio.to_thread(
                        self._restore_preview_snapshot_sync, project_id, generation.version, snapshot, published,
                    )
                    return await self._persist_preview_state(preview)
                except (RuntimeError, ValueError):
                    pass

        # No reusable built artifact exists (for example, generation changed since
        # the last deployment). Build once from the current generated files.
        return await asyncio.to_thread(
            self._start_runtime, project_id, generation, published, True
        )

    @classmethod
    def _current_generation_preview_container(cls, project_id: UUID, generation_version: int) -> str | None:
        for container_id in cls._preview_container_ids(project_id):
            if not cls._container_running(container_id) or cls._container_is_deployment(container_id):
                continue
            inspected = subprocess.run(
                ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.generation_version"}}', container_id],
                capture_output=True, text=True, check=False, timeout=10,
            )
            if inspected.returncode == 0 and inspected.stdout.strip() == str(generation_version):
                return container_id
        return None

    @classmethod
    def _preview_model_for_container(cls, project_id: UUID, generation_version: int, container_id: str) -> WebsitePreview:
        port = subprocess.run(
            ["docker", "port", container_id, "3000/tcp"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        mapping = port.stdout.strip().splitlines()[0] if port.stdout.strip() else ""
        host_port = mapping.rsplit(":", 1)[-1] if mapping else ""
        if port.returncode != 0 or not host_port.isdigit():
            raise RuntimeError("Docker did not expose a preview port.")
        return WebsitePreview(
            project_id=project_id, generation_version=generation_version,
            status=WebsitePreviewStatus.STARTED,
            url=f"http://127.0.0.1:{host_port}", container_id=container_id,
        )

    def _restore_preview_snapshot_sync(self, project_id: UUID, generation_version: int, snapshot: str, published_content) -> WebsitePreview:
        key = str(project_id)
        self._stop_sync(project_id, preserve_deployment=True)
        volume_name = restore_deployment_snapshot(snapshot, prefix="awe-preview-clone")
        try:
            self._write_content_volume(volume_name, published_content)
            fingerprint = self._published_content_fingerprint(published_content)
            command = [
                "docker", "run", "-d", "--rm", "--network", os.getenv("AWE_PREVIEW_NETWORK", "awe-platform"),
                "--label", "com.awe.preview=true",
                "--label", f"com.awe.project_id={project_id}",
                "--label", f"com.awe.generation_version={generation_version}",
                "--label", f"com.awe.content_fingerprint={fingerprint}",
                "--label", f"com.awe.preview.volume={volume_name}",
                "--cpus", "1", "--memory", "768m", "--pids-limit", "128",
                "--read-only", "--tmpfs", "/tmp:rw,nosuid,nodev,noexec",
                "-e", "NEXT_TELEMETRY_DISABLED=1",
                "-p", "127.0.0.1::3000",
                "-v", f"{volume_name}:/workspace:rw",
                "-w", "/workspace",
                "node:22-alpine", "npm", "run", "start", "--",
                "-H", "0.0.0.0", "-p", "3000",
            ]
            started = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
            if started.returncode != 0:
                raise RuntimeError(started.stderr[-4000:] or "Preview runtime failed to start from deployment snapshot.")
            container_id = started.stdout.strip()
            if not self._wait_for_runtime_ready(container_id, timeout_seconds=30.0):
                subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False, timeout=10)
                raise RuntimeError("Preview runtime restored from deployment snapshot did not become HTTP-ready.")
            preview = self._preview_model_for_container(project_id, generation_version, container_id)
            self._sessions[key] = preview
            self._workspaces[key] = volume_name
            return preview
        except Exception:
            remove_workspace_volume(volume_name)
            raise

    @staticmethod
    def _failed(
        project_id: UUID,
        generation_version: int,
        diagnostic: str,
    ) -> WebsitePreview:
        return WebsitePreview(
            project_id=project_id,
            generation_version=generation_version,
            status=WebsitePreviewStatus.FAILED,
            diagnostics=[diagnostic],
        )

    @staticmethod
    def _wait_for_runtime_ready(container_id: str, timeout_seconds: float = 15.0) -> bool:
        """Wait until the private runtime accepts HTTP requests."""
        import time
        import httpx

        deadline = time.monotonic() + timeout_seconds
        attempts = 0

        while time.monotonic() < deadline:
            attempts += 1

            port = subprocess.run(
                ["docker", "port", container_id, "3000/tcp"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            mapping = port.stdout.strip().splitlines()[0] if port.stdout.strip() else ""
            host_port = mapping.rsplit(":", 1)[-1] if mapping else ""

            if host_port.isdigit():
                try:
                    with httpx.Client(timeout=1.5, follow_redirects=False) as client:
                        response = client.get(
                            f"http://127.0.0.1:{host_port}/"
                        )
                    if response.status_code < 500:
                        return True
                except httpx.HTTPError:
                    pass

            time.sleep(0.25)

        return False

    @staticmethod
    def _container_running(container_id: str) -> bool:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_id],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip().lower() == "true"

    @staticmethod
    def _preview_container_ids(project_id: UUID | None = None) -> list[str]:
        command = ["docker", "ps", "-aq", "--filter", "label=com.awe.preview=true"]
        if project_id is not None:
            command.extend(["--filter", f"label=com.awe.project_id={project_id}"])
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    @classmethod
    def _legacy_preview_container_ids(cls) -> list[str]:
        """Find pre-label CAP-009 runtimes by inspecting containers on the preview network."""
        network = os.getenv("AWE_PREVIEW_NETWORK", "awe-platform")
        result = subprocess.run(
            ["docker", "ps", "-aq", "--filter", f"network={network}"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        if result.returncode != 0:
            return []

        ids: list[str] = []
        for container_id in result.stdout.splitlines():
            container_id = container_id.strip()
            if not container_id:
                continue
            inspect = subprocess.run(
                ["docker", "inspect", "--format",
                 "{{json .Config.Image}}\t{{json .Config.Cmd}}\t{{json .Config.Entrypoint}}",
                 container_id],
                capture_output=True, text=True, check=False, timeout=10,
            )
            if inspect.returncode != 0:
                continue
            parts = inspect.stdout.strip().split("\t")
            if len(parts) != 3:
                continue
            try:
                image = json.loads(parts[0])
                command = json.loads(parts[1])
                entrypoint = json.loads(parts[2])
            except json.JSONDecodeError:
                continue

            image_text = str(image or "").lower()
            full_command = " ".join(str(part) for part in (entrypoint or []) + (command or [])).lower()
            if ("node:22-alpine" in image_text
                    and "npm" in full_command
                    and "run" in full_command
                    and "start" in full_command
                    and "3000" in full_command):
                ids.append(container_id)
        return ids

    @classmethod
    def cleanup_orphaned_runtimes(cls, preserved_project_ids: set[str] | None = None) -> None:
        """Remove orphaned preview runtimes, preserving projects with a live deployment.

        Docker is an optional runtime dependency for the API process. The API must
        still start when Docker is unavailable; Preview/Build endpoints report the
        unavailable runtime explicitly when they are invoked.
        """
        if shutil.which("docker") is None:
            return
        preserved_project_ids = preserved_project_ids or set()
        container_ids = set(cls._preview_container_ids())
        container_ids.update(cls._legacy_preview_container_ids())
        for container_id in container_ids:
            if preserved_project_ids:
                inspect = subprocess.run(
                    ["docker", "inspect", "-f", "{{index .Config.Labels \"com.awe.project_id\"}}" , container_id],
                    capture_output=True, text=True, check=False, timeout=10,
                )
                if inspect.returncode == 0 and inspect.stdout.strip() in preserved_project_ids:
                    continue
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                capture_output=True, check=False, timeout=10,
            )

    @staticmethod
    def _container_is_deployment(container_id: str) -> bool:
        result = subprocess.run(
            ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.deployment_id"}}', container_id],
            capture_output=True, text=True, check=False, timeout=10,
        )
        return result.returncode == 0 and bool(result.stdout.strip())

    @classmethod
    def _deployment_runtime_for_deployment(cls, project_id: UUID, deployment_id: UUID) -> str | None:
        """Return one ready runtime for an exact deployment and retire duplicates."""
        ready: list[str] = []
        matching: list[str] = []
        for container_id in cls._preview_container_ids(project_id):
            if not container_id or not cls._container_running(container_id):
                continue
            inspect = subprocess.run(
                ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.deployment_id"}}', container_id],
                capture_output=True, text=True, check=False, timeout=10,
            )
            if inspect.returncode != 0 or inspect.stdout.strip() != str(deployment_id):
                continue
            matching.append(container_id)
            if cls._wait_for_runtime_ready(container_id, timeout_seconds=3.0):
                ready.append(container_id)

        if not ready:
            return None

        keeper = ready[0]
        # A previous race may already have produced multiple runtimes for the same
        # deployment. Keep one ready runtime and retire every redundant match.
        for container_id in matching:
            if container_id == keeper:
                continue
            inspect = subprocess.run(
                ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.preview.volume"}}', container_id],
                capture_output=True, text=True, check=False, timeout=10,
            )
            volume_name = inspect.stdout.strip() if inspect.returncode == 0 else ""
            subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False, timeout=10)
            if volume_name:
                remove_workspace_volume(volume_name)
        return keeper

    @classmethod
    def _deployment_runtime_for_project(cls, project_id: UUID) -> str | None:
        """Return the currently running local deployment runtime, if any."""
        result = subprocess.run(
            [
                "docker", "ps", "-q",
                "--filter", "label=com.awe.preview=true",
                "--filter", f"label=com.awe.project_id={project_id}",
                "--filter", "label=com.awe.deployment_id",
            ],
            capture_output=True, text=True, check=False, timeout=10,
        )
        if result.returncode != 0:
            return None
        for container_id in result.stdout.splitlines():
            container_id = container_id.strip()
            if not container_id or not cls._container_running(container_id):
                continue
            # A Docker container can remain in Running state while the
            # Next.js process inside it is dead/unready. Only advertise a
            # deployment runtime once it is actually reachable from the API
            # over the private preview network. If it is not reachable, the
            # caller will restore the immutable snapshot instead.
            if cls._wait_for_runtime_ready(container_id, timeout_seconds=3.0):
                return container_id
        return None

    @staticmethod
    def _container_content_fingerprint(container_id: str) -> str | None:
        result = subprocess.run(
            ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.content_fingerprint"}}', container_id],
            capture_output=True, text=True, check=False, timeout=10,
        )
        if result.returncode != 0:
            return None
        value = result.stdout.strip()
        return value or None

    @classmethod
    def _current_preview_container(cls, project_id: UUID, generation_version: int, content_fingerprint: str) -> str | None:
        """Find a preview runtime that matches the current artifact AND content."""
        for container_id in cls._preview_container_ids(project_id):
            if not cls._container_running(container_id) or cls._container_is_deployment(container_id):
                continue
            inspect = subprocess.run(
                ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.generation_version"}}\t{{index .Config.Labels "com.awe.content_fingerprint"}}', container_id],
                capture_output=True, text=True, check=False, timeout=10,
            )
            if inspect.returncode != 0:
                continue
            version, _, fingerprint = inspect.stdout.strip().partition("\t")
            if version == str(generation_version) and fingerprint == content_fingerprint:
                return container_id
        return None

    @classmethod
    def _runtime_for_project(cls, project_id: UUID) -> str | None:
        """Return only an active non-deployment preview runtime."""
        for container_id in cls._preview_container_ids(project_id):
            if not cls._container_running(container_id):
                continue
            inspect = subprocess.run(
                ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.deployment_id"}}', container_id],
                capture_output=True, text=True, check=False, timeout=10,
            )
            if inspect.returncode == 0 and inspect.stdout.strip():
                continue
            return container_id
        return None

    @classmethod
    def _runtime_for_port(cls, port: int) -> str | None:
        for container_id in cls._preview_container_ids():
            if not cls._container_running(container_id):
                continue
            result = subprocess.run(
                ["docker", "port", container_id, "3000/tcp"],
                capture_output=True, text=True, check=False, timeout=10,
            )
            for mapping in result.stdout.splitlines():
                if mapping.rsplit(":", 1)[-1].strip() == str(port):
                    return container_id
        return None

    def _stop_sync(self, project_id: UUID, *, preserve_deployment: bool = False) -> WebsitePreview | None:
        key = str(project_id)
        existing = self._sessions.pop(key, None)

        # Labels are authoritative because the API process may have restarted
        # and therefore lost its in-memory session registry.
        for container_id in self._preview_container_ids(project_id):
            if preserve_deployment:
                inspect = subprocess.run(
                    ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.deployment_id"}}', container_id],
                    capture_output=True, text=True, check=False, timeout=10,
                )
                if inspect.returncode == 0 and inspect.stdout.strip():
                    continue
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                capture_output=True,
                check=False,
                timeout=10,
            )

        volume_name = self._workspaces.pop(key, None)
        if volume_name:
            deployment_volumes: set[str] = set()
            if preserve_deployment:
                for deployment_container in self._preview_container_ids(project_id):
                    inspect = subprocess.run(
                        ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.deployment_id"}}\t{{index .Config.Labels "com.awe.preview.volume"}}', deployment_container],
                        capture_output=True, text=True, check=False, timeout=10,
                    )
                    if inspect.returncode == 0:
                        parts = inspect.stdout.strip().split("\t", 1)
                        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                            deployment_volumes.add(parts[1].strip())
            if volume_name not in deployment_volumes:
                remove_workspace_volume(volume_name)
            else:
                # Keep the deployment volume alive even though the in-memory
                # preview workspace slot is being released for a separate
                # disposable Preview runtime.
                self._workspaces.pop(key, None)

        if existing:
            existing.status = WebsitePreviewStatus.STOPPED
        return existing

    async def proxy_deployment_request(
        self,
        project_id: UUID,
        request,
        *,
        request_prefix: str = "",
        public_prefix: str | None = None,
    ):
        """Proxy a deployment through a stable, deployment-aware namespace.

        ``request_prefix`` identifies the internal API route being proxied.
        ``public_prefix`` identifies the stable Studio-facing namespace used
        when rewriting runtime-relative links. Keeping these explicit prevents
        routing mechanics from becoming part of deployment identity.
        """
        from urllib.parse import parse_qs, urlparse

        requested = parse_qs(urlparse(str(getattr(request, "url", ""))).query).get("deployment_id", [None])[0]
        explicit_deployment = bool(requested)
        requested_id = None
        if requested:
            try:
                requested_id = UUID(requested)
            except ValueError as exc:
                raise KeyError("Invalid deployment_id") from exc

        request_prefix = request_prefix or f"/api/v1/website-preview/deployment-proxy/{project_id}"
        legacy_public_prefix = public_prefix is None
        if public_prefix is None:
            public_prefix = f"/api/live-preview/deployment/{project_id}"

        # No deployment_id means the canonical current live deployment. Resolve
        # it from the database first; never choose an arbitrary Docker runtime.
        if requested_id is None:
            deployments = await self.repository.list_deployments(project_id)
            deployment = next(
                (item for item in deployments
                 if item.lifecycle_role == DeploymentLifecycleRole.CURRENT
                 and item.status == DeploymentStatus.DEPLOYED),
                None,
            )
            if not deployment:
                raise KeyError("No deployed deployment is available for this project")
            requested_id = deployment.deployment_id

        deployment = await self.repository.get_deployment(requested_id)
        if not deployment or deployment.project_id != project_id:
            raise KeyError("deployment")
        if deployment.status not in {DeploymentStatus.DEPLOYED, DeploymentStatus.STOPPED}:
            raise KeyError("Deployment is not restorable")

        async with self._deployment_restore_lock(requested_id):
            container_id = await asyncio.to_thread(
                self._deployment_runtime_for_deployment, project_id, requested_id
            )
            if not container_id:
                snapshot = deployment_snapshot_volume(str(requested_id))
                if not await asyncio.to_thread(self._volume_exists, snapshot):
                    raise KeyError("Deployment snapshot is unavailable")
                preview = await asyncio.to_thread(
                    self._restore_runtime_sync, project_id, deployment, snapshot
                )
                container_id = preview.container_id
            if not container_id:
                raise KeyError("Deployment runtime could not be restored")

            # The host port is disposable. Persist the runtime identity and current
            # endpoint whenever reconciliation selects/restores a runtime. This keeps
            # deployment metadata truthful while the Studio still uses the stable API
            # proxy URL for navigation.
            preview = await asyncio.to_thread(
                self._preview_model_for_container, project_id, deployment.generation_version, container_id
            )
            deployment.runtime_id = preview.container_id
            deployment.url = preview.url
            await self.repository.update_deployment(deployment)

        # Browser-facing routing is supplied by the caller. The canonical
        # stable live route keeps CURRENT navigation on /api/live/<project>/...,
        # while an explicitly selected historical deployment is pinned under
        # /api/live/<project>/deployment/<deployment>/.... Legacy callers that
        # do not supply a public prefix retain the FIX-31 live-preview namespace.
        if legacy_public_prefix:
            deployment_public_prefix = f"/api/live-preview/deployment/{project_id}/{requested_id}"
        elif explicit_deployment:
            deployment_public_prefix = f"{public_prefix.rstrip('/')}/deployment/{requested_id}"
        else:
            deployment_public_prefix = public_prefix.rstrip("/")
        try:
            return await self.proxy_container_request(
                container_id, request, deployment_public_prefix, request_prefix
            )
        except RuntimeError:
            # Reconcile once if the selected runtime dies between readiness and proxy.
            async with self._deployment_restore_lock(requested_id):
                preview = await asyncio.to_thread(
                    self._restore_runtime_sync, project_id, deployment,
                    deployment_snapshot_volume(str(requested_id)),
                )
                if not preview.container_id:
                    raise KeyError("Deployment runtime could not be restored")
                deployment.runtime_id = preview.container_id
                deployment.url = preview.url
                await self.repository.update_deployment(deployment)
                container_id = preview.container_id
            return await self.proxy_container_request(
                container_id,
                request,
                deployment_public_prefix,
                request_prefix,
            )

    async def proxy_preview_project_request(self, project_id: UUID, request):
        """Proxy the current-generation Preview and self-heal transient runtime races."""
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError("generation")
        published = await self.repository.list_content(
            project_id, status=WebsiteContentStatus.PUBLISHED
        )
        container_id = await asyncio.to_thread(
            self._current_generation_preview_container, project_id, generation.version
        )
        if not container_id:
            preview = await self.refresh_published_content(project_id)
            if preview.status != WebsitePreviewStatus.STARTED:
                raise RuntimeError(
                    "Live preview runtime could not be started: "
                    + " ".join(preview.diagnostics)
                )
            container_id = preview.container_id
        if not container_id:
            raise KeyError("Live preview runtime not found")

        # Synchronize content immediately before serving. If the selected runtime
        # disappears during a concurrent refresh, recover once instead of exposing
        # the transient docker-exec failure inside the iframe.
        try:
            await asyncio.to_thread(self._write_content_file, container_id, published)
        except RuntimeError:
            preview = await self.refresh_published_content(project_id)
            if preview.status != WebsitePreviewStatus.STARTED or not preview.container_id:
                raise RuntimeError("Failed to synchronize website content into the live preview.")
            container_id = preview.container_id
            await asyncio.to_thread(self._write_content_file, container_id, published)

        return await self.proxy_container_request(
            container_id, request,
            f"/api/live-preview/preview/{project_id}",
            f"/api/v1/website-preview/preview-proxy/{project_id}",
        )

    async def proxy_request(self, port: int, request):
        """Proxy an active disposable runtime through the private API network."""
        container_id = self._runtime_for_port(port)
        if not container_id:
            raise KeyError("Live preview runtime not found")
        return await self.proxy_container_request(
            container_id, request, f"/api/live-preview/{port}", f"/api/v1/website-preview/proxy/{port}"
        )

    async def proxy_container_request(self, container_id: str, request, public_prefix: str, request_prefix: str):
        network_name = os.getenv("AWE_PREVIEW_NETWORK", "awe-platform")
        inspected = subprocess.run(
            ["docker", "inspect", "-f", "{{json .NetworkSettings.Networks}}", container_id],
            capture_output=True, text=True, check=False, timeout=10,
        )
        if inspected.returncode != 0:
            raise RuntimeError("Unable to inspect live preview runtime")
        try:
            networks = json.loads(inspected.stdout)
            ip_address = networks[network_name]["IPAddress"]
        except (ValueError, KeyError, TypeError):
            raise RuntimeError(f"Live preview runtime is not attached to network '{network_name}'")
        if not ip_address:
            raise RuntimeError("Live preview runtime has no reachable network address")

        request_path = request.url.path
        # Strip the API proxy route, leaving the generated runtime path.
        suffix = request_path.split(request_prefix, 1)[-1] or "/"
        target = f"http://{ip_address}:3000{suffix}"
        if request.url.query:
            target = f"{target}?{request.url.query}"

        import httpx
        from fastapi.responses import Response
        body = await request.body()
        headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "connection", "content-length"}}
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
                upstream = await client.request(request.method, target, headers=headers, content=body or None)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Live preview runtime is unreachable: {exc}") from exc

        response_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in {"content-length", "content-encoding", "transfer-encoding", "connection", "x-frame-options", "content-security-policy"}}
        location = response_headers.get("location")
        if location:
            from urllib.parse import urljoin, urlparse
            absolute = urljoin(target, location)
            parsed = urlparse(absolute)
            if parsed.hostname == ip_address and parsed.port == 3000:
                proxied_path = parsed.path.lstrip("/")
                response_headers["location"] = f"{public_prefix}/{proxied_path}" + (f"?{parsed.query}" if parsed.query else "")

        content = upstream.content
        if "text/html" in upstream.headers.get("content-type", ""):
            html = content.decode(upstream.encoding or "utf-8", errors="replace")
            # Rewrite both rendered HTML attributes and Next.js serialized
            # navigation payloads. The latter matters because hydration can
            # replace server-rendered anchor attributes with the href stored in
            # the RSC payload; rewriting only the visible <a> tags therefore
            # still allowed V7 navigation to fall back to the canonical V8.
            html = re.sub(
                r"""((?:src|href|action)=["'])/(?!/)""",
                rf"\1{public_prefix}/",
                html,
                flags=re.I,
            )
            html = re.sub(
                r"""((?:["'])(?:href|src|action)(?:["'])\s*:\s*["'])/(?!/)""",
                rf"\1{public_prefix}/",
                html,
                flags=re.I,
            )
            html = re.sub(r"""(url\(["'])/(?!/)""", rf"\1{public_prefix}/", html, flags=re.I)
            content = html.encode("utf-8")
        return Response(content=content, status_code=upstream.status_code, headers=response_headers)

    async def reconcile_deployment_runtimes(self, project_id: UUID) -> None:
        """Keep only current + immediately previous deployment runtimes warm.

        Snapshot-backed deployments remain restorable after their runtime is
        stopped. Docker labels are authoritative so reconciliation survives API
        process restarts.
        """
        deployments = await self.repository.list_deployments(project_id)
        ordered = sorted(
            [d for d in deployments if d.status in {DeploymentStatus.DEPLOYED, DeploymentStatus.STOPPED}],
            key=lambda d: d.version,
            reverse=True,
        )
        keep_ids = {
            d.deployment_id for d in ordered
            if d.lifecycle_role in {DeploymentLifecycleRole.CURRENT, DeploymentLifecycleRole.PREVIOUS}
        }
        # Retain at most the canonical current and one previous runtime.
        for deployment in ordered:
            if deployment.deployment_id in keep_ids:
                continue
            await self.stop_deployment_runtime(project_id, deployment.deployment_id)
            deployment.status = DeploymentStatus.STOPPED
            deployment.url = None
            deployment.runtime_id = None
            deployment.stopped_at = datetime.now(timezone.utc)
            await self.repository.update_deployment(deployment)

    async def activate_deployment_runtime_from_snapshot(self, project_id: UUID, deployment, snapshot: str) -> WebsitePreview:
        """Start the immutable deployment runtime from its persisted snapshot.

        Docker does not support mutating container labels after creation, so the
        deployment identifier is attached by ``_restore_runtime_sync`` when the
        replacement runtime is created with ``docker run --label``.
        """
        return await asyncio.to_thread(self._restore_runtime_sync, project_id, deployment, snapshot)

    async def stop_deployment_runtime(self, project_id: UUID, deployment_id: UUID | None = None) -> WebsitePreview | None:
        """Stop one local deployment runtime without touching disposable Preview.

        ``deployment_id`` is optional for backwards compatibility; when omitted,
        all deployment runtimes for the project are stopped (the explicit Stop
        deployment operation uses this legacy-compatible behavior).
        """
        return await asyncio.to_thread(self._stop_deployment_runtime_sync, project_id, deployment_id)

    @classmethod
    def _stop_deployment_runtime_sync(cls, project_id: UUID, deployment_id: UUID | None = None) -> WebsitePreview | None:
        deployment_containers = []
        for container_id in cls._preview_container_ids(project_id):
            inspect = subprocess.run(
                ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.deployment_id"}}', container_id],
                capture_output=True, text=True, check=False, timeout=10,
            )
            if inspect.returncode != 0:
                continue
            label = inspect.stdout.strip()
            if label and (deployment_id is None or label == str(deployment_id)):
                deployment_containers.append(container_id)
        for container_id in deployment_containers:
            inspect = subprocess.run(
                ["docker", "inspect", "-f", '{{index .Config.Labels "com.awe.preview.volume"}}', container_id],
                capture_output=True, text=True, check=False, timeout=10,
            )
            volume_name = inspect.stdout.strip() if inspect.returncode == 0 else ""
            subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=False, timeout=10)
            if volume_name:
                remove_workspace_volume(volume_name)
        return None

    async def stop(self, project_id: UUID) -> WebsitePreview | None:
        # Docker cleanup is blocking too, so keep it off the event loop.
        return await asyncio.to_thread(self._stop_sync, project_id, preserve_deployment=True)

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
