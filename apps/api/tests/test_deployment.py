import pytest
from uuid import uuid4

from app.models import (
    DeploymentStatus,
    GeneratedFile,
    WebsiteDeployment,
    WebsiteGeneration,
    WebsiteGenerationStatus,
    WebsitePreviewStatus,
)
from app.services.deployment import DeploymentService, LocalDeploymentProvider
from app.store import InMemoryRepository


@pytest.mark.anyio
async def test_deploy_requires_generation():
    repo = InMemoryRepository()
    with pytest.raises(KeyError):
        await DeploymentService(repo).deploy(uuid4())


@pytest.mark.anyio
async def test_local_deployment_promotes_started_preview(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[GeneratedFile(path="package.json", content="{}")],
    ))

    class FakePreview:
        status = WebsitePreviewStatus.STARTED
        url = "http://127.0.0.1:4321"
        preview_id = uuid4()
        diagnostics = []

    async def fake_start(self, project_id):
        return FakePreview()

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    deployment = await DeploymentService(repo).deploy(project_id)

    assert deployment.status == DeploymentStatus.DEPLOYED
    assert deployment.provider == "local"
    assert deployment.url == "http://127.0.0.1:4321"


@pytest.mark.anyio
async def test_failed_preview_becomes_failed_deployment(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[],
    ))

    class FakePreview:
        status = WebsitePreviewStatus.FAILED
        url = None
        preview_id = uuid4()
        diagnostics = ["build failed"]

    async def fake_start(self, project_id):
        return FakePreview()

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    deployment = await DeploymentService(repo).deploy(project_id)

    assert deployment.status == DeploymentStatus.FAILED
    assert deployment.diagnostics == ["build failed"]


@pytest.mark.anyio
async def test_stop_marks_deployment_stopped(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[],
    ))

    class FakePreview:
        status = WebsitePreviewStatus.STARTED
        url = "http://127.0.0.1:4321"
        preview_id = uuid4()
        diagnostics = []

    async def fake_start(self, project_id):
        return FakePreview()

    async def fake_stop(self, project_id):
        return None

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.stop", fake_stop)
    deployment = await DeploymentService(repo).deploy(project_id)
    stopped = await DeploymentService(repo).stop(deployment.deployment_id)

    assert stopped.status == DeploymentStatus.STOPPED
    assert stopped.stopped_at is not None
