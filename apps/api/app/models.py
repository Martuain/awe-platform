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


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"


class SitemapPage(BaseModel):
    path: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=120)
    objective: str = Field(min_length=1, max_length=500)
    primary_cta: str | None = None


class ContentStrategy(BaseModel):
    positioning: str = ""
    key_messages: list[str] = Field(default_factory=list)
    tone: list[str] = Field(default_factory=list)
    primary_cta: str | None = None


class DesignDirection(BaseModel):
    visual_principles: list[str] = Field(default_factory=list)
    layout_principles: list[str] = Field(default_factory=list)
    accessibility_priority: str = "high"
    responsive_priority: str = "high"


class WebsiteStrategy(BaseModel):
    project_id: UUID
    strategy_id: UUID = Field(default_factory=uuid4)
    version: int = 1
    status: StrategyStatus = StrategyStatus.DRAFT
    sitemap: list[SitemapPage] = Field(default_factory=list)
    content: ContentStrategy = Field(default_factory=ContentStrategy)
    design: DesignDirection = Field(default_factory=DesignDirection)
    rationale: list[str] = Field(default_factory=list)
    source_context_version: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: datetime | None = None
