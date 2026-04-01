<template>
  <div class="reactor-view">
    <div class="container">
      <!-- Tab Navigation -->
      <div class="tabs-container">
        <nav class="tabs-nav">
          <button
            @click="switchTab('feed')"
            :class="['tab-btn', activeTab === 'feed' ? 'active' : '']"
          >
            🎬 Reactor
          </button>
          <button
            @click="switchTab('competitions')"
            :class="['tab-btn', activeTab === 'competitions' ? 'active' : '']"
          >
            🏆 Конкурсы
          </button>
        </nav>
      </div>

      <!-- Reactor Feed Tab -->
      <div v-if="activeTab === 'feed'" class="tab-content">
        <!-- Create Video Button -->
        <div class="actions-bar">
          <button @click="router.push('/reactor/create')" class="btn-primary">
            🎬 Создать видео
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Загрузка...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="videos.length === 0" class="empty-state">
          <div class="empty-icon">🎬</div>
          <h2 class="empty-title">Reactor лента</h2>
          <p class="empty-text">Пока нет видео. Будьте первым!</p>
        </div>

        <!-- Videos Grid -->
        <div v-else class="videos-grid">
          <div
            v-for="video in videos"
            :key="video.id"
            class="video-card"
            @click="playVideo(video)"
          >
            <!-- Video Thumbnail -->
            <div class="video-thumbnail">
              <video
                v-if="video.video_file"
                :src="video.video_file"
                class="thumbnail-video"
                muted
                preload="metadata"
              ></video>
              <div v-else class="thumbnail-placeholder">
                <span class="placeholder-icon">🎬</span>
              </div>

              <!-- Play Button Overlay -->
              <div class="play-overlay">
                <div class="play-button">
                  <span class="play-icon">▶️</span>
                </div>
              </div>

              <!-- Duration -->
              <div class="duration-badge">
                {{ formatDuration(video.duration || 30) }}
              </div>
            </div>

            <!-- Video Info -->
            <div class="video-info">
              <h4 class="video-title">{{ video.title || 'Без названия' }}</h4>

              <!-- Anime Tag -->
              <div v-if="video.anime" class="anime-tag">
                <img :src="video.anime.poster_url" :alt="video.anime.title_ru" class="anime-poster">
                <span class="anime-title">{{ video.anime.title_ru }}</span>
              </div>

              <!-- Author -->
              <div class="video-meta">
                <span class="author">{{ video.user_username }}</span>
                <div class="stats">
                  <span class="stat">❤️ {{ video.likes_count || 0 }}</span>
                  <span class="stat">💬 {{ video.comments_count || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Competitions Tab -->
      <div v-if="activeTab === 'competitions'" class="tab-content">
        <!-- Create Competition Button -->
        <div class="actions-bar">
          <button @click="router.push('/competitions/create')" class="btn-primary">
            🏆 Создать конкурс
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>Загрузка...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="activeContests.length === 0 && finishedContests.length === 0" class="empty-state">
          <div class="empty-icon">🏆</div>
          <h2 class="empty-title">Конкурсы</h2>
          <p class="empty-text">Пока нет конкурсов. Будьте первым!</p>
        </div>

        <!-- Active Competitions -->
        <section v-if="activeContests.length > 0" class="competitions-section">
          <h3 class="section-title">Активные конкурсы</h3>
          <div class="competitions-grid">
            <div
              v-for="contest in activeContests"
              :key="contest.id"
              class="contest-card active"
            >
              <div class="contest-header">
                <span :class="['contest-type', getContestTypeClass(contest.type)]">
                  {{ getContestTypeLabel(contest.type) }}
                </span>
                <span class="contest-deadline">
                  до {{ formatDate(contest.ended_at || contest.voting_started_at) }}
                </span>
              </div>

              <h4 class="contest-title">{{ contest.title }}</h4>
              <p class="contest-description">{{ contest.description }}</p>

              <div v-if="contest.theme" class="contest-theme">
                <strong>Тема:</strong> {{ contest.theme }}
              </div>

              <div v-if="contest.prize_1st || contest.prize_2nd || contest.prize_3rd" class="contest-prizes">
                <p class="prizes-title">🎁 Призы:</p>
                <ul class="prizes-list">
                  <li v-if="contest.prize_1st">1 место: {{ contest.prize_1st }}</li>
                  <li v-if="contest.prize_2nd">2 место: {{ contest.prize_2nd }}</li>
                  <li v-if="contest.prize_3rd">3 место: {{ contest.prize_3rd }}</li>
                </ul>
              </div>

              <div class="contest-stats">
                <span class="contest-stat">👥 {{ contest.entries_count }} участников</span>
                <span class="contest-stat">🗳️ {{ contest.votes_count }} голосов</span>
              </div>

              <button
                @click="participateInContest(contest)"
                class="contest-btn participate"
              >
                Участвовать
              </button>
            </div>
          </div>
        </section>

        <!-- Finished Competitions -->
        <section v-if="finishedContests.length > 0" class="competitions-section">
          <h3 class="section-title">Завершённые конкурсы</h3>
          <div class="competitions-grid">
            <div
              v-for="contest in finishedContests"
              :key="contest.id"
              class="contest-card finished"
            >
              <div class="contest-header">
                <span class="contest-type finished">Завершён</span>
                <span class="contest-deadline">
                  {{ formatDate(contest.ended_at) }}
                </span>
              </div>

              <h4 class="contest-title">{{ contest.title }}</h4>
              <p class="contest-description">{{ contest.description }}</p>

              <div v-if="contest.theme" class="contest-theme">
                <strong>Тема:</strong> {{ contest.theme }}
              </div>

              <button
                @click="viewContestResults(contest)"
                class="contest-btn view"
              >
                Посмотреть результаты
              </button>
            </div>
          </div>
        </section>

        <!-- My Participations -->
        <section v-if="myEntries.length > 0" class="my-entries-section">
          <h3 class="section-title">Мои участия</h3>
          <div class="entries-list">
            <div
              v-for="entry in myEntries"
              :key="entry.id"
              class="entry-item"
            >
              <div class="entry-info">
                <h4 class="entry-title">{{ entry.contest_title }}</h4>
                <p class="entry-status">
                  Статус: {{ getEntryStatus(entry) }}
                </p>
                <p v-if="entry.is_winner" class="entry-winner">
                  🏆 {{ entry.winner_place }} место!
                </p>
              </div>
              <span :class="['entry-badge', getEntryStatusClass(entry)]">
                {{ getEntryStatusText(entry) }}
              </span>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Participation Modal -->
    <div
      v-if="showParticipationModal"
      class="modal-overlay"
      @click="closeParticipationModal"
    >
      <div class="modal-content" @click.stop>
        <h3 class="modal-title">Участие в конкурсе</h3>
        <p class="modal-subtitle">{{ selectedContest?.title }}</p>

        <form @submit.prevent="submitEntry">
          <div class="form-group">
            <label class="form-label">Название работы</label>
            <input
              v-model="entryForm.title"
              type="text"
              class="form-input"
              placeholder="Название вашей работы"
            />
          </div>

          <div class="form-group">
            <label class="form-label">Описание</label>
            <textarea
              v-model="entryForm.description"
              rows="3"
              class="form-input"
              placeholder="Опишите вашу работу"
            ></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">
              {{ selectedContest?.format === 'image' ? 'Изображение' : selectedContest?.format === 'video' ? 'Видео' : 'Файл' }}
            </label>
            <input
              type="file"
              @change="handleFileUpload"
              :accept="getAcceptTypes(selectedContest?.format)"
              class="form-input"
            />
          </div>

          <div class="modal-actions">
            <button
              type="button"
              @click="closeParticipationModal"
              class="btn-secondary"
            >
              Отмена
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="btn-primary"
            >
              {{ submitting ? 'Отправка...' : 'Отправить' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api/client'

// Types
interface Contest {
  id: number
  title: string
  description: string
  type: 'weekly' | 'monthly' | 'seasonal' | 'special'
  format: 'image' | 'video' | 'text' | 'mixed'
  status: string
  theme?: string
  prize_1st?: string
  prize_2nd?: string
  prize_3rd?: string
  ended_at?: string
  voting_started_at?: string
  entries_count: number
  votes_count: number
}

interface ContestEntry {
  id: number
  contest_title: string
  title?: string
  description?: string
  is_winner: boolean
  winner_place?: number
}

interface ReactorVideo {
  id: number
  title?: string
  description?: string
  video_file: string
  user_username: string
  likes_count: number
  comments_count: number
  duration?: number
  anime?: {
    id: number
    title_ru: string
    poster_url: string
  }
}

const router = useRouter()

// Reactive data
const activeTab = ref('feed')
const loading = ref(false)
const error = ref('')

// Feed data
const videos = ref<ReactorVideo[]>([])

// Competitions data
const activeContests = ref<Contest[]>([])
const finishedContests = ref<Contest[]>([])
const myEntries = ref<ContestEntry[]>([])

// Participation modal
const showParticipationModal = ref(false)
const selectedContest = ref<Contest | null>(null)
const submitting = ref(false)

const entryForm = ref({
  title: '',
  description: ''
})

const selectedFile = ref<File | null>(null)

// Methods
const loadVideos = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.get('/reactor/posts/')
    videos.value = response.data.results || response.data
  } catch (err: any) {
    error.value = 'Не удалось загрузить видео: ' + (err.response?.data?.detail || err.message)
  } finally {
    loading.value = false
  }
}

const loadContests = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await apiClient.get('/social/contests/')
    const allContests = response.data

    // Separate active and finished contests
    activeContests.value = allContests.filter((contest: Contest) =>
      contest.status === 'active' || contest.status === 'voting'
    )

    finishedContests.value = allContests.filter((contest: Contest) =>
      contest.status === 'finished' || contest.status === 'cancelled'
    )

    // Load user's entries
    await loadMyEntries()
  } catch (err: any) {
    error.value = 'Не удалось загрузить конкурсы: ' + (err.response?.data?.detail || err.message)
  } finally {
    loading.value = false
  }
}

