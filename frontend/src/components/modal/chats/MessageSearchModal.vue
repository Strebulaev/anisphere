<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="close">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Поиск по сообщениям</h3>
          <button class="close-btn" @click="close">×</button>
        </div>

        <div class="modal-body">
          <div class="search-form">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Введите текст для поиска..."
              class="search-input"
              @keyup.enter="performSearch"
            />
            <button
              class="search-btn"
              @click="performSearch"
              :disabled="!searchQuery.trim() || searching"
            >
              {{ searching ? 'Поиск...' : 'Найти' }}
            </button>
          </div>

          <div class="filters">
            <div class="filter-group">
              <label class="filter-label">Тип медиа</label>
              <select v-model="filters.mediaType" class="filter-select">
                <option value="">Все</option>
                <option value="text">Текст</option>
                <option value="image">Изображения</option>
                <option value="video">Видео</option>
                <option value="audio">Аудио</option>
                <option value="file">Файлы</option>
              </select>
            </div>
            <div class="filter-group">
              <label class="filter-label">С</label>
              <input v-model="filters.dateFrom" type="date" class="filter-input" />
            </div>
            <div class="filter-group">
              <label class="filter-label">По</label>
              <input v-model="filters.dateTo" type="date" class="filter-input" />
            </div>
          </div>

          <div v-if="searchResults.length > 0" class="search-results">
            <div class="results-header">Найдено: {{ searchResults.length }} сообщений</div>
            <div class="results-list">
              <div v-for="message in searchResults" :key="message.id" class="result-item" @click="goToMessage(message)">
                <div class="result-header">
                  <span class="result-sender">{{ message.sender_username }}</span>
                  <span class="result-date">{{ formatDate(message.created_at) }}</span>
                </div>
                <div class="result-text">{{ message.text || 'Медиа-сообщение' }}</div>
                <div v-if="message.media_type" class="result-media-type">
                  {{ getMediaTypeLabel(message.media_type) }}
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="searched && !searching" class="no-results">Ничего не найдено</div>
          <div v-else-if="!searched" class="search-hint">Введите текст для поиска и нажмите "Найти"</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useChatExtrasStore } from '@/stores/chatExtras'
import { useRouter } from 'vue-router'

interface Props {
  isOpen: boolean
  chatId?: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'message-selected', messageId: number): void
}>()

const chatExtrasStore = useChatExtrasStore()
const router = useRouter()

const searchQuery = ref('')
const searching = ref(false)
const searched = ref(false)
const searchResults = ref<any[]>([])

const filters = reactive({
  mediaType: '',
  dateFrom: '',
  dateTo: ''
})

const performSearch = async () => {
  if (!searchQuery.value.trim()) return
  searching.value = true
  searched.value = false
  try {
    const result = await chatExtrasStore.searchMessages(searchQuery.value, {
      chat_id: props.chatId,
      media_type: filters.mediaType || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined
    })
    searchResults.value = result.results
    searched.value = true
  } catch (error) {
    console.error('Error searching messages:', error)
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

const goToMessage = (message: any) => {
  emit('message-selected', message.id)
  close()
  if (message.chat_id) {
    router.push(`/chat/${message.chat_id}`)
  } else if (message.private_chat_id) {
    router.push(`/chat/${message.private_chat_id}`)
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Только что'
  if (diffMins < 60) return `${diffMins} мин. назад`
  if (diffHours < 24) return `${diffHours} ч. назад`
  if (diffDays < 7) return `${diffDays} дн. назад`

  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  })
}

const getMediaTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    text: 'Текст',
    image: 'Изображение',
    video: 'Видео',
    audio: 'Аудио',
    file: 'Файл',
    location: 'Местоположение',
    post: 'Пост',
    anime: 'Аниме'
  }
  return labels[type] || type
}

const close = () => {
  emit('close')
  searchQuery.value = ''
  searchResults.value = []
  searched.value = false
  filters.mediaType = ''
  filters.dateFrom = ''
  filters.dateTo = ''
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(5,4,8,0.88);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-modal);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  transition: all 0.2s var(--ease-petal);
}

.close-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
}

.search-form {
  display: flex;
  gap: 0.5rem;
}

.search-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  font-size: 1rem;
  background: var(--surface-4);
  color: var(--text-primary);
  transition: all 0.2s var(--ease-petal);
}

.search-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.search-btn {
  padding: 0.75rem 1.5rem;
  background: var(--accent);
  border: none;
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-on-accent);
  cursor: pointer;
  transition: all 0.2s var(--ease-petal);
  white-space: nowrap;
}

.search-btn:hover {
  box-shadow: var(--shadow-glow-sm);
}

.search-btn:disabled {
  background: var(--surface-5);
  color: var(--text-tertiary);
  cursor: not-allowed;
}

.filters {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.filter-select,
.filter-input {
  padding: 0.5rem;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  background: var(--surface-4);
  color: var(--text-primary);
  transition: all 0.2s var(--ease-petal);
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: var(--accent);
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.results-header {
  font-size: 0.875rem;
  color: var(--text-secondary);
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-subtle);
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.result-item {
  padding: 0.75rem;
  background: var(--surface-3);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s var(--ease-petal);
  border: 1px solid var(--border-subtle);
}

.result-item:hover {
  background: var(--surface-4);
  border-color: var(--accent);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.result-sender {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.result-date {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.result-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-media-type {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--accent);
}

.no-results,
.search-hint {
  text-align: center;
  padding: 2rem;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}
</style>
