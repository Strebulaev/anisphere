<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal" @click.stop>
      <h3>Изменить email</h3>
      
      <div class="modal-form">
        <label>Новый email</label>
        <input v-model="newEmail" type="email" placeholder="example@mail.com" />
        
        <label>Текущий пароль</label>
        <input v-model="password" type="password" placeholder="Введите пароль" />
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
        <button @click="save" class="confirm-btn">Изменить</button>
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
  save: [email: string, password: string]
}>()

const newEmail = ref('')
const password = ref('')

const save = () => {
  emit('save', newEmail.value, password.value)
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

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.modal-form label {
  font-weight: 500;
  font-size: 14px;
}

.modal-form input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-color);
  color: var(--text-color);
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
