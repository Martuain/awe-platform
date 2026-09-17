import { NextRequest, NextResponse } from "next/server";

async function handle(request: NextRequest, context: { params: Promise<{ port: string; path?: string[] }> }) {
  const { port, path = [] } = await context.params;
  if (!/^\d{4,5}$/.test(port)) return new NextResponse("Invalid preview target", { status: 400 });
  const suffix = path.map((segment) => encodeURIComponent(segment)).join("/");
  // Keep the browser same-origin with Studio. Studio forwards through the API,
  // which reaches the disposable runtime on the private Docker network.
  const apiBase = process.env.INTERNAL_API_URL || "http://api:8000";
  const target = `${apiBase}/api/v1/website-preview/proxy/${port}/${suffix}${request.nextUrl.search}`;
  try {
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.delete("connection");
    headers.set("X-AWE-Preview-Proxy", process.env.AWE_INTERNAL_PREVIEW_SECRET || "dev-preview-proxy");
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(),
      redirect: "manual",
      cache: "no-store",
      signal: AbortSignal.timeout(30000),
    });
    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.delete("content-length");
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-security-policy");
    responseHeaders.delete("x-frame-options");
    return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch (error) {
    return NextResponse.json({ error: "Live preview runtime is unreachable.", detail: String(error) }, { status: 502 });
  }
}
export const GET = handle; export const HEAD = handle; export const POST = handle; export const PUT = handle; export const PATCH = handle; export const DELETE = handle; export const OPTIONS = handle;
