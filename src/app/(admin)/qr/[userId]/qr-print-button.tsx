"use client";

export default function QRPrintButton() {
  return (
    <button
      onClick={() => window.print()}
      className="px-6 py-2.5 bg-gray-800 dark:bg-gray-200 dark:text-gray-800 text-white font-medium rounded-lg hover:opacity-90 transition-opacity"
    >
      🖨️ Drucken
    </button>
  );
}
