import { NextRequest, NextResponse } from "next/server";
import { getAuth } from "@/lib/auth";
import { setGuestCount } from "@/lib/utils";
import { logAdmin } from "@/lib/audit";

export async function POST(req: NextRequest) {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const body = await req.json();
    const { date, menu_choice, count } = body;

    if (!date || menu_choice === undefined || count === undefined) {
      return NextResponse.json(
        { error: "date, menu_choice und count erforderlich" },
        { status: 400 },
      );
    }

    await setGuestCount(date, menu_choice, count);
    await logAdmin(
      auth.username,
      "Gäste aktualisiert",
      `${date}: Menü ${menu_choice} = ${count}`,
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Admin guests error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
