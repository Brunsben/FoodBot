"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface Props {
  user: { id: number; name: string; personalNumber: string };
  menu: {
    description: string;
    zweiMenuesAktiv: boolean;
    menu1Name: string | null;
    menu2Name: string | null;
    registrationDeadline: string;
    deadlineEnabled: boolean;
  } | null;
  initialRegistration: { menuChoice: number } | null;
}

export default function MobileRegistration({ user, menu, initialRegistration }: Props) {
  const [registration, setRegistration] = useState(initialRegistration);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const router = useRouter();

  const showMessage = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleRegister = async (choice: number = 1) => {
    setLoading(true);
    try {
      const res = await fetch("/food/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ personal_number: user.personalNumber, menu_choice: choice }),
      });
      const data = await res.json();
      if (res.ok) {
        setRegistration({ menuChoice: choice });
        showMessage("success", data.message || "Anmeldung erfolgreich");
        router.refresh();
      } else {
        showMessage("error", data.error || "Fehler");
      }
    } catch {
      showMessage("error", "Verbindungsfehler");
    } finally {
      setLoading(false);
    }
  };

  const handleUnregister = async () => {
    setLoading(true);
    try {
      const res = await fetch("/food/api/register", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ personal_number: user.personalNumber }),
      });
      const data = await res.json();
      if (res.ok) {
        setRegistration(null);
        showMessage("success", data.message || "Abmeldung erfolgreich");
        router.refresh();
      } else {
        showMessage("error", data.error || "Fehler");
      }
    } catch {
      showMessage("error", "Verbindungsfehler");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6 w-full max-w-sm">
        {/* User info */}
        <div className="text-center mb-6">
          <p className="text-sm text-gray-500 dark:text-gray-400">Angemeldet als</p>
          <h1 className="text-xl font-bold dark:text-white">{user.name}</h1>
        </div>

        {/* Menu display */}
        {menu ? (
          <div className="bg-gray-50 dark:bg-slate-700 rounded-xl p-4 mb-6">
            <h2 className="font-semibold text-sm text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
              Heutiges Menü
            </h2>
            <p className="text-gray-800 dark:text-gray-200">{menu.description}</p>
            {menu.zweiMenuesAktiv && (
              <div className="flex gap-2 mt-2 text-xs">
                <span className="bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                  1: {menu.menu1Name || "Standard"}
                </span>
                <span className="bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 px-2 py-0.5 rounded">
                  2: {menu.menu2Name || "Alternativ"}
                </span>
              </div>
            )}
            {menu.deadlineEnabled && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Anmeldeschluss: {menu.registrationDeadline} Uhr
              </p>
            )}
          </div>
        ) : (
          <div className="bg-gray-50 dark:bg-slate-700 rounded-xl p-4 mb-6 text-center">
            <p className="text-gray-500 dark:text-gray-400">Kein Menü für heute</p>
          </div>
        )}

        {/* Registration status */}
        <div className="text-center mb-4">
          {registration ? (
            <div className="inline-flex items-center gap-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-4 py-2 rounded-full">
              <span className="w-2 h-2 bg-green-500 rounded-full" />
              Angemeldet {menu?.zweiMenuesAktiv ? `(Menü ${registration.menuChoice})` : ""}
            </div>
          ) : (
            <div className="inline-flex items-center gap-2 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 px-4 py-2 rounded-full">
              <span className="w-2 h-2 bg-gray-400 rounded-full" />
              Nicht angemeldet
            </div>
          )}
        </div>

        {/* Action buttons */}
        {menu && (
          <div className="space-y-3">
            {!registration ? (
              menu.zweiMenuesAktiv ? (
                <div className="flex gap-3">
                  <button
                    onClick={() => handleRegister(1)}
                    disabled={loading}
                    className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors"
                  >
                    {menu.menu1Name || "Menü 1"}
                  </button>
                  <button
                    onClick={() => handleRegister(2)}
                    disabled={loading}
                    className="flex-1 py-3 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors"
                  >
                    {menu.menu2Name || "Menü 2"}
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => handleRegister(1)}
                  disabled={loading}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors"
                >
                  Anmelden
                </button>
              )
            ) : (
              <button
                onClick={handleUnregister}
                disabled={loading}
                className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-semibold rounded-xl transition-colors"
              >
                Abmelden
              </button>
            )}
          </div>
        )}
      </div>

      {/* Status message */}
      {message && (
        <div
          className={`fixed top-4 left-1/2 -translate-x-1/2 px-6 py-3 rounded-xl font-semibold shadow-lg z-50 ${
            message.type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"
          }`}
        >
          {message.text}
        </div>
      )}
    </div>
  );
}
