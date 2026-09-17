import subprocess

import pytest

from app.services.docker_workspace import (
    _build_archive,
    _validate_path,
    create_workspace_volume,
    populate_workspace_volume,
    remove_workspace_volume,
    restore_deployment_snapshot,
)


def test_validate_path_accepts_relative_posix_path():
    assert _validate_path("app/page.tsx") == "app/page.tsx"
    assert _validate_path("package.json") == "package.json"


@pytest.mark.parametrize(
    "path",
    [
        "",
        ".",
        "..",
        "/package.json",
        "../package.json",
        "app/../package.json",
        "app//page.tsx",
    ],
)
def test_validate_path_rejects_unsafe_paths(path):
    with pytest.raises(ValueError):
        _validate_path(path)


def test_build_archive_contains_generated_files():
    archive = _build_archive(
        [
            ("package.json", '{"name":"test"}'),
            ("app/page.tsx", "export default function Page() { return null }"),
        ]
    )

    import io
    import tarfile

    with tarfile.open(fileobj=io.BytesIO(archive), mode="r") as tar:
        names = tar.getnames()
        assert names == ["package.json", "app/page.tsx"]
        assert tar.extractfile("package.json").read() == b'{"name":"test"}'


def test_create_workspace_volume_uses_docker_volume_create(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="awe-build-1234567890ab\n",
            stderr="",
        )

    monkeypatch.setattr(
        "app.services.docker_workspace.subprocess.run",
        fake_run,
    )
    monkeypatch.setattr(
        "app.services.docker_workspace.uuid4",
        lambda: type("UUID", (), {"hex": "1234567890abcdef"})(),
    )

    volume = create_workspace_volume("awe-build")

    assert volume == "awe-build-1234567890ab"[:24]
    assert calls[0][0] == ["docker", "volume", "create", volume]


def test_populate_workspace_volume_uses_named_volume_not_host_path(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["input"] = kwargs["input"]
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(
        "app.services.docker_workspace.subprocess.run",
        fake_run,
    )

    populate_workspace_volume(
        "awe-build-test",
        [("package.json", "{}")],
    )

    command = captured["command"]

    assert "-v" in command
    assert "awe-build-test:/workspace:rw" in command
    assert all("/tmp/awe-" not in arg for arg in command)
    assert captured["input"]


def test_remove_workspace_volume_uses_docker_volume_rm(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "app.services.docker_workspace.subprocess.run",
        fake_run,
    )

    remove_workspace_volume("awe-build-test")

    assert calls == [["docker", "volume", "rm", "-f", "awe-build-test"]]


def test_restore_deployment_snapshot_copies_persisted_volume(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.services.docker_workspace.create_workspace_volume",
        lambda prefix: "awe-preview-restore-test",
    )
    monkeypatch.setattr(
        "app.services.docker_workspace.subprocess.run",
        lambda command, **kwargs: (
            calls.append(command)
            or subprocess.CompletedProcess(command, 0, "", "")
        ),
    )

    restored = restore_deployment_snapshot("awe-deployment-deploy123")

    assert restored == "awe-preview-restore-test"
    assert calls == [[
        "docker", "run", "--rm",
        "-v", "awe-deployment-deploy123:/from:ro",
        "-v", "awe-preview-restore-test:/to:rw",
        "alpine:3.22", "sh", "-c", "cp -a /from/. /to/",
    ]]
