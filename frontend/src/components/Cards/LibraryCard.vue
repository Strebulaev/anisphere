<template>
  <div class="lib-card" :class="`st-${item.status}`">

    <!-- ── ПОСТЕР ──────────────────────────────────────────── -->
    <div class="poster-wrap" @click="goAnime">
      <OptimizedImage
        v-if="posterUrl && !posterFailed"
        :src="posterUrl"
        :alt="title"
        class="poster-img"
        @error="posterFailed = true"
      />
      <div v-else class="poster-ph">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="2" y="2" width="20" height="20" rx="3"/>
          <circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
        </svg>
      </div>

      <!-- Бейдж статуса -->
      <div class="status-pill" :style="{ background: STATUS[item.status]?.color }">
        {{ STATUS[item.status]?.icon }}
      </div>

      <!-- Кнопки действий (сверху справа) -->
      <div class="card-action-btns">
        <button
          class="card-action-btn fav-btn"
          :class="{ active: item.is_favorite }"
          title="Избранное"
          @click.stop="toggleFav"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" :fill="item.is_favorite ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
        </button>
        <button
          class="card-action-btn discuss-btn"
          title="Обсудить"
          @click.stop="handleDiscuss"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </button>
        <button
          class="card-action-btn playlist-btn"
          title="Добавить в плейлист"
          @click.stop="showPlaylistModal = true"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
          </svg>
        </button>
        <button
          class="card-action-btn reminder-btn"
          title="Напоминание"
          @click.stop="showReminderModal = true"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="13" r="8"/>
            <path d="M12 9v4l2 2"/>
            <path d="M5 5a3 3 0 0 1 3-3V3"/>
          </svg>
        </button>
      </div>

      <!-- Прогресс снизу -->
      <div v-if="showProgress" class="prog-bar">
        <div class="prog-fill" :style="{ width: item.progress_percentage + '%' }"></div>
      </div>

      <!-- Оверлей при наведении -->
      <div class="poster-overlay">
        <button class="ov-play" @click.stop="watchNow" :title="playLabel">
          <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </button>
        <!-- <button class="ov-more" @click.stop="openMenu" title="Ещё">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
          </svg>
        </button> -->
      </div>
    </div>

    <!-- ── ИНФО ────────────────────────────────────────────── -->
    <div class="card-meta">
      <h3 class="card-title" @click="goAnime" :title="title">{{ title }}</h3>

      <!-- Прогресс для смотрящих -->
      <div v-if="showProgress" class="prog-row">
        <span class="ep-txt">{{ item.current_episode }}/{{ item.anime_episodes_count || '?' }}</span>
        <span class="ep-pct">{{ item.progress_percentage }}%</span>
      </div>

      <!-- Оценка -->
      <div v-if="item.rating" class="rating-row">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="var(--warning)" stroke="none">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
        <span class="rating-num">{{ item.rating }}/10</span>
      </div>

      <!-- Дата -->
      <span class="date-lbl">{{ dateLabel }}</span>

      <!-- Кнопки действий -->
      <div class="quick-row">
        <button class="qa-primary" @click.stop="watchNow">{{ playLabel }}</button>
        <button v-if="item.status === 'started'" class="qa-done" title="Просмотрено" @click.stop="setStatus('completed')">✓</button>
        <button class="qa-menu" title="Ещё" @click.stop="openMenu">⋯</button>
      </div>
    </div>

    <!-- ── КОНТЕКСТНОЕ МЕНЮ ────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="menuOpen" class="ctx-back" @click="menuOpen = false"></div>
      <div v-if="menuOpen" class="ctx-menu" :style="menuPos">

        <button class="ctx-item" @click="goAnime">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
            <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
          Страница аниме
        </button>
        <button class="ctx-item" @click="watchNow">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          Смотреть
        </button>

        <div class="ctx-sep"></div>

        <button
          v-for="s in STATUS_LIST"
          :key="s.key"
          class="ctx-item"
          :class="{ active: item.status === s.key }"
          @click="setStatus(s.key)"
        >
          <span>{{ s.icon }}</span> {{ s.label }}
        </button>

        <div class="ctx-sep"></div>

        <button class="ctx-item" @click="toggleFav">
          <span>{{ item.is_favorite ? '<SakuraIcon name="heart" />' : '<SakuraIcon name="star" />' }}</span>
          {{ item.is_favorite ? 'Убрать из избранного' : 'В избранное' }}
        </button>
        <button class="ctx-item" @click="openEdit">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 1 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Редактировать
        </button>
        <button class="ctx-item danger" @click="deleteItem">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
            <path d="M10 11v6M14 11v6M9 6V4h6v2"/>
          </svg>
          Удалить
        </button>
      </div>
    </Teleport>

    <!-- ── МОДАЛКИ ПЛЕЙЛИСТА И НАПОМИНАНИЯ ──────────────── -->
    <PlaylistSelectModal
      :show="showPlaylistModal"
      :anime="animeForModal"
      :playlists="playlists"
      :is-loading="playlistsLoading"
      @close="showPlaylistModal = false"
      @save="onAddedToPlaylist"
      @create-playlist="handleCreatePlaylist"
    />

    <!-- Модалка создания нового плейлиста -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showCreateModal" @click.self="showCreateModal = false" style="position:fixed;inset:0;background:rgba(0,0,0,0.8);backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;z-index:10001;padding:1rem;">
          <div style="background:var(--surface-2);border-radius:1rem;max-width:420px;width:100%;padding:1.5rem;box-shadow:0 25px 50px -12px rgba(0,0,0,0.5);display:flex;flex-direction:column;gap:1rem;">
            <h3 style="margin:0;font-size:1.1rem;font-weight:700;color:var(--text-primary);">Новый плейлист</h3>
            <input
              v-model="newPlaylistTitle"
              placeholder="Название плейлиста"
              @keydown.enter="saveNewPlaylist"
              autofocus
              style="height:38px;padding:0 12px;background:var(--surface-3);border:1px solid var(--border-subtle);border-radius:var(--radius-md);color:var(--text-primary);font-size:var(--text-sm);outline:none;width:100%;box-sizing:border-box;"
            />
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:var(--text-sm);color:var(--text-secondary);">
              <input type="checkbox" v-model="newPlaylistPublic" />
              Публичный
            </label>
            <div style="display:flex;gap:8px;justify-content:flex-end;">
              <button @click="showCreateModal = false" style="height:36px;padding:0 16px;background:var(--surface-4);color:var(--text-secondary);border:1px solid var(--border-subtle);border-radius:var(--radius-md);cursor:pointer;font-size:var(--text-sm);">Отмена</button>
              <button @click="saveNewPlaylist" :disabled="!newPlaylistTitle.trim() || creatingPlaylist" style="height:36px;padding:0 16px;background:var(--accent);color:white;border:none;border-radius:var(--radius-md);cursor:pointer;font-size:var(--text-sm);font-weight:600;" :style="{ opacity: !newPlaylistTitle.trim() || creatingPlaylist ? '0.5' : '1' }">{{ creatingPlaylist ? 'Создание...' : 'Создать' }}</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
    <ReminderModal
      :show="showReminderModal"
      :anime="animeForModal"
      @close="showReminderModal = false"
      @save="handleReminderSave"
    />

    <!-- ── МОДАЛКА РЕДАКТИРОВАНИЯ ─────────────────────────── -->
    <Teleport to="body">
      <div v-if="editOpen" class="modal-back" @click.self="editOpen = false">
        <div class="edit-modal">
          <div class="em-header">
            <div>
              <h3 class="em-title">{{ title }}</h3>
              <p class="em-sub">Редактировать запись</p>
            </div>
            <button class="em-close" @click="editOpen = false">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <div class="em-body">

            <!-- Статус -->
            <div class="em-field">
              <label class="em-label">Статус</label>
              <div class="status-grid">
                <button
                  v-for="s in STATUS_LIST"
                  :key="s.key"
                  class="sg-opt"
                  :class="{ sel: editForm.status === s.key }"
                  @click="editForm.status = s.key"
                >
                  <span class="sg-icon">{{ s.icon }}</span>
                  <span class="sg-lbl">{{ s.label }}</span>
                </button>
              </div>
            </div>

            <!-- Эпизод -->
            <div v-if="editForm.status === 'started' || editForm.status === 'on_hold'" class="em-field">
              <label class="em-label">
                Эпизод
                <span class="em-hint">из {{ item.anime_episodes_count || '?' }}</span>
              </label>
              <div class="ep-row">
                <button class="ep-adj" @click="editForm.current_episode = Math.max(0, editForm.current_episode - 1)">−</button>
                <input type="number" class="ep-in" v-model.number="editForm.current_episode" :min="0" :max="item.anime_episodes_count || 9999" />
                <button class="ep-adj" @click="editForm.current_episode++">+</button>
              </div>
            </div>

            <!-- Оценка -->
            <div class="em-field">
              <label class="em-label">Оценка</label>
              <div class="stars-row">
                <button
                  v-for="n in 10" :key="n"
                  class="star-b"
                  @mouseenter="hoverR = n"
                  @mouseleave="hoverR = 0"
                  @click="editForm.rating = editForm.rating === n ? null : n"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24"
                    :fill="n <= (hoverR || editForm.rating || 0) ? 'var(--warning)' : 'none'"
                    stroke="var(--warning)" stroke-width="1.5">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                  </svg>
                </button>
                <span v-if="editForm.rating" class="rating-disp">{{ editForm.rating }}/10</span>
                <button v-if="editForm.rating" class="clear-r" @click="editForm.rating = null">✕</button>
              </div>
            </div>

            <!-- Избранное -->
            <div class="em-field">
              <label class="em-toggle-row" @click="editForm.is_favorite = !editForm.is_favorite">
                <span class="em-label" style="margin:0"><SakuraIcon name="star" /> В избранном</span>
                <div class="toggle" :class="{ on: editForm.is_favorite }">
                  <div class="toggle-thumb"></div>
                </div>
              </label>
            </div>

            <!-- Заметка -->
            <div class="em-field">
              <label class="em-label">Заметка</label>
              <textarea class="em-note" v-model="editForm.notes" placeholder="Мысли об аниме..." rows="3"></textarea>
            </div>

          </div>

          <div class="em-footer">
            <button class="em-cancel" @click="editOpen = false">Отмена</button>
            <button class="em-save" :disabled="saving" @click="saveEdit">
              <svg v-if="saving" class="spin-ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
              </svg>
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>

        </div>
      </div>
    </Teleport>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'
