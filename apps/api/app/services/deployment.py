from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from app.models import DeploymentLifecycleRole, DeploymentStatus, WebsiteContentStatus, WebsiteDeployment
from app.services.preview import WebsitePreviewService
from app.services.docker_workspace import create_deployment_snapshot
from app.store import Repository


class DeploymentProvider:
    name = "local"

    async def deploy(self, project_id: UUID, repository: Repository) -> WebsiteDeployment:
        raise NotImplementedError

    async def stop(self, deployment: WebsiteDeployment, repository: Repository) -> WebsiteDeployment:
        raise NotImplementedError


class HostedDeploymentProvider(DeploymentProvider):
    """Provider-neutral HTTP bridge for a separately scalable deployment service."""
    name = "hosted"

    async def deploy(self, project_id: UUID, repository: Repository) -> WebsiteDeployment:
        generation = await repository.get_generation(project_id)
        if not generation:
            raise KeyError("generation")
        if generation.status.value != "validated":
            raise ValueError("Website Generation must be validated before deployment.")
        endpoint = os.getenv("AWE_DEPLOYMENT_PROVIDER_URL", "").strip()
        if not endpoint:
            raise ValueError("AWE_DEPLOYMENT_PROVIDER_URL is required for hosted deployment")
        deployment = WebsiteDeployment(project_id=project_id, generation_version=generation.version, version=max((d.version for d in await repository.list_deployments(project_id)), default=0)+1, status=DeploymentStatus.DEPLOYING, provider=self.name)
        await repository.create_deployment(deployment)
        payload = {"project_id": str(project_id), "generation": generation.model_dump(mode="json"), "deployment_id": str(deployment.deployment_id), "version": deployment.version}
        token = os.getenv("AWE_DEPLOYMENT_PROVIDER_TOKEN", "").strip()
        request = Request(endpoint.rstrip("/") + "/deploy", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json", **({"Authorization":f"Bearer {token}"} if token else {})}, method="POST")
        try:
            with urlopen(request, timeout=float(os.getenv("AWE_DEPLOYMENT_PROVIDER_TIMEOUT_SECONDS", "600"))) as response:
                result = json.loads(response.read().decode())
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            deployment.status = DeploymentStatus.FAILED
            deployment.diagnostics = [f"Hosted deployment provider failed: {exc}"]
            return await repository.update_deployment(deployment)
        if not isinstance(result, dict) or not result.get("url"):
            deployment.status = DeploymentStatus.FAILED
            deployment.diagnostics = ["Hosted deployment provider returned no deployment URL."]
            return await repository.update_deployment(deployment)
        deployment.status = DeploymentStatus.DEPLOYED
        deployment.url = str(result["url"])
        deployment.runtime_id = str(result.get("runtime_id")) if result.get("runtime_id") else None
        deployment.snapshot_ref = str(result.get("snapshot_ref")) if result.get("snapshot_ref") else None
        deployment.deployed_at = datetime.now(timezone.utc)
        deployment = await repository.update_deployment(deployment)
        if deployment.snapshot_ref:
            return await repository.promote_deployment(deployment.deployment_id)
        deployment.diagnostics = [*deployment.diagnostics, "Hosted deployment succeeded but returned no immutable snapshot reference; left historical until snapshot is available."]
        return await repository.update_deployment(deployment)

    async def stop(self, deployment: WebsiteDeployment, repository: Repository) -> WebsiteDeployment:
        endpoint = os.getenv("AWE_DEPLOYMENT_PROVIDER_URL", "").strip()
        if not endpoint:
            deployment.status = DeploymentStatus.FAILED
            deployment.diagnostics.append("AWE_DEPLOYMENT_PROVIDER_URL is required to stop hosted deployments.")
            return await repository.update_deployment(deployment)
        request = Request(endpoint.rstrip("/") + "/deployments/" + str(deployment.deployment_id) + "/stop", method="POST")
        try:
            with urlopen(request, timeout=float(os.getenv("AWE_DEPLOYMENT_PROVIDER_TIMEOUT_SECONDS", "600"))):
                pass
            deployment.status = DeploymentStatus.STOPPED
            deployment.stopped_at = datetime.now(timezone.utc)
        except (HTTPError, URLError, TimeoutError) as exc:
            deployment.diagnostics.append(f"Hosted stop failed: {exc}")
        return await repository.update_deployment(deployment)


def deployment_provider_from_environment() -> DeploymentProvider:
    mode = os.getenv("AWE_DEPLOYMENT_PROVIDER", "local").strip().lower()
    if mode == "local":
        return LocalDeploymentProvider()
    if mode == "hosted":
        return HostedDeploymentProvider()
    raise ValueError(f"Unsupported AWE_DEPLOYMENT_PROVIDER: {mode}")


class LocalDeploymentProvider(DeploymentProvider):
    """MVP provider: promotes the disposable local runtime to a deployment lifecycle.

    The provider boundary is intentional. A future hosted provider can implement
    the same contract without changing the Studio/API lifecycle.
    """

    name = "local"

    async def deploy(self, project_id: UUID, repository: Repository) -> WebsiteDeployment:
        generation = await repository.get_generation(project_id)
        if not generation:
            raise KeyError("generation")

        if generation.status.value != "validated":
            raise ValueError("Website Generation must be validated before deployment.")

        existing = await repository.list_deployments(project_id)
        # Currentness is promoted only after the new snapshot and runtime are
        # healthy. Never stop/demote the current deployment before success.
        next_version = max((item.version for item in existing), default=0) + 1
        deployment = WebsiteDeployment(
            project_id=project_id,
            generation_version=generation.version,
            version=next_version,
            status=DeploymentStatus.DEPLOYING,
            lifecycle_role=DeploymentLifecycleRole.HISTORICAL,
            provider=self.name,
        )
        await repository.create_deployment(deployment)

        try:
            preview = await WebsitePreviewService(repository).start(project_id, preserve_deployment=False)
        except Exception as exc:
            deployment.status = DeploymentStatus.FAILED
            deployment.diagnostics = [f"Deployment runtime failed: {exc}"]
            return await repository.update_deployment(deployment)
        if preview.status.value != "started" or not preview.url:
            deployment.status = DeploymentStatus.FAILED
            deployment.diagnostics = preview.diagnostics or ["Deployment runtime failed to start."]
            return await repository.update_deployment(deployment)

        try:
            workspace = WebsitePreviewService._workspaces.get(str(project_id))
            if not workspace:
                raise RuntimeError("Deployment runtime workspace is unavailable for snapshot persistence.")

            # The deployment snapshot is the immutable source of truth for the
            # newly created live version. Do not rely on the Preview runtime's
            # previous synchronization state: explicitly materialize the
            # latest PUBLISHED content into the exact workspace immediately
            # before taking the snapshot. This is deliberately different from
            # the editable draft row, which must never leak into Deploy.
            published_content = await repository.list_content(
                project_id, status=WebsiteContentStatus.PUBLISHED
            )
            await asyncio.to_thread(
                WebsitePreviewService._write_content_volume,
                workspace,
                published_content,
            )
            snapshot = await asyncio.to_thread(
                create_deployment_snapshot,
                workspace,
                str(deployment.deployment_id),
            )
            # Docker container labels are immutable after creation. Instead of
            # attempting to mutate the Preview runtime, start a deployment
            # runtime from the exact persisted snapshot with the deployment
            # label applied at docker run creation time.
            deployment_runtime = await WebsitePreviewService(repository).activate_deployment_runtime_from_snapshot(
                project_id, deployment, snapshot
            )
        except Exception as exc:
            await WebsitePreviewService(repository).stop(project_id)
            deployment.status = DeploymentStatus.FAILED
            deployment.diagnostics = [f"Deployment snapshot failed: {exc}"]
            return await repository.update_deployment(deployment)

        deployment.status = DeploymentStatus.DEPLOYED
        deployment.url = deployment_runtime.url
        deployment.runtime_id = deployment_runtime.preview_id.hex
        deployment.snapshot_ref = snapshot
        deployment.deployed_at = datetime.now(timezone.utc)
        deployment.diagnostics = [*deployment.diagnostics, f"Persistent snapshot: {snapshot}"]
        deployment = await repository.update_deployment(deployment)
        # This is the sole currentness transition. It occurs only after the
        # immutable snapshot and healthy deployment runtime exist.
        promoted = await repository.promote_deployment(deployment.deployment_id)
        await WebsitePreviewService(repository).reconcile_deployment_runtimes(project_id)
        return promoted

    async def stop(self, deployment: WebsiteDeployment, repository: Repository) -> WebsiteDeployment:
        await WebsitePreviewService(repository).stop_deployment_runtime(deployment.project_id, deployment.deployment_id)
        deployment.status = DeploymentStatus.STOPPED
        deployment.stopped_at = datetime.now(timezone.utc)
        return await repository.update_deployment(deployment)


class DeploymentService:
    def __init__(self, repository: Repository, provider: DeploymentProvider | None = None) -> None:
        self.repository = repository
        self.provider = provider or deployment_provider_from_environment()

    async def deploy(self, project_id: UUID) -> WebsiteDeployment:
        return await self.provider.deploy(project_id, self.repository)

    async def get(self, deployment_id: UUID) -> WebsiteDeployment:
        deployment = await self.repository.get_deployment(deployment_id)
        if not deployment:
            raise KeyError("deployment")
        return deployment

    async def list(self, project_id: UUID) -> list[WebsiteDeployment]:
        return sorted(await self.repository.list_deployments(project_id), key=lambda x: x.created_at, reverse=True)

    async def stop(self, deployment_id: UUID) -> WebsiteDeployment:
        deployment = await self.get(deployment_id)
        if deployment.status == DeploymentStatus.STOPPED:
            return deployment
        return await self.provider.stop(deployment, self.repository)
