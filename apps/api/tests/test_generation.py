from fastapi.testclient import TestClient
from app.main import app


def test_generation_requires_approved_specification_and_generates_pages():
    with TestClient(app) as client:
        pid = client.post("/api/v1/projects", json={"name": "Generation Demo"}).json()["id"]
        assert client.post(f"/api/v1/website-generation/generate?project_id={pid}").status_code == 404
        client.post(f"/api/v1/business-discovery/start?project_id={pid}")
        client.post("/api/v1/business-discovery/message", json={"project_id": pid, "message": "We run a marketing agency."})
        client.post("/api/v1/business-discovery/message", json={"project_id": pid, "message": "Our goal is to generate leads."})
        client.post(f"/api/v1/business-discovery/approve/{pid}")
        client.post(f"/api/v1/website-strategy/generate?project_id={pid}")
        client.post(f"/api/v1/website-strategy/{pid}/approve")
        client.post(f"/api/v1/brand-design/generate?project_id={pid}")
        client.post(f"/api/v1/brand-design/{pid}/approve")
        client.post(f"/api/v1/website-specification/generate?project_id={pid}")
        client.post(f"/api/v1/website-specification/{pid}/approve")
        generated = client.post(f"/api/v1/website-generation/generate?project_id={pid}")
        assert generated.status_code == 201
        body = generated.json()
        assert body["status"] == "validated"
        assert body["source_specification_version"] == 1
        assert body["pages_generated"]
        assert any(file["path"] == "app/page.tsx" for file in body["files"])
        assert body["validation"]["specification_approved"] is True
