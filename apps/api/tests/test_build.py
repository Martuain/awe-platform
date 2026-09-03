import subprocess
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.store import InMemoryRepository
from app.models import WebsiteGeneration, WebsiteGenerationStatus, GeneratedFile
from app.services.build import WebsiteBuildService
from uuid import uuid4


@pytest.mark.anyio
async def test_build_plan_is_safe_and_does_not_execute_generated_code():
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
    app.state.repository = repo
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/website-build/plan?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "planned"
    assert data["isolation"] == "sandbox-required"
    assert data["workspace_strategy"] == "docker-volume"
    assert data["network_access"] == "build-install-only"
    assert data["allowed_commands"] == ["npm install", "next build", "next start"]


@pytest.mark.anyio
async def test_build_plan_rejects_unsupported_dependencies():
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
    plan = await WebsiteBuildService(repo).plan(project_id)
    assert plan.status.value == "rejected"
    assert "Unsupported runtime dependencies" in plan.diagnostics[0]


@pytest.mark.anyio
async def test_build_plan_rejects_unsupported_dev_dependencies():
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[
            GeneratedFile(
                path="package.json",
                content='{"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"},"devDependencies":{"evil-tool":"1.0.0"}}',
            ),
            GeneratedFile(path="app/page.tsx", content="export default function Page(){return null}"),
        ],
    ))
    plan = await WebsiteBuildService(repo).plan(project_id)
    assert plan.status.value == "rejected"
    assert "Unsupported development dependencies" in plan.diagnostics[0]


@pytest.mark.anyio
async def test_build_execute_uses_docker_volume_workspace(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()

    await repo.create_generation(
        WebsiteGeneration(
            project_id=project_id,
            status=WebsiteGenerationStatus.VALIDATED,
            files=[
                GeneratedFile(
                    path="package.json",
                    content='{"scripts":{"build":"next build"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"},"devDependencies":{"typescript":"5.8.2","@types/react":"19.1.10","@types/node":"20.17.6"}}',
                ),
                GeneratedFile(
                    path="app/page.tsx",
                    content="export default function Page(){return null}",
                ),
            ],
        )
    )

    monkeypatch.setattr(
        "app.services.build.shutil.which",
        lambda _: "/usr/bin/docker",
    )

    volume_calls = []

    def fake_create(prefix):
        volume_calls.append(("create", prefix))
        return "awe-build-test"

    def fake_populate(volume, files):
        volume_calls.append(("populate", volume, files))

    def fake_remove(volume):
        volume_calls.append(("remove", volume))

    monkeypatch.setattr(
        "app.services.build.create_workspace_volume",
        fake_create,
    )
    monkeypatch.setattr(
        "app.services.build.populate_workspace_volume",
        fake_populate,
    )
    monkeypatch.setattr(
        "app.services.build.remove_workspace_volume",
        fake_remove,
    )

    commands = []

    def fake_run(volume_name, command, network, timeout):
        commands.append((volume_name, command, network, timeout))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(
        "app.services.build.WebsiteBuildService._docker_run",
        staticmethod(fake_run),
    )

    result = await WebsiteBuildService(repo).execute(project_id)

    assert result["status"] == "succeeded"
    assert result["workspace"] == "docker-volume"

    assert volume_calls[0] == ("create", "awe-build")
    assert volume_calls[-1] == ("remove", "awe-build-test")

    assert commands[0][0] == "awe-build-test"
    assert commands[0][2] == "bridge"
    assert commands[0][3] == 300
    assert "--cache" in commands[0][1]
    assert commands[1][0] == "awe-build-test"
    assert commands[1][2] == "none"
    assert commands[1][3] == 180


@pytest.mark.anyio
async def test_build_execute_removes_volume_after_build_failure(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()

    await repo.create_generation(
        WebsiteGeneration(
            project_id=project_id,
            status=WebsiteGenerationStatus.VALIDATED,
            files=[
                GeneratedFile(
                    path="package.json",
                    content='{"scripts":{"build":"next build"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"},"devDependencies":{"typescript":"5.8.2","@types/react":"19.1.10","@types/node":"20.17.6"}}',
                ),
                GeneratedFile(
                    path="app/page.tsx",
                    content="export default function Page(){return null}",
                ),
            ],
        )
    )

    monkeypatch.setattr(
        "app.services.build.shutil.which",
        lambda _: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        "app.services.build.create_workspace_volume",
        lambda _: "awe-build-failure",
    )
    monkeypatch.setattr(
        "app.services.build.populate_workspace_volume",
        lambda *_: None,
    )

    removed = []
    monkeypatch.setattr(
        "app.services.build.remove_workspace_volume",
        lambda volume: removed.append(volume),
    )

    calls = []

    def fake_run(volume_name, command, network, timeout):
        calls.append(command)
        if command[:2] == ["npm", "install"]:
            return subprocess.CompletedProcess(command, 0, "installed", "")
        return subprocess.CompletedProcess(
            command,
            1,
            "",
            "next build failed",
        )

    monkeypatch.setattr(
        "app.services.build.WebsiteBuildService._docker_run",
        staticmethod(fake_run),
    )

    result = await WebsiteBuildService(repo).execute(project_id)

    assert result["status"] == "failed"
    assert result["phase"] == "build"
    assert removed == ["awe-build-failure"]


@pytest.mark.anyio
async def test_build_execute_uses_separate_phase_timeouts(monkeypatch):
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
    monkeypatch.setattr("app.services.build.shutil.which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr("app.services.build.create_workspace_volume", lambda _: "awe-timeout-test")
    monkeypatch.setattr("app.services.build.populate_workspace_volume", lambda *_: None)
    monkeypatch.setattr("app.services.build.remove_workspace_volume", lambda *_: None)

    calls = []
    def fake_run(volume_name, command, network, timeout):
        calls.append((command, network, timeout))
        return subprocess.CompletedProcess(command, 0, "ok", "")
    monkeypatch.setattr("app.services.build.WebsiteBuildService._docker_run", staticmethod(fake_run))

    result = await WebsiteBuildService(repo).execute(
        project_id, install_timeout_seconds=240, build_timeout_seconds=150
    )
    assert result["status"] == "succeeded"
    assert calls[0][2] == 240
    assert calls[1][2] == 150


@pytest.mark.anyio
async def test_build_execute_rejects_invalid_timeout(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[
            GeneratedFile(path="package.json", content='{"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"}}'),
            GeneratedFile(path="app/page.tsx", content="export default function Page(){return null}"),
        ],
    ))
    with pytest.raises(ValueError, match="between 1 and 600"):
        await WebsiteBuildService(repo).execute(project_id, install_timeout_seconds=0)
