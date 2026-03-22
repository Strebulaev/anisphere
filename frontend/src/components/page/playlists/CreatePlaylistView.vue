<template>
  <div class="create-playlist-page">
    <!-- Навигация -->
    <div class="breadcrumb">
      <router-link to="/playlists" class="breadcrumb-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        К плейлистам
      </router-link>
    </div>

    <div class="page-title-wrap">
      <div class="page-title-icon">📁</div>
      <div>
        <h1 class="page-title">Создание нового плейлиста</h1>
        <p class="page-subtitle">Соберите подборку аниме и поделитесь ей с сообществом</p>
      </div>
    </div>

    <div class="create-layout">
      <!-- Левая колонка: форма -->
      <div class="form-column">
        <div class="form-card">
          <h2 class="form-card-title">Основное</h2>

          <div class="form-group">
            <label class="form-label">
              Название <span class="req">*</span>
            </label>
            <input
              v-model="form.title"
              type="text"
              placeholder="Например: Топ романтических аниме"
              class="form-input"
              :class="{ error: titleError }"
              maxlength="100"
              @input="titleError = ''"
            />
            <div v-if="titleError" class="field-error">{{ titleError }}</div>
            <div class="field-hint">{{ form.title.length }}/100</div>
          </div>

          <div class="form-group">
            <label class="form-label">Описание</label>
            <textarea
              v-model="form.description"
              placeholder="Расскажите, что особенного в этой подборке..."
              class="form-textarea"
              rows="4"
              maxlength="500"
            ></textarea>
            <div class="field-hint">{{ form.description.length }}/500</div>
          </div>

          <div class="form-group">
            <label class="form-label">Видимость</label>
            <div class="privacy-options">
              <label
                v-for="opt in privacyOptions"
                :key="opt.value"
                :class="['privacy-option', { active: form.visibility === opt.value }]"
              >
                <input type="radio" :value="opt.value" v-model="form.visibility" style="display:none" />
                <div class="privacy-option-icon">{{ opt.icon }}</div>
                <div class="privacy-option-info">
                  <span class="privacy-option-label">{{ opt.label }}</span>
                  <span class="privacy-option-desc">{{ opt.desc }}</span>
                </div>
                <div class="privacy-option-check">
                  <svg v-if="form.visibility === opt.value" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
              </label>
            </div>
          </div>
        </div>

        <!-- Кнопка создания -->
        <div class="create-footer">
          <button @click="router.back()" class="btn-cancel">Отмена</button>
          <button
            @click="createPlaylist"
            :disabled="!canCreate || isCreating"
            class="btn-create"
          >
            <div v-if="isCreating" class="spinner-sm"></div>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ isCreating ? 'Создание...' : 'Создать плейлист' }}
          </button>
        </div>
      </div>

      <!-- Правая колонка: добавление аниме -->
      <div class="anime-column">
        <div class="form-card">
          <h2 class="form-card-title">
            🔍 Поиск аниме
            <span class="req">*</span>
          </h2>

          <!-- Поиск -->
          <div class="search-wrap">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="search-icon">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              v-model="searchQuery"
              @input="debouncedSearch"
              type="text"
              placeholder="Поиск по названию аниме..."
              class="search-input"
            />
            <button v-if="searchQuery" @click="clearSearch" class="search-clear">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <!-- Результаты поиска -->
          <div v-if="isSearching" class="search-loading">
            <div class="spinner-sm-dark"></div>
            <span>Поиск...</span>
          </div>

          <div v-else-if="searchResults.length > 0" class="search-results">
            <div class="results-label">Результаты поиска:</div>
            <div
              v-for="anime in searchResults"
              :key="anime.id"
              @click="addAnime(anime)"
              :class="['result-item', { added: isAdded(anime.id) }]"
            >
              <img
                v-if="anime.poster_url"
                :src="getMediaUrl(anime.poster_url)"
                :alt="anime.title_ru || anime.title_en"
                class="result-poster"
                @error="(e: Event) => ((e.target as HTMLImageElement).style.display='none')"
              />
              <div v-else class="result-poster-ph"></div>

              <div class="result-info">
                <span class="result-title">{{ anime.title_ru || anime.title_en }}</span>
                <span class="result-meta">
                  {{ anime.year }}{{ anime.episodes ? ` · ${anime.episodes} эп.` : '' }}
                  {{ anime.score ? ` · ⭐ ${anime.score.toFixed(1)}` : '' }}
                </span>
              </div>

              <button v-if="!isAdded(anime.id)" class="btn-add-result" type="button">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </button>
              <span v-else class="added-badge">✓</span>
            </div>
          </div>

          <div v-else-if="searchQuery.length >= 2 && !isSearching" class="search-empty">
            Ничего не найдено по запросу «{{ searchQuery }}»
          </div>
        </div>

        <!-- Добавленные аниме -->
        <div v-if="selectedAnime.length > 0" class="form-card added-section">
          <div class="added-header">
            <h2 class="form-card-title" style="margin-bottom:0">
              Добавленные аниме
            </h2>
            <span class="added-count-badge">{{ selectedAnime.length }}</span>
          </div>

          <div class="added-list">
            <div
              v-for="(anime, index) in selectedAnime"
              :key="anime.id"
              class="added-item"
            >
              <span class="added-num">{{ index + 1 }}</span>

              <img
                v-if="anime.poster_url"
                :src="getMediaUrl(anime.poster_url)"
                :alt="anime.title_ru || anime.title_en"
                class="added-poster"
                @error="(e: Event) => ((e.target as HTMLImageElement).style.display='none')"
              />
              <div v-else class="added-poster-ph"></div>

              <div class="added-info">
                <span class="added-title">{{ anime.title_ru || anime.title_en }}</span>
                <!-- Заметка -->
                <input
                  v-model="animeNotes[anime.id]"
                  type="text"
                  placeholder="Заметка (необязательно)..."
                  class="added-note-input"
                  maxlength="150"
                />
              </div>

              <button @click="removeAnime(index)" class="btn-remove-anime" type="button">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Подсказка если ничего не добавлено -->
        <div v-else class="hint-card">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="7" width="20" height="14" rx="2"/>
            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
          </svg>
          <p>Найдите и добавьте хотя бы одно аниме для создания плейлиста</p>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <Teleport to="body">
      <transition name="toast">
        <div v-if="toastMsg" class="toast-notification">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {{ toastMsg }}
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import apiClient, { getMediaUrl } from '@/api/client'
import playlistsApi from '@/api/playlists'
import type { Anime } from '@/types'

