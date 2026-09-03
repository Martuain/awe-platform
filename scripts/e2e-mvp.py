#!/usr/bin/env python3
"""Drive the local AWE MVP through a fresh project to a live deployment.

Prerequisite: `pnpm mvp:up` must already be running and Docker must be available
through the API service. The script intentionally creates a new project so it
never depends on an existing Studio/localStorage state.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

API = "http://localhost:8000"


def request(method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=480) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach API at {API}: {exc.reason}") from exc


def wait_for_api() -> None:
    for _ in range(30):
        try:
            if request("GET", "/api/v1/health"):
                return
        except RuntimeError:
            time.sleep(2)
    raise RuntimeError("API did not become ready within 60 seconds")


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise RuntimeError(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> int:
    print("AWE MVP end-to-end smoke test")
    print("=============================")
    wait_for_api()

    project = request("POST", "/api/v1/projects", {"name": "E2E Fresh Café"})
    project_id = project["id"]
    print(f"[1/12] Project created: {project_id}")

    # Exercise the lifecycle repair directly: a fresh project has no Discovery
    # context, then the explicit initialization endpoint creates one.
    try:
        request("POST", "/api/v1/business-discovery/message", {
            "project_id": project_id,
            "message": "We are a consulting firm helping enterprise teams grow.",
        })
    except RuntimeError as exc:
        if "HTTP 404" not in str(exc):
            raise
    else:
        raise RuntimeError("Strict Discovery API unexpectedly accepted an uninitialized session")

    discovery = request("POST", f"/api/v1/business-discovery/start?project_id={project_id}")
    assert_equal(discovery["status"], "collecting", "Discovery start status")
    discovery = request("POST", "/api/v1/business-discovery/message", {
        "project_id": project_id,
        "message": (
            "We are a specialty coffee shop called E2E Fresh Café. "
            "The website should showcase our menu and atmosphere, explain what makes our coffee special, "
            "and encourage people to visit the shop."
        ),
    })
    assert_equal(discovery["status"], "awaiting_approval", "Discovery completion status")
    discovery = request("POST", f"/api/v1/business-discovery/approve/{project_id}")["context"]
    assert_equal(discovery["status"], "approved", "Discovery approval")
    print("[2/12] Discovery approved")

    strategy = request("POST", f"/api/v1/website-strategy/generate?project_id={project_id}")
    strategy = request("POST", f"/api/v1/website-strategy/{project_id}/approve")
    assert_equal(strategy["status"], "approved", "Strategy approval")
    print("[3/12] Strategy approved")

    design = request("POST", f"/api/v1/brand-design/generate?project_id={project_id}")
    design = request("POST", f"/api/v1/brand-design/{project_id}/approve")
    assert_equal(design["status"], "approved", "Design approval")
    print("[4/12] Design approved")

    specification = request("POST", f"/api/v1/website-specification/generate?project_id={project_id}")
    specification = request("POST", f"/api/v1/website-specification/{project_id}/approve")
    assert_equal(specification["status"], "approved", "Specification approval")
    print("[5/12] Website Specification approved")

    generation = request("POST", f"/api/v1/website-generation/generate?project_id={project_id}")
    assert_equal(generation["framework"], "Next.js App Router", "Generated framework")
    assert_equal(generation["status"], "validated", "Generation status")
    assert_equal(generation["validation"]["business_content_present"], True, "Business content validation")
    generated_files = {item["path"]: item["content"] for item in generation["files"]}
    generated_text = "".join(generated_files.values())
    forbidden_leaks = (
        "Hero/value proposition",
        "Help prospective customers understand and act on the value offered by",
        "value offered by restaurant",
    )
    if any(leak in generated_text for leak in forbidden_leaks):
        raise RuntimeError("Generated website leaked strategy/specification implementation copy into visitor-facing content")
    print(f"[6/12] Website generated: {len(generation['files'])} files")

    plan = request("POST", f"/api/v1/website-build/plan?project_id={project_id}")
    assert_equal(plan["status"], "planned", "Build plan status")
    print("[7/12] Build plan accepted")

    build = request(
        "POST",
        f"/api/v1/website-build/execute?project_id={project_id}&install_timeout_seconds=300&build_timeout_seconds=180",
    )
    assert_equal(build["status"], "succeeded", "Build execution")
    print("[8/12] Isolated build succeeded")

    validation = request("POST", f"/api/v1/website-validation/validate?project_id={project_id}")
    assert_equal(validation["status"], "passed", "Website validation")
    print("[9/12] Website validation passed")

    deployment = request("POST", f"/api/v1/deployments?project_id={project_id}")
    assert_equal(deployment["status"], "deployed", "Deployment status")
    url = deployment.get("url")
    if not url:
        raise RuntimeError("Deployment succeeded without a live URL")
    print(f"[10/12] Deployment running: {url}")

    html = None
    last_error = None

    for attempt in range(1, 11):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                html = response.read().decode("utf-8", errors="replace")
                if response.status != 200:
                    raise RuntimeError(f"Live deployment returned HTTP {response.status}")
                break
        except Exception as exc:
            last_error = exc
            if attempt < 10:
                time.sleep(1)

    if html is None:
        raise RuntimeError(f"Live deployment did not become ready: {last_error}")
    if "E2E Fresh Café" not in html and "AWE generated website" not in html:
        raise RuntimeError("Live deployment did not return the generated website HTML")
    print("[11/12] Live URL returned generated website HTML")

    workspace = request("GET", f"/api/v1/projects/{project_id}/workspace")
    if workspace["deployment_count"] < 1 or workspace["latest_deployment_status"] != "deployed":
        raise RuntimeError(f"Workspace does not reflect deployed state: {workspace}")
    print("[12/12] Workspace reflects deployed state")
    print("\nE2E MVP: GREEN")
    print(f"Project: {project_id}")
    print(f"Live website: {url}")
    print("The deployment is intentionally left running for browser validation.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"E2E MVP: RED — {exc}", file=sys.stderr)
        raise SystemExit(1)
