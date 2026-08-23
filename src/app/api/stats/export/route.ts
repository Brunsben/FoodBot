import { NextResponse } from "next/server";
import { getAuth } from "@/lib/auth";
import { db } from "@/lib/db";
import { registrations, users, menus } from "@/lib/db/schema";
import { eq, gte, desc } from "drizzle-orm";

export async function GET() {
  try {
    const auth = await getAuth();
    if (!auth) {
      return NextResponse.json({ error: "Nicht autorisiert" }, { status: 401 });
    }

    const since = new Date();
    since.setDate(since.getDate() - 365);
    const sinceStr = since.toISOString().split("T")[0];

    const data = await db
      .select({
        date: registrations.date,
        userName: users.name,
        personalNumber: users.personalNumber,
        menuChoice: registrations.menuChoice,
        menuDescription: menus.description,
      })
      .from(registrations)
      .innerJoin(users, eq(registrations.userId, users.id))
      .leftJoin(menus, eq(registrations.date, menus.date))
      .where(gte(registrations.date, sinceStr))
      .orderBy(desc(registrations.date), users.name);

    const lines = ["Datum;Name;Personalnummer;Menüwahl;Menübeschreibung"];
    for (const row of data) {
      lines.push(
        `${row.date};${row.userName};${row.personalNumber};Menü ${row.menuChoice};${row.menuDescription || ""}`,
      );
    }

    const csv = lines.join("\n");
    return new NextResponse(csv, {
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="essensmeldung_export_${new Date().toISOString().split("T")[0]}.csv"`,
      },
    });
  } catch (error) {
    console.error("Stats export error:", error);
    return NextResponse.json({ error: "Interner Fehler" }, { status: 500 });
  }
}
