from app.models import WebsiteBuildPlan, WebsiteBuildStatus
from app.store import Repository


class WebsiteBuildService:
    """Creates the CAP-007 build contract without executing generated code.

    Execution is deliberately deferred to a real sandbox adapter. This service
    establishes the boundary and makes the build lifecycle testable now.
    """

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def plan(self, project_id) -> WebsiteBuildPlan:
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError("generation")
        if generation.status.value not in {"generated", "validated"}:
            return WebsiteBuildPlan(
                project_id=project_id,
                generation_version=generation.version,
                status=WebsiteBuildStatus.REJECTED,
                diagnostics=["Website Generation is not in an executable lifecycle state."],
                files=[f.path for f in generation.files],
            )
        diagnostics = []
        paths = [f.path for f in generation.files]
        if "package.json" not in paths:
            diagnostics.append("Generated artifact is missing package.json.")
        if not any(p.startswith("app/") for p in paths):
            diagnostics.append("Generated artifact contains no Next.js App Router files.")
        return WebsiteBuildPlan(
            project_id=project_id,
            generation_version=generation.version,
            status=WebsiteBuildStatus.PLANNED if not diagnostics else WebsiteBuildStatus.REJECTED,
            diagnostics=diagnostics,
            files=paths,
        )
