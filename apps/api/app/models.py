from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class DiscoveryMessageRequest(BaseModel):
    project_id: UUID
    message: str = Field(min_length=1, max_length=10000)


class DiscoveryContext(BaseModel):
    project_id: UUID
    status: str = "collecting"
    business_name: str | None = None
    industry: str | None = None
    goals: list[str] = []
    audience: list[str] = []
    value_proposition: str | None = None
    source_messages: list[str] = []
