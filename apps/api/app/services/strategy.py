from uuid import uuid4

from app.models import (
    ContentStrategy,
    DesignDirection,
    DiscoveryStatus,
    SitemapPage,
    StrategyStatus,
    WebsiteStrategy,
)
from app.store import Repository


class WebsiteStrategyService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def generate(self, project_id) -> WebsiteStrategy:
        context = await self.repository.get_context(project_id)
        if not context:
            raise KeyError(project_id)
        if context.status != DiscoveryStatus.APPROVED:
            raise ValueError("Business Discovery must be approved before generating Website Strategy")

        industry = context.knowledge.industry.value or "the business"
        audience = [x.value for x in context.knowledge.audience if x.value]
        goals = [x.value for x in context.knowledge.goals if x.value]
        goal = goals[0] if goals else "generate qualified enquiries"
        audience_label = audience[0] if audience else "prospective customers"
        proposition = context.knowledge.value_proposition.value or f"Help {audience_label} understand and act on the value offered by {industry}."

        strategy = WebsiteStrategy(
            project_id=project_id,
            strategy_id=uuid4(),
            source_context_version=context.version,
            sitemap=[
                SitemapPage(path="/", name="Home", objective="Communicate the value proposition quickly and direct visitors toward the primary conversion.", primary_cta=goal),
                SitemapPage(path="/about", name="About", objective="Build trust by explaining the business, expertise and relevant credibility."),
                SitemapPage(path="/services", name="Services", objective="Explain the core offer in a scannable, outcome-oriented structure."),
                SitemapPage(path="/contact", name="Contact", objective="Provide a low-friction path for qualified prospects to start a conversation.", primary_cta="Contact us"),
            ],
            content=ContentStrategy(
                positioning=proposition,
                key_messages=[f"Designed for {audience_label}.", f"Focused on {goal}."],
                tone=["clear", "credible", "human"],
                primary_cta="Get started",
            ),
            design=DesignDirection(
                visual_principles=["Clarity before decoration", "Strong hierarchy", "Trust through consistency"],
                layout_principles=["One primary action per section", "Responsive-first composition", "Scannable content blocks"],
            ),
            rationale=[
                "Strategy is derived only from approved Business Discovery context.",
                "The initial sitemap is intentionally small and extensible.",
                "Content and design recommendations prioritize the stated business goal before visual novelty.",
            ],
            status=StrategyStatus.READY_FOR_REVIEW,
        )
        return await self.repository.create_strategy(strategy)

    async def get(self, project_id) -> WebsiteStrategy:
        strategy = await self.repository.get_strategy(project_id)
        if not strategy:
            raise KeyError(project_id)
        return strategy

    async def approve(self, project_id) -> WebsiteStrategy:
        return await self.repository.approve_strategy(project_id)
