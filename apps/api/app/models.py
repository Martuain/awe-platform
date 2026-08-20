from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    ACTIVE = "active"


class DiscoveryStatus(str, Enum):
    COLLECTING = "collecting"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class DiscoveryMessageRequest(BaseModel):
    project_id: UUID
    message: str = Field(min_length=1, max_length=10000)


class DiscoverySource(BaseModel):
    kind: str = "user_message"
    reference: str


class KnowledgeField(BaseModel):
    value: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    sources: list[DiscoverySource] = Field(default_factory=list)


class BusinessKnowledge(BaseModel):
    business_name: KnowledgeField = Field(default_factory=KnowledgeField)
    industry: KnowledgeField = Field(default_factory=KnowledgeField)
    goals: list[KnowledgeField] = Field(default_factory=list)
    audience: list[KnowledgeField] = Field(default_factory=list)
    value_proposition: KnowledgeField = Field(default_factory=KnowledgeField)


class DiscoveryContext(BaseModel):
    project_id: UUID
    session_id: UUID
    version: int = 1
    status: DiscoveryStatus = DiscoveryStatus.COLLECTING
    knowledge: BusinessKnowledge = Field(default_factory=BusinessKnowledge)
    source_messages: list[str] = Field(default_factory=list)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    open_questions: list[str] = Field(default_factory=list)
    approved_at: datetime | None = None


class DiscoveryApprovalResponse(BaseModel):
    context: DiscoveryContext


class DiscoverySession(BaseModel):
    project_id: UUID
    session_id: UUID = Field(default_factory=uuid4)
    status: DiscoveryStatus = DiscoveryStatus.COLLECTING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
