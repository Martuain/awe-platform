import { NextRequest, NextResponse } from "next/server";

async function handle(
  request: NextRequest,
  context: { params: Promise<{ projectId: string; path?: string[] }> },
) {
  const { projectId, path = [] } = await context.params;
  if (!/^[0-9a-fA-F-]{36}$/.test(projectId)) {
    return new NextResponse("Invalid project target", { status: 400 });
  }

  const suffix = path.map((segment) => encodeURIComponent(segment)).join("/");
  const apiBase = process.env.INTERNAL_API_URL || "http://api:8000";
  const target = `${apiBase}/api/v1/website-preview/deployment-proxy/${projectId}/${suffix}${request.nextUrl.search}`;

  try {
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.delete("connection");
    headers.set(
      "X-AWE-Preview-Proxy",
      process.env.AWE_INTERNAL_PREVIEW_SECRET || "dev-preview-proxy",
    );
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(),
      redirect: "manual",
      cache: "no-store",
      signal: AbortSignal.timeout(120000),
    });
    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.delete("content-length");
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-security-policy");
    responseHeaders.delete("x-frame-options");
    return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch (error) {
    return NextResponse.json(
      { error: "Latest deployed website is unreachable.", detail: String(error) },
      { status: 502 },
    );
  }
}

export const GET = handle;
export const HEAD = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const OPTIONS = handle;
