import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

// Routes that require authentication.
const PROTECTED_PREFIXES = ["/chat", "/profile", "/admin"]
// Auth routes that an authenticated user should be bounced away from.
const AUTH_ROUTES = ["/login", "/register"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const hasToken = Boolean(request.cookies.get("access_token")?.value)

  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  )
  const isAuthRoute = AUTH_ROUTES.includes(pathname)

  // Unauthenticated users cannot access protected routes.
  if (isProtected && !hasToken) {
    const loginUrl = new URL("/login", request.url)
    loginUrl.searchParams.set("from", pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Authenticated users shouldn't see login/register.
  if (isAuthRoute && hasToken) {
    return NextResponse.redirect(new URL("/chat", request.url))
  }

  // Send the bare root to the right place.
  if (pathname === "/") {
    return NextResponse.redirect(new URL(hasToken ? "/chat" : "/login", request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    "/",
    "/login",
    "/register",
    "/chat/:path*",
    "/profile/:path*",
    "/admin/:path*",
  ],
}
