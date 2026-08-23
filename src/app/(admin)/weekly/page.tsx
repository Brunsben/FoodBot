"use client";

import { useState } from "react";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

interface DayPlan {
  id: number;
  date: string;
  description: string;
  zweiMenuesAktiv: boolean;
  menu1Name: string | null;
  menu2Name: string | null;
  registrationDeadline: string;
  deadlineEnabled: boolean;
}

export default function WeeklyPage() {
  const { data: days, mutate } = useSWR<DayPlan[]>(
    "/food/api/admin/weekly",
    fetcher,
  );
  const [newDate, setNewDate] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<Partial<DayPlan>>({});

  const handleAddDay = async () => {
    if (!newDate) return;
    await fetch("/food/api/admin/weekly", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date: newDate }),
    });
    setNewDate("");
    mutate();
  };

  const handleSave = async (id: number) => {
    await fetch(`/food/api/admin/weekly/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(editForm),
    });
    setEditingId(null);
    setEditForm({});
    mutate();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Tag wirklich löschen?")) return;
    await fetch(`/food/api/admin/weekly/${id}`, { method: "DELETE" });
    mutate();
  };

  const startEdit = (day: DayPlan) => {
    setEditingId(day.id);
    setEditForm({
      description: day.description,
      zweiMenuesAktiv: day.zweiMenuesAktiv,
      menu1Name: day.menu1Name,
      menu2Name: day.menu2Name,
      registrationDeadline: day.registrationDeadline,
      deadlineEnabled: day.deadlineEnabled,
    });
  };

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString("de-DE", {
      weekday: "short",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold dark:text-white">Wochenplan</h1>

      {/* Add new day */}
      <div className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex gap-3 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Neuen Tag hinzufügen
            </label>
            <input
              type="date"
              value={newDate}
              onChange={(e) => setNewDate(e.target.value)}
              className="p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>
          <button
            onClick={handleAddDay}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            Hinzufügen
          </button>
        </div>
      </div>

      {/* Day cards */}
      <div className="space-y-4">
        {days?.map((day) => (
          <div
            key={day.id}
            className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-lg dark:text-white">
                  {formatDate(day.date)}
                </h3>
                {editingId !== day.id && (
                  <p className="text-gray-600 dark:text-gray-400 mt-1">
                    {day.description || "Kein Menü eingetragen"}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                {editingId === day.id ? (
                  <button
                    onClick={() => handleSave(day.id)}
                    className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    Speichern
                  </button>
                ) : (
                  <button
                    onClick={() => startEdit(day)}
                    className="px-3 py-1.5 bg-gray-200 dark:bg-slate-600 hover:bg-gray-300 dark:hover:bg-slate-500 text-sm font-medium rounded-lg transition-colors dark:text-white"
                  >
                    Bearbeiten
                  </button>
                )}
                <button
                  onClick={() => handleDelete(day.id)}
                  className="px-3 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 text-sm font-medium rounded-lg transition-colors"
                >
                  Löschen
                </button>
              </div>
            </div>

            {editingId === day.id && (
              <div className="space-y-3 border-t border-gray-100 dark:border-slate-700 pt-4">
                <input
                  type="text"
                  value={editForm.description ?? ""}
                  onChange={(e) =>
                    setEditForm({ ...editForm, description: e.target.value })
                  }
                  placeholder="Menübeschreibung"
                  className="w-full p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <input
                      type="checkbox"
                      checked={editForm.zweiMenuesAktiv ?? false}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          zweiMenuesAktiv: e.target.checked,
                        })
                      }
                      className="rounded border-gray-300 dark:border-gray-600"
                    />
                    Zwei Menüs
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <input
                      type="checkbox"
                      checked={editForm.deadlineEnabled ?? true}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          deadlineEnabled: e.target.checked,
                        })
                      }
                      className="rounded border-gray-300 dark:border-gray-600"
                    />
                    Deadline
                  </label>
                  {editForm.deadlineEnabled && (
                    <input
                      type="time"
                      value={editForm.registrationDeadline ?? "19:45"}
                      onChange={(e) =>
                        setEditForm({
                          ...editForm,
                          registrationDeadline: e.target.value,
                        })
                      }
                      className="p-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
                    />
                  )}
                </div>
                {editForm.zweiMenuesAktiv && (
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      value={editForm.menu1Name ?? ""}
                      onChange={(e) =>
                        setEditForm({ ...editForm, menu1Name: e.target.value })
                      }
                      placeholder="Menü 1 Name"
                      className="p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                    <input
                      type="text"
                      value={editForm.menu2Name ?? ""}
                      onChange={(e) =>
                        setEditForm({ ...editForm, menu2Name: e.target.value })
                      }
                      placeholder="Menü 2 Name"
                      className="p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Tags */}
            {editingId !== day.id && (
              <div className="flex flex-wrap gap-2 text-xs">
                {day.zweiMenuesAktiv && (
                  <span className="bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-2 py-1 rounded">
                    2 Menüs
                  </span>
                )}
                {day.deadlineEnabled && (
                  <span className="bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 px-2 py-1 rounded">
                    Deadline: {day.registrationDeadline}
                  </span>
                )}
              </div>
            )}
          </div>
        ))}

        {days?.length === 0 && (
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            Noch keine Tage geplant
          </p>
        )}
      </div>
    </div>
  );
}
