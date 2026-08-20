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


class SourceMessageRow(Base):
    __tablename__ = "source_messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Repository:
    async def create_project(self, name: str) -> Project: ...
    async def get_project(self, project_id: UUID) -> Project | None: ...
    async def start_discovery(self, project_id: UUID) -> DiscoveryContext: ...
    async def get_context(self, project_id: UUID) -> DiscoveryContext | None: ...
    async def append_message(self, project_id: UUID, message: str) -> DiscoveryContext: ...
    async def update_context(self, context: DiscoveryContext) -> DiscoveryContext: ...
    async def approve_context(self, project_id: UUID) -> DiscoveryContext: ...


class InMemoryRepository(Repository):
    def __init__(self) -> None:
        self.projects: dict[UUID, Project] = {}
        self.contexts: dict[UUID, DiscoveryContext] = {}

    async def create_project(self, name: str) -> Project:
        project = Project(name=name)
        self.projects[project.id] = project
        return project

    async def get_project(self, project_id: UUID) -> Project | None:
        return self.projects.get(project_id)

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
