from uuid import uuid4

from app.models import (
    BrandDesignStatus,
    WebsitePageSpecification,
    WebsiteSpecification,
    WebsiteSpecificationStatus,
)
from app.store import Repository


class WebsiteSpecificationService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def generate(self, project_id) -> WebsiteSpecification:
        strategy = await self.repository.get_strategy(project_id)
        design = await self.repository.get_design(project_id)
        if not strategy:
            raise KeyError("strategy")
        if strategy.status.value != "approved":
            raise ValueError("Website Strategy must be approved before generating Website Specification")
        if not design:
            raise KeyError("design")
        if design.status != BrandDesignStatus.APPROVED:
            raise ValueError("Brand & Design Direction must be approved before generating Website Specification")

        pages = [
            WebsitePageSpecification(
                path=page.path,
                name=page.name,
                objective=page.objective,
                primary_cta=page.primary_cta or strategy.content.primary_cta,
                required_sections=self._sections_for(page.path),
                content_requirements=self._content_for(page.path),
                components=self._components_for(page.path),
            )
            for page in strategy.sitemap
        ]
        spec = WebsiteSpecification(
            project_id=project_id,
            specification_id=uuid4(),
            source_strategy_version=strategy.version,
            source_design_version=design.version,
            pages=pages,
            global_components=["Header/navigation", "Primary CTA", "Footer", "Responsive navigation", "Accessible form controls"],
            content_requirements=["Use approved positioning and key messages", "Keep page copy aligned to the target audience", "Provide meaningful empty/error states where interactions require them"],
            seo_requirements=["Unique title and meta description per page", "One clear H1 per page", "Descriptive internal links", "Semantic HTML and crawlable content"],
            accessibility_requirements=design.accessibility_requirements,
            responsive_requirements=["Mobile-first layout behavior", "No horizontal overflow", "Touch-friendly interactive targets", "Readable typography across breakpoints"],
            technical_requirements=["Next.js App Router-compatible structure", "Reusable typed components", "No page-specific duplication when a shared component is appropriate", "Keep content and presentation separable"],
            acceptance_criteria=["Every approved sitemap page has a defined objective", "Every primary conversion path has an explicit CTA", "Design direction is traceable to the approved design artifact", "Pages meet accessibility and responsive requirements", "Specification is sufficient for deterministic website generation"],
            rationale=["The specification translates approved strategy and design into implementation-ready constraints.", "Page objectives and CTAs remain traceable to the approved strategy.", "Global requirements consolidate accessibility, responsive, SEO and technical expectations before generation."],
            status=WebsiteSpecificationStatus.READY_FOR_REVIEW,
        )
        return await self.repository.create_specification(spec)

    @staticmethod
    def _sections_for(path: str) -> list[str]:
        mapping = {
            "/": ["Hero/value proposition", "Key benefits", "Proof or credibility", "Primary conversion section"],
            "/about": ["Business story", "Approach or differentiators", "Trust signals"],
            "/services": ["Services overview", "Service detail/value", "Conversion section"],
            "/contact": ["Contact context", "Contact form or action", "Response expectation"],
        }
        return mapping.get(path, ["Page introduction", "Primary content", "Conversion section"])

    @staticmethod
    def _content_for(path: str) -> list[str]:
        if path == "/":
            return ["State who the business serves and the value it provides", "Lead with the approved positioning"]
        if path == "/contact":
            return ["Make the next step unambiguous", "Set expectations for the response"]
        return ["Reflect the approved strategy and audience needs", "Use scannable content hierarchy"]

    @staticmethod
    def _components_for(path: str) -> list[str]:
        if path == "/contact":
            return ["Contact form", "CTA", "Validation/error states"]
        return ["Hero", "Content sections", "CTA", "Responsive media/content block"]

    async def get(self, project_id):
        spec = await self.repository.get_specification(project_id)
        if not spec:
            raise KeyError(project_id)
        return spec

    async def approve(self, project_id):
        return await self.repository.approve_specification(project_id)