const loadMyEntries = async () => {
  try {
    const response = await apiClient.get('/social/contest-entries/')
    myEntries.value = response.data
  } catch (err) {
    console.error('Error loading my entries:', err)
  }
}

const switchTab = (tab: string) => {
  activeTab.value = tab
  if (tab === 'feed') {
    loadVideos()
  } else if (tab === 'competitions') {
    loadContests()
  }
}

const playVideo = (video: ReactorVideo) => {
  alert(`Воспроизведение видео: ${video.title || 'Без названия'}`)
}

const formatDuration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const getContestTypeClass = (type: string) => {
  const classes = {
    weekly: 'type-weekly',
    monthly: 'type-monthly',
    seasonal: 'type-seasonal',
    special: 'type-special'
  }
  return classes[type as keyof typeof classes] || 'type-default'
}

const getContestTypeLabel = (type: string) => {
  const labels = {
    weekly: 'Еженедельный',
    monthly: 'Ежемесячный',
    seasonal: 'Сезонный',
    special: 'Специальный'
  }
  return labels[type as keyof typeof labels] || type
}

const formatDate = (dateString?: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU')
}

const participateInContest = (contest: Contest) => {
  selectedContest.value = contest
  showParticipationModal.value = true

  // Reset form
  entryForm.value = {
    title: '',
    description: ''
  }
  selectedFile.value = null
}

