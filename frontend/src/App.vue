<template>
  <div>
    <!-- App Shell -->
    <Sidebar />
    <MobileHeader />

    <main class="min-h-screen bg-gray-50 dark:bg-gray-900 md:pl-56 transition-all">
      <div class="px-4 py-6 max-w-7xl">
        <Transition name="fade" mode="out-in">
          <!-- Login-Seite -->
          <div v-if="page === 'login' && !loggedIn" key="login"
            class="flex items-center justify-center min-h-[60vh]">
            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 w-full max-w-sm border border-gray-100 dark:border-gray-700">
              <div class="text-center mb-6">
                <span class="text-4xl">🔑</span>
                <h1 class="text-xl font-bold text-gray-900 dark:text-white mt-2">Admin-Login</h1>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ feuerwehrName }} · FoodBot</p>
              </div>
              <div class="grid gap-3">
                <div>
                  <label class="label">Passwort</label>
                  <input v-model="loginForm.password" type="password" class="input" placeholder="Admin-Passwort" @keyup.enter="doLogin" autocomplete="current-password" />
                </div>
                <div v-if="loginForm.error" class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg px-3 py-2">
                  {{ loginForm.error }}
                </div>
                <button @click="doLogin" class="btn-primary w-full justify-center mt-2" :disabled="loading">
                  <i class="ph ph-sign-in"></i> Anmelden
                </button>
              </div>
            </div>
          </div>

          <!-- Mobile-Seite (Token-URL) -->
          <MobilePage v-else-if="page === 'mobile'" key="mobile" />

          <!-- Normale Seiten -->
          <component v-else :is="currentPageComponent" :key="page" />
        </Transition>
      </div>
    </main>

    <Toast />
    <Loader />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { page, loggedIn, loginForm, loading, doLogin, feuerwehrName } from './store'

import Sidebar from './components/layout/Sidebar.vue'
import MobileHeader from './components/layout/MobileHeader.vue'
import Toast from './components/ui/Toast.vue'
import Loader from './components/ui/Loader.vue'

import TouchPage from './pages/TouchPage.vue'
import KitchenPage from './pages/KitchenPage.vue'
import AdminPage from './pages/AdminPage.vue'
import WeeklyPage from './pages/WeeklyPage.vue'
import StatsPage from './pages/StatsPage.vue'
import HistoryPage from './pages/HistoryPage.vue'
import MobilePage from './pages/MobilePage.vue'

const pageComponents: Record<string, any> = {
  touch: TouchPage,
  kitchen: KitchenPage,
  admin: AdminPage,
  weekly: WeeklyPage,
  stats: StatsPage,
  history: HistoryPage,
}

const currentPageComponent = computed(() => pageComponents[page.value] || TouchPage)

onMounted(() => {
  // Deep-Link: /mobile/<token>
  const path = window.location.pathname
  if (path.startsWith('/mobile/')) {
    page.value = 'mobile'
  }
})
</script>
