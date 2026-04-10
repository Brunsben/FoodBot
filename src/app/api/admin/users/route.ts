import { NextRequest, NextResponse } from "next/server";
import { getAuth } from "@/lib/auth";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { logAdmin } from "@/lib/audit";

export async function GET() {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const allUsers = await db.select().from(users).orderBy(users.name);
    return NextResponse.json({ users: allUsers });
  } catch (error) {
    console.error("Admin users GET error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const body = await req.json();
    const { name, personal_number, card_id } = body;

    if (!name || !personal_number) {
      return NextResponse.json({ error: "Name und Personalnummer erforderlich" }, { status: 400 });
    }

    const [newUser] = await db
      .insert(users)
      .values({
        name,
        personalNumber: personal_number,
        cardId: card_id || null,
      })
      .returning();

    await logAdmin(auth.username, "Benutzer erstellt", `${name} (${personal_number})`);

    return NextResponse.json({ success: true, user: newUser }, { status: 201 });
  } catch (error) {
    console.error("Admin users POST error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
