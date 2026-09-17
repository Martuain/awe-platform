import base64
import json
from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app
from app.services.preview import WebsitePreviewService


def _mock_code(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def test_mock_oidc_state_is_single_use_and_links_existing_user(monkeypatch):
    monkeypatch.setenv("AWE_AUTH_MODE", "strict")
    monkeypatch.setenv("AWE_SSO_MODE", "mock")
    monkeypatch.setenv("AWE_OIDC_ISSUER", "https://mock-idp.example")
    monkeypatch.setenv("AWE_OIDC_CLIENT_ID", "awe-test")
    monkeypatch.setenv("AWE_OIDC_REDIRECT_URI", "http://testserver/api/v1/auth/sso/oidc/callback")
    monkeypatch.setattr(
        WebsitePreviewService,
        "cleanup_orphaned_runtimes",
        staticmethod(lambda preserved_project_ids: None),
    )
    with TestClient(app) as client:
        email = f"sso-cap032-{uuid4().hex[:12]}@example.com"
        assert client.post("/api/v1/auth/register", json={"email": email, "password": "initial-password-123"}).status_code == 201
        start = client.get("/api/v1/auth/sso/oidc/start", follow_redirects=False)
        assert start.status_code == 302
        location = start.headers["location"]
        assert "state=" in location and "nonce=" in location
        from urllib.parse import parse_qs, urlparse
        params = parse_qs(urlparse(location).query)
        state, nonce = params["state"][0], params["nonce"][0]
        code = _mock_code({"sub": "provider-user-1", "email": email, "email_verified": True, "nonce": nonce})
        callback = client.get("/api/v1/auth/sso/oidc/callback", params={"state": state, "code": code})
        assert callback.status_code == 200
        assert callback.json()["provider"] == "oidc"
        assert client.get("/api/v1/auth/sso/oidc/callback", params={"state": state, "code": code}).status_code == 400


def test_mock_oidc_auto_provisions_only_verified_external_identity(monkeypatch):
    monkeypatch.setenv("AWE_AUTH_MODE", "strict")
    monkeypatch.setenv("AWE_SSO_MODE", "mock")
    monkeypatch.setenv("AWE_SSO_AUTO_PROVISION", "true")
    monkeypatch.setenv("AWE_OIDC_ISSUER", "https://mock-idp.example")
    monkeypatch.setenv("AWE_OIDC_CLIENT_ID", "awe-test")
    monkeypatch.setenv("AWE_OIDC_REDIRECT_URI", "http://testserver/api/v1/auth/sso/oidc/callback")
    monkeypatch.setattr(
        WebsitePreviewService,
        "cleanup_orphaned_runtimes",
        staticmethod(lambda preserved_project_ids: None),
    )

    with TestClient(app) as client:
        start = client.get("/api/v1/auth/sso/oidc/start", follow_redirects=False)
        from urllib.parse import parse_qs, urlparse
        params = parse_qs(urlparse(start.headers["location"]).query)
        state, nonce = params["state"][0], params["nonce"][0]
        code = _mock_code({"sub": "provider-user-2", "email": f"new-{uuid4().hex[:8]}@example.com", "email_verified": True, "nonce": nonce})
        response = client.get("/api/v1/auth/sso/oidc/callback", params={"state": state, "code": code})
        assert response.status_code == 200
        assert response.json()["access_token"]
