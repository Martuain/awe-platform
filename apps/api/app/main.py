from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware import AuthenticationMiddleware
from app.services.preview import WebsitePreviewService

from app.routes import health, projects, discovery, strategy, design, specification, generation, validation, mock, build, preview, deployment, performance, monitoring, auth, team, content
from app.store import build_repository, init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    app.state.repository = build_repository()
    # Preview runtimes are disposable, but a local deployment intentionally
    # reuses one as its live deployment endpoint. Preserve those deployed
    # project runtimes across API restarts; clean only true preview orphans.
    preserved_project_ids: set[str] = set()
    for project in await app.state.repository.list_projects():
        deployments = await app.state.repository.list_deployments(project.id)
        if any(item.status.value == "deployed" for item in deployments):
            preserved_project_ids.add(str(project.id))
    await asyncio.to_thread(WebsitePreviewService.cleanup_orphaned_runtimes, preserved_project_ids)
    yield


app = FastAPI(
    title="AWE Platform API",
    version="1.0.6",
    description="API-first foundation for AWE Studio.",
    lifespan=lifespan,
)

app.add_middleware(AuthenticationMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(team.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(discovery.router, prefix="/api/v1")
app.include_router(strategy.router, prefix="/api/v1")
app.include_router(design.router, prefix="/api/v1")
app.include_router(specification.router, prefix="/api/v1")
app.include_router(generation.router, prefix="/api/v1")
app.include_router(validation.router, prefix="/api/v1")
app.include_router(mock.router, prefix="/api/v1")
app.include_router(build.router, prefix="/api/v1")
app.include_router(preview.router, prefix="/api/v1")
app.include_router(deployment.router, prefix="/api/v1")
app.include_router(performance.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")
