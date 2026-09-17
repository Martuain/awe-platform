from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Project
from app.security import DEV_USER_ID, _hash_secret, _password_hash, _verify_password, get_user, require_scope, AuthenticatedUser
from app.store import InMemoryRepository


def app_with_repo(repo):
    app.state.repository = repo
    return TestClient(app)


def test_development_auth_identity_is_explicit_and_stable():
    repo = InMemoryRepository()
    client = app_with_repo(repo)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["id"] == str(DEV_USER_ID)
    assert response.json()["auth_type"] == "development"


def test_project_access_is_owner_scoped():
    repo = InMemoryRepository()
    project = Project(name="Private", owner_id=uuid4())
    repo.projects[project.id] = project
    client = app_with_repo(repo)
    response = client.get(f"/api/v1/projects/{project.id}")
    assert response.status_code == 403


def test_project_creation_assigns_authenticated_owner():
    repo = InMemoryRepository()
    client = app_with_repo(repo)
    response = client.post("/api/v1/projects", json={"name": "Owned"})
    assert response.status_code == 201
    assert response.json()["owner_id"] == str(DEV_USER_ID)


def test_password_hash_is_salted_and_verifiable():
    encoded = _password_hash("a-strong-password")
    assert encoded != _password_hash("a-strong-password")
    assert _verify_password("a-strong-password", encoded)
    assert not _verify_password("wrong-password", encoded)


def test_api_secret_hash_is_not_the_secret():
    secret = "awe_example-secret"
    assert _hash_secret(secret) != secret


def test_api_key_scope_is_enforced():
    from fastapi import Request
    user = AuthenticatedUser(uuid4(), uuid4(), "client@example.test", "api_key", uuid4(), ("project:read",))
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b"", "server": ("test", 80), "client": ("test", 80), "scheme": "http", "root_path": ""})
    request.state.user = user
    require_scope(request, "project:read")
    with pytest.raises(Exception):
        require_scope(request, "deployment:write")

def test_strict_mode_rejects_unauthenticated_requests(monkeypatch):
    monkeypatch.setenv("AWE_AUTH_MODE", "strict")
    client = app_with_repo(InMemoryRepository())
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