const router = useRouter()

const form = ref({
  title: '',
  description: '',
  visibility: 'public' as 'public' | 'private' | 'link'
})

const privacyOptions = [
  { value: 'public', label: 'Публичный', icon: '🌍', desc: 'Виден всем пользователям' },
  { value: 'private', label: 'Приватный', icon: '🔒', desc: 'Только для вас' },
  { value: 'link', label: 'По ссылке', icon: '🔗', desc: 'Доступен по уникальной ссылке' }
]

const searchQuery = ref('')
const searchResults = ref<Anime[]>([])
const isSearching = ref(false)
const selectedAnime = ref<Anime[]>([])
const animeNotes = ref<Record<number, string>>({})
const isCreating = ref(false)
const titleError = ref('')
const toastMsg = ref('')

let searchTimer: ReturnType<typeof setTimeout> | null = null

const canCreate = computed(() => {
  return form.value.title.trim().length >= 3 && selectedAnime.value.length >= 1
})

const debouncedSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }
  isSearching.value = true
  searchTimer = setTimeout(async () => {
    try {
      // Используем правильный API эндпоинт для поиска
      const res = await apiClient.get('/anime/search/', {
        params: { q: searchQuery.value, limit: 10 }
      })
      searchResults.value = res.data.results || []
    } catch {
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }, 300)
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
}

const isAdded = (animeId: number) => {
  return selectedAnime.value.some(a => a.id === animeId)
}

const addAnime = (anime: Anime) => {
  if (isAdded(anime.id)) return
  selectedAnime.value.push(anime)
  animeNotes.value[anime.id] = ''
}

const removeAnime = (index: number) => {
  const anime = selectedAnime.value[index]
  if (anime) {
    delete animeNotes.value[anime.id]
  }
  selectedAnime.value.splice(index, 1)
}

