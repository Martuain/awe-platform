from fastapi.testclient import TestClient

from app.main import app


def test_strategy_requires_approved_discovery_and_generates_vertical_slice():
    with TestClient(app) as client:
        project = client.post("/api/v1/projects", json={"name": "Strategy Demo"})
        assert project.status_code == 201
        project_id = project.json()["id"]

        not_ready = client.post(f"/api/v1/website-strategy/generate?project_id={project_id}")
        assert not_ready.status_code == 404

        client.post(f"/api/v1/business-discovery/start?project_id={project_id}")
        client.post("/api/v1/business-discovery/message", json={"project_id": project_id, "message": "We run a marketing agency."})
        complete = client.post("/api/v1/business-discovery/message", json={"project_id": project_id, "message": "Our goal is to generate leads."})
        assert complete.status_code == 200
        assert complete.json()["status"] == "awaiting_approval"
        client.post(f"/api/v1/business-discovery/approve/{project_id}")

        generated = client.post(f"/api/v1/website-strategy/generate?project_id={project_id}")
        assert generated.status_code == 201
        body = generated.json()
        assert body["status"] == "ready_for_review"
        assert [page["path"] for page in body["sitemap"]] == ["/", "/about", "/services", "/contact"]
        assert body["content"]["primary_cta"]
        assert body["design"]["responsive_priority"] == "high"

        approved = client.post(f"/api/v1/website-strategy/{project_id}/approve")
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
