from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.security import get_user

from app.models import (
    CreateProjectRequest,
    DuplicateProjectRequest,
    Project,
    ProjectStatus,
    UpdateProjectRequest,
    WorkspaceSummary,
    WebsiteExecutionState,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Project, status_code=201)
async def create_project(request: CreateProjectRequest, http_request: Request):
    return await http_request.app.state.repository.create_project(request.name, get_user(http_request).id)


@router.get("", response_model=list[Project])
async def list_projects(http_request: Request):
    user = get_user(http_request)
    # Development mode is intentionally a single local workspace. Historical
    # fixtures may have been created under different owners/tenants, so the
    # project picker must remain able to see the complete local dataset.
    # Production/authenticated users retain tenant-scoped visibility.
    if user.auth_type == "development":
        return await http_request.app.state.repository.list_projects()
    return await http_request.app.state.repository.list_projects_for_user(user.id, user.tenant_id)


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


def _workspace_progress(context, strategy, design, specification, generation, deployments, execution_state=None):
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

    # Deployment is the durable completion signal for the preview/deployment
    # boundary. Once the latest deployment is live, reopening the project must
    # not infer an unfinished Build/Preview state from transient execution
    # artifacts that only existed in the previous Studio session.
    latest_deployment = max(deployments, key=lambda d: d.created_at) if deployments else None
    if latest_deployment and latest_deployment.status.value == "deployed":
        completed.extend(["preview", "deployment"])
        return completed, None

    if execution_state and generation:
        if execution_state.preview_status == "started":
            completed.append("preview")
            return completed, "deployment"
        if execution_state.validation_status == "passed":
            return completed, "preview"
        if execution_state.build_status == "succeeded":
            return completed, "build"

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
    execution_state = await repository.get_execution_state(project_id)

    completed, next_capability = _workspace_progress(context, strategy, design, specification, generation, deployments, execution_state)
    if next_capability == "preview" and not generation:
        next_capability = "generation"

    current_stage = next_capability or "deployment"
    if project.status == ProjectStatus.ARCHIVED:
        current_stage = "archived"

    activity_dates = [project.created_at]
    for artifact in (context, strategy, design, specification, generation):
    	if artifact:
        	created_at = getattr(artifact, "created_at", None)
        	if created_at:
            		activity_dates.append(created_at)

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
        execution_state=execution_state,
    )


@router.post("/{project_id}/duplicate", response_model=Project, status_code=201)
async def duplicate_project(project_id: UUID, request: DuplicateProjectRequest, http_request: Request):
    repository = http_request.app.state.repository
    try:
        return await repository.duplicate_project(project_id, request.name, get_user(http_request).id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID, http_request: Request):
    project = await http_request.app.state.repository.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
