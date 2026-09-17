import pathlib
from pathlib import Path
import asyncio
import subprocess
import pytest
from uuid import UUID, uuid4
from app.models import GeneratedFile, WebsiteGeneration, WebsiteGenerationStatus, WebsitePreview, WebsitePreviewStatus
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
    monkeypatch.setattr(
        "app.services.preview.WebsitePreviewService._wait_for_runtime_ready",
        staticmethod(lambda container_id, timeout_seconds=15.0: True),
    )

    result = await WebsitePreviewService(repo).start(project_id)

    assert result.status == WebsitePreviewStatus.STARTED
    assert result.url == "http://127.0.0.1:49152"
    assert populated[0][0] == "awe-preview-test"

    await WebsitePreviewService(repo).stop(project_id)

    assert removed == ["awe-preview-test"]


@pytest.mark.anyio
async def test_preview_reuses_running_runtime_for_same_generation(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[
            GeneratedFile(path="package.json", content='{"scripts":{"build":"next build","start":"next start"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"},"devDependencies":{"typescript":"5.8.2","@types/react":"19.1.10","@types/node":"20.17.6"}}'),
            GeneratedFile(path="app/page.tsx", content="export default function Page(){return null}"),
        ],
    ))

    monkeypatch.setattr("app.services.preview.shutil.which", lambda _: "/usr/bin/docker")
    monkeypatch.setattr("app.services.preview.WebsitePreviewService._container_running", staticmethod(lambda _: True))
    monkeypatch.setattr("app.services.preview.WebsitePreviewService._container_is_deployment", staticmethod(lambda _: False))
    monkeypatch.setattr("app.services.preview.WebsitePreviewService._write_content_file", staticmethod(lambda *args, **kwargs: None))

    service = WebsitePreviewService(repo)
    existing = WebsitePreviewService._sessions[str(project_id)] = WebsitePreview(
        project_id=project_id,
        generation_version=1,
        status=WebsitePreviewStatus.STARTED,
        url="http://127.0.0.1:4567",
        container_id="existing-container",
    )
    WebsitePreviewService._workspaces[str(project_id)] = "existing-volume"

    def fail_if_called(*args, **kwargs):
        raise AssertionError("preview runtime should be reused")

    monkeypatch.setattr("app.services.preview.create_workspace_volume", fail_if_called)

    result = await service.start(project_id)
    assert result is existing
    assert result.url == "http://127.0.0.1:4567"

    # Keep class-level test state isolated.
    WebsitePreviewService._sessions.pop(str(project_id), None)
    WebsitePreviewService._workspaces.pop(str(project_id), None)


def test_runtime_for_port_uses_labeled_docker_container(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:3] == ["docker", "ps", "-aq"]:
            return subprocess.CompletedProcess(command, 0, "runtime-123\n", "")
        if command[:3] == ["docker", "inspect", "-f"]:
            return subprocess.CompletedProcess(command, 0, "\n", "")
        if command == ["docker", "port", "runtime-123", "3000/tcp"]:
            return subprocess.CompletedProcess(command, 0, "127.0.0.1:49223\n", "")
        raise AssertionError(command)

    monkeypatch.setattr("app.services.preview.subprocess.run", fake_run)
    monkeypatch.setattr("app.services.preview.WebsitePreviewService._container_running", staticmethod(lambda _: True))
    assert WebsitePreviewService._runtime_for_port(49223) == "runtime-123"
    assert "label=com.awe.preview=true" in calls[0]


def test_runtime_for_project_uses_project_label(monkeypatch):
    project_id = uuid4()
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:3] == ["docker", "ps", "-aq"]:
            if "label=com.awe.deployment_id" in command:
                return subprocess.CompletedProcess(command, 0, "", "")
            return subprocess.CompletedProcess(command, 0, "runtime-456\n", "")
        if command[:3] == ["docker", "inspect", "-f"]:
            value = "true\n" if "State.Running" in command[3] else "\n"
            return subprocess.CompletedProcess(command, 0, value, "")
        raise AssertionError(command)

    monkeypatch.setattr("app.services.preview.subprocess.run", fake_run)
    assert WebsitePreviewService._runtime_for_project(project_id) == "runtime-456"
    assert f"label=com.awe.project_id={project_id}" in calls[0]