import { getMediaUrl } from '@/api/client'
import { PlaylistSelectModal, ReminderModal } from '@/components/Modals'
import playlistsApi from '@/api/playlists'
import { animeDiscussionsApi } from '@/api/animeDiscussions'
import remindersApi from '@/api/reminders'
import { useToast } from '@/composables/useToast'

const props = defineProps<{ item: any }>()
const emit  = defineEmits<{ updated: []; deleted: [] }>()
const router = useRouter()

// ── Статусы ───────────────────────────────────────────────────
const STATUS: Record<string, { icon: string; color: string; label: string }> = {
  started:   { icon: '▶️', color: 'var(--accent)',  label: 'В процессе'    },
  completed: { icon: '☑️', color: '#22c55e',         label: 'Просмотрено'   },
  planned:   { icon: '📅', color: '#a78bfa',         label: 'Запланировано' },
  on_hold:   { icon: '⏸️', color: '#f59e0b',         label: 'Отложено'      },
  dropped:   { icon: '✖️', color: '#ef4444',         label: 'Брошено'       },
  favorite:  { icon: '🌠', color: '#f59e0b',         label: 'Избранное'     },
}

const STATUS_LIST = [
  { key: 'started',   ...STATUS.started   },
  { key: 'completed', ...STATUS.completed },
  { key: 'planned',   ...STATUS.planned   },
  { key: 'on_hold',   ...STATUS.on_hold   },
  { key: 'dropped',   ...STATUS.dropped   },
]

