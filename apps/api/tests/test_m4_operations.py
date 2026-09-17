from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models import GeneratedFile, WebsiteGeneration, WebsiteGenerationStatus
from app.routes import monitoring, performance
from app.store import InMemoryRepository


def app_with_repo(repo):
    app = FastAPI()
    app.state.repository = repo
    app.include_router(performance.router, prefix="/api/v1")
    app.include_router(monitoring.router, prefix="/api/v1")
    return app


def test_performance_check_reports_artifact_budgets():
    repo = InMemoryRepository()
    project_id = uuid4()
    import asyncio
    asyncio.run(repo.create_generation(WebsiteGeneration(
        project_id=project_id,
        status=WebsiteGenerationStatus.VALIDATED,
        files=[GeneratedFile(path="app/page.tsx", content="export default function Page(){return null}"), GeneratedFile(path="app/globals.css", content="body{margin:0}")],
    )))
    client = TestClient(app_with_repo(repo))
    response = client.post(f"/api/v1/website-performance/check?project_id={project_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "passed"
    assert body["total_bytes"] > 0
    assert len(body["checks"]) == 5


def test_performance_check_requires_generation():
    repo = InMemoryRepository()
    project_id = uuid4()
    client = TestClient(app_with_repo(repo))
    response = client.post(f"/api/v1/website-performance/check?project_id={project_id}")
    assert response.status_code == 404


def test_monitoring_reports_service_counts():
    repo = InMemoryRepository()
    client = TestClient(app_with_repo(repo))
    response = client.get("/api/v1/monitoring")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "awe-api"
