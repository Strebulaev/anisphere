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
        :can-interact="canInteract"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import PostCard from '@/components/Cards/PostCard.vue'
import { postsApi } from '@/api/feed'

interface Props {
  userId: number
}

const props = defineProps<Props>()

const authStore = useAuthStore()
const loading = ref(true)
const posts = ref<any[]>([])

const currentUser = computed(() => authStore.user)
const canInteract = computed(() => {
  // Взаимодействие разрешено только со своими постами в своём профиле
  return currentUser.value?.id === props.userId
})

onMounted(async () => {
  loading.value = true
  try {
    const response = await postsApi.getUserPosts(props.userId)
    posts.value = response.data.results || response.data
  } catch (error) {
    console.error('Ошибка загрузки ленты:', error)
    posts.value = []
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
