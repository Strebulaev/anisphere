<template>
  <Teleport to="body">`n  <Transition name="gen-anim">
    <div v-if="show" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content playlist-create-modal">
        <div class="modal-header">
          <h2 class="modal-title">РЎРѕР·РґР°С‚СЊ РЅРѕРІС‹Р№ РїР»РµР№Р»РёСЃС‚</h2>
          <button @click="handleClose" class="modal-close" type="button">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-section">
            <div class="form-group">
              <label class="form-label required">РќР°Р·РІР°РЅРёРµ</label>
              <input
                v-model="formData.title"
                type="text"
                placeholder="Р’РІРµРґРёС‚Рµ РЅР°Р·РІР°РЅРёРµ РїР»РµР№Р»РёСЃС‚Р°"
                class="form-input"
                maxlength="100"
              />
            </div>

            <div class="form-group">
              <label class="form-label">РћРїРёСЃР°РЅРёРµ</label>
              <textarea
                v-model="formData.description"
                placeholder="РћРїРёСЃР°РЅРёРµ РїР»РµР№Р»РёСЃС‚Р° (РЅРµРѕР±СЏР·Р°С‚РµР»СЊРЅРѕ)"
                class="form-textarea"
                rows="3"
                maxlength="500"
              ></textarea>
            </div>

            <div class="form-group">
              <label class="form-label">РџСЂРёРІР°С‚РЅРѕСЃС‚СЊ</label>
              <div class="privacy-options">
                <label
                  v-for="option in privacyOptions"
                  :key="option.value"
                  :class="['privacy-option', { active: formData.privacy === option.value }]"
                >
                  <input
                    v-model="formData.privacy"
                    type="radio"
                    :value="option.value"
                    class="privacy-radio"
                  />
                  <span class="privacy-icon">{{ option.icon }}</span>
                  <span class="privacy-label">{{ option.label }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="anime-section">
            <label class="form-label required">Р”РѕР±Р°РІРёС‚СЊ Р°РЅРёРјРµ</label>
            <div class="search-wrapper">
              <div class="search-input-container">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="search-icon">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <input
                  v-model="searchQuery"
                  @input="handleSearch"
                  type="text"
                  placeholder="РџРѕРёСЃРє Р°РЅРёРјРµ РїРѕ РЅР°Р·РІР°РЅРёСЋ..."
                  class="search-input"
                />
                <button
                  v-if="searchQuery"
                  @click="clearSearch"
                  class="search-clear"
                  type="button"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
            </div>

            <div v-if="isSearching" class="search-loading">
              <div class="loading-spinner"></div>
              <span>РџРѕРёСЃРє...</span>
            </div>

            <div v-else-if="searchResults.length > 0" class="search-results">
              <div
                v-for="anime in searchResults"
                :key="anime.id"
                @click="addAnime(anime)"
                class="anime-result"
              >
                <img
                  v-if="anime.poster_url"
                  :src="getMediaUrl(anime.poster_url) || undefined"
                  :alt="anime.title_ru || anime.title_en"
                  class="anime-poster"
                />
                <div v-else class="anime-poster-placeholder">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="2" width="20" height="20" rx="2"/>
                    <path d="M12 2v20M2 12h20"/>
                  </svg>
                </div>
                <div class="anime-info">
                  <span class="anime-title">{{ anime.title_ru || anime.title_en }}</span>
                  <span v-if="anime.year || anime.episodes" class="anime-meta">
                    {{ anime.year }}{{ anime.year && anime.episodes ? ' вЂў ' : '' }}{{ anime.episodes }} СЌРї.
                  </span>
                </div>
                <button type="button" class="btn-add">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <line x1="5" y1="12" x2="19" y2="12"/>
                  </svg>
                </button>
              </div>
            </div>

            <div v-if="selectedAnime.length > 0" class="selected-anime">
              <div class="selected-header">
                <span class="selected-count">Р’С‹Р±СЂР°РЅРѕ: {{ selectedAnime.length }} Р°РЅРёРјРµ</span>
              </div>
              <div class="anime-list">
                <div
                  v-for="(anime, index) in selectedAnime"
                  :key="anime.id"
                  class="selected-anime-item"
                >
                  <img
                    v-if="anime.poster_url"
                    :src="getMediaUrl(anime.poster_url) || undefined"
                    :alt="anime.title_ru || anime.title_en"
                    class="anime-poster"
                  />
                  <div v-else class="anime-poster-placeholder">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="2" y="2" width="20" height="20" rx="2"/>
                      <path d="M12 2v20M2 12h20"/>
                    </svg>
                  </div>
                  <span class="anime-title">{{ anime.title_ru || anime.title_en }}</span>
                  <button type="button" @click="removeAnime(index)" class="btn-remove">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="18" y1="6" x2="6" y2="18"/>
                      <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div v-if="selectedAnime.length === 0 && !isSearching && searchResults.length === 0" class="hint">
              Р”РѕР±Р°РІСЊС‚Рµ С…РѕС‚СЏ Р±С‹ РѕРґРЅРѕ Р°РЅРёРјРµ РґР»СЏ СЃРѕР·РґР°РЅРёСЏ РїР»РµР№Р»РёСЃС‚Р°
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="handleClose" class="btn btn-secondary" type="button">
            РћС‚РјРµРЅР°
          </button>
          <button
            @click="handleCreate"
            :disabled="!canCreate || isCreating"
            class="btn btn-primary"
            type="button"
          >
            <svg v-if="!isCreating" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            {{ isCreating ? 'РЎРѕР·РґР°РЅРёРµ...' : 'РЎРѕР·РґР°С‚СЊ' }}
          </button>
        </div>
      </div>
    </div>
  </Transition>`n  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Anime } from '@/types'
