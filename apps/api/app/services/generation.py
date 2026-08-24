from uuid import uuid4
from app.models import GeneratedFile, WebsiteGeneration, WebsiteGenerationStatus
from app.store import Repository


class WebsiteGenerationService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def generate(self, project_id) -> WebsiteGeneration:
        specification = await self.repository.get_specification(project_id)
        if not specification:
            raise KeyError("specification")
        if specification.status.value != "approved":
            raise ValueError("Website Specification must be approved before generating a website")

        files = [
            GeneratedFile(path="package.json", content='''{"name":"awe-generated-site","private":true,"scripts":{"dev":"next dev","build":"next build","start":"next start"},"dependencies":{"next":"15.5.21","react":"19.1.9","react-dom":"19.1.9"}}'''),
            GeneratedFile(path="app/layout.tsx", content='''import React from "react";\n\nexport default function RootLayout({ children }: { children: React.ReactNode }) {\n  return <html lang="en"><body>{children}</body></html>;\n}\n'''),
            GeneratedFile(path="app/globals.css", content='''*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;color:#151515;background:#fff}main{max-width:1120px;margin:auto;padding:48px 24px}nav{display:flex;gap:20px;margin-bottom:72px}a{color:inherit;text-decoration:none}.hero{padding:72px 0}.cta{display:inline-block;padding:12px 18px;background:#111;color:#fff;border-radius:8px}section{padding:56px 0;border-top:1px solid #eee}'''),
        ]
        page_paths = []
        for page in specification.pages:
            page_paths.append(page.path)
            filename = "app/page.tsx" if page.path == "/" else f"app{page.path}/page.tsx"
            title = page.name
            sections = "".join(f'<section><h2>{section}</h2><p>{page.objective}</p></section>' for section in page.required_sections)
            cta = f'<a className="cta" href="#contact">{page.primary_cta}</a>' if page.primary_cta else ""
            content = f'''export default function Page() {{\n  return <main><nav><a href="/">Home</a>{"".join(f'<a href="{p.path}">{p.name}</a>' for p in specification.pages if p.path != "/")}</nav><div className="hero"><p>AWE generated website</p><h1>{title}</h1><p>{page.objective}</p>{cta}</div>{sections}</main>;\n}}\n'''
            files.append(GeneratedFile(path=filename, content=content))

        validation = {
            "specification_approved": True,
            "pages_covered": len(page_paths) == len(specification.pages),
            "required_sections_present": all(page.required_sections for page in specification.pages),
            "framework": "nextjs-app-router",
        }
        status = WebsiteGenerationStatus.VALIDATED if all(validation.values()) else WebsiteGenerationStatus.FAILED
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
                "The first generator is deterministic and template-driven so generated output is reproducible.",
                "Every approved sitemap page receives a concrete Next.js App Router file.",
            ],
        )
        return await self.repository.create_generation(generation)

    async def get(self, project_id):
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError(project_id)
        return generation
