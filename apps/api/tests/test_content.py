from uuid import uuid4

from app.main import app
from app.models import Project
from app.security import DEV_USER_ID
from app.store import InMemoryRepository


def _new_project(client, name="CAP-034 Content"):
    response = client.post(
        "/api/v1/projects",
        json={"name": f"{name} {uuid4().hex[:8]}"},
    )
    assert response.status_code == 201
    return response.json()


def test_content_can_be_created_as_draft(client):
    project = _new_project(client)

    response = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "Welcome to our website",
        },
    )

    assert response.status_code in (200, 201)

    content = response.json()
    assert content["project_id"] == project["id"]
    assert content["page"] == "home"
    assert content["key"] == "headline"
    assert content["content_type"] == "text"
    assert content["value"] == "Welcome to our website"
    assert content["version"] == 1
    assert content["status"] == "draft"
    assert content["published_at"] is None
    assert content["content_id"]


def test_content_update_increments_version(client):
    project = _new_project(client)

    first = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "Original headline",
        },
    )

    assert first.status_code in (200, 201)
    first_content = first.json()

    second = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "Updated headline",
        },
    )

    assert second.status_code in (200, 201)
    second_content = second.json()

    assert second_content["content_id"] == first_content["content_id"]
    assert second_content["version"] == 2
    assert second_content["status"] == "draft"
    assert second_content["value"] == "Updated headline"
    assert second_content["published_at"] is None


def test_content_version_history_preserves_previous_revisions(client):
    project = _new_project(client)

    first = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "Version one",
        },
    )

    assert first.status_code in (200, 201)
    content_id = first.json()["content_id"]

    second = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "Version two",
        },
    )

    assert second.status_code in (200, 201)

    history = client.get(
        f"/api/v1/website-content/{project['id']}/{content_id}/versions"
    )

    assert history.status_code == 200

    versions = history.json()

    assert len(versions) >= 2

    version_numbers = [item["version"] for item in versions]
    assert 1 in version_numbers
    assert 2 in version_numbers

    values = [item["value"] for item in versions]
    assert "Version one" in values
    assert "Version two" in values


def test_content_can_be_published(client):
    project = _new_project(client)

    created = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "Publish me",
        },
    )

    assert created.status_code in (200, 201)

    published = client.post(
        f"/api/v1/website-content/{project['id']}/publish"
    )

    assert published.status_code == 200

    content_response = client.get(
        f"/api/v1/website-content/{project['id']}"
    )

    assert content_response.status_code == 200

    contents = content_response.json()
    assert len(contents) >= 1

    headline = next(
        item
        for item in contents
        if item["key"] == "headline"
        and item["page"] == "home"
    )

    assert headline["status"] == "published"
    assert headline["published_at"] is not None


def test_editing_published_content_returns_it_to_draft(client):
    project = _new_project(client)

    created = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "Published headline",
        },
    )

    assert created.status_code in (200, 201)

    published = client.post(
        f"/api/v1/website-content/{project['id']}/publish"
    )

    assert published.status_code == 200

    updated = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "New draft headline",
        },
    )

    assert updated.status_code in (200, 201)

    content = updated.json()

    assert content["version"] == 2
    assert content["status"] == "draft"
    assert content["value"] == "New draft headline"
    assert content["published_at"] is None

    published_view = client.get(
        f"/api/v1/website-content/{project['id']}?status=published"
    )
    assert published_view.status_code == 200
    published_items = published_view.json()
    assert any(
        item["page"] == "home"
        and item["key"] == "headline"
        and item["value"] == "Published headline"
        and item["version"] == 1
        for item in published_items
    )
    assert not any(item["value"] == "New draft headline" for item in published_items)


def test_content_can_store_multiple_pages_and_keys(client):
    project = _new_project(client)

    home = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "Home headline",
        },
    )

    about = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={
            "page": "about",
            "key": "headline",
            "content_type": "text",
            "value": "About headline",
        },
    )

    assert home.status_code in (200, 201)
    assert about.status_code in (200, 201)

    response = client.get(
        f"/api/v1/website-content/{project['id']}"
    )

    assert response.status_code == 200

    contents = response.json()

    matching = {
        (item["page"], item["key"]): item["value"]
        for item in contents
    }

    assert matching[("home", "headline")] == "Home headline"
    assert matching[("about", "headline")] == "About headline"


