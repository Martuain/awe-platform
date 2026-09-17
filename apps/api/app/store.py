from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models import (
    BusinessKnowledge,
    DiscoveryContext,
    DiscoverySession,
    DiscoveryStatus,
    KnowledgeField,
    DiscoverySource,
    Project,
    ProjectStatus,
    WebsiteStrategy,
    StrategyStatus,
    BrandDesignDirection,
    BrandDesignStatus,
    WebsiteSpecification,
    WebsiteSpecificationStatus,
    WebsiteGeneration,
    WebsiteMock,
    WebsiteMockStatus,
    WebsiteDeployment,
    DeploymentStatus,
    DeploymentLifecycleRole,
    TeamMember,
    TeamInvitation,
    TeamRole,
    WebsiteContentItem,
    WebsiteContentStatus,
    WebsiteExecutionState,
    WebsiteValidation,
    WebsitePreview,
)

DATABASE_URL = os.getenv("DATABASE_URL")


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="active")
    owner_id: Mapped[str] = mapped_column(String(36), index=True, default="00000000-0000-0000-0000-000000000001")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TeamMemberRow(Base):
    __tablename__ = "team_members"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TeamInvitationRow(Base):
    __tablename__ = "team_invitations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    inviter_id: Mapped[str] = mapped_column(String(36), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    role: Mapped[str] = mapped_column(String(32))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DiscoverySessionRow(Base):
    __tablename__ = "discovery_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(String(32), default="collecting")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ContextVersionRow(Base):
    __tablename__ = "context_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteStrategyRow(Base):
    __tablename__ = "website_strategies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)
    status: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteStrategyVersionRow(Base):
    __tablename__ = "website_strategy_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    strategy_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BrandDesignDirectionRow(Base):
    __tablename__ = "brand_design_directions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)
    status: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BrandDesignDirectionVersionRow(Base):
    __tablename__ = "brand_design_direction_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    design_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteSpecificationRow(Base):
    __tablename__ = "website_specifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)
    status: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))




class WebsiteContentRow(Base):
    __tablename__ = "website_content"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    page: Mapped[str] = mapped_column(String(200))
    content_key: Mapped[str] = mapped_column(String(200))
    content_type: Mapped[str] = mapped_column(String(32))
    value: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (Index("uq_website_content_project_page_key", "project_id", "page", "content_key", unique=True),)


