<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { weeklyData, fetchWeekly, doSaveWeeklyDay, doDeleteWeeklyDay, presets, fetchPresets, showToast } from '../store'
import { fmtDate, fmtWeekday } from '../utils/formatters'

/* ── Editing ────────────────────────────────────────────────────────────── */
const editingDay = ref<string | null>(null)
const dayForm = ref({
  beschreibung: '',
  zwei_menues: false,
  menu1_name: '',
  menu2_name: '',
  anmeldefrist: '19:45',
  frist_aktiv: true,
})

function editDay(datum: string) {
  const day = weeklyData.value.find(d => d.datum === datum)
  if (day?.menu) {
    dayForm.value = {
      beschreibung: day.menu.beschreibung || '',
      zwei_menues: day.menu.zwei_menues || false,
      menu1_name: day.menu.menu1_name || '',
      menu2_name: day.menu.menu2_name || '',
      anmeldefrist: day.menu.anmeldefrist || '19:45',
      frist_aktiv: day.menu.frist_aktiv ?? true,
    }
  } else {
    dayForm.value = { beschreibung: '', zwei_menues: false, menu1_name: '', menu2_name: '', anmeldefrist: '19:45', frist_aktiv: true }
  }
  editingDay.value = datum
}

async function saveDay() {
  if (!editingDay.value) return
  await doSaveWeeklyDay(editingDay.value, dayForm.value)
  editingDay.value = null
  fetchWeekly()
}

async function removeDay(datum: string) {
  if (!confirm('Menü für diesen Tag löschen?')) return
  await doDeleteWeeklyDay(datum)
  fetchWeekly()
}

function applyPreset(name: string) {
  dayForm.value.beschreibung = name
}

function cancelEdit() {
  editingDay.value = null
}

/* ── Helpers ────────────────────────────────────────────────────────────── */
function isWeekend(datum: string): boolean {
  const d = new Date(datum)
  return d.getDay() === 0 || d.getDay() === 6
}

function isToday(datum: string): boolean {
  return datum === new Date().toISOString().split('T')[0]
}

/* ── Init ───────────────────────────────────────────────────────────────── */
onMounted(() => {
  fetchWeekly()
  fetchPresets()
})
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-6">
      <i class="ph ph-calendar-dots text-orange-500"></i>
      Wochenplan
    </h1>

    <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
      Die nächsten 14 Tage im Überblick. Klicke auf einen Tag, um das Menü zu bearbeiten.
    </p>

    <div class="space-y-3">
      <div v-for="day in weeklyData" :key="day.datum"
           :class="[
             'bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-4 transition-all',
             isToday(day.datum)
               ? 'border-orange-300 dark:border-orange-600 ring-1 ring-orange-200 dark:ring-orange-700'
               : 'border-gray-200 dark:border-gray-700',
             isWeekend(day.datum) ? 'opacity-60' : '',
           ]">

        <!-- Tag-Header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="text-center min-w-[50px]">
              <p class="text-xs text-gray-500 dark:text-gray-400 uppercase">{{ fmtWeekday(day.datum) }}</p>
              <p class="text-lg font-bold" :class="isToday(day.datum) ? 'text-orange-500' : 'text-gray-900 dark:text-white'">
                {{ new Date(day.datum).getDate() }}
              </p>
            </div>
            <div>
              <p v-if="day.menu" class="text-gray-900 dark:text-white font-medium">
                {{ day.menu.beschreibung }}
              </p>
              <p v-else class="text-gray-400 text-sm italic">Kein Menü geplant</p>
              <div v-if="day.menu?.zwei_menues" class="flex gap-3 text-xs mt-1">
                <span class="text-orange-500"><i class="ph ph-number-circle-one"></i> {{ day.menu.menu1_name }}</span>
                <span class="text-blue-500"><i class="ph ph-number-circle-two"></i> {{ day.menu.menu2_name }}</span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span v-if="day.registrations_count" class="text-xs text-gray-400">
              <i class="ph ph-users"></i> {{ day.registrations_count }}
            </span>
            <button @click="editDay(day.datum)" class="text-gray-400 hover:text-orange-500 transition-colors">
              <i class="ph ph-pencil-simple text-lg"></i>
            </button>
            <button v-if="day.menu" @click="removeDay(day.datum)" class="text-gray-400 hover:text-red-500 transition-colors">
              <i class="ph ph-trash text-lg"></i>
            </button>
          </div>
        </div>

        <!-- Inline Edit -->
        <Transition name="fade">
          <div v-if="editingDay === day.datum" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <form @submit.prevent="saveDay" class="space-y-3">
              <!-- Preset-Buttons -->
              <div v-if="presets.length" class="flex flex-wrap gap-2">
                <button v-for="p in presets" :key="p.id" type="button"
                        @click="applyPreset(p.name)"
                        class="px-2 py-1 rounded-full text-xs bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 hover:bg-orange-200">
                  {{ p.name }}
                </button>
              </div>

              <input v-model="dayForm.beschreibung" class="input text-sm" placeholder="Beschreibung"
                     :disabled="dayForm.zwei_menues" />

              <div class="flex items-center gap-2">
                <input type="checkbox" v-model="dayForm.zwei_menues" :id="'z-'+day.datum" class="rounded">
                <label :for="'z-'+day.datum" class="text-xs text-gray-600 dark:text-gray-400">Zwei Menüs</label>
              </div>
              <div v-if="dayForm.zwei_menues" class="grid grid-cols-2 gap-2">
                <input v-model="dayForm.menu1_name" class="input text-sm" placeholder="Menü 1" />
                <input v-model="dayForm.menu2_name" class="input text-sm" placeholder="Menü 2" />
              </div>

              <div class="flex items-center gap-2">
                <input type="checkbox" v-model="dayForm.frist_aktiv" :id="'f-'+day.datum" class="rounded">
                <label :for="'f-'+day.datum" class="text-xs text-gray-600 dark:text-gray-400">Frist aktiv</label>
                <input v-if="dayForm.frist_aktiv" v-model="dayForm.anmeldefrist" type="time" class="input text-sm w-28 ml-2" />
              </div>

              <div class="flex gap-2">
                <button type="submit" class="btn-primary text-xs"><i class="ph ph-check"></i> Speichern</button>
                <button type="button" @click="cancelEdit" class="btn-ghost text-xs">Abbrechen</button>
              </div>
            </form>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>
