"use client";

import useSWR from "swr";
import Link from "next/link";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function KitchenPage() {
  const { data, mutate } = useSWR("/food/api/kitchen/data", fetcher, {
    refreshInterval: 10000,
  });

  const adjustGuests = async (menuChoice: number, delta: number) => {
    await fetch("/food/api/kitchen/guests", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ menu_choice: menuChoice, delta }),
    });
    mutate();
  };

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  const menu = data.menu;
  const users = data.users || [];
  const guests = data.guests || { menu1: 0, menu2: 0 };
  const registeredUsers = users.filter(
    (u: { registered: boolean }) => u.registered,
  );
  const menu1Users = registeredUsers.filter(
    (u: { menuChoice?: number }) => u.menuChoice !== 2,
  );
  const menu2Users = registeredUsers.filter(
    (u: { menuChoice?: number }) => u.menuChoice === 2,
  );
  const totalGuests = guests.menu1 + guests.menu2;
  const total = registeredUsers.length + totalGuests;

  return (
    <div className="space-y-6">
      {/* Stats bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Gesamt" value={total} color="blue" />
        <StatCard
          label="Menü 1"
          value={menu1Users.length + guests.menu1}
          color="sky"
        />
        {menu?.zweiMenuesAktiv && (
          <StatCard
            label="Menü 2"
            value={menu2Users.length + guests.menu2}
            color="green"
          />
        )}
        <StatCard label="Gäste" value={totalGuests} color="amber" />
      </div>

      {/* Menu */}
      {menu && (
        <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold dark:text-white">
            {menu.description}
          </h2>
          {menu.zweiMenuesAktiv && (
            <div className="flex gap-3 mt-2 text-sm">
              <span className="text-blue-600 dark:text-blue-400">
                Menü 1: {menu.menu1Name || "Standard"}
              </span>
              <span className="text-green-600 dark:text-green-400">
                Menü 2: {menu.menu2Name || "Alternativ"}
              </span>
            </div>
          )}
        </div>
      )}

      {/* User grid */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">
          Angemeldete Benutzer ({registeredUsers.length})
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
          {registeredUsers.map(
            (u: { id: number; name: string; menuChoice?: number }) => (
              <div
                key={u.id}
                className={`p-2.5 text-sm rounded-lg text-center font-medium ${
                  u.menuChoice === 2
                    ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300"
                    : "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300"
                }`}
              >
                {u.name}
              </div>
            ),
          )}
        </div>
      </div>

      {/* Guest controls */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">Gäste</h2>
        <div className="flex flex-wrap gap-6">
          <GuestCounter
            label="Menü 1"
            count={guests.menu1}
            onAdjust={(d) => adjustGuests(1, d)}
          />
          {menu?.zweiMenuesAktiv && (
            <GuestCounter
              label="Menü 2"
              count={guests.menu2}
              onAdjust={(d) => adjustGuests(2, d)}
            />
          )}
        </div>
      </div>

      {/* Print button */}
      <div className="flex justify-end">
        <Link
          href="/food/kitchen/print"
          className="px-6 py-2.5 bg-gray-800 dark:bg-gray-200 dark:text-gray-800 text-white font-medium rounded-lg hover:opacity-90 transition-opacity"
        >
          🖨️ Druckansicht
        </Link>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  const colors: Record<string, string> = {
    blue: "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400",
    sky: "bg-sky-50 dark:bg-sky-900/20 text-sky-600 dark:text-sky-400",
    green:
      "bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400",
    amber:
      "bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400",
  };

  return (
    <div className={`rounded-xl p-4 ${colors[color] ?? colors.blue}`}>
      <p className="text-sm font-medium opacity-80">{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
  );
}

function GuestCounter({
  label,
  count,
  onAdjust,
}: {
  label: string;
  count: number;
  onAdjust: (d: number) => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-600 dark:text-gray-400 w-16">
        {label}:
      </span>
      <button
        onClick={() => onAdjust(-1)}
        className="w-10 h-10 rounded-lg bg-gray-200 dark:bg-slate-600 hover:bg-gray-300 dark:hover:bg-slate-500 text-lg font-bold transition-colors"
      >
        -
      </button>
      <span className="w-10 text-center text-xl font-semibold dark:text-white">
        {count}
      </span>
      <button
        onClick={() => onAdjust(1)}
        className="w-10 h-10 rounded-lg bg-gray-200 dark:bg-slate-600 hover:bg-gray-300 dark:hover:bg-slate-500 text-lg font-bold transition-colors"
      >
        +
      </button>
    </div>
  );
}
