<template>
  <div class="progress-bar" :class="progressBarClasses">
    <div 
      class="progress-bar-fill"
      :style="fillStyles"
      role="progressbar"
      :aria-valuenow="value"
      :aria-valuemin="min"
      :aria-valuemax="max"
    >
      <span v-if="showLabel && labelPosition === 'inside'" class="progress-bar-label">
        {{ formattedValue }}%
      </span>
    </div>
    <span v-if="showLabel && labelPosition === 'outside'" class="progress-bar-label-outside">
      {{ formattedValue }}%
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  value: number
  min?: number
  max?: number
  size?: 'small' | 'medium' | 'large'
  variant?: 'primary' | 'success' | 'warning' | 'danger'
  color?: string
  showLabel?: boolean
  labelPosition?: 'inside' | 'outside'
  animated?: boolean
  striped?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  min: 0,
  max: 100,
  size: 'medium',
  variant: 'primary',
  showLabel: false,
  labelPosition: 'inside',
  animated: false,
  striped: false,
})

const progressBarClasses = computed(() => {
  return [
    `progress-bar--${props.size}`,
    `progress-bar--${props.variant}`,
    {
      'progress-bar--animated': props.animated,
      'progress-bar--striped': props.striped,
    },
  ]
})

const normalizedValue = computed(() => {
  return Math.min(Math.max(props.value, props.min), props.max)
})

const percentage = computed(() => {
  const range = props.max - props.min
  if (range === 0) return 0
  return ((normalizedValue.value - props.min) / range) * 100
})

const formattedValue = computed(() => {
  return Math.round(percentage.value)
})

const fillStyles = computed(() => {
  const styles: Record<string, string> = {
    width: `${percentage.value}%`,
  }
  
  if (props.color) {
    styles.backgroundColor = props.color
  }
  
  return styles
})
</script>

<style scoped>
.progress-bar {
  position: relative;
  width: 100%;
  background-color: var(--color-background-active);
  border-radius: 4px;
  overflow: hidden;
}

/* Размеры */
.progress-bar--small {
  height: 6px;
}

.progress-bar--medium {
  height: 8px;
}

.progress-bar--large {
  height: 12px;
}

/* Заполнение */
.progress-bar-fill {
  height: 100%;
  background-color: var(--color-accent);
  border-radius: 4px;
  transition: width 0.3s var(--transition-smooth);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Варианты цветов */
.progress-bar--primary .progress-bar-fill {
  background-color: var(--color-accent);
}

.progress-bar--success .progress-bar-fill {
  background-color: var(--color-accent-teal);
}

.progress-bar--warning .progress-bar-fill {
  background-color: var(--color-accent-orange);
}

.progress-bar--danger .progress-bar-fill {
  background-color: var(--color-accent-pink);
}

/* Полосатый эффект */
.progress-bar--striped .progress-bar-fill {
  background-image: linear-gradient(
    45deg,
    rgba(0, 0, 0, 0.1) 25%,
    transparent 25%,
    transparent 50%,
    rgba(0, 0, 0, 0.1) 50%,
    rgba(0, 0, 0, 0.1) 75%,
    transparent 75%,
    transparent
  );
  background-size: 20px 20px;
}

/* Анимированный эффект */
.progress-bar--animated .progress-bar-fill {
  animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
  0% {
    background-position: 20px 0;
  }
  100% {
    background-position: 0 0;
  }
}

/* Лейбл внутри */
.progress-bar-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  white-space: nowrap;
}

.progress-bar--large .progress-bar-label {
  font-size: 12px;
}

/* Лейбл снаружи */
.progress-bar-label-outside {
  margin-left: 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}
</style>
