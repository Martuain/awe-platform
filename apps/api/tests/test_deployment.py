import pytest
from uuid import uuid4


@pytest.fixture(autouse=True)
def _no_docker_content_sync(monkeypatch):
    """Keep unit deployment tests independent from a local Docker daemon."""
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService._write_content_volume", lambda volume, items: None)

from app.models import (
    DeploymentLifecycleRole,
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
async def test_deployment_snapshots_latest_published_content_not_stale_workspace(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[GeneratedFile(path="package.json", content="{}")],
    ))
    from app.models import WebsiteContentItem, WebsiteContentStatus
    await repo.upsert_content(WebsiteContentItem(
        project_id=project_id, page="/", key="headline", content_type="text",
        value="Published v2", version=1, status=WebsiteContentStatus.DRAFT,
    ))
    await repo.publish_content(project_id)
    await repo.upsert_content(WebsiteContentItem(
        project_id=project_id, page="/", key="headline", content_type="text",
        value="Unpublished draft v3", version=2, status=WebsiteContentStatus.DRAFT,
    ))

    class FakePreview:
        status = WebsitePreviewStatus.STARTED
        url = "http://127.0.0.1:4321"
        preview_id = uuid4()
        diagnostics = []

    async def fake_start(self, project_id, preserve_deployment=False):
        return FakePreview()

    synced = []
    def fake_write_content_volume(volume_name, items):
        synced.append((volume_name, [(item.page, item.key, item.value, item.status.value) for item in items]))

    async def fake_activate(self, project_id, deployment, snapshot):
        return FakePreview()

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.activate_deployment_runtime_from_snapshot", fake_activate)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService._workspaces", {str(project_id): "test-workspace"})
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService._write_content_volume", fake_write_content_volume)
    monkeypatch.setattr("app.services.deployment.create_deployment_snapshot", lambda source, deployment_id: f"awe-deployment-{deployment_id}")

    deployment = await DeploymentService(repo).deploy(project_id)

    assert deployment.status == DeploymentStatus.DEPLOYED
    assert synced == [("test-workspace", [("/", "headline", "Published v2", "published")])]


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

    async def fake_start(self, project_id, preserve_deployment=False):
        return FakePreview()

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    async def fake_activate(self, project_id, deployment, snapshot):
        return FakePreview()
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.activate_deployment_runtime_from_snapshot", fake_activate)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService._workspaces", {str(project_id): "test-workspace"})
    monkeypatch.setattr("app.services.deployment.create_deployment_snapshot", lambda source, deployment_id: f"awe-deployment-{deployment_id}")
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

    async def fake_start(self, project_id, preserve_deployment=False):
        return FakePreview()

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    async def fake_activate(self, project_id, deployment, snapshot):
        return FakePreview()
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.activate_deployment_runtime_from_snapshot", fake_activate)
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

    async def fake_start(self, project_id, preserve_deployment=False):
        return FakePreview()

    async def fake_stop(self, project_id):
        return None

    async def fake_stop_deployment_runtime(self, project_id, deployment_id=None):
        return None

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    async def fake_activate(self, project_id, deployment, snapshot):
        return FakePreview()
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.activate_deployment_runtime_from_snapshot", fake_activate)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.stop", fake_stop)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.stop_deployment_runtime", fake_stop_deployment_runtime)
    deployment = await DeploymentService(repo).deploy(project_id)
    stopped = await DeploymentService(repo).stop(deployment.deployment_id)

    assert stopped.status == DeploymentStatus.STOPPED
    assert stopped.stopped_at is not None

@pytest.mark.anyio
async def test_deployment_versions_increment_and_previous_deployment_is_stopped(monkeypatch):
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

    async def fake_start(self, project_id, preserve_deployment=False):
        return FakePreview()

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    async def fake_activate(self, project_id, deployment, snapshot):
        return FakePreview()
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.activate_deployment_runtime_from_snapshot", fake_activate)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService._workspaces", {str(project_id): "test-workspace"})
    monkeypatch.setattr("app.services.deployment.create_deployment_snapshot", lambda source, deployment_id: f"awe-deployment-{deployment_id}")
    service = DeploymentService(repo)
    first = await service.deploy(project_id)
    second = await service.deploy(project_id)

    assert first.version == 1
    assert second.version == 2
    history = await service.list(project_id)
    previous = next(item for item in history if item.deployment_id == first.deployment_id)
    assert previous.status == DeploymentStatus.DEPLOYED
    assert previous.lifecycle_role == DeploymentLifecycleRole.PREVIOUS