// ── Вычисляемые ───────────────────────────────────────────────
const title = computed(() => props.item.anime_title_ru || props.item.anime_title_en || '—')

const posterUrl = computed(() => {
  if (!props.item.anime_poster) return null
  return getMediaUrl(props.item.anime_poster)
})

const showProgress = computed(() =>
  props.item.status === 'started' || props.item.status === 'on_hold'
)

const playLabel = computed(() => {
  if (props.item.status === 'planned')   return 'Начать'
  if (props.item.status === 'completed') return 'Пересмотреть'
  return 'Продолжить'
})

const dateLabel = computed(() => {
  const fmt = (d: string | null) => {
    if (!d) return null
    const date = new Date(d)
    const diff = Math.floor((Date.now() - date.getTime()) / 86400000)
    if (diff === 0) return 'сегодня'
    if (diff === 1) return 'вчера'
    if (diff < 7)  return `${diff} дн. назад`
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
  }
  const s = props.item.status
  if (s === 'completed' && props.item.completed_at) return 'Завершено ' + fmt(props.item.completed_at)
  if (s === 'started'   && props.item.updated_at)   return 'Смотрел '  + fmt(props.item.updated_at)
  return 'Добавлено ' + (fmt(props.item.added_at) ?? '—')
})

// ── Состояние ─────────────────────────────────────────────────
const posterFailed      = ref(false)
const menuOpen          = ref(false)
const menuPos           = ref<Record<string, string>>({})
const editOpen          = ref(false)
const saving            = ref(false)
const hoverR            = ref(0)
const showPlaylistModal = ref(false)
const showReminderModal = ref(false)
const showCreateModal   = ref(false)
const newPlaylistTitle  = ref('')
const newPlaylistPublic = ref(false)
const creatingPlaylist  = ref(false)
const playlists         = ref<any[]>([])
const playlistsLoading  = ref(false)

