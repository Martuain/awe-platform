import subprocess
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
            GeneratedFile(path="package.json", content='{"scripts":{"build":"next build"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"},"devDependencies":{"typescript":"5.8.2","@types/react":"19.1.10","@types/node":"20.17.6"}}'),
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


@pytest.mark.anyio
async def test_preview_uses_docker_volume_workspace(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()

    await repo.create_generation(
        WebsiteGeneration(
            project_id=project_id,
            status=WebsiteGenerationStatus.VALIDATED,
            files=[
                GeneratedFile(
                    path="package.json",
                    content='{"scripts":{"build":"next build","start":"next start"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"},"devDependencies":{"typescript":"5.8.2","@types/react":"19.1.10","@types/node":"20.17.6"}}',
                ),
                GeneratedFile(
                    path="app/page.tsx",
                    content="export default function Page(){return null}",
                ),
            ],
        )
    )

    monkeypatch.setattr(
        "app.services.preview.shutil.which",
        lambda _: "/usr/bin/docker",
    )

    monkeypatch.setattr(
        "app.services.preview.create_workspace_volume",
        lambda _: "awe-preview-test",
    )

    populated = []
    monkeypatch.setattr(
        "app.services.preview.populate_workspace_volume",
        lambda volume, files: populated.append((volume, files)),
    )

    removed = []
    monkeypatch.setattr(
        "app.services.preview.remove_workspace_volume",
        lambda volume: removed.append(volume),
    )

    def fake_run(volume_name, command, network, timeout):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(
        "app.services.preview.WebsitePreviewService._run",
        staticmethod(fake_run),
    )

    def fake_subprocess_run(command, **kwargs):
        if command[0:2] == ["docker", "run"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="preview-container-id\n",
                stderr="",
            )

        if command[0:2] == ["docker", "port"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="127.0.0.1:49152\n",
                stderr="",
            )

        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "app.services.preview.subprocess.run",
        fake_subprocess_run,
    )

    result = await WebsitePreviewService(repo).start(project_id)

    assert result.status == WebsitePreviewStatus.STARTED
    assert result.url == "http://127.0.0.1:49152"
    assert populated[0][0] == "awe-preview-test"

    await WebsitePreviewService(repo).stop(project_id)

    assert removed == ["awe-preview-test"]
