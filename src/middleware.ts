import { NextRequest, NextResponse } from "next/server";
import { authFromRequest } from "@/lib/auth";

const ADMIN_ROUTES = ["/food/admin", "/food/kitchen", "/food/stats", "/food/history", "/food/qr"];
const PUBLIC_ROUTES = ["/food", "/food/login", "/food/m"];

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // Public routes — no auth needed
  if (PUBLIC_ROUTES.some((r) => pathname === r || pathname.startsWith(r + "/"))) {
    // Except /food/admin, /food/kitchen etc. which also start with /food
    if (!ADMIN_ROUTES.some((r) => pathname === r || pathname.startsWith(r + "/"))) {
      return NextResponse.next();
    }
  }

  // API routes — check per route
  if (pathname.startsWith("/food/api/")) {
    const publicApis = ["/food/api/status", "/food/api/register", "/food/api/menu/data", "/food/api/rfid-scan", "/food/api/stats"];
    if (publicApis.some((r) => pathname === r || pathname.startsWith(r + "/"))) {
      return NextResponse.next();
    }
  }

  // Admin routes — check auth
  if (ADMIN_ROUTES.some((r) => pathname === r || pathname.startsWith(r + "/"))) {
    const auth = await authFromRequest(req);
    const sessionToken = req.cookies.get("food_session")?.value;

    if (!auth && !sessionToken) {
      return NextResponse.redirect(new URL("/food/login", req.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/food/:path*"],
};
