import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest, context: { params: Promise<{ projectId: string; path?: string[] }> }) {
  return proxy(request, context);
}
export async function HEAD(request: NextRequest, context: { params: Promise<{ projectId: string; path?: string[] }> }) {
  return proxy(request, context);
}
export async function POST(request: NextRequest, context: { params: Promise<{ projectId: string; path?: string[] }> }) {
  return proxy(request, context);
}
export async function PUT(request: NextRequest, context: { params: Promise<{ projectId: string; path?: string[] }> }) {
  return proxy(request, context);
}
export async function PATCH(request: NextRequest, context: { params: Promise<{ projectId: string; path?: string[] }> }) {
  return proxy(request, context);
}
export async function DELETE(request: NextRequest, context: { params: Promise<{ projectId: string; path?: string[] }> }) {
  return proxy(request, context);
}
export async function OPTIONS(request: NextRequest, context: { params: Promise<{ projectId: string; path?: string[] }> }) {
  return proxy(request, context);
}

async function proxy(request: NextRequest, context: { params: Promise<{ projectId: string; path?: string[] }> }) {
  const { projectId, path = [] } = await context.params;
  const apiBase = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://api:8000";
  const suffix = path.join("/");
  const target = `${apiBase}/api/v1/website-preview/preview-proxy/${projectId}/${suffix}${request.nextUrl.search}`;
  try {
    const headers = new Headers(request.headers);
    headers.set("X-AWE-Preview-Proxy", process.env.AWE_INTERNAL_PREVIEW_SECRET || "dev-preview-proxy");
    headers.delete("host");
    const response = await fetch(target, { method: request.method, headers, body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(), redirect: "manual" });
    const out = new Headers(response.headers);
    out.delete("content-encoding");
    out.delete("content-length");
    out.delete("transfer-encoding");
    out.delete("connection");
    out.delete("x-frame-options");
    out.delete("content-security-policy");
    out.set("cache-control", "no-store, no-cache, must-revalidate");
    const location = out.get("location");
    if (location) {
      try {
        const absolute = new URL(location, target);
        const apiUrl = new URL(target);
        if (absolute.hostname === apiUrl.hostname && absolute.port === apiUrl.port) {
          const proxied = absolute.pathname.replace(`/api/v1/website-preview/preview-proxy/${projectId}`, `/api/live-preview/preview/${projectId}`);
          out.set("location", `${proxied}${absolute.search}`);
        }
      } catch {}
    }
    return new NextResponse(response.body, { status: response.status, headers: out });
  } catch (error) {
    return NextResponse.json({ error: "Live preview runtime is unreachable.", detail: String(error) }, { status: 502 });
  }
}
