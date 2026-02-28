<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal" @click.stop>
      <h3>Экспорт данных</h3>
      
      <p>Выберите данные, которые хотите экспортировать:</p>
      
      <div class="modal-options">
        <label class="checkbox-label">
          <input type="checkbox" v-model="options.profile" />
          <span>Профиль и настройки</span>
        </label>
        <label class="checkbox-label">
          <input type="checkbox" v-model="options.playlists" />
          <span>Плейлисты</span>
        </label>
        <label class="checkbox-label">
          <input type="checkbox" v-model="options.favorites" />
          <span>Избранное</span>
        </label>
        <label class="checkbox-label">
          <input type="checkbox" v-model="options.history" />
          <span>История просмотра</span>
        </label>
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
        <button @click="exportData" class="confirm-btn">Экспортировать</button>
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
  export: [options: any]
}>()

const options = ref({
  profile: true,
  playlists: true,
  favorites: false,
  history: false
})

const exportData = () => {
  emit('export', options.value)
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
  margin-bottom: 15px;
  color: var(--secondary-text);
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
