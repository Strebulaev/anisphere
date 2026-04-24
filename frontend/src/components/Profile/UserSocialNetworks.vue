<template>
  <div class="user-social-networks">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка информации...</p>
    </div>
    <div v-else class="social-content">
      <h2>Социальные сети</h2>
      
      <div v-if="hasNoSocialNetworks" class="empty">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
        </svg>
        <p>Пользователь пока не добавил социальные сети</p>
      </div>

      <div v-else class="social-grid">
        <!-- Social links from social_links array -->
        <div v-for="(link, index) in user.social_links" :key="index" class="social-item">
          <div class="social-icon">🔗</div>
          <div class="social-info">
            <h3>{{ link.name || 'Ссылка' }}</h3>
            <a :href="formatUrl(link.url)" target="_blank" rel="noopener noreferrer" class="social-link">
              {{ link.url }}
            </a>
          </div>
        </div>
      </div>

      <div v-if="canEdit" class="edit-section">
        <button @click="$emit('edit')" class="btn-edit">
          Редактировать социальные сети
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

interface Props {
  user: any
  canEdit?: boolean
}

const props = defineProps<Props>()
const loading = ref(false)

defineEmits<{
  edit: []
}>()

const hasNoSocialNetworks = computed(() => {
  return !(props.user?.social_links && Array.isArray(props.user.social_links) && props.user.social_links.length > 0)
})

const formatUrl = (url: string) => {
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return `https://${url}`
  }
  return url
}

// Загружаем данные профиля если не переданы в пропсах
onMounted(() => {
  loading.value = true
  // Если user передан, не загружаем
  if (props.user) {
    loading.value = false
  }
  // TODO: возможно загрузка по ID пользователя
})
</script>

<style scoped>
.user-social-networks {
  background: var(--color-background-surface);
  border-radius: 1rem;
  padding: 2rem;
  min-height: 400px;
}

.loading,
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--color-text-secondary);
}

.empty svg {
  margin-bottom: 1rem;
  opacity: 0.5;
}

.social-content h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
}

.social-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.social-item {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  background: var(--color-background);
  border-radius: 0.75rem;
  border: 1px solid var(--color-divider);
  transition: transform 0.2s, border-color 0.2s;
}

.social-item:hover {
  transform: translateY(-2px);
  border-color: var(--color-accent);
}

.social-icon {
  font-size: 1.5rem;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-background-surface);
  border-radius: 50%;
  flex-shrink: 0;
}

.social-info {
  flex: 1;
}

.social-info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text);
}

.social-link,
.social-text {
  color: var(--color-text-secondary);
}

.social-link {
  color: var(--color-accent);
  text-decoration: none;
  transition: color 0.2s;
}

.social-link:hover {
  color: var(--color-accent-dark);
  text-decoration: underline;
}

.edit-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-divider);
}

.btn-edit {
  padding: 0.75rem 1.5rem;
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-edit:hover {
  background: var(--color-accent-dark);
}

@media (max-width: 768px) {
  .user-social-networks {
    padding: 1.5rem;
  }
  
  .social-item {
    padding: 1rem;
  }
}
</style>