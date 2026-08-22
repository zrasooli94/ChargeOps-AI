import { cookies } from "next/headers";
import { NextResponse } from "next/server";

type Context = { params: Promise<{ path: string[] }> };

async function forward(request: Request, context: Context) {
  const backend = process.env.CHARGEOPS_API_URL;
  if (!backend) {
    return NextResponse.json({ detail: "CHARGEOPS_API_URL is not configured." }, { status: 500 });
  }

  const cookieStore = await cookies();
  const token = cookieStore.get("chargeops_token")?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { path } = await context.params;
  const sourceUrl = new URL(request.url);
  const upstreamUrl = `${backend}/${path.join("/")}${sourceUrl.search}`;
  const headers = new Headers(request.headers);
  ["host", "cookie", "content-length", "connection"].forEach((name) => headers.delete(name));
  headers.set("Authorization", `Bearer ${token}`);

  const method = request.method;
  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();
  const upstream = await fetch(upstreamUrl, {
    method,
    headers,
    body,
    cache: "no-store",
  });

  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("transfer-encoding");

  const response = new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
  if (upstream.status === 401) response.cookies.delete("chargeops_token");
  return response;
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const PUT = forward;
export const DELETE = forward;
