import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const page = readFileSync(resolve(root, "app/page.tsx"), "utf8");
const currentRoute = readFileSync(resolve(root, "app/api/live/[projectId]/[[...path]]/route.ts"), "utf8");
const pinnedRoute = readFileSync(resolve(root, "app/api/live/[projectId]/deployment/[deploymentId]/[[...path]]/route.ts"), "utf8");
const compatRoute = readFileSync(resolve(root, "app/api/live-preview/deployment/[projectId]/[[...path]]/route.ts"), "utf8");

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

assert(page.includes("`/api/live/${projectId}/`"), "Studio must emit the canonical stable current URL");
assert(page.includes("`/api/live/${projectId}/deployment/${encodeURIComponent(deploymentId)}/`"), "Studio must emit deployment-pinned stable URLs");
assert(!page.includes("return `/api/live-preview/deployment/${projectId}/${suffix}`"), "Studio live links must not be generated through the legacy FIX-31 namespace");
assert(currentRoute.includes("/api/v1/website-preview/live-proxy/"), "Stable current route must delegate to canonical live-proxy API");
assert(pinnedRoute.includes('query.set("deployment_id", deploymentId)'), "Pinned stable route must propagate deployment_id");
assert(pinnedRoute.includes("/api/v1/website-preview/live-proxy/"), "Pinned stable route must delegate to canonical live-proxy API");
assert(compatRoute.includes("/api/v1/website-preview/deployment-proxy/"), "Legacy live-preview compatibility route must remain mapped to deployment-proxy");

console.log("CAP-038.1 Studio routing contract: PASS");
