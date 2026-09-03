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


def _goal_cta(goal: str) -> str:
    """Turn an approved business goal into a short, action-oriented CTA."""
    lower = goal.casefold()
    if any(word in lower for word in ("visit", "shop", "store", "location")):
        return "Visit us"
    if any(word in lower for word in ("book", "appointment", "consult")):
        return "Book a consultation"
    if any(word in lower for word in ("contact", "enquir", "inquir", "conversation")):
        return "Contact us"
    if any(word in lower for word in ("buy", "purchase", "order", "sales")):
        return "Shop now"
    if any(word in lower for word in ("lead", "customer", "client", "attract")):
        return "Get in touch"
    if "brand" in lower or "showcase" in lower:
        return "Discover more"
    return "Learn more"


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
        goal_cta = _goal_cta(goal)
        audience_label = audience[0] if audience else "prospective customers"
        is_hospitality = any(term in f"{industry} {goal}".casefold() for term in (
            "cafe", "café", "coffee shop", "restaurant", "bakery", "hospitality"
        ))
        if is_hospitality:
            proposition = (
                context.knowledge.value_proposition.value
                or f"A welcoming place for carefully prepared coffee, good food and time well spent at {context.knowledge.business_name.value or 'the café'}."
            )
        else:
            proposition = context.knowledge.value_proposition.value or f"Help {audience_label} understand and act on the value offered by {industry}."
        offer_page_name = "Menu & Coffee" if is_hospitality else "Services"
        offer_objective = (
            "Showcase the menu, signature offerings and experience, and make it easy for visitors to plan a visit."
            if is_hospitality
            else "Explain the core offer in a scannable, outcome-oriented structure."
        )
        contact_objective = (
            "Help visitors plan a visit or get in touch with the business."
            if is_hospitality
            else "Provide a low-friction path for qualified prospects to start a conversation."
        )
        contact_cta = "Visit us" if is_hospitality else "Contact us"

        strategy = WebsiteStrategy(
            project_id=project_id,
            strategy_id=uuid4(),
            source_context_version=context.version,
            sitemap=[
                SitemapPage(path="/", name="Home", objective="Communicate the value proposition quickly and direct visitors toward the primary conversion.", primary_cta=goal_cta),
                SitemapPage(path="/about", name="About", objective=(
                    "Tell the story behind the business, what makes the experience distinctive, and why visitors can trust it."
                    if is_hospitality
                    else "Build trust by explaining the business, expertise and relevant credibility."
                )),
                SitemapPage(path="/services", name=offer_page_name, objective=offer_objective),
                SitemapPage(path="/contact", name="Contact", objective=contact_objective, primary_cta=contact_cta),
            ],
            content=ContentStrategy(
                positioning=proposition,
                key_messages=[
                    (
                        f"A welcoming experience for {audience_label}."
                        if is_hospitality
                        else f"Designed for {audience_label}."
                    ),
                    f"Focused on {goal}.",
                ],
                tone=["clear", "credible", "human"],
                primary_cta=goal_cta,
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

    @staticmethod
    def apply_revision_feedback(strategy: WebsiteStrategy, feedback: str) -> None:
        """Apply the supported deterministic revision instructions to a strategy.

        CAP-002 deliberately remains provider-independent. This parser supports
        explicit CTA syntax plus a small set of natural-language instructions
        that are meaningful for the current vertical slice. A future model-based
        revision agent can replace this method without changing the lifecycle
        or persistence contract.
        """
        normalized = feedback.lower().strip()

        # Preserve the original explicit syntax: ``CTA: Book a consultation``.
        if "cta:" in normalized:
            cta = feedback.split(":", 1)[1].strip()
            if cta:
                WebsiteStrategyService._set_primary_cta(strategy, cta)
            return

        # Natural-language CTA requests.
        requests_consultation = (
            "primary conversion action" in normalized
            or "primary cta" in normalized
            or "call to action" in normalized
            or "cta" in normalized
        ) and "consultation" in normalized

        if requests_consultation:
            WebsiteStrategyService._set_primary_cta(strategy, "Request a consultation")
        elif (
            "primary conversion action" in normalized
            or "primary cta" in normalized
            or "call to action" in normalized
        ) and "contact" in normalized:
            WebsiteStrategyService._set_primary_cta(strategy, "Contact us")

        # Natural-language positioning requests.
        if "positioning" in normalized and "b2b" in normalized:
            if "decision-maker" in normalized or "decision maker" in normalized or "decisionmakers" in normalized:
                strategy.content.positioning = (
                    "Help B2B marketing decision-makers identify and act on "
                    "opportunities to improve commercial growth."
                )
                strategy.content.key_messages[0] = (
                    "Designed for B2B marketing decision-makers."
                )
            else:
                strategy.content.positioning = (
                    "Help B2B customers understand and act on marketing "
                    "opportunities that support commercial growth."
                )
                strategy.content.key_messages[0] = "Designed for B2B customers."

    @staticmethod
    def _set_primary_cta(strategy: WebsiteStrategy, cta: str) -> None:
        strategy.content.primary_cta = cta
        for page in strategy.sitemap:
            if page.path == "/":
                page.primary_cta = cta
            elif page.path == "/contact":
                page.primary_cta = cta

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
        self.apply_revision_feedback(revised, feedback)
        revised.rationale.append(f"Revision incorporated user feedback: {feedback}")

        if context:
            revised.evaluation = self.evaluate(revised, context)
        return await self.repository.create_strategy(revised)
