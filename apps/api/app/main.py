from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health, projects, discovery, strategy, design, specification, generation
from app.store import build_repository, init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    app.state.repository = build_repository()
    yield


app = FastAPI(
    title="AWE Platform API",
    version="0.1.0",
    description="API-first foundation for AWE Studio.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(discovery.router, prefix="/api/v1")
app.include_router(strategy.router, prefix="/api/v1")
app.include_router(design.router, prefix="/api/v1")
app.include_router(specification.router, prefix="/api/v1")
app.include_router(generation.router, prefix="/api/v1")
