<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { todayData, fetchToday, doRegister, doRfidRegister, showToast } from '../store'
import { getMenuToday } from '../api'
import type { Menu } from '../types'

/* ── State ──────────────────────────────────────────────────────────────── */
const personalnummer = ref('')
const feedback = ref<{ name: string; registered: boolean; menuChoice?: number } | null>(null)
const feedbackTimer = ref<ReturnType<typeof setTimeout>>()
const menuChoiceModal = ref(false)
const pendingMemberId = ref('')
const pendingMenu = ref<{ menu1: string; menu2: string }>({ menu1: '', menu2: '' })

/* RFID */
const rfidBuffer = ref('')
const rfidTimer = ref<ReturnType<typeof setTimeout>>()

/* Polling */
const menuPollTimer = ref<ReturnType<typeof setInterval>>()

/* ── Computed ───────────────────────────────────────────────────────────── */
const menu = computed(() => todayData.value?.menu)
const regCount = computed(() => todayData.value?.total ?? 0)
const deadlinePassed = computed(() => todayData.value?.deadline_passed ?? false)

/* ── Numpad ─────────────────────────────────────────────────────────────── */
function numpadInput(digit: string) {
  if (personalnummer.value.length < 10) {
    personalnummer.value += digit
  }
}

function numpadClear() {
  personalnummer.value = ''
}

function numpadBackspace() {
  personalnummer.value = personalnummer.value.slice(0, -1)
}

async function submitPersonalnummer() {
  const pn = personalnummer.value.trim()
  if (!pn) return
  personalnummer.value = ''
  await doRegistration({ personalnummer: pn })
}

/* ── RFID Keyboard Capture ──────────────────────────────────────────────── */
function onKeyDown(e: KeyboardEvent) {
  // Ignoriere Modifier-Tasten und Tab/Escape
  if (e.ctrlKey || e.altKey || e.metaKey) return
  if (e.key === 'Tab' || e.key === 'Escape') return

  // RFID-Reader sendet Zeichen schnell hintereinander
  if (e.key === 'Enter') {
    e.preventDefault()
    if (rfidBuffer.value.length >= 3) {
      processRfidScan(rfidBuffer.value)
    }
    rfidBuffer.value = ''
    clearTimeout(rfidTimer.value)
    return
  }

  if (e.key.length === 1) {
    e.preventDefault()
    rfidBuffer.value += e.key
    clearTimeout(rfidTimer.value)
    rfidTimer.value = setTimeout(() => {
      // Timeout: wahrscheinlich manuelle Eingabe, ignorieren
      rfidBuffer.value = ''
    }, 200)
  }
}

async function processRfidScan(cardId: string) {
  await doRegistration({ rfid: cardId })
}

/* ── Registrierung ──────────────────────────────────────────────────────── */
async function doRegistration(params: { personalnummer?: string; rfid?: string; menu_choice?: number }) {
  try {
    const res = await doRegister(params)
    if (res.need_menu_choice) {
      // Zwei-Menü-Modus: Auswahl nötig
      pendingMemberId.value = res.member_id || ''
      pendingMenu.value = { menu1: res.menu1 || 'Menü 1', menu2: res.menu2 || 'Menü 2' }
      menuChoiceModal.value = true
      return
    }
    showFeedback(res.user?.name || 'Unbekannt', res.registered)
  } catch {
    // Fehler wird durch showToast im store behandelt
  }
}

async function selectMenu(choice: number) {
  menuChoiceModal.value = false
  // Re-Registrierung mit Menüwahl
  try {
    const res = await doRegister({
      personalnummer: pendingMemberId.value,
      menu_choice: choice,
    })
    showFeedback(res.user?.name || 'Unbekannt', res.registered)
  } catch {
    // handled
  }
}

/* ── Feedback ───────────────────────────────────────────────────────────── */
function showFeedback(name: string, registered: boolean) {
  clearTimeout(feedbackTimer.value)
  feedback.value = { name, registered }
  feedbackTimer.value = setTimeout(() => {
    feedback.value = null
  }, 3000)
  // Daten aktualisieren
  fetchToday()
}

