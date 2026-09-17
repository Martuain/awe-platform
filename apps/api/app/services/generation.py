from __future__ import annotations

import json
from html import escape
from uuid import uuid4
import re

from app.models import GeneratedFile, WebsiteGeneration, WebsiteGenerationStatus
from app.store import Repository


_HOSPITALITY_TERMS = (
    "cafe",
    "café",
    "coffee shop",
    "restaurant",
    "bakery",
    "hospitality",
)

_SECTION_HEADINGS = {
    "Hero/value proposition": "What we offer",
    "Value proposition": "What we offer",
    "Key benefits": "Why choose us",
    "Proof or credibility": "Why customers trust us",
    "Primary conversion section": "Ready to take the next step?",
    "Business story": "Our story",
    "Approach or differentiators": "What makes us different",
    "Trust signals": "Why customers choose us",
    "Services overview": "What we offer",
    "Service detail and value": "How the offer helps",
    "Service detail/value": "How the offer helps",
    "Conversion section": "Take the next step",
    "Contact context": "Get in touch",
    "Contact form or action": "Get in touch",
    "Response expectation": "What happens next",
    "Page introduction": "A closer look",
    "Primary content": "The details",
}


def _is_hospitality(industry: str, goal: str) -> bool:
    haystack = f"{industry} {goal}".casefold()
    return any(term in haystack for term in _HOSPITALITY_TERMS)


def _section_heading(section: str) -> str:
    return _SECTION_HEADINGS.get(section, section.replace("/", " and "))


def _hero_objective(path: str, hospitality: bool, site_name: str, goal: str) -> str:
    if hospitality:
        return {
            "/": f"Discover what makes {site_name} special and find a simple reason to visit.",
            "/about": f"Learn the story, coffee and hospitality behind {site_name}.",
            "/services": "Explore the coffee, food and seasonal offering and plan a visit.",
            "/contact": "Plan a visit or get in touch with the café.",
        }.get(path, f"Discover what makes {site_name} special.")
    return {
        "/": "Understand the value quickly and take the next step.",
        "/about": "Learn the story, strengths and approach behind the business.",
        "/services": "Explore the core offer and how it can help.",
        "/contact": "Start a conversation and take the next step.",
    }.get(path, f"Discover more about {site_name}.")


