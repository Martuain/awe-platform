from __future__ import annotations

import re
from html import escape
from uuid import UUID, uuid4

from app.models import WebsiteContentStatus, WebsiteMock, WebsiteMockStatus
from app.services.generation import WebsiteGenerationService, _hero_objective, _is_hospitality, _page_copy, _section_heading
from app.services.validation import WebsiteValidationService
from app.store import Repository


class WebsiteMockService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def create(self, project_id: UUID) -> WebsiteMock:
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError(project_id)
        validation = await WebsiteValidationService(self.repository).validate(project_id)
        if validation.status.value != "passed":
            raise ValueError("A passed validation is required before creating a customer mock")
        current = await self.repository.get_mock(project_id)
        version = (current.version + 1) if current else 1
        html = await self._render_current_mock(project_id, validation.preview.get("html", ""), generation)
        mock = WebsiteMock(
            project_id=project_id,
            mock_id=uuid4(),
            generation_version=generation.version,
            version=version,
            status=WebsiteMockStatus.READY_FOR_REVIEW,
            title=validation.preview.get("title", "AWE Website Mock"),
            html=html,
            feedback=current.feedback if current else [],
        )
        return await self.repository.create_mock(mock)

    async def get(self, project_id: UUID) -> WebsiteMock:
        mock = await self.repository.get_mock(project_id)
        if not mock:
            raise KeyError(project_id)
        generation = await self.repository.get_generation(project_id)
        if not generation:
            return mock
        # CAP-036: Customer Mock is a review of the current website content, not
        # a frozen copy of the original canonical preview. Re-render the view
        # from the latest persisted content while keeping the mock version and
        # approval record tied to its generation boundary.
        html = await self._render_current_mock(project_id, mock.html, generation)
        return mock.model_copy(update={"html": html}, deep=True)

    async def _render_current_mock(self, project_id: UUID, canonical_html: str, generation) -> str:
        specification = await self.repository.get_specification(project_id)
        content = await self.repository.list_content(project_id, status=WebsiteContentStatus.PUBLISHED)
        if not specification:
            return canonical_html

        context = await self.repository.get_context(project_id)
        strategy = await self.repository.get_strategy(project_id)
        site_name = (
            context.knowledge.business_name.value
            if context and context.knowledge.business_name.value
            else "AWE Website"
        )
        industry = context.knowledge.industry.value if context else ""
        goals = [item.value for item in context.knowledge.goals if item.value] if context else []
        goal = goals[0] if goals else "take the next step"
        audience_values = [item.value for item in context.knowledge.audience if item.value] if context else []
        audience = audience_values[0] if audience_values else "prospective customers"
        positioning = strategy.content.positioning if strategy else "A clear value proposition for the people this business serves."
        hospitality = _is_hospitality(industry, goal)
        content_map: dict[str, dict[str, str]] = {}
        for item in content:
            content_map.setdefault(item.page, {})[item.key] = item.value

        # A generated revision can change the canonical website artifact without
        # creating/publishing WebsiteContent. The Customer Mock must therefore
        # resolve its defaults from the current generation before falling back to
        # the Website Specification. Published WebsiteContent remains authoritative.
        generated_defaults = self._generated_defaults(generation)

        style_match = re.search(r"<style[^>]*>([\s\S]*?)</style>", canonical_html, re.IGNORECASE)
        style = style_match.group(1) if style_match else ""
        nav = "".join(
            f'<a href="{self._page_fragment(page.path)}">{escape(page.name)}</a>'
            for page in specification.pages
        )
        pages: list[str] = []
        for index, page in enumerate(specification.pages):
            values = content_map.get(page.path, {})
            generated = generated_defaults.get(page.path, {})
            headline = values.get("headline") or generated.get("headline") or page.name
            page_positioning = values.get("positioning") or generated.get("positioning") or positioning
            cta = (
                values.get("cta")
                if "cta" in values
                else (generated.get("cta") or page.primary_cta or "")
            )
            objective = escape(_hero_objective(page.path, hospitality, site_name, goal))
            sections: list[str] = []
            for section in page.required_sections:
                heading = _section_heading(section)
                primary_copy, secondary_copy = _page_copy(
                    page.path, section, site_name, positioning, industry, audience, goal
                )
                sections.append(
                    f'<section><h2>{escape(heading)}</h2>'
                    f'<p class="lead">{escape(primary_copy)}</p>'
                    f'<div class="card"><p>{escape(secondary_copy)}</p></div></section>'
                )
            cta_html = f'<a class="cta" href="{self._page_fragment("/contact")}">{escape(cta)}</a>' if cta else ""
            page_id = self._page_id(page.path)
            display = "block" if index == 0 else "none"
            pages.append(
                f'<article id="{page_id}" class="awe-mock-page" style="display:{display}">'
                f'<div class="hero"><span class="eyebrow">{escape("Coffee, food and hospitality" if hospitality else "AWE generated website")}</span>'
                f'<h1>{escape(headline)}</h1><p class="lead">{objective}</p>'
                f'<p class="lead">{escape(page_positioning)}</p>{cta_html}</div>'
                f'{"".join(sections)}<footer>Built from an approved AWE strategy and design</footer></article>'
            )

        navigation_css = (
            ".awe-mock-page{display:none!important}.awe-mock-page:first-of-type{display:block!important}"
            ".awe-mock-page:target{display:block!important}"
            "body:has(.awe-mock-page:target) .awe-mock-page:first-of-type:not(:target){display:none!important}"
        )
        return (
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(site_name)}</title><style>{style}{navigation_css}</style></head>'
            f'<body><main><nav><strong>{escape(site_name)}</strong><div class="links">{nav}</div></nav>'
            f'{"".join(pages)}</main></body></html>'
        )

    @staticmethod
    def _generated_defaults(generation) -> dict[str, dict[str, str]]:
        """Extract deterministic visitor-facing defaults from the current generation.

        The generator normally exposes these values through runtime expressions,
        but mock revisions may replace an expression with a literal value. Reading
        the generated artifact keeps the mock aligned with that current revision
        without treating unpublished WebsiteContent as published content.
        """
        defaults: dict[str, dict[str, str]] = {}
        for item in generation.files:
            if not (item.path.startswith("app/") and item.path.endswith("/page.tsx")):
                continue
            if item.path == "app/page.tsx":
                page_path = "/"
            else:
                page_path = "/" + item.path[len("app/") : -len("/page.tsx")]
            values: dict[str, str] = {}
            headline = re.search(r"<h1>([^<{][\s\S]*?)</h1>", item.content)
            if headline:
                values["headline"] = re.sub(r"<[^>]+>", "", headline.group(1)).strip()
            cta = re.search(r'<a className="cta"[^>]*>([^<{][\s\S]*?)</a>', item.content)
            if cta:
                values["cta"] = re.sub(r"<[^>]+>", "", cta.group(1)).strip()
            if values:
                defaults[page_path] = values
        return defaults

    @staticmethod
    def _page_id(path: str) -> str:
        normalized = path.strip("/").replace("/", "-") or "home"
        return f"awe-mock-page-{re.sub(r"[^a-zA-Z0-9_-]", "-", normalized)}"

    @classmethod
    def _page_fragment(cls, path: str) -> str:
        return f"#{cls._page_id(path)}"

    async def feedback(self, project_id: UUID, feedback: str) -> WebsiteMock:
        mock = await self.get(project_id)
        if mock.status == WebsiteMockStatus.APPROVED:
            raise ValueError("Approved website mock is immutable")
        updated = mock.model_copy(deep=True)
        updated.status = WebsiteMockStatus.CHANGES_REQUESTED
        updated.feedback.append(feedback)
        await self.repository.create_mock_feedback(project_id, updated.mock_id, updated.version, feedback)
        return await self.repository.create_mock(updated)

    async def revise(self, project_id: UUID, feedback: str) -> WebsiteMock:
        current = await self.feedback(project_id, feedback)
        generation = await WebsiteGenerationService(self.repository).revise(project_id, feedback)
        validation = await WebsiteValidationService(self.repository).validate(project_id)
        if validation.status.value != "passed":
            raise ValueError("Generated revision did not pass validation")
        html = await self._render_current_mock(project_id, validation.preview.get("html", ""), generation)
        revised = WebsiteMock(
            project_id=project_id,
            mock_id=uuid4(),
            generation_version=generation.version,
            version=current.version + 1,
            status=WebsiteMockStatus.READY_FOR_REVIEW,
            title=validation.preview.get("title", "AWE Website Mock"),
            html=html,
            feedback=current.feedback,
        )
        return await self.repository.create_mock(revised)

    async def approve(self, project_id: UUID) -> WebsiteMock:
        mock = await self.get(project_id)
        if mock.status != WebsiteMockStatus.READY_FOR_REVIEW:
            raise ValueError("Website mock must be ready for review before approval")
        approved = mock.model_copy(deep=True)
        approved.status = WebsiteMockStatus.APPROVED
        from datetime import datetime, timezone
        approved.approved_at = datetime.now(timezone.utc)
        return await self.repository.create_mock(approved)
