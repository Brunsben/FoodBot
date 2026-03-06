<template>
  <aside :class="['fixed inset-y-0 left-0 z-40 w-56 bg-white dark:bg-gray-900 border-r border-gray-100 dark:border-gray-700 flex flex-col transition-transform duration-300 ease-in-out',
    sidebarOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full md:translate-x-0']">

    <div class="flex items-center gap-3 px-5 py-5 border-b border-gray-100 dark:border-gray-800">
      <span class="text-xl">🍽️</span>
      <div>
        <div class="font-bold text-gray-900 dark:text-white text-sm leading-tight">{{ feuerwehrName }}</div>
        <div class="text-xs text-gray-400 dark:text-gray-500">FoodBot</div>
      </div>
    </div>

    <nav class="flex-1 py-3 px-3 space-y-0.5">
      <button v-for="p in visiblePages" :key="p.id"
        @click="page = p.id; sidebarOpen = false"
        :class="['w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm font-medium text-left',
          page === p.id
            ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100']">
        <i :class="[p.iconClass, 'text-xl flex-shrink-0']"></i>
        {{ p.label }}
      </button>
    </nav>

    <div class="p-3 border-t border-gray-100 dark:border-gray-800 space-y-0.5">
      <button @click="toggleDark" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
        <i v-if="darkMode" class="ph ph-sun text-xl flex-shrink-0"></i>
        <i v-else class="ph ph-moon text-xl flex-shrink-0"></i>
        {{ darkMode ? 'Helles Design' : 'Dunkles Design' }}
      </button>

      <template v-if="loggedIn">
        <div class="flex items-center gap-2 px-3 py-2 text-xs text-gray-400 dark:text-gray-500 mt-1">
          <i class="ph ph-shield-check text-base"></i>
          <span>Admin</span>
        </div>
        <button @click="doLogout; sidebarOpen = false" class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
          <i class="ph ph-sign-out text-lg flex-shrink-0"></i> Abmelden
        </button>
      </template>

      <template v-else>
        <button @click="page = 'login'; sidebarOpen = false" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
          <i class="ph ph-sign-in text-xl flex-shrink-0"></i> Admin-Login
        </button>
      </template>
    </div>
  </aside>

  <div v-if="sidebarOpen" @click="sidebarOpen = false"
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 md:hidden"></div>
</template>

<script setup>
import { page, sidebarOpen, visiblePages, loggedIn, doLogout, darkMode, toggleDark, feuerwehrName } from '../../store'
</script>
