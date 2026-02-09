<template>
  <button
    :class="buttonClasses"
    :disabled="disabled || isLoading"
    :type="type"
    @click="handleClick"
  >
    <span v-if="isLoading" class="button-spinner"></span>
    <slot v-else></slot>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'tertiary' | 'danger'
  size?: 'small' | 'medium' | 'large'
  disabled?: boolean
  isLoading?: boolean
  type?: 'button' | 'submit' | 'reset'
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'medium',
  disabled: false,
  isLoading: false,
  type: 'button',
  fullWidth: false,
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const buttonClasses = computed(() => {
  return [
    'base-button',
    `base-button--${props.variant}`,
    `base-button--${props.size}`,
    {
      'base-button--disabled': props.disabled,
      'base-button--loading': props.isLoading,
      'base-button--full-width': props.fullWidth,
    },
  ]
})

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.isLoading) {
    emit('click', event)
  }
}
</script>

<style scoped>
.base-button {
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: all 0.15s var(--transition-smooth);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  outline: none;
  min-height: 44px;
  touch-action: manipulation;
}

.base-button:active {
  transform: scale(0.98);
}

/* Варианты */
.base-button--primary {
  background-color: var(--color-accent);
  color: white;
}

.base-button--primary:hover {
  background-color: var(--color-accent-hover);
}

.base-button--primary:active {
  background-color: var(--color-accent-active);
}

.base-button--secondary {
  background-color: transparent;
  color: var(--color-accent);
  border: 1px solid var(--color-accent);
}

.base-button--secondary:hover {
  background-color: rgba(58, 134, 255, 0.1);
}

.base-button--secondary:active {
  background-color: rgba(58, 134, 255, 0.2);
}

.base-button--tertiary {
  background-color: transparent;
  color: var(--color-accent);
  border: none;
  padding: 0 8px;
}

.base-button--tertiary:hover {
  text-decoration: underline;
}

.base-button--danger {
  background-color: var(--color-accent-pink);
  color: white;
}

.base-button--danger:hover {
  background-color: var(--color-accent-pink-hover);
}

/* Размеры */
.base-button--small {
  padding: 8px 16px;
  font-size: 12px;
  min-height: 32px;
}

.base-button--medium {
  padding: 10px 16px;
  font-size: 14px;
  min-height: 40px;
}

.base-button--large {
  padding: 12px 24px;
  font-size: 16px;
  min-height: 48px;
}

/* Состояния */
.base-button--disabled {
  background-color: var(--color-background-active);
  color: var(--color-text-disabled);
  border-color: transparent;
  cursor: not-allowed;
}

.base-button--loading {
  pointer-events: none;
}

.base-button--full-width {
  width: 100%;
}

/* Спиннер загрузки */
.button-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: var(--color-text);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
