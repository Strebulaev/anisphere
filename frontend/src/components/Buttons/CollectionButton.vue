<template>
  <div class="col-btn-wrap" ref="wrapRef">
    <!-- Кнопка с текущим статусом -->
    <button
      class="col-btn"
      :class="{ 'has-status': !!libraryStatus }"
      :style="libraryStatus ? { borderColor: currentStatus?.color, color: currentStatus?.color } : {}"
      @click="toggleDropdown"
      :disabled="loading"
      type="button"
    >
      <svg v-if="!libraryStatus" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
        <polyline points="17 21 17 13 7 13 7 21"/>
        <polyline points="7 3 7 8 15 8"/>
      </svg>
      <span v-else class="status-icon">{{ currentStatus?.icon }}</span>
      <span class="col-label">{{ currentStatus?.label ?? 'В коллекцию' }}</span>
      <svg class="chevron" :class="{ open: dropOpen }" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>

    <!-- Дропдаун -->
    <Transition name="drop">
      <div v-if="dropOpen" class="col-drop">
        <div class="drop-label">Добавить в коллекцию</div>
        <button
          v-for="s in STATUS_LIST"
          :key="s.key"
          class="drop-item"
          :class="{ active: libraryStatus === s.key }"
          @click="selectStatus(s.key)"
        >
          <span class="di-icon">{{ s.icon }}</span>
          <span class="di-label">{{ s.label }}</span>
          <svg v-if="libraryStatus === s.key" class="di-check" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </button>
        <div v-if="libraryStatus" class="drop-sep"></div>
        <button v-if="libraryStatus" class="drop-item remove" @click="removeFromLibrary">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
          </svg>
          Удалить из коллекции
        </button>
      </div>
    </Transition>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import apiClient from '@/api/client'

const props = defineProps<{
  animeId: number | string
}>()

const STATUS_LIST = [
  { key: 'started',   icon: '▶️', label: 'В процессе',    color: 'var(--accent)'  },
  { key: 'completed', icon: '☑️', label: 'Просмотрено',   color: '#22c55e'        },
  { key: 'planned',   icon: '📅', label: 'Запланировано', color: '#a78bfa'        },
  { key: 'on_hold',   icon: '⏸️', label: 'Отложено',      color: '#f59e0b'        },
  { key: 'dropped',   icon: '✖️', label: 'Брошено',       color: '#ef4444'        },
]

const libraryStatus = ref<string | null>(null)
const libraryItemId = ref<number | null>(null)
const loading       = ref(false)
const dropOpen      = ref(false)
const wrapRef       = ref<HTMLElement | null>(null)

const currentStatus = computed(() =>
  STATUS_LIST.find(s => s.key === libraryStatus.value) ?? null
)

// ── Загрузка статуса ──────────────────────────────────────────
const checkLibrary = async () => {
  if (!props.animeId) return
  try {
    const res = await apiClient.get('/users/library/check_anime/', {
      params: { anime_id: props.animeId }
    })
    if (res.data.in_library) {
      libraryStatus.value = res.data.status
      // Загружаем ID элемента библиотеки
      const listRes = await apiClient.get('/users/library/', {
        params: { status: res.data.status }
      })
      const items = Array.isArray(listRes.data) ? listRes.data : (listRes.data.results ?? [])
      const found = items.find((i: any) => i.anime === Number(props.animeId))
      if (found) libraryItemId.value = found.id
    }
  } catch (e) { /* silent */ }
}

// ── Переключение ──────────────────────────────────────────────
const toggleDropdown = () => {
  dropOpen.value = !dropOpen.value
}

const selectStatus = async (status: string) => {
  dropOpen.value = false
  loading.value  = true
  try {
    if (libraryItemId.value) {
      // Обновляем существующий
      await apiClient.patch(`/users/library/${libraryItemId.value}/`, { status })
    } else {
      // Добавляем новый
      const res = await apiClient.post('/users/library/', {
        anime: props.animeId,
        status
      })
      libraryItemId.value = res.data.id
    }
    libraryStatus.value = status
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const removeFromLibrary = async () => {
  dropOpen.value = false
  if (!libraryItemId.value) return
  loading.value = true
  try {
    await apiClient.delete(`/users/library/${libraryItemId.value}/`)
    libraryStatus.value = null
    libraryItemId.value = null
  } catch (e) { console.error(e) } finally { loading.value = false }
}

// ── Клик вне компонента ───────────────────────────────────────
const onOutsideClick = (e: MouseEvent) => {
  if (wrapRef.value && !wrapRef.value.contains(e.target as Node)) {
    dropOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onOutsideClick, true)
  checkLibrary()
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onOutsideClick, true)
})

watch(() => props.animeId, () => checkLibrary())
</script>

<style scoped>
.col-btn-wrap {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  gap: 0;
}

/* ── Главная кнопка ──────────────────────────────────────────  */
.col-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0.625rem 1.1rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-base);
  white-space: nowrap;
}

.col-btn:hover { border-color: var(--border-default); color: var(--text-primary); background: var(--surface-4); }
.col-btn.has-status { background: var(--accent-subtle); border-color: currentColor; }

.col-label { flex: 1; }
.status-icon { font-size: 14px; line-height: 1; }

.chevron {
  transition: transform var(--duration-base);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.chevron.open { transform: rotate(180deg); }

/* ── Дропдаун ────────────────────────────────────────────────  */
.col-drop {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 500;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  padding: var(--space-1);
  min-width: 210px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.35);
}

.drop-label {
  padding: 6px var(--space-3) 4px;
  font-size: 10px;
  font-weight: 700;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.drop-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  height: 34px;
  padding: 0 var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-base);
  text-align: left;
}

.drop-item:hover { background: var(--surface-4); color: var(--text-primary); }
.drop-item.active { color: var(--accent); background: var(--accent-subtle); }
.drop-item.remove { color: var(--danger); }
.drop-item.remove:hover { background: rgba(239,68,68,0.1); }

.di-icon { font-size: 14px; line-height: 1; }
.di-label { flex: 1; font-weight: 500; }
.di-check { color: var(--accent); flex-shrink: 0; }

.drop-sep { height: 1px; background: var(--border-subtle); margin: 3px 0; }

/* Анимация */
.drop-enter-active,
.drop-leave-active { transition: opacity .15s, transform .15s; }
.drop-enter-from,
.drop-leave-to { opacity: 0; transform: translateY(-6px) scale(0.96); }
</style>
