from html import escape
import re
from uuid import UUID, uuid4

from app.models import WebsiteValidation, WebsiteValidationStatus, WebsiteExecutionState
from app.store import Repository


class WebsiteValidationService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def validate(self, project_id: UUID) -> WebsiteValidation:
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError(project_id)

        files = {item.path: item.content for item in generation.files}
        page_files = [
            path
            for path in files
            if path == "app/page.tsx"
            or (path.startswith("app/") and path.endswith("/page.tsx"))
        ]
        checks = {
            "generation_present": bool(generation.files),
            "package_manifest_present": "package.json" in files,
            "root_layout_present": "app/layout.tsx" in files,
            "global_styles_present": "app/globals.css" in files,
            "pages_generated": len(generation.pages_generated) > 0,
            "page_files_present": len(page_files) == len(generation.pages_generated),
            "tsx_exports_present": all(re.search(r"export default (?:async )?function Page", files[path]) is not None for path in page_files),
        }
        diagnostics = []
        if not checks["package_manifest_present"]:
            diagnostics.append("Generated project is missing package.json.")
        if not checks["root_layout_present"]:
            diagnostics.append("Generated project is missing app/layout.tsx.")
        if not checks["global_styles_present"]:
            diagnostics.append("Generated project is missing app/globals.css.")
        if not checks["page_files_present"]:
            diagnostics.append("Generated page count does not match the generated sitemap.")
        if not checks["tsx_exports_present"]:
            diagnostics.append("One or more generated page files do not contain a default Page export.")

        passed = all(checks.values())
        preview = self._build_preview(generation, files)
        result = WebsiteValidation(
            project_id=project_id,
            validation_id=uuid4(),
            generation_version=generation.version,
            status=WebsiteValidationStatus.PASSED if passed else WebsiteValidationStatus.FAILED,
            checks=checks,
            diagnostics=diagnostics,
            preview=preview,
        )
        prior = await self.repository.get_execution_state(project_id) or WebsiteExecutionState(project_id=project_id)
        await self.repository.save_execution_state(prior.model_copy(update={
            "generation_version": generation.version,
            "validation_status": result.status.value,
            "validation": result,
        }, deep=True))
        return result

    @staticmethod
    def _build_preview(generation, files: dict[str, str]) -> dict[str, str]:
        canonical = files.get("awe-preview.html")
        if canonical:
            return {"format": "html", "title": _extract_title(canonical), "html": canonical}

        # Backward-compatible fallback for generations created before the
        # canonical preview artifact existed.
        pages = generation.pages_generated or ["/"]
        title = "AWE Generated Website"
        home_file = files.get("app/page.tsx", "")
        if '<h1>' in home_file:
            raw = home_file.split('<h1>', 1)[1].split('</h1>', 1)[0]
            title = raw or title
        nav = "".join(f'<a href="{escape(path)}">{escape(path or "/")}</a>' for path in pages)
        body = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title><style>body{{margin:0;font-family:system-ui,sans-serif;color:#151515;background:#fff}}main{{max-width:960px;margin:auto;padding:48px 24px}}nav{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:64px}}a{{color:inherit;text-decoration:none}}.hero{{padding:48px 0}}.cta{{display:inline-block;padding:12px 18px;background:#111;color:#fff;border-radius:8px}}section{{padding:40px 0;border-top:1px solid #eee}}</style></head><body><main><nav>{nav}</nav><div class="hero"><p>AWE generated website</p><h1>{escape(title)}</h1><p>CAP-006 preview rendered from the generated website artifact.</p><a class="cta" href="#pages">Explore pages</a></div><section id="pages"><h2>Generated pages</h2><ul>{''.join(f'<li><a href="{escape(path)}">{escape(path)}</a></li>' for path in pages)}</ul></section></main></body></html>"""
        return {"format": "html", "title": title, "html": body}


def _extract_title(html: str) -> str:
    if "<title>" in html and "</title>" in html:
        return html.split("<title>", 1)[1].split("</title>", 1)[0]
    return "AWE Website Mock"
