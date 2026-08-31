import pytest
from uuid import uuid4
from app.models import GeneratedFile, WebsiteGeneration, WebsiteGenerationStatus, WebsitePreviewStatus
from app.services.preview import WebsitePreviewService
from app.store import InMemoryRepository


@pytest.mark.anyio
async def test_preview_is_unavailable_without_docker(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[
            GeneratedFile(path="package.json", content='{"scripts":{"build":"next build"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"}}'),
            GeneratedFile(path="app/page.tsx", content="export default function Page(){return null}"),
        ],
    ))
    monkeypatch.setattr("app.services.preview.shutil.which", lambda _: None)
    result = await WebsitePreviewService(repo).start(project_id)
    assert result.status == WebsitePreviewStatus.UNAVAILABLE
    assert result.url is None


@pytest.mark.anyio
async def test_preview_rejects_unsupported_dependencies(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[
            GeneratedFile(path="package.json", content='{"dependencies":{"evil-package":"1.0.0"}}'),
            GeneratedFile(path="app/page.tsx", content="export default function Page(){return null}"),
        ],
    ))
    monkeypatch.setattr("app.services.preview.shutil.which", lambda _: "/usr/bin/docker")
    result = await WebsitePreviewService(repo).start(project_id)
    assert result.status == WebsitePreviewStatus.FAILED
    assert any("Unsupported runtime dependencies" in x for x in result.diagnostics)
