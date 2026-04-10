import { NextRequest, NextResponse } from "next/server";
import { verifyPassword } from "@/lib/auth";
import { SignJWT } from "jose";

const JWT_SECRET = process.env.JWT_SECRET || "foodbot-session-secret";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { password } = body;

    if (!password) {
      return NextResponse.json({ error: "Passwort erforderlich" }, { status: 400 });
    }

    if (!verifyPassword(password)) {
      return NextResponse.json({ error: "Ungültiges Passwort" }, { status: 401 });
    }

    const secret = new TextEncoder().encode(JWT_SECRET);
    const token = await new SignJWT({ username: "admin", role: "admin" })
      .setProtectedHeader({ alg: "HS256" })
      .setIssuedAt()
      .setExpirationTime("24h")
      .sign(secret);

    const response = NextResponse.json({ success: true });
    response.cookies.set("food_session", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/food",
      maxAge: 60 * 60 * 24, // 24 hours
    });

    return response;
  } catch (error) {
    console.error("Login error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
