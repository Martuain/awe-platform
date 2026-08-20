from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.models import CreateProjectRequest, Project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=201)
async def create_project(request: CreateProjectRequest, http_request: Request):
    return await http_request.app.state.repository.create_project(request.name)


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID, http_request: Request):
    project = await http_request.app.state.repository.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
