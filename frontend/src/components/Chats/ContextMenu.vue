<script setup lang="ts">
interface Props {
  isOpen: boolean
  x?: number
  y?: number
}

defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="context-menu-backdrop"
      @click="emit('close')"
    >
      <div
        class="context-menu"
        :style="{ left: x + 'px', top: y + 'px' }"
        @click.stop
      >
        <div class="context-menu-content">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.context-menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
}

.context-menu {
  position: absolute;
  background: var(--color-background-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  min-width: 180px;
  max-width: 280px;
}

.context-menu-content {
  padding: 0.25rem;
}

:deep(.context-menu-item) {
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background 0.15s;
}

:deep(.context-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
}

:deep(.context-menu-divider) {
  height: 1px;
  background: var(--color-border);
  margin: 0.25rem 0;
}

:deep(.context-menu-item.danger) {
  color: #ff6b6b;
}

:deep(.context-menu-item.danger:hover) {
  background: rgba(244, 67, 54, 0.15);
}
</style>