class WebsiteContentVersionRow(Base):
    __tablename__ = "website_content_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    content_id: Mapped[str] = mapped_column(String(36), index=True)
    page: Mapped[str] = mapped_column(String(200))
    content_key: Mapped[str] = mapped_column(String(200))
    content_type: Mapped[str] = mapped_column(String(32))
    value: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class WebsiteGenerationRow(Base):
    __tablename__ = "website_generations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteMockRow(Base):
    __tablename__ = "website_mocks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    generation_version: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteMockVersionRow(Base):
    __tablename__ = "website_mock_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    mock_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteMockFeedbackRow(Base):
    __tablename__ = "website_mock_feedback"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    mock_id: Mapped[str] = mapped_column(String(36), index=True)
    mock_version: Mapped[int] = mapped_column(Integer)
    feedback: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteExecutionStateRow(Base):
    __tablename__ = "website_execution_states"
    project_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    generation_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    build_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    build_result: Mapped[str] = mapped_column(Text, default="{}")
    validation_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    validation_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preview_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteDeploymentRow(Base):
    __tablename__ = "website_deployments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    generation_version: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    lifecycle_role: Mapped[str] = mapped_column(String(32), default="historical", index=True)
    provider: Mapped[str] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    runtime_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    snapshot_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    diagnostics: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WebsiteGenerationVersionRow(Base):
    __tablename__ = "website_generation_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    generation_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteSpecificationVersionRow(Base):
    __tablename__ = "website_specification_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    specification_id: Mapped[str] = mapped_column(String(36), index=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SourceMessageRow(Base):
    __tablename__ = "source_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Repository:
    async def list_team_members(self, tenant_id: UUID) -> list[TeamMember]: ...
    async def get_team_role(self, tenant_id: UUID, user_id: UUID) -> TeamRole | None: ...
    async def add_team_member(self, member: TeamMember) -> TeamMember: ...
    async def create_team_invitation(self, invitation: TeamInvitation, token_hash: str) -> TeamInvitation: ...
    async def get_team_invitation(self, invitation_id: UUID) -> TeamInvitation | None: ...
    async def accept_team_invitation(self, invitation_id: UUID, user_id: UUID, token_hash: str, accepted_at: datetime) -> TeamInvitation: ...
    async def list_projects_for_user(self, user_id: UUID, tenant_id: UUID) -> list[Project]: ...
    async def can_access_project(self, project_id: UUID, user_id: UUID, tenant_id: UUID) -> bool: ...

    async def list_team_members(self, tenant_id: UUID) -> list[TeamMember]:
        return [m.model_copy(deep=True) for (tenant, _), m in self.team_members.items() if tenant == tenant_id]

    async def get_team_role(self, tenant_id: UUID, user_id: UUID) -> TeamRole | None:
        member = self.team_members.get((tenant_id, user_id))
        return member.role if member else None

    async def add_team_member(self, member: TeamMember) -> TeamMember:
        self.team_members[(member.tenant_id, member.user_id)] = member.model_copy(deep=True)
        return member.model_copy(deep=True)

    async def create_team_invitation(self, invitation: TeamInvitation, token_hash: str) -> TeamInvitation:
        self.team_invitations[invitation.id] = (invitation.model_copy(deep=True), token_hash)
        return invitation.model_copy(deep=True)

    async def get_team_invitation(self, invitation_id: UUID) -> TeamInvitation | None:
        item = self.team_invitations.get(invitation_id)
        return item[0].model_copy(deep=True) if item else None

    async def accept_team_invitation(self, invitation_id: UUID, user_id: UUID, token_hash: str, accepted_at: datetime) -> TeamInvitation:
        item = self.team_invitations.get(invitation_id)
        if not item or item[1] != token_hash:
            raise KeyError(invitation_id)
        invitation = item[0].model_copy(update={"status": "accepted", "accepted_at": accepted_at}, deep=True)
        self.team_invitations[invitation_id] = (invitation, item[1])
        await self.add_team_member(TeamMember(user_id=user_id, tenant_id=invitation.tenant_id, role=invitation.role))
        return invitation

    async def list_projects_for_user(self, user_id: UUID, tenant_id: UUID) -> list[Project]:
        return sorted((p.model_copy(deep=True) for p in self.projects.values()
                       if p.owner_id == user_id or (self.project_tenants.get(p.id) == tenant_id and (tenant_id, user_id) in self.team_members)),
                      key=lambda p: p.created_at, reverse=True)

    async def can_access_project(self, project_id: UUID, user_id: UUID, tenant_id: UUID) -> bool:
        project = self.projects.get(project_id)
        if not project:
            return False
        return project.owner_id == user_id or (self.project_tenants.get(project_id) == tenant_id and (tenant_id, user_id) in self.team_members)

    async def create_project(self, name: str, owner_id: UUID | None = None) -> Project: ...
    async def get_project(self, project_id: UUID) -> Project | None: ...
    async def list_projects(self, owner_id: UUID | None = None) -> list[Project]: ...
    async def update_project(self, project_id: UUID, status: ProjectStatus) -> Project: ...
    async def duplicate_project(self, project_id: UUID, name: str | None = None, owner_id: UUID | None = None) -> Project: ...
    async def start_discovery(self, project_id: UUID) -> DiscoveryContext: ...
    async def get_context(self, project_id: UUID) -> DiscoveryContext | None: ...
    async def append_message(self, project_id: UUID, message: str) -> DiscoveryContext: ...
    async def update_context(self, context: DiscoveryContext) -> DiscoveryContext: ...
    async def approve_context(self, project_id: UUID) -> DiscoveryContext: ...
    async def create_strategy(self, strategy: WebsiteStrategy) -> WebsiteStrategy: ...
    async def get_strategy(self, project_id: UUID) -> WebsiteStrategy | None: ...
    async def approve_strategy(self, project_id: UUID) -> WebsiteStrategy: ...
    async def create_design(self, design: BrandDesignDirection) -> BrandDesignDirection: ...
    async def get_design(self, project_id: UUID) -> BrandDesignDirection | None: ...
    async def approve_design(self, project_id: UUID) -> BrandDesignDirection: ...
    async def create_specification(self, specification: WebsiteSpecification) -> WebsiteSpecification: ...
    async def get_specification(self, project_id: UUID) -> WebsiteSpecification | None: ...
    async def approve_specification(self, project_id: UUID) -> WebsiteSpecification: ...
    async def list_content(self, project_id: UUID, status: WebsiteContentStatus | None = None) -> list[WebsiteContentItem]: ...
    async def upsert_content(self, item: WebsiteContentItem) -> WebsiteContentItem: ...
    async def publish_content(self, project_id: UUID) -> list[WebsiteContentItem]: ...
    async def list_content_versions(self, project_id: UUID, content_id: UUID) -> list[WebsiteContentItem]: ...
    async def list_content(self, project_id: UUID, status: WebsiteContentStatus | None = None) -> list[WebsiteContentItem]:
        if status == WebsiteContentStatus.PUBLISHED:
            versions = self.content_versions.get(project_id, [])
            latest: dict[UUID, WebsiteContentItem] = {}
            for item in versions:
                if item.status != WebsiteContentStatus.PUBLISHED:
                    continue
                prior = latest.get(item.content_id)
                if prior is None or (item.version, item.published_at or item.updated_at) > (prior.version, prior.published_at or prior.updated_at):
                    latest[item.content_id] = item
            return [i.model_copy(deep=True) for i in sorted(latest.values(), key=lambda x: (x.page, x.key))]
        items = self.content.get(project_id, [])
        return [i.model_copy(deep=True) for i in items if status is None or i.status == status]

    async def upsert_content(self, item: WebsiteContentItem) -> WebsiteContentItem:
        items = self.content.setdefault(item.project_id, [])
        existing = next((i for i in items if i.page == item.page and i.key == item.key), None)
        if existing:
            item.version = existing.version + 1
            item.content_id = existing.content_id
            item.created_at = existing.created_at
        item.status = WebsiteContentStatus.DRAFT
        item.published_at = None
        items[items.index(existing)] = item.model_copy(deep=True) if existing else item.model_copy(deep=True)
        self.content_versions.setdefault(item.project_id, []).append(item.model_copy(deep=True))
        return item

    async def publish_content(self, project_id: UUID) -> list[WebsiteContentItem]:
        now = datetime.now(timezone.utc)
        items = self.content.get(project_id, [])
        for item in items:
            item.status = WebsiteContentStatus.PUBLISHED
            item.published_at = now
            item.updated_at = now
            self.content_versions.setdefault(project_id, []).append(item.model_copy(deep=True))
        return [i.model_copy(deep=True) for i in items]

    async def list_content_versions(self, project_id: UUID, content_id: UUID) -> list[WebsiteContentItem]:
        items = self.content_versions.get(project_id, [])
        return [i.model_copy(deep=True) for i in items if i.content_id == content_id]

    async def create_generation(self, generation: WebsiteGeneration) -> WebsiteGeneration: ...
    async def get_generation(self, project_id: UUID) -> WebsiteGeneration | None: ...
    async def create_mock(self, mock: WebsiteMock) -> WebsiteMock: ...
    async def get_mock(self, project_id: UUID) -> WebsiteMock | None: ...
    async def create_mock_feedback(self, project_id: UUID, mock_id: UUID, mock_version: int, feedback: str) -> None: ...
    async def create_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment: ...
    async def promote_deployment(self, deployment_id: UUID) -> WebsiteDeployment: ...
    async def get_current_deployment(self, project_id: UUID) -> WebsiteDeployment | None: ...
    async def get_execution_state(self, project_id: UUID) -> WebsiteExecutionState | None: ...
    async def save_execution_state(self, state: WebsiteExecutionState) -> WebsiteExecutionState: ...
    async def get_deployment(self, deployment_id: UUID) -> WebsiteDeployment | None: ...
    async def list_deployments(self, project_id: UUID) -> list[WebsiteDeployment]: ...
    async def update_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment: ...


