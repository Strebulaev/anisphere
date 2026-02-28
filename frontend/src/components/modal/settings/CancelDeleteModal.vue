<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal success-modal" @click.stop>
      <h3>Отменить удаление аккаунта?</h3>
      
      <p>Если вы отмените удаление, ваш аккаунт останется активным и вы сможете продолжить пользоваться сервисом.</p>
      
      <div class="modal-info">
        <strong>Информация:</strong>
        <p>Запрос на удаление будет отменен, и все ваши данные сохранятся.</p>
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
        <button @click="$emit('confirm')" class="confirm-btn">Отменить удаление</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean
}>()

defineEmits<{
  close: []
  confirm: []
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
  max-width: 400px;
  width: 90%;
  border: 1px solid var(--border-color);
}

.success-modal {
  border-color: #10b981;
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #10b981;
}

.modal p {
  margin-bottom: 15px;
  color: var(--secondary-text);
  line-height: 1.5;
}

.modal-info {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid #10b981;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 20px;
}

.modal-info strong {
  display: block;
  margin-bottom: 5px;
}

.modal-info p {
  margin: 0;
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
  background: #10b981;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}
</style>
