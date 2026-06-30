<template>
  <div class="gf">
    <div class="gf-search">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        v-model="searchQuery"
        class="gf-search-input"
        placeholder="Жанр..."
        type="text"
      />
      <button v-if="searchQuery" class="gf-search-clear" @click="searchQuery = ''" type="button">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <div class="gf-scroll">
      <button
        :class="['gf-chip', { active: !modelValue || (Array.isArray(modelValue) && !modelValue.length) }]"
        @click="clearAll"
        type="button"
      >Все</button>

      <template v-if="loading">
        <div v-for="i in 16" :key="i" class="gf-chip-skeleton"></div>
      </template>

      <template v-else>
        <button
          v-for="g in filteredGenres"
          :key="g.title"
          :class="['gf-chip', { active: isActive(g.title) }]"
          @click="toggle(g.title)"
          type="button"
          :title="`${g.count} аниме`"
        >{{ g.title }}</button>
        <span v-if="searchQuery && filteredGenres.length === 0" class="gf-empty">Не найдено</span>
      </template>
    </div>

    <button
      v-if="hasSelection"
      class="gf-clear"
      @click="clearAll"
      type="button"
      title="Сбросить жанры"
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { KODIK_API_BASE, KODIK_API_TOKEN } from '../../config/kodik'

interface KodikGenre { title: string; count: number }

const props = defineProps<{ modelValue: string | string[] }>()
const emit  = defineEmits<{ 'update:modelValue': [v: string | string[]] }>()

const genres      = ref<KodikGenre[]>([])
const loading     = ref(true)
const searchQuery = ref('')

const filteredGenres = computed(() => {
  if (!searchQuery.value.trim()) return genres.value
  const q = searchQuery.value.toLowerCase()
  return genres.value.filter(g => g.title.toLowerCase().includes(q))
})

const isActive = (title: string) => {
  if (Array.isArray(props.modelValue)) return props.modelValue.includes(title)
  return props.modelValue === title
}

const hasSelection = computed(() => {
  if (Array.isArray(props.modelValue)) return props.modelValue.length > 0
  return !!props.modelValue
})

const toggle = (title: string) => {
  if (Array.isArray(props.modelValue)) {
    const cur = [...props.modelValue]
    const idx = cur.indexOf(title)
    if (idx === -1) cur.push(title)
    else cur.splice(idx, 1)
    emit('update:modelValue', cur)
  } else {
    emit('update:modelValue', props.modelValue === title ? '' : title)
  }
}

const clearAll = () => {
  emit('update:modelValue', Array.isArray(props.modelValue) ? [] : '')
}

onMounted(async () => {
  try {
    const url = new URL(`${KODIK_API_BASE}/genres`)
    url.searchParams.set('token', KODIK_API_TOKEN)
    url.searchParams.set('types', 'anime-serial')
    url.searchParams.set('sort', 'count')
    const res  = await fetch(url.toString())
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    if (Array.isArray(data.results)) {
      genres.value = (data.results as KodikGenre[]).filter(g => g.count >= 3)
    }
  } catch (e) {
    console.error('[GenreFilter] error:', e)
    genres.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.gf {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.gf-search {
  position: relative;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}
.gf-search svg {
  position: absolute;
  left: 8px;
  color: var(--text-tertiary);
  pointer-events: none;
}
.gf-search-input {
  width: 110px;
  height: 30px;
  padding: 0 26px 0 26px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-primary);
  font-size: var(--text-xs);
  outline: none;
  transition: border-color .15s, width .2s;
}
.gf-search-input:focus {
  border-color: var(--accent);
  width: 140px;
}
.gf-search-input::placeholder { color: var(--text-tertiary); }
.gf-search-clear {
  position: absolute; right: 8px;
  background: none; border: none;
  color: var(--text-tertiary); cursor: pointer;
  display: flex; padding: 2px;
}

.gf-scroll {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  flex: 1;
  padding-bottom: 2px;
  align-items: center;
}
.gf-scroll::-webkit-scrollbar { display: none; }

.gf-chip {
  flex-shrink: 0;
  height: 30px;
  padding: 0 12px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all .15s var(--ease-out);
}
.gf-chip:hover {
  background: var(--surface-5);
  color: var(--text-primary);
  border-color: var(--border-default);
}
.gf-chip.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
  box-shadow: 0 0 10px var(--accent-glow);
}

.gf-chip-skeleton {
  flex-shrink: 0; height: 30px; width: 68px;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: gf-sk 1.5s ease-in-out infinite;
}
.gf-chip-skeleton:nth-child(2n) { width: 82px; }
.gf-chip-skeleton:nth-child(3n) { width: 56px; }
.gf-chip-skeleton:nth-child(5n) { width: 96px; }
@keyframes gf-sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

.gf-empty {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
  padding: 0 var(--space-2);
}

.gf-clear {
  flex-shrink: 0; width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: var(--danger-subtle, rgba(239,68,68,.1));
  border: 1px solid var(--danger, #ef4444);
  border-radius: 50%;
  color: var(--danger, #ef4444);
  cursor: pointer;
  transition: all .15s;
}
.gf-clear:hover { background: var(--danger, #ef4444); color: white; }
</style>