class InMemoryRepository(Repository):
    def __init__(self) -> None:
        self.projects: dict[UUID, Project] = {}
        self.contexts: dict[UUID, DiscoveryContext] = {}
        self.strategies: dict[UUID, list[WebsiteStrategy]] = {}
        self.designs: dict[UUID, list[BrandDesignDirection]] = {}
        self.specifications: dict[UUID, list[WebsiteSpecification]] = {}
        self.generations: dict[UUID, list[WebsiteGeneration]] = {}
        self.deployments: dict[UUID, WebsiteDeployment] = {}
        self.execution_states: dict[UUID, WebsiteExecutionState] = {}
        self.mocks: dict[UUID, list[WebsiteMock]] = {}
        self.content: dict[UUID, list[WebsiteContentItem]] = {}
        self.content_versions: dict[UUID, list[WebsiteContentItem]] = {}
        self.team_members: dict[tuple[UUID, UUID], TeamMember] = {}
        self.team_invitations: dict[UUID, tuple[TeamInvitation, str]] = {}
        self.project_tenants: dict[UUID, UUID] = {}

    async def create_project(self, name: str, owner_id: UUID | None = None) -> Project:
        owner = owner_id or UUID("00000000-0000-0000-0000-000000000001")
        project = Project(name=name, owner_id=owner)
        self.projects[project.id] = project
        self.project_tenants[project.id] = next((tenant for (tenant, user) in self.team_members if user == owner), owner)
        return project

    async def get_project(self, project_id: UUID) -> Project | None:
        project = self.projects.get(project_id)
        return project.model_copy(deep=True) if project else None

    async def list_projects(self, owner_id: UUID | None = None) -> list[Project]:
        return sorted((p.model_copy(deep=True) for p in self.projects.values() if owner_id is None or p.owner_id == owner_id), key=lambda p: p.created_at, reverse=True)

    async def update_project(self, project_id: UUID, status: ProjectStatus) -> Project:
        project = self.projects.get(project_id)
        if not project:
            raise KeyError(project_id)
        updated = project.model_copy(update={"status": status}, deep=True)
        self.projects[project_id] = updated
        return updated.model_copy(deep=True)

    async def duplicate_project(self, project_id: UUID, name: str | None = None, owner_id: UUID | None = None) -> Project:
        source = self.projects.get(project_id)
        if not source:
            raise KeyError(project_id)
        project = Project(name=name or f"{source.name} Copy", owner_id=owner_id or source.owner_id)
        self.projects[project.id] = project
        return project.model_copy(deep=True)

    async def start_discovery(self, project_id: UUID) -> DiscoveryContext:
        existing = await self.get_context(project_id)
        if existing:
            return existing
        context = DiscoveryContext(project_id=project_id, session_id=uuid4())
        self.contexts[project_id] = context
        return context

    async def get_context(self, project_id: UUID) -> DiscoveryContext | None:
        return self.contexts.get(project_id)

    async def append_message(self, project_id: UUID, message: str) -> DiscoveryContext:
        context = self.contexts[project_id].model_copy(deep=True)
        if context.status == DiscoveryStatus.APPROVED:
            raise ValueError("Approved discovery context is immutable")
        context.source_messages.append(message)
        self.contexts[project_id] = context
        return context

    async def update_context(self, context: DiscoveryContext) -> DiscoveryContext:
        updated = context.model_copy(deep=True)
        updated.version += 1
        self.contexts[updated.project_id] = updated
        return updated

    async def approve_context(self, project_id: UUID) -> DiscoveryContext:
        context = self.contexts[project_id].model_copy(deep=True)
        context.status = DiscoveryStatus.APPROVED
        context.approved_at = datetime.now(timezone.utc)
        self.contexts[project_id] = context
        return context

    async def create_strategy(self, strategy: WebsiteStrategy) -> WebsiteStrategy:
        versions = self.strategies.setdefault(strategy.project_id, [])
        versions.append(strategy.model_copy(deep=True))
        return strategy

    async def get_strategy(self, project_id: UUID) -> WebsiteStrategy | None:
        versions = self.strategies.get(project_id, [])
        return versions[-1].model_copy(deep=True) if versions else None

    async def approve_strategy(self, project_id: UUID) -> WebsiteStrategy:
        strategy = await self.get_strategy(project_id)
        if not strategy:
            raise KeyError(project_id)
        if strategy.status != StrategyStatus.READY_FOR_REVIEW:
            raise ValueError("Website strategy is not ready for approval")
        strategy.status = StrategyStatus.APPROVED
        strategy.approved_at = datetime.now(timezone.utc)
        self.strategies[project_id].append(strategy.model_copy(deep=True))
        return strategy

    async def create_design(self, design: BrandDesignDirection) -> BrandDesignDirection:
        self.designs.setdefault(design.project_id, []).append(design.model_copy(deep=True))
        return design

    async def get_design(self, project_id: UUID) -> BrandDesignDirection | None:
        versions = self.designs.get(project_id, [])
        return versions[-1].model_copy(deep=True) if versions else None

    async def approve_design(self, project_id: UUID) -> BrandDesignDirection:
        design = await self.get_design(project_id)
        if not design:
            raise KeyError(project_id)
        if design.status != BrandDesignStatus.READY_FOR_REVIEW:
            raise ValueError("Brand & Design Direction is not ready for approval")
        design.status = BrandDesignStatus.APPROVED
        design.approved_at = datetime.now(timezone.utc)
        self.designs[project_id].append(design.model_copy(deep=True))
        return design


    async def create_specification(self, specification: WebsiteSpecification) -> WebsiteSpecification:
        self.specifications.setdefault(specification.project_id, []).append(specification.model_copy(deep=True))
        return specification

    async def get_specification(self, project_id: UUID) -> WebsiteSpecification | None:
        versions = self.specifications.get(project_id, [])
        return versions[-1].model_copy(deep=True) if versions else None

    async def approve_specification(self, project_id: UUID) -> WebsiteSpecification:
        specification = await self.get_specification(project_id)
        if not specification:
            raise KeyError(project_id)
        if specification.status != WebsiteSpecificationStatus.READY_FOR_REVIEW:
            raise ValueError("Website Specification is not ready for approval")
        specification.status = WebsiteSpecificationStatus.APPROVED
        specification.approved_at = datetime.now(timezone.utc)
        self.specifications[project_id].append(specification.model_copy(deep=True))
        return specification

    async def list_content(self, project_id: UUID, status: WebsiteContentStatus | None = None) -> list[WebsiteContentItem]:
        if status == WebsiteContentStatus.PUBLISHED:
            versions = self.content_versions.get(project_id, [])
            latest: dict[UUID, WebsiteContentItem] = {}
            for item in versions:
                if item.status != WebsiteContentStatus.PUBLISHED:
                    continue
                prior = latest.get(item.content_id)
                if prior is None or (item.version, item.published_at or item.updated_at) > (prior.version, prior.published_at or prior.updated_at):
                    latest[item.content_id] = item
            return [i.model_copy(deep=True) for i in sorted(latest.values(), key=lambda x: (x.page, x.key))]
        items = self.content.get(project_id, [])
        return [i.model_copy(deep=True) for i in items if status is None or i.status == status]

    async def upsert_content(self, item: WebsiteContentItem) -> WebsiteContentItem:
        items = self.content.setdefault(item.project_id, [])
        existing = next((i for i in items if i.page == item.page and i.key == item.key), None)
        if existing:
            item.version = existing.version + 1
            item.content_id = existing.content_id
            item.created_at = existing.created_at
        item.status = WebsiteContentStatus.DRAFT
        item.published_at = None
        item.updated_at = datetime.now(timezone.utc)
        if existing:
            items[items.index(existing)] = item.model_copy(deep=True)
        else:
            items.append(item.model_copy(deep=True))
        self.content_versions.setdefault(item.project_id, []).append(item.model_copy(deep=True))
        return item

    async def publish_content(self, project_id: UUID) -> list[WebsiteContentItem]:
        now = datetime.now(timezone.utc)
        items = self.content.get(project_id, [])
        for item in items:
            item.status = WebsiteContentStatus.PUBLISHED
            item.published_at = now
            item.updated_at = now
            self.content_versions.setdefault(project_id, []).append(item.model_copy(deep=True))
        return [i.model_copy(deep=True) for i in items]

    async def list_content_versions(self, project_id: UUID, content_id: UUID) -> list[WebsiteContentItem]:
        items = self.content_versions.get(project_id, [])
        return [i.model_copy(deep=True) for i in items if i.content_id == content_id]

    async def create_generation(self, generation: WebsiteGeneration) -> WebsiteGeneration:
        self.generations.setdefault(generation.project_id, []).append(generation.model_copy(deep=True))
        return generation

    async def get_generation(self, project_id: UUID) -> WebsiteGeneration | None:
        versions = self.generations.get(project_id, [])
        return versions[-1].model_copy(deep=True) if versions else None

    async def create_mock(self, mock: WebsiteMock) -> WebsiteMock:
        self.mocks.setdefault(mock.project_id, []).append(mock.model_copy(deep=True))
        return mock

    async def get_mock(self, project_id: UUID) -> WebsiteMock | None:
        versions = self.mocks.get(project_id, [])
        return versions[-1].model_copy(deep=True) if versions else None

    async def create_mock_feedback(self, project_id: UUID, mock_id: UUID, mock_version: int, feedback: str) -> None:
        return None

    async def create_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment:
        # In-memory tests emulate the project-scoped serialization used by the
        # SQL repository. Version allocation is corrected here as a final guard.
        existing = [d for d in self.deployments.values() if d.project_id == deployment.project_id]
        max_version = max((d.version for d in existing), default=0)
        if deployment.version <= max_version:
            deployment = deployment.model_copy(update={"version": max_version + 1}, deep=True)
        self.deployments[deployment.deployment_id] = deployment.model_copy(deep=True)
        return deployment

    async def promote_deployment(self, deployment_id: UUID) -> WebsiteDeployment:
        target = self.deployments.get(deployment_id)
        if not target:
            raise KeyError(deployment_id)
        if target.status != DeploymentStatus.DEPLOYED or not target.snapshot_ref:
            raise ValueError("Only a successful deployment with a snapshot can become current.")
        for item in self.deployments.values():
            if item.project_id != target.project_id:
                continue
            if item.deployment_id == deployment_id:
                item.lifecycle_role = DeploymentLifecycleRole.CURRENT
            elif item.lifecycle_role == DeploymentLifecycleRole.CURRENT:
                item.lifecycle_role = DeploymentLifecycleRole.PREVIOUS
        return target.model_copy(deep=True)

    async def get_current_deployment(self, project_id: UUID) -> WebsiteDeployment | None:
        current = [d for d in self.deployments.values()
                   if d.project_id == project_id and d.lifecycle_role == DeploymentLifecycleRole.CURRENT]
        return max((d.model_copy(deep=True) for d in current), key=lambda d: d.version, default=None)

    async def get_deployment(self, deployment_id: UUID) -> WebsiteDeployment | None:
        deployment = self.deployments.get(deployment_id)
        return deployment.model_copy(deep=True) if deployment else None

    async def list_deployments(self, project_id: UUID) -> list[WebsiteDeployment]:
        return [d.model_copy(deep=True) for d in self.deployments.values() if d.project_id == project_id]

    async def update_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment:
        self.deployments[deployment.deployment_id] = deployment.model_copy(deep=True)
        return deployment
    async def get_execution_state(self, project_id: UUID) -> WebsiteExecutionState | None:
        state = self.execution_states.get(project_id)
        return state.model_copy(deep=True) if state else None

    async def save_execution_state(self, state: WebsiteExecutionState) -> WebsiteExecutionState:
        saved = state.model_copy(update={"updated_at": datetime.now(timezone.utc)}, deep=True)
        self.execution_states[state.project_id] = saved
        return saved.model_copy(deep=True)



