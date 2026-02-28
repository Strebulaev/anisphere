<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal danger-modal" @click.stop>
      <h3>⚠️ Завершить все сессии?</h3>
      
      <p>Это действие завершит все активные сессии на всех устройствах, кроме текущего. Вам нужно будет заново авторизоваться.</p>
      
      <div class="modal-warning">
        <strong>Внимание:</strong>
        <ul>
          <li>Все устройства будут отключены</li>
          <li>Текущая сессия останется активной</li>
          <li>Действие нельзя отменить</li>
        </ul>
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
        <button @click="$emit('confirm')" class="confirm-btn">Завершить все</button>
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

.danger-modal {
  border-color: #f44336;
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #f44336;
}

.modal p {
  margin-bottom: 15px;
  color: var(--secondary-text);
  line-height: 1.5;
}

.modal-warning {
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid #f44336;
  border-radius: 6px;
  padding: 15px;
  margin-bottom: 20px;
}

.modal-warning ul {
  margin: 10px 0 0 20px;
  padding: 0;
}

.modal-warning li {
  margin-bottom: 5px;
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
  background: #f44336;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}
</style>