def _page_copy(
    path: str,
    section: str,
    site_name: str,
    positioning: str,
    industry: str,
    audience: str,
    goal: str,
) -> tuple[str, str]:
    hospitality = _is_hospitality(industry, goal)

    if hospitality:
        hospitality_copy = {
            "/": {
                "Value proposition and atmosphere": (
                    "A welcoming place for carefully prepared coffee, good food and time well spent.",
                    positioning,
                ),
                "Signature menu highlights": (
                    "Explore the coffee, food and seasonal offerings that make the café worth a visit. Menu details can be kept current as the offering changes.",
                    f"{site_name} is designed around an experience visitors can discover, enjoy and return to.",
                ),
                "Reasons to visit": (
                    f"For {audience}, the experience should feel approachable, memorable and easy to choose.",
                    f"The website supports the goal to {goal.rstrip('.') }.",
                ),
                "Visit prompt": (
                    "Ready to make it part of your next coffee stop?",
                    "Plan a visit or get in touch with the café.",
                ),
                "default": (
                    positioning,
                    f"Discover what makes {site_name} special.",
                ),
            },
            "/about": {
                "Our story": (
                    f"{site_name} brings together coffee, hospitality and a place where visitors can feel welcome.",
                    "The brand story can grow from the business details approved during discovery.",
                ),
                "Coffee and hospitality approach": (
                    "The experience puts care, clarity and hospitality ahead of unnecessary complexity.",
                    "Use this space to introduce the people, craft and choices that shape the café.",
                ),
                "What guests can expect": (
                    "A clear sense of what the café feels like, what it serves and why people come back.",
                    positioning,
                ),
                "default": (
                    positioning,
                    f"Learn more about {site_name} and the experience behind it.",
                ),
            },
            "/services": {
                "Menu highlights": (
                    "Discover signature coffee, food and seasonal choices, with the current menu kept easy to find and update.",
                    "Where exact menu details are not yet available, the site avoids inventing prices or specific items.",
                ),
                "Coffee and food experience": (
                    "From the first coffee of the day to a relaxed catch-up, the offering is presented around the experience it creates.",
                    positioning,
                ),
                "Plan your visit": (
                    "Use the café's current opening, location and contact details to decide when to stop by.",
                    "The next step is simple: visit the café or contact the team with a question.",
                ),
                "default": (
                    "Explore the current coffee and food offering.",
                    positioning,
                ),
            },
            "/contact": {
                "Visit information": (
                    "Have a question about the menu, the experience or planning a visit? Send a message and the team can help.",
                    f"{site_name} keeps the next step simple for visitors.",
                ),
                "Contact or enquiry action": (
                    "Tell us what you need and we will point you in the right direction.",
                    "Use the form below for a straightforward enquiry.",
                ),
                "Response expectation": (
                    "We will review your message and get back to you as soon as possible.",
                    "For time-sensitive visit details, use the latest contact information provided by the café.",
                ),
                "default": (
                    "Start a conversation with the café.",
                    positioning,
                ),
            },
        }
        return hospitality_copy.get(path, {}).get(section, hospitality_copy.get(path, {}).get("default", (positioning, positioning)))

    generic_copy = {
        "/": {
            "Value proposition": (positioning, f"Built for {audience}.") ,
            "Key benefits": ("Clear value, practical next steps and a focused experience.", positioning),
            "Proof or credibility": ("Make relevant experience, evidence and trust signals easy to understand.", "Approved business information should replace this baseline copy as it becomes available."),
            "Primary conversion section": ("Ready to move forward?", f"Take the next step toward {goal.rstrip('.') }.") ,
        },
        "/about": {
            "Business story": (f"Learn what shapes {site_name}, how it works and what it stands for.", positioning),
            "Approach or differentiators": ("Explain the choices and strengths that make the business distinctive.", "Keep differentiators grounded in approved business information."),
            "Trust signals": ("Make relevant expertise, proof and customer confidence visible.", "Add verified evidence as it becomes available."),
        },
        "/services": {
            "Services overview": ("Explore the core services and the outcomes they are designed to support.", positioning),
            "Service detail and value": ("Explain what each offer includes and why it matters.", "Use concise, scannable descriptions rather than unsupported claims."),
            "Service detail/value": ("Explain what each offer includes and why it matters.", positioning),
            "Conversion section": ("Take the next step", f"Contact the business to discuss {goal.rstrip('.') }.") ,
        },
        "/contact": {
            "Contact context": ("Have a question or ready to discuss your needs? Start a conversation.", positioning),
            "Contact form or action": ("Tell us what you need and we will help with the next step.", "Use the form below for a straightforward enquiry."),
            "Response expectation": ("What happens next", "We will review your message and respond as soon as possible."),
        },
    }
    return generic_copy.get(path, {}).get(section, (positioning, f"Discover more about {site_name}."))


