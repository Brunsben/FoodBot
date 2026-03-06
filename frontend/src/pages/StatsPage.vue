<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { statsData, fetchStats, showToast } from '../store'
import { fmtDate, fmtWeekday } from '../utils/formatters'

/* ── State ──────────────────────────────────────────────────────────────── */
const days = ref(14)

/* ── Computed ───────────────────────────────────────────────────────────── */
const stats = computed(() => statsData.value)
const totalRegs = computed(() => stats.value.reduce((s, d) => s + d.anzahl, 0))
const totalGuests = computed(() => stats.value.reduce((s, d) => s + d.gaeste, 0))
const avgPerDay = computed(() => {
  const daysWithFood = stats.value.filter(d => d.total > 0).length
  return daysWithFood > 0 ? Math.round((totalRegs.value + totalGuests.value) / daysWithFood) : 0
})
const maxDay = computed(() => {
  if (!stats.value.length) return null
  return stats.value.reduce((best, d) => d.total > best.total ? d : best, stats.value[0])
})
const maxTotal = computed(() => Math.max(...stats.value.map(d => d.total), 1))

/* ── CSV-Export ─────────────────────────────────────────────────────────── */
function exportCsv() {
  const header = 'Datum;Wochentag;Beschreibung;Mitglieder;Gäste;Gesamt'
  const rows = stats.value.map(d =>
    `${d.datum};${fmtWeekday(d.datum)};${d.beschreibung || ''};${d.anzahl};${d.gaeste};${d.total}`
  )
  const csv = [header, ...rows].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `foodbot-statistik-${days.value}tage.csv`
  a.click()
  URL.revokeObjectURL(url)
  showToast('CSV exportiert', 'success')
}

/* ── Init ───────────────────────────────────────────────────────────────── */
onMounted(() => fetchStats(days.value))
watch(days, (v) => fetchStats(v))
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <i class="ph ph-chart-bar text-orange-500"></i>
        Statistiken
      </h1>
      <div class="flex items-center gap-3">
        <select v-model="days" class="input text-sm w-auto">
          <option :value="7">7 Tage</option>
          <option :value="14">14 Tage</option>
          <option :value="30">30 Tage</option>
          <option :value="60">60 Tage</option>
          <option :value="90">90 Tage</option>
        </select>
        <button @click="exportCsv" class="btn-ghost text-sm flex items-center gap-1">
          <i class="ph ph-download-simple"></i> CSV
        </button>
      </div>
    </div>

    <!-- KPI-Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 text-center">
        <p class="text-3xl font-bold text-orange-500">{{ totalRegs }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Anmeldungen</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 text-center">
        <p class="text-3xl font-bold text-blue-500">{{ totalGuests }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Gäste</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 text-center">
        <p class="text-3xl font-bold text-green-500">{{ avgPerDay }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Ø pro Tag</p>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 text-center">
        <p class="text-3xl font-bold text-purple-500">{{ maxDay?.total ?? 0 }}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">Maximum</p>
      </div>
    </div>

    <!-- Mini-Balkendiagramm -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 mb-6">
      <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-4">Tagesübersicht</h3>
      <div class="flex items-end gap-1 h-32">
        <div v-for="d in [...stats].reverse()" :key="d.datum"
             class="flex-1 flex flex-col items-center gap-1 group relative">
          <div class="w-full flex flex-col justify-end" style="height: 100px;">
            <div v-if="d.gaeste" class="bg-blue-400 dark:bg-blue-500 rounded-t-sm transition-all"
                 :style="{ height: (d.gaeste / maxTotal * 100) + 'px' }"></div>
            <div v-if="d.anzahl" class="bg-orange-400 dark:bg-orange-500 rounded-t-sm transition-all"
                 :class="{ 'rounded-t-sm': !d.gaeste }"
                 :style="{ height: (d.anzahl / maxTotal * 100) + 'px' }"></div>
          </div>
          <!-- Tooltip -->
          <div class="absolute -top-10 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
            {{ fmtDate(d.datum) }}: {{ d.total }}
          </div>
        </div>
      </div>
      <div class="flex items-center gap-4 mt-3 text-xs text-gray-500">
        <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-orange-400 inline-block"></span> Mitglieder</span>
        <span class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-blue-400 inline-block"></span> Gäste</span>
      </div>
    </div>

    <!-- Tabelle -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-left text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50">
            <th class="px-4 py-3 font-medium">Datum</th>
            <th class="px-4 py-3 font-medium">Menü</th>
            <th class="px-4 py-3 font-medium text-right">Mitglieder</th>
            <th class="px-4 py-3 font-medium text-right">Gäste</th>
            <th class="px-4 py-3 font-medium text-right">Gesamt</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
          <tr v-for="d in stats" :key="d.datum" class="hover:bg-gray-50 dark:hover:bg-gray-700/30">
            <td class="px-4 py-3">
              <span class="text-gray-900 dark:text-white">{{ fmtDate(d.datum) }}</span>
              <span class="text-xs text-gray-400 ml-1">{{ fmtWeekday(d.datum) }}</span>
            </td>
            <td class="px-4 py-3 text-gray-600 dark:text-gray-300 truncate max-w-[200px]">
              {{ d.beschreibung || '—' }}
            </td>
            <td class="px-4 py-3 text-right font-mono text-gray-900 dark:text-white">{{ d.anzahl }}</td>
            <td class="px-4 py-3 text-right font-mono text-gray-500">{{ d.gaeste }}</td>
            <td class="px-4 py-3 text-right font-mono font-bold" :class="d.total > 0 ? 'text-orange-500' : 'text-gray-300'">
              {{ d.total }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
