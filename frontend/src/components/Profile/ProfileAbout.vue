<template>
  <div class="profile-about">
    <div v-if="!user" class="loading">
      <LoadingSpinner />
    </div>
    <div v-else class="about-content">
      <h2>О себе</h2>
      <p v-if="user.bio" class="bio">{{ user.bio }}</p>
      <p v-else class="no-bio">Пользователь пока ничего не написал о себе</p>

      <div class="info-section">
        <h3>Основная информация</h3>
        
        <div v-if="user.display_name" class="info-item">
          <strong><SakuraIcon name="user" /> Отображаемое имя:</strong>
          <span>{{ user.display_name }}</span>
        </div>

        <div v-if="user.nickname" class="info-item">
          <strong><SakuraIcon name="tag" /> Никнейм:</strong>
          <span>@{{ user.nickname }}</span>
        </div>

        <div v-if="user.created_at" class="info-item">
          <strong>🗓 На сайте с:</strong>
          <span>{{ formatDate(user.created_at) }}</span>
        </div>
      </div>

      

      <div v-if="user.favorite_genres && user.favorite_genres.length > 0" class="info-section">
        <h3>Любимые жанры</h3>
        <div class="genres-list">
          <span v-for="genre in user.favorite_genres" :key="genre" class="genre-tag">
            {{ genre }}
          </span>
        </div>
      </div>

      <div v-if="user.badges && user.badges.length > 0" class="info-section">
        <h3>Значки</h3>
        <div class="badges-list">
          <span v-for="badge in user.badges" :key="badge" class="badge-tag">
            {{ badge }}
          </span>
        </div>
      </div>

      <!-- <div class="info-section">
        <h3>Статистика</h3>
        
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ user.level || 1 }}</div>
            <div class="stat-label">Уровень</div>
          </div>
          
          <div class="stat-item">
            <div class="stat-value">{{ user.experience || 0 }}</div>
            <div class="stat-label">Опыт</div>
          </div>

          <div class="stat-item">
            <div class="stat-value">{{ user.mana || 0 }}</div>
            <div class="stat-label">Мана</div>
          </div>

          <div class="stat-item">
            <div class="stat-value">{{ user.posts_count || 0 }}</div>
            <div class="stat-label">Посты</div>
          </div>

          <div class="stat-item">
            <div class="stat-value">{{ user.comments_count || 0 }}</div>
            <div class="stat-label">Комментарии</div>
          </div>

          <div class="stat-item">
            <div class="stat-value">{{ user.likes_received || 0 }}</div>
            <div class="stat-label">Лайки</div>
          </div>

          <div class="stat-item">
            <div class="stat-value">{{ user.playlists_count || 0 }}</div>
            <div class="stat-label">Плейлисты</div>
          </div>
        </div>
      </div> -->


    </div>
  </div>
</template>

<script setup lang="ts">
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

interface Props {
  user: any
}

defineProps<Props>()

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

const formatDateTime = (date: string) => {
  return new Date(date).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.profile-about {
  background: var(--color-background-surface);
  border-radius: 1rem;
  padding: 2rem;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.about-content h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
}

.bio {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--color-text-secondary);
  margin-bottom: 1.5rem;
}

.no-bio {
  color: var(--color-text-tertiary);
  font-style: italic;
  margin-bottom: 1.5rem;
}

.info-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: var(--color-background);
  border-radius: 0.75rem;
  border: 1px solid var(--color-divider);
}

.info-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text);
}

.info-item {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  color: var(--color-text-secondary);
  align-items: center;
}

.info-item strong {
  color: var(--color-text);
  min-width: 180px;
}

.info-item a {
  color: var(--color-accent);
  text-decoration: none;
}

.info-item a:hover {
  text-decoration: underline;
}

.verified-badge {
  color: var(--color-accent-teal);
  font-weight: 500;
}

.unverified-badge {
  color: var(--color-text-tertiary);
  font-style: italic;
}

.enabled-badge {
  color: var(--color-accent-teal);
  font-weight: 500;
}

.disabled-badge {
  color: var(--color-text-tertiary);
}

.online-badge {
  color: var(--color-accent-teal);
  font-weight: 500;
}

.offline-badge {
  color: var(--color-text-tertiary);
}

.genres-list,
.badges-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.genre-tag,
.badge-tag {
  padding: 0.4rem 0.8rem;
  background: var(--color-accent);
  color: white;
  border-radius: 2rem;
  font-size: 0.85rem;
  font-weight: 500;
}

.badge-tag {
  background: var(--color-accent-teal);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 1rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background: var(--color-background-surface);
  border-radius: 0.5rem;
  border: 1px solid var(--color-divider);
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--color-text-tertiary);
}


</style>