def test_content_project_access_is_owner_scoped(client):
    repo = InMemoryRepository()

    owned_project = Project(
        name="Owned Content",
        owner_id=DEV_USER_ID,
    )

    private_project = Project(
        name="Private Content",
        owner_id=uuid4(),
    )

    repo.projects[owned_project.id] = owned_project
    repo.projects[private_project.id] = private_project

    app.state.repository = repo

    allowed = client.get(
        f"/api/v1/website-content/{owned_project.id}"
    )

    assert allowed.status_code == 200

    denied = client.get(
        f"/api/v1/website-content/{private_project.id}"
    )

    assert denied.status_code == 403


def test_content_write_is_denied_for_project_without_access(client):
    repo = InMemoryRepository()

    private_project = Project(
        name="Private Content Write",
        owner_id=uuid4(),
    )

    repo.projects[private_project.id] = private_project

    app.state.repository = repo

    response = client.put(
        f"/api/v1/website-content/{private_project.id}",
        json={
            "page": "home",
            "key": "headline",
            "content_type": "text",
            "value": "Should not be writable",
        },
    )

    assert response.status_code == 403


def test_invalid_content_project_id_is_rejected(client):
    response = client.get(
        "/api/v1/website-content/not-a-valid-project-id"
    )

    assert response.status_code == 400


def test_publish_content_synchronizes_live_preview(client, monkeypatch):
    project = _new_project(client, "CAP-035 Live Content")
    response = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={"page": "/", "key": "headline", "content_type": "text", "value": "Draft headline"},
    )
    assert response.status_code in (200, 201)

    called = []
    async def refresh(self, project_id):
        called.append(project_id)
        from app.models import WebsitePreview, WebsitePreviewStatus
        return WebsitePreview(
            project_id=project_id,
            generation_version=1,
            status=WebsitePreviewStatus.STARTED,
            url="http://127.0.0.1:49152",
            container_id="preview-test",
        )

    monkeypatch.setattr("app.routes.content.WebsitePreviewService.refresh_published_content", refresh)
    published = client.post(f"/api/v1/website-content/{project['id']}/publish")
    assert published.status_code == 200
    assert published.json()[0]["status"] == "published"
    assert called == [__import__("uuid").UUID(project["id"])]


def test_generated_site_exposes_runtime_content_contract():
    from app.services.generation import WebsiteGenerationService
    import inspect
    source = inspect.getsource(WebsiteGenerationService.generate)
    assert 'GeneratedFile(path="awe-content.json"' in source
    assert 'readFile("/workspace/awe-content.json"' in source
    assert 'dynamic = "force-dynamic"' in source


def test_published_content_remains_authoritative_after_draft_edit(client, monkeypatch):
    project = _new_project(client, "CAP-036 Published Boundary")
    created = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={"page": "/", "key": "headline", "content_type": "text", "value": "Official v1"},
    )
    assert created.status_code in (200, 201)
    assert client.post(f"/api/v1/website-content/{project['id']}/publish").status_code == 200

    draft = client.put(
        f"/api/v1/website-content/{project['id']}",
        json={"page": "/", "key": "headline", "content_type": "text", "value": "Unpublished v2 draft"},
    )
    assert draft.status_code in (200, 201)

    published = client.get(f"/api/v1/website-content/{project['id']}?status=published")
    assert published.status_code == 200
    headline = next(item for item in published.json() if item["page"] == "/" and item["key"] == "headline")
    assert headline["value"] == "Official v1"
    assert headline["version"] == 1

    current = client.get(f"/api/v1/website-content/{project['id']}")
    assert current.status_code == 200
    draft_headline = next(item for item in current.json() if item["page"] == "/" and item["key"] == "headline")
    assert draft_headline["value"] == "Unpublished v2 draft"
    assert draft_headline["status"] == "draft"
