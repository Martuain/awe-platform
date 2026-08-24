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


class StrategyEvaluation(BaseModel):
    completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    business_alignment: float = Field(default=0.0, ge=0.0, le=1.0)
    traceability: float = Field(default=0.0, ge=0.0, le=1.0)
    actionability: float = Field(default=0.0, ge=0.0, le=1.0)
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    findings: list[str] = Field(default_factory=list)
    ready: bool = False


class StrategyRevisionRequest(BaseModel):
    feedback: str = Field(min_length=1, max_length=5000)


class WebsiteStrategy(BaseModel):
    project_id: UUID
    strategy_id: UUID = Field(default_factory=uuid4)
    version: int = 1
    status: StrategyStatus = StrategyStatus.DRAFT
    sitemap: list[SitemapPage] = Field(default_factory=list)
    content: ContentStrategy = Field(default_factory=ContentStrategy)
    design: DesignDirection = Field(default_factory=DesignDirection)
    rationale: list[str] = Field(default_factory=list)
    evaluation: StrategyEvaluation = Field(default_factory=StrategyEvaluation)
    revision_feedback: list[str] = Field(default_factory=list)
    source_context_version: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: datetime | None = None

class BrandDesignStatus(str, Enum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"


class ColorPalette(BaseModel):
    primary: str = ""
    secondary: str = ""
    accent: str = ""
    background: str = ""
    text: str = ""


class TypographyDirection(BaseModel):
    heading_style: str = ""
    body_style: str = ""
    hierarchy: str = "clear"


class BrandDesignDirection(BaseModel):
    project_id: UUID
    design_id: UUID = Field(default_factory=uuid4)
    version: int = 1
    status: BrandDesignStatus = BrandDesignStatus.DRAFT
    brand_attributes: list[str] = Field(default_factory=list)
    visual_principles: list[str] = Field(default_factory=list)
    color_palette: ColorPalette = Field(default_factory=ColorPalette)
    typography: TypographyDirection = Field(default_factory=TypographyDirection)
    imagery_direction: list[str] = Field(default_factory=list)
    component_direction: list[str] = Field(default_factory=list)
    accessibility_requirements: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
    source_strategy_version: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: datetime | None = None





class WebsiteGenerationStatus(str, Enum):
    GENERATED = "generated"
    VALIDATED = "validated"
    FAILED = "failed"


class GeneratedFile(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    content: str


class WebsiteGeneration(BaseModel):
    project_id: UUID
    generation_id: UUID = Field(default_factory=uuid4)
    version: int = 1
    status: WebsiteGenerationStatus = WebsiteGenerationStatus.GENERATED
    source_specification_version: int = 0
    framework: str = "Next.js App Router"
    files: list[GeneratedFile] = Field(default_factory=list)
    pages_generated: list[str] = Field(default_factory=list)
    validation: dict[str, object] = Field(default_factory=dict)
    rationale: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebsiteSpecificationStatus(str, Enum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"


class WebsitePageSpecification(BaseModel):
    path: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=120)
    objective: str = Field(min_length=1, max_length=500)
    primary_cta: str | None = None
    required_sections: list[str] = Field(default_factory=list)
    content_requirements: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)


class WebsiteSpecification(BaseModel):
    project_id: UUID
    specification_id: UUID = Field(default_factory=uuid4)
    version: int = 1
    status: WebsiteSpecificationStatus = WebsiteSpecificationStatus.DRAFT
    pages: list[WebsitePageSpecification] = Field(default_factory=list)
    global_components: list[str] = Field(default_factory=list)
    content_requirements: list[str] = Field(default_factory=list)
    seo_requirements: list[str] = Field(default_factory=list)
    accessibility_requirements: list[str] = Field(default_factory=list)
    responsive_requirements: list[str] = Field(default_factory=list)
    technical_requirements: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
    source_strategy_version: int = 0
    source_design_version: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: datetime | None = None
