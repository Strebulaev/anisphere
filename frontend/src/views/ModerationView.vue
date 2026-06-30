<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const complaints = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const response = await apiClient.get('/social/complaints/')
    complaints.value = response.data.results || response.data
  } catch (e) {
    console.error('Failed to load complaints:', e)
  } finally {
    loading.value = false
  }
})

const resolveComplaint = async (id: number) => {
  try {
    await apiClient.post(`/social/complaints/${id}/resolve/`)
    complaints.value = complaints.value.filter(c => c.id !== id)
  } catch (e) {
    console.error('Failed to resolve complaint:', e)
  }
}
</script>

<template>
  <div class="moderation-view">
    <h1>Модерация</h1>
    <div v-if="loading">Загрузка...</div>
    <div v-else-if="complaints.length === 0">Нет жалоб</div>
    <div v-else class="complaints-list">
      <div v-for="complaint in complaints" :key="complaint.id" class="complaint-card">
        <h3>{{ complaint.reason }}</h3>
        <p>{{ complaint.description }}</p>
        <button @click="resolveComplaint(complaint.id)">Решить</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.moderation-view {
  padding: 2rem;
}
.complaint-card {
  border: 1px solid #ddd;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 8px;
}
</style>