import { NextResponse } from "next/server";
import { getAuth } from "@/lib/auth";
import { syncFromPortal } from "@/lib/sync";
import { logAdmin } from "@/lib/audit";

export async function POST() {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const result = await syncFromPortal();
    await logAdmin(
      auth.username,
      "Portal-Sync",
      `Erstellt: ${result.created}, Aktualisiert: ${result.updated}`,
    );

    return NextResponse.json({ success: true, ...result });
  } catch (error) {
    console.error("Sync error:", error);
    const message =
      error instanceof Error ? error.message : "Sync fehlgeschlagen";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
