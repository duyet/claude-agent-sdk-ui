import { type NextRequest, NextResponse } from "next/server"

const PUBLIC_ROUTES = ["/login"]
const SESSION_COOKIE = "claude_agent_session"

export async function proxy(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl

  // Skip static files and API routes
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".") // Static files like favicon.ico
  ) {
    return NextResponse.next()
  }

  const sessionCookie = request.cookies.get(SESSION_COOKIE)
  const isAuthenticated = !!sessionCookie?.value
  const isPublicRoute = PUBLIC_ROUTES.includes(pathname)

  // Redirect authenticated users away from login
  if (isAuthenticated && isPublicRoute) {
    return NextResponse.redirect(new URL("/", request.url))
  }

  // Redirect unauthenticated users to login
  if (!isAuthenticated && !isPublicRoute) {
    const loginUrl = new URL("/login", request.url)
    // Preserve the original destination
    if (pathname !== "/") {
      loginUrl.searchParams.set("from", pathname)
    }
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}
