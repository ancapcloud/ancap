import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
// Fixed backend URL: user input can never become an open redirect target.
export function GET(_request: NextRequest) {
  const response = NextResponse.redirect(new URL("https://api.ancap.cloud/v1/qr/street"), 307);
  response.headers.set("Cache-Control", "no-store, max-age=0");
  response.headers.set("X-Robots-Tag", "noindex, nofollow");
  return response;
}
export const HEAD = GET;
