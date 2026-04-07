// Augment the Vue types to include custom directives
import '@vue/runtime-core'

declare module '@vue/runtime-core' {
  // Global custom directives
  interface HTMLElement {
    // Sakura emoji directive
    v_sakura_emoji?: (value: string) => void
  }
}

export {}
