import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasApiKey = request.cookies.has("pm_api_key");

  // Auth pages: redirect to console if already logged in
  if (pathname === "/login" || pathname === "/register") {
    if (hasApiKey) {
      return NextResponse.redirect(new URL("/console", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/console/:path*", "/login", "/register"],
};
