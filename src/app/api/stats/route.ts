import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { menus, registrations, guests } from "@/lib/db/schema";
import { sql, gte, desc } from "drizzle-orm";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const days = Math.min(Math.max(parseInt(searchParams.get("days") || "7", 10) || 7, 1), 90);

    const since = new Date();
    since.setDate(since.getDate() - days);
    const sinceStr = since.toISOString().split("T")[0];

    const menuData = await db
      .select()
      .from(menus)
      .where(gte(menus.date, sinceStr))
      .orderBy(desc(menus.date));

    const regCounts = await db
      .select({
        date: registrations.date,
        menuChoice: registrations.menuChoice,
        count: sql<number>`count(*)::int`,
      })
      .from(registrations)
      .where(gte(registrations.date, sinceStr))
      .groupBy(registrations.date, registrations.menuChoice);

    const guestData = await db
      .select()
      .from(guests)
      .where(gte(guests.date, sinceStr));

    const stats = menuData.map((menu) => {
      const dayRegs = regCounts.filter((r) => r.date === menu.date);
      const dayGuests = guestData.filter((g) => g.date === menu.date);
      const menu1Regs = dayRegs.find((r) => r.menuChoice === 1)?.count || 0;
      const menu2Regs = dayRegs.find((r) => r.menuChoice === 2)?.count || 0;
      const menu1Guests = dayGuests.find((g) => g.menuChoice === 1)?.count || 0;
      const menu2Guests = dayGuests.find((g) => g.menuChoice === 2)?.count || 0;

      return {
        date: menu.date,
        description: menu.description,
        menu1: menu1Regs,
        menu2: menu2Regs,
        guests_menu1: menu1Guests,
        guests_menu2: menu2Guests,
        total: menu1Regs + menu2Regs + menu1Guests + menu2Guests,
      };
    });

    return NextResponse.json({ days, stats });
  } catch (error) {
    console.error("Stats error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
