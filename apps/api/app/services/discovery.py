from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.models import (
    BusinessKnowledge,
    DiscoveryContext,
    DiscoveryStatus,
    KnowledgeField,
    DiscoverySource,
)
from app.store import Repository
from app.services.model_gateway import build_model_gateway


@dataclass
class ModelResponse:
    content: str


class MockModelGateway:
    """Deterministic provider-neutral gateway used by tests and local development."""

    async def complete(self, request: dict) -> str:
        text = request["messages"][-1]["content"]
        return json.dumps(extract_knowledge(text))


INDUSTRY_ALIASES = (
    ("restaurant", (
        "restaurant", "restaurants", "café", "cafe", "cafeteria", "coffee shop",
        "coffeehouse", "coffee house", "bakery", "bistro", "bar", "tapas",
        "tienda de café", "cafetería",
    )),
    ("retail", (
        "retail", "retailer", "shop", "store", "retail shop", "retail store",
        "boutique", "market", "mercado", "tienda", "comercio",
    )),
    ("hospitality", ("hospitality", "hotel", "hotels", "lodging", "accommodation")),
    ("architecture", ("architecture", "architect", "architectural")),
    ("marketing", ("marketing", "agency", "advertising")),
    ("saas", ("saas", "software as a service")),
    ("technology", ("technology", "tech", "software", "it company", "information technology")),
    ("fintech", ("fintech", "financial technology")),
    ("finance", ("finance", "financial services", "banking", "investment")),
    ("ecommerce", ("ecommerce", "e-commerce", "online store", "online shop")),
    ("consulting", ("consulting", "consultancy", "consultant")),
    ("healthcare", ("healthcare", "health care", "medical", "clinic", "hospital")),
    ("education", ("education", "school", "university", "training", "academy")),
    ("real estate", ("real estate", "property", "realtor", "estate agency")),
    ("legal", ("legal", "law firm", "lawyer", "attorney")),
    ("construction", ("construction", "builder", "building contractor")),
    ("fitness", ("fitness", "gym", "personal training")),
    ("beauty", ("beauty", "salon", "spa", "hairdresser", "barber")),
    ("fashion", ("fashion", "clothing", "apparel", "fashion brand")),
    ("automotive", ("automotive", "car dealership", "auto repair", "automobile")),
    ("travel", ("travel", "tourism", "travel agency", "tour operator")),
)

GOAL_PATTERNS = (
    r"(?:primary|main|business)?\s*goal\s+(?:of|for)\s+(?:the\s+)?(?:website|site)\s*(?:is|would\s+be|should\s+be|:|-)?\s*(?:to\s+)?(.+?)(?:[.!?]|$)",
    r"(?:primary\s+)?(?:business\s+)?goal\s*(?:is|would\s+be|should\s+be|:|-)?\s*(?:to\s+)?(.+?)(?:[.!?]|$)",
    r"(?:we|our\s+business)\b.*?\b(?:want|wants|need|needs|aim|aims)\s+(?:to\s+)?(.+?)(?:[.!?]|$)",
    r"(?:the\s+website\s+should|we\s+want\s+the\s+website\s+to)\s+(.+?)(?:[.!?]|$)",
)

AUDIENCE_PATTERNS = (
    r"(?:our\s+)?(?:target|main|primary)\s+(?:audience|customers?|clients?)\s*(?:is|are|:|-)?\s*(.+?)(?:[.!?]|$)",
    r"(?:we|our\s+business)\b.*?\b(?:serve|serves|target|targets)\s+(.+?)(?:[.!?]|$)",
    r"(?:for|aimed\s+at)\s+(.+?)(?:[.!?]|$)",
)

VALUE_PATTERNS = (
    r"(?:our\s+)?(?:value\s+proposition|unique\s+value|usp)\s*(?:is|:|-)?\s*(.+?)(?:[.!?]|$)",
    r"(?:what\s+(?:makes|sets)\s+us\s+apart(?:\s+is)?|we\s+differentiate\s+ourselves\s+by)\s+(.+?)(?:[.!?]|$)",
    r"(?:customers?|clients?)\s+(?:choose|use)\s+us\s+because\s+(.+?)(?:[.!?]|$)",
)


def _clean_extracted(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" \t\r\n.,;:")
    return value


def _first_match(patterns: tuple[str, ...], message: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            value = _clean_extracted(match.group(1))
            if value:
                return value
    return None


def _extract_goals(message: str) -> list[str]:
    goals: list[str] = []

    for pattern in GOAL_PATTERNS:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            value = _clean_extracted(match.group(1))
            value = re.sub(r"^help(?:\s+us)?\s+", "", value, flags=re.IGNORECASE)
            if value:
                goals.append(value)
                break

    # Also retain concise, explicit goal signals when the message does not use
    # a goal/want/aim construction.
    lower = message.lower()
    if not goals:
        for keyword in ("leads", "enquiries", "bookings", "sales", "customers", "visibility"):
            if keyword in lower:
                goals.append(keyword)

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(goals))