def test_legacy_preview_cleanup_targets_only_node_preview_runtimes(monkeypatch):
    def fake_run(command, **kwargs):
        if command[:3] == ["docker", "ps", "-aq"]:
            return subprocess.CompletedProcess(command, 0, "legacy-123\nother-456\n", "")
        if command[:3] == ["docker", "inspect", "--format"] and command[-1] == "legacy-123":
            return subprocess.CompletedProcess(
                command, 0,
                '"node:22-alpine"\t["npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000"]\t[]\n',
                "",
            )
        if command[:3] == ["docker", "inspect", "--format"] and command[-1] == "other-456":
            return subprocess.CompletedProcess(
                command, 0,
                '"node:22-alpine"\t["node", "server.js"]\t[]\n',
                "",
            )
        raise AssertionError(command)

    monkeypatch.setattr("app.services.preview.subprocess.run", fake_run)
    assert WebsitePreviewService._legacy_preview_container_ids() == ["legacy-123"]


@pytest.mark.anyio
async def test_stable_deployment_proxy_restores_latest_snapshot_when_runtime_is_missing(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    from app.models import WebsiteDeployment, DeploymentStatus, DeploymentLifecycleRole
    deployment = WebsiteDeployment(
        project_id=project_id, generation_version=3, version=1,
        status=DeploymentStatus.DEPLOYED,
        lifecycle_role=DeploymentLifecycleRole.CURRENT,
        provider="local",
    )
    await repo.create_deployment(deployment)
    service = WebsitePreviewService(repo)
    restored = WebsitePreview(
        project_id=project_id, generation_version=3, status=WebsitePreviewStatus.STARTED,
        url="http://127.0.0.1:49888", container_id="restored-container",
    )
    calls = []
    monkeypatch.setattr(WebsitePreviewService, "_deployment_runtime_for_deployment", classmethod(lambda cls, project, dep: None))
    monkeypatch.setattr(WebsitePreviewService, "_volume_exists", staticmethod(lambda _: True))
    monkeypatch.setattr(WebsitePreviewService, "_restore_runtime_sync", lambda self, project, dep, snapshot: restored)
    monkeypatch.setattr(WebsitePreviewService, "_preview_model_for_container", staticmethod(lambda project, generation, container: restored))
    async def fake_proxy(container_id, request, public_prefix, request_prefix):
        calls.append((container_id, public_prefix, request_prefix))
        return "proxied"
    monkeypatch.setattr(service, "proxy_container_request", fake_proxy)
    result = await service.proxy_deployment_request(project_id, type("Request", (), {})())
    assert result == "proxied"
    assert calls[0][0] == "restored-container"
    assert calls[0][1] == f"/api/live-preview/deployment/{project_id}/{deployment.deployment_id}"
    refreshed = await repo.get_deployment(deployment.deployment_id)
    assert refreshed.runtime_id == "restored-container"
    assert refreshed.url == "http://127.0.0.1:49888"

@pytest.mark.anyio
async def test_deployment_proxy_uses_deployment_scoped_public_prefix_for_explicit_version(monkeypatch):
    project_id = uuid4()
    deployment_id = uuid4()
    repo = InMemoryRepository()
    from app.models import WebsiteDeployment, DeploymentStatus

    deployment = WebsiteDeployment(
        project_id=project_id,
        generation_version=1,
        version=7,
        status=DeploymentStatus.STOPPED,
        provider="local",
        deployment_id=deployment_id,
    )
    await repo.create_deployment(deployment)
    service = WebsitePreviewService(repo)
    restored = WebsitePreview(
        project_id=project_id,
        generation_version=1,
        status=WebsitePreviewStatus.STARTED,
        url="http://127.0.0.1:49911",
        container_id="v7-runtime",
    )

    monkeypatch.setattr(
        WebsitePreviewService,
        "_deployment_runtime_for_deployment",
        classmethod(lambda cls, project, dep: restored.container_id),
    )
    monkeypatch.setattr(
        WebsitePreviewService,
        "_preview_model_for_container",
        staticmethod(lambda project, generation, container: restored),
    )

    calls = []

    async def fake_proxy(container_id, request, public_prefix, request_prefix):
        calls.append((container_id, public_prefix, request_prefix))
        return "proxied"

    monkeypatch.setattr(service, "proxy_container_request", fake_proxy)
    request = type(
        "Request",
        (),
        {
            "url": f"http://studio/api/live-preview/deployment/{project_id}/?deployment_id={deployment_id}"
        },
    )()

    result = await service.proxy_deployment_request(project_id, request)

    assert result == "proxied"
    assert calls[0] == (
        "v7-runtime",
        f"/api/live-preview/deployment/{project_id}/{deployment_id}",
        f"/api/v1/website-preview/deployment-proxy/{project_id}",
    )


def test_deployment_preview_links_are_deployment_scoped():
    source = (pathlib.Path(__file__).resolve().parents[1] / "app/services/preview.py").read_text()
    assert 'f"/api/live-preview/deployment/{project_id}/{requested_id}"' in source
    assert r"(?:src|href|action)" in source
    assert r"(?:href|src|action)" in source



@pytest.mark.anyio
async def test_restore_latest_deployment_requires_successful_snapshot(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    from app.models import WebsiteDeployment, DeploymentStatus
    deployment = WebsiteDeployment(
        project_id=project_id, generation_version=2, version=1,
        status=DeploymentStatus.DEPLOYED, provider="local",
    )
    await repo.create_deployment(deployment)
    service = WebsitePreviewService(repo)
    monkeypatch.setattr(service, "_volume_exists", lambda _: False)
    with pytest.raises(KeyError, match="snapshot is unavailable"):
        await service.restore_latest_deployment(project_id)

@pytest.mark.anyio
async def test_stable_deployment_proxy_restores_requested_historical_snapshot(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    from app.models import WebsiteDeployment, DeploymentStatus
    first = WebsiteDeployment(project_id=project_id, generation_version=1, version=1, status=DeploymentStatus.STOPPED, provider="local")
    second = WebsiteDeployment(project_id=project_id, generation_version=2, version=2, status=DeploymentStatus.DEPLOYED, provider="local")
    await repo.create_deployment(first)
    await repo.create_deployment(second)
    service = WebsitePreviewService(repo)
    restored = WebsitePreview(project_id=project_id, generation_version=1, status=WebsitePreviewStatus.STARTED, url="http://127.0.0.1:49901", container_id="historical-container")
    monkeypatch.setattr(WebsitePreviewService, "_deployment_runtime_for_deployment", classmethod(lambda cls, project, dep: None))
    monkeypatch.setattr(WebsitePreviewService, "_volume_exists", staticmethod(lambda _: True))
    monkeypatch.setattr(WebsitePreviewService, "_restore_runtime_sync", lambda self, project, dep, snapshot: restored)
    monkeypatch.setattr(WebsitePreviewService, "_preview_model_for_container", staticmethod(lambda project, generation, container: restored))
    async def fake_proxy(container_id, request, public_prefix, request_prefix):
        return container_id
    monkeypatch.setattr(service, "proxy_container_request", fake_proxy)
    request = type("Request", (), {"url": f"http://studio/api/live-preview/deployment/{project_id}/?deployment_id={first.deployment_id}"})()
    result = await service.proxy_deployment_request(project_id, request)
    assert result == "historical-container"
    refreshed = await repo.get_deployment(first.deployment_id)
    assert refreshed.status == DeploymentStatus.STOPPED
    assert refreshed.runtime_id == "historical-container"


def test_runtime_for_project_excludes_deployment_restore(monkeypatch):
    project_id = uuid4()

    monkeypatch.setattr(
        "app.services.preview.WebsitePreviewService._preview_container_ids",
        classmethod(lambda cls, _: ["deployment-runtime", "active-runtime"]),
    )
    monkeypatch.setattr(
        "app.services.preview.WebsitePreviewService._container_running",
        staticmethod(lambda _: True),
    )

    def fake_run(command, **kwargs):
        if command[:3] == ["docker", "inspect", "-f"]:
            container_id = command[-1]
            value = "deployment-id\n" if container_id == "deployment-runtime" else "\n"
            return subprocess.CompletedProcess(command, 0, value, "")
        raise AssertionError(command)

    monkeypatch.setattr("app.services.preview.subprocess.run", fake_run)
    assert WebsitePreviewService._runtime_for_project(project_id) == "active-runtime"


@pytest.mark.anyio
async def test_deployment_runtime_selector_prefers_running_deployment(monkeypatch):
    project_id = uuid4()

    def fake_run(command, **kwargs):
        if command[:3] == ["docker", "ps", "-q"]:
            return subprocess.CompletedProcess(command, 0, "deployment-runtime\n", "")
        if command[:3] == ["docker", "inspect", "-f"]:
            return subprocess.CompletedProcess(command, 0, "true\n", "")
        raise AssertionError(command)

    monkeypatch.setattr("app.services.preview.subprocess.run", fake_run)
    monkeypatch.setattr("app.services.preview.WebsitePreviewService._wait_for_runtime_ready", staticmethod(lambda *_args, **_kwargs: True))
    assert WebsitePreviewService._deployment_runtime_for_project(project_id) == "deployment-runtime"


@pytest.mark.anyio
async def test_refresh_published_content_hot_syncs_current_generation(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    await repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[
            GeneratedFile(path="package.json", content='{"scripts":{"build":"next build","start":"next start"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"},"devDependencies":{"typescript":"5.8.2","@types/react":"19.1.10","@types/node":"20.17.6"}}'),
            GeneratedFile(path="app/page.tsx", content="export default function Page(){return null}"),
        ],
    ))
    monkeypatch.setattr("app.services.preview.shutil.which", lambda _: "/usr/bin/docker")
    service = WebsitePreviewService(repo)
    monkeypatch.setattr(service, "_current_generation_preview_container", lambda *_: "current-preview")
    written = []
    monkeypatch.setattr(service, "_write_content_file", lambda container, items: written.append((container, list(items))))
    monkeypatch.setattr(service, "_preview_model_for_container", lambda project, version, container: WebsitePreview(
        project_id=project, generation_version=version, status=WebsitePreviewStatus.STARTED,
        url="http://127.0.0.1:49152", container_id=container
    ))
    monkeypatch.setattr(service, "_start_runtime", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not rebuild")))

    result = await service.refresh_published_content(project_id)
    assert result.status == WebsitePreviewStatus.STARTED
    assert result.container_id == "current-preview"
    assert written and written[0][0] == "current-preview"


def test_deployment_runtime_labels_are_creation_time_only():
    source = (Path(__file__).resolve().parents[1] / "app/services/preview.py").read_text()
    assert "docker\", \"update" not in source
    assert "--label-add" not in source
    assert 'f"com.awe.deployment_id={deployment.deployment_id}"' in source


def test_refresh_preview_route_exists():
    source = (Path(__file__).resolve().parents[1] / "app/routes/preview.py").read_text()
    assert '@router.post("/refresh", response_model=WebsitePreview)' in source
    assert 'refresh_published_content(project_id)' in source


def test_published_content_fingerprint_changes_when_value_changes():
    from app.models import WebsiteContentItem
    project_id = uuid4()
    first = WebsiteContentItem(project_id=project_id, page="/", key="headline", value="one")
    second = WebsiteContentItem(project_id=project_id, page="/", key="headline", value="two")
    a = WebsitePreviewService._published_content_fingerprint([first])
    b = WebsitePreviewService._published_content_fingerprint([second])
    assert a != b


def test_current_preview_container_requires_matching_content(monkeypatch):
    project_id = uuid4()
    expected = "abc123"

    monkeypatch.setattr(
        WebsitePreviewService,
        "_preview_container_ids",
        classmethod(lambda cls, _: ["old-preview", "current-preview"]),
    )
    monkeypatch.setattr(WebsitePreviewService, "_container_running", staticmethod(lambda _: True))
    monkeypatch.setattr(WebsitePreviewService, "_container_is_deployment", staticmethod(lambda _: False))

    def fake_run(command, **kwargs):
        if command[:3] == ["docker", "inspect", "-f"]:
            cid = command[-1]
            fingerprint = "old" if cid == "old-preview" else expected
            return subprocess.CompletedProcess(command, 0, f"7\t{fingerprint}\n", "")
        raise AssertionError(command)

    monkeypatch.setattr("app.services.preview.subprocess.run", fake_run)
    assert WebsitePreviewService._current_preview_container(project_id, 7, expected) == "current-preview"


def test_preview_runtime_command_contains_content_fingerprint():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "app/services/preview.py").read_text()
    assert 'com.awe.content_fingerprint=' in source


@pytest.mark.anyio
async def test_historical_deployment_reuses_matching_running_runtime(monkeypatch):
    project_id = uuid4()
    deployment_id = uuid4()
    repo = InMemoryRepository()
    from app.models import WebsiteDeployment, DeploymentStatus
    deployment = WebsiteDeployment(project_id=project_id, generation_version=1, version=1, status=DeploymentStatus.STOPPED, provider="local", deployment_id=deployment_id)
    await repo.create_deployment(deployment)
    service = WebsitePreviewService(repo)
    monkeypatch.setattr(WebsitePreviewService, "_deployment_runtime_for_deployment", classmethod(lambda cls, project, dep: "historical-runtime"))
    async def fake_proxy(container_id, request, public_prefix, request_prefix):
        return container_id
    monkeypatch.setattr(service, "proxy_container_request", fake_proxy)
    monkeypatch.setattr(WebsitePreviewService, "_preview_model_for_container", staticmethod(lambda project, generation, container: WebsitePreview(project_id=project, generation_version=generation, status=WebsitePreviewStatus.STARTED, url="http://127.0.0.1:49902", container_id=container)))
    request = type("Request", (), {"url": f"http://studio/api/live-preview/deployment/{project_id}/?deployment_id={deployment_id}"})()
    result = await service.proxy_deployment_request(project_id, request)
    assert result == "historical-runtime"


def test_historical_restore_preserves_deployment_runtime(monkeypatch):
    calls=[]
    project_id = uuid4()
    deployment_id = uuid4()
    monkeypatch.setattr(WebsitePreviewService, "_preview_container_ids", classmethod(lambda cls, _: ["deployment-runtime", "other-deployment"]))
    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:3] == ["docker", "inspect", "-f"]:
            container_id = command[-1]
            return subprocess.CompletedProcess(command, 0, (str(deployment_id) if container_id == "deployment-runtime" else str(uuid4())) + "\n", "")
        return subprocess.CompletedProcess(command, 0, "", "")
    monkeypatch.setattr("app.services.preview.subprocess.run", fake_run)
    WebsitePreviewService._stop_deployment_runtime_sync(project_id, deployment_id)
    assert any(cmd[-1] == "deployment-runtime" for cmd in calls if cmd[:3] == ["docker", "inspect", "-f"])
    assert not any(cmd[:3] == ["docker", "rm", "-f"] and cmd[-1] == "other-deployment" for cmd in calls)

@pytest.mark.anyio
async def test_concurrent_live_deployment_opens_converge_on_one_runtime(monkeypatch):
    project_id = uuid4()
    repo = InMemoryRepository()
    from app.models import WebsiteDeployment, DeploymentStatus, DeploymentLifecycleRole
    deployment = WebsiteDeployment(
        project_id=project_id, generation_version=1, version=8,
        status=DeploymentStatus.DEPLOYED,
        lifecycle_role=DeploymentLifecycleRole.CURRENT,
        provider="local",
    )
    await repo.create_deployment(deployment)
    service = WebsitePreviewService(repo)
    state = {"runtime": None, "restores": 0}
    restored = WebsitePreview(
        project_id=project_id, generation_version=1, status=WebsitePreviewStatus.STARTED,
        url="http://127.0.0.1:49908", container_id="one-runtime",
    )

    def fake_finder(cls, project, deployment_id):
        return state["runtime"]

    def fake_restore(self, project, dep, snapshot):
        import time
        state["restores"] += 1
        time.sleep(0.02)
        state["runtime"] = restored.container_id
        return restored

    monkeypatch.setattr(WebsitePreviewService, "_deployment_runtime_for_deployment", classmethod(fake_finder))
    monkeypatch.setattr(WebsitePreviewService, "_volume_exists", staticmethod(lambda _: True))
    monkeypatch.setattr(WebsitePreviewService, "_restore_runtime_sync", fake_restore)
    monkeypatch.setattr(WebsitePreviewService, "_preview_model_for_container", staticmethod(lambda project, generation, container: restored))

    calls = []
    async def fake_proxy(container_id, request, public_prefix, request_prefix):
        calls.append(container_id)
        return container_id
    monkeypatch.setattr(service, "proxy_container_request", fake_proxy)

    requests = [type("Request", (), {})(), type("Request", (), {})()]
    results = await asyncio.gather(*(service.proxy_deployment_request(project_id, request) for request in requests))

    assert results == ["one-runtime", "one-runtime"]
    assert calls == ["one-runtime", "one-runtime"]
    assert state["restores"] == 1


def test_deployment_runtime_reconciles_duplicate_ready_containers(monkeypatch):
    project_id = uuid4()
    deployment_id = uuid4()
    containers = ["runtime-a", "runtime-b"]
    removed = []

    monkeypatch.setattr(WebsitePreviewService, "_preview_container_ids", classmethod(lambda cls, project: containers))
    monkeypatch.setattr(WebsitePreviewService, "_container_running", staticmethod(lambda container: True))
    monkeypatch.setattr(WebsitePreviewService, "_wait_for_runtime_ready", staticmethod(lambda container, timeout_seconds=3.0: True))

    def fake_run(command, **kwargs):
        if command[:3] == ["docker", "inspect", "-f"]:
            if "deployment_id" in command[3]:
                return subprocess.CompletedProcess(command, 0, str(deployment_id) + "\n", "")
            return subprocess.CompletedProcess(command, 0, "awe-preview-restore-duplicate\n", "")
        if command[:3] == ["docker", "rm", "-f"]:
            removed.append(command[-1])
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("app.services.preview.subprocess.run", fake_run)
    monkeypatch.setattr("app.services.preview.remove_workspace_volume", lambda volume: None)

    assert WebsitePreviewService._deployment_runtime_for_deployment(project_id, deployment_id) == "runtime-a"
    assert removed == ["runtime-b"]

@pytest.mark.anyio
async def test_cap038_stable_live_proxy_keeps_current_navigation_on_stable_project_namespace(monkeypatch):
    project_id = uuid4()
    deployment_id = uuid4()
    repo = InMemoryRepository()
    from app.models import WebsiteDeployment, DeploymentStatus, DeploymentLifecycleRole

    deployment = WebsiteDeployment(
        project_id=project_id,
        generation_version=1,
        version=8,
        status=DeploymentStatus.DEPLOYED,
        lifecycle_role=DeploymentLifecycleRole.CURRENT,
        provider="local",
        deployment_id=deployment_id,
    )
    await repo.create_deployment(deployment)
    service = WebsitePreviewService(repo)
    restored = WebsitePreview(
        project_id=project_id,
        generation_version=1,
        status=WebsitePreviewStatus.STARTED,
        url="http://127.0.0.1:49920",
        container_id="current-runtime",
    )
    monkeypatch.setattr(WebsitePreviewService, "_deployment_runtime_for_deployment", classmethod(lambda cls, project, dep: restored.container_id))
    monkeypatch.setattr(WebsitePreviewService, "_preview_model_for_container", staticmethod(lambda project, generation, container: restored))
    calls = []

    async def fake_proxy(container_id, request, public_prefix, request_prefix):
        calls.append((container_id, public_prefix, request_prefix))
        return "proxied"

    monkeypatch.setattr(service, "proxy_container_request", fake_proxy)
    request = type("Request", (), {"url": f"http://api/api/v1/website-preview/live-proxy/{project_id}/"})()
    result = await service.proxy_deployment_request(
        project_id,
        request,
        request_prefix=f"/api/v1/website-preview/live-proxy/{project_id}",
        public_prefix=f"/api/live/{project_id}",
    )

    assert result == "proxied"
    assert calls[0] == (
        "current-runtime",
        f"/api/live/{project_id}",
        f"/api/v1/website-preview/live-proxy/{project_id}",
    )


@pytest.mark.anyio
async def test_cap038_stable_live_proxy_pins_explicit_deployment_in_stable_namespace(monkeypatch):
    project_id = uuid4()
    deployment_id = uuid4()
    repo = InMemoryRepository()
    from app.models import WebsiteDeployment, DeploymentStatus, DeploymentLifecycleRole

    deployment = WebsiteDeployment(
        project_id=project_id,
        generation_version=1,
        version=7,
        status=DeploymentStatus.STOPPED,
        lifecycle_role=DeploymentLifecycleRole.PREVIOUS,
        provider="local",
        deployment_id=deployment_id,
    )
    await repo.create_deployment(deployment)
    service = WebsitePreviewService(repo)
    restored = WebsitePreview(
        project_id=project_id,
        generation_version=1,
        status=WebsitePreviewStatus.STARTED,
        url="http://127.0.0.1:49921",
        container_id="previous-runtime",
    )
    monkeypatch.setattr(WebsitePreviewService, "_deployment_runtime_for_deployment", classmethod(lambda cls, project, dep: restored.container_id))
    monkeypatch.setattr(WebsitePreviewService, "_preview_model_for_container", staticmethod(lambda project, generation, container: restored))
    calls = []

    async def fake_proxy(container_id, request, public_prefix, request_prefix):
        calls.append((container_id, public_prefix, request_prefix))
        return "proxied"

    monkeypatch.setattr(service, "proxy_container_request", fake_proxy)
    request = type("Request", (), {"url": f"http://api/api/v1/website-preview/live-proxy/{project_id}/?deployment_id={deployment_id}"})()
    result = await service.proxy_deployment_request(
        project_id,
        request,
        request_prefix=f"/api/v1/website-preview/live-proxy/{project_id}",
        public_prefix=f"/api/live/{project_id}",
    )

    assert result == "proxied"
    assert calls[0] == (
        "previous-runtime",
        f"/api/live/{project_id}/deployment/{deployment_id}",
        f"/api/v1/website-preview/live-proxy/{project_id}",
    )
