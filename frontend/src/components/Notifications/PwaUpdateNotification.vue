<template>
  <Transition name="pwa-toast">
    <div v-if="needsRefresh" class="pwa-update-toast">
      <div class="pwa-update-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"/>
          <polyline points="1 20 1 14 7 14"/>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>
      </div>
      <div class="pwa-update-text">
        <span class="pwa-update-title">Доступно обновление</span>
        <span class="pwa-update-sub">Нажмите чтобы применить</span>
      </div>
      <button class="pwa-update-btn" @click="updateSW()">
        Обновить
      </button>
      <button class="pwa-update-close" @click="close">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRegisterSW } from 'virtual:pwa-register/vue'

const needsRefresh = ref(false)
let swUpdateFn: ((reloadPage?: boolean) => Promise<void>) | null = null

const { updateServiceWorker } = useRegisterSW({
  onNeedRefresh() {
    needsRefresh.value = true
  },
  onOfflineReady() {
    // приложение готово к работе офлайн — тихо, без уведомления
  },
})

swUpdateFn = updateServiceWorker

const updateSW = () => {
  updateServiceWorker(true)
}

const close = () => {
  needsRefresh.value = false
}
</script>

<style scoped>
.pwa-update-toast {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px 10px 12px;
  background: var(--surface-2);
  border: 1px solid var(--accent);
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(124, 92, 252, 0.15);
  z-index: 9999;
  min-width: 280px;
  max-width: 360px;
  backdrop-filter: blur(12px);
}

.pwa-update-icon {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--accent-subtle);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pwa-update-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.pwa-update-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.pwa-update-sub {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.pwa-update-btn {
  flex-shrink: 0;
  height: 30px;
  padding: 0 12px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--duration-base);
  white-space: nowrap;
}

.pwa-update-btn:hover {
  background: var(--accent-hover);
}

.pwa-update-close {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all var(--duration-base);
  padding: 0;
}

.pwa-update-close:hover {
  color: var(--text-primary);
  background: var(--surface-4);
}

/* Анимация */
.pwa-toast-enter-active,
.pwa-toast-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.pwa-toast-enter-from,
.pwa-toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(16px);
}

/* Десктоп — прижать к левому краю над навбаром */
@media (min-width: 768px) {
  .pwa-update-toast {
    bottom: 24px;
    left: auto;
    right: 24px;
    transform: none;
  }

  .pwa-toast-enter-from,
  .pwa-toast-leave-to {
    opacity: 0;
    transform: translateY(16px);
  }
}
</style>
