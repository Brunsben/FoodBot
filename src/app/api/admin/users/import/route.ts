import { NextRequest, NextResponse } from "next/server";
import { getAuth } from "@/lib/auth";
import { db } from "@/lib/db";
import { users } from "@/lib/db/schema";
import { eq } from "drizzle-orm";
import { logAdmin } from "@/lib/audit";

export async function POST(req: NextRequest) {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const body = await req.json();
    const { csv } = body;

    if (!csv || typeof csv !== "string") {
      return NextResponse.json({ error: "CSV-Daten erforderlich" }, { status: 400 });
    }

    const lines = csv
      .split("\n")
      .map((l: string) => l.trim())
      .filter((l: string) => l && !l.startsWith("name") && !l.startsWith("Name"));

    let created = 0;
    let updated = 0;
    const errors: string[] = [];

    for (let i = 0; i < lines.length; i++) {
      const parts = lines[i].split(/[,;]/).map((p: string) => p.trim());
      const [name, personalNumber, cardId] = parts;

      if (!name || !personalNumber) {
        errors.push(`Zeile ${i + 1}: Name und Personalnummer erforderlich`);
        continue;
      }

      try {
        const [existing] = await db
          .select()
          .from(users)
          .where(eq(users.personalNumber, personalNumber))
          .limit(1);

        if (existing) {
          await db
            .update(users)
            .set({ name, cardId: cardId || existing.cardId })
            .where(eq(users.id, existing.id));
          updated++;
        } else {
          await db.insert(users).values({
            name,
            personalNumber,
            cardId: cardId || null,
          });
          created++;
        }
      } catch (err) {
        errors.push(`Zeile ${i + 1}: ${err instanceof Error ? err.message : "Fehler"}`);
      }
    }

    await logAdmin(auth.username, "CSV-Import", `Erstellt: ${created}, Aktualisiert: ${updated}, Fehler: ${errors.length}`);

    return NextResponse.json({ success: true, created, updated, errors });
  } catch (error) {
    console.error("User import error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
