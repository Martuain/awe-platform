from fastapi import APIRouter, Request

from app.security import get_user

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("")
async def monitoring(request: Request):
    projects = await request.app.state.repository.list_projects(get_user(request).id)
    deployments = []
    for project in projects:
        deployments.extend(await request.app.state.repository.list_deployments(project.id))
    return {
        "status": "ok",
        "service": "awe-api",
        "projects": len(projects),
        "deployments": len(deployments),
        "deployed": sum(item.status.value == "deployed" for item in deployments),
        "failed": sum(item.status.value == "failed" for item in deployments),
    }
