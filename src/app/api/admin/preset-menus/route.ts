import { NextRequest, NextResponse } from "next/server";
import { getAuth } from "@/lib/auth";
import { db } from "@/lib/db";
import { presetMenus } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import { logAdmin } from "@/lib/audit";

export async function GET() {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const menus = await db
      .select()
      .from(presetMenus)
      .orderBy(presetMenus.sortOrder, presetMenus.name);
    return NextResponse.json({ preset_menus: menus });
  } catch (error) {
    console.error("Preset menus GET error:", error);
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
    const { name, sort_order } = body;

    if (!name) {
      return NextResponse.json({ error: "Name erforderlich" }, { status: 400 });
    }

    const [preset] = await db
      .insert(presetMenus)
      .values({ name, sortOrder: sort_order || 0 })
      .returning();

    await logAdmin(auth.username, "Voreinstellung erstellt", name);

    return NextResponse.json(
      { success: true, preset_menu: preset },
      { status: 201 },
    );
  } catch (error) {
    console.error("Preset menus POST error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const { searchParams } = new URL(req.url);
    const id = searchParams.get("id");

    if (!id) {
      return NextResponse.json({ error: "ID erforderlich" }, { status: 400 });
    }

    const [existing] = await db
      .select()
      .from(presetMenus)
      .where(eq(presetMenus.id, parseInt(id, 10)))
      .limit(1);
    if (!existing) {
      return NextResponse.json(
        { error: "Voreinstellung nicht gefunden" },
        { status: 404 },
      );
    }

    await db.delete(presetMenus).where(eq(presetMenus.id, parseInt(id, 10)));
    await logAdmin(auth.username, "Voreinstellung gelöscht", existing.name);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Preset menus DELETE error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
