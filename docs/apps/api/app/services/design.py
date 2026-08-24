from uuid import uuid4

from app.models import (
    BrandDesignDirection,
    BrandDesignStatus,
    ColorPalette,
    TypographyDirection,
    DiscoveryStatus,
    WebsiteStrategy,
)
from app.store import Repository


class BrandDesignService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def generate(self, project_id) -> BrandDesignDirection:
        context = await self.repository.get_context(project_id)
        strategy = await self.repository.get_strategy(project_id)
        if not context:
            raise KeyError("context")
        if context.status != DiscoveryStatus.APPROVED:
            raise ValueError("Business Discovery must be approved before generating Brand & Design Direction")
        if not strategy:
            raise KeyError("strategy")
        if strategy.status.value != "approved":
            raise ValueError("Website Strategy must be approved before generating Brand & Design Direction")

        tone = strategy.content.tone or ["clear", "credible", "human"]
        design = BrandDesignDirection(
            project_id=project_id,
            design_id=uuid4(),
            source_strategy_version=strategy.version,
            brand_attributes=tone[:3],
            visual_principles=strategy.design.visual_principles + ["Use whitespace to reinforce hierarchy"],
            color_palette=ColorPalette(
                primary="Deep neutral",
                secondary="Warm neutral",
                accent="One high-contrast action color",
                background="Accessible light/dark surfaces",
                text="High-contrast foreground",
            ),
            typography=TypographyDirection(
                heading_style="Confident, distinctive, short headings",
                body_style="Readable sans-serif with comfortable line length",
                hierarchy="Clear H1/H2/H3 hierarchy with restrained variation",
            ),
            imagery_direction=["Prefer authentic business-relevant imagery", "Avoid decorative imagery that competes with the primary action"],
            component_direction=["Consistent CTA treatment", "Reusable cards and sections", "Visible focus states", "Responsive-first components"],
            accessibility_requirements=["WCAG-oriented contrast", "Keyboard-visible focus", "Semantic heading hierarchy", "Respect reduced-motion preferences"],
            rationale=[
                "Design direction is derived from the approved Website Strategy.",
                "The palette remains intentionally semantic until brand assets are available.",
                "Accessibility and responsive behavior are treated as design requirements, not post-build fixes.",
            ],
            status=BrandDesignStatus.READY_FOR_REVIEW,
        )
        return await self.repository.create_design(design)

    async def get(self, project_id):
        design = await self.repository.get_design(project_id)
        if not design: raise KeyError(project_id)
        return design

    async def approve(self, project_id):
        return await self.repository.approve_design(project_id)