const closeParticipationModal = () => {
  showParticipationModal.value = false
  selectedContest.value = null
}

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    selectedFile.value = file
  }
}

const getAcceptTypes = (format?: string) => {
  switch (format) {
    case 'image':
      return 'image/*'
    case 'video':
      return 'video/*'
    default:
      return '*/*'
  }
}

const submitEntry = async () => {
  if (!selectedContest.value) return

  submitting.value = true

  try {
    const formData = new FormData()
    formData.append('contest', selectedContest.value.id.toString())
    formData.append('title', entryForm.value.title)
    formData.append('description', entryForm.value.description)

    if (selectedFile.value) {
      if (selectedContest.value.format === 'image') {
        formData.append('image_file', selectedFile.value)
      } else if (selectedContest.value.format === 'video') {
        formData.append('video_file', selectedFile.value)
      }
    }

    await apiClient.post('/social/contest-entries/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // Reload data
    await loadContests()
    closeParticipationModal()

    alert('Ваша работа успешно отправлена!')

  } catch (err: any) {
    alert('Ошибка при отправке работы: ' + (err.response?.data?.detail || err.message))
  } finally {
    submitting.value = false
  }
}

const viewContestResults = (contest: Contest) => {
  alert(`Просмотр результатов конкурса "${contest.title}" будет реализован позже`)
}

const getEntryStatus = (entry: ContestEntry) => {
  if (entry.is_winner) {
    return `Завершено • ${entry.winner_place} место`
  }
  return 'Ожидание результатов'
}

const getEntryStatusText = (entry: ContestEntry) => {
  if (entry.is_winner) {
    return '🏆 Победа'
  }
  return 'Участвую'
}

const getEntryStatusClass = (entry: ContestEntry) => {
  if (entry.is_winner) {
    return 'status-winner'
  }
  return 'status-participating'
}

// Lifecycle
onMounted(() => {
  loadVideos()
})
</script>

<style scoped>
.reactor-view {
  min-height: 100vh;
  background: var(--color-background);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 1rem;
}

/* Tabs */
.tabs-container {
  margin-bottom: 2rem;
}

.tabs-nav {
  display: flex;
  gap: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

.tab-btn {
  padding: 0.75rem 1.25rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
}

/* Tab Content */
.tab-content {
  min-height: 400px;
}

/* Actions Bar */
.actions-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: var(--color-accent-hover);
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: var(--color-text-secondary);
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
}

.empty-text {
  color: var(--color-text-secondary);
  margin: 0;
}

/* Videos Grid */
.videos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.video-card {
  background: var(--color-background-surface);
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.video-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.video-thumbnail {
  position: relative;
  aspect-ratio: 16/9;
}

.thumbnail-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-active);
}

