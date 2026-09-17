import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    original_repository = getattr(app.state, "repository", None)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if original_repository is not None:
            app.state.repository = original_repository


@pytest.fixture(autouse=True)
def development_auth_mode(monkeypatch):
    """Keep the legacy API test suite on the local development auth contract.

    Security-specific tests opt into strict mode explicitly with monkeypatch.
    This prevents a caller's shell/CI AWE_AUTH_MODE from leaking into unrelated
    tests and turning expected authorization checks into authentication failures.
    """
    monkeypatch.setenv("AWE_AUTH_MODE", "development")
