
import '@vue/runtime-core'

declare module '@vue/runtime-core' {
  
  interface HTMLElement {
    
    v_sakura_emoji?: (value: string) => void
  }
}

export {}
