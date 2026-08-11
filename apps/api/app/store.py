from uuid import UUID
from app.models import Project, DiscoveryContext

projects: dict[UUID, Project] = {}
contexts: dict[UUID, DiscoveryContext] = {}