def extract_knowledge(message: str) -> dict:
    """Extract only evidence present in one user message.

    This mock intentionally avoids inventing missing information. A future model
    adapter can implement the same structured-output contract.
    """

    lower = message.lower()
    # Match aliases as words/phrases rather than arbitrary substrings. This
    # prevents collisions such as "marketing" -> "retail" via "market" and
    # "fintech" -> "technology" via "tech". Prefer the longest matching alias
    # when multiple categories are present.
    industry_matches = [
        (len(alias), canonical)
        for canonical, aliases in INDUSTRY_ALIASES
        for alias in aliases
        if re.search(r"(?<!\\w)" + re.escape(alias) + r"(?!\\w)", lower)
    ]
    industry = max(industry_matches, key=lambda item: item[0])[1] if industry_matches else None

    # Also recognize explicit industry/sector statements when the value is not
    # in the canonical alias catalogue. This prevents Discovery from repeatedly
    # asking the same question simply because a customer used a valid but
    # previously unseen industry label.
    if not industry:
        explicit_industry = re.search(
            r"(?:our\s+)?(?:industry|sector|business\s+sector)\s*(?:is|:|-)?\s*([^.!?]+)",
            message,
            flags=re.IGNORECASE,
        )
        if explicit_industry:
            industry = _clean_extracted(explicit_industry.group(1))

    if not industry:
        operating_in = re.search(
            r"(?:we\s+)?(?:operate|work)\s+(?:in|within)\s+([^.!?]+)",
            message,
            flags=re.IGNORECASE,
        )
        if operating_in:
            industry = _clean_extracted(operating_in.group(1))

    business_name = None
    match = re.search(
        r"(?:business\s+name|company\s+name|brand\s+name)\s*(?:is|:|-)?\s*([^.?!]+)",
        message,
        flags=re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r"(?:called|named)\s+([^.?!]+)",
            message,
            flags=re.IGNORECASE,
        )
    if match:
        business_name = _clean_extracted(match.group(1))

    audience = _first_match(AUDIENCE_PATTERNS, message)
    value_proposition = _first_match(VALUE_PATTERNS, message)

    return {
        "business_name": business_name,
        "industry": industry,
        "goals": _extract_goals(message),
        "audience": audience,
        "value_proposition": value_proposition,
    }


QUESTION_BY_FIELD = {
    "industry": "What industry does the business operate in?",
    "goals": "What is the primary business goal for the website?",
    "audience": "Who is the main audience you want the website to reach?",
    "value_proposition": "What makes the business different or valuable to that audience?",
}


def _missing_fields(knowledge: BusinessKnowledge) -> list[str]:
    # Industry + at least one goal are the minimum gating requirements for the
    # MVP. Audience and value proposition are captured when available, but do
    # not block approval; this keeps Discovery useful without forcing an
    # unnecessarily long interview.
    missing: list[str] = []
    if not knowledge.industry.value:
        missing.append("industry")
    if not knowledge.goals:
        missing.append("goals")
    return missing


def _merge_field(
    current: KnowledgeField,
    value: str | None,
    source: DiscoverySource,
    confidence: float,
) -> KnowledgeField:
    if not value:
        return current
    sources = list(current.sources)
    if source.reference not in {item.reference for item in sources}:
        sources.append(source)
    return KnowledgeField(
        value=value,
        confidence=confidence,
        sources=sources,
    )


def _merge_goal(
    goals: list[KnowledgeField],
    value: str,
    source: DiscoverySource,
) -> list[KnowledgeField]:
    normalized = value.casefold()
    for goal in goals:
        if goal.value and goal.value.casefold() == normalized:
            if source.reference not in {item.reference for item in goal.sources}:
                goal.sources.append(source)
            return goals

    goals.append(KnowledgeField(value=value, confidence=0.75, sources=[source]))
    return goals


class DiscoveryService:
    def __init__(
        self,
        repository: Repository,
        gateway: MockModelGateway | None = None,
    ) -> None:
        self.repository = repository
        self.gateway = gateway or build_model_gateway(MockModelGateway())

    async def start(self, project_id):
        existing = await self.repository.get_context(project_id)
        if existing:
            return existing
        context = await self.repository.start_discovery(project_id)
        context.open_questions = [QUESTION_BY_FIELD["industry"]]
        return await self._persist_updated_context(context)

    async def message(self, project_id, message: str) -> DiscoveryContext:
        context = await self.repository.append_message(project_id, message)
        result = json.loads(
            await self.gateway.complete(
                {"messages": [{"role": "user", "content": message}]}
            )
        )
        source = DiscoverySource(reference=f"message:{len(context.source_messages)}")
        knowledge = context.knowledge.model_copy(deep=True)

        knowledge.business_name = _merge_field(
            knowledge.business_name, result.get("business_name"), source, 0.85
        )
        knowledge.industry = _merge_field(
            knowledge.industry, result.get("industry"), source, 0.8
        )

        for goal in result.get("goals") or []:
            _merge_goal(knowledge.goals, goal, source)

        audience = result.get("audience")
        if audience:
            existing = {item.value.casefold() for item in knowledge.audience if item.value}
            if audience.casefold() not in existing:
                knowledge.audience.append(
                    KnowledgeField(value=audience, confidence=0.75, sources=[source])
                )

        knowledge.value_proposition = _merge_field(
            knowledge.value_proposition,
            result.get("value_proposition"),
            source,
            0.75,
        )

        context.knowledge = knowledge
        missing = _missing_fields(knowledge)
        context.completeness_score = (2 - len(missing)) / 2
        context.open_questions = [QUESTION_BY_FIELD[field] for field in missing[:1]]

        if not missing:
            context.status = DiscoveryStatus.AWAITING_APPROVAL
        else:
            context.status = DiscoveryStatus.COLLECTING

        return await self._persist_updated_context(context)

    async def _persist_updated_context(self, context: DiscoveryContext) -> DiscoveryContext:
        return await self.repository.update_context(context)

    async def approve(self, project_id):
        context = await self.repository.get_context(project_id)
        if not context:
            raise KeyError(project_id)
        if context.status != DiscoveryStatus.AWAITING_APPROVAL:
            raise ValueError("Discovery context is not ready for approval")
        return await self.repository.approve_context(project_id)