@pytest.mark.anyio
async def test_deployment_requires_validated_generation():
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.GENERATED,
        files=[GeneratedFile(path="package.json", content="{}")],
    ))

    with pytest.raises(ValueError, match="validated before deployment"):
        await DeploymentService(repo).deploy(project_id)


@pytest.mark.anyio
async def test_snapshot_failure_never_marks_deployment_deployed(monkeypatch):
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

    async def fake_start(self, project_id, preserve_deployment=False):
        return FakePreview()

    async def fake_stop(self, project_id):
        return None

    async def fake_stop_deployment_runtime(self, project_id, deployment_id=None):
        return None

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    async def fake_activate(self, project_id, deployment, snapshot):
        return FakePreview()
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.activate_deployment_runtime_from_snapshot", fake_activate)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.stop", fake_stop)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.stop_deployment_runtime", fake_stop_deployment_runtime)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService._workspaces", {str(project_id): "test-workspace"})

    def fail_snapshot(source, deployment_id):
        raise RuntimeError("snapshot storage unavailable")

    monkeypatch.setattr("app.services.deployment.create_deployment_snapshot", fail_snapshot)
    deployment = await DeploymentService(repo).deploy(project_id)

    assert deployment.status == DeploymentStatus.FAILED
    assert "Deployment snapshot failed" in deployment.diagnostics[0]


@pytest.mark.anyio
async def test_new_deployment_promotes_only_after_success_and_keeps_previous(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id, status=WebsiteGenerationStatus.VALIDATED,
        files=[GeneratedFile(path="package.json", content="{}")],
    ))

    class FakePreview:
        status = WebsitePreviewStatus.STARTED
        url = "http://127.0.0.1:4321"
        preview_id = uuid4()
        diagnostics = []

    async def fake_start(self, project_id, preserve_deployment=False):
        return FakePreview()
    async def fake_activate(self, project_id, deployment, snapshot):
        return FakePreview()

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", fake_start)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.activate_deployment_runtime_from_snapshot", fake_activate)
    async def fake_reconcile(self, project_id):
        return None
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.reconcile_deployment_runtimes", fake_reconcile)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService._workspaces", {str(project_id): "test-workspace"})
    monkeypatch.setattr("app.services.deployment.create_deployment_snapshot", lambda source, deployment_id: f"awe-deployment-{deployment_id}")

    first = await DeploymentService(repo).deploy(project_id)
    second = await DeploymentService(repo).deploy(project_id)

    first_after = await repo.get_deployment(first.deployment_id)
    assert first_after is not None
    assert first_after.lifecycle_role == DeploymentLifecycleRole.PREVIOUS
    assert second.lifecycle_role == DeploymentLifecycleRole.CURRENT
    assert second.snapshot_ref == f"awe-deployment-{second.deployment_id}"
    assert first_after.status == DeploymentStatus.DEPLOYED


@pytest.mark.anyio
async def test_failed_new_deployment_does_not_displace_current(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id, status=WebsiteGenerationStatus.VALIDATED,
        files=[],
    ))

    class GoodPreview:
        status = WebsitePreviewStatus.STARTED
        url = "http://127.0.0.1:4321"
        preview_id = uuid4()
        diagnostics = []

    async def good_start(self, project_id, preserve_deployment=False):
        return GoodPreview()
    async def good_activate(self, project_id, deployment, snapshot):
        return GoodPreview()

    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", good_start)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.activate_deployment_runtime_from_snapshot", good_activate)
    async def fake_reconcile(self, project_id):
        return None
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.reconcile_deployment_runtimes", fake_reconcile)
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService._workspaces", {str(project_id): "test-workspace"})
    monkeypatch.setattr("app.services.deployment.create_deployment_snapshot", lambda source, deployment_id: f"awe-deployment-{deployment_id}")
    first = await DeploymentService(repo).deploy(project_id)

    class BadPreview:
        status = WebsitePreviewStatus.FAILED
        url = None
        preview_id = uuid4()
        diagnostics = ["runtime failed"]

    async def bad_start(self, project_id, preserve_deployment=False):
        return BadPreview()
    monkeypatch.setattr("app.services.deployment.WebsitePreviewService.start", bad_start)
    second = await DeploymentService(repo).deploy(project_id)

    current = await repo.get_current_deployment(project_id)
    assert current is not None
    assert current.deployment_id == first.deployment_id
    assert second.status == DeploymentStatus.FAILED
    assert second.lifecycle_role == DeploymentLifecycleRole.HISTORICAL
