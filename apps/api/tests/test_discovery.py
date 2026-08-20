from fastapi.testclient import TestClient

from app.main import app


def test_discovery_lifecycle():
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Demo Studio"})
        assert project.status_code == 201
        project_id = project.json()["id"]

        started = client.post(f"/api/v1/business-discovery/start?project_id={project_id}")
        assert started.status_code == 201
        assert started.json()["status"] == "collecting"

        partial = client.post("/api/v1/business-discovery/message", json={"project_id": project_id, "message": "We run a marketing agency."})
        assert partial.status_code == 200
        assert partial.json()["knowledge"]["industry"]["value"] == "marketing"
        assert partial.json()["status"] == "collecting"

        complete = client.post("/api/v1/business-discovery/message", json={"project_id": project_id, "message": "Our goal is to generate leads."})
        assert complete.status_code == 200
        assert complete.json()["status"] == "awaiting_approval"

        approved = client.post(f"/api/v1/business-discovery/approve/{project_id}")
        assert approved.status_code == 200
        assert approved.json()["context"]["status"] == "approved"

        immutable = client.post("/api/v1/business-discovery/message", json={"project_id": project_id, "message": "This must not mutate approved context."})
        assert immutable.status_code == 409
