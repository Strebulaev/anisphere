<template>
  <div class="user-shorts">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка шортов...</p>
    </div>
    <div v-else-if="shorts.length === 0" class="empty">
      <p>Нет шортов</p>
    </div>
    <div v-else class="shorts-grid">
      <div
        v-for="short in shorts"
        :key="short.id"
        class="short-item"
      >
        <video
          v-if="short.video_url"
          :src="short.video_url"
          controls
          class="short-video"
        />
        <div class="short-info">
          <p>{{ short.title }}</p>
          <small>{{ formatDate(short.created_at) }}</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

interface Props {
  userId: number
}

const props = defineProps<Props>()

const loading = ref(true)
const shorts = ref<any[]>([])

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('ru-RU')
}

onMounted(async () => {
  loading.value = true
  try {
    const response = await fetch(`/api/reactor/posts/?user=${props.userId}`)
    if (!response.ok) throw new Error('Failed to load shorts')
    const data = await response.json()
    shorts.value = data.results || data
  } catch (error) {
    console.error('Ошибка загрузки шортов:', error)
    shorts.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.user-shorts {
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

.shorts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.short-item {
  background: var(--color-background-surface);
  border-radius: 0.75rem;
  overflow: hidden;
}

.short-video {
  width: 100%;
  aspect-ratio: 9/16;
  object-fit: cover;
}

.short-info {
  padding: 0.75rem;
}

.short-info p {
  margin: 0 0 0.25rem 0;
  font-weight: 500;
}

.short-info small {
  color: var(--color-text-secondary);
}
</style>
