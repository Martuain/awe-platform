from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.models import CreateProjectRequest, Project, ProjectStatus, UpdateProjectRequest, WorkspaceSummary

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=201)
async def create_project(request: CreateProjectRequest, http_request: Request):
    return await http_request.app.state.repository.create_project(request.name)


@router.get("", response_model=list[Project])
async def list_projects(http_request: Request):
    return await http_request.app.state.repository.list_projects()


@router.patch("/{project_id}", response_model=Project)
async def update_project(project_id: UUID, request: UpdateProjectRequest, http_request: Request):
    repository = http_request.app.state.repository
    project = await repository.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        return await repository.update_project(project_id, request.status)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


def _workspace_progress(context, strategy, design, specification, generation, deployments):
    completed: list[str] = []
    if context and context.status.value == "approved":
        completed.append("discovery")
    if strategy and strategy.status.value == "approved":
        completed.append("strategy")
    if design and design.status.value == "approved":
        completed.append("design")
    if specification and specification.status.value == "approved":
        completed.append("specification")
    if generation:
        completed.append("generation")
    if generation and any(d.status.value == "deployed" for d in deployments):
        completed.append("deployment")

    ordered = ["discovery", "strategy", "design", "specification", "generation", "preview", "deployment"]
    for stage in ordered:
        if stage not in completed:
            return completed, stage
    return completed, None


@router.get("/{project_id}/workspace", response_model=WorkspaceSummary)
async def get_workspace(project_id: UUID, http_request: Request):
    repository = http_request.app.state.repository
    project = await repository.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    context = await repository.get_context(project_id)
    strategy = await repository.get_strategy(project_id)
    design = await repository.get_design(project_id)
    specification = await repository.get_specification(project_id)
    generation = await repository.get_generation(project_id)
    deployments = await repository.list_deployments(project_id)

    completed, next_capability = _workspace_progress(context, strategy, design, specification, generation, deployments)
    if next_capability == "preview" and not generation:
        next_capability = "generation"

    current_stage = next_capability or "deployment"
    if project.status == ProjectStatus.ARCHIVED:
        current_stage = "archived"

    activity_dates: list[datetime] = [project.created_at]
    for artifact in (context, strategy, design, specification, generation):
        if artifact:
            activity_dates.append(artifact.created_at)
    activity_dates.extend(d.created_at for d in deployments)
    last_activity = max(activity_dates) if activity_dates else project.created_at
    latest = max(deployments, key=lambda d: d.created_at) if deployments else None

    return WorkspaceSummary(
        project=project,
        current_stage=current_stage,
        discovery_version=context.version if context else None,
        strategy_version=strategy.version if strategy else None,
        design_version=design.version if design else None,
        specification_version=specification.version if specification else None,
        generation_version=generation.version if generation else None,
        deployment_count=len(deployments),
        latest_deployment_status=latest.status.value if latest else None,
        completed_capabilities=completed,
        next_capability=next_capability,
        last_activity_at=last_activity,
    )


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID, http_request: Request):
    project = await http_request.app.state.repository.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
