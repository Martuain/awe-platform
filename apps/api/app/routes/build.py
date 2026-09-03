from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Request
from app.models import WebsiteBuildPlan
from app.services.build import WebsiteBuildService

router = APIRouter(prefix="/website-build", tags=["website-build"])


@router.post("/plan", response_model=WebsiteBuildPlan)
async def plan_build(project_id: UUID, request: Request):
    try:
        return await WebsiteBuildService(request.app.state.repository).plan(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {exc.args[0]}") from exc


@router.post("/execute")
async def execute_build(
    project_id: UUID,
    request: Request,
    install_timeout_seconds: int = Query(300, ge=1, le=600),
    build_timeout_seconds: int = Query(180, ge=1, le=600),
):
    try:
        return await WebsiteBuildService(request.app.state.repository).execute(
            project_id,
            install_timeout_seconds=install_timeout_seconds,
            build_timeout_seconds=build_timeout_seconds,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {exc.args[0]}") from exc