const createPlaylist = async () => {
  if (!canCreate.value) return

  if (form.value.title.trim().length < 3) {
    titleError.value = 'Название должно содержать минимум 3 символа'
    return
  }

  isCreating.value = true
  try {
    // Создаём плейлист
    const playlistRes = await playlistsApi.createPlaylist({
      title: form.value.title.trim(),
      description: form.value.description.trim() || undefined,
      visibility: form.value.visibility
    })

    const playlistId = playlistRes.data.id

    // Добавляем аниме по очереди
    let addedCount = 0
    let failedCount = 0
    for (const anime of selectedAnime.value) {
      try {
        await playlistsApi.addItemToPlaylist(playlistId, {
          anime: anime.id,
          notes: animeNotes.value[anime.id] || ''
        })
        addedCount++
      } catch (err: any) {
        console.warn(`Не удалось добавить аниме ${anime.id}:`, err)
        failedCount++
      }
    }

    if (failedCount > 0) {
      showToast(`Плейлист создан, но ${failedCount} аниме не удалось добавить`)
    } else {
      showToast(`Плейлист успешно создан! Добавлено ${addedCount} аниме 🎉`)
    }
    setTimeout(() => router.push(`/playlist/${playlistId}`), 800)

  } catch (err: any) {
    const msg = err.response?.data?.title?.[0] || err.response?.data?.detail || 'Ошибка создания плейлиста'
    titleError.value = msg
  } finally {
    isCreating.value = false
  }
}

const showToast = (msg: string) => {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = '' }, 3000)
}
</script>

<style scoped>
.create-playlist-page {
  padding: 2rem 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
}

/* Breadcrumb */
.breadcrumb { margin-bottom: 1.5rem; }
.breadcrumb-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  text-decoration: none;
  transition: color 0.2s;
}
.breadcrumb-link:hover { color: var(--color-accent); }

