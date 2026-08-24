from fastapi.testclient import TestClient
from app.main import app


def _generate(client):
    pid = client.post("/api/v1/projects", json={"name": "Validation Demo"}).json()["id"]
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
    result = client.post(f"/api/v1/website-generation/generate?project_id={pid}")
    assert result.status_code == 201
    return pid


def test_validation_returns_passed_checks_and_preview():
    with TestClient(app) as client:
        pid = _generate(client)
        result = client.post(f"/api/v1/website-validation/validate?project_id={pid}")
        assert result.status_code == 201
        body = result.json()
        assert body["status"] == "passed"
        assert all(body["checks"].values())
        assert body["preview"]["format"] == "html"
        assert "CAP-006 preview" in body["preview"]["html"]
