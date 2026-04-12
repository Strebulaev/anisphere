<template>
  <div 
    class="avatar"
    :class="[
      `avatar-${size}`,
      { 'avatar-with-border': withBorder }
    ]"
    :style="avatarStyle"
    @click="handleClick"
  >
    <img 
      v-if="imageUrl" 
      :src="imageUrl" 
      :alt="alt || props.user?.username || 'Avatar'"
      class="avatar-image"
      @error="handleError"
    />
    <div v-else class="avatar-placeholder">
      <span class="avatar-text">{{ avatarText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  user?: {
    id?: number | string
    username?: string
    avatar_url?: string | null
    avatar?: string | null
    display_name?: string
  }
  src?: string
  alt?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  withBorder?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  withBorder: false
})

const emit = defineEmits<{
  (e: 'click', user?: any): void
  (e: 'error'): void
}>()

const imageUrl = ref(props.src || props.user?.avatar_url || props.user?.avatar || null)
const hasError = ref(false)

const avatarText = computed(() => {
  if (props.user?.display_name) {
    return props.user.display_name.charAt(0).toUpperCase()
  }
  if (props.user?.username) {
    return props.user.username.charAt(0).toUpperCase()
  }
  if (props.placeholder) {
    return props.placeholder.charAt(0).toUpperCase()
  }
  return '?'
})

const avatarStyle = computed(() => {
  if (!imageUrl.value && !hasError.value) {
    // Генерируем цвет на основе username
    const seed = (props.user?.username || props.user?.id?.toString() || 'default')
    const color = generateColor(seed)
    return {
      backgroundColor: color
    }
  }
  return {}
})

const generateColor = (str: string): string => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  const hue = hash % 360
  return `hsl(${hue}, 70%, 50%)`
}

const handleError = () => {
  hasError.value = true
  imageUrl.value = null
  emit('error')
}

const handleClick = () => {
  emit('click', props.user)
}
</script>

<style scoped>
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  background: var(--surface-4);
  flex-shrink: 0;
  position: relative;
}

.avatar-with-border {
  border: 2px solid var(--accent);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
}

.avatar-text {
  font-size: 1.2em;
  text-transform: uppercase;
}

/* Sizes */
.avatar-xs {
  width: 20px;
  height: 20px;
  font-size: 10px;
}

.avatar-sm {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.avatar-md {
  width: 40px;
  height: 40px;
  font-size: 18px;
}

.avatar-lg {
  width: 56px;
  height: 56px;
  font-size: 24px;
}

.avatar-xl {
  width: 80px;
  height: 80px;
  font-size: 32px;
}

.avatar-with-border {
  border: 2px solid var(--accent);
}
</style>
