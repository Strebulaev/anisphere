<template>
  <div class="user-feed">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка ленты...</p>
    </div>
    <div v-else-if="posts.length === 0" class="empty">
      <p>Нет записей</p>
    </div>
    <div v-else class="posts-list">
      <PostCard
        v-for="post in posts"
        :key="post.id"
        :post="post"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import PostCard from '@/components/Cards/PostCard.vue'

interface Props {
  userId: number
}

const props = defineProps<Props>()

const loading = ref(true)
const posts = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    const response = await fetch(`/api/users/${props.userId}/feed/`)
    const data = await response.json()
    posts.value = data.results || data
  } catch (error) {
    console.error('Ошибка загрузки ленты:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.user-feed {
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

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
