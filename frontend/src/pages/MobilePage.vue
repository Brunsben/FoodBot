<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getMobileStatus, mobileRegister } from '../api'
import { showToast } from '../store'

/* ── Props ──────────────────────────────────────────────────────────────── */
const props = defineProps<{ token?: string }>()

/* ── State ──────────────────────────────────────────────────────────────── */
const mobileToken = ref(props.token || '')
const loading = ref(false)
const data = ref<{
  member: { name: string } | null
  menu: any | null
  registered: boolean
  menu_wahl: number | null
  deadline_passed: boolean
} | null>(null)
const error = ref('')
const menuChoiceModal = ref(false)

/* ── Actions ────────────────────────────────────────────────────────────── */
async function loadStatus() {
  if (!mobileToken.value) return
  loading.value = true
  error.value = ''
  try {
    data.value = await getMobileStatus(mobileToken.value)
  } catch (e: any) {
    error.value = e.message || 'Token ungültig oder Fehler'
    data.value = null
  } finally {
    loading.value = false
  }
}

async function doToggle(menuChoice?: number) {
  if (!mobileToken.value) return

  // Zwei-Menü: Menüwahl nötig
  if (data.value?.menu?.zwei_menues && !data.value?.registered && !menuChoice) {
    menuChoiceModal.value = true
    return
  }

  loading.value = true
  try {
    const res = await mobileRegister(mobileToken.value, menuChoice)
    if (res.need_menu_choice) {
      menuChoiceModal.value = true
      loading.value = false
      return
    }
    // Status neu laden
    await loadStatus()
    showToast(
      data.value?.registered ? 'Angemeldet ✓' : 'Abgemeldet ✗',
      data.value?.registered ? 'success' : 'error'
    )
  } catch (e: any) {
    showToast(e.message || 'Fehler', 'error')
  } finally {
    loading.value = false
    menuChoiceModal.value = false
  }
}

/* ── Token aus URL ──────────────────────────────────────────────────────── */
onMounted(() => {
  // Token aus URL-Pfad: /mobile/abc123
  const path = window.location.pathname
  const match = path.match(/\/mobile\/([a-zA-Z0-9_-]+)/)
  if (match) {
    mobileToken.value = match[1]
  }
  // Oder aus Hash
  const hash = window.location.hash
  const hashMatch = hash.match(/mobile\/([a-zA-Z0-9_-]+)/)
  if (hashMatch) {
    mobileToken.value = hashMatch[1]
  }
  if (mobileToken.value) {
    loadStatus()
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="max-w-md w-full">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center mx-auto mb-3">
          <i class="ph ph-fork-knife text-3xl text-orange-500"></i>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">FoodBot Mobile</h1>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-8">
        <i class="ph ph-spinner animate-spin text-3xl text-orange-500"></i>
        <p class="text-gray-400 mt-2">Laden…</p>
      </div>

      <!-- Fehler -->
      <div v-else-if="error" class="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 text-center">
        <i class="ph ph-warning text-3xl text-red-500 mb-2"></i>
        <p class="text-red-700 dark:text-red-300">{{ error }}</p>
        <button @click="loadStatus" class="mt-4 btn-primary text-sm">Erneut versuchen</button>
      </div>

      <!-- Kein Token -->
      <div v-else-if="!mobileToken" class="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-6 text-center">
        <i class="ph ph-link-break text-3xl text-yellow-500 mb-2"></i>
        <p class="text-yellow-700 dark:text-yellow-300">Kein gültiger Link</p>
        <p class="text-sm text-gray-500 mt-1">Bitte verwende den Link, den du von deinem Admin erhalten hast.</p>
      </div>

      <!-- Status -->
      <div v-else-if="data" class="space-y-4">
        <!-- Begrüßung -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 text-center">
          <p class="text-gray-500 dark:text-gray-400 text-sm">Hallo,</p>
          <p class="text-xl font-bold text-gray-900 dark:text-white">{{ data.member?.name || 'Kamerad' }}</p>
        </div>

        <!-- Menü -->
        <div v-if="data.menu" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Heutiges Menü</p>
          <p class="text-lg font-semibold text-gray-900 dark:text-white">{{ data.menu.beschreibung }}</p>
          <div v-if="data.menu.zwei_menues" class="mt-2 space-y-1 text-sm">
            <p class="text-orange-600 dark:text-orange-400">
              <i class="ph ph-number-circle-one"></i> {{ data.menu.menu1_name }}
            </p>
            <p class="text-blue-600 dark:text-blue-400">
              <i class="ph ph-number-circle-two"></i> {{ data.menu.menu2_name }}
            </p>
          </div>
          <p v-if="data.deadline_passed" class="text-red-500 text-sm mt-2">
            <i class="ph ph-clock-countdown"></i> Anmeldefrist abgelaufen
          </p>
        </div>

        <div v-else class="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-5 text-center">
          <p class="text-yellow-700 dark:text-yellow-300">Heute kein Menü geplant</p>
        </div>

        <!-- An-/Abmeldebutton -->
        <button @click="doToggle()"
                :disabled="loading || (!data.registered && data.deadline_passed)"
                :class="[
                  'w-full py-6 rounded-xl text-xl font-bold shadow-lg transition-all active:scale-95',
                  data.registered
                    ? 'bg-red-500 hover:bg-red-600 text-white'
                    : 'bg-green-500 hover:bg-green-600 text-white',
                  (loading || (!data.registered && data.deadline_passed)) ? 'opacity-50 cursor-not-allowed' : ''
                ]">
          <i :class="data.registered ? 'ph ph-x-circle' : 'ph ph-check-circle'" class="text-3xl mb-1 block"></i>
          {{ data.registered ? 'Abmelden' : 'Anmelden' }}
        </button>

        <p v-if="data.registered && data.menu_wahl" class="text-center text-sm text-gray-500">
          Angemeldet für Menü {{ data.menu_wahl }}
        </p>
      </div>

      <!-- Menüwahl-Modal -->
      <Transition name="fade">
        <div v-if="menuChoiceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div class="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-2xl max-w-sm w-full mx-4">
            <h3 class="text-xl font-bold text-center text-gray-900 dark:text-white mb-6">Menü wählen</h3>
            <div class="grid grid-cols-2 gap-4">
              <button @click="doToggle(1)"
                      class="p-6 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-center font-semibold active:scale-95 transition-all">
                <i class="ph ph-number-circle-one text-3xl mb-2 block"></i>
                {{ data?.menu?.menu1_name || 'Menü 1' }}
              </button>
              <button @click="doToggle(2)"
                      class="p-6 rounded-xl bg-blue-500 hover:bg-blue-600 text-white text-center font-semibold active:scale-95 transition-all">
                <i class="ph ph-number-circle-two text-3xl mb-2 block"></i>
                {{ data?.menu?.menu2_name || 'Menü 2' }}
              </button>
            </div>
            <button @click="menuChoiceModal = false" class="mt-4 w-full text-gray-400 text-sm">Abbrechen</button>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>
