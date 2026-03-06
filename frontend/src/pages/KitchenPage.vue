<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { kitchenData, fetchKitchen, showToast, loggedIn } from '../store'
import { saveMenu, deleteMenu, addGuest, removeGuest, getPrintData } from '../api'
import type { Menu } from '../types'

/* ── State ──────────────────────────────────────────────────────────────── */
const pollTimer = ref<ReturnType<typeof setInterval>>()

/* Menü-Formular */
const showMenuForm = ref(false)
const menuForm = ref({
  beschreibung: '',
  zwei_menues: false,
  menu1_name: '',
  menu2_name: '',
  anmeldefrist: '19:45',
  frist_aktiv: true,
})

/* ── Computed ───────────────────────────────────────────────────────────── */
const data = computed(() => kitchenData.value)
const menu = computed(() => data.value?.menu)
const registrations = computed(() => data.value?.registrations ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalMenu1 = computed(() => data.value?.total_menu1 ?? 0)
const totalMenu2 = computed(() => data.value?.total_menu2 ?? 0)
const guestCountMenu1 = computed(() => data.value?.guest_count_menu1 ?? 0)
const guestCountMenu2 = computed(() => data.value?.guest_count_menu2 ?? 0)
const guestCount = computed(() => data.value?.guest_count ?? 0)
const isZweiMenues = computed(() => menu.value?.zwei_menues ?? false)

const regsMenu1 = computed(() => registrations.value.filter(r => r.menu_wahl === 1))
const regsMenu2 = computed(() => registrations.value.filter(r => r.menu_wahl === 2))

/* ── Menü speichern ─────────────────────────────────────────────────────── */
function openMenuForm() {
  if (menu.value) {
    menuForm.value = {
      beschreibung: menu.value.beschreibung || '',
      zwei_menues: menu.value.zwei_menues || false,
      menu1_name: menu.value.menu1_name || '',
      menu2_name: menu.value.menu2_name || '',
      anmeldefrist: menu.value.anmeldefrist || '19:45',
      frist_aktiv: menu.value.frist_aktiv ?? true,
    }
  } else {
    menuForm.value = {
      beschreibung: '',
      zwei_menues: false,
      menu1_name: '',
      menu2_name: '',
      anmeldefrist: '19:45',
      frist_aktiv: true,
    }
  }
  showMenuForm.value = true
}

async function submitMenu() {
  try {
    await saveMenu({
      datum: new Date().toISOString().split('T')[0],
      ...menuForm.value,
    })
    showMenuForm.value = false
    showToast('Menü gespeichert', 'success')
    fetchKitchen()
  } catch {
    showToast('Fehler beim Speichern', 'error')
  }
}

async function removeMenu() {
  if (!confirm('Menü für heute wirklich löschen?')) return
  try {
    const today = new Date().toISOString().split('T')[0]
    await deleteMenu(today)
    showMenuForm.value = false
    showToast('Menü gelöscht', 'success')
    fetchKitchen()
  } catch {
    showToast('Fehler beim Löschen', 'error')
  }
}

/* ── Gäste ──────────────────────────────────────────────────────────────── */
async function guestPlus(menuWahl: number = 1) {
  try {
    await addGuest({ menu_wahl: menuWahl })
    fetchKitchen()
  } catch { /* */ }
}

async function guestMinus(menuWahl: number = 1) {
  try {
    await removeGuest({ menu_wahl: menuWahl })
    fetchKitchen()
  } catch { /* */ }
}

/* ── Drucken ────────────────────────────────────────────────────────────── */
function doPrint() {
  window.print()
}

/* ── Lifecycle ──────────────────────────────────────────────────────────── */
onMounted(() => {
  fetchKitchen()
  pollTimer.value = setInterval(fetchKitchen, 5000)
})

onUnmounted(() => {
  clearInterval(pollTimer.value)
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <i class="ph ph-cooking-pot text-orange-500"></i>
        Küche
      </h1>
      <div class="flex items-center gap-3">
        <button @click="doPrint"
                class="btn-ghost text-sm flex items-center gap-1 print:hidden">
          <i class="ph ph-printer"></i> Drucken
        </button>
        <button v-if="loggedIn" @click="openMenuForm"
                class="btn-primary text-sm flex items-center gap-1 print:hidden">
          <i class="ph ph-pencil-simple"></i> Menü bearbeiten
        </button>
      </div>
    </div>

    <!-- Menü-Info -->
    <div v-if="menu" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 mb-6">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Heutiges Menü</p>
          <p class="text-xl font-bold text-gray-900 dark:text-white">{{ menu.beschreibung }}</p>
          <div v-if="isZweiMenues" class="mt-2 flex gap-4 text-sm">
            <span class="text-orange-600 dark:text-orange-400">
              <i class="ph ph-number-circle-one"></i> {{ menu.menu1_name }}
            </span>
            <span class="text-blue-600 dark:text-blue-400">
              <i class="ph ph-number-circle-two"></i> {{ menu.menu2_name }}
            </span>
          </div>
        </div>
        <div class="text-right">
          <p class="text-4xl font-bold text-orange-500">{{ total }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400">Gesamt</p>
        </div>
      </div>

      <!-- Zusammenfassung -->
      <div class="mt-4 grid gap-3" :class="isZweiMenues ? 'grid-cols-2' : 'grid-cols-1'">
        <div class="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3 text-center">
          <p class="text-2xl font-bold text-orange-600 dark:text-orange-400">{{ isZweiMenues ? totalMenu1 : total - guestCount }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ isZweiMenues ? (menu.menu1_name || 'Menü 1') : 'Mitglieder' }}</p>
        </div>
        <div v-if="isZweiMenues" class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
          <p class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ totalMenu2 }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ menu.menu2_name || 'Menü 2' }}</p>
        </div>
      </div>
    </div>

    <div v-else class="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-5 mb-6 text-center print:hidden">
      <p class="text-yellow-700 dark:text-yellow-300">Kein Menü für heute</p>
      <button v-if="loggedIn" @click="openMenuForm"
              class="mt-2 btn-primary text-sm">
        <i class="ph ph-plus"></i> Menü eintragen
      </button>
    </div>

    <!-- Gäste -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 mb-6 print:hidden">
      <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
        <i class="ph ph-user-plus"></i> Gäste
      </h3>
      <div class="grid gap-4" :class="isZweiMenues ? 'grid-cols-2' : 'grid-cols-1'">
        <div class="flex items-center justify-center gap-4">
          <button @click="guestMinus(1)" class="touch-btn w-14 h-14 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg text-2xl hover:bg-red-200">
            <i class="ph ph-minus"></i>
          </button>
          <div class="text-center min-w-[60px]">
            <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ isZweiMenues ? guestCountMenu1 : guestCount }}</p>
            <p class="text-xs text-gray-500">{{ isZweiMenues ? (menu?.menu1_name || 'Menü 1') : 'Gäste' }}</p>
          </div>
          <button @click="guestPlus(1)" class="touch-btn w-14 h-14 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-lg text-2xl hover:bg-green-200">
            <i class="ph ph-plus"></i>
          </button>
        </div>
        <div v-if="isZweiMenues" class="flex items-center justify-center gap-4">
          <button @click="guestMinus(2)" class="touch-btn w-14 h-14 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg text-2xl hover:bg-red-200">
            <i class="ph ph-minus"></i>
          </button>
          <div class="text-center min-w-[60px]">
            <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ guestCountMenu2 }}</p>
            <p class="text-xs text-gray-500">{{ menu?.menu2_name || 'Menü 2' }}</p>
          </div>
          <button @click="guestPlus(2)" class="touch-btn w-14 h-14 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-lg text-2xl hover:bg-green-200">
            <i class="ph ph-plus"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Anmeldungsliste -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
      <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
        <i class="ph ph-list-checks"></i> Anmeldungen ({{ registrations.length }})
      </h3>

      <div v-if="!isZweiMenues">
        <div v-if="registrations.length === 0" class="text-center text-gray-400 py-4">
          Noch keine Anmeldungen
        </div>
        <ul v-else class="divide-y divide-gray-100 dark:divide-gray-700">
          <li v-for="r in registrations" :key="r.id" class="py-2 flex items-center gap-2">
            <i class="ph ph-user text-gray-400"></i>
            <span class="text-gray-900 dark:text-white">{{ r.member_name }}</span>
          </li>
        </ul>
      </div>

      <div v-else class="grid grid-cols-2 gap-6">
        <div>
          <h4 class="text-orange-600 dark:text-orange-400 font-medium text-sm mb-2">
            <i class="ph ph-number-circle-one"></i> {{ menu?.menu1_name || 'Menü 1' }} ({{ regsMenu1.length }})
          </h4>
          <ul class="divide-y divide-gray-100 dark:divide-gray-700">
            <li v-for="r in regsMenu1" :key="r.id" class="py-2 text-sm text-gray-900 dark:text-white">
              {{ r.member_name }}
            </li>
          </ul>
          <div v-if="guestCountMenu1 > 0" class="mt-2 text-sm text-gray-500">
            + {{ guestCountMenu1 }} Gäste
          </div>
        </div>
        <div>
          <h4 class="text-blue-600 dark:text-blue-400 font-medium text-sm mb-2">
            <i class="ph ph-number-circle-two"></i> {{ menu?.menu2_name || 'Menü 2' }} ({{ regsMenu2.length }})
          </h4>
          <ul class="divide-y divide-gray-100 dark:divide-gray-700">
            <li v-for="r in regsMenu2" :key="r.id" class="py-2 text-sm text-gray-900 dark:text-white">
              {{ r.member_name }}
            </li>
          </ul>
          <div v-if="guestCountMenu2 > 0" class="mt-2 text-sm text-gray-500">
            + {{ guestCountMenu2 }} Gäste
          </div>
        </div>
      </div>
    </div>

    <!-- Menü-Formular Modal -->
    <Transition name="fade">
      <div v-if="showMenuForm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 print:hidden" @click.self="showMenuForm = false">
        <div class="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-xl max-w-lg w-full mx-4">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
            <i class="ph ph-cooking-pot"></i> Menü bearbeiten
          </h3>
          <form @submit.prevent="submitMenu" class="space-y-4">
            <div>
              <label class="label">Beschreibung</label>
              <input v-model="menuForm.beschreibung" type="text" class="input" placeholder="z.B. Schnitzel mit Pommes"
                     :disabled="menuForm.zwei_menues" />
            </div>

            <div class="flex items-center gap-2">
              <input type="checkbox" v-model="menuForm.zwei_menues" id="zweiMenues" class="rounded">
              <label for="zweiMenues" class="text-sm text-gray-700 dark:text-gray-300">Zwei Menüs anbieten</label>
            </div>

            <div v-if="menuForm.zwei_menues" class="grid grid-cols-2 gap-3">
              <div>
                <label class="label">Menü 1</label>
                <input v-model="menuForm.menu1_name" type="text" class="input" placeholder="Menü 1" />
              </div>
              <div>
                <label class="label">Menü 2</label>
                <input v-model="menuForm.menu2_name" type="text" class="input" placeholder="Menü 2" />
              </div>
            </div>

            <div class="flex items-center gap-2">
              <input type="checkbox" v-model="menuForm.frist_aktiv" id="fristAktiv" class="rounded">
              <label for="fristAktiv" class="text-sm text-gray-700 dark:text-gray-300">Anmeldefrist aktiv</label>
            </div>

            <div v-if="menuForm.frist_aktiv">
              <label class="label">Anmeldefrist</label>
              <input v-model="menuForm.anmeldefrist" type="time" class="input" />
            </div>

            <div class="flex gap-3 justify-end pt-2">
              <button v-if="menu" type="button" @click="removeMenu"
                      class="btn-ghost text-red-600 hover:text-red-700 text-sm">
                <i class="ph ph-trash"></i> Löschen
              </button>
              <button type="button" @click="showMenuForm = false" class="btn-ghost text-sm">
                Abbrechen
              </button>
              <button type="submit" class="btn-primary text-sm">
                <i class="ph ph-check"></i> Speichern
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>
