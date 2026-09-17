from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.models import WebsiteDeployment
from app.services.preview import WebsitePreviewService
from app.services.deployment import DeploymentService

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.post("", response_model=WebsiteDeployment)
async def deploy(project_id: UUID, request: Request):
    try:
        return await DeploymentService(request.app.state.repository).deploy(project_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=list[WebsiteDeployment])
async def list_deployments(project_id: UUID, request: Request):
    return await DeploymentService(request.app.state.repository).list(project_id)


@router.get("/{deployment_id}", response_model=WebsiteDeployment)
async def get_deployment(deployment_id: UUID, request: Request):
    try:
        return await DeploymentService(request.app.state.repository).get(deployment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {exc.args[0]}") from exc


@router.post("/{deployment_id}/stop", response_model=WebsiteDeployment)
async def stop_deployment(deployment_id: UUID, request: Request):
    try:
        return await DeploymentService(request.app.state.repository).stop(deployment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Missing artifact: {exc.args[0]}") from exc


@router.post("/{deployment_id}/restore")
async def restore_deployment(deployment_id: UUID, project_id: UUID, request: Request):
    """Restore a specific immutable deployment snapshot without promoting it."""
    try:
        deployment = await DeploymentService(request.app.state.repository).get(deployment_id)
        if deployment.project_id != project_id:
            raise KeyError("deployment")
        preview = await WebsitePreviewService(request.app.state.repository).restore_deployment(
            project_id, deployment_id
        )
        # Runtime identity is disposable; keep the durable deployment row stable.
        deployment.runtime_id = preview.container_id
        deployment.url = preview.url
        return await request.app.state.repository.update_deployment(deployment)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Missing deployment: {exc.args[0]}") from exc
