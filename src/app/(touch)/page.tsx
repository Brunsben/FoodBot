"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

interface MenuData {
  menu: {
    description: string;
    zweiMenuesAktiv: boolean;
    menu1Name: string | null;
    menu2Name: string | null;
    registrationDeadline: string;
    deadlineEnabled: boolean;
  } | null;
  registrationCount: number;
}

interface StatusPopup {
  type: "success" | "error";
  message: string;
}

export default function TouchPage() {
  const [manualInput, setManualInput] = useState("");
  const [status, setStatus] = useState<StatusPopup | null>(null);
  const [menuChoice, setMenuChoice] = useState<number | null>(null);
  const [pendingIdentifier, setPendingIdentifier] = useState<{
    card_id?: string;
    personal_number?: string;
  } | null>(null);
  const bufferRef = useRef("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data, mutate } = useSWR<MenuData>("/food/api/menu/data", fetcher, {
    refreshInterval: 10000,
  });

  const showStatus = useCallback(
    (type: "success" | "error", message: string) => {
      setStatus({ type, message });
      setTimeout(() => setStatus(null), 3000);
    },
    [],
  );

  const doRegister = useCallback(
    async (
      identifier: { card_id?: string; personal_number?: string },
      choice?: number,
    ) => {
      try {
        const res = await fetch("/food/api/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...identifier, menu_choice: choice || 1 }),
        });
        const result = await res.json();
        if (res.ok) {
          showStatus("success", result.message || "Anmeldung erfolgreich");
          mutate();
        } else {
          showStatus("error", result.error || "Fehler bei der Anmeldung");
        }
      } catch {
        showStatus("error", "Verbindungsfehler");
      }
    },
    [showStatus, mutate],
  );

  const processInput = useCallback(
    (input: string) => {
      const trimmed = input.trim();
      if (!trimmed) return;

      const identifier = /^\d+$/.test(trimmed)
        ? { personal_number: trimmed }
        : { card_id: trimmed };

      if (data?.menu?.zweiMenuesAktiv) {
        setPendingIdentifier(identifier);
        setMenuChoice(null);
      } else {
        doRegister(identifier);
      }
    },
    [data, doRegister],
  );

  // RFID scanner keyboard listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if focus is on the manual input field
      if ((e.target as HTMLElement)?.tagName === "INPUT") return;

      if (e.key === "Enter") {
        e.preventDefault();
        const input = bufferRef.current;
        bufferRef.current = "";
        if (timerRef.current) clearTimeout(timerRef.current);
        processInput(input);
      } else if (e.key.length === 1) {
        bufferRef.current += e.key;
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => {
          bufferRef.current = "";
        }, 500);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [processInput]);

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    processInput(manualInput);
    setManualInput("");
  };

  const handleMenuChoiceSelect = (choice: number) => {
    if (pendingIdentifier) {
      doRegister(pendingIdentifier, choice);
      setPendingIdentifier(null);
      setMenuChoice(choice);
    }
  };

  const enterFullscreen = () => {
    document.documentElement.requestFullscreen?.();
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 select-none">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold dark:text-white">Essensanmeldung</h1>
        <p className="text-2xl mt-2 text-gray-600 dark:text-gray-400">
          {data?.registrationCount ?? 0} Anmeldungen
        </p>
      </div>

      {/* Menu display */}
      {data?.menu ? (
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6 mb-8 w-full max-w-lg text-center">
          <h2 className="text-xl font-semibold mb-2">Heutiges Menü</h2>
          <p className="text-lg text-gray-700 dark:text-gray-300">
            {data.menu.description}
          </p>
          {data.menu.zweiMenuesAktiv && (
            <div className="mt-3 flex gap-4 justify-center text-sm">
              <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full">
                Menü 1: {data.menu.menu1Name || "Standard"}
              </span>
              <span className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-3 py-1 rounded-full">
                Menü 2: {data.menu.menu2Name || "Alternativ"}
              </span>
            </div>
          )}
          {data.menu.deadlineEnabled && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              Anmeldeschluss: {data.menu.registrationDeadline} Uhr
            </p>
          )}
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6 mb-8 w-full max-w-lg text-center">
          <p className="text-gray-500 dark:text-gray-400">
            Kein Menü für heute eingetragen
          </p>
        </div>
      )}

      {/* Scanner area */}
      <div className="bg-blue-50 dark:bg-slate-800 border-2 border-dashed border-blue-300 dark:border-blue-700 rounded-2xl p-8 mb-6 w-full max-w-lg text-center">
        <p className="text-xl text-blue-700 dark:text-blue-300 font-medium">
          Karte an den Scanner halten
        </p>
        <p className="text-sm text-blue-500 dark:text-blue-400 mt-1">
          RFID / Barcode
        </p>
      </div>

      {/* Manual input */}
      <form onSubmit={handleManualSubmit} className="w-full max-w-lg mb-6">
        <div className="flex gap-3">
          <input
            type="text"
            value={manualInput}
            onChange={(e) => setManualInput(e.target.value)}
            placeholder="Personalnummer eingeben..."
            className="flex-1 text-xl p-4 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white text-xl font-semibold rounded-xl transition-colors"
          >
            OK
          </button>
        </div>
      </form>

      {/* Fullscreen button */}
      <button
        onClick={enterFullscreen}
        className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
      >
        Vollbild
      </button>

      {/* Status popup */}
      {status && (
        <div
          className={`fixed top-8 left-1/2 -translate-x-1/2 px-8 py-4 rounded-xl text-xl font-semibold shadow-2xl z-50 transition-all ${
            status.type === "success"
              ? "bg-green-500 text-white"
              : "bg-red-500 text-white"
          }`}
        >
          {status.message}
        </div>
      )}

      {/* Menu choice overlay */}
      {pendingIdentifier && data?.menu?.zweiMenuesAktiv && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-40">
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
            <h3 className="text-2xl font-bold text-center mb-6 dark:text-white">
              Menü wählen
            </h3>
            <div className="flex gap-4">
              <button
                onClick={() => handleMenuChoiceSelect(1)}
                className="flex-1 py-6 bg-blue-600 hover:bg-blue-700 text-white text-xl font-bold rounded-xl transition-colors"
              >
                {data.menu.menu1Name || "Menü 1"}
              </button>
              <button
                onClick={() => handleMenuChoiceSelect(2)}
                className="flex-1 py-6 bg-green-600 hover:bg-green-700 text-white text-xl font-bold rounded-xl transition-colors"
              >
                {data.menu.menu2Name || "Menü 2"}
              </button>
            </div>
            <button
              onClick={() => setPendingIdentifier(null)}
              className="w-full mt-4 py-3 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
            >
              Abbrechen
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
