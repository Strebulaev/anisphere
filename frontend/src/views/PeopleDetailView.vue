<template>
  <div class="people-detail-page">
    <!-- Навигация -->
    <div class="breadcrumb">
      <router-link to="/people" class="breadcrumb-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        К людям
      </router-link>
    </div>

    <!-- Загрузка -->
    <div v-if="isLoading" class="loading-state">
      <div class="skeleton-detail">
        <div class="skeleton-avatar-lg"></div>
        <div class="skeleton-info">
          <div class="skeleton-name-lg"></div>
          <div class="skeleton-roles-lg"></div>
          <div class="skeleton-desc-lg"></div>
        </div>
      </div>
    </div>

    <!-- Контент -->
    <div v-else-if="person" class="person-detail">
      <!-- Основная информация -->
      <div class="person-header">
        <div class="person-photo">
          <img
            v-if="person.photo_url"
            :src="getMediaUrl(person.photo_url)"
            :alt="person.name"
            class="photo-image"
          />
          <div v-else class="photo-placeholder">
            {{ person.name[0]?.toUpperCase() }}
          </div>
        </div>

        <div class="person-main-info">
          <h1 class="person-name">{{ person.name }}</h1>
          <p v-if="person.name_jp" class="person-name-jp">{{ person.name_jp }}</p>
          
          <div class="person-roles">
            <span
              v-for="(role, index) in person.roles_display"
              :key="index"
              class="role-badge"
            >
              {{ role }}
            </span>
          </div>

          <p v-if="person.birth_date" class="person-birth">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            {{ formatDate(person.birth_date) }}
          </p>

          <p class="person-works">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
            {{ person.works_count || person.anime_count || 0 }} работ
          </p>
        </div>
      </div>

      <!-- Биография -->
      <div v-if="person.description" class="person-bio">
        <h2 class="section-title">О себе</h2>
        <p class="bio-text">{{ person.description }}</p>
      </div>

      <!-- Фильмография -->
      <div class="person-filmography">
        <h2 class="section-title">Фильмография</h2>
        
        <div v-if="animeLoading" class="anime-loading">
          <div class="spinner"></div>
          <span>Загрузка...</span>
        </div>

        <div v-else-if="relatedAnime.length > 0" class="anime-grid">
          <router-link
            v-for="anime in relatedAnime"
            :key="anime.id"
            :to="`/anime/${anime.id}`"
            class="anime-item"
          >
            <div class="anime-poster">
              <img
                v-if="anime.poster_url"
                :src="getMediaUrl(anime.poster_url)"
                :alt="anime.title_ru || anime.title_en"
              />
              <div v-else class="poster-placeholder">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="2" y="2" width="20" height="20" rx="2"/>
                  <path d="M12 2v20M2 12h20"/>
                </svg>
              </div>
            </div>
            <div class="anime-info">
              <h3 class="anime-title">{{ anime.title_ru || anime.title_en }}</h3>
              <p class="anime-meta">
                {{ anime.year }}
                <span v-if="anime.type">· {{ anime.type }}</span>
              </p>
            </div>
          </router-link>
        </div>

        <div v-else class="anime-empty">
          <p>Нет данных о работах</p>
        </div>
      </div>
    </div>

    <!-- Ошибка -->
    <div v-else class="error-state">
      <p>Персона не найдена</p>
      <router-link to="/people" class="back-link">Вернуться к списку</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getMediaUrl } from '@/api/client'
import peopleApi, { type PersonDetail } from '@/api/people'

const route = useRoute()

const person = ref<PersonDetail | null>(null)
const relatedAnime = ref<any[]>([])
const isLoading = ref(true)
const animeLoading = ref(false)

const fetchPerson = async () => {
  isLoading.value = true
  try {
    const id = Number(route.params.id)
    const response = await peopleApi.getPerson(id)
    person.value = response.data
  } catch (error) {
    console.error('Error fetching person:', error)
    person.value = null
  } finally {
    isLoading.value = false
  }
}

const fetchRelatedAnime = async () => {
  if (!person.value) return
  
  animeLoading.value = true
  try {
    const id = Number(route.params.id)
    const response = await peopleApi.getPersonAnime(id)
    relatedAnime.value = response.data.results || response.data || []
  } catch (error) {
    console.error('Error fetching related anime:', error)
    relatedAnime.value = []
  } finally {
    animeLoading.value = false
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

onMounted(async () => {
  await fetchPerson()
  if (person.value) {
    await fetchRelatedAnime()
  }
})
</script>

<style scoped>
.people-detail-page {
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

/* Breadcrumb */
.breadcrumb {
  margin-bottom: 1.5rem;
}

.breadcrumb-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  text-decoration: none;
  transition: color 0.2s;
}

.breadcrumb-link:hover {
  color: var(--color-accent);
}

/* Загрузка */
.loading-state {
  padding: 2rem 0;
}

.skeleton-detail {
  display: flex;
  gap: 2rem;
}

.skeleton-avatar-lg {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: var(--color-background-active);
  animation: pulse 1.5s infinite;
}

.skeleton-info {
  flex: 1;
}

.skeleton-name-lg {
  height: 36px;
  width: 60%;
  background: var(--color-background-active);
  border-radius: 4px;
  margin-bottom: 1rem;
  animation: pulse 1.5s infinite;
}

.skeleton-roles-lg {
  height: 24px;
  width: 40%;
  background: var(--color-background-active);
  border-radius: 4px;
  margin-bottom: 1rem;
  animation: pulse 1.5s infinite;
}

.skeleton-desc-lg {
  height: 100px;
  width: 100%;
  background: var(--color-background-active);
  border-radius: 4px;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Детали персоны */
.person-header {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
}

.person-photo {
  flex-shrink: 0;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-background-active);
}

.photo-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent);
  color: #fff;
  font-size: 4rem;
  font-weight: 700;
}

.person-main-info {
  flex: 1;
}

.person-name {
  font-size: 2rem;
  font-weight: 800;
  color: var(--color-text);
  margin: 0 0 0.25rem;
}

.person-name-jp {
  font-size: 1.125rem;
  color: var(--color-text-tertiary);
  margin: 0 0 1rem;
}

.person-roles {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.375rem 0.75rem;
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
}

.person-birth,
.person-works {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  margin: 0.5rem 0;
}

/* Секции */
.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 1rem;
}

.person-bio {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
}

.bio-text {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* Фильмография */
.person-filmography {
  margin-bottom: 2rem;
}

.anime-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--color-text-tertiary);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-divider);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
}

.anime-item {
  display: flex;
  flex-direction: column;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  overflow: hidden;
  text-decoration: none;
  transition: all 0.2s;
}

.anime-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  border-color: var(--color-accent);
}

.anime-poster {
  aspect-ratio: 2/3;
  background: var(--color-background-active);
  overflow: hidden;
}

.anime-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
}

.anime-info {
  padding: 0.75rem;
}

.anime-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.anime-meta {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin: 0;
}

.anime-empty {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-tertiary);
}

/* Ошибка */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: var(--color-text-tertiary);
}

.back-link {
  margin-top: 1rem;
  color: var(--color-accent);
  text-decoration: none;
}

/* Адаптивность */
@media (max-width: 768px) {
  .people-detail-page {
    padding: 1rem;
  }

  .person-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .person-photo {
    width: 150px;
    height: 150px;
  }

  .person-name {
    font-size: 1.5rem;
  }

  .person-roles {
    justify-content: center;
  }

  .person-birth,
  .person-works {
    justify-content: center;
  }

  .anime-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  }
}
</style>
