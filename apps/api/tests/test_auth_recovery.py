import os
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.services.preview import WebsitePreviewService


def test_email_verification_and_password_reset_tokens_are_single_use(monkeypatch):
    monkeypatch.setenv("AWE_AUTH_MODE", "strict")
    monkeypatch.setenv("AWE_AUTH_EXPOSE_TEST_TOKENS", "true")
    monkeypatch.setattr(
        WebsitePreviewService,
        "cleanup_orphaned_runtimes",
        staticmethod(lambda preserved_project_ids: None),
    )
    with TestClient(app) as client:
        email = f"recovery-cap031-{uuid4().hex[:12]}@example.com"
        password = "initial-password-123"
        r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
        assert r.status_code == 201
        r = client.post("/api/v1/auth/verify-email/request", json={"email": email})
        assert r.status_code == 202 and r.json().get("verification_token")
        token = r.json()["verification_token"]
        assert client.post("/api/v1/auth/verify-email/confirm", json={"token": token}).status_code == 200
        assert client.post("/api/v1/auth/verify-email/confirm", json={"token": token}).status_code == 400
        r = client.post("/api/v1/auth/password-reset/request", json={"email": email})
        assert r.status_code == 202 and r.json().get("reset_token")
        reset = r.json()["reset_token"]
        assert client.post("/api/v1/auth/password-reset/confirm", json={"token": reset, "password": "new-password-123"}).status_code == 200
        assert client.post("/api/v1/auth/password-reset/confirm", json={"token": reset, "password": "another-password-123"}).status_code == 400
        assert client.post("/api/v1/auth/login", json={"email": email, "password": "new-password-123"}).status_code == 200
