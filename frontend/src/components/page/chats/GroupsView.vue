<template>
  <div class="groups-view">
    <div class="container">
      <h1>Группы</h1>
      <p>Здесь будут сообщества аниме.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
  import NavBar from '@/components/Navigation/NavBar.vue'
</script>

<style scoped>
.groups-view {
  min-height: 100vh;
  background: var(--surface-1);
  position: relative;
}

/* Фоновый узор */
.groups-view::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 10% 90%, rgba(255,126,179,0.03) 0%, transparent 40%),
    radial-gradient(circle at 90% 10%, rgba(168,197,226,0.03) 0%, transparent 40%);
  pointer-events: none;
}

/* Мобильная адаптация - отступ сверху под мобильную навигацию */
@media (max-width: 767px) {
  .groups-view {
    padding-top: 54px;
    box-sizing: border-box;
  }
}

.container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

h1 {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

p {
  color: var(--text-tertiary);
}
</style>