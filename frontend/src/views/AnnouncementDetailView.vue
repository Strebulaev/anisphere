<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/api/client'

const route = useRoute()
const announcement = ref<any>(null)
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const slug = route.params.slug
    const response = await apiClient.get(`/anime/announcements/${slug}/`)
    announcement.value = response.data
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка загрузки анонса'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="announcement-detail">
    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="announcement" class="content">
      <h1>{{ announcement.title }}</h1>
      <div class="meta">
        <span>{{ new Date(announcement.created_at).toLocaleDateString() }}</span>
      </div>
      <div class="body" v-html="announcement.content"></div>
    </div>
  </div>
</template>

<style scoped>
.announcement-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}
h1 {
  font-size: 2rem;
  margin-bottom: 1rem;
}
.meta {
  color: #888;
  margin-bottom: 2rem;
}
.body {
  line-height: 1.6;
}
</style>