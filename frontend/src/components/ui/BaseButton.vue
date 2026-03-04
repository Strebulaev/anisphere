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
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: 500;
  border-radius: var(--radius-button);
  cursor: pointer;
  transition:
    background-color var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out),
    transform var(--duration-fast) var(--ease-out);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: 1px solid transparent;
  outline: none;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  white-space: nowrap;
}

.base-button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.base-button:active {
  transform: scale(0.97);
}

/* ── Варианты ───────────────────────────────────── */
.base-button--primary {
  background-color: var(--accent);
  color: var(--text-on-accent);
  border-color: var(--accent);
}
.base-button--primary:hover {
  background-color: var(--accent-hover);
  border-color: var(--accent-hover);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

.base-button--secondary {
  background-color: var(--surface-4);
  color: var(--text-primary);
  border-color: var(--border-default);
}
.base-button--secondary:hover {
  background-color: var(--surface-5);
  border-color: var(--border-strong);
}

.base-button--tertiary {
  background-color: transparent;
  color: var(--accent);
  border-color: transparent;
  padding: 0 var(--space-2);
}
.base-button--tertiary:hover {
  background-color: var(--accent-subtle);
}

.base-button--danger {
  background-color: var(--danger-subtle);
  color: var(--danger);
  border-color: transparent;
}
.base-button--danger:hover {
  background-color: var(--danger);
  color: #fff;
}

/* ── Размеры ────────────────────────────────────── */
.base-button--small  { padding: 0 var(--space-3); min-height: 28px; font-size: var(--text-sm); }
.base-button--medium { padding: 0 var(--space-4); min-height: 36px; font-size: var(--text-base); }
.base-button--large  { padding: 0 var(--space-6); min-height: 44px; font-size: var(--text-md); }

/* ── Состояния ──────────────────────────────────── */
.base-button--disabled {
  background-color: var(--surface-4);
  color: var(--text-disabled);
  border-color: transparent;
  cursor: not-allowed;
  opacity: 0.5;
}

.base-button--loading { pointer-events: none; opacity: 0.7; }
.base-button--full-width { width: 100%; }

/* ── Спиннер ────────────────────────────────────── */
.button-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.25);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin var(--duration-slower) linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
