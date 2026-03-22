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
  background: rgba(0,0,0,.55);
  display: flex; align-items: center; justify-content: center;
}
.mute-modal {
  background: #1e1e1e; border: 1px solid #333; border-radius: 12px;
  min-width: 280px; max-width: 340px; width: 100%;
  box-shadow: 0 8px 32px rgba(0,0,0,.5);
}
.mute-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; border-bottom: 1px solid #2a2a2a;
}
.mute-title { color: #e0e0e0; font-weight: 600; font-size: .95rem; }
.mute-close { background: none; border: none; color: #666; cursor: pointer; font-size: 1rem; }
.mute-options { display: flex; flex-direction: column; padding: 8px; gap: 2px; }
.mute-opt {
  padding: 10px 12px; border: none; border-radius: 8px;
  background: transparent; color: #ccc; font-size: .9rem;
  text-align: left; cursor: pointer; transition: background .15s;
}
.mute-opt:hover { background: #2a2a2a; color: #fff; }
.mute-opt.custom { color: #60a5fa; }
.mute-custom { padding: 8px 4px; display: flex; gap: 8px; flex-wrap: wrap; }
.mute-date-input {
  flex: 1; background: #111; border: 1px solid #333; border-radius: 6px;
  color: #ddd; padding: 6px 8px; font-size: .85rem;
}
.mute-apply {
  background: #3b82f6; color: #fff; border: none; border-radius: 6px;
  padding: 6px 14px; cursor: pointer; font-size: .85rem;
}
</style>
