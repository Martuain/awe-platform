import json
import re
from dataclasses import dataclass

from app.models import BusinessKnowledge, DiscoveryContext, DiscoveryStatus, KnowledgeField, DiscoverySource
from app.store import Repository


@dataclass
class ModelResponse:
    content: str


class MockModelGateway:
    async def complete(self, request: dict) -> str:
        text = request["messages"][-1]["content"]
        return json.dumps(extract_knowledge(text))


def extract_knowledge(message: str) -> dict:
    # Deterministic baseline used by tests and local development. A real provider
    # adapter can implement the same structured-output contract later.
    lower = message.lower()
    industry = None
    for candidate in ["architecture", "marketing", "restaurant", "saas", "fintech", "ecommerce", "consulting"]:
        if candidate in lower:
            industry = candidate
            break
    business_name = None
    match = re.search(r"(?:called|named)\s+([A-Z][\w&.-]*(?:\s+[A-Z][\w&.-]*)*)", message)
    if match:
        business_name = match.group(1).strip()
    goals = []
    for keyword in ["leads", "enquiries", "bookings", "sales", "customers", "visibility"]:
        if keyword in lower:
            goals.append(keyword)
    return {"business_name": business_name, "industry": industry, "goals": goals}


class DiscoveryService:
    def __init__(self, repository: Repository, gateway: MockModelGateway | None = None) -> None:
        self.repository = repository
        self.gateway = gateway or MockModelGateway()

    async def start(self, project_id):
        return await self.repository.start_discovery(project_id)

    async def message(self, project_id, message: str) -> DiscoveryContext:
        context = await self.repository.append_message(project_id, message)
        result = json.loads(await self.gateway.complete({"messages": [{"role": "user", "content": message}]}))
        source = DiscoverySource(reference=f"message:{len(context.source_messages)}")
        knowledge = context.knowledge.model_copy(deep=True)
        if result.get("business_name"):
            knowledge.business_name = KnowledgeField(value=result["business_name"], confidence=0.85, sources=[source])
        if result.get("industry"):
            knowledge.industry = KnowledgeField(value=result["industry"], confidence=0.8, sources=[source])
        if result.get("goals"):
            knowledge.goals = [KnowledgeField(value=g, confidence=0.75, sources=[source]) for g in result["goals"]]
        context.knowledge = knowledge
        required = [knowledge.industry.value, knowledge.goals]
        context.completeness_score = sum(bool(x) for x in required) / len(required)
        context.open_questions = [] if context.completeness_score >= 1 else ["What is the primary business goal for the website?"]
        if context.completeness_score >= 1:
            context.status = DiscoveryStatus.AWAITING_APPROVAL
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
