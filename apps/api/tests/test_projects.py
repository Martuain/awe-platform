import pytest


def test_project_workspace_can_be_listed_and_resumed(client):
    created = client.post("/api/v1/projects", json={"name": "CAP-013 Workspace"})
    assert created.status_code == 201
    project = created.json()

    listed = client.get("/api/v1/projects")
    assert listed.status_code == 200
    assert any(item["id"] == project["id"] for item in listed.json())

    workspace = client.get(f"/api/v1/projects/{project['id']}/workspace")
    assert workspace.status_code == 200
    data = workspace.json()
    assert data["project"]["id"] == project["id"]
    assert data["current_stage"] == "discovery"
    assert data["next_capability"] == "discovery"
    assert data["completed_capabilities"] == []
    assert data["deployment_count"] == 0
    assert data["last_activity_at"]

    archived = client.patch(f"/api/v1/projects/{project['id']}", json={"status": "archived"})
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    archived_workspace = client.get(f"/api/v1/projects/{project['id']}/workspace")
    assert archived_workspace.status_code == 200
    assert archived_workspace.json()["current_stage"] == "archived"

    restored = client.patch(f"/api/v1/projects/{project['id']}", json={"status": "active"})
    assert restored.status_code == 200
    assert restored.json()["status"] == "active"


def test_duplicate_project(client):
    created = client.post("/api/v1/projects", json={"name": "Original"}).json()
    duplicated = client.post(f"/api/v1/projects/{created['id']}/duplicate", json={"name": "Original Copy"})
    assert duplicated.status_code == 201
    body = duplicated.json()
    assert body["name"] == "Original Copy"
    assert body["id"] != created["id"]
    workspace = client.get(f"/api/v1/projects/{body['id']}/workspace").json()
    assert workspace["completed_capabilities"] == []

    # Duplication intentionally does not copy Discovery state. The Studio lifecycle
    # initializes an independent Discovery session before messaging the duplicate.
    context = client.get(f"/api/v1/business-discovery/context/{body['id']}")
    assert context.status_code == 404

    started = client.post(f"/api/v1/business-discovery/start?project_id={body['id']}")
    assert started.status_code == 201
    assert started.json()["project_id"] == body["id"]

    message = client.post(
        "/api/v1/business-discovery/message",
        json={
            "project_id": body["id"],
            "message": "We run a marketing agency.",
        },
    )
    assert message.status_code == 200
    assert message.json()["knowledge"]["industry"]["value"] == "marketing"


def test_workspace_progress_marks_live_deployment_as_complete():
    from types import SimpleNamespace
    from datetime import datetime, timezone
    from app.routes.projects import _workspace_progress

    deployment = SimpleNamespace(created_at=datetime.now(timezone.utc), status=SimpleNamespace(value="deployed"))
    completed, next_capability = _workspace_progress(None, None, None, None, object(), [deployment])

    assert "generation" in completed
    assert "preview" in completed
    assert "deployment" in completed
    assert next_capability is None


@pytest.mark.anyio
async def test_workspace_uses_persisted_execution_state_before_deployment():
    from app.models import Project, WebsiteGeneration, WebsiteExecutionState
    from app.store import InMemoryRepository
    repo = InMemoryRepository()
    project = await repo.create_project("Execution State")
    await repo.create_generation(WebsiteGeneration(project_id=project.id))
    await repo.save_execution_state(WebsiteExecutionState(project_id=project.id, generation_version=1, build_status="succeeded", build_result={"status": "succeeded"}, validation_status="passed"))
    state = await repo.get_execution_state(project.id)
    assert state is not None and state.validation_status == "passed"
