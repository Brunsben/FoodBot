import { NextResponse } from "next/server";
import {
  today,
  getMenuForDate,
  getRegistrationCount,
  getGuestsForDate,
} from "@/lib/utils";

export async function GET() {
  try {
    const dateStr = today();
    const menu = await getMenuForDate(dateStr);
    const regCount = await getRegistrationCount(dateStr);
    const guestData = await getGuestsForDate(dateStr);
    const guestTotal = guestData.menu1 + guestData.menu2;

    return NextResponse.json({
      date: dateStr,
      menu: menu?.description || null,
      registrations: regCount,
      guests: guestTotal,
      total: regCount + guestTotal,
    });
  } catch (error) {
    console.error("Status error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
