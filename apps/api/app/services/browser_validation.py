from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from uuid import UUID

from app.services.preview import WebsitePreviewService
from app.store import Repository


BROWSER_IMAGE = os.getenv("AWE_BROWSER_IMAGE", "mcr.microsoft.com/playwright:v1.55.0-noble")
BROWSER_TIMEOUT_SECONDS = 180


class BrowserValidationService:
    """Runs a disposable Chromium audit against the active local preview."""

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    async def check(self, project_id: UUID) -> dict:
        generation = await self.repository.get_generation(project_id)
        if not generation:
            raise KeyError(project_id)

        container_id = WebsitePreviewService._runtime_for_project(project_id)
        if not container_id:
            return {
                "project_id": str(project_id),
                "generation_version": generation.version,
                "status": "unavailable",
                "diagnostics": ["Start a validated disposable live preview before running browser validation."],
                "browser": "chromium",
                "url": None,
                "metrics": {},
                "checks": [],
            }

        port_result = subprocess.run(
            ["docker", "port", container_id, "3000/tcp"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        mapping = port_result.stdout.strip().splitlines()[0] if port_result.stdout.strip() else ""
        host_port = mapping.rsplit(":", 1)[-1] if mapping else ""
        if not host_port.isdigit():
            return {
                "project_id": str(project_id),
                "generation_version": generation.version,
                "status": "unavailable",
                "diagnostics": ["Active preview runtime has no published host port."],
                "browser": "chromium",
                "url": None,
                "metrics": {},
                "checks": [],
            }
        preview_url = f"http://127.0.0.1:{host_port}"

        if shutil.which("docker") is None:
            return {
                "project_id": str(project_id),
                "generation_version": generation.version,
                "status": "unavailable",
                "diagnostics": ["Docker is required for browser validation."],
                "browser": "chromium",
                "url": preview_url,
                "metrics": {},
                "checks": [],
            }

        return await asyncio.to_thread(self._run, project_id, generation.version, preview_url, container_id)

    @staticmethod
    def _run(project_id: UUID, generation_version: int, url: str, container_id: str) -> dict:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host_port = parsed.port
        if not host_port:
            return {
                "project_id": str(project_id),
                "generation_version": generation_version,
                "status": "failed",
                "diagnostics": ["Live preview URL does not contain a published host port."],
                "browser": "chromium",
                "url": url,
                "metrics": {},
                "checks": [],
            }
        target = f"http://host.docker.internal:{host_port}"
        command = [
            "docker", "run", "--rm",
            "--add-host", "host.docker.internal:host-gateway",
            "--cpus", "1", "--memory", "1g", "--pids-limit", "128",
            "-e", f"AWE_BROWSER_TARGET={target}",
            "-e", "AWE_BROWSER_SCRIPT=Y29uc3QgeyBjaHJvbWl1bSB9ID0gcmVxdWlyZSgicGxheXdyaWdodCIpOwpjb25zdCB0YXJnZXQgPSBwcm9jZXNzLmVudi5BV0VfQlJPV1NFUl9UQVJHRVQ7Cihhc3luYyAoKSA9PiB7CiAgY29uc3QgYnJvd3NlciA9IGF3YWl0IGNocm9taXVtLmxhdW5jaCh7IGhlYWRsZXNzOiB0cnVlLCBhcmdzOiBbIi0tbm8tc2FuZGJveCIsICItLWRpc2FibGUtZGV2LXNobS11c2FnZSJdIH0pOwogIGNvbnN0IHBhZ2UgPSBhd2FpdCBicm93c2VyLm5ld1BhZ2UoeyB2aWV3cG9ydDogeyB3aWR0aDogMTM2NSwgaGVpZ2h0OiA3NjggfSB9KTsKICBhd2FpdCBwYWdlLmFkZEluaXRTY3JpcHQoKCkgPT4gewogICAgd2luZG93Ll9fYXdlVml0YWxzID0geyBsY3A6IG51bGwsIGNsczogMCwgaW5wOiBudWxsIH07CiAgICBjb25zdCBzdGF0ZSA9IHdpbmRvdy5fX2F3ZVZpdGFsczsKICAgIHRyeSB7IG5ldyBQZXJmb3JtYW5jZU9ic2VydmVyKGxpc3QgPT4geyBjb25zdCBlbnRyaWVzID0gbGlzdC5nZXRFbnRyaWVzKCk7IGNvbnN0IGxhc3QgPSBlbnRyaWVzW2VudHJpZXMubGVuZ3RoIC0gMV07IGlmIChsYXN0KSBzdGF0ZS5sY3AgPSBsYXN0LnN0YXJ0VGltZTsgfSkub2JzZXJ2ZSh7IHR5cGU6ICJsYXJnZXN0LWNvbnRlbnRmdWwtcGFpbnQiLCBidWZmZXJlZDogdHJ1ZSB9KTsgfSBjYXRjaCB7fQogICAgdHJ5IHsgbmV3IFBlcmZvcm1hbmNlT2JzZXJ2ZXIobGlzdCA9PiB7IGZvciAoY29uc3QgZW50cnkgb2YgbGlzdC5nZXRFbnRyaWVzKCkpIHsgaWYgKCFlbnRyeS5oYWRSZWNlbnRJbnB1dCkgc3RhdGUuY2xzICs9IGVudHJ5LnZhbHVlOyB9IH0pLm9ic2VydmUoeyB0eXBlOiAibGF5b3V0LXNoaWZ0IiwgYnVmZmVyZWQ6IHRydWUgfSk7IH0gY2F0Y2gge30KICAgIHRyeSB7IG5ldyBQZXJmb3JtYW5jZU9ic2VydmVyKGxpc3QgPT4geyBmb3IgKGNvbnN0IGVudHJ5IG9mIGxpc3QuZ2V0RW50cmllcygpKSBzdGF0ZS5pbnAgPSBNYXRoLm1heChzdGF0ZS5pbnAgfHwgMCwgZW50cnkuZHVyYXRpb24pOyB9KS5vYnNlcnZlKHsgdHlwZTogImV2ZW50IiwgYnVmZmVyZWQ6IHRydWUsIGR1cmF0aW9uVGhyZXNob2xkOiA0MCB9KTsgfSBjYXRjaCB7fQogIH0pOwogIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgcGFnZS5nb3RvKHRhcmdldCwgeyB3YWl0VW50aWw6ICJsb2FkIiwgdGltZW91dDogMzAwMDAgfSk7CiAgYXdhaXQgcGFnZS53YWl0Rm9yVGltZW91dCgxMDAwKTsKICBjb25zdCBtZXRyaWNzID0gYXdhaXQgcGFnZS5ldmFsdWF0ZSgoKSA9PiB7CiAgICBjb25zdCBuYXYgPSBwZXJmb3JtYW5jZS5nZXRFbnRyaWVzQnlUeXBlKCJuYXZpZ2F0aW9uIilbMF07CiAgICBjb25zdCBwYWludCA9IHBlcmZvcm1hbmNlLmdldEVudHJpZXNCeU5hbWUoImZpcnN0LWNvbnRlbnRmdWwtcGFpbnQiKVswXTsKICAgIHJldHVybiB7IGxjcF9tczogd2luZG93Ll9fYXdlVml0YWxzLmxjcCwgY2xzOiBOdW1iZXIod2luZG93Ll9fYXdlVml0YWxzLmNscy50b0ZpeGVkKDQpKSwgaW5wX21zOiB3aW5kb3cuX19hd2VWaXRhbHMuaW5wLCBmY3BfbXM6IHBhaW50ID8gcGFpbnQuc3RhcnRUaW1lIDogbnVsbCwgdHRmYl9tczogbmF2ID8gbmF2LnJlc3BvbnNlU3RhcnQgLSBuYXYucmVxdWVzdFN0YXJ0IDogbnVsbCwgZG9tX2NvbnRlbnRfbG9hZGVkX21zOiBuYXYgPyBuYXYuZG9tQ29udGVudExvYWRlZEV2ZW50RW5kIC0gbmF2LnN0YXJ0VGltZSA6IG51bGwsIGxvYWRfbXM6IG5hdiA/IG5hdi5sb2FkRXZlbnRFbmQgLSBuYXYuc3RhcnRUaW1lIDogbnVsbCwgdGl0bGU6IGRvY3VtZW50LnRpdGxlLCBsaW5rczogZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbCgiYSIpLmxlbmd0aCB9OwogIH0pOwogIGNvbnNvbGUubG9nKEpTT04uc3RyaW5naWZ5KHsgaHR0cF9zdGF0dXM6IHJlc3BvbnNlID8gcmVzcG9uc2Uuc3RhdHVzKCkgOiBudWxsLCBtZXRyaWNzIH0pKTsKICBhd2FpdCBicm93c2VyLmNsb3NlKCk7Cn0pKCkuY2F0Y2goZXJyb3IgPT4geyBjb25zb2xlLmVycm9yKGVycm9yICYmIGVycm9yLnN0YWNrID8gZXJyb3Iuc3RhY2sgOiBTdHJpbmcoZXJyb3IpKTsgcHJvY2Vzcy5leGl0KDEpOyB9KTsK",
            BROWSER_IMAGE,
            "sh", "-lc",
            "npm install --ignore-scripts --no-audit --no-fund --prefix /tmp/awe-browser playwright@1.55.0 >/dev/null 2>&1 && NODE_PATH=/tmp/awe-browser/node_modules node -e 'require(\"node:vm\").runInThisContext(Buffer.from(process.env.AWE_BROWSER_SCRIPT, \"base64\").toString(\"utf8\"))'",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=BROWSER_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "project_id": str(project_id),
                "generation_version": generation_version,
                "status": "failed",
                "diagnostics": [f"Browser validation timed out after {BROWSER_TIMEOUT_SECONDS} seconds."],
                "browser": "chromium",
                "url": url,
                "metrics": {},
                "checks": [],
            }
        if result.returncode != 0:
            return {
                "project_id": str(project_id),
                "generation_version": generation_version,
                "status": "failed",
                "diagnostics": [result.stderr[-4000:] or "Browser validation failed."],
                "browser": "chromium",
                "url": url,
                "metrics": {},
                "checks": [],
            }

        try:
            payload = json.loads(result.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return {
                "project_id": str(project_id),
                "generation_version": generation_version,
                "status": "failed",
                "diagnostics": ["Browser validation returned an unreadable result."],
                "browser": "chromium",
                "url": url,
                "metrics": {},
                "checks": [],
            }

        metrics = payload.get("metrics", {})
        thresholds = {
            "fcp_ms": (1800, "First Contentful Paint"),
            "lcp_ms": (2500, "Largest Contentful Paint"),
            "inp_ms": (200, "Interaction to Next Paint"),
            "cls": (0.1, "Cumulative Layout Shift"),
            "ttfb_ms": (800, "Time to First Byte"),
        }
        checks = []
        diagnostics = []
        for key, (limit, label) in thresholds.items():
            value = metrics.get(key)
            if value is None:
                checks.append({"name": label, "status": "warning", "detail": "Metric unavailable in this browser run."})
                continue
            passed = value <= limit
            unit = "ms" if key.endswith("_ms") else ""
            checks.append({"name": label, "status": "passed" if passed else "warning", "detail": f"{value:.1f}{unit} (budget {limit}{unit})"})
            if not passed:
                diagnostics.append(f"{label} exceeded its budget.")
        if payload.get("http_status") != 200:
            diagnostics.append(f"Preview returned HTTP {payload.get('http_status')}.")

        return {
            "project_id": str(project_id),
            "generation_version": generation_version,
            "status": "passed" if not diagnostics and all(c["status"] == "passed" for c in checks) else "warning",
            "diagnostics": diagnostics,
            "browser": "chromium",
            "url": url,
            "http_status": payload.get("http_status"),
            "metrics": metrics,
            "checks": checks,
        }
