// ── FoodBot Zentraler Store ────────────────────────────────────────────────
// Modul-Level-Singletons (analog PSA-Frontend)

import { ref, reactive, computed } from 'vue'
import {
  login as apiLogin, checkAuth, getJwt, setJwt, clearJwt,
  getToday, getKitchenData, getMenuToday, register,
  getMembers, saveMenu, getStats, getHistory, getMemberHistory,
  getRfidCards, assignRfidCard, removeRfidCard as apiRemoveRfidCard,
  getPresets, addPreset as apiAddPreset, deletePreset as apiDeletePreset,
  getWeeklyPlan, saveWeeklyDay, deleteWeeklyDay,
  addGuest, removeGuest, setGuests,
  adminRegister, getPrintData,
} from './api/index'
import { safeJsonParse, todayStr } from './utils/formatters'
import type { Member, TodayData, KitchenData, AppUser } from './types/index'

// ── UI-Zustand ─────────────────────────────────────────────────────────────
export const page        = ref('touch')
export const sidebarOpen = ref(false)
export const loading     = ref(false)
export const toast       = reactive({ show: false, msg: '', type: 'ok' as 'ok' | 'error' })

export function showToast(msg: string, type: 'ok' | 'error' | 'success' = 'ok') {
  toast.msg = msg; toast.type = type === 'success' ? 'ok' : type; toast.show = true
  setTimeout(() => { toast.show = false }, 3000)
}

export async function load(fn: () => Promise<void>) {
  loading.value = true
  try { await fn() }
  catch (e: any) { showToast(e?.message || String(e), 'error') }
  finally { loading.value = false }
}

// ── Dark Mode ──────────────────────────────────────────────────────────────
export const darkMode = ref(document.documentElement.classList.contains('dark'))
export function toggleDark() {
  darkMode.value = !darkMode.value
  document.documentElement.classList.toggle('dark', darkMode.value)
  localStorage.setItem('darkMode', String(darkMode.value))
}

// ── Auth ───────────────────────────────────────────────────────────────────
export const loggedIn    = ref(!!getJwt())
export const currentUser = ref<AppUser | null>(
  safeJsonParse('foodbot_user', null) || (getJwt() ? { role: 'admin' } : null)
)

window.addEventListener('foodbot:unauthorized', () => {
  clearJwt()
  localStorage.removeItem('foodbot_user')
  localStorage.removeItem('fw_jwt')
  localStorage.removeItem('fw_user')
  loggedIn.value    = false
  currentUser.value = null
  page.value = 'touch'
  showToast('Sitzung abgelaufen', 'error')
})

export const loginForm = reactive({ password: '', error: '' })

export async function doLogin() {
  loginForm.error = ''
  try {
    const res = await apiLogin(loginForm.password)
    setJwt(res.token)
    const user: AppUser = { role: 'admin' }
    localStorage.setItem('foodbot_user', JSON.stringify(user))
    currentUser.value = user
    loggedIn.value = true
    loginForm.password = ''
    page.value = 'admin'
    showToast('Angemeldet')
  } catch (e: any) {
    loginForm.error = e?.message || 'Login fehlgeschlagen'
  }
}

export function doLogout() {
  clearJwt()
  localStorage.removeItem('foodbot_user')
  localStorage.removeItem('fw_jwt')
  localStorage.removeItem('fw_user')
  loggedIn.value    = false
  currentUser.value = null
  page.value = 'touch'
  showToast('Abgemeldet')
  window.location.href = '/'
}

// ── Feuerwehr-Name ─────────────────────────────────────────────────────────
export const feuerwehrName = window.CONFIG?.feuerwehrName || 'FF Wietmarschen'

// ── Navigation ─────────────────────────────────────────────────────────────
export const publicPages = [
  { id: 'touch',   label: 'Anmeldung',  iconClass: 'ph ph-hand-tap' },
  { id: 'kitchen', label: 'Küche',      iconClass: 'ph ph-cooking-pot' },
]

export const adminPages = [
  { id: 'admin',   label: 'Verwaltung', iconClass: 'ph ph-gear' },
  { id: 'weekly',  label: 'Wochenplan', iconClass: 'ph ph-calendar' },
  { id: 'stats',   label: 'Statistiken', iconClass: 'ph ph-chart-bar' },
  { id: 'history', label: 'Historie',   iconClass: 'ph ph-clock-counter-clockwise' },
]

export const visiblePages = computed(() => {
  if (loggedIn.value) return [...publicPages, ...adminPages]
  return publicPages
})

// ── Daten ──────────────────────────────────────────────────────────────────
export const todayData     = ref<TodayData | null>(null)
export const kitchenData   = ref<KitchenData | null>(null)
export const members       = ref<Member[]>([])
export const rfidCards     = ref<any[]>([])
export const presets       = ref<any[]>([])
export const statsData     = ref<any[]>([])
export const historyData   = ref<any>(null)
export const weeklyData    = ref<any[]>([])

// ── Daten laden ────────────────────────────────────────────────────────────
export async function fetchToday() {
  todayData.value = await getToday()
}

export async function fetchKitchen() {
  kitchenData.value = await getKitchenData()
}

export async function fetchMembers() {
  members.value = await getMembers()
}

export async function fetchRfidCards() {
  rfidCards.value = await getRfidCards()
}

export async function fetchPresets() {
  presets.value = await getPresets()
}

export async function fetchStats(days = 14) {
  statsData.value = await getStats(days)
}

export async function fetchHistory() {
  historyData.value = await getHistory()
}

export async function fetchWeekly() {
  weeklyData.value = await getWeeklyPlan()
}

/** Lade Admin-Daten (Mitglieder, RFID, Presets) */
export async function fetchAdminData() {
  await Promise.all([fetchMembers(), fetchRfidCards(), fetchPresets()])
}

// ── Aktionen ───────────────────────────────────────────────────────────────

export async function doRegister(params: { personalnummer?: string; rfid?: string; menu_choice?: number }) {
  const res = await register(params)
  return res
}

export async function doSaveMenu(data: Parameters<typeof saveMenu>[0]) {
  await saveMenu(data)
  showToast('Menü gespeichert')
}

export async function doAddGuest(datum: string, menuWahl: number) {
  await addGuest(datum, menuWahl)
}

export async function doRemoveGuest(datum: string, menuWahl: number) {
  await removeGuest(datum, menuWahl)
}



export async function doAssignRfid(memberId: string, cardId: string) {
  await assignRfidCard(memberId, cardId)
  showToast('RFID-Karte zugewiesen')
  await fetchRfidCards()
}

export async function doRemoveRfid(cardId: string) {
  await apiRemoveRfidCard(cardId)
  showToast('RFID-Karte entfernt')
  await fetchRfidCards()
}

export async function doAddPreset(name: string) {
  await apiAddPreset(name)
  showToast('Preset hinzugefügt')
  await fetchPresets()
}

export async function doDeletePreset(id: string) {
  await apiDeletePreset(id)
  showToast('Preset gelöscht')
  await fetchPresets()
}

export async function doSaveWeeklyDay(datum: string, formData: Record<string, any>) {
  await saveWeeklyDay({ datum, ...formData } as any)
  showToast('Tag gespeichert')
  await fetchWeekly()
}

export async function doDeleteWeeklyDay(datum: string) {
  await deleteWeeklyDay(datum)
  showToast('Tag gelöscht')
  await fetchWeekly()
}

export async function doAdminRegister(memberId: string, menuChoice?: number) {
  const res = await adminRegister(memberId, menuChoice)
  return res
}