class SqlAlchemyRepository(Repository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def list_team_members(self, tenant_id: UUID) -> list[TeamMember]:
        async with self.session_factory() as session:
            result = await session.execute(select(TeamMemberRow).where(TeamMemberRow.tenant_id == str(tenant_id)).order_by(TeamMemberRow.created_at))
            rows = result.scalars().all()
        return [TeamMember(user_id=UUID(r.user_id), tenant_id=UUID(r.tenant_id), role=TeamRole(r.role), created_at=r.created_at) for r in rows]

    async def get_team_role(self, tenant_id: UUID, user_id: UUID) -> TeamRole | None:
        async with self.session_factory() as session:
            result = await session.execute(select(TeamMemberRow).where(TeamMemberRow.tenant_id == str(tenant_id), TeamMemberRow.user_id == str(user_id)))
            row = result.scalars().first()
        return TeamRole(row.role) if row else None

    async def add_team_member(self, member: TeamMember) -> TeamMember:
        async with self.session_factory() as session:
            existing = await session.execute(select(TeamMemberRow).where(TeamMemberRow.tenant_id == str(member.tenant_id), TeamMemberRow.user_id == str(member.user_id)))
            row = existing.scalars().first()
            if row:
                row.role = member.role.value
            else:
                session.add(TeamMemberRow(id=str(uuid4()), tenant_id=str(member.tenant_id), user_id=str(member.user_id), role=member.role.value, created_at=member.created_at))
            await session.commit()
        return member

    async def create_team_invitation(self, invitation: TeamInvitation, token_hash: str) -> TeamInvitation:
        async with self.session_factory() as session:
            session.add(TeamInvitationRow(id=str(invitation.id), tenant_id=str(invitation.tenant_id), inviter_id=str(invitation.inviter_id), email=invitation.email, role=invitation.role.value, token_hash=token_hash, status=invitation.status, created_at=invitation.created_at, expires_at=invitation.expires_at))
            await session.commit()
        return invitation

    async def get_team_invitation(self, invitation_id: UUID) -> TeamInvitation | None:
        async with self.session_factory() as session:
            row = await session.get(TeamInvitationRow, str(invitation_id))
        if not row:
            return None
        return TeamInvitation(id=UUID(row.id), tenant_id=UUID(row.tenant_id), inviter_id=UUID(row.inviter_id), email=row.email, role=TeamRole(row.role), status=row.status, created_at=row.created_at, expires_at=row.expires_at, accepted_at=row.accepted_at)

    async def accept_team_invitation(self, invitation_id: UUID, user_id: UUID, token_hash: str, accepted_at: datetime) -> TeamInvitation:
        async with self.session_factory() as session:
            row = await session.get(TeamInvitationRow, str(invitation_id))
            if not row or row.token_hash != token_hash:
                raise KeyError(invitation_id)
            row.status = "accepted"
            row.accepted_at = accepted_at
            existing = await session.execute(select(TeamMemberRow).where(TeamMemberRow.tenant_id == row.tenant_id, TeamMemberRow.user_id == str(user_id)))
            member = existing.scalars().first()
            if member:
                member.role = row.role
            else:
                session.add(TeamMemberRow(id=str(uuid4()), tenant_id=row.tenant_id, user_id=str(user_id), role=row.role, created_at=accepted_at))
            await session.commit()
        return await self.get_team_invitation(invitation_id)

    async def list_projects_for_user(self, user_id: UUID, tenant_id: UUID) -> list[Project]:
        async with self.session_factory() as session:
            result = await session.execute(select(ProjectRow).order_by(ProjectRow.created_at.desc()))
            rows = result.scalars().all()
        # Project tenant is derived from its owner because CAP-025 stored tenant_id on users.
        async with self.session_factory() as session:
            from app.security import UserRow
            owners = await session.execute(select(UserRow.id, UserRow.tenant_id).where(UserRow.id.in_([r.owner_id for r in rows])))
            owner_tenants = {uid: tid for uid, tid in owners.all()}
        allowed = [r for r in rows if r.owner_id == str(user_id) or owner_tenants.get(r.owner_id) == str(tenant_id)]
        return [Project(id=UUID(r.id), name=r.name, status=ProjectStatus(r.status), owner_id=UUID(r.owner_id), created_at=r.created_at) for r in allowed]

    async def can_access_project(self, project_id: UUID, user_id: UUID, tenant_id: UUID) -> bool:
        project = await self.get_project(project_id)
        if not project:
            return False
        if project.owner_id == user_id:
            return True
        async with self.session_factory() as session:
            from app.security import UserRow
            owner = await session.get(UserRow, str(project.owner_id))
            if not owner or owner.tenant_id != str(tenant_id):
                return False
            result = await session.execute(select(TeamMemberRow).where(TeamMemberRow.tenant_id == str(tenant_id), TeamMemberRow.user_id == str(user_id)))
            return result.scalars().first() is not None

    async def create_project(self, name: str, owner_id: UUID | None = None) -> Project:
        project = Project(name=name, owner_id=owner_id or UUID("00000000-0000-0000-0000-000000000001"))
        async with self.session_factory() as session:
            session.add(ProjectRow(id=str(project.id), name=project.name, status=project.status.value, owner_id=str(project.owner_id), created_at=project.created_at))
            await session.commit()
        return project

    async def get_project(self, project_id: UUID) -> Project | None:
        async with self.session_factory() as session:
            row = await session.get(ProjectRow, str(project_id))
        if not row:
            return None
        return Project(id=UUID(row.id), name=row.name, status=ProjectStatus(row.status), owner_id=UUID(row.owner_id), created_at=row.created_at)

    async def list_projects(self, owner_id: UUID | None = None) -> list[Project]:
        async with self.session_factory() as session:
            query = select(ProjectRow).order_by(ProjectRow.created_at.desc())
            if owner_id:
                query = query.where(ProjectRow.owner_id == str(owner_id))
            result = await session.execute(query)
            rows = result.scalars().all()
        return [Project(id=UUID(row.id), name=row.name, status=ProjectStatus(row.status), owner_id=UUID(row.owner_id), created_at=row.created_at) for row in rows]

    async def update_project(self, project_id: UUID, status: ProjectStatus) -> Project:
        async with self.session_factory() as session:
            row = await session.get(ProjectRow, str(project_id))
            if not row:
                raise KeyError(project_id)
            row.status = status.value
            await session.commit()
            project = Project(id=UUID(row.id), name=row.name, status=ProjectStatus(row.status), owner_id=UUID(row.owner_id), created_at=row.created_at)
        return project

    async def duplicate_project(self, project_id: UUID, name: str | None = None, owner_id: UUID | None = None) -> Project:
        source = await self.get_project(project_id)
        if not source:
            raise KeyError(project_id)
        project = Project(name=name or f"{source.name} Copy", owner_id=owner_id or source.owner_id)
        async with self.session_factory() as session:
            session.add(ProjectRow(id=str(project.id), name=project.name, status=project.status.value, owner_id=str(project.owner_id), created_at=project.created_at))
            await session.commit()
        return project

    async def start_discovery(self, project_id: UUID) -> DiscoveryContext:
        existing = await self.get_context(project_id)
        if existing:
            return existing

        session_id = uuid4()
        now = datetime.now(timezone.utc)
        context = DiscoveryContext(project_id=project_id, session_id=session_id)
        async with self.session_factory() as session:
            session.add(DiscoverySessionRow(id=str(session_id), project_id=str(project_id), status=context.status.value, created_at=now))
            session.add(ContextVersionRow(id=str(uuid4()), session_id=str(session_id), version=1, status=context.status.value, payload=context.model_dump_json(), completeness_score=0.0, created_at=now))
            await session.commit()
        return context

    async def get_context(self, project_id: UUID) -> DiscoveryContext | None:
        async with self.session_factory() as session:
            result = await session.execute(select(DiscoverySessionRow).where(DiscoverySessionRow.project_id == str(project_id)).order_by(DiscoverySessionRow.created_at.desc()))
            row = result.scalars().first()
            if not row:
                return None
            versions = await session.execute(select(ContextVersionRow).where(ContextVersionRow.session_id == row.id).order_by(ContextVersionRow.version.desc()))
            version = versions.scalars().first()
        return DiscoveryContext.model_validate_json(version.payload) if version else None

    async def append_message(self, project_id: UUID, message: str) -> DiscoveryContext:
        context = await self.get_context(project_id)
        if not context:
            raise KeyError(project_id)
        if context.status == DiscoveryStatus.APPROVED:
            raise ValueError("Approved discovery context is immutable")
        context = context.model_copy(deep=True)
        context.source_messages.append(message)
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            session.add(SourceMessageRow(id=str(uuid4()), session_id=str(context.session_id), message=message, created_at=now))
            context.version += 1
            session.add(ContextVersionRow(id=str(uuid4()), session_id=str(context.session_id), version=context.version, status=context.status.value, payload=context.model_dump_json(), completeness_score=context.completeness_score, created_at=now))
            await session.commit()
        return context

    async def update_context(self, context: DiscoveryContext) -> DiscoveryContext:
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            context.version += 1
            session.add(ContextVersionRow(id=str(uuid4()), session_id=str(context.session_id), version=context.version, status=context.status.value, payload=context.model_dump_json(), completeness_score=context.completeness_score, created_at=now))
            await session.commit()
        return context

    async def approve_context(self, project_id: UUID) -> DiscoveryContext:
        context = await self.get_context(project_id)
        if not context:
            raise KeyError(project_id)
        context = context.model_copy(deep=True)
        context.status = DiscoveryStatus.APPROVED
        context.approved_at = datetime.now(timezone.utc)
        context.version += 1
        async with self.session_factory() as session:
            session.add(ContextVersionRow(id=str(uuid4()), session_id=str(context.session_id), version=context.version, status=context.status.value, payload=context.model_dump_json(), completeness_score=context.completeness_score, created_at=context.approved_at))
            await session.execute(select(DiscoverySessionRow).where(DiscoverySessionRow.id == str(context.session_id)))
            row = await session.get(DiscoverySessionRow, str(context.session_id))
            if row:
                row.status = context.status.value
            await session.commit()
        return context


    async def create_strategy(self, strategy: WebsiteStrategy) -> WebsiteStrategy:
        now = datetime.now(timezone.utc)
        payload = strategy.model_dump_json()
        async with self.session_factory() as session:
            existing = await session.execute(select(WebsiteStrategyRow).where(WebsiteStrategyRow.project_id == str(strategy.project_id)))
            row = existing.scalars().first()
            if row:
                row.id = str(strategy.strategy_id)
                row.payload = payload
                row.status = strategy.status.value
                row.version = strategy.version
            else:
                session.add(WebsiteStrategyRow(id=str(strategy.strategy_id), project_id=str(strategy.project_id), status=strategy.status.value, version=strategy.version, payload=payload, created_at=now))
            session.add(WebsiteStrategyVersionRow(id=str(uuid4()), project_id=str(strategy.project_id), strategy_id=str(strategy.strategy_id), version=strategy.version, status=strategy.status.value, payload=payload, created_at=now))
            await session.commit()
        return strategy

    async def get_strategy(self, project_id: UUID) -> WebsiteStrategy | None:
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteStrategyRow).where(WebsiteStrategyRow.project_id == str(project_id)))
            row = result.scalars().first()
        return WebsiteStrategy.model_validate_json(row.payload) if row else None

    async def approve_strategy(self, project_id: UUID) -> WebsiteStrategy:
        strategy = await self.get_strategy(project_id)
        if not strategy:
            raise KeyError(project_id)
        if strategy.status != StrategyStatus.READY_FOR_REVIEW:
            raise ValueError("Website strategy is not ready for approval")
        strategy.status = StrategyStatus.APPROVED
        strategy.approved_at = datetime.now(timezone.utc)
        return await self.create_strategy(strategy)


    async def create_design(self, design: BrandDesignDirection) -> BrandDesignDirection:
        now = datetime.now(timezone.utc)
        payload = design.model_dump_json()
        async with self.session_factory() as session:
            result = await session.execute(select(BrandDesignDirectionRow).where(BrandDesignDirectionRow.project_id == str(design.project_id)))
            row = result.scalars().first()
            if row:
                row.id = str(design.design_id); row.payload = payload; row.status = design.status.value; row.version = design.version
            else:
                session.add(BrandDesignDirectionRow(id=str(design.design_id), project_id=str(design.project_id), status=design.status.value, version=design.version, payload=payload, created_at=now))
            session.add(BrandDesignDirectionVersionRow(id=str(uuid4()), project_id=str(design.project_id), design_id=str(design.design_id), version=design.version, status=design.status.value, payload=payload, created_at=now))
            await session.commit()
        return design

    async def get_design(self, project_id: UUID) -> BrandDesignDirection | None:
        async with self.session_factory() as session:
            result = await session.execute(select(BrandDesignDirectionRow).where(BrandDesignDirectionRow.project_id == str(project_id)))
            row = result.scalars().first()
        return BrandDesignDirection.model_validate_json(row.payload) if row else None

    async def approve_design(self, project_id: UUID) -> BrandDesignDirection:
        design = await self.get_design(project_id)
        if not design: raise KeyError(project_id)
        if design.status != BrandDesignStatus.READY_FOR_REVIEW: raise ValueError("Brand & Design Direction is not ready for approval")
        design.status = BrandDesignStatus.APPROVED; design.approved_at = datetime.now(timezone.utc)
        return await self.create_design(design)


    async def create_specification(self, specification: WebsiteSpecification) -> WebsiteSpecification:
        now = datetime.now(timezone.utc)
        payload = specification.model_dump_json()
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteSpecificationRow).where(WebsiteSpecificationRow.project_id == str(specification.project_id)))
            row = result.scalars().first()
            if row:
                row.id = str(specification.specification_id)
                row.payload = payload
                row.status = specification.status.value
                row.version = specification.version
            else:
                session.add(WebsiteSpecificationRow(id=str(specification.specification_id), project_id=str(specification.project_id), status=specification.status.value, version=specification.version, payload=payload, created_at=now))
            session.add(WebsiteSpecificationVersionRow(id=str(uuid4()), project_id=str(specification.project_id), specification_id=str(specification.specification_id), version=specification.version, status=specification.status.value, payload=payload, created_at=now))
            await session.commit()
        return specification

    async def get_specification(self, project_id: UUID) -> WebsiteSpecification | None:
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteSpecificationRow).where(WebsiteSpecificationRow.project_id == str(project_id)))
            row = result.scalars().first()
        return WebsiteSpecification.model_validate_json(row.payload) if row else None

    async def approve_specification(self, project_id: UUID) -> WebsiteSpecification:
        specification = await self.get_specification(project_id)
        if not specification:
            raise KeyError(project_id)
        if specification.status != WebsiteSpecificationStatus.READY_FOR_REVIEW:
            raise ValueError("Website Specification is not ready for approval")
        specification.status = WebsiteSpecificationStatus.APPROVED
        specification.approved_at = datetime.now(timezone.utc)
        return await self.create_specification(specification)

    async def list_content(self, project_id: UUID, status: WebsiteContentStatus | None = None) -> list[WebsiteContentItem]:
        async with self.session_factory() as session:
            if status == WebsiteContentStatus.PUBLISHED:
                result = await session.execute(
                    select(WebsiteContentVersionRow)
                    .where(
                        WebsiteContentVersionRow.project_id == str(project_id),
                        WebsiteContentVersionRow.status == WebsiteContentStatus.PUBLISHED.value,
                    )
                    .order_by(WebsiteContentVersionRow.content_id, WebsiteContentVersionRow.version.desc(), WebsiteContentVersionRow.created_at.desc())
                )
                rows = result.scalars().all()
                latest: dict[str, WebsiteContentVersionRow] = {}
                for row in rows:
                    latest.setdefault(row.content_id, row)
                return [WebsiteContentItem(content_id=UUID(r.content_id), project_id=project_id, page=r.page, key=r.content_key, content_type=r.content_type, value=r.value, version=r.version, status=WebsiteContentStatus.PUBLISHED, created_at=r.created_at, updated_at=r.created_at, published_at=r.published_at) for r in sorted(latest.values(), key=lambda x: (x.page, x.content_key))]

            q = select(WebsiteContentRow).where(WebsiteContentRow.project_id == str(project_id))
            if status:
                q = q.where(WebsiteContentRow.status == status.value)
            result = await session.execute(q.order_by(WebsiteContentRow.page, WebsiteContentRow.content_key))
            rows = result.scalars().all()
        return [WebsiteContentItem(content_id=UUID(r.id), project_id=project_id, page=r.page, key=r.content_key, content_type=r.content_type, value=r.value, version=r.version, status=WebsiteContentStatus(r.status), created_at=r.created_at, updated_at=r.updated_at, published_at=r.published_at) for r in rows]

    async def upsert_content(self, item: WebsiteContentItem) -> WebsiteContentItem:
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteContentRow).where(WebsiteContentRow.project_id == str(item.project_id), WebsiteContentRow.page == item.page, WebsiteContentRow.content_key == item.key))
            row = result.scalars().first()
            if row:
                item.content_id = UUID(row.id); item.version = row.version + 1; item.created_at = row.created_at
                row.value=item.value; row.content_type=item.content_type; row.version=item.version; row.status=WebsiteContentStatus.DRAFT.value; row.updated_at=now; row.published_at=None
            else:
                item.updated_at=now
                session.add(WebsiteContentRow(id=str(item.content_id), project_id=str(item.project_id), page=item.page, content_key=item.key, content_type=item.content_type, value=item.value, version=item.version, status=item.status.value, created_at=item.created_at, updated_at=now, published_at=None))
            session.add(WebsiteContentVersionRow(id=str(uuid4()), project_id=str(item.project_id), content_id=str(item.content_id), page=item.page, content_key=item.key, content_type=item.content_type, value=item.value, version=item.version, status=WebsiteContentStatus.DRAFT.value, created_at=now, published_at=None))
            await session.commit()
        return item

    async def publish_content(self, project_id: UUID) -> list[WebsiteContentItem]:
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteContentRow).where(WebsiteContentRow.project_id == str(project_id)))
            rows=result.scalars().all()
            for row in rows:
                row.status=WebsiteContentStatus.PUBLISHED.value; row.published_at=now; row.updated_at=now
                session.add(WebsiteContentVersionRow(id=str(uuid4()), project_id=str(project_id), content_id=row.id, page=row.page, content_key=row.content_key, content_type=row.content_type, value=row.value, version=row.version, status=WebsiteContentStatus.PUBLISHED.value, created_at=now, published_at=now))
            await session.commit()
        return await self.list_content(project_id)

    async def list_content_versions(self, project_id: UUID, content_id: UUID) -> list[WebsiteContentItem]:
        async with self.session_factory() as session:
            result=await session.execute(select(WebsiteContentVersionRow).where(WebsiteContentVersionRow.project_id == str(project_id), WebsiteContentVersionRow.content_id == str(content_id)).order_by(WebsiteContentVersionRow.version))
            rows=result.scalars().all()
        return [WebsiteContentItem(content_id=content_id, project_id=project_id, page=r.page, key=r.content_key, content_type=r.content_type, value=r.value, version=r.version, status=WebsiteContentStatus(r.status), created_at=r.created_at, updated_at=r.created_at, published_at=r.published_at) for r in rows]

    async def get_execution_state(self, project_id: UUID) -> WebsiteExecutionState | None:
        import json
        async with self.session_factory() as session:
            row = await session.get(WebsiteExecutionStateRow, str(project_id))
        if not row:
            return None
        return WebsiteExecutionState(
            project_id=project_id, generation_version=row.generation_version,
            build_status=row.build_status, build_result=json.loads(row.build_result or "{}"),
            validation_status=row.validation_status,
            validation=WebsiteValidation.model_validate_json(row.validation_payload) if row.validation_payload else None,
            preview_status=row.preview_status,
            preview=WebsitePreview.model_validate_json(row.preview_payload) if row.preview_payload else None,
            updated_at=row.updated_at,
        )

    async def save_execution_state(self, state: WebsiteExecutionState) -> WebsiteExecutionState:
        import json
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            row = await session.get(WebsiteExecutionStateRow, str(state.project_id))
            values = dict(generation_version=state.generation_version, build_status=state.build_status,
                          build_result=json.dumps(state.build_result), validation_status=state.validation_status,
                          validation_payload=state.validation.model_dump_json() if state.validation else None,
                          preview_status=state.preview_status,
                          preview_payload=state.preview.model_dump_json() if state.preview else None, updated_at=now)
            if row:
                for key, value in values.items(): setattr(row, key, value)
            else:
                session.add(WebsiteExecutionStateRow(project_id=str(state.project_id), **values))
            await session.commit()
        return state.model_copy(update={"updated_at": now}, deep=True)

    async def create_generation(self, generation: WebsiteGeneration) -> WebsiteGeneration:
        now = datetime.now(timezone.utc)
        payload = generation.model_dump_json()
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteGenerationRow).where(WebsiteGenerationRow.project_id == str(generation.project_id)))
            row = result.scalars().first()
            if row:
                row.id = str(generation.generation_id); row.payload = payload; row.status = generation.status.value; row.version = generation.version
            else:
                session.add(WebsiteGenerationRow(id=str(generation.generation_id), project_id=str(generation.project_id), status=generation.status.value, version=generation.version, payload=payload, created_at=now))
            session.add(WebsiteGenerationVersionRow(id=str(uuid4()), project_id=str(generation.project_id), generation_id=str(generation.generation_id), version=generation.version, status=generation.status.value, payload=payload, created_at=now))
            await session.commit()
        return generation

    async def get_generation(self, project_id: UUID) -> WebsiteGeneration | None:
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteGenerationRow).where(WebsiteGenerationRow.project_id == str(project_id)))
            row = result.scalars().first()
        return WebsiteGeneration.model_validate_json(row.payload) if row else None


    async def create_mock(self, mock: WebsiteMock) -> WebsiteMock:
        now = datetime.now(timezone.utc)
        payload = mock.model_dump_json()
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteMockRow).where(WebsiteMockRow.project_id == str(mock.project_id)))
            row = result.scalars().first()
            if row:
                row.id = str(mock.mock_id); row.payload = payload; row.status = mock.status.value; row.version = mock.version; row.generation_version = mock.generation_version
            else:
                session.add(WebsiteMockRow(id=str(mock.mock_id), project_id=str(mock.project_id), generation_version=mock.generation_version, version=mock.version, status=mock.status.value, payload=payload, created_at=now))
            session.add(WebsiteMockVersionRow(id=str(uuid4()), project_id=str(mock.project_id), mock_id=str(mock.mock_id), version=mock.version, status=mock.status.value, payload=payload, created_at=now))
            await session.commit()
        return mock

    async def get_mock(self, project_id: UUID) -> WebsiteMock | None:
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteMockRow).where(WebsiteMockRow.project_id == str(project_id)))
            row = result.scalars().first()
        return WebsiteMock.model_validate_json(row.payload) if row else None

    async def create_mock_feedback(self, project_id: UUID, mock_id: UUID, mock_version: int, feedback: str) -> None:
        async with self.session_factory() as session:
            session.add(WebsiteMockFeedbackRow(id=str(uuid4()), project_id=str(project_id), mock_id=str(mock_id), mock_version=mock_version, feedback=feedback, created_at=datetime.now(timezone.utc)))
            await session.commit()

    async def create_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment:
        import json
        async with self.session_factory() as session:
            # PostgreSQL advisory lock serializes version allocation per project
            # across API workers. SQLite/test backends simply use the submitted
            # version.
            if session.bind and session.bind.dialect.name == "postgresql":
                await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(str(deployment.project_id)))))
            result = await session.execute(
                select(func.coalesce(func.max(WebsiteDeploymentRow.version), 0)).where(
                    WebsiteDeploymentRow.project_id == str(deployment.project_id)
                )
            )
            max_version = int(result.scalar_one() or 0)
            if deployment.version <= max_version:
                deployment = deployment.model_copy(update={"version": max_version + 1}, deep=True)
            session.add(WebsiteDeploymentRow(
                id=str(deployment.deployment_id), project_id=str(deployment.project_id),
                generation_version=deployment.generation_version, version=deployment.version,
                status=deployment.status.value, lifecycle_role=deployment.lifecycle_role.value, provider=deployment.provider, url=deployment.url,
                runtime_id=deployment.runtime_id, snapshot_ref=deployment.snapshot_ref, diagnostics=json.dumps(deployment.diagnostics),
                created_at=deployment.created_at, deployed_at=deployment.deployed_at, stopped_at=deployment.stopped_at,
            ))
            await session.commit()
        return deployment

    async def promote_deployment(self, deployment_id: UUID) -> WebsiteDeployment:
        import json
        async with self.session_factory() as session:
            target = await session.get(WebsiteDeploymentRow, str(deployment_id), with_for_update=True)
            if not target:
                raise KeyError(deployment_id)
            if target.status != DeploymentStatus.DEPLOYED.value or not target.snapshot_ref:
                raise ValueError("Only a successful deployment with a snapshot can become current.")
            if session.bind and session.bind.dialect.name == "postgresql":
                await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(target.project_id))))
            await session.execute(
                WebsiteDeploymentRow.__table__.update()
                .where(WebsiteDeploymentRow.project_id == target.project_id,
                       WebsiteDeploymentRow.lifecycle_role == DeploymentLifecycleRole.CURRENT.value,
                       WebsiteDeploymentRow.id != target.id)
                .values(lifecycle_role=DeploymentLifecycleRole.PREVIOUS.value)
            )
            target.lifecycle_role = DeploymentLifecycleRole.CURRENT.value
            await session.commit()
        return await self.get_deployment(deployment_id)

    async def get_current_deployment(self, project_id: UUID) -> WebsiteDeployment | None:
        import json
        async with self.session_factory() as session:
            result = await session.execute(
                select(WebsiteDeploymentRow).where(
                    WebsiteDeploymentRow.project_id == str(project_id),
                    WebsiteDeploymentRow.lifecycle_role == DeploymentLifecycleRole.CURRENT.value,
                ).order_by(WebsiteDeploymentRow.version.desc())
            )
            row = result.scalars().first()
        if not row:
            return None
        return WebsiteDeployment(
            project_id=UUID(row.project_id), deployment_id=UUID(row.id), generation_version=row.generation_version,
            version=row.version, status=DeploymentStatus(row.status), lifecycle_role=DeploymentLifecycleRole(row.lifecycle_role),
            provider=row.provider, url=row.url, runtime_id=row.runtime_id, snapshot_ref=row.snapshot_ref,
            diagnostics=json.loads(row.diagnostics), created_at=row.created_at, deployed_at=row.deployed_at, stopped_at=row.stopped_at,
        )

    async def get_deployment(self, deployment_id: UUID) -> WebsiteDeployment | None:
        import json
        async with self.session_factory() as session:
            row = await session.get(WebsiteDeploymentRow, str(deployment_id))
        if not row:
            return None
        return WebsiteDeployment(
            project_id=UUID(row.project_id), deployment_id=UUID(row.id), generation_version=row.generation_version,
            version=row.version, status=DeploymentStatus(row.status), lifecycle_role=DeploymentLifecycleRole(row.lifecycle_role), provider=row.provider, url=row.url,
            runtime_id=row.runtime_id, snapshot_ref=row.snapshot_ref, diagnostics=json.loads(row.diagnostics), created_at=row.created_at,
            deployed_at=row.deployed_at, stopped_at=row.stopped_at,
        )

    async def list_deployments(self, project_id: UUID) -> list[WebsiteDeployment]:
        import json
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteDeploymentRow).where(WebsiteDeploymentRow.project_id == str(project_id)).order_by(WebsiteDeploymentRow.created_at.desc()))
            rows = result.scalars().all()
        return [WebsiteDeployment(
            project_id=UUID(row.project_id), deployment_id=UUID(row.id), generation_version=row.generation_version,
            version=row.version, status=DeploymentStatus(row.status), lifecycle_role=DeploymentLifecycleRole(row.lifecycle_role), provider=row.provider, url=row.url,
            runtime_id=row.runtime_id, snapshot_ref=row.snapshot_ref, diagnostics=json.loads(row.diagnostics), created_at=row.created_at,
            deployed_at=row.deployed_at, stopped_at=row.stopped_at,
        ) for row in rows]

    async def update_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment:
        import json
        async with self.session_factory() as session:
            row = await session.get(WebsiteDeploymentRow, str(deployment.deployment_id))
            if not row:
                raise KeyError(deployment.deployment_id)
            row.generation_version = deployment.generation_version
            row.version = deployment.version
            row.status = deployment.status.value
            row.provider = deployment.provider
            row.url = deployment.url
            row.runtime_id = deployment.runtime_id
            row.snapshot_ref = deployment.snapshot_ref
            row.diagnostics = json.dumps(deployment.diagnostics)
            row.deployed_at = deployment.deployed_at
            row.stopped_at = deployment.stopped_at
            await session.commit()
        return deployment


async def init_database() -> None:
    if not DATABASE_URL:
        return
    # Alembic is the authoritative schema lifecycle. Running it in a worker
    # thread keeps startup migration work out of the async event loop.
    await asyncio.to_thread(_upgrade_database)


def _upgrade_database() -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    command.upgrade(config, "head")


def build_repository() -> Repository:
    if not DATABASE_URL:
        return InMemoryRepository()
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    return SqlAlchemyRepository(async_sessionmaker(engine, expire_on_commit=False))


@asynccontextmanager
async def lifespan_repository() -> AsyncIterator[Repository]:
    await init_database()
    yield build_repository()
