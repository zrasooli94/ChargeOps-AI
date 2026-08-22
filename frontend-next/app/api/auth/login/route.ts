import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const { email, password } = await request.json();
  const backend = process.env.CHARGEOPS_API_URL;
  if (!backend) {
    return NextResponse.json({ detail: "CHARGEOPS_API_URL is not configured." }, { status: 500 });
  }

  const body = new URLSearchParams({ username: email, password });
  const response = await fetch(`${backend}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    cache: "no-store",
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok || !payload.access_token) {
    return NextResponse.json(
      { detail: payload.detail ?? "Incorrect email or password." },
      { status: response.status || 401 },
    );
  }

  const cookieStore = await cookies();
  cookieStore.set("chargeops_token", payload.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 8,
  });

  return NextResponse.json({ ok: true });
}
