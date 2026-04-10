import { NextRequest, NextResponse } from "next/server";
import { getAuth } from "@/lib/auth";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import { logAdmin } from "@/lib/audit";

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const { id } = await params;
    const [user] = await db.select().from(users).where(eq(users.id, parseInt(id, 10))).limit(1);

    if (!user) {
      return NextResponse.json({ error: "Benutzer nicht gefunden" }, { status: 404 });
    }

    return NextResponse.json({ user });
  } catch (error) {
    console.error("Admin user GET error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}

export async function PUT(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const { id } = await params;
    const userId = parseInt(id, 10);
    const body = await req.json();
    const { name, personal_number, card_id } = body;

    const [existing] = await db.select().from(users).where(eq(users.id, userId)).limit(1);
    if (!existing) {
      return NextResponse.json({ error: "Benutzer nicht gefunden" }, { status: 404 });
    }

    const [updated] = await db
      .update(users)
      .set({
        ...(name !== undefined && { name }),
        ...(personal_number !== undefined && { personalNumber: personal_number }),
        ...(card_id !== undefined && { cardId: card_id || null }),
      })
      .where(eq(users.id, userId))
      .returning();

    await logAdmin(auth.username, "Benutzer aktualisiert", `ID ${userId}: ${updated.name}`);

    return NextResponse.json({ success: true, user: updated });
  } catch (error) {
    console.error("Admin user PUT error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}

export async function DELETE(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const { id } = await params;
    const userId = parseInt(id, 10);

    const [existing] = await db.select().from(users).where(eq(users.id, userId)).limit(1);
    if (!existing) {
      return NextResponse.json({ error: "Benutzer nicht gefunden" }, { status: 404 });
    }

    await db.delete(users).where(eq(users.id, userId));
    await logAdmin(auth.username, "Benutzer gelöscht", `${existing.name} (${existing.personalNumber})`);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Admin user DELETE error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
