from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.models import CreateProjectRequest, Project, WorkspaceSummary

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=201)
async def create_project(request: CreateProjectRequest, http_request: Request):
    return await http_request.app.state.repository.create_project(request.name)



@router.get("", response_model=list[Project])
async def list_projects(http_request: Request):
    return await http_request.app.state.repository.list_projects()


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

    current_stage = "discovery"
    if context and context.status.value == "approved":
        current_stage = "strategy"
    if strategy and strategy.status.value == "approved":
        current_stage = "design"
    if design and design.status.value == "approved":
        current_stage = "specification"
    if specification and specification.status.value == "approved":
        current_stage = "generation"
    if generation:
        current_stage = "preview"
    if any(d.status.value == "deployed" for d in deployments):
        current_stage = "deployment"

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
    )

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID, http_request: Request):
    project = await http_request.app.state.repository.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
