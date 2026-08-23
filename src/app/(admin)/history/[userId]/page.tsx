import { db } from "@/lib/db";
import { users, registrations, menus } from "@/lib/db/schema";
import { eq, sql, desc } from "drizzle-orm";
import { notFound } from "next/navigation";
import Link from "next/link";

export default async function UserHistoryPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId: userIdStr } = await params;
  const userId = parseInt(userIdStr, 10);
  if (isNaN(userId)) notFound();

  const user = await db.query.users.findFirst({ where: eq(users.id, userId) });
  if (!user) notFound();

  // Total registrations
  const [totalResult] = await db
    .select({ count: sql<number>`count(*)` })
    .from(registrations)
    .where(eq(registrations.userId, userId));
  const totalRegs = Number(totalResult.count);

  // Last registration
  const lastReg = await db
    .select({ date: registrations.date })
    .from(registrations)
    .where(eq(registrations.userId, userId))
    .orderBy(desc(registrations.date))
    .limit(1);

  // Monthly breakdown
  const monthlyStats = await db
    .select({
      month: sql<string>`to_char(${registrations.date}::date, 'YYYY-MM')`.as(
        "month",
      ),
      count: sql<number>`count(*)`.as("count"),
    })
    .from(registrations)
    .where(eq(registrations.userId, userId))
    .groupBy(sql`to_char(${registrations.date}::date, 'YYYY-MM')`)
    .orderBy(desc(sql`to_char(${registrations.date}::date, 'YYYY-MM')`));

  const avgPerMonth =
    monthlyStats.length > 0
      ? (totalRegs / monthlyStats.length).toFixed(1)
      : "0";

  // All registrations with menu info
  const allRegs = await db
    .select({
      date: registrations.date,
      menuChoice: registrations.menuChoice,
      menuDescription: menus.description,
      zweiMenuesAktiv: menus.zweiMenuesAktiv,
      menu1Name: menus.menu1Name,
      menu2Name: menus.menu2Name,
    })
    .from(registrations)
    .leftJoin(menus, eq(registrations.date, menus.date))
    .where(eq(registrations.userId, userId))
    .orderBy(desc(registrations.date));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/food/history"
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
        >
          ←
        </Link>
        <div>
          <h1 className="text-2xl font-bold dark:text-white">{user.name}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Personal-Nr: {user.personalNumber}
          </p>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm">
          <p className="text-sm text-gray-500 dark:text-gray-400">Gesamt</p>
          <p className="text-3xl font-bold mt-1 text-blue-600 dark:text-blue-400">
            {totalRegs}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500">
            Anmeldungen
          </p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Ø pro Monat
          </p>
          <p className="text-3xl font-bold mt-1 text-green-600 dark:text-green-400">
            {avgPerMonth}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500">
            Anmeldungen
          </p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Letzte Anmeldung
          </p>
          <p className="text-xl font-bold mt-1 dark:text-white">
            {lastReg[0]
              ? new Date(lastReg[0].date).toLocaleDateString("de-DE")
              : "–"}
          </p>
        </div>
      </div>

      {/* Monthly breakdown */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 dark:border-slate-700">
          <h2 className="font-semibold dark:text-white">
            Monatliche Übersicht
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-slate-700">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-300">
                  Monat
                </th>
                <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-300">
                  Anmeldungen
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
              {monthlyStats.map((m) => (
                <tr
                  key={m.month}
                  className="hover:bg-gray-50 dark:hover:bg-slate-700/50"
                >
                  <td className="p-3 text-sm dark:text-gray-200">{m.month}</td>
                  <td className="p-3 text-sm text-right font-medium dark:text-white">
                    {m.count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* All registrations */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 dark:border-slate-700">
          <h2 className="font-semibold dark:text-white">Alle Anmeldungen</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-slate-700">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-300">
                  Datum
                </th>
                <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-300">
                  Menü
                </th>
                <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-300">
                  Wahl
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
              {allRegs.map((r, i) => (
                <tr
                  key={i}
                  className="hover:bg-gray-50 dark:hover:bg-slate-700/50"
                >
                  <td className="p-3 text-sm dark:text-gray-200">
                    {new Date(r.date).toLocaleDateString("de-DE", {
                      weekday: "short",
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric",
                    })}
                  </td>
                  <td className="p-3 text-sm text-gray-600 dark:text-gray-400 max-w-[200px] truncate">
                    {r.menuDescription || "–"}
                  </td>
                  <td className="p-3 text-sm">
                    {r.zweiMenuesAktiv ? (
                      <span
                        className={
                          r.menuChoice === 2
                            ? "text-green-600 dark:text-green-400"
                            : "text-blue-600 dark:text-blue-400"
                        }
                      >
                        Menü {r.menuChoice}
                        {r.menuChoice === 1 && r.menu1Name
                          ? ` (${r.menu1Name})`
                          : ""}
                        {r.menuChoice === 2 && r.menu2Name
                          ? ` (${r.menu2Name})`
                          : ""}
                      </span>
                    ) : (
                      <span className="text-gray-500 dark:text-gray-400">
                        –
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
