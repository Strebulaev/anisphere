<template>
  <div v-show="show" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ isEditing ? 'Изменить озвучку' : 'Добавить озвучку' }}</h3>
        <button class="close-btn" @click="closeModal">&times;</button>
      </div>

      <form @submit.prevent="submitForm" class="dub-form">
        <div class="form-group">
          <label for="groupName">Группа озвучки *</label>
          <input
            id="groupName"
            v-model="form.group_name"
            type="text"
            placeholder="Например: Cube-in-Cube"
            required
          />
          <small class="form-help">Введите название группы озвучки. Если группа не существует, она будет создана автоматически.</small>
        </div>

        <div class="form-group">
          <div class="links-header">
            <label>Ссылки на группу</label>
            <button
              type="button"
              class="add-link-btn"
              @click="addLink"
              title="Добавить ссылку"
            >
              +
            </button>
          </div>
          <div v-if="form.group_links.length === 0" class="no-links">
            <small class="form-help">Добавьте ссылки на сайт группы, социальные сети и т.д.</small>
          </div>
          <div v-else class="links-list">
            <div
              v-for="(link, index) in form.group_links"
              :key="index"
              class="link-item"
            >
              <input
                v-model="form.group_links[index]"
                type="url"
                placeholder="https://example.com"
                class="link-url"
              />
              <button
                type="button"
                class="remove-link-btn"
                @click="removeLink(index)"
                title="Удалить ссылку"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label for="dubType">Тип озвучки</label>
          <select id="dubType" v-model="form.dub_type">
            <option value="full">Полная озвучка</option>
            <option value="subtitles">Субтитры</option>
            <option value="partial">Частичная озвучка</option>
            <option value="voiceover">Закадровый перевод</option>
          </select>
        </div>

        <div class="form-group">
          <label for="externalUrl">Ссылка на озвучку</label>
          <input
            id="externalUrl"
            v-model="form.external_url"
            type="url"
            placeholder="https://example.com/dub"
          />
          <small class="form-help">Ссылка на сайт с озвучкой (опционально)</small>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="episodesDone">Эпизодов готово</label>
            <input
              id="episodesDone"
              v-model.number="form.episodes_done"
              type="number"
              min="0"
              placeholder="0"
            />
          </div>

          <div class="form-group">
            <label for="totalEpisodes">Всего эпизодов</label>
            <input
              id="totalEpisodes"
              v-model.number="form.total_episodes"
              type="number"
              min="0"
              placeholder="12"
            />
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" @click="closeModal">
            Отмена
          </button>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading" class="spinner-small"></span>
            {{ loading ? (isEditing ? 'Изменение...' : 'Добавление...') : (isEditing ? 'Изменить озвучку' : 'Добавить озвучку') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'

interface Props {
  show: boolean
  animeId: number
  editingDub?: {
    id: number
    group: {
      id: number
      name: string
      slug: string
      logo_url: string | null
    } | null
    dub_type: string
    external_url: string | null
    episodes_done: number
    total_episodes: number | null
  } | null
}

interface Emits {
  (e: 'close'): void
  (e: 'dub-added'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

import apiClient from '@/api/client'

const loading = ref(false)
const error = ref<string | null>(null)

const form = reactive({
  group_name: '',
  group_links: [] as Array<string>,
  dub_type: 'full',
  external_url: '',
  episodes_done: 0,
  total_episodes: null as number | null
})

const isEditing = computed(() => !!props.editingDub)

const resetForm = () => {
  form.group_name = ''
  form.group_links = []
  form.dub_type = 'full'
  form.external_url = ''
  form.episodes_done = 0
  form.total_episodes = null
  error.value = null
}

// Следим за изменениями editingDub для инициализации формы
watch(() => props.editingDub, (newDub) => {
  if (newDub) {
    // Заполняем форму данными для редактирования
    form.group_name = newDub.group?.name || ''
    form.dub_type = newDub.dub_type
    form.external_url = newDub.external_url || ''
    form.episodes_done = newDub.episodes_done
    form.total_episodes = newDub.total_episodes
    form.group_links = [] // Для редактирования группы нужно загрузить ссылки отдельно
  } else {
    resetForm()
  }
}, { immediate: true })

const closeModal = () => {
  emit('close')
  resetForm()
}

const addLink = () => {
  form.group_links.push('')
}

const removeLink = (index: number) => {
  form.group_links.splice(index, 1)
}

const submitForm = async () => {
  if (!form.group_name.trim()) {
    error.value = 'Название группы обязательно'
    return
  }

  loading.value = true
  error.value = null

  try {
    const payload = {
      group_name: form.group_name,
      group_links: form.group_links,
      dub_type: form.dub_type,
      external_url: form.external_url || '',
      episodes_done: form.episodes_done || 0,
      total_episodes: form.total_episodes || null
    }

    await apiClient.post(`/dubs/anime/${props.animeId}/dubs/`, payload)

    emit('dub-added')
    closeModal()
  } catch (err: any) {
    error.value = err.response?.data?.error || err.response?.data?.group_name?.[0] || 'Ошибка при добавлении озвучки'
    console.error('Ошибка добавления озвучки:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #374151;
}

.dub-form {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-help {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.links-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.add-link-btn {
  background: #10b981;
  color: white;
  aspect-ratio: 1;
  border-radius: 50%;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.2s;
}

.add-link-btn:hover {
  background: #059669;
}

.no-links {
  color: #6b7280;
  font-style: italic;
  padding: 1rem;
  text-align: center;
  border: 1px dashed #d1d5db;
  border-radius: 0.5rem;
}

.links-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.link-item {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.link-url {
  flex: 1;
}

.remove-link-btn {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  transition: background 0.2s;
  flex-shrink: 0;
}

.remove-link-btn:hover {
  background: #dc2626;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-size: 0.875rem;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-outline {
  background: transparent;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.btn-outline:hover {
  background: #222222;
  color: #374151;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  display: inline-block;
  margin-right: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>