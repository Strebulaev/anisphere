<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal" @click.stop>
      <h3>Фон для "{{ selectedChat?.name }}"</h3>
      
      <div class="modal-bg-options">
        <label class="modal-bg-option">
          <input type="radio" v-model="selectedChatBg" value="shared" />
          <span>Использовать общий фон</span>
        </label>
        <label class="modal-bg-option">
          <input type="radio" v-model="selectedChatBg" value="custom" />
          <span>Свой фон</span>
        </label>
      </div>

      <div v-if="selectedChatBg === 'custom'" class="modal-bg-upload">
        <input type="file" @change="handleFileChange" accept="image/*" />
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
        <button @click="save" class="confirm-btn">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  show: boolean
  selectedChat?: { name: string }
}>()

const emit = defineEmits<{
  close: []
  save: [background: string]
}>()

const selectedChatBg = ref('shared')
const backgroundFile = ref<File | null>(null)

const handleFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    backgroundFile.value = target.files[0]
  }
}

const save = () => {
  emit('save', selectedChatBg.value)
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
  margin-bottom: 20px;
}

.modal-bg-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.modal-bg-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.modal-bg-upload {
  margin-bottom: 20px;
}

.modal-bg-upload input {
  width: 100%;
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