/* Заголовок */
.page-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
}
.page-title-icon { font-size: 2.5rem; flex-shrink: 0; }
.page-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-text);
  margin: 0 0 0.25rem;
}
.page-subtitle {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Layout */
.create-layout {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 1.5rem;
  align-items: start;
}

/* Form card */
.form-card {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: var(--radius-lg, 0.75rem);
  padding: 1.5rem;
  margin-bottom: 1rem;
}
.form-card-title {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 1.25rem;
}

.form-group { margin-bottom: 1.25rem; }
.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}
.req { color: var(--color-accent-pink); }
.form-input, .form-textarea {
  width: 100%;
  padding: 0.75rem 0.875rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  color: var(--color-text);
  background: var(--color-background-active);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  font-family: inherit;
}
.form-input:focus, .form-textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58,134,255,0.1);
  background: var(--color-background-surface);
}
.form-input.error { border-color: #ef4444; }
.form-textarea { resize: vertical; min-height: 100px; }
.field-error { font-size: 0.8125rem; color: #ef4444; margin-top: 0.375rem; }
.field-hint { font-size: 0.75rem; color: var(--color-text-tertiary); margin-top: 0.25rem; text-align: right; }

/* Privacy options */
.privacy-options { display: flex; flex-direction: column; gap: 0.5rem; }
.privacy-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.625rem;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}
.privacy-option:hover { border-color: var(--color-accent); }
.privacy-option.active {
  background: rgba(58,134,255,0.08);
  border-color: var(--color-accent);
}
.privacy-option-icon { font-size: 1.25rem; flex-shrink: 0; }
.privacy-option-info { flex: 1; }
.privacy-option-label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
}
.privacy-option-desc {
  display: block;
  font-size: 0.78rem;
  color: var(--color-text-tertiary);
}
.privacy-option-check {
  width: 22px;
  height: 22px;
  border: 2px solid var(--color-divider-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}
.privacy-option.active .privacy-option-check {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}

/* Create footer */
.create-footer {
  display: flex;
  gap: 0.75rem;
}
.btn-cancel {
  flex: 1;
  padding: 0.875rem;
  background: transparent;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.625rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.btn-cancel:hover { background: var(--color-background-active); }
.btn-create {
  flex: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem;
  background: var(--color-accent);
  border: none;
  border-radius: 0.625rem;
  font-size: 0.9375rem;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-create:hover:not(:disabled) {
  background: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(58,134,255,0.35);
}
.btn-create:disabled { opacity: 0.5; cursor: not-allowed; }

/* Search */
.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
}
.search-icon {
  position: absolute;
  left: 0.875rem;
  color: var(--color-text-tertiary);
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 2.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.625rem;
  font-size: 0.9375rem;
  color: var(--color-text);
  background: var(--color-background-active);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.search-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58,134,255,0.1);
  background: var(--color-background-surface);
}
.search-clear {
  position: absolute;
  right: 0.75rem;
  width: 26px; height: 26px;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: none;
  border-radius: 50%; color: var(--color-text-tertiary);
  cursor: pointer; transition: all 0.2s;
}
.search-clear:hover { background: var(--color-background-active); color: var(--color-text); }

.search-loading {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 1rem; color: var(--color-text-tertiary); font-size: 0.875rem;
}

.search-results { margin-top: 0.25rem; }
.results-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}
.result-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.15s;
}
.result-item:hover:not(.added) { background: var(--color-background-active); }
.result-item.added { opacity: 0.6; cursor: default; }
.result-poster {
  width: 40px; height: 56px;
  object-fit: cover; border-radius: 3px; flex-shrink: 0;
}
.result-poster-ph {
  width: 40px; height: 56px;
  background: var(--color-background-active);
  border-radius: 3px; flex-shrink: 0;
}
.result-info { flex: 1; min-width: 0; }
.result-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0.15rem;
}
.result-meta { font-size: 0.75rem; color: var(--color-text-tertiary); }
.btn-add-result {
  width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-accent); border: none; border-radius: 50%;
  color: #fff; cursor: pointer; flex-shrink: 0;
  transition: all 0.2s;
}
.btn-add-result:hover { background: var(--color-accent-hover); transform: scale(1.1); }
.added-badge {
  width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  background: rgba(34,197,94,0.15);
  border-radius: 50%;
  color: #22c55e;
  font-weight: 700;
  font-size: 0.875rem;
  flex-shrink: 0;
}
.search-empty {
  padding: 1.5rem;
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

/* Added section */
/* .added-section { } */

.added-header {
  display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;
}
.added-count-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px;
  background: var(--color-accent);
  color: #fff;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 700;
}
.added-list { display: flex; flex-direction: column; gap: 0.5rem; }
.added-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem;
  background: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
}
.added-num {
  width: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  text-align: center;
}
.added-poster {
  width: 36px; height: 50px;
  object-fit: cover; border-radius: 3px; flex-shrink: 0;
}
.added-poster-ph {
  width: 36px; height: 50px;
  background: var(--color-background-surface);
  border-radius: 3px; flex-shrink: 0;
}
.added-info { flex: 1; min-width: 0; }
.added-title {
  display: block;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0.25rem;
}
.added-note-input {
  width: 100%;
  padding: 0.375rem 0.5rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.375rem;
  font-size: 0.75rem;
  color: var(--color-text);
  outline: none;
  transition: border-color 0.2s;
}
.added-note-input:focus { border-color: var(--color-accent); }
.added-note-input::placeholder { color: var(--color-text-tertiary); }
.btn-remove-anime {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: none; border-radius: 0.375rem;
  color: var(--color-text-tertiary); cursor: pointer;
  flex-shrink: 0; transition: all 0.2s;
}
.btn-remove-anime:hover {
  background: rgba(239,68,68,0.1);
  color: #ef4444;
}

/* Hint card */
.hint-card {
  background: var(--color-background-surface);
  border: 1px dashed var(--color-divider-light);
  border-radius: var(--radius-lg, 0.75rem);
  padding: 2rem;
  text-align: center;
  color: var(--color-text-tertiary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.hint-card p { margin: 0; font-size: 0.9rem; }

/* Spinners */
.spinner-sm {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.spinner-sm-dark {
  width: 16px; height: 16px;
  border: 2px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Toast */
.toast-notification {
  position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 2rem;
  font-size: 0.875rem; font-weight: 600; color: var(--color-text);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
  z-index: 9999; white-space: nowrap;
}
.toast-notification svg { color: #22c55e; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from { opacity: 0; transform: translateX(-50%) translateY(16px); }
.toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

/* Responsive */
@media (max-width: 900px) {
  .create-layout { grid-template-columns: 1fr; }
}
@media (max-width: 767px) {
  .create-playlist-page { padding: 1rem; }
  .page-title { font-size: 1.375rem; }
  .create-footer { flex-direction: column; }
  .btn-cancel, .btn-create { flex: none; width: 100%; }
}
</style>