class WebsiteGenerationService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def generate(self, project_id, feedback: str | None = None) -> WebsiteGeneration:
        project = await self.repository.get_project(project_id)
        specification = await self.repository.get_specification(project_id)
        design = await self.repository.get_design(project_id)
        strategy = await self.repository.get_strategy(project_id)
        context = await self.repository.get_context(project_id)
        if not specification:
            raise KeyError("specification")
        if specification.status.value != "approved":
            raise ValueError("Website Specification must be approved before generating a website")
        if not design:
            raise KeyError("design")
        if not strategy:
            raise KeyError("strategy")

        palette = design.color_palette
        primary = "#111111" if "neutral" in palette.primary.lower() else palette.primary
        accent = "#111111" if "high-contrast" in palette.accent.lower() else palette.accent
        background = "#ffffff" if "light" in palette.background.lower() else palette.background
        text = "#151515" if "contrast" in palette.text.lower() else palette.text
        default_positioning = "A clear value proposition for the people this business serves."
        positioning = strategy.content.positioning or default_positioning
        tone = ", ".join(strategy.content.tone) if strategy.content.tone else "clear, credible and human"
        site_name_raw = (
            context.knowledge.business_name.value
            if context and context.knowledge.business_name.value
            else (project.name if project else "AWE Website")
        )
        industry = context.knowledge.industry.value if context else ""
        audience_values = [item.value for item in context.knowledge.audience if item.value] if context else []
        audience = audience_values[0] if audience_values else "prospective customers"
        goals = [item.value for item in context.knowledge.goals if item.value] if context else []
        goal = goals[0] if goals else "take the next step"

        site_name = escape(site_name_raw)
        positioning_html = escape(positioning)
        safe_tone = escape(tone)

        globals_css = f'''*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;color:{text};background:{background};line-height:1.6}}body{{min-height:100vh}}a{{color:inherit;text-decoration:none}}a:focus-visible,button:focus-visible{{outline:3px solid {accent};outline-offset:3px}}main{{max-width:1160px;margin:auto;padding:0 24px}}nav{{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:24px 0;border-bottom:1px solid rgba(0,0,0,.1)}}nav .links{{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}}.hero{{padding:96px 0 80px;max-width:820px}}.eyebrow{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;opacity:.65}}h1,h2,h3{{line-height:1.1;letter-spacing:-.03em}}h1{{font-size:clamp(44px,7vw,76px);margin:18px 0}}h2{{font-size:clamp(30px,4vw,46px)}}section{{padding:72px 0;border-top:1px solid rgba(0,0,0,.1)}}.lead{{font-size:20px;max-width:720px;color:rgba(21,21,21,.72)}}.cta{{display:inline-flex;margin-top:28px;padding:13px 19px;background:{primary};color:#fff;border-radius:9px;font-weight:650}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}}.card{{padding:24px;border:1px solid rgba(0,0,0,.1);border-radius:16px;background:rgba(255,255,255,.65)}}footer{{padding:48px 0;color:rgba(21,21,21,.6);font-size:13px}}.contact-form{{display:grid;gap:10px;max-width:680px}}.contact-form input,.contact-form textarea{{font:inherit;padding:12px;border:1px solid rgba(0,0,0,.2);border-radius:8px;background:#fff}}.contact-form .cta{{border:0;cursor:pointer;width:max-content}}@media(max-width:760px){{nav{{align-items:flex-start;flex-direction:column}}.hero{{padding:64px 0}}section{{padding:52px 0}}.grid{{grid-template-columns:1fr}}}}'''

        files = [
            GeneratedFile(path="package.json", content='''{"name":"awe-generated-site","private":true,"scripts":{"dev":"next dev","build":"next build","start":"next start"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"},"devDependencies":{"typescript":"5.8.2","@types/react":"19.1.10","@types/node":"20.17.6"}}'''),
            GeneratedFile(path="app/layout.tsx", content=f'''import "./globals.css";
import React from "react";

export const metadata = {{
  title: {{
    default: {json.dumps(site_name_raw)},
    template: {json.dumps(f"%s | {site_name_raw}")},
  }},
  description: {json.dumps(positioning)},
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return <html lang="en"><body>{{children}}</body></html>;
}}
'''),
            GeneratedFile(path="app/globals.css", content=globals_css),
            GeneratedFile(path="awe-content.json", content="{}"),
        ]

        nav = "".join(
            f'<a href="{escape(page.path, quote=True)}">{escape(page.name)}</a>'
            for page in specification.pages
        )
        preview_pages: dict[str, str] = {}

        for page in specification.pages:
            filename = "app/page.tsx" if page.path == "/" else f"app{page.path}/page.tsx"
            page_name = escape(page.name)
            hospitality = _is_hospitality(industry, goal)
            objective = escape(_hero_objective(page.path, hospitality, site_name_raw, goal))
            section_blocks: list[str] = []
            for section in page.required_sections:
                heading = _section_heading(section)
                primary_copy, secondary_copy = _page_copy(
                    page.path,
                    section,
                    site_name_raw,
                    positioning,
                    industry,
                    audience,
                    goal,
                )
                section_blocks.append(
                    f'<section><h2>{escape(heading)}</h2>'
                    f'<p className="lead">{escape(primary_copy)}</p>'
                    f'<div className="card"><p>{escape(secondary_copy)}</p></div></section>'
                )
            sections = "".join(section_blocks)
            preview_section_blocks = []
            for section in page.required_sections:
                heading = _section_heading(section)
                primary_copy, secondary_copy = _page_copy(
                    page.path, section, site_name_raw, positioning, industry, audience, goal
                )
                preview_section_blocks.append(
                    f'<section><h2>{escape(heading)}</h2>'
                    f'<p class="lead">{escape(primary_copy)}</p>'
                    f'<div class="card"><p>{escape(secondary_copy)}</p></div></section>'
                )
            preview_sections = "".join(preview_section_blocks)
            cta = (
                f'<a className="cta" href="/contact">{escape(page.primary_cta)}</a>'
                if page.primary_cta
                else ""
            )
            contact_form = ""
            if page.path == "/contact":
                contact_form = '''<section id="contact">
  <h2>Start a conversation</h2>
  <form className="card contact-form" action="/contact" method="get">
    <label htmlFor="name">Name</label>
    <input id="name" name="name" required />
    <label htmlFor="email">Email</label>
    <input id="email" name="email" type="email" required />
    <label htmlFor="message">Message</label>
    <textarea id="message" name="message" rows={5} required />
    <button className="cta" type="submit">Send enquiry</button>
  </form>
  <p className="lead">We’ll review your message and get back to you as soon as possible.</p>
</section>'''
            eyebrow = "Coffee, food and hospitality" if _is_hospitality(industry, goal) else "AWE generated website"
            content = f'''import {{ readFile }} from "node:fs/promises";

export const dynamic = "force-dynamic";

export const metadata = {{ title: {json.dumps(page.name)} }};

async function contentValue(key: string, fallback: string) {{
  try {{
    const raw = await readFile("/workspace/awe-content.json", "utf8");
    const data = JSON.parse(raw) as Record<string, Record<string, string>>;
    return data[{json.dumps(page.path)}]?.[key] || fallback;
  }} catch {{
    return fallback;
  }}
}}

export default async function Page() {{
  const headline = await contentValue("headline", {json.dumps(page.name)});
  const pagePositioning = await contentValue("positioning", {json.dumps(positioning)});
  const editableCta = await contentValue("cta", {json.dumps(page.primary_cta or "")});
  return <main><nav><strong>{site_name}</strong><div className="links">{nav}</div></nav><div className="hero"><span className="eyebrow">{escape(eyebrow)}</span><h1>{{headline}}</h1><p className="lead">{objective}</p><p className="lead">{{pagePositioning}}</p>{{editableCta && <a className="cta" href="/contact">{{editableCta}}</a>}}</div>{sections}{contact_form}<footer>Built from an approved AWE strategy and design · {safe_tone}</footer></main>;
}}
'''
            files.append(GeneratedFile(path=filename, content=content))
            preview_cta = (
                f'<a class="cta" href="/contact">{escape(page.primary_cta)}</a>'
                if page.primary_cta else ""
            )
            preview_contact_form = ""
            if page.path == "/contact":
                preview_contact_form = (
                    '<section id="contact"><h2>Start a conversation</h2>'
                    '<form class="card contact-form" action="/contact" method="get">'
                    '<label for="name">Name</label><input id="name" name="name" required>'
                    '<label for="email">Email</label><input id="email" name="email" type="email" required>'
                    '<label for="message">Message</label><textarea id="message" name="message" rows="5" required></textarea>'
                    '<button class="cta" type="submit">Send enquiry</button></form>'
                    '<p class="lead">We’ll review your message and get back to you as soon as possible.</p></section>'
                )
            preview_eyebrow = "Coffee, food and hospitality" if _is_hospitality(industry, goal) else "AWE generated website"
            preview_pages[page.path] = (
                f'<main><nav><strong>{site_name}</strong><div class="links">{nav}</div></nav>'
                f'<div class="hero"><span class="eyebrow">{escape(preview_eyebrow)}</span><h1>{page_name}</h1>'
                f'<p class="lead">{objective}</p><p class="lead">{positioning_html}</p>{preview_cta}</div>'
                f'{preview_sections}{preview_contact_form}<footer>Built from an approved AWE strategy and design · {safe_tone}</footer></main>'
            )

        preview_home = preview_pages.get("/", next(iter(preview_pages.values()), "<main></main>"))
        preview_html = (
            f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{escape(site_name_raw)}</title><style>{globals_css}</style></head>'
            f'<body>{preview_home}</body></html>'
        )
        files.append(GeneratedFile(path="awe-preview.html", content=preview_html))

        validation = {
            "specification_approved": True,
            "pages_covered": len([f.path for f in files if f.path.endswith("page.tsx")]) == len(specification.pages),
            "required_sections_present": all(page.required_sections for page in specification.pages),
            "design_traceable": specification.source_design_version == design.version,
            "strategy_traceable": specification.source_strategy_version == strategy.version,
            "responsive_foundation": "@media" in globals_css,
            "seo_metadata": "metadata" in files[1].content,
            "business_content_present": bool(
                positioning.strip() != ""
                and (
                    site_name_raw != "AWE Website"
                    or industry.strip()
                    or audience_values
                    or goals
                )
            ),
            "framework": "nextjs-app-router",
        }
        status = WebsiteGenerationStatus.VALIDATED if all(value is True or isinstance(value, str) for value in validation.values()) else WebsiteGenerationStatus.FAILED
        current = await self.repository.get_generation(project_id)
        version = (current.version + 1) if current else 1
        generation = WebsiteGeneration(
            project_id=project_id,
            generation_id=uuid4(),
            version=version,
            source_specification_version=specification.version,
            files=files,
            pages_generated=[page.path for page in specification.pages],
            validation=validation,
            status=status,
            rationale=[
                "Generation consumes only an approved Website Specification.",
                "The generator remains deterministic and template-driven so generated output is reproducible.",
                "Approved strategy and design are reflected in positioning, navigation, responsive styling and visual tokens.",
                "Industry-aware content mapping keeps visitor-facing copy distinct from implementation/specification labels.",
                "The executable MVP avoids inventing unsupported prices, addresses, testimonials or other business facts.",
            ],
        )
        if feedback:
            generation = self._apply_revision_feedback(generation, feedback)
        return await self.repository.create_generation(generation)

    @staticmethod
    def _apply_revision_feedback(generation: WebsiteGeneration, feedback: str) -> WebsiteGeneration:
        """Apply explicit, deterministic mock-refinement instructions.

        Supported syntax is intentionally narrow: ``headline: ...`` and
        ``cta: ...``. Unsupported feedback is retained as rationale without
        silently inventing a design change.
        """
        normalized = feedback.strip()
        files = [item.model_copy(deep=True) for item in generation.files]
        changed = False
        headline_match = re.search(r"headline\s*:\s*(.+)", normalized, re.IGNORECASE)
        cta_match = re.search(r"cta\s*:\s*(.+)", normalized, re.IGNORECASE)
        for item in files:
            if item.path == "app/page.tsx" and headline_match:
                item.content = re.sub(r"<h1>.*?</h1>", f"<h1>{escape(headline_match.group(1).strip())}</h1>", item.content, count=1, flags=re.DOTALL)
                changed = True
            if item.path == "app/page.tsx" and cta_match:
                item.content = re.sub(r"(<a className=\"cta\"[^>]*>).*?(</a>)", lambda m: m.group(1) + escape(cta_match.group(1).strip()) + m.group(2), item.content, count=1, flags=re.DOTALL)
                changed = True
            if item.path == "awe-preview.html" and headline_match:
                item.content = re.sub(r"<h1>.*?</h1>", f"<h1>{escape(headline_match.group(1).strip())}</h1>", item.content, count=1, flags=re.DOTALL)
            if item.path == "awe-preview.html" and cta_match:
                item.content = re.sub(r"(<a class=\"cta\"[^>]*>).*?(</a>)", lambda m: m.group(1) + escape(cta_match.group(1).strip()) + m.group(2), item.content, count=1, flags=re.DOTALL)
        generation.files = files
        generation.rationale.append(f"Customer mock feedback captured: {feedback}")
        if changed:
            generation.rationale.append("Revision applied using deterministic headline/CTA refinement instructions.")
        else:
            generation.rationale.append("Feedback was retained for review; no supported deterministic refinement syntax was detected.")
        return generation

    async def revise(self, project_id, feedback: str) -> WebsiteGeneration:
        return await self.generate(project_id, feedback=feedback)

    async def get(self, project_id):
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError(project_id)
        return generation
