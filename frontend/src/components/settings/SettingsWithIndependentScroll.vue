<template>
  <div class="settings-with-scroll">
    <div class="settings-container">
      <!-- Левая колонка - навигация -->
      <div class="settings-sidebar" ref="sidebarRef">
        <div class="sidebar-content">
          <h2>Настройки</h2>

          <nav class="settings-nav">
            <button
              v-for="section in sections"
              :key="section.id"
              @click="activeSection = section.id"
              :class="['nav-item', { active: activeSection === section.id }]"
            >
              <component :is="section.icon" class="w-5 h-5" />
              <span>{{ section.name }}</span>
            </button>
          </nav>
        </div>
      </div>

      <!-- Правая колонка - содержимое -->
      <div class="settings-content" ref="contentRef">
        <div class="content-wrapper">
          <component
            :is="currentSectionComponent"
            @save="handleSave"
            @cancel="handleCancel"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import {
  UserIcon,
  BellIcon,
  PaintBrushIcon,
  DatabaseIcon,
  GlobeAltIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'
import AccountSettings from './AccountSettings.vue'
import NotificationSettings from './NotificationSettings.vue'
import AppearanceSettings from './AppearanceSettings.vue'
import DataSettings from './DataSettings.vue'
import AdditionalSettings from './AdditionalSettings.vue'
import AboutSettings from './AboutSettings.vue'

const sections = [
  { id: 'account', name: 'Учётная запись', icon: UserIcon },
  { id: 'notifications', name: 'Уведомления', icon: BellIcon },
  { id: 'appearance', name: 'Внешний вид', icon: PaintBrushIcon },
  { id: 'data', name: 'Данные', icon: DatabaseIcon },
  { id: 'additional', name: 'Дополнительно', icon: GlobeAltIcon },
  { id: 'about', name: 'О программе', icon: InformationCircleIcon },
]

const activeSection = ref('account')
const sidebarRef = ref(null)
const contentRef = ref(null)

const currentSectionComponent = computed(() => {
  const components = {
    account: AccountSettings,
    notifications: NotificationSettings,
    appearance: AppearanceSettings,
    data: DataSettings,
    additional: AdditionalSettings,
    about: AboutSettings,
  }
  return components[activeSection.value] || AccountSettings
})

// При смене раздела прокручиваем содержимое к началу
watch(activeSection, async () => {
  await nextTick()
  if (contentRef.value) {
    contentRef.value.scrollTop = 0
  }
})

const handleSave = () => {
  // Обработка сохранения настроек
}

const handleCancel = () => {
  // Обработка отмены изменений
}
</script>

<style scoped>
.settings-with-scroll {
  height: 100vh;
  overflow: hidden;
}

.settings-container {
  display: flex;
  height: 100%;
}

.settings-sidebar {
  width: 280px;
  background: #f9f9f9;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-content {
  padding: 20px;
}

.sidebar-content h2 {
  margin: 0 0 24px;
  font-size: 20px;
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  color: #666;
  transition: all 0.3s;
  width: 100%;
}

.nav-item:hover {
  background: #f0f0f0;
}

.nav-item.active {
  background: #667eea;
  color: white;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  background: white;
}

.content-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px;
}

/* Кастомный скроллбар для обеих колонок */
.settings-sidebar::-webkit-scrollbar,
.settings-content::-webkit-scrollbar {
  width: 8px;
}

.settings-sidebar::-webkit-scrollbar-track,
.settings-content::-webkit-scrollbar-track {
  background: transparent;
}

.settings-sidebar::-webkit-scrollbar-thumb,
.settings-content::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 4px;
}

.settings-sidebar::-webkit-scrollbar-thumb:hover,
.settings-content::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}

/* Адаптив для мобильных устройств */
@media (max-width: 768px) {
  .settings-container {
    flex-direction: column;
  }

  .settings-sidebar {
    width: 100%;
    height: auto;
    max-height: 200px;
  }

  .sidebar-content {
    padding: 12px;
  }

  .settings-nav {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 8px;
  }

  .nav-item {
    white-space: nowrap;
    flex-shrink: 0;
  }

  .content-wrapper {
    padding: 16px;
  }
}
</style>
