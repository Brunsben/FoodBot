import { db } from "@/lib/db";
import { menus, registrations, guests } from "@/lib/db/schema";
import { sql, desc, eq } from "drizzle-orm";
import Link from "next/link";

export default async function StatsPage() {
  // Average registrations per day
  const avgResult = await db
    .select({
      avgCount: sql<number>`round(avg(cnt), 1)`.as("avg_count"),
    })
    .from(
      db
        .select({
          date: registrations.date,
          cnt: sql<number>`count(*)`.as("cnt"),
        })
        .from(registrations)
        .groupBy(registrations.date)
        .as("daily_counts"),
    );

  const avgPerDay = avgResult[0]?.avgCount ?? 0;

  // Last 14 service days
  const recentDays = await db
    .select({
      date: menus.date,
      description: menus.description,
      zweiMenuesAktiv: menus.zweiMenuesAktiv,
    })
    .from(menus)
    .orderBy(desc(menus.date))
    .limit(14);

  const dayStats = await Promise.all(
    recentDays.map(async (day) => {
      const [regCount] = await db
        .select({ count: sql<number>`count(*)` })
        .from(registrations)
        .where(eq(registrations.date, day.date));

      const guestRows = await db
        .select({ count: guests.count })
        .from(guests)
        .where(eq(guests.date, day.date));

      const guestTotal = guestRows.reduce((sum, g) => sum + g.count, 0);

      return {
        ...day,
        registrations: Number(regCount.count),
        guests: guestTotal,
        total: Number(regCount.count) + guestTotal,
      };
    }),
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold dark:text-white">Statistiken</h1>
        <Link
          href="/food/api/stats/export"
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors text-sm"
        >
          📥 CSV Export
        </Link>
      </div>

      {/* Summary */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Durchschnitt pro Tag
        </p>
        <p className="text-4xl font-bold mt-1 text-blue-600 dark:text-blue-400">
          {avgPerDay}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Anmeldungen
        </p>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm overflow-hidden">
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
                <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-300">
                  Anmeldungen
                </th>
                <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-300">
                  Gäste
                </th>
                <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-300">
                  Gesamt
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
              {dayStats.map((day) => (
                <tr
                  key={day.date}
                  className="hover:bg-gray-50 dark:hover:bg-slate-700/50"
                >
                  <td className="p-3 text-sm dark:text-gray-200">
                    {new Date(day.date).toLocaleDateString("de-DE", {
                      weekday: "short",
                      day: "2-digit",
                      month: "2-digit",
                    })}
                  </td>
                  <td className="p-3 text-sm text-gray-600 dark:text-gray-400 max-w-[200px] truncate">
                    {day.description}
                  </td>
                  <td className="p-3 text-sm text-right dark:text-gray-200">
                    {day.registrations}
                  </td>
                  <td className="p-3 text-sm text-right text-gray-500 dark:text-gray-400">
                    {day.guests}
                  </td>
                  <td className="p-3 text-sm text-right font-semibold dark:text-white">
                    {day.total}
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
