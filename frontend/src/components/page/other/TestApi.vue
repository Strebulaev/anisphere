<template>
    <div class="p-8">
      <h1 class="text-2xl font-bold mb-4">Тест связи с бэкендом</h1>
      <button 
        @click="testApi" 
        class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Тест API
      </button>
      
      <div v-if="response" class="mt-4 p-4 bg-gray-100 rounded">
        <pre>{{ response }}</pre>
      </div>
      
      <div v-if="error" class="mt-4 p-4 bg-red-100 text-red-800 rounded">
        {{ error }}
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  import apiClient from '@/api/client'
  
  const response = ref(null)
  const error = ref('')
  
  const testApi = async () => {
    try {
      const { data } = await apiClient.get('/test/')
      response.value = data
      error.value = ''
    } catch (err) {
      error.value = 'Ошибка соединения с бэкендом'
      console.error(err)
    }
  }
  </script>