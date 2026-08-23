import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import {
  today,
  getMenuForDate,
  isRegistrationOpen,
  toggleRegistration,
} from "@/lib/utils";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { card_id, personal_number, portal_member_id, menu_choice } = body;

    if (!card_id && !personal_number && !portal_member_id) {
      return NextResponse.json(
        { error: "card_id, personal_number oder portal_member_id erforderlich" },
        { status: 400 },
      );
    }

    // Find user
    let user;
    if (portal_member_id) {
      [user] = await db
        .select()
        .from(users)
        .where(eq(users.portalMemberId, String(portal_member_id)))
        .limit(1);
    }
    if (!user && card_id) {
      [user] = await db
        .select()
        .from(users)
        .where(eq(users.cardId, card_id))
        .limit(1);
    }
    if (!user && personal_number) {
      [user] = await db
        .select()
        .from(users)
        .where(eq(users.personalNumber, personal_number))
        .limit(1);
    }

    if (!user) {
      return NextResponse.json(
        { error: "Benutzer nicht gefunden" },
        { status: 404 },
      );
    }

    const dateStr = today();
    const menu = await getMenuForDate(dateStr);

    // Check dual menu — if active and no choice given, ask user
    if (menu?.zweiMenuesAktiv && !menu_choice) {
      return NextResponse.json({
        success: true,
        need_menu_choice: true,
        user_id: user.id,
        menu1: menu.menu1Name,
        menu2: menu.menu2Name,
        user: { name: user.name, personal_number: user.personalNumber },
      });
    }

    // Check deadline
    if (menu && !isRegistrationOpen(menu)) {
      return NextResponse.json(
        { error: "Anmeldefrist abgelaufen" },
        { status: 403 },
      );
    }

    const result = await toggleRegistration(user.id, menu_choice || 1);

    return NextResponse.json({
      success: true,
      registered: result.registered,
      user: { name: user.name, personal_number: user.personalNumber },
    });
  } catch (error) {
    console.error("Register error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
