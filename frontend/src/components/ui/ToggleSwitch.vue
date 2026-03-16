<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :disabled="disabled"
    class="toggle-switch"
    :class="{ 'toggle-active': modelValue, 'toggle-disabled': disabled }"
    @click="toggle"
  >
    <span class="toggle-slider"></span>
  </button>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const toggle = () => {
  if (!props.disabled) {
    emit('update:modelValue', !props.modelValue)
  }
}
</script>

<style scoped>
.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  background: #374151;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
  padding: 0;
}

.toggle-switch:hover:not(.toggle-disabled) {
  background: #4b5563;
}

.toggle-active {
  background: #3b82f6;
}

.toggle-active:hover:not(.toggle-disabled) {
  background: #2563eb;
}

.toggle-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-slider {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.toggle-active .toggle-slider {
  transform: translateX(20px);
}
</style>
