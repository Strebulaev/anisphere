<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal large-modal" @click.stop>
      <h3>Лицензионное соглашение</h3>
      <div class="modal-content legal-content">
        <p>Версия: 2.1</p>
        <p class="placeholder-text">[Содержание лицензионного соглашения...]</p>
      </div>
      <button @click="$emit('close')" class="close-modal-btn">Закрыть</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean
}>()

defineEmits<{
  close: []
}>()
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--card-bg);
  padding: 30px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  border: 1px solid var(--border-color);
  max-height: 80vh;
  overflow-y: auto;
}

.large-modal {
  max-width: 700px;
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 20px;
}

.modal-content {
  margin-bottom: 20px;
}

.legal-content {
  line-height: 1.6;
}

.placeholder-text {
  color: var(--secondary-text);
  font-style: italic;
}

.close-modal-btn {
  width: 100%;
  padding: 12px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
</style>
