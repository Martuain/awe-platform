from fastapi import APIRouter, HTTPException
from app.models import CreateProjectRequest, Project
from app.store import projects

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model=Project, status_code=201)
async def create_project(request: CreateProjectRequest):
    project = Project(name=request.name)
    projects[project.id] = project
    return project

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id):
    project = projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
