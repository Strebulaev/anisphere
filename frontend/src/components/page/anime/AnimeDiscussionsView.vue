<template>
  <div class="anime-discussions-view">
    <div class="container">
      <div class="view-header">
        <h1 class="view-title">Обсуждения аниме</h1>
        <p class="view-subtitle">Аниме, которые вы обсуждаете</p>
      </div>

      <AnimeDiscussionsList />
    </div>
  </div>
</template>

<script setup lang="ts">
import AnimeDiscussionsList from '@/components/anime/AnimeDiscussionsList.vue'
</script>

<style scoped>
.anime-discussions-view {
  min-height: 100vh;
  background-color: var(--color-background);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.view-header {
  margin-bottom: 2rem;
  text-align: center;
}

.view-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.5rem 0;
}

.view-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }

  .view-title {
    font-size: 1.5rem;
  }

  .view-subtitle {
    font-size: 0.875rem;
  }
}
</style>
