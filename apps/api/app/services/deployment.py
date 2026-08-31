from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.models import DeploymentStatus, WebsiteDeployment
from app.services.preview import WebsitePreviewService
from app.store import Repository


class DeploymentProvider:
    name = "local"

    async def deploy(self, project_id: UUID, repository: Repository) -> WebsiteDeployment:
        raise NotImplementedError

    async def stop(self, deployment: WebsiteDeployment, repository: Repository) -> WebsiteDeployment:
        raise NotImplementedError


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

        deployment = WebsiteDeployment(
            project_id=project_id,
            generation_version=generation.version,
            status=DeploymentStatus.DEPLOYING,
            provider=self.name,
        )
        await repository.create_deployment(deployment)

        preview = await WebsitePreviewService(repository).start(project_id)
        if preview.status.value != "started" or not preview.url:
            deployment.status = DeploymentStatus.FAILED
            deployment.diagnostics = preview.diagnostics or ["Deployment runtime failed to start."]
            return await repository.update_deployment(deployment)

        deployment.status = DeploymentStatus.DEPLOYED
        deployment.url = preview.url
        deployment.runtime_id = preview.preview_id.hex
        deployment.deployed_at = datetime.now(timezone.utc)
        return await repository.update_deployment(deployment)

    async def stop(self, deployment: WebsiteDeployment, repository: Repository) -> WebsiteDeployment:
        await WebsitePreviewService(repository).stop(deployment.project_id)
        deployment.status = DeploymentStatus.STOPPED
        deployment.stopped_at = datetime.now(timezone.utc)
        return await repository.update_deployment(deployment)


class DeploymentService:
    def __init__(self, repository: Repository, provider: DeploymentProvider | None = None) -> None:
        self.repository = repository
        self.provider = provider or LocalDeploymentProvider()

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
