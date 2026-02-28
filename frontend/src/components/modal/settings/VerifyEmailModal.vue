<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal" @click.stop>
      <h3>Подтвердить email</h3>
      
      <p>Введите код подтверждения, отправленный на {{ email }}</p>
      
      <div class="modal-form">
        <input v-model="code" type="text" placeholder="Код из письма" maxlength="6" />
      </div>

      <div class="modal-actions">
        <button @click="resend" class="resend-btn">Отправить повторно</button>
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
        <button @click="verify" class="confirm-btn">Подтвердить</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  show: boolean
  email?: string
}>()

const emit = defineEmits<{
  close: []
  verify: [code: string]
  resend: []
}>()

const code = ref('')

const verify = () => {
  emit('verify', code.value)
}

const resend = () => {
  emit('resend')
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
}

.modal-form {
  margin-bottom: 20px;
}

.modal-form input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-color);
  color: var(--text-color);
  font-size: 18px;
  text-align: center;
  letter-spacing: 4px;
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

.resend-btn {
  padding: 10px 20px;
  border: 1px solid var(--primary-color);
  background: transparent;
  color: var(--primary-color);
  border-radius: 6px;
  cursor: pointer;
}
</style>
