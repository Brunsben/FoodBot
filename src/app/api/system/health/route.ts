import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { users, menus, registrations } from "@/lib/db/schema";
import { sql } from "drizzle-orm";

export async function GET() {
  try {
    const [userCount] = await db
      .select({ count: sql<number>`count(*)::int` })
      .from(users);
    const [menuCount] = await db
      .select({ count: sql<number>`count(*)::int` })
      .from(menus);
    const [regCount] = await db
      .select({ count: sql<number>`count(*)::int` })
      .from(registrations);

    return NextResponse.json({
      status: "ok",
      database: "connected",
      counts: {
        users: userCount?.count || 0,
        menus: menuCount?.count || 0,
        registrations: regCount?.count || 0,
      },
    });
  } catch (error) {
    console.error("Health check error:", error);
    return NextResponse.json(
      {
        status: "error",
        database: "disconnected",
        error: error instanceof Error ? error.message : "Unbekannter Fehler",
      },
      { status: 503 },
    );
  }
}
