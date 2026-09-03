from __future__ import annotations

import io
import subprocess
import tarfile
from pathlib import PurePosixPath
from uuid import uuid4


DOCKER_WORKSPACE_IMAGE = "alpine:3.22"


def create_workspace_volume(prefix: str) -> str:
    name = f"{prefix}-{uuid4().hex[:12]}"
    result = subprocess.run(
        ["docker", "volume", "create", name],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "Failed to create Docker workspace volume."
        )
    return result.stdout.strip() or name


def populate_workspace_volume(
    volume_name: str,
    files: list[tuple[str, str]],
) -> None:
    archive = _build_archive(files)

    command = [
        "docker",
        "run",
        "--rm",
        "-i",
        "-v",
        f"{volume_name}:/workspace:rw",
        DOCKER_WORKSPACE_IMAGE,
        "tar",
        "-x",
        "-C",
        "/workspace",
    ]

    result = subprocess.run(
        command,
        input=archive,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        stderr = (
            result.stderr.decode("utf-8", errors="replace")
            if isinstance(result.stderr, bytes)
            else str(result.stderr)
        )
        raise RuntimeError(
            stderr.strip() or "Failed to populate Docker workspace volume."
        )


def remove_workspace_volume(volume_name: str) -> None:
    subprocess.run(
        ["docker", "volume", "rm", "-f", volume_name],
        capture_output=True,
        text=True,
        check=False,
    )


def _build_archive(files: list[tuple[str, str]]) -> bytes:
    buffer = io.BytesIO()

    with tarfile.open(fileobj=buffer, mode="w") as archive:
        seen: set[str] = set()

        for path, content in files:
            normalized = _validate_path(path)

            if normalized in seen:
                raise ValueError(f"Duplicate generated file path: {path}")
            seen.add(normalized)

            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=normalized)
            info.size = len(data)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))

    return buffer.getvalue()


def _validate_path(path: str) -> str:
    if "//" in path:
        raise ValueError(f"Unsafe generated file path: {path}")
    candidate = PurePosixPath(path)

    if candidate.is_absolute():
        raise ValueError(f"Generated file path must be relative: {path}")

    if not path or path in {".", ".."}:
        raise ValueError(f"Invalid generated file path: {path}")

    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValueError(f"Unsafe generated file path: {path}")

    return candidate.as_posix()
