from fastapi import FastAPI
from app.routes import health, projects, discovery

app = FastAPI(
    title="AWE Platform API",
    version="0.1.0",
    description="API-first foundation for AWE Studio."
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(discovery.router, prefix="/api/v1")
