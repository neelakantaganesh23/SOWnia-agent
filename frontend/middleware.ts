import { NextRequest, NextResponse } from "next/server";

/**
 * Route protection. This checks only for the PRESENCE of the access_token
 * cookie, not its validity - verifying the JWT signature here would
 * duplicate backend logic and require the signing secret in the edge
 * runtime. A stale/expired cookie still passes this gate but yields a 401
 * from the API on the first real request, which lib/api.ts's response
 * interceptor turns into a redirect to /login.
 */
export function middleware(request: NextRequest) {
  const hasSession = request.cookies.has("access_token");

  if (!hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Protect everything except: /login, /signup, Next internals,
     * static assets, and API routes (auth itself is enforced by FastAPI).
     */
    "/((?!login|signup|api|_next/static|_next/image|favicon.ico).*)",
  ],
};
