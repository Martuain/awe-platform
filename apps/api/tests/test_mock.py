from fastapi.testclient import TestClient
from app.main import app


def _ready_project(client: TestClient) -> str:
    pid = client.post("/api/v1/projects", json={"name": "Customer Mock Demo"}).json()["id"]
    client.post(f"/api/v1/business-discovery/start?project_id={pid}")
    client.post("/api/v1/business-discovery/message", json={"project_id": pid, "message": "We run a marketing agency focused on lead generation. We help B2B marketing decision-makers improve commercial growth and want to attract qualified prospects."})
    client.post(f"/api/v1/business-discovery/approve/{pid}")
    assert client.post(f"/api/v1/website-strategy/generate?project_id={pid}").status_code == 201
    assert client.post(f"/api/v1/website-strategy/{pid}/approve").status_code == 200
    assert client.post(f"/api/v1/brand-design/generate?project_id={pid}").status_code == 201
    assert client.post(f"/api/v1/brand-design/{pid}/approve").status_code == 200
    assert client.post(f"/api/v1/website-specification/generate?project_id={pid}").status_code == 201
    assert client.post(f"/api/v1/website-specification/{pid}/approve").status_code == 200
    assert client.post(f"/api/v1/website-generation/generate?project_id={pid}").status_code == 201
    return pid


def test_customer_mock_is_created_and_approved_before_build(client):
    pid = _ready_project(client)
    mock = client.post(f"/api/v1/website-mock/create?project_id={pid}")
    assert mock.status_code == 201
    body = mock.json()
    assert body["status"] == "ready_for_review"
    assert body["generation_version"] == 1
    files = client.get(f"/api/v1/website-generation/{pid}").json()["files"]
    assert any(item["path"] == "awe-preview.html" for item in files)
    assert "AWE generated website" in body["html"]
    assert "<!doctype html>" in body["html"]
    assert "Built from an approved AWE strategy and design" in body["html"]
    approved = client.post(f"/api/v1/website-mock/{pid}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert client.post(f"/api/v1/website-mock/{pid}/approve").status_code == 409


def test_mock_feedback_can_produce_a_new_generation_and_mock_revision(client):
    pid = _ready_project(client)
    assert client.post(f"/api/v1/website-mock/create?project_id={pid}").status_code == 201
    revised = client.post(
        f"/api/v1/website-mock/{pid}/revise",
        json={"feedback": "headline: Grow your pipeline with AWE"},
    )
    assert revised.status_code == 201
    body = revised.json()
    assert body["status"] == "ready_for_review"
    assert body["version"] == 2
    assert body["generation_version"] == 2
    assert "Grow your pipeline with AWE" in body["html"]

    generation = client.get(f"/api/v1/website-generation/{pid}").json()
    assert generation["version"] == 2
    home = next(item["content"] for item in generation["files"] if item["path"] == "app/page.tsx")
    assert "Grow your pipeline with AWE" in home


def test_customer_mock_renders_current_persisted_content_and_internal_routes(client):
    pid = _ready_project(client)
    created = client.post(f"/api/v1/website-mock/create?project_id={pid}")
    assert created.status_code == 201

    updated = client.put(
        f"/api/v1/website-content/{pid}",
        json={"page": "/", "key": "headline", "content_type": "text", "value": "Latest user headline"},
    )
    assert updated.status_code in (200, 201)
    assert client.post(f"/api/v1/website-content/{pid}/publish").status_code == 200

    refreshed = client.get(f"/api/v1/website-mock/{pid}")
    assert refreshed.status_code == 200
    html = refreshed.json()["html"]
    assert "Latest user headline" in html
    assert "href="#awe-mock-page-home"" in html
    assert 'href="/about"' not in html


def test_customer_mock_revision_uses_current_content(client):
    pid = _ready_project(client)
    assert client.post(f"/api/v1/website-mock/create?project_id={pid}").status_code == 201
    assert client.put(
        f"/api/v1/website-content/{pid}",
        json={"page": "/", "key": "cta", "content_type": "text", "value": "Latest CTA"},
    ).status_code in (200, 201)
    assert client.post(f"/api/v1/website-content/{pid}/publish").status_code == 200
    revised = client.post(
        f"/api/v1/website-mock/{pid}/revise",
        json={"feedback": "headline: Revised headline"},
    )
    assert revised.status_code == 201
    assert "Latest CTA" in revised.json()["html"]
    assert "Revised headline" in revised.json()["html"]


def test_customer_mock_does_not_render_unpublished_draft_over_published_content(client):
    pid = _ready_project(client)
    assert client.post(f"/api/v1/website-mock/create?project_id={pid}").status_code == 201
    assert client.put(
        f"/api/v1/website-content/{pid}",
        json={"page": "/", "key": "headline", "content_type": "text", "value": "Official published headline"},
    ).status_code in (200, 201)
    assert client.post(f"/api/v1/website-content/{pid}/publish").status_code == 200
    assert client.put(
        f"/api/v1/website-content/{pid}",
        json={"page": "/", "key": "headline", "content_type": "text", "value": "Unpublished draft headline"},
    ).status_code in (200, 201)

    body = client.get(f"/api/v1/website-mock/{pid}").json()
    assert "Official published headline" in body["html"]
    assert "Unpublished draft headline" not in body["html"]
