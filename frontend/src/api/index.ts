// ── FoodBot API-Layer ──────────────────────────────────────────────────────
// JWT + Session Auth, Fetch-Wrapper

const API = () => window.CONFIG?.api || '/api'

// ── JWT ───────────────────────────────────────────────────────────────────
export const getJwt   = (): string | null => localStorage.getItem('foodbot_jwt') || localStorage.getItem('fw_jwt')
export const setJwt   = (token: string) => localStorage.setItem('foodbot_jwt', token)
export const clearJwt = () => localStorage.removeItem('foodbot_jwt')

function authHeaders(): Record<string, string> {
  const token = getJwt()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// ── Generischer Fetch ─────────────────────────────────────────────────────
export async function api<T = unknown>(
  method: string,
  path: string,
  body?: unknown,
  extraHeaders: Record<string, string> = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...authHeaders(),
    ...extraHeaders,
  }
  const r = await fetch(`${API()}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (r.status === 401) {
    clearJwt()
    window.dispatchEvent(new CustomEvent('foodbot:unauthorized'))
    throw new Error('Sitzung abgelaufen – bitte neu anmelden')
  }
  if (!r.ok) {
    const err = await r.json().catch(() => ({})) as { error?: string; message?: string }
    throw new Error(err.error || err.message || `Fehler ${r.status}`)
  }
  if (r.status === 204) return null as T
  return r.json()
}

// ── Öffentliche Endpoints (kein Auth) ─────────────────────────────────────

/** Tages-Status: Menü, Anmeldungen, Gäste */
export const getToday = () => api<any>('GET', '/today')

/** Küchen-Livedaten */
export const getKitchenData = () => api<any>('GET', '/kitchen/data')

/** Menü für heute (Polling Touch) */
export const getMenuToday = () => api<any>('GET', '/menu/today')

/** Registrierung: An-/Abmelden per Personalnummer oder RFID */
export const register = (data: {
  personalnummer?: string
  rfid?: string
  menu_choice?: number
}) => api<any>('POST', '/register', data)

/** Statistiken (letzte N Tage) */
export const getStats = (days = 14) => api<any>('GET', `/stats?days=${days}`)

// ── Auth ──────────────────────────────────────────────────────────────────

/** Admin-Login */
export const login = (password: string) =>
  api<{ token: string }>('POST', '/auth/login', { password })

/** Session prüfen */
export const checkAuth = () => api<{ authenticated: boolean }>('GET', '/auth/check')

// ── Admin-Endpoints (Auth required) ───────────────────────────────────────

/** Alle Mitglieder (aus fw_common.members) */
export const getMembers = () => api<any[]>('GET', '/members')

/** Menü für ein Datum speichern/aktualisieren */
export const saveMenu = (data: {
  datum: string
  beschreibung: string
  zwei_menues?: boolean
  menu1_name?: string
  menu2_name?: string
  anmeldefrist?: string
  frist_aktiv?: boolean
}) => api<any>('POST', '/menu', data)

/** Menü löschen */
export const deleteMenu = (datum: string) =>
  api<void>('DELETE', `/menu/${datum}`)

/** Gäste setzen */
export const setGuests = (datum: string, menuWahl: number, anzahl: number) =>
  api<any>('POST', '/guests', { datum, menu_wahl: menuWahl, anzahl })

/** Gäste +1 */
export const addGuest = (datumOrOpts: string | { datum?: string; menu_wahl: number }, menuWahl?: number) => {
  const opts = typeof datumOrOpts === 'string'
    ? { datum: datumOrOpts, menu_wahl: menuWahl! }
    : { datum: datumOrOpts.datum || new Date().toISOString().split('T')[0], menu_wahl: datumOrOpts.menu_wahl }
  return api<any>('POST', '/guests/add', opts)
}

/** Gäste -1 */
export const removeGuest = (datumOrOpts: string | { datum?: string; menu_wahl: number }, menuWahl?: number) => {
  const opts = typeof datumOrOpts === 'string'
    ? { datum: datumOrOpts, menu_wahl: menuWahl! }
    : { datum: datumOrOpts.datum || new Date().toISOString().split('T')[0], menu_wahl: datumOrOpts.menu_wahl }
  return api<any>('POST', '/guests/remove', opts)
}

/** RFID-Karten auflisten */
export const getRfidCards = () => api<any[]>('GET', '/rfid')

/** RFID-Karte zuweisen */
export const assignRfidCard = (memberId: string, cardId: string) =>
  api<any>('POST', '/rfid', { member_id: memberId, card_id: cardId })

/** RFID-Karte entfernen */
export const removeRfidCard = (cardId: string) =>
  api<void>('DELETE', `/rfid/${cardId}`)

/** Preset-Menüs auflisten */
export const getPresets = () => api<any[]>('GET', '/presets')

/** Preset-Menü hinzufügen */
export const addPreset = (name: string) =>
  api<any>('POST', '/presets', { name })

/** Preset-Menü löschen */
export const deletePreset = (id: string) =>
  api<void>('DELETE', `/presets/${id}`)

/** Wochenplan (14 Tage) */
export const getWeeklyPlan = () => api<any[]>('GET', '/weekly')

/** Tag im Wochenplan speichern */
export const saveWeeklyDay = (data: {
  datum: string
  beschreibung: string
  zwei_menues?: boolean
  menu1_name?: string
  menu2_name?: string
  anmeldefrist?: string
  frist_aktiv?: boolean
}) => api<any>('POST', `/weekly/${data.datum}`, data)

/** Tag aus Wochenplan löschen */
export const deleteWeeklyDay = (datum: string) =>
  api<void>('DELETE', `/weekly/${datum}`)

/** Historie-Übersicht */
export const getHistory = () => api<any>('GET', '/history')

/** Mitglied-Detail-Historie */
export const getMemberHistory = (memberId: string, page = 1) =>
  api<any>('GET', `/history/${memberId}?page=${page}`)

/** Admin Mitglied an-/abmelden */
export const adminRegister = (memberId: string, menuChoice?: number) =>
  api<any>('POST', '/admin/register', { member_id: memberId, menu_choice: menuChoice })

/** Admin-Log */
export const getAdminLog = () => api<any[]>('GET', '/system/log')

/** Druckliste-Daten */
export const getPrintData = () => api<any>('GET', '/kitchen/print-data')

// ── Mobile (Token-basiert, kein Auth) ─────────────────────────────────────

/** Mobile Status */
export const getMobileStatus = (token: string) =>
  api<any>('GET', `/mobile/${token}`)

/** Mobile Registrierung */
export const mobileRegister = (token: string, menuChoice?: number) =>
  api<any>('POST', `/mobile/${token}`, { menu_choice: menuChoice })
