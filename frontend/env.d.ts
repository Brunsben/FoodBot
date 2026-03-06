/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface FoodBotConfig {
  api: string
  feuerwehrName: string
}

declare global {
  interface Window {
    CONFIG: FoodBotConfig
  }
}