.placeholder-icon {
  font-size: 3rem;
}

.play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  opacity: 0;
  transition: opacity 0.2s;
}

.video-card:hover .play-overlay {
  opacity: 1;
}

.play-button {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.play-icon {
  font-size: 1.5rem;
}

.duration-badge {
  position: absolute;
  bottom: 0.5rem;
  right: 0.5rem;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.video-info {
  padding: 1rem;
}

.video-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.75rem 0;
  line-height: 1.4;
}

.anime-tag {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.anime-poster {
  width: 1.5rem;
  height: 2rem;
  object-fit: cover;
  border-radius: 0.25rem;
}

.anime-title {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.video-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.stats {
  display: flex;
  gap: 0.75rem;
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

/* Competitions */
.competitions-section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 1rem 0;
}

.competitions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.contest-card {
  background: var(--color-background-surface);
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.contest-card.active {
  border: 1px solid var(--color-accent);
}

.contest-card.finished {
  background: var(--color-background-active);
}

.contest-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.contest-type {
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: 500;
}

.contest-type.type-weekly {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.contest-type.type-monthly {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.contest-type.type-seasonal {
  background: rgba(139, 92, 246, 0.2);
  color: #8b5cf6;
}

.contest-type.type-special {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.contest-type.finished {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
}

.contest-deadline {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.contest-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
}

.contest-description {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin: 0 0 0.75rem 0;
  line-height: 1.5;
}

.contest-theme {
  font-size: 0.85rem;
  color: var(--color-text-primary);
  margin-bottom: 0.75rem;
}

.contest-prizes {
  margin-bottom: 1rem;
}

.prizes-title {
  font-size: 0.85rem;
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
}

.prizes-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.prizes-list li {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  padding-left: 1rem;
  margin-bottom: 0.25rem;
}

.contest-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.contest-stat {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.contest-btn {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.contest-btn.participate {
  background: var(--color-accent);
  color: white;
}

.contest-btn.participate:hover {
  background: var(--color-accent-hover);
}

.contest-btn.view {
  background: var(--color-border);
  color: var(--color-text-primary);
}

.contest-btn.view:hover {
  background: var(--color-border-light);
}

/* My Entries */
.my-entries-section {
  margin-top: 2rem;
}

.entries-list {
  background: var(--color-background-surface);
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.entry-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border: 1px solid var(--color-divider);
  border-radius: 0.5rem;
  margin-bottom: 0.75rem;
}

.entry-item:last-child {
  margin-bottom: 0;
}

.entry-info h4 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.25rem 0;
}

.entry-status {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  margin: 0;
}

.entry-winner {
  font-size: 0.85rem;
  color: #10b981;
  font-weight: 500;
  margin: 0;
}

.entry-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.85rem;
  font-weight: 500;
}

.entry-badge.status-winner {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.entry-badge.status-participating {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: var(--color-background-surface);
  border-radius: 1rem;
  padding: 2rem;
  width: 100%;
  max-width: 500px;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
}

.modal-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0 0 1.5rem 0;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 0.5rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  background: var(--color-background);
  color: var(--color-text-primary);
  font-size: 0.95rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn-secondary {
  flex: 1;
  padding: 0.75rem;
  background: var(--color-border);
  color: var(--color-text-primary);
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-secondary:hover {
  background: var(--color-border-light);
}

/* Responsive */
@media (max-width: 768px) {
  .videos-grid,
  .competitions-grid {
    grid-template-columns: 1fr;
  }

  .tabs-nav {
    gap: 0.25rem;
  }

  .tab-btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
  }
}

/* ═══ АДАПТИВНЫЕ СТИЛИ REACTOR ═══ */

/* xs: 320px */
@media (max-width: 374px) {
  .reactor-view {
    padding: 0.5rem;
  }
  
  .reactor-header {
    padding: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  .reactor-title {
    font-size: 1.25rem;
  }
  
  .reactor-tabs {
    gap: 0.25rem;
    padding: 0.25rem;
    overflow-x: auto;
  }
  
  .reactor-tab {
    padding: 0.375rem 0.5rem;
    font-size: 0.75rem;
    white-space: nowrap;
  }
  
  .reactor-filters {
    gap: 0.25rem;
    padding: 0.25rem;
    overflow-x: auto;
  }
  
  .reactor-filter {
    padding: 0.25rem 0.5rem;
    font-size: 0.625rem;
  }
  
  .reactor-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .reactor-video {
    aspect-ratio: 3/4;
    border-radius: 0.5rem;
  }
  
  .reactor-video-info {
    padding: 0.5rem;
  }
  
  .reactor-video-title {
    font-size: 0.875rem;
  }
  
  .reactor-video-stats {
    font-size: 0.75rem;
    gap: 0.5rem;
  }
  
  .reactor-video-author {
    font-size: 0.75rem;
  }
  
  .reactor-upload-btn {
    width: 3rem;
    height: 3rem;
    bottom: 1rem;
    right: 1rem;
  }
  
  .reactor-upload-icon {
    width: 1.5rem;
    height: 1.5rem;
  }
  
  .reactor-modal {
    padding: 0.5rem;
  }
  
  .reactor-modal-content {
    max-width: 100%;
    border-radius: 0.5rem;
  }
  
  .reactor-modal-header {
    padding: 0.75rem;
  }
  
  .reactor-modal-title {
    font-size: 1rem;
  }
  
  .reactor-modal-body {
    padding: 0.75rem;
  }
  
  .reactor-modal-footer {
    padding: 0.75rem;
    gap: 0.5rem;
    flex-direction: column;
  }
  
  .reactor-select {
    padding: 0.5rem;
    font-size: 0.875rem;
  }
  
  .reactor-upload-area {
    padding: 1rem;
    min-height: 150px;
  }
  
  .reactor-upload-text {
    font-size: 0.875rem;
  }
  
  .reactor-submit-btn {
    width: 100%;
    padding: 0.5rem;
    font-size: 0.875rem;
  }
}

/* sm: 375px */
@media (min-width: 375px) and (max-width: 767px) {
  .reactor-view {
    padding: 0.75rem;
  }
  
  .reactor-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
  
  .reactor-video {
    aspect-ratio: 9/16;
  }
  
  .reactor-modal-footer {
    flex-direction: row;
  }
  
  .reactor-submit-btn {
    width: auto;
  }
}

/* md: 768px+ */
@media (min-width: 768px) {
  .reactor-view {
    padding: 1rem;
  }
  
  .reactor-header {
    padding: 1rem;
    margin-bottom: 1rem;
  }
  
  .reactor-title {
    font-size: 1.5rem;
  }
  
  .reactor-tabs {
    gap: 0.5rem;
    padding: 0.5rem 1rem;
  }
  
  .reactor-tab {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }
  
  .reactor-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .reactor-video {
    aspect-ratio: 9/16;
  }
  
  .reactor-upload-btn {
    width: 4rem;
    height: 4rem;
    bottom: 1.5rem;
    right: 1.5rem;
  }
  
  .reactor-modal {
    padding: 1.5rem;
  }
  
  .reactor-modal-content {
    max-width: 36rem;
  }
  
  .reactor-modal-header {
    padding: 1rem;
  }
  
  .reactor-modal-body {
    padding: 1.5rem;
  }
  
  .reactor-modal-footer {
    padding: 1rem;
    gap: 0.75rem;
  }
}

/* tablet-lg: 1024px+ */
@media (min-width: 1024px) {
  .reactor-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .reactor-video {
    aspect-ratio: 3/4;
  }
}

/* laptop: 1280px+ */
@media (min-width: 1280px) {
  .reactor-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .reactor-modal-content {
    max-width: 42rem;
  }
}

/* desktop: 1536px+ */
@media (min-width: 1536px) {
  .reactor-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}
</style>