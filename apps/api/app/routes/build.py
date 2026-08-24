from uuid import UUID
from fastapi import APIRouter, HTTPException, Request
from app.models import WebsiteBuildPlan
from app.services.build import WebsiteBuildService

router = APIRouter(prefix="/website-build", tags=["website-build"])


@router.post("/plan", response_model=WebsiteBuildPlan)
async def plan_build(project_id: UUID, request: Request):
    try:
        return await WebsiteBuildService(request.app.state.repository).plan(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {exc.args[0]}") from exc
