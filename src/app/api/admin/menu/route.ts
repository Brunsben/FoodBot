import { NextRequest, NextResponse } from "next/server";
import { getAuth } from "@/lib/auth";
import { saveMenu } from "@/lib/utils";
import { logAdmin } from "@/lib/audit";

export async function POST(req: NextRequest) {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const body = await req.json();
    const { date, description, zwei_menues_aktiv, menu1_name, menu2_name, registration_deadline, deadline_enabled } =
      body;

    if (!date || !description) {
      return NextResponse.json({ error: "Datum und Beschreibung erforderlich" }, { status: 400 });
    }

    await saveMenu(date, {
      description,
      zweiMenuesAktiv: zwei_menues_aktiv,
      menu1Name: menu1_name,
      menu2Name: menu2_name,
      registrationDeadline: registration_deadline,
      deadlineEnabled: deadline_enabled,
    });

    await logAdmin(auth.username, "Menü gespeichert", `${date}: ${description}`);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Admin menu error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
