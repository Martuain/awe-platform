import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer, String, Text, select
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
    WebsiteDeployment,
    DeploymentStatus,
)

DATABASE_URL = os.getenv("DATABASE_URL")


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


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


class WebsiteGenerationRow(Base):
    __tablename__ = "website_generations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebsiteDeploymentRow(Base):
    __tablename__ = "website_deployments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    generation_version: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    provider: Mapped[str] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    runtime_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
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
    async def create_project(self, name: str) -> Project: ...
    async def get_project(self, project_id: UUID) -> Project | None: ...
    async def list_projects(self) -> list[Project]: ...
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
    async def create_generation(self, generation: WebsiteGeneration) -> WebsiteGeneration: ...
    async def get_generation(self, project_id: UUID) -> WebsiteGeneration | None: ...
    async def create_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment: ...
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

    async def create_project(self, name: str) -> Project:
        project = Project(name=name)
        self.projects[project.id] = project
        return project

    async def get_project(self, project_id: UUID) -> Project | None:
        project = self.projects.get(project_id)
        return project.model_copy(deep=True) if project else None

    async def list_projects(self) -> list[Project]:
        return sorted((p.model_copy(deep=True) for p in self.projects.values()), key=lambda p: p.created_at, reverse=True)

    async def start_discovery(self, project_id: UUID) -> DiscoveryContext:
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

    async def create_generation(self, generation: WebsiteGeneration) -> WebsiteGeneration:
        self.generations.setdefault(generation.project_id, []).append(generation.model_copy(deep=True))
        return generation

    async def get_generation(self, project_id: UUID) -> WebsiteGeneration | None:
        versions = self.generations.get(project_id, [])
        return versions[-1].model_copy(deep=True) if versions else None

    async def create_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment:
        self.deployments[deployment.deployment_id] = deployment.model_copy(deep=True)
        return deployment

    async def get_deployment(self, deployment_id: UUID) -> WebsiteDeployment | None:
        deployment = self.deployments.get(deployment_id)
        return deployment.model_copy(deep=True) if deployment else None

    async def list_deployments(self, project_id: UUID) -> list[WebsiteDeployment]:
        return [d.model_copy(deep=True) for d in self.deployments.values() if d.project_id == project_id]

    async def update_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment:
        self.deployments[deployment.deployment_id] = deployment.model_copy(deep=True)
        return deployment


class SqlAlchemyRepository(Repository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def create_project(self, name: str) -> Project:
        project = Project(name=name)
        async with self.session_factory() as session:
            session.add(ProjectRow(id=str(project.id), name=project.name, status=project.status.value, created_at=project.created_at))
            await session.commit()
        return project

    async def get_project(self, project_id: UUID) -> Project | None:
        async with self.session_factory() as session:
            row = await session.get(ProjectRow, str(project_id))
        if not row:
            return None
        return Project(id=UUID(row.id), name=row.name, status=ProjectStatus(row.status), created_at=row.created_at)

    async def list_projects(self) -> list[Project]:
        async with self.session_factory() as session:
            result = await session.execute(select(ProjectRow).order_by(ProjectRow.created_at.desc()))
            rows = result.scalars().all()
        return [Project(id=UUID(row.id), name=row.name, status=ProjectStatus(row.status), created_at=row.created_at) for row in rows]

    async def start_discovery(self, project_id: UUID) -> DiscoveryContext:
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


    async def create_deployment(self, deployment: WebsiteDeployment) -> WebsiteDeployment:
        import json
        async with self.session_factory() as session:
            session.add(WebsiteDeploymentRow(
                id=str(deployment.deployment_id), project_id=str(deployment.project_id),
                generation_version=deployment.generation_version, version=deployment.version,
                status=deployment.status.value, provider=deployment.provider, url=deployment.url,
                runtime_id=deployment.runtime_id, diagnostics=json.dumps(deployment.diagnostics),
                created_at=deployment.created_at, deployed_at=deployment.deployed_at, stopped_at=deployment.stopped_at,
            ))
            await session.commit()
        return deployment

    async def get_deployment(self, deployment_id: UUID) -> WebsiteDeployment | None:
        import json
        async with self.session_factory() as session:
            row = await session.get(WebsiteDeploymentRow, str(deployment_id))
        if not row:
            return None
        return WebsiteDeployment(
            project_id=UUID(row.project_id), deployment_id=UUID(row.id), generation_version=row.generation_version,
            version=row.version, status=DeploymentStatus(row.status), provider=row.provider, url=row.url,
            runtime_id=row.runtime_id, diagnostics=json.loads(row.diagnostics), created_at=row.created_at,
            deployed_at=row.deployed_at, stopped_at=row.stopped_at,
        )

    async def list_deployments(self, project_id: UUID) -> list[WebsiteDeployment]:
        import json
        async with self.session_factory() as session:
            result = await session.execute(select(WebsiteDeploymentRow).where(WebsiteDeploymentRow.project_id == str(project_id)).order_by(WebsiteDeploymentRow.created_at.desc()))
            rows = result.scalars().all()
        return [WebsiteDeployment(
            project_id=UUID(row.project_id), deployment_id=UUID(row.id), generation_version=row.generation_version,
            version=row.version, status=DeploymentStatus(row.status), provider=row.provider, url=row.url,
            runtime_id=row.runtime_id, diagnostics=json.loads(row.diagnostics), created_at=row.created_at,
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
            row.diagnostics = json.dumps(deployment.diagnostics)
            row.deployed_at = deployment.deployed_at
            row.stopped_at = deployment.stopped_at
            await session.commit()
        return deployment


async def init_database() -> None:
    if not DATABASE_URL:
        return
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def build_repository() -> Repository:
    if not DATABASE_URL:
        return InMemoryRepository()
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    return SqlAlchemyRepository(async_sessionmaker(engine, expire_on_commit=False))


@asynccontextmanager
async def lifespan_repository() -> AsyncIterator[Repository]:
    await init_database()
    yield build_repository()
