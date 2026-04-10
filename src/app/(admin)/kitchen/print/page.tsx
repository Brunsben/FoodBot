import { db } from "@/lib/db";
import { menus, registrations, users, guests } from "@/lib/db/schema";
import { eq, and } from "drizzle-orm";
import PrintTrigger from "./print-trigger";

function todayString() {
  return new Date().toISOString().slice(0, 10);
}

export default async function KitchenPrintPage() {
  const today = todayString();

  const [menu, regs, guestRows] = await Promise.all([
    db.query.menus.findFirst({ where: eq(menus.date, today) }),
    db
      .select({
        userName: users.name,
        menuChoice: registrations.menuChoice,
      })
      .from(registrations)
      .innerJoin(users, eq(registrations.userId, users.id))
      .where(eq(registrations.date, today))
      .orderBy(users.name),
    db.select().from(guests).where(eq(guests.date, today)),
  ]);

  const menu1Regs = regs.filter((r) => r.menuChoice !== 2);
  const menu2Regs = regs.filter((r) => r.menuChoice === 2);
  const guestMenu1 = guestRows.find((g) => g.menuChoice === 1)?.count ?? 0;
  const guestMenu2 = guestRows.find((g) => g.menuChoice === 2)?.count ?? 0;

  const dateFormatted = new Date(today).toLocaleDateString("de-DE", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });

  return (
    <div className="p-8 max-w-3xl mx-auto bg-white text-black print:p-4">
      <PrintTrigger />

      <header className="text-center mb-6 border-b pb-4">
        <h1 className="text-2xl font-bold">Essensanmeldung</h1>
        <p className="text-lg mt-1">{dateFormatted}</p>
        {menu && <p className="text-gray-600 mt-1">{menu.description}</p>}
      </header>

      {/* Menu 1 list */}
      <section className="mb-6">
        <h2 className="text-lg font-bold border-b-2 border-black pb-1 mb-2">
          {menu?.zweiMenuesAktiv ? `Menü 1: ${menu.menu1Name || "Standard"}` : "Anmeldungen"}
          {" "}({menu1Regs.length})
        </h2>
        <div className="grid grid-cols-3 gap-x-4 gap-y-0.5 text-sm">
          {menu1Regs.map((r, i) => (
            <p key={i}>☐ {r.userName}</p>
          ))}
        </div>
      </section>

      {/* Menu 2 list */}
      {menu?.zweiMenuesAktiv && menu2Regs.length > 0 && (
        <section className="mb-6">
          <h2 className="text-lg font-bold border-b-2 border-black pb-1 mb-2">
            Menü 2: {menu.menu2Name || "Alternativ"} ({menu2Regs.length})
          </h2>
          <div className="grid grid-cols-3 gap-x-4 gap-y-0.5 text-sm">
            {menu2Regs.map((r, i) => (
              <p key={i}>☐ {r.userName}</p>
            ))}
          </div>
        </section>
      )}

      {/* Summary table */}
      <section className="mt-8 border-t-2 border-black pt-4">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-1">Kategorie</th>
              <th className="text-right py-1">Anzahl</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="py-1">{menu?.zweiMenuesAktiv ? "Menü 1" : "Anmeldungen"}</td>
              <td className="text-right py-1">{menu1Regs.length}</td>
            </tr>
            {menu?.zweiMenuesAktiv && (
              <tr>
                <td className="py-1">Menü 2</td>
                <td className="text-right py-1">{menu2Regs.length}</td>
              </tr>
            )}
            <tr>
              <td className="py-1">Gäste</td>
              <td className="text-right py-1">{guestMenu1 + guestMenu2}</td>
            </tr>
            <tr className="border-t-2 border-black font-bold">
              <td className="py-1">Gesamt</td>
              <td className="text-right py-1">{regs.length + guestMenu1 + guestMenu2}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  );
}
