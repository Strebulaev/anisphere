<template>
  <div
    v-if="visible"
    class="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-48"
    :style="{ left: x + 'px', top: y + 'px' }"
    @click.stop
  >
    <div
      v-for="item in items"
      :key="item.id"
      @click="handleItemClick(item)"
      class="flex items-center px-3 py-2 text-sm hover:bg-gray-100 cursor-pointer"
      :class="{ 'border-t border-gray-200': item.type === 'divider', 'text-red-600': item.danger }"
    >
      <component
        :is="getIconComponent(item.icon)"
        v-if="item.icon && item.type !== 'divider'"
        class="w-4 h-4 mr-3"
      />
      <span>{{ item.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  StarIcon,
  ArchiveBoxIcon,
  SpeakerXMarkIcon,
  CheckIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'

interface MenuItem {
  id: string
  label: string
  icon?: string
  action?: string
  type?: 'divider'
  danger?: boolean
}

interface Props {
  visible: boolean
  x: number
  y: number
  items: MenuItem[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  action: [action: string]
}>()

const getIconComponent = (iconName?: string) => {
  const icons: Record<string, any> = {
    pin: StarIcon,
    archive: ArchiveBoxIcon,
    'bell-slash': SpeakerXMarkIcon,
    check: CheckIcon,
    trash: TrashIcon
  }
  return icons[iconName || ''] || null
}

const handleItemClick = (item: MenuItem) => {
  if (item.type === 'divider') return

  emit('action', item.action || item.id)
  emit('close')
}

// Close menu when clicking outside (handled by parent)
</script>