/* ── Lifecycle ──────────────────────────────────────────────────────────── */
onMounted(() => {
  document.addEventListener('keydown', onKeyDown, true)
  fetchToday()
  // Menü-Polling alle 10 Sekunden
  menuPollTimer.value = setInterval(fetchToday, 10000)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeyDown, true)
  clearTimeout(rfidTimer.value)
  clearTimeout(feedbackTimer.value)
  clearInterval(menuPollTimer.value)
})
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 py-6 select-none">
    <!-- Header -->
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white flex items-center justify-center gap-3">
        <i class="ph ph-fork-knife text-orange-500"></i>
        Essensanmeldung
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mt-1">
        Personalnummer eingeben oder RFID-Karte scannen
      </p>
    </div>

    <!-- Heutiges Menü -->
    <div v-if="menu" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 mb-6">
      <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-2">
        <i class="ph ph-cooking-pot"></i>
        Heutiges Menü
      </div>
      <p class="text-lg font-semibold text-gray-900 dark:text-white">{{ menu.beschreibung }}</p>
      <div v-if="menu.zwei_menues" class="mt-2 space-y-1 text-sm">
        <div class="text-orange-600 dark:text-orange-400">
          <i class="ph ph-number-circle-one"></i> {{ menu.menu1_name }}
        </div>
        <div class="text-blue-600 dark:text-blue-400">
          <i class="ph ph-number-circle-two"></i> {{ menu.menu2_name }}
        </div>
      </div>
      <div class="mt-3 flex items-center gap-4 text-sm">
        <span class="text-gray-500 dark:text-gray-400">
          <i class="ph ph-users"></i> {{ regCount }} Anmeldungen
        </span>
        <span v-if="deadlinePassed" class="text-red-500">
          <i class="ph ph-clock-countdown"></i> Frist abgelaufen
        </span>
        <span v-else-if="menu.frist_aktiv" class="text-green-600 dark:text-green-400">
          <i class="ph ph-clock"></i> bis {{ menu.anmeldefrist }} Uhr
        </span>
      </div>
    </div>

    <div v-else class="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-5 mb-6 text-center">
      <i class="ph ph-warning text-2xl text-yellow-500"></i>
      <p class="text-yellow-700 dark:text-yellow-300 mt-1">Kein Menü für heute eingetragen</p>
    </div>

    <!-- Feedback-Overlay -->
    <Transition name="fade">
      <div v-if="feedback"
           :class="[
             'fixed inset-0 z-50 flex items-center justify-center bg-black/30',
           ]"
           @click="feedback = null">
        <div :class="[
               'rounded-2xl p-10 text-center shadow-2xl min-w-[300px]',
               feedback.registered
                 ? 'bg-green-500 text-white'
                 : 'bg-red-500 text-white'
             ]">
          <i :class="[
               'text-6xl mb-4 block',
               feedback.registered ? 'ph ph-check-circle' : 'ph ph-x-circle'
             ]"></i>
          <p class="text-2xl font-bold">{{ feedback.name }}</p>
          <p class="text-xl mt-2">{{ feedback.registered ? 'Angemeldet ✓' : 'Abgemeldet ✗' }}</p>
        </div>
      </div>
    </Transition>

    <!-- Menüwahl-Modal -->
    <Transition name="fade">
      <div v-if="menuChoiceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
        <div class="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-2xl max-w-md w-full mx-4">
          <h3 class="text-xl font-bold text-center text-gray-900 dark:text-white mb-6">
            Menü wählen
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <button @click="selectMenu(1)"
                    class="touch-btn bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-lg font-semibold p-6">
              <i class="ph ph-number-circle-one text-3xl mb-2 block"></i>
              {{ pendingMenu.menu1 }}
            </button>
            <button @click="selectMenu(2)"
                    class="touch-btn bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-lg font-semibold p-6">
              <i class="ph ph-number-circle-two text-3xl mb-2 block"></i>
              {{ pendingMenu.menu2 }}
            </button>
          </div>
          <button @click="menuChoiceModal = false"
                  class="mt-4 w-full text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-sm">
            Abbrechen
          </button>
        </div>
      </div>
    </Transition>

    <!-- Numpad -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
      <!-- Eingabefeld -->
      <div class="relative mb-4">
        <input
          type="text"
          :value="personalnummer"
          readonly
          placeholder="Personalnummer"
          class="w-full text-center text-3xl font-mono tracking-widest bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg py-4 px-4 text-gray-900 dark:text-white"
        />
        <button v-if="personalnummer" @click="numpadClear"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
          <i class="ph ph-x-circle text-2xl"></i>
        </button>
      </div>

      <!-- Tasten -->
      <div class="grid grid-cols-3 gap-3">
        <button v-for="d in ['1','2','3','4','5','6','7','8','9']" :key="d"
                @click="numpadInput(d)"
                class="touch-btn bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-xl text-2xl font-bold">
          {{ d }}
        </button>
        <button @click="numpadBackspace"
                class="touch-btn bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-500 dark:text-gray-400 rounded-xl text-2xl">
          <i class="ph ph-backspace"></i>
        </button>
        <button @click="numpadInput('0')"
                class="touch-btn bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-xl text-2xl font-bold">
          0
        </button>
        <button @click="submitPersonalnummer" :disabled="!personalnummer"
                class="touch-btn rounded-xl text-2xl font-bold"
                :class="personalnummer
                  ? 'bg-green-500 hover:bg-green-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-600 text-gray-400 cursor-not-allowed'">
          <i class="ph ph-check"></i>
        </button>
      </div>

      <p class="text-center text-sm text-gray-400 dark:text-gray-500 mt-4">
        <i class="ph ph-contactless-payment"></i>
        Alternativ: RFID-Karte an den Leser halten
      </p>
    </div>
  </div>
</template>
