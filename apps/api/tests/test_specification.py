from fastapi.testclient import TestClient
from app.main import app


def test_website_specification_requires_approved_design_and_is_approvable():
    with TestClient(app) as client:
        pid = client.post("/api/v1/projects", json={"name": "Specification Demo"}).json()["id"]
        assert client.post(f"/api/v1/website-specification/generate?project_id={pid}").status_code == 404
        client.post(f"/api/v1/business-discovery/start?project_id={pid}")
        client.post("/api/v1/business-discovery/message", json={"project_id": pid, "message": "We run a marketing agency."})
        client.post("/api/v1/business-discovery/message", json={"project_id": pid, "message": "Our goal is to generate leads."})
        client.post(f"/api/v1/business-discovery/approve/{pid}")
        client.post(f"/api/v1/website-strategy/generate?project_id={pid}")
        client.post(f"/api/v1/website-strategy/{pid}/approve")
        assert client.post(f"/api/v1/website-specification/generate?project_id={pid}").status_code == 404
        client.post(f"/api/v1/brand-design/generate?project_id={pid}")
        client.post(f"/api/v1/brand-design/{pid}/approve")
        generated = client.post(f"/api/v1/website-specification/generate?project_id={pid}")
        assert generated.status_code == 201
        body = generated.json()
        assert body["status"] == "ready_for_review"
        assert body["source_strategy_version"] == 1
        assert body["source_design_version"] == 1
        assert len(body["pages"]) == 4
        assert body["acceptance_criteria"]
        approved = client.post(f"/api/v1/website-specification/{pid}/approve")
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
