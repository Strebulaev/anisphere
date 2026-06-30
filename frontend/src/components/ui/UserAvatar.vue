<template>
  <div class="user-avatar" :class="avatarClasses" :style="avatarStyles">
    <img 
      v-if="effectiveSrc && !imageError" 
      :src="effectiveSrc" 
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
    <span
      v-if="showOnlineIndicator && isOnline"
      class="online-indicator"
    ></span>
    <PremiumCrown
      v-if="isPremium && showPremiumCrown"
      :size="crownSize"
      class="premium-crown-badge"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import PremiumCrown from '@/components/icons/PremiumCrown.vue'
// import OptimizedImage from './OptimizedImage.vue'
import { getDefaultAvatarForUser } from '@/utils/defaultAvatars'
import { getMediaUrl } from '@/api/client'

interface Props {
  src?: string | null
  user?: {
    id?: number | string
    username?: string
    avatar_url?: string | null
    avatar?: string | null
    display_name?: string
    is_premium?: boolean
  }
  alt?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  shape?: 'circle' | 'square' | 'rounded'
  showOnlineIndicator?: boolean
  isOnline?: boolean
  showPremiumCrown?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  alt: 'Avatar',
  size: 'md',
  shape: 'circle',
  showOnlineIndicator: false,
  isOnline: false,
  showPremiumCrown: true
})

const emit = defineEmits<{ error: [] }>()

const imageError = ref(false)

// Используем дефолтную аватарку если у пользователя нет фото
const effectiveSrc = computed(() => {
  let url = props.src || props.user?.avatar_url || props.user?.avatar || null
  
  // Если URL есть и не пустой - используем getMediaUrl для полного URL
  if (url && url !== '' && url !== 'null' && url !== 'undefined') {
    return getMediaUrl(url) || url
  }
  
  // Если нет аватарки - возвращаем дефолтную на основе user.id
  if (props.user?.id) {
    return getDefaultAvatarForUser(Number(props.user.id))
  }
  
  return null
})

const avatarClasses = computed(() => {
  return [
    `user-avatar--${props.size}`,
    `user-avatar--${props.shape}`,
  ]
})

const avatarStyles = computed(() => {
  return {}
})

const isPremium = computed(() => props.user?.is_premium ?? false)

const crownSize = computed(() => {
  switch (props.size) {
    case 'xs': return 8
    case 'sm': return 10
    case 'md': return 12
    case 'lg': return 14
    case 'xl': return 16
    case '2xl': return 20
    default: return 12
  }
})

const handleImageError = () => {
  imageError.value = true
  emit('error')
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
  overflow: hidden;
  flex-shrink: 0;
}

/* Размеры */
.user-avatar--xs {
  width: 24px;
  height: 24px;
}

.user-avatar--sm {
  width: 32px;
  height: 32px;
}

.user-avatar--md {
  width: 40px;
  height: 40px;
}

.user-avatar--lg {
  width: 48px;
  height: 48px;
}

.user-avatar--xl {
  width: 64px;
  height: 64px;
}

.user-avatar--2xl {
  width: 120px;
  height: 120px;
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
  bottom: 0;
  right: 0;
  background-color: var(--color-accent-teal);
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

/* Корона премиум */
.premium-crown-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  z-index: 3;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  padding: 1px;
}
</style>

