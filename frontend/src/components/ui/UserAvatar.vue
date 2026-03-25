<template>
  <div class="user-avatar" :class="avatarClasses" :style="avatarStyles">
    <OptimizedImage 
      v-if="src && !imageError" 
      :src="src" 
      :alt="alt"
      class="avatar-image"
      @error="handleImageError"
    />
    <div v-else class="avatar-placeholder">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    </div>
    
    <!-- Индикатор онлайн-статуса -->
    <div v-if="showOnlineStatus" class="online-indicator" :class="onlineClass"></div>
    
    <!-- Динамическая рамка уровня -->
    <div v-if="showLevelBorder && level !== undefined" class="level-border">
      <svg class="level-ring" viewBox="0 0 136 136">
        <circle
          cx="68"
          cy="68"
          r="62"
          fill="none"
          :stroke="levelBorderColor"
          stroke-width="4"
        />
        <circle
          v-if="levelProgress !== undefined"
          cx="68"
          cy="68"
          r="62"
          fill="none"
          :stroke="levelBorderColor"
          stroke-width="4"
          :stroke-dasharray="levelCircumference"
          :stroke-dashoffset="levelOffset"
          stroke-linecap="round"
          transform="rotate(-90 68 68)"
          class="level-progress-ring"
        />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  src?: string
  alt?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  shape?: 'circle' | 'square' | 'rounded'
  isOnline?: boolean | null
  showOnlineStatus?: boolean
  level?: number
  levelProgress?: number
  showLevelBorder?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  alt: 'Avatar',
  size: 'md',
  shape: 'circle',
  isOnline: null,
  showOnlineStatus: true,
  showLevelBorder: false,
})

const imageError = ref(false)

const avatarClasses = computed(() => {
  return [
    `user-avatar--${props.size}`,
    `user-avatar--${props.shape}`,
  ]
})

const avatarStyles = computed(() => {
  const styles: Record<string, string> = {}
  return styles
})

const onlineClass = computed(() => {
  if (props.isOnline === null) return 'online-indicator--unknown'
  return props.isOnline ? 'online-indicator--online' : 'online-indicator--offline'
})

const levelBorderColor = computed(() => {
  const level = props.level || 0
  if (level >= 41) return 'var(--color-level-41-plus)'
  if (level >= 31) return 'var(--color-level-31-40)'
  if (level >= 21) return 'var(--color-level-21-30)'
  if (level >= 11) return 'var(--color-level-11-20)'
  return 'var(--color-level-1-10)'
})

const levelCircumference = computed(() => {
  return 2 * Math.PI * 62
})

const levelOffset = computed(() => {
  if (props.levelProgress === undefined) return 0
  const progress = Math.min(Math.max(props.levelProgress, 0), 100)
  return levelCircumference.value - (progress / 100) * levelCircumference.value
})

const handleImageError = () => {
  imageError.value = true
}
</script>

<style scoped>
.user-avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-background-surface);
  border: 2px solid var(--color-divider);
  overflow: visible;
  flex-shrink: 0;
}

/* Размеры */
.user-avatar--xs {
  width: 24px;
  height: 24px;
  font-size: 10px;
}

.user-avatar--sm {
  width: 32px;
  height: 32px;
  font-size: 12px;
}

.user-avatar--md {
  width: 40px;
  height: 40px;
  font-size: 14px;
}

.user-avatar--lg {
  width: 48px;
  height: 48px;
  font-size: 16px;
}

.user-avatar--xl {
  width: 64px;
  height: 64px;
  font-size: 20px;
}

.user-avatar--2xl {
  width: 120px;
  height: 120px;
  font-size: 32px;
}

/* Формы */
.user-avatar--circle {
  border-radius: 50%;
}

.user-avatar--square {
  border-radius: 8px;
}

.user-avatar--rounded {
  border-radius: 12px;
}

/* Изображение */
.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
}

/* Индикатор онлайн-статуса */
.online-indicator {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--color-background);
  z-index: 2;
}

.user-avatar--xs .online-indicator,
.user-avatar--sm .online-indicator {
  width: 8px;
  height: 8px;
  border-width: 1px;
}

.user-avatar--xl .online-indicator,
.user-avatar--2xl .online-indicator {
  width: 16px;
  height: 16px;
  border-width: 3px;
}

.online-indicator--online {
  background-color: var(--color-accent-teal);
}

.online-indicator--offline {
  background-color: var(--color-text-disabled);
}

.online-indicator--unknown {
  background-color: var(--color-text-tertiary);
}

/* Позиционирование индикатора */
.user-avatar--circle .online-indicator,
.user-avatar--rounded .online-indicator {
  bottom: 0;
  right: 0;
}

.user-avatar--square .online-indicator {
  bottom: -2px;
  right: -2px;
}

/* Рамка уровня */
.level-border {
  position: absolute;
  top: -8px;
  left: -8px;
  width: calc(100% + 16px);
  height: calc(100% + 16px);
  pointer-events: none;
}

.level-ring {
  width: 100%;
  height: 100%;
  animation: spin-slow 120s linear infinite;
}

.level-progress-ring {
  transition: stroke-dashoffset 0.5s var(--transition-smooth);
}

/* Ховер эффекты */
.user-avatar {
  transition: border-color 0.15s var(--transition-smooth);
}

.user-avatar:hover {
  border-color: var(--color-accent);
}

.user-avatar--2xl:hover .level-border {
  transform: scale(1.02);
}

@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
