<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  todayData, members, rfidCards, presets,
  fetchToday, fetchMembers, fetchRfidCards, fetchPresets,
  doSaveMenu, doAddGuest, doRemoveGuest, doAssignRfid, doRemoveRfid,
  doAddPreset, doDeletePreset, doAdminRegister, showToast, loggedIn,
} from '../store'
import { saveMenu, deleteMenu } from '../api'
import type { Member } from '../types'

/* ── Tab-Navigation ─────────────────────────────────────────────────────── */
const tabs = [
  { id: 'tagesplanung', label: 'Tagesplanung', icon: 'ph-calendar-check' },
  { id: 'mitglieder', label: 'Mitglieder', icon: 'ph-users' },
  { id: 'rfid', label: 'RFID-Karten', icon: 'ph-contactless-payment' },
  { id: 'presets', label: 'Menü-Vorlagen', icon: 'ph-book-bookmark' },
]
const activeTab = ref('tagesplanung')

/* ── Menü-Formular ──────────────────────────────────────────────────────── */
const menuForm = ref({
  beschreibung: '',
  zwei_menues: false,
  menu1_name: '',
  menu2_name: '',
  anmeldefrist: '19:45',
  frist_aktiv: true,
})

function resetMenuForm() {
  const menu = todayData.value?.menu
  if (menu) {
    menuForm.value = {
      beschreibung: menu.beschreibung || '',
      zwei_menues: menu.zwei_menues || false,
      menu1_name: menu.menu1_name || '',
      menu2_name: menu.menu2_name || '',
      anmeldefrist: menu.anmeldefrist || '19:45',
      frist_aktiv: menu.frist_aktiv ?? true,
    }
  } else {
    menuForm.value = { beschreibung: '', zwei_menues: false, menu1_name: '', menu2_name: '', anmeldefrist: '19:45', frist_aktiv: true }
  }
}

async function submitMenu() {
  try {
    const today = new Date().toISOString().split('T')[0]
    await saveMenu({ datum: today, ...menuForm.value })
    showToast('Menü gespeichert', 'success')
    fetchToday()
  } catch {
    showToast('Fehler beim Speichern', 'error')
  }
}

async function removeMenu() {
  if (!confirm('Menü für heute löschen?')) return
  try {
    await deleteMenu(new Date().toISOString().split('T')[0])
    showToast('Menü gelöscht', 'success')
    fetchToday()
    resetMenuForm()
  } catch { showToast('Fehler', 'error') }
}

/* ── Preset anwenden ────────────────────────────────────────────────────── */
function applyPreset(name: string) {
  menuForm.value.beschreibung = name
}

/* ── Mitglieder ─────────────────────────────────────────────────────────── */
const memberSearch = ref('')
const filteredMembers = computed(() => {
  const q = memberSearch.value.toLowerCase()
  if (!q) return members.value
  return members.value.filter(m => m.name.toLowerCase().includes(q))
})

async function toggleMember(m: Member) {
  try {
    const menu = todayData.value?.menu
    let menuChoice = 1
    if (menu?.zwei_menues) {
      const choice = prompt(`Menü wählen:\n1 = ${menu.menu1_name || 'Menü 1'}\n2 = ${menu.menu2_name || 'Menü 2'}`, '1')
      if (!choice) return
      menuChoice = parseInt(choice) || 1
    }
    await doAdminRegister(m.id, menuChoice)
    fetchToday()
    fetchMembers()
  } catch { /* handled */ }
}

/* ── RFID ───────────────────────────────────────────────────────────────── */
const rfidForm = ref({ card_id: '', member_id: '' })
const rfidListening = ref(false)
const rfidBuffer = ref('')

function startRfidListen() {
  rfidListening.value = true
  rfidBuffer.value = ''
  document.addEventListener('keydown', onRfidKey, true)
}

function stopRfidListen() {
  rfidListening.value = false
  document.removeEventListener('keydown', onRfidKey, true)
}

function onRfidKey(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    if (rfidBuffer.value.length >= 3) {
      rfidForm.value.card_id = rfidBuffer.value
      stopRfidListen()
    }
    rfidBuffer.value = ''
    return
  }
  if (e.key.length === 1) {
    e.preventDefault()
    rfidBuffer.value += e.key
  }
}

async function submitRfid() {
  if (!rfidForm.value.card_id || !rfidForm.value.member_id) {
    showToast('Karten-ID und Mitglied erforderlich', 'error')
    return
  }
  try {
    await doAssignRfid(rfidForm.value.member_id, rfidForm.value.card_id)
    rfidForm.value = { card_id: '', member_id: '' }
    fetchRfidCards()
  } catch { /* handled */ }
}