import { getMediaUrl } from '@/api/client'
import api from '@/api';

interface Props {
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  create: [data: PlaylistCreateData]
}>()

interface PlaylistCreateData {
  title: string
  description?: string
  privacy: 'public' | 'private' | 'link'
  animeIds: number[]
}

const formData = ref({
  title: '',
  description: '',
  privacy: 'public' as 'public' | 'private' | 'link'
})

const searchQuery = ref('')
const searchResults = ref<Anime[]>([])
const selectedAnime = ref<Anime[]>([])
const isSearching = ref(false)
const isCreating = ref(false)
const searchTimeout = ref<number | null>(null)

const privacyOptions = [
  { value: 'public', label: 'РџСѓР±Р»РёС‡РЅС‹Р№', icon: 'рџЊЌ' },
  { value: 'private', label: 'РџСЂРёРІР°С‚РЅС‹Р№', icon: 'рџ”’' },
  { value: 'link', label: 'РџРѕ СЃСЃС‹Р»РєРµ', icon: 'рџ”—' }
]

const canCreate = computed(() => {
  return formData.value.title.trim().length > 0 && selectedAnime.value.length >= 1
})

const handleSearch = () => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }

  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }

  isSearching.value = true

  searchTimeout.value = window.setTimeout(async () => {
    try {
      // Нормализуем запрос для бэкенда
      const normalizedQuery = searchQuery.value
        .toLowerCase()
        .replace(/[-_:/\\|,.!?@#$%^&*(){}\[\]<>~`'"\\s]+/g, ' ')
        .trim()
      
      // Используем тот же endpoint что и каталог - для консистентности результатов
      const response = await api.get('/anime/', { 
        params: { 
          search: normalizedQuery, 
          page_size: 100 
        } 
      })
      searchResults.value = response.data.results || response.data
    } catch (err) {
      console.error('Ошибка поиска аниме:', err)
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }, 500)
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
}

const addAnime = (anime: Anime) => {
  if (!selectedAnime.value.find(a => a.id === anime.id)) {
    selectedAnime.value.push(anime)
  }
  searchQuery.value = ''
  searchResults.value = []
}

const removeAnime = (index: number) => {
  selectedAnime.value.splice(index, 1)
}

const handleCreate = () => {
  if (!canCreate.value) return

  const data: PlaylistCreateData = {
    title: formData.value.title.trim(),
    description: formData.value.description.trim() || undefined,
    privacy: formData.value.privacy,
    animeIds: selectedAnime.value.map(a => a.id)
  }

  emit('create', data)
  resetForm()
}

const handleClose = () => {
  emit('close')
}

const resetForm = () => {
  formData.value = {
    title: '',
    description: '',
    privacy: 'public'
  }
  searchQuery.value = ''
  searchResults.value = []
  selectedAnime.value = []
  isCreating.value = false
}

watch(() => props.show, (newShow) => {
  if (!newShow) {
    resetForm()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--color-background-surface);
  border-radius: 1rem;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-modal);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.modal-close:hover {
  background-color: var(--color-background-active);
  color: var(--color-accent-pink);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.form-label.required::after {
  content: ' *';
  color: var(--color-accent-pink);
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
  font-family: inherit;
}

.form-input:focus,
.form-textarea:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.privacy-options {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.privacy-option {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.625rem 1rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  user-select: none;
}

.privacy-option:hover {
  border-color: var(--color-accent);
}

.privacy-option.active {
  background-color: rgba(58, 134, 255, 0.1);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.privacy-radio {
  display: none;
}

.privacy-icon {
  font-size: 1rem;
}

.privacy-label {
  font-size: 0.875rem;
  font-weight: 600;
}

.anime-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.search-wrapper {
  position: relative;
}

.search-input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.search-input {
  width: 100%;
  padding: 0.75rem 2.5rem;
  padding-right: 2.5rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  color: var(--color-text);
  background-color: var(--color-background-surface);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
}

.search-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.search-clear {
  position: absolute;
  right: 0.75rem;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.search-clear:hover {
  background-color: var(--color-background-active);
  color: var(--color-text);
}

.search-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1.5rem;
  color: var(--color-text-tertiary);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.search-results {
  max-height: 250px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  padding: 0.5rem;
}

.anime-result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem;
  background-color: var(--color-background-active);
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.anime-result:hover {
  background-color: var(--color-accent);
  color: var(--color-text);
}

.anime-poster {
  width: 40px;
  height: 56px;
  object-fit: cover;
  border-radius: 0.25rem;
  flex-shrink: 0;
}

.anime-poster-placeholder {
  width: 40px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-surface);
  border-radius: 0.25rem;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.anime-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.anime-title {
  font-weight: 600;
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.anime-meta {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.btn-add {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-accent);
  color: var(--color-text);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  flex-shrink: 0;
}

.btn-add:hover {
  background-color: var(--color-accent-hover);
  transform: scale(1.05);
}

.selected-anime {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.selected-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  background-color: rgba(58, 134, 255, 0.1);
  border-radius: 0.375rem;
}

.selected-count {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-accent);
}

.anime-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 250px;
  overflow-y: auto;
}

.selected-anime-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem;
  background-color: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.375rem;
}

.selected-anime-item .anime-poster {
  width: 32px;
  height: 45px;
}

.selected-anime-item .anime-poster-placeholder {
  width: 32px;
  height: 45px;
}

.selected-anime-item .anime-title {
  flex: 1;
  font-size: 0.8125rem;
}

.btn-remove {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--color-text-tertiary);
  transition: all 0.2s var(--transition-smooth);
  flex-shrink: 0;
}

.btn-remove:hover {
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.hint {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
  text-align: center;
  padding: 1rem;
  background-color: var(--color-background-active);
  border-radius: 0.5rem;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--color-divider);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid;
}

.btn-primary {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-text);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: transparent;
  border-color: var(--color-divider-light);
  color: var(--color-text-secondary);
}

.btn-secondary:hover {
  background-color: var(--color-background-active);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.spin {
  animation: spin 1s linear infinite;
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s var(--transition-smooth);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.95) translateY(20px);
}

@media (max-width: 768px) {
  .modal-content {
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .privacy-options {
    flex-direction: column;
  }

  .privacy-option {
    width: 100%;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }
}
</style>

