"use client";

import { useState } from "react";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

// ─── Tab 1: Tagesplanung ────────────────────────────────────────

function DayPlanningTab() {
  const { data: menuData, mutate: mutateMenu } = useSWR("/food/api/menu/data", fetcher);
  const { data: kitchenData, mutate: mutateKitchen } = useSWR("/food/api/kitchen/data", fetcher);
  const { data: presets } = useSWR("/food/api/admin/preset-menus", fetcher);

  const [description, setDescription] = useState("");
  const [zweiMenues, setZweiMenues] = useState(false);
  const [menu1Name, setMenu1Name] = useState("");
  const [menu2Name, setMenu2Name] = useState("");
  const [deadline, setDeadline] = useState("19:45");
  const [deadlineEnabled, setDeadlineEnabled] = useState(true);
  const [saving, setSaving] = useState(false);

  // Initialize form from server data
  const menu = menuData?.menu;

  const handleSaveMenu = async () => {
    setSaving(true);
    try {
      await fetch("/food/api/admin/menu", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: description || menu?.description || "",
          zwei_menues_aktiv: zweiMenues,
          menu1_name: menu1Name,
          menu2_name: menu2Name,
          registration_deadline: deadline,
          deadline_enabled: deadlineEnabled,
        }),
      });
      mutateMenu();
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  };

  const toggleUser = async (personalNumber: string) => {
    await fetch("/food/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ personal_number: personalNumber, menu_choice: 1 }),
    });
    mutateKitchen();
  };

  const adjustGuests = async (menuChoice: number, delta: number) => {
    await fetch("/food/api/kitchen/guests", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ menu_choice: menuChoice, delta }),
    });
    mutateKitchen();
  };

  return (
    <div className="space-y-6">
      {/* Menu form */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">Tagesmenü</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Beschreibung
            </label>
            <input
              type="text"
              list="preset-menus"
              value={description || menu?.description || ""}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              placeholder="z.B. Schnitzel mit Pommes"
            />
            {presets?.length > 0 && (
              <datalist id="preset-menus">
                {presets.map((p: { id: number; name: string }) => (
                  <option key={p.id} value={p.name} />
                ))}
              </datalist>
            )}
          </div>

          <div className="flex items-center gap-3">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={zweiMenues}
                onChange={(e) => setZweiMenues(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 dark:bg-gray-600 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600" />
            </label>
            <span className="text-sm text-gray-700 dark:text-gray-300">Zwei Menüs</span>
          </div>

          {zweiMenues && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Menü 1</label>
                <input
                  type="text"
                  value={menu1Name}
                  onChange={(e) => setMenu1Name(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Menü 2</label>
                <input
                  type="text"
                  value={menu2Name}
                  onChange={(e) => setMenu2Name(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>
            </div>
          )}

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={deadlineEnabled}
                  onChange={(e) => setDeadlineEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 dark:bg-gray-600 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600" />
              </label>
              <span className="text-sm text-gray-700 dark:text-gray-300">Deadline</span>
            </div>
            {deadlineEnabled && (
              <input
                type="time"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            )}
          </div>

          <button
            onClick={handleSaveMenu}
            disabled={saving}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            {saving ? "Speichern..." : "Menü speichern"}
          </button>
        </div>
      </div>

      {/* Guest management */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">Gäste</h2>
        <div className="flex gap-6">
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600 dark:text-gray-400">Menü 1:</span>
            <button onClick={() => adjustGuests(1, -1)} className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-slate-600 hover:bg-gray-300 dark:hover:bg-slate-500 font-bold transition-colors">-</button>
            <span className="w-8 text-center font-semibold dark:text-white">{kitchenData?.guests?.menu1 ?? 0}</span>
            <button onClick={() => adjustGuests(1, 1)} className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-slate-600 hover:bg-gray-300 dark:hover:bg-slate-500 font-bold transition-colors">+</button>
          </div>
          {(zweiMenues || menu?.zweiMenuesAktiv) && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600 dark:text-gray-400">Menü 2:</span>
              <button onClick={() => adjustGuests(2, -1)} className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-slate-600 hover:bg-gray-300 dark:hover:bg-slate-500 font-bold transition-colors">-</button>
              <span className="w-8 text-center font-semibold dark:text-white">{kitchenData?.guests?.menu2 ?? 0}</span>
              <button onClick={() => adjustGuests(2, 1)} className="w-8 h-8 rounded-lg bg-gray-200 dark:bg-slate-600 hover:bg-gray-300 dark:hover:bg-slate-500 font-bold transition-colors">+</button>
            </div>
          )}
        </div>
      </div>

      {/* User list */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">Benutzer ({kitchenData?.users?.length ?? 0})</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {kitchenData?.users?.map((u: { id: number; name: string; personalNumber: string; registered: boolean; menuChoice?: number }) => (
            <button
              key={u.id}
              onClick={() => toggleUser(u.personalNumber)}
              className={`p-2 text-sm rounded-lg text-left transition-colors ${
                u.registered
                  ? u.menuChoice === 2
                    ? "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 ring-1 ring-green-300 dark:ring-green-700"
                    : "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 ring-1 ring-blue-300 dark:ring-blue-700"
                  : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-slate-600"
              }`}
            >
              {u.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Tab 2: User-Verwaltung ──────────────────────────────────────

function UserManagementTab() {
  const { data: usersData, mutate: mutateUsers } = useSWR("/food/api/users", fetcher);
  const { data: presets, mutate: mutatePresets } = useSWR("/food/api/admin/preset-menus", fetcher);

  const [newName, setNewName] = useState("");
  const [newPersonalNr, setNewPersonalNr] = useState("");
  const [newCardId, setNewCardId] = useState("");
  const [newPreset, setNewPreset] = useState("");
  const [syncing, setSyncing] = useState(false);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await fetch("/food/api/admin/sync", { method: "POST" });
      mutateUsers();
    } catch {
      /* ignore */
    } finally {
      setSyncing(false);
    }
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName || !newPersonalNr) return;
    await fetch("/food/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName, personal_number: newPersonalNr, card_id: newCardId || null }),
    });
    setNewName("");
    setNewPersonalNr("");
    setNewCardId("");
    mutateUsers();
  };

  const handleDeleteUser = async (id: number) => {
    if (!confirm("Benutzer wirklich löschen?")) return;
    await fetch(`/food/api/users/${id}`, { method: "DELETE" });
    mutateUsers();
  };

  const handleImportCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    await fetch("/food/api/admin/users/import", { method: "POST", body: formData });
    mutateUsers();
    e.target.value = "";
  };

  const handleAddPreset = async () => {
    if (!newPreset.trim()) return;
    await fetch("/food/api/admin/preset-menus", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newPreset }),
    });
    setNewPreset("");
    mutatePresets();
  };

  const handleDeletePreset = async (id: number) => {
    await fetch(`/food/api/admin/preset-menus/${id}`, { method: "DELETE" });
    mutatePresets();
  };

  return (
    <div className="space-y-6">
      {/* Sync + Import */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            {syncing ? "Synchronisiere..." : "Portal-Sync"}
          </button>
          <label className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors cursor-pointer">
            CSV Import
            <input type="file" accept=".csv" onChange={handleImportCSV} className="hidden" />
          </label>
        </div>
      </div>

      {/* Add user */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">Benutzer hinzufügen</h2>
        <form onSubmit={handleAddUser} className="flex flex-wrap gap-3">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Name"
            required
            className="flex-1 min-w-[150px] p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
          <input
            type="text"
            value={newPersonalNr}
            onChange={(e) => setNewPersonalNr(e.target.value)}
            placeholder="Personalnummer"
            required
            className="w-40 p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
          <input
            type="text"
            value={newCardId}
            onChange={(e) => setNewCardId(e.target.value)}
            placeholder="Karten-ID (optional)"
            className="w-44 p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
          <button
            type="submit"
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            Hinzufügen
          </button>
        </form>
      </div>

      {/* Users table */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-slate-700">
              <tr>
                <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-300">Name</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-300">Personal-Nr.</th>
                <th className="text-left p-3 text-sm font-medium text-gray-600 dark:text-gray-300">Karten-ID</th>
                <th className="text-right p-3 text-sm font-medium text-gray-600 dark:text-gray-300">Aktionen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-700">
              {usersData?.map?.((u: { id: number; name: string; personalNumber: string; cardId: string | null }) => (
                <tr key={u.id} className="hover:bg-gray-50 dark:hover:bg-slate-700/50">
                  <td className="p-3 text-sm dark:text-gray-200">{u.name}</td>
                  <td className="p-3 text-sm text-gray-600 dark:text-gray-400">{u.personalNumber}</td>
                  <td className="p-3 text-sm text-gray-600 dark:text-gray-400">{u.cardId || "–"}</td>
                  <td className="p-3 text-sm text-right">
                    <a href={`/food/qr/${u.id}`} className="text-blue-600 dark:text-blue-400 hover:underline mr-3">
                      QR
                    </a>
                    <button
                      onClick={() => handleDeleteUser(u.id)}
                      className="text-red-600 dark:text-red-400 hover:underline"
                    >
                      Löschen
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Preset menus */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">Menü-Vorlagen</h2>
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            value={newPreset}
            onChange={(e) => setNewPreset(e.target.value)}
            placeholder="Neue Vorlage..."
            className="flex-1 p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            onKeyDown={(e) => e.key === "Enter" && handleAddPreset()}
          />
          <button
            onClick={handleAddPreset}
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            +
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {presets?.map?.((p: { id: number; name: string }) => (
            <span key={p.id} className="inline-flex items-center gap-1 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 px-3 py-1.5 rounded-lg text-sm">
              {p.name}
              <button
                onClick={() => handleDeletePreset(p.id)}
                className="ml-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main Admin Page ─────────────────────────────────────────────

export default function AdminPage() {
  const [tab, setTab] = useState<"day" | "users">("day");

  return (
    <div>
      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 dark:bg-slate-800 rounded-lg p-1 w-fit">
        <button
          onClick={() => setTab("day")}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === "day"
              ? "bg-white dark:bg-slate-700 text-gray-900 dark:text-white shadow-sm"
              : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          }`}
        >
          Tagesplanung
        </button>
        <button
          onClick={() => setTab("users")}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            tab === "users"
              ? "bg-white dark:bg-slate-700 text-gray-900 dark:text-white shadow-sm"
              : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          }`}
        >
          User-Verwaltung
        </button>
      </div>

      {tab === "day" ? <DayPlanningTab /> : <UserManagementTab />}
    </div>
  );
}