async function removeCard(cardId: string) {
  if (!confirm('RFID-Karte wirklich entfernen?')) return
  await doRemoveRfid(cardId)
  fetchRfidCards()
}

/* ── Presets ────────────────────────────────────────────────────────────── */
const newPresetName = ref('')

async function submitPreset() {
  const name = newPresetName.value.trim()
  if (!name) return
  await doAddPreset(name)
  newPresetName.value = ''
  fetchPresets()
}

async function removePreset(id: string) {
  if (!confirm('Vorlage löschen?')) return
  await doDeletePreset(id)
  fetchPresets()
}

/* ── Init ───────────────────────────────────────────────────────────────── */
onMounted(() => {
  fetchToday()
  fetchMembers()
  fetchRfidCards()
  fetchPresets()
  resetMenuForm()
})

watch(() => todayData.value?.menu, () => resetMenuForm())
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-6">
      <i class="ph ph-gear-six text-orange-500"></i>
      Administration
    </h1>

    <!-- Tabs -->
    <div class="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 mb-6 overflow-x-auto">
      <button v-for="tab in tabs" :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors',
                activeTab === tab.id
                  ? 'bg-white dark:bg-gray-700 text-orange-600 dark:text-orange-400 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              ]">
        <i :class="['ph', tab.icon]"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- ═══ Tab: Tagesplanung ═══ -->
    <div v-if="activeTab === 'tagesplanung'" class="space-y-6">
      <!-- Menü-Formular -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <i class="ph ph-cooking-pot"></i> Heutiges Menü
        </h3>
        <form @submit.prevent="submitMenu" class="space-y-4">
          <!-- Preset-Schnellwahl -->
          <div v-if="presets.length" class="flex flex-wrap gap-2">
            <button v-for="p in presets" :key="p.id" type="button"
                    @click="applyPreset(p.name)"
                    class="px-3 py-1 rounded-full text-xs font-medium bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 hover:bg-orange-200 dark:hover:bg-orange-900/50 transition-colors">
              {{ p.name }}
            </button>
          </div>

          <div>
            <label class="label">Beschreibung</label>
            <input v-model="menuForm.beschreibung" type="text" class="input" :disabled="menuForm.zwei_menues"
                   placeholder="z.B. Schnitzel mit Pommes" />
          </div>

          <div class="flex items-center gap-2">
            <input type="checkbox" v-model="menuForm.zwei_menues" id="admin-zwei" class="rounded">
            <label for="admin-zwei" class="text-sm text-gray-700 dark:text-gray-300">Zwei Menüs</label>
          </div>

          <div v-if="menuForm.zwei_menues" class="grid grid-cols-2 gap-3">
            <div><label class="label">Menü 1</label><input v-model="menuForm.menu1_name" class="input" /></div>
            <div><label class="label">Menü 2</label><input v-model="menuForm.menu2_name" class="input" /></div>
          </div>

          <div class="flex items-center gap-2">
            <input type="checkbox" v-model="menuForm.frist_aktiv" id="admin-frist" class="rounded">
            <label for="admin-frist" class="text-sm text-gray-700 dark:text-gray-300">Anmeldefrist aktiv</label>
          </div>
          <div v-if="menuForm.frist_aktiv">
            <label class="label">Frist bis</label>
            <input v-model="menuForm.anmeldefrist" type="time" class="input w-40" />
          </div>

          <div class="flex gap-3">
            <button type="submit" class="btn-primary text-sm">
              <i class="ph ph-check"></i> Speichern
            </button>
            <button v-if="todayData?.menu" type="button" @click="removeMenu"
                    class="btn-ghost text-red-600 text-sm">
              <i class="ph ph-trash"></i> Löschen
            </button>
          </div>
        </form>
      </div>

      <!-- Aktuelle Anmeldungen -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <i class="ph ph-users"></i> Heutige Anmeldungen ({{ todayData?.registrations?.length || 0 }})
        </h3>
        <div v-if="!todayData?.registrations?.length" class="text-gray-400 text-sm py-2">
          Noch keine Anmeldungen
        </div>
        <ul v-else class="divide-y divide-gray-100 dark:divide-gray-700 max-h-64 overflow-y-auto">
          <li v-for="r in todayData?.registrations" :key="r.id"
              class="py-2 flex items-center justify-between text-sm">
            <span class="text-gray-900 dark:text-white">{{ r.member_name }}</span>
            <span v-if="todayData?.menu?.zwei_menues"
                  :class="r.menu_wahl === 1 ? 'text-orange-500' : 'text-blue-500'"
                  class="text-xs font-medium">
              Menü {{ r.menu_wahl }}
            </span>
          </li>
        </ul>
      </div>
    </div>

    <!-- ═══ Tab: Mitglieder ═══ -->
    <div v-if="activeTab === 'mitglieder'" class="space-y-4">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            <i class="ph ph-users"></i> Mitglieder ({{ members.length }})
          </h3>
          <input v-model="memberSearch" type="search" placeholder="Suchen…" class="input w-48 text-sm" />
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                <th class="pb-2 font-medium">Name</th>
                <th class="pb-2 font-medium text-center">RFID</th>
                <th class="pb-2 font-medium text-center">Heute</th>
                <th class="pb-2 font-medium text-right">Aktion</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
              <tr v-for="m in filteredMembers" :key="m.id" class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td class="py-2 text-gray-900 dark:text-white">{{ m.name }}</td>
                <td class="py-2 text-center">
                  <i :class="m.has_rfid ? 'ph-fill ph-check-circle text-green-500' : 'ph ph-minus-circle text-gray-300'" class="text-lg"></i>
                </td>
                <td class="py-2 text-center">
                  <span v-if="m.registered_today" class="text-green-600 dark:text-green-400 font-medium">✓</span>
                  <span v-else class="text-gray-300">–</span>
                </td>
                <td class="py-2 text-right">
                  <button @click="toggleMember(m)"
                          :class="m.registered_today ? 'text-red-500 hover:text-red-600' : 'text-green-600 hover:text-green-700'"
                          class="text-xs font-medium">
                    {{ m.registered_today ? 'Abmelden' : 'Anmelden' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ═══ Tab: RFID ═══ -->
    <div v-if="activeTab === 'rfid'" class="space-y-4">
      <!-- Neue Karte -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <i class="ph ph-plus-circle"></i> Neue RFID-Karte zuweisen
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
          <div>
            <label class="label">Karten-ID</label>
            <div class="flex gap-2">
              <input v-model="rfidForm.card_id" class="input flex-1" placeholder="Karte scannen…" />
              <button @click="rfidListening ? stopRfidListen() : startRfidListen()"
                      :class="rfidListening ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'"
                      class="px-3 py-2 rounded-lg text-white text-sm">
                <i :class="rfidListening ? 'ph ph-stop' : 'ph ph-contactless-payment'"></i>
              </button>
            </div>
            <p v-if="rfidListening" class="text-xs text-blue-500 mt-1 animate-pulse">
              Warte auf RFID-Scan…
            </p>
          </div>
          <div>
            <label class="label">Mitglied</label>
            <select v-model="rfidForm.member_id" class="input">
              <option value="">Bitte wählen…</option>
              <option v-for="m in members" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </div>
          <button @click="submitRfid" class="btn-primary text-sm h-[42px]"
                  :disabled="!rfidForm.card_id || !rfidForm.member_id">
            <i class="ph ph-check"></i> Zuweisen
          </button>
        </div>
      </div>

      <!-- Bestehende Karten -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <i class="ph ph-cards"></i> Zugewiesene Karten ({{ rfidCards.length }})
        </h3>
        <div v-if="rfidCards.length === 0" class="text-gray-400 text-sm py-2">
          Noch keine RFID-Karten zugewiesen
        </div>
        <ul v-else class="divide-y divide-gray-100 dark:divide-gray-700">
          <li v-for="c in rfidCards" :key="c.id" class="py-3 flex items-center justify-between">
            <div>
              <span class="text-gray-900 dark:text-white font-medium">{{ c.member_name }}</span>
              <span class="ml-2 text-xs text-gray-400 font-mono">{{ c.card_id }}</span>
            </div>
            <button @click="removeCard(c.card_id)" class="text-red-500 hover:text-red-600 text-sm">
              <i class="ph ph-trash"></i>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- ═══ Tab: Presets ═══ -->
    <div v-if="activeTab === 'presets'" class="space-y-4">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <i class="ph ph-book-bookmark"></i> Menü-Vorlagen
        </h3>
        <form @submit.prevent="submitPreset" class="flex gap-3 mb-4">
          <input v-model="newPresetName" class="input flex-1" placeholder="Neue Vorlage (z.B. Schnitzel)" />
          <button type="submit" class="btn-primary text-sm" :disabled="!newPresetName.trim()">
            <i class="ph ph-plus"></i> Hinzufügen
          </button>
        </form>
        <ul class="divide-y divide-gray-100 dark:divide-gray-700">
          <li v-for="p in presets" :key="p.id" class="py-3 flex items-center justify-between">
            <span class="text-gray-900 dark:text-white">{{ p.name }}</span>
            <button @click="removePreset(p.id)" class="text-red-500 hover:text-red-600 text-sm">
              <i class="ph ph-trash"></i>
            </button>
          </li>
        </ul>
        <div v-if="presets.length === 0" class="text-gray-400 text-sm py-2">
          Noch keine Vorlagen angelegt
        </div>
      </div>
    </div>
  </div>
</template>
