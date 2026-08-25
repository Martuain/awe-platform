from fastapi.testclient import TestClient

from app.main import app


def test_project_workspace_can_be_listed_and_resumed():
    with TestClient(app) as client:
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
