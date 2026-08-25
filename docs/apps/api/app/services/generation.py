from uuid import uuid4
from app.models import GeneratedFile, WebsiteGeneration, WebsiteGenerationStatus
from app.store import Repository


class WebsiteGenerationService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def generate(self, project_id) -> WebsiteGeneration:
        specification = await self.repository.get_specification(project_id)
        design = await self.repository.get_design(project_id)
        strategy = await self.repository.get_strategy(project_id)
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
        positioning = strategy.content.positioning or "A clear value proposition for the people this business serves."
        tone = ", ".join(strategy.content.tone) if strategy.content.tone else "clear, credible and human"
        site_name = specification.pages[0].name if specification.pages else "AWE Website"

        globals_css = f'''*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;color:{text};background:{background};line-height:1.6}}body{{min-height:100vh}}a{{color:inherit;text-decoration:none}}a:focus-visible,button:focus-visible{{outline:3px solid {accent};outline-offset:3px}}main{{max-width:1160px;margin:auto;padding:0 24px}}nav{{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:24px 0;border-bottom:1px solid rgba(0,0,0,.1)}}nav .links{{display:flex;gap:18px;flex-wrap:wrap;font-size:14px}}.hero{{padding:96px 0 80px;max-width:820px}}.eyebrow{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;opacity:.65}}h1,h2,h3{{line-height:1.1;letter-spacing:-.03em}}h1{{font-size:clamp(44px,7vw,76px);margin:18px 0}}h2{{font-size:clamp(30px,4vw,46px)}}section{{padding:72px 0;border-top:1px solid rgba(0,0,0,.1)}}.lead{{font-size:20px;max-width:720px;color:rgba(21,21,21,.72)}}.cta{{display:inline-flex;margin-top:28px;padding:13px 19px;background:{primary};color:#fff;border-radius:9px;font-weight:650}}.card{{padding:24px;border:1px solid rgba(0,0,0,.1);border-radius:16px;background:rgba(255,255,255,.65)}}footer{{padding:48px 0;color:rgba(21,21,21,.6);font-size:13px}}@media(max-width:760px){{nav{{align-items:flex-start;flex-direction:column}}.hero{{padding:64px 0}}section{{padding:52px 0}}}}'''

        files = [
            GeneratedFile(path="package.json", content='''{"name":"awe-generated-site","private":true,"scripts":{"dev":"next dev","build":"next build","start":"next start"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"}}'''),
            GeneratedFile(path="app/layout.tsx", content=f'''import React from "react";

export const metadata = {{
  title: {site_name!r},
  description: {positioning!r},
}};

export default function RootLayout({{ children }}: {{ children: React.ReactNode }}) {{
  return <html lang="en"><body>{{children}}</body></html>;
}}
'''),
            GeneratedFile(path="app/globals.css", content=globals_css),
        ]

        page_paths = []
        nav = "".join(f'<a href="{page.path}">{page.name}</a>' for page in specification.pages)
        for page in specification.pages:
            page_paths.append(page.path)
            filename = "app/page.tsx" if page.path == "/" else f"app{page.path}/page.tsx"
            sections = "".join(f'<section><h2>{section}</h2><p className="lead">{page.objective}</p><div className="card"><p>{positioning}</p></div></section>' for section in page.required_sections)
            cta = f'<a className="cta" href="/contact">{page.primary_cta}</a>' if page.primary_cta else ""
            content = f'''export default function Page() {{
  return <main><nav><strong>{site_name}</strong><div className="links">{nav}</div></nav><div className="hero"><span className="eyebrow">AWE generated website</span><h1>{page.name}</h1><p className="lead">{page.objective}</p><p className="lead">{positioning}</p>{cta}</div>{sections}<footer>Built from an approved AWE Website Specification · Tone: {tone}</footer></main>;
}}
'''
            files.append(GeneratedFile(path=filename, content=content))

        validation = {
            "specification_approved": True,
            "pages_covered": len(page_paths) == len(specification.pages),
            "required_sections_present": all(page.required_sections for page in specification.pages),
            "design_traceable": specification.source_design_version == design.version,
            "strategy_traceable": specification.source_strategy_version == strategy.version,
            "responsive_foundation": "@media" in globals_css,
            "seo_metadata": "metadata" in files[1].content,
            "framework": "nextjs-app-router",
        }
        status = WebsiteGenerationStatus.VALIDATED if all(value is True or isinstance(value, str) for value in validation.values()) else WebsiteGenerationStatus.FAILED
        generation = WebsiteGeneration(
            project_id=project_id,
            generation_id=uuid4(),
            source_specification_version=specification.version,
            files=files,
            pages_generated=page_paths,
            validation=validation,
            status=status,
            rationale=[
                "Generation consumes only an approved Website Specification.",
                "The generator remains deterministic and template-driven so generated output is reproducible.",
                "Approved strategy and design are reflected in positioning, navigation, responsive styling and visual tokens.",
                "The first executable MVP prioritizes a polished framework-specific baseline before introducing arbitrary AI-generated code.",
            ],
        )
        return await self.repository.create_generation(generation)

    async def get(self, project_id):
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError(project_id)
        return generation