const toast = useToast()

// Объект аниме для модалок
const animeForModal = computed(() => ({
  id: props.item.anime,
  title_ru: props.item.anime_title_ru,
  title_en: props.item.anime_title_en || '',
  poster_url: props.item.anime_poster || null,
  poster_image_url: props.item.anime_poster || null,
} as any))

const loadPlaylists = async () => {
  playlistsLoading.value = true
  try {
    const res = await playlistsApi.getMyPlaylists()
    playlists.value = res.data || []
  } catch {} finally {
    playlistsLoading.value = false
  }
}

watch(showPlaylistModal, (v) => { if (v) loadPlaylists() })

const onAddedToPlaylist = async (data: any) => {
  try {
    const promises = data.playlistIds.map((pid: number) =>
      playlistsApi.addItemToPlaylist(pid, {
        anime: data.animeId,
        notes: data.note || ''
      })
    )
    await Promise.all(promises)
    showPlaylistModal.value = false
    toast.success('Аниме добавлено в плейлист!')
  } catch (e: any) {
    toast.error(e.response?.data?.detail || 'Не удалось добавить в плейлист')
  }
}

const handleCreatePlaylist = () => {
  showPlaylistModal.value = false
  newPlaylistTitle.value = ''
  newPlaylistPublic.value = false
  showCreateModal.value = true
}

const saveNewPlaylist = async () => {
  if (!newPlaylistTitle.value.trim() || creatingPlaylist.value) return
  creatingPlaylist.value = true
  try {
    await playlistsApi.createPlaylist({
      title: newPlaylistTitle.value.trim(),
      visibility: newPlaylistPublic.value ? 'public' : 'private'
    })
    showCreateModal.value = false
    toast.success('Плейлист создан!')
    await loadPlaylists()
    showPlaylistModal.value = true
  } catch (e: any) {
    toast.error(e.response?.data?.detail || 'Не удалось создать плейлист')
  } finally {
    creatingPlaylist.value = false
  }
}

const handleDiscuss = async () => {
  try {
    let group
    try {
      group = await animeDiscussionsApi.getDiscussionGroup(props.item.anime)
    } catch (e: any) {
      if (e.response?.status === 404) {
        group = await animeDiscussionsApi.createDiscussionGroup(props.item.anime)
      } else throw e
    }
    if (!group.user_joined) group = await animeDiscussionsApi.joinDiscussionGroup(props.item.anime)
    router.push(`/chats/${group.id}`)
  } catch (e: any) {
    toast.error(e.response?.data?.detail || 'Не удалось открыть обсуждение')
  }
}

