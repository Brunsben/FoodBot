import { db } from "@/lib/db";
import { users, registrations } from "@/lib/db/schema";
import { sql, desc, eq, gte } from "drizzle-orm";
import Link from "next/link";

export default async function HistoryPage() {
  const now = new Date();
  const d90 = new Date(now.getTime() - 90 * 86400000).toISOString().slice(0, 10);
  const d30 = new Date(now.getTime() - 30 * 86400000).toISOString().slice(0, 10);
  const d7 = new Date(now.getTime() - 7 * 86400000).toISOString().slice(0, 10);

  // Top 10 by total registration count
  const topUsers = await db
    .select({
      userId: users.id,
      name: users.name,
      totalRegs: sql<number>`count(${registrations.id})`.as("total_regs"),
    })
    .from(users)
    .leftJoin(registrations, eq(users.id, registrations.userId))
    .groupBy(users.id, users.name)
    .orderBy(desc(sql`count(${registrations.id})`))
    .limit(10);

  // All users with period counts
  const allUsers = await db
    .select({
      userId: users.id,
      name: users.name,
      personalNumber: users.personalNumber,
    })
    .from(users)
    .orderBy(users.name);

  const userStats = await Promise.all(
    allUsers.map(async (u) => {
      const [r90] = await db
        .select({ count: sql<number>`count(*)` })
        .from(registrations)
        .where(
          sql`${registrations.userId} = ${u.userId} AND ${registrations.date} >= ${d90}`,
        );
      const [r30] = await db
        .select({ count: sql<number>`count(*)` })
        .from(registrations)
        .where(
          sql`${registrations.userId} = ${u.userId} AND ${registrations.date} >= ${d30}`,
        );
      const [r7] = await db
        .select({ count: sql<number>`count(*)` })
        .from(registrations)
        .where(
          sql`${registrations.userId} = ${u.userId} AND ${registrations.date} >= ${d7}`,
        );

      return {
        ...u,
        last90: Number(r90.count),
        last30: Number(r30.count),
        last7: Number(r7.count),
      };
    }),
  );

  const badges = ["🥇", "🥈", "🥉"];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold dark:text-white">Historie</h1>

      {/* Top 10 */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">Top 10 Stammesser</h2>
        <div className="space-y-2">
          {topUsers.map((u, i) => (
            <Link
              key={u.userId}
              href={`/food/history/${u.userId}`}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-xl w-8 text-center">{badges[i] ?? `${i + 1}.`}</span>
                <span className="font-medium dark:text-white">{u.name}</span>
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {u.totalRegs} Anmeldungen
              </span>
            </Link>
          ))}
        </div>
      </div>

      {/* All users table */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-slate-700">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-300">Name</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-300">90 Tage</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-300">30 Tage</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-300">7 Tage</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-300"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
              {userStats.map((u) => (
                <tr key={u.userId} className="hover:bg-gray-50 dark:hover:bg-slate-700/50">
                  <td className="p-3 text-sm dark:text-gray-200">{u.name}</td>
                  <td className="p-3 text-sm text-right dark:text-gray-300">{u.last90}</td>
                  <td className="p-3 text-sm text-right dark:text-gray-300">{u.last30}</td>
                  <td className="p-3 text-sm text-right dark:text-gray-300">{u.last7}</td>
                  <td className="p-3 text-sm text-right">
                    <Link
                      href={`/food/history/${u.userId}`}
                      className="text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Details
                    </Link>
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
