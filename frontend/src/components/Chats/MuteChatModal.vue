<template>
  <Teleport to="body">
    <div class="mute-backdrop" @click="$emit('close')">
      <div class="mute-modal" @click.stop>
        <div class="mute-header">
          <span class="mute-title">Заглушить уведомления</span>
          <button class="mute-close" @click="$emit('close')">✕</button>
        </div>
        <div class="mute-options">
          <button
            v-for="opt in options"
            :key="opt.value"
            class="mute-opt"
            @click="select(opt.value)"
          >{{ opt.label }}</button>
          <button class="mute-opt custom" @click="showCustom = !showCustom">
            До определённой даты…
          </button>
          <div v-if="showCustom" class="mute-custom">
            <input type="datetime-local" v-model="customDate" class="mute-date-input" />
            <button class="mute-apply" @click="applyCustom">Применить</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ close: []; muted: [until: string | null] }>()

const showCustom = ref(false)
const customDate = ref('')

const options = [
  { label: '15 минут', value: '15m' },
  { label: '1 час',   value: '1h'  },
  { label: '8 часов', value: '8h'  },
  { label: '2 дня',   value: '2d'  },
  { label: '1 неделю',value: '1w'  },
  { label: 'Навсегда',value: 'forever' },
]

const calcUntil = (value: string): string | null => {
  if (value === 'forever') return null  // null = навсегда
  const now = Date.now()
  const map: Record<string, number> = {
    '15m': 15 * 60 * 1000,
    '1h':   1 * 60 * 60 * 1000,
    '8h':   8 * 60 * 60 * 1000,
    '2d':   2 * 24 * 60 * 60 * 1000,
    '1w':   7 * 24 * 60 * 60 * 1000,
  }
  const ms = map[value]
  if (ms === undefined) return null
  return new Date(now + ms).toISOString()
}

const select = (value: string) => {
  emit('muted', calcUntil(value))
  emit('close')
}

const applyCustom = () => {
  if (!customDate.value) return
  emit('muted', new Date(customDate.value).toISOString())
  emit('close')
}
</script>

<style scoped>
.mute-backdrop {
  position: fixed; inset: 0; z-index: 10000;
  background: rgba(5,4,8,0.88);
  backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
}
.mute-modal {
  background: var(--surface-2); border: 1px solid var(--border-default); border-radius: var(--radius-lg);
  min-width: 280px; max-width: 340px; width: 100%;
  box-shadow: var(--shadow-modal);
}
.mute-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; border-bottom: 1px solid var(--border-subtle);
}
.mute-title { color: var(--text-primary); font-weight: 600; font-size: .95rem; }
.mute-close { background: none; border: none; color: var(--text-tertiary); cursor: pointer; font-size: 1rem; transition: color .15s var(--ease-petal); }
.mute-close:hover { color: var(--accent); }
.mute-options { display: flex; flex-direction: column; padding: 8px; gap: 2px; }
.mute-opt {
  padding: 10px 12px; border: none; border-radius: var(--radius-lg);
  background: transparent; color: var(--text-secondary); font-size: .9rem;
  text-align: left; cursor: pointer; transition: background .15s var(--ease-petal);
}
.mute-opt:hover { background: var(--surface-4); color: var(--text-primary); }
.mute-opt.custom { color: var(--accent); }
.mute-custom { padding: 8px 4px; display: flex; gap: 8px; flex-wrap: wrap; }
.mute-date-input {
  flex: 1; background: var(--surface-4); border: 1px solid var(--border-default); border-radius: var(--radius-md);
  color: var(--text-primary); padding: 6px 8px; font-size: .85rem; transition: all .15s var(--ease-petal);
}
.mute-date-input:focus { outline: none; border-color: var(--accent); }
.mute-apply {
  background: var(--accent); color: var(--text-on-accent); border: none; border-radius: var(--radius-md);
  padding: 6px 14px; cursor: pointer; font-size: .85rem; transition: all .15s var(--ease-petal);
}
.mute-apply:hover { box-shadow: var(--shadow-glow-sm); }
</style>
