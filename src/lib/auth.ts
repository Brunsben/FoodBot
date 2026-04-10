import { jwtVerify } from "jose";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "crypto";

const JWT_SECRET = process.env.JWT_SECRET || "";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "";

export interface AuthSession {
  userId: number;
  username: string;
  role: string;
  foodRolle?: string;
  isPortalUser: boolean;
}

/**
 * Verify JWT from fw_jwt cookie.
 * Returns null if no valid token found.
 */
export async function verifyAuth(): Promise<AuthSession | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get("fw_jwt")?.value;
  if (!token || !JWT_SECRET) return null;

  try {
    const secret = new TextEncoder().encode(JWT_SECRET);
    const { payload } = await jwtVerify(token, secret, { algorithms: ["HS256"] });

    const foodRolle = (payload.food_rolle as string) || "";
    const appRole = (payload.app_role as string) || "";

    // Only users with food_rolle 'Admin' or app_role 'Admin' can access admin
    const isAdmin = foodRolle === "Admin" || appRole === "Admin";
    if (!isAdmin) return null;

    return {
      userId: (payload.benutzer_id as number) || 0,
      username: (payload.benutzername as string) || "",
      role: "admin",
      foodRolle,
      isPortalUser: true,
    };
  } catch {
    return null;
  }
}

/**
 * Password-based login for admin access.
 */
export function verifyPassword(password: string): boolean {
  if (!ADMIN_PASSWORD || !password) return false;
  try {
    const a = Buffer.from(password);
    const b = Buffer.from(ADMIN_PASSWORD);
    if (a.length !== b.length) return false;
    return timingSafeEqual(a, b);
  } catch {
    return false;
  }
}

/**
 * Middleware helper: check if request has valid auth.
 */
export async function authFromRequest(req: NextRequest): Promise<AuthSession | null> {
  const token = req.cookies.get("fw_jwt")?.value;
  if (!token || !JWT_SECRET) return null;

  try {
    const secret = new TextEncoder().encode(JWT_SECRET);
    const { payload } = await jwtVerify(token, secret, { algorithms: ["HS256"] });

    const foodRolle = (payload.food_rolle as string) || "";
    const appRole = (payload.app_role as string) || "";
    const isAdmin = foodRolle === "Admin" || appRole === "Admin";
    if (!isAdmin) return null;

    return {
      userId: (payload.benutzer_id as number) || 0,
      username: (payload.benutzername as string) || "",
      role: "admin",
      foodRolle,
      isPortalUser: true,
    };
  } catch {
    return null;
  }
}

/**
 * Check auth session cookie (set after password login).
 */
export async function checkSessionCookie(): Promise<AuthSession | null> {
  const cookieStore = await cookies();
  const session = cookieStore.get("food_session")?.value;
  if (!session) return null;

  try {
    const secret = new TextEncoder().encode(JWT_SECRET || "foodbot-session-secret");
    const { payload } = await jwtVerify(session, secret, { algorithms: ["HS256"] });
    return {
      userId: 0,
      username: (payload.username as string) || "admin",
      role: "admin",
      isPortalUser: false,
    };
  } catch {
    return null;
  }
}

/**
 * Get auth session from either Portal JWT or session cookie.
 */
export async function getAuth(): Promise<AuthSession | null> {
  return (await verifyAuth()) || (await checkSessionCookie());
}

/**
 * Require admin auth — returns auth or throws redirect.
 */
export async function requireAuth(): Promise<AuthSession> {
  const auth = await getAuth();
  if (!auth) {
    const { redirect } = await import("next/navigation");
    redirect("/food/login");
    // redirect() throws — this is unreachable
  }
  return auth as AuthSession;
}