const handleReminderSave = async (data: any) => {
  try {
    await remindersApi.createReminder({
      anime_id: props.item.anime,
      reminder_time: new Date(data.reminderTime).toISOString(),
      repeat_weekly: data.repeatWeekly || false,
      repeat_interval_days: data.repeatIntervalDays,
      end_date: data.endDate ? new Date(data.endDate).toISOString().slice(0, 10) : undefined,
      comment: data.comment || ''
    })
    toast.success('Напоминание установлено!')
    showReminderModal.value = false
  } catch (e: any) {
    toast.error(e.response?.data?.error || 'Не удалось установить напоминание')
  }
}

const editForm = reactive({
  status:          props.item.status,
  current_episode: props.item.current_episode,
  rating:          props.item.rating as number | null,
  notes:           props.item.notes ?? '',
  is_favorite:     props.item.is_favorite,
})

// ── Действия ─────────────────────────────────────────────────
const goAnime  = () => router.push(`/anime/${props.item.anime}`)

const watchNow = () => {
  menuOpen.value = false
  const ep = props.item.status === 'completed' ? 1 : (props.item.current_episode || 1)
  router.push(`/anime/${props.item.anime}/watch?episode=${ep}`)
}

const openMenu = (e: MouseEvent) => {
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  menuPos.value = {
    top:  Math.min(rect.bottom + 4, window.innerHeight - 360) + 'px',
    left: Math.min(rect.left, window.innerWidth - 220) + 'px',
  }
  menuOpen.value = true
}

const openEdit = () => {
  menuOpen.value = false
  Object.assign(editForm, {
    status:          props.item.status,
    current_episode: props.item.current_episode,
    rating:          props.item.rating,
    notes:           props.item.notes ?? '',
    is_favorite:     props.item.is_favorite,
  })
  editOpen.value = true
}

const setStatus = async (status: string) => {
  menuOpen.value = false
  try {
    await apiClient.patch(`/users/library/${props.item.id}/`, { status })
    emit('updated')
  } catch (e) { console.error(e) }
}

const toggleFav = async () => {
  menuOpen.value = false
  try {
    await apiClient.post(`/users/library/${props.item.id}/mark_favorite/`)
    emit('updated')
  } catch (e) { console.error(e) }
}

const deleteItem = async () => {
  menuOpen.value = false
  if (!confirm(`Удалить "${title.value}" из коллекции?`)) return
  try {
    await apiClient.delete(`/users/library/${props.item.id}/`)
    emit('deleted')
  } catch (e) { console.error(e) }
}

const saveEdit = async () => {
  saving.value = true
  try {
    await apiClient.patch(`/users/library/${props.item.id}/`, {
      status:           editForm.status,
      current_episode:  editForm.current_episode,
      episodes_watched: editForm.current_episode,
      rating:           editForm.rating,
      notes:            editForm.notes,
      is_favorite:      editForm.is_favorite,
    })
    editOpen.value = false
    emit('updated')
  } catch (e) { console.error(e) } finally { saving.value = false }
}
</script>

<style scoped>
/* ═══ КАРТОЧКА ═══════════════════════════════════════════════ */
.lib-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: transform var(--duration-slow) var(--ease-out);
}

.lib-card:hover { transform: translateY(-3px); }

/* ═══ ПОСТЕР ════════════════════════════════════════════════ */
.poster-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-4);
  cursor: pointer;
}

.poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-slow) var(--ease-out);
}

.lib-card:hover .poster-img { transform: scale(1.05); }

.poster-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

/* Кнопки действий (сверху справа) */
.card-action-btns {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  flex-direction: row;
  gap: 3px;
  opacity: 0;
  transform: translateY(-6px);
  transition: opacity var(--duration-base) var(--ease-out), transform var(--duration-base) var(--ease-out);
  z-index: 10;
}

