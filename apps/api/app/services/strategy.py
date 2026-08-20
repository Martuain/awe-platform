from uuid import uuid4

from app.models import (
    ContentStrategy,
    DesignDirection,
    DiscoveryStatus,
    SitemapPage,
    StrategyEvaluation,
    StrategyStatus,
    WebsiteStrategy,
)
from app.store import Repository


class WebsiteStrategyService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    @staticmethod
    def evaluate(strategy: WebsiteStrategy, context) -> StrategyEvaluation:
        findings: list[str] = []
        completeness = sum(bool(value) for value in (strategy.sitemap, strategy.content.positioning, strategy.content.primary_cta, strategy.design.visual_principles)) / 4
        goals = {x.value for x in context.knowledge.goals if x.value}
        audience = {x.value for x in context.knowledge.audience if x.value}
        business_alignment = 1.0 if strategy.content.primary_cta and (goals or audience) else 0.5
        traceability = 1.0 if strategy.source_context_version == context.version else 0.0
        actionability = min(1.0, sum(bool(page.objective) for page in strategy.sitemap) / max(1, len(strategy.sitemap)))
        if not goals:
            findings.append("No explicit business goal is available in the approved discovery context.")
        if not audience:
            findings.append("No explicit audience is available in the approved discovery context.")
        if len(strategy.sitemap) < 3:
            findings.append("Strategy should contain at least three useful pages.")
        overall = round((completeness + business_alignment + traceability + actionability) / 4, 2)
        ready = overall >= 0.75 and traceability == 1.0
        return StrategyEvaluation(
            completeness=round(completeness, 2),
            business_alignment=round(business_alignment, 2),
            traceability=round(traceability, 2),
            actionability=round(actionability, 2),
            overall=overall,
            findings=findings,
            ready=ready,
        )

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
        strategy.evaluation = self.evaluate(strategy, context)
        return await self.repository.create_strategy(strategy)

    async def get(self, project_id) -> WebsiteStrategy:
        strategy = await self.repository.get_strategy(project_id)
        if not strategy:
            raise KeyError(project_id)
        return strategy

    async def approve(self, project_id) -> WebsiteStrategy:
        strategy = await self.get(project_id)
        if not strategy.evaluation.ready:
            raise ValueError("Website strategy did not pass evaluation")
        return await self.repository.approve_strategy(project_id)

    async def revise(self, project_id, feedback: str) -> WebsiteStrategy:
        context = await self.repository.get_context(project_id)
        strategy = await self.get(project_id)
        if strategy.status == StrategyStatus.APPROVED:
            raise ValueError("Approved website strategy is immutable")
        revised = strategy.model_copy(deep=True)
        revised.strategy_id = uuid4()
        revised.version += 1
        revised.status = StrategyStatus.READY_FOR_REVIEW
        revised.approved_at = None
        revised.revision_feedback.append(feedback)
        revised.rationale.append(f"Revision incorporated user feedback: {feedback}")
        if "cta" in feedback.lower() and revised.content.primary_cta:
            revised.content.primary_cta = feedback.split(":", 1)[1].strip() if ":" in feedback else revised.content.primary_cta
        if context:
            revised.evaluation = self.evaluate(revised, context)
        return await self.repository.create_strategy(revised)
