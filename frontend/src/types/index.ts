// ── FoodBot Typen ──────────────────────────────────────────────────────────

export interface Member {
  id: string
  personalnummer: string
  vorname: string
  name: string
  dienstgrad: string
  aktiv: boolean
}

export interface Menu {
  id: string
  datum: string           // ISO date
  beschreibung: string
  zwei_menues: boolean
  menu1_name: string | null
  menu2_name: string | null
  anmeldefrist: string    // "19:45"
  frist_aktiv: boolean
}

export interface Registration {
  id: string
  member_id: string
  datum: string
  menu_wahl: number       // 1 oder 2
  member_name?: string    // joined
  member_personalnummer?: string
}

export interface GuestEntry {
  id: string
  datum: string
  menu_wahl: number
  anzahl: number
}

export interface RfidCard {
  id: string
  card_id: string         // hex string
  member_id: string
  member_name?: string
}

export interface MobileToken {
  id: string
  member_id: string
  token: string
}

export interface PresetMenu {
  id: string
  name: string
  sort_order: number
}

export interface AdminLogEntry {
  id: string
  timestamp: string
  action: string
  details: string
  ip_address: string | null
}

export interface TodayData {
  menu: Menu | null
  registrations: Registration[]
  guests: GuestEntry[]
  total: number
  total_menu1: number
  total_menu2: number
  guest_count: number
  guest_count_menu1: number
  guest_count_menu2: number
  deadline_passed: boolean
  member_count: number
}

export interface KitchenData {
  menu: Menu | null
  registrations: Registration[]
  guests: GuestEntry[]
  total: number
  total_menu1: number
  total_menu2: number
  guest_count: number
  guest_count_menu1: number
  guest_count_menu2: number
}

export interface StatsDay {
  datum: string
  beschreibung: string
  anzahl: number
  gaeste: number
  total: number
}

export interface HistoryMember {
  member_id: string
  name: string
  total: number
  letzte: string | null
}

export interface WeeklyDay {
  datum: string
  menu: Menu | null
  registrations_count: number
}

export interface AppUser {
  role: string
}