.lib-card:hover .card-action-btns {
  opacity: 1;
  transform: translateY(0);
}

.card-action-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: none;
  background: rgba(8, 8, 9, 0.8);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}

.card-action-btn:hover { background-color: var(--accent); transform: scale(1.1); }
.card-action-btn.fav-btn.active { color: var(--danger); background-color: rgba(239,68,68,0.85); }
.card-action-btn.fav-btn.active:hover { background-color: var(--danger); }
.card-action-btn.discuss-btn:hover { background-color: var(--accent); }
.card-action-btn.playlist-btn:hover { background-color: var(--accent-2, var(--accent)); }
.card-action-btn.reminder-btn:hover { background-color: var(--warning); }

/* Мобильные — всегда видимые */
@media (max-width: 767px) {
  .card-action-btns { opacity: 1; transform: translateY(0); }
  .card-action-btn { width: 24px; height: 24px; }
}

/* Статус-бейдж */
.status-pill {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 25px;
  height: 25px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.35);
}

/* (fav-btn styles moved to .card-action-btns section) */

/* Прогресс */
.prog-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(0,0,0,0.35);
}

.prog-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.4s ease;
}

/* Оверлей */
.poster-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  opacity: 0;
  transition: opacity 0.15s ease-out;
  z-index: 4;
  pointer-events: none;
}

.lib-card:hover .poster-overlay {
  opacity: 1;
  pointer-events: auto;
}

/* Квадратные синие кнопки с анимацией распыления */
.ov-play, .ov-more {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  border: none;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(6px);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  transform: scale(0.6);
  box-shadow: 0 0 0 0 rgba(124, 92, 252, 0);
}

.lib-card:hover .ov-play,
.lib-card:hover .ov-more {
  transform: scale(1);
  box-shadow: 0 0 20px 3px rgba(124, 92, 252, 0.4);
}

.ov-play {
  width: 64px;
  height: 64px;
  background: var(--accent);
  padding-left: 4px;
}

.lib-card:hover .ov-play {
  box-shadow: 0 0 30px 5px rgba(124, 92, 252, 0.5);
}

.ov-play:hover { 
  background: var(--accent-hover);
  transform: scale(1.2);
  box-shadow: 0 0 40px 10px rgba(124, 92, 252, 0.6);
}

.ov-more:hover { 
  background: rgba(255,255,255,0.28);
  transform: scale(1.15);
}

.ov-play svg, .ov-more svg {
  width: 24px;
  height: 24px;
}

/* ═══ ИНФО ══════════════════════════════════════════════════ */
.card-meta {
  padding: 0 2px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
  cursor: pointer;
}

.card-title:hover { color: var(--accent); }

.prog-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ep-txt { font-size: var(--text-xs); color: var(--text-secondary); }
.ep-pct { font-size: 10px; font-weight: 600; color: var(--accent); }

.rating-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rating-num { font-size: 11px; font-weight: 600; color: var(--warning); }

.date-lbl {
  font-size: 10px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Быстрые действия */
.quick-row {
  display: flex;
  gap: 4px;
  margin-top: 2px;
}

.qa-primary {
  flex: 1;
  height: 26px;
  padding: 0 var(--space-2);
  background: var(--accent-subtle);
  color: var(--accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration-base);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qa-primary:hover { background: var(--accent); color: white; }

.qa-done, .qa-menu {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-base);
}

.qa-done:hover, .qa-menu:hover { background: var(--surface-5); color: var(--text-primary); }

/* ═══ КОНТЕКСТНОЕ МЕНЮ ══════════════════════════════════════ */
.ctx-back {
  position: fixed; inset: 0; z-index: 1100;
}

.ctx-menu {
  position: fixed;
  z-index: 1101;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  padding: var(--space-1);
  min-width: 200px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
  animation: pop-in 0.12s var(--ease-out);
}

@keyframes pop-in {
  from { opacity: 0; transform: scale(0.94) translateY(-4px); }
  to   { opacity: 1; transform: none; }
}

.ctx-item {
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
  text-align: left;
  transition: all var(--duration-base);
}

.ctx-item:hover { background: var(--surface-4); color: var(--text-primary); }
.ctx-item.active { color: var(--accent); background: var(--accent-subtle); }
.ctx-item.danger { color: var(--danger); }
.ctx-item.danger:hover { background: rgba(239,68,68,0.1); }

.ctx-sep { height: 1px; background: var(--border-subtle); margin: 3px 0; }

/* ═══ МОДАЛКА РЕДАКТИРОВАНИЯ ════════════════════════════════ */
.modal-back {
  position: fixed;
  inset: 0;
  z-index: 1200;
  background: rgba(0,0,0,0.65);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-4);
  animation: fb .15s var(--ease-out);
}

