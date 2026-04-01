<template>
  <div class="groups-view">
    <div class="container">
      <h1>Группы</h1>
      <p>Здесь будут сообщества аниме.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
  import NavBar from '@/components/NavBar.vue'
</script>

<style scoped>
.groups-view {
  min-height: 100vh;
}

/* Мобильная адаптация - отступ сверху под мобильную навигацию */
@media (max-width: 767px) {
  .groups-view {
    padding-top: 60px;
    box-sizing: border-box;
  }
}

.container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  font-size: 2rem;
  margin-bottom: 1rem;
}

p {
  color: var(--color-text-tertiary);
}
</style>