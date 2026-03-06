<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { historyData, fetchHistory, showToast } from '../store'
import { getMemberHistory } from '../api'
import { fmtDate } from '../utils/formatters'

/* ── State ──────────────────────────────────────────────────────────────── */
const selectedMember = ref<string | null>(null)
const memberDetail = ref<{ member: any; registrations: any[]; page: number; has_more: boolean } | null>(null)
const detailLoading = ref(false)

/* ── Computed ───────────────────────────────────────────────────────────── */
const top10 = computed(() => historyData.value?.top10 ?? [])
const allMembers = computed(() => historyData.value?.members ?? [])

/* ── Member-Detail ──────────────────────────────────────────────────────── */
async function openMember(memberId: string) {
  selectedMember.value = memberId
  detailLoading.value = true
  try {
    memberDetail.value = await getMemberHistory(memberId)
  } catch {
    showToast('Fehler beim Laden', 'error')
  } finally {
    detailLoading.value = false
  }
}

async function loadMore() {
  if (!selectedMember.value || !memberDetail.value?.has_more) return
  detailLoading.value = true
  try {
    const next = await getMemberHistory(selectedMember.value, memberDetail.value.page + 1)
    memberDetail.value = {
      ...next,
      registrations: [...memberDetail.value.registrations, ...next.registrations],
    }
  } catch { /* */ } finally {
    detailLoading.value = false
  }
}

function closeMember() {
  selectedMember.value = null
  memberDetail.value = null
}

/* ── Init ───────────────────────────────────────────────────────────────── */
onMounted(() => fetchHistory())
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-6">
      <i class="ph ph-trophy text-orange-500"></i>
      Essens-Historie
    </h1>

    <!-- Detail-View -->
    <Transition name="fade">
      <div v-if="selectedMember" class="mb-6">
        <button @click="closeMember" class="btn-ghost text-sm mb-4 flex items-center gap-1">
          <i class="ph ph-arrow-left"></i> Zurück zur Übersicht
        </button>

        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
          <div v-if="memberDetail" class="space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-xl font-bold text-gray-900 dark:text-white">
                <i class="ph ph-user"></i> {{ memberDetail.member?.name || 'Unbekannt' }}
              </h3>
              <span class="text-2xl font-bold text-orange-500">
                {{ memberDetail.registrations.length }}{{ memberDetail.has_more ? '+' : '' }} ×
              </span>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-gray-500 dark:text-gray-400 border-b">
                    <th class="pb-2 font-medium">Datum</th>
                    <th class="pb-2 font-medium">Menü</th>
                    <th class="pb-2 font-medium text-right">Wahl</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
                  <tr v-for="r in memberDetail.registrations" :key="r.datum">
                    <td class="py-2 text-gray-900 dark:text-white">{{ fmtDate(r.datum) }}</td>
                    <td class="py-2 text-gray-500 truncate max-w-[200px]">{{ r.menu || '—' }}</td>
                    <td class="py-2 text-right">
                      <span :class="r.menu_wahl === 1 ? 'text-orange-500' : 'text-blue-500'" class="text-xs font-medium">
                        Menü {{ r.menu_wahl }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <button v-if="memberDetail.has_more" @click="loadMore"
                    :disabled="detailLoading"
                    class="btn-ghost text-sm w-full">
              {{ detailLoading ? 'Laden…' : 'Mehr laden' }}
            </button>
          </div>
          <div v-else class="text-center py-8 text-gray-400">
            <i class="ph ph-spinner animate-spin text-2xl"></i>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Übersicht -->
    <div v-if="!selectedMember" class="space-y-6">
      <!-- Top 10 -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <i class="ph ph-trophy"></i> Top 10 Viel-Esser
        </h3>
        <div class="space-y-3">
          <div v-for="(m, i) in top10" :key="m.member_id"
               @click="openMember(m.member_id)"
               class="flex items-center gap-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded-lg p-2 -mx-2 transition-colors">
            <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                 :class="[
                   i === 0 ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400' :
                   i === 1 ? 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-300' :
                   i === 2 ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400' :
                   'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                 ]">
              {{ i + 1 }}
            </div>
            <div class="flex-1">
              <p class="text-gray-900 dark:text-white font-medium">{{ m.name }}</p>
              <p v-if="m.letzte" class="text-xs text-gray-400">Zuletzt: {{ fmtDate(m.letzte) }}</p>
            </div>
            <div class="text-right">
              <p class="text-lg font-bold text-orange-500">{{ m.total }}</p>
              <p class="text-xs text-gray-400">Essen</p>
            </div>
            <!-- Mini-Bar -->
            <div class="hidden md:block w-24 h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div class="h-full bg-orange-400 dark:bg-orange-500 rounded-full"
                   :style="{ width: ((m.total / (top10[0]?.total || 1)) * 100) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Alle Mitglieder -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            <i class="ph ph-list"></i> Alle Mitglieder ({{ allMembers.length }})
          </h3>
        </div>
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50">
              <th class="px-5 py-3 font-medium">#</th>
              <th class="px-5 py-3 font-medium">Name</th>
              <th class="px-5 py-3 font-medium text-right">Essen</th>
              <th class="px-5 py-3 font-medium text-right">Zuletzt</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-for="(m, i) in allMembers" :key="m.member_id"
                @click="openMember(m.member_id)"
                class="hover:bg-gray-50 dark:hover:bg-gray-700/30 cursor-pointer">
              <td class="px-5 py-3 text-gray-400">{{ i + 1 }}</td>
              <td class="px-5 py-3 text-gray-900 dark:text-white font-medium">{{ m.name }}</td>
              <td class="px-5 py-3 text-right font-mono" :class="m.total > 0 ? 'text-orange-500 font-bold' : 'text-gray-300'">
                {{ m.total }}
              </td>
              <td class="px-5 py-3 text-right text-gray-400 text-xs">{{ m.letzte ? fmtDate(m.letzte) : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