@keyframes fb { from { opacity: 0; } to { opacity: 1; } }

.edit-modal {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-2xl);
  width: 100%;
  max-width: 460px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  animation: slide-up .2s var(--ease-out);
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(14px) scale(0.97); }
  to   { opacity: 1; transform: none; }
}

.em-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}

.em-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  display: -webkit-box;
  line-clamp: 2;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.35;
}

.em-sub { font-size: var(--text-xs); color: var(--text-tertiary); margin: 3px 0 0 0; }

.em-close {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: var(--surface-4);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--duration-base);
}

.em-close:hover { background: var(--surface-5); color: var(--text-primary); }

.em-body {
  padding: var(--space-5);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.em-field { display: flex; flex-direction: column; gap: var(--space-2); }

.em-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
}

.em-hint { font-weight: 400; color: var(--text-tertiary); margin-left: var(--space-2); }

/* Статус */
.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}

.sg-opt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--space-3) var(--space-2);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-base);
}

.sg-opt:hover { background: var(--surface-4); border-color: var(--border-default); }
.sg-opt.sel   { background: var(--accent-subtle); border-color: var(--accent); }

.sg-icon { font-size: 18px; line-height: 1; }
.sg-lbl  { font-size: 10px; font-weight: 500; color: var(--text-secondary); text-align: center; }
.sg-opt.sel .sg-lbl { color: var(--accent); }

/* Эпизод */
.ep-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.ep-adj {
  width: 34px;
  height: 34px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-base);
}

.ep-adj:hover { background: var(--surface-4); }

.ep-in {
  flex: 1;
  height: 34px;
  text-align: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-base);
  font-weight: 600;
  outline: none;
}

.ep-in:focus { border-color: var(--accent); }

/* Оценка */
.stars-row {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}

.star-b {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  line-height: 0;
  transition: transform var(--duration-base);
}

.star-b:hover { transform: scale(1.2); }

.rating-disp { font-size: var(--text-sm); font-weight: 700; color: var(--warning); margin-left: 4px; }

.clear-r {
  background: none;
  border: none;
  color: var(--text-tertiary);
  font-size: 12px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
}

.clear-r:hover { color: var(--danger); }

/* Тоггл */
.em-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.toggle {
  width: 40px;
  height: 22px;
  border-radius: var(--radius-full);
  background: var(--surface-5);
  position: relative;
  transition: background var(--duration-base);
}

.toggle.on { background: var(--accent); }

.toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  transition: transform var(--duration-base);
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.toggle.on .toggle-thumb { transform: translateX(18px); }

/* Заметка */
.em-note {
  width: 100%;
  padding: var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  font-size: var(--text-sm);
  line-height: 1.5;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
}

.em-note:focus { border-color: var(--accent); }
.em-note::placeholder { color: var(--text-tertiary); }

/* Футер */
.em-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--border-subtle);
}

.em-cancel {
  height: 36px;
  padding: 0 var(--space-5);
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
}

.em-cancel:hover { background: var(--surface-5); color: var(--text-primary); }

.em-save {
  height: 36px;
  padding: 0 var(--space-6);
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  transition: all var(--duration-base);
}

.em-save:hover:not(:disabled) { background: var(--accent-hover); }
.em-save:disabled { opacity: 0.6; cursor: not-allowed; }

@keyframes spin { to { transform: rotate(360deg); } }
.spin-ic { animation: spin 0.8s linear infinite; }
</style>