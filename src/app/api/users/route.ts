import { NextRequest, NextResponse } from "next/server";
import { getAuth } from "@/lib/auth";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { sql } from "drizzle-orm";

export async function GET(req: NextRequest) {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const { searchParams } = new URL(req.url);
    const page = Math.max(parseInt(searchParams.get("page") || "1", 10), 1);
    const perPage = Math.min(Math.max(parseInt(searchParams.get("per_page") || "50", 10), 1), 200);
    const offset = (page - 1) * perPage;

    const [countResult] = await db.select({ count: sql<number>`count(*)::int` }).from(users);
    const total = countResult?.count || 0;

    const data = await db
      .select()
      .from(users)
      .orderBy(users.name)
      .limit(perPage)
      .offset(offset);

    return NextResponse.json({
      users: data,
      pagination: { page, per_page: perPage, total, pages: Math.ceil(total / perPage) },
    });
  } catch (error) {
    console.error("Users error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
