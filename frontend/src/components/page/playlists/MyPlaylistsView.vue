<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

// MyPlaylistsView перенаправляет на основную страницу плейлистов с фильтром "мои"
const router = useRouter()

onMounted(() => {
  router.replace('/playlists')
})
</script>

<template>
  <div></div>
</template>
