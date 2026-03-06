// ── Hilfsfunktionen ───────────────────────────────────────────────────────

/** Datum → "Mo, 06.03.2026" */
export function fmtDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' })
}

/** Datum → "06.03.2026" */
export function fmtDateShort(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

/** Datum → "Montag" */
export function fmtWeekday(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('de-DE', { weekday: 'long' })
}

/** ISO-Datum für heute */
export function todayStr(): string {
  return new Date().toISOString().slice(0, 10)
}

/** Ist Datum heute? */
export function isToday(iso: string): boolean {
  return iso === todayStr()
}

/** JSON aus localStorage sicher parsen */
export function safeJsonParse<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}
