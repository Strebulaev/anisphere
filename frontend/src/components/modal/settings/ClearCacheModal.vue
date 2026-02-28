<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal" @click.stop>
      <h3>Подтвердить очистку?</h3>
      <p>Это действие очистит кэш изображений и временные файлы. Вы можете потерять несохраненные данные.</p>
      
      <div class="modal-options">
        <label class="checkbox-label">
          <input type="checkbox" v-model="clearImages" />
          <span>Очистить изображения</span>
        </label>
        <label class="checkbox-label">
          <input type="checkbox" v-model="clearTemp" />
          <span>Очистить временные файлы</span>
        </label>
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
        <button @click="confirm" class="confirm-btn">Очистить</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  close: []
  confirm: [options: { clearImages: boolean; clearTemp: boolean }]
}>()

const clearImages = ref(true)
const clearTemp = ref(true)

const confirm = () => {
  emit('confirm', { clearImages: clearImages.value, clearTemp: clearTemp.value })
}
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
  max-width: 400px;
  width: 90%;
  border: 1px solid var(--border-color);
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.modal p {
  margin-bottom: 20px;
  color: var(--secondary-text);
  line-height: 1.5;
}

.modal-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 10px 20px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}

.confirm-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}
</style>
