<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="chat-settings-modal">
        <!-- Sidebar -->
        <div class="settings-sidebar">
          <div class="sidebar-header">
            <h3>Настройки чата</h3>
            <button @click="$emit('close')" class="close-btn">
              <XMarkIcon class="w-5 h-5" />
            </button>
          </div>

          <nav class="sidebar-nav">
            <button
              v-for="section in sections"
              :key="section.id"
              @click="activeSection = section.id"
              class="nav-item"
              :class="{ active: activeSection === section.id }"
            >
              <component :is="section.icon" class="w-5 h-5" />
              <span>{{ section.name }}</span>
            </button>
          </nav>
        </div>

        <!-- Content -->
        <div class="settings-content">
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <span>Загрузка...</span>
          </div>

          <!-- Обои -->
          <div v-else-if="activeSection === 'wallpaper'" class="section">
            <h2 class="section-title">Обои чата</h2>

            <div class="wallpaper-grid">
              <div
                v-for="preset in wallpaperPresets"
                :key="preset.id"
                @click="selectWallpaper(preset)"
                class="wallpaper-item"
                :class="{ active: currentWallpaperId === preset.id }"
                :style="getWallpaperStyle(preset)"
              >
                <div v-if="preset.preset_name" class="preset-label">
                  {{ preset.preset_name }}
                </div>
                <CheckIcon v-if="currentWallpaperId === preset.id" class="w-6 h-6 check-icon" />
              </div>
            </div>

            <div class="custom-wallpaper">
              <h4>Свои обои</h4>

              <div class="wallpaper-type-select">
                <button
                  v-for="type in wallpaperTypes"
                  :key="type.value"
                  @click="customWallpaper.wallpaper_type = type.value as 'solid' | 'gradient' | 'image'"
                  :class="{ active: customWallpaper.wallpaper_type === type.value }"
                >
                  {{ type.label }}
                </button>
              </div>

              <div v-if="customWallpaper.wallpaper_type === 'solid'" class="color-picker">
                <label>Цвет</label>
                <input type="color" v-model="customWallpaper.wallpaper_color" />
              </div>

              <div v-else-if="customWallpaper.wallpaper_type === 'gradient'" class="gradient-picker">
                <div class="color-picker">
                  <label>Цвет 1</label>
                  <input type="color" v-model="customWallpaper.wallpaper_color" />
                </div>
                <div class="color-picker">
                  <label>Цвет 2</label>
                  <input type="color" v-model="customWallpaper.wallpaper_color2" />
                </div>
              </div>

              <div v-else-if="customWallpaper.wallpaper_type === 'image'" class="image-upload">
                <input
                  type="file"
                  ref="wallpaperInput"
                  @change="handleWallpaperUpload"
                  accept="image/*"
                  hidden
                />
                <button @click="wallpaperInput?.click()" class="upload-btn">
                  <PhotoIcon class="w-5 h-5" />
                  Загрузить изображение
                </button>
                <div v-if="wallpaperPreview" class="preview">
                  <img :src="wallpaperPreview" alt="Preview" />
                </div>
              </div>

              <div class="wallpaper-settings">
                <div class="slider-setting">
                  <label>Интенсивность: {{ customWallpaper.wallpaper_intensity }}%</label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    v-model.number="customWallpaper.wallpaper_intensity"
                  />
                </div>
                <div class="slider-setting">
                  <label>Размытие: {{ customWallpaper.wallpaper_blur }}px</label>
                  <input
                    type="range"
                    min="0"
                    max="20"
                    v-model.number="customWallpaper.wallpaper_blur"
                  />
                </div>
              </div>

              <button @click="applyCustomWallpaper" class="apply-btn" :disabled="saving">
                {{ saving ? 'Сохранение...' : 'Применить' }}
              </button>
            </div>
          </div>

          <!-- Тема -->
          <div v-else-if="activeSection === 'theme'" class="section">
            <h2 class="section-title">Тема оформления</h2>

            <div class="theme-options">
              <div class="option-group">
                <label>Тема</label>
                <div class="theme-select">
                  <button
                    v-for="theme in themes"
                    :key="theme.value"
                    @click="currentTheme.theme = theme.value"
                    :class="{ active: currentTheme.theme === theme.value }"
                  >
                    {{ theme.label }}
                  </button>
                </div>
              </div>

              <div class="option-group">
                <label>Цвет сообщений</label>
                <div class="color-options">
                  <div class="color-picker">
                    <span>Ваши сообщения</span>
                    <input type="color" v-model="currentTheme.message_color" />
                  </div>
                  <div class="color-picker">
                    <span>Чужие сообщения</span>
                    <input type="color" v-model="currentTheme.message_color_other" />
                  </div>
                </div>
              </div>

              <div class="option-group">
                <label>Стиль пузырей</label>
                <div class="bubble-styles">
                  <button
                    v-for="style in bubbleStyles"
                    :key="style.value"
                    @click="currentTheme.bubble_style = style.value"
                    :class="{ active: currentTheme.bubble_style === style.value }"
                  >
                    {{ style.label }}
                  </button>
                </div>
              </div>

              <div class="option-group">
                <label>Размер шрифта</label>
                <div class="font-sizes">
                  <button
                    v-for="size in fontSizes"
                    :key="size.value"
                    @click="currentTheme.font_size = size.value"
                    :class="{ active: currentTheme.font_size === size.value }"
                  >
                    {{ size.label }}
                  </button>
                </div>
              </div>

              <div class="option-group">
                <label>Формат времени</label>
                <div class="time-formats">
                  <button
                    v-for="format in timeFormats"
                    :key="format.value"
                    @click="currentTheme.time_format = format.value"
                    :class="{ active: currentTheme.time_format === format.value }"
                  >
                    {{ format.label }}
                  </button>
                </div>
              </div>

              <div class="option-group">
                <label>Анимации</label>
                <div class="animation-settings">
                  <ToggleSwitch 
                    v-model="enableMessageAnimation" 
                    label="Анимация сообщений" 
                  />
                  <ToggleSwitch 
                    v-model="enableReactionAnimation" 
                    label="Анимация реакций" 
                  />
                </div>
              </div>

              <div class="option-group">
                <label>Набор эмодзи</label>
                <div class="emoji-sets">
                  <button
                    v-for="set in emojiSets"
                    :key="set.value"
                    @click="currentTheme.emoji_set = set.value"
                    :class="{ active: currentTheme.emoji_set === set.value }"
                  >
                    {{ set.label }}
                  </button>
                </div>
              </div>
            </div>

            <button @click="saveTheme" class="save-btn" :disabled="saving">
              {{ saving ? 'Сохранение...' : 'Сохранить тему' }}
            </button>
          </div>

          <!-- Уведомления -->
          <div v-else-if="activeSection === 'notifications'" class="section">
            <h2 class="section-title">Уведомления</h2>

            <div class="notification-settings">
              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-name">Уведомления</span>
                  <span class="setting-desc">Получать уведомления о новых сообщениях</span>
                </div>
                <ToggleSwitch v-model="notifications.enabled" />
              </div>

              <div v-if="notifications.enabled" class="setting-item">
                <div class="setting-info">
                  <span class="setting-name">Звук</span>
                  <span class="setting-desc">Звуковое оповещение</span>
                </div>
                <ToggleSwitch v-model="notifications.sound" />
              </div>

              <div v-if="notifications.enabled" class="setting-item">
                <div class="setting-info">
                  <span class="setting-name">Превью сообщений</span>
                  <span class="setting-desc">Показывать текст сообщения в уведомлении</span>
                </div>
                <ToggleSwitch v-model="notifications.preview" />
              </div>

              <div v-if="notifications.enabled" class="setting-item">
                <div class="setting-info">
                  <span class="setting-name">Только упоминания</span>
                  <span class="setting-desc">Уведомлять только при упоминании @username</span>
                </div>
                <ToggleSwitch v-model="notifications.mentionsOnly" />
              </div>

              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-name">Отключить до</span>
                  <span class="setting-desc">Временно отключить уведомления</span>
                </div>
                <select v-model="notifications.muteDuration" class="mute-select">
                  <option value="">Не отключать</option>
                  <option value="1h">На 1 час</option>
                  <option value="8h">На 8 часов</option>
                  <option value="1d">На 1 день</option>
                  <option value="1w">На 1 неделю</option>
                  <option value="always">Навсегда</option>
                </select>
              </div>
            </div>

            <button @click="saveNotifications" class="save-btn" :disabled="saving">
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>

          <!-- Теги -->
          <div v-else-if="activeSection === 'tags'" class="section">
            <h2 class="section-title">Теги чата</h2>

            <div class="current-tags">
              <div
                v-for="tag in chatTags"
                :key="tag.id"
                class="tag-chip"
                :style="{ backgroundColor: tag.color + '20', borderColor: tag.color }"
              >
                <span v-if="tag.emoji">{{ tag.emoji }}</span>
                <span>{{ tag.name }}</span>
                <button @click="removeTag(tag)" class="remove-tag">
                  <XMarkIcon class="w-4 h-4" />
                </button>
              </div>
              <div v-if="chatTags.length === 0" class="empty-tags">
                Нет тегов
              </div>
            </div>

            <div class="add-tag">
              <h4>Создать новый тег</h4>
              <div class="tag-form">
                <input
                  v-model="newTag.name"
                  type="text"
                  placeholder="Название тега"
                  class="tag-input"
                />
                <div class="tag-colors">
                  <button
                    v-for="color in tagColors"
                    :key="color"
                    @click="newTag.color = color"
                    class="color-btn"
                    :style="{ backgroundColor: color }"
                    :class="{ active: newTag.color === color }"
                  />
                </div>
                <input
                  v-model="newTag.emoji"
                  type="text"
                  placeholder="Эмодзи"
                  class="emoji-input"
                />
                <button @click="createTag" class="create-tag-btn" :disabled="saving || !newTag.name.trim()">
                  Создать
                </button>
              </div>
            </div>

            <div class="your-tags">
              <h4>Ваши теги (нажмите, чтобы добавить к чату)</h4>
              <div v-if="userTags.length === 0" class="empty-tags">
                У вас пока нет тегов
              </div>
              <div v-else class="tags-list">
                <div
                  v-for="tag in userTags"
                  :key="tag.id"
                  @click="assignTag(tag)"
                  class="tag-item"
                  :style="{ borderColor: tag.color }"
                >
                  <span v-if="tag.emoji">{{ tag.emoji }}</span>
                  <span>{{ tag.name }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Медленный режим -->
          <div v-else-if="activeSection === 'slowmode'" class="section">
            <h2 class="section-title">Медленный режим</h2>

            <div class="slowmode-settings">
              <div class="setting-item">
                <div class="setting-info">
                  <span class="setting-name">Медленный режим</span>
                  <span class="setting-desc">Ограничить частоту отправки сообщений</span>
                </div>
                <ToggleSwitch v-model="slowMode.enabled" />
              </div>

              <div v-if="slowMode.enabled" class="slowmode-config">
                <div class="option-group">
                  <label>Задержка между сообщениями</label>
                  <div class="delay-options">
                    <button
                      v-for="delay in delayOptions"
                      :key="delay.value"
                      @click="slowMode.delay = delay.value"
                      :class="{ active: slowMode.delay === delay.value }"
                    >
                      {{ delay.label }}
                    </button>
                  </div>
                </div>

                <div class="setting-item">
                  <div class="setting-info">
                    <span class="setting-name">Исключить админов</span>
                    <span class="setting-desc">Администраторы могут отправлять сообщения без ограничений</span>
                  </div>
                  <ToggleSwitch v-model="slowMode.exempt_admins" />
                </div>

                <div class="setting-item">
                  <div class="setting-info">
                    <span class="setting-name">Исключить модераторов</span>
                    <span class="setting-desc">Модераторы могут отправлять сообщения без ограничений</span>
                  </div>
                  <ToggleSwitch v-model="slowMode.exempt_moderators" />
                </div>
              </div>
            </div>

            <button @click="saveSlowMode" class="save-btn" :disabled="saving">
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>

          <!-- Анти-спам -->
          <div v-else-if="activeSection === 'antispam'" class="section">
            <h2 class="section-title">Анти-спам</h2>

            <div class="antispam-rules">
              <div
                v-for="rule in antiSpamRules"
                :key="rule.id"
                class="rule-item"
              >
                <div class="rule-header">
                  <div class="rule-info">
                    <span class="rule-name">{{ rule.rule_type_display }}</span>
                    <span class="rule-desc">{{ getRuleDescription(rule) }}</span>
                  </div>
                  <ToggleSwitch v-model="rule.enabled" @change="updateRule(rule)" />
                </div>
                <div class="rule-actions">
                  <button @click="editRule(rule)" class="edit-btn">
                    <PencilIcon class="w-4 h-4" />
                  </button>
                  <button @click="deleteRule(rule)" class="delete-btn">
                    <TrashIcon class="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div v-if="antiSpamRules.length === 0" class="empty-state">
                Нет правил анти-спама
              </div>
            </div>

            <button @click="showCreateRule = true" class="add-rule-btn">
              <PlusIcon class="w-5 h-5" />
              Добавить правило
            </button>
          </div>

          <!-- Запланированные сообщения -->
          <div v-else-if="activeSection === 'scheduled'" class="section">
            <h2 class="section-title">Запланированные сообщения</h2>

            <div class="scheduled-list">
              <div
                v-for="msg in scheduledMessages"
                :key="msg.id"
                class="scheduled-item"
              >
                <div class="scheduled-info">
                  <span class="scheduled-text">{{ msg.text?.substring(0, 50) ?? '' }}{{ (msg.text?.length ?? 0) > 50 ? '...' : '' }}</span>
                  <span class="scheduled-time">
                    {{ formatScheduledTime(msg.scheduled_at) }}
                  </span>
                </div>
                <div class="scheduled-actions">
                  <button @click="sendScheduledNow(msg)" class="send-btn">
                    Отправить
                  </button>
                  <button @click="cancelScheduled(msg)" class="cancel-btn">
                    Отменить
                  </button>
                </div>
              </div>

              <div v-if="scheduledMessages.length === 0" class="empty-state">
                Нет запланированных сообщений
              </div>
            </div>

            <button @click="showScheduleMessage = true" class="add-scheduled-btn">
              <PlusIcon class="w-5 h-5" />
              Запланировать сообщение
            </button>
          </div>

          <!-- Резервные копии -->
          <div v-else-if="activeSection === 'backups'" class="section">
            <h2 class="section-title">Резервные копии</h2>

            <div class="backups-list">
              <div
                v-for="backup in backups"
                :key="backup.id"
                class="backup-item"
              >
                <div class="backup-info">
                  <span class="backup-date">{{ formatDate(backup.created_at) }}</span>
                  <span class="backup-stats">
                    {{ backup.messages_count }} сообщений • {{ backup.file_size_mb }} MB
                  </span>
                </div>
                <div class="backup-actions">
                  <button @click="downloadBackup(backup)" class="download-btn">
                    <ArrowDownTrayIcon class="w-4 h-4" />
                  </button>
                  <button @click="restoreBackup(backup)" class="restore-btn">
                    Восстановить
                  </button>
                </div>
              </div>

              <div v-if="backups.length === 0" class="empty-state">
                Нет резервных копий
              </div>
            </div>

            <button @click="createBackup" class="create-backup-btn" :disabled="creatingBackup">
              <ArrowPathIcon class="w-5 h-5" />
              {{ creatingBackup ? 'Создание...' : 'Создать резервную копию' }}
            </button>
          </div>

          <!-- Danger Zone -->
          <div v-else-if="activeSection === 'danger'" class="section danger-zone">
            <h2 class="section-title text-red-500">Опасная зона</h2>

            <div class="danger-actions">
              <div class="danger-item">
                <div class="danger-info">
                  <span class="danger-name">Очистить историю</span>
                  <span class="danger-desc">Удалить все сообщения в чате</span>
                </div>
                <button @click="clearHistory" class="danger-btn">
                  Очистить
                </button>
              </div>

              <div class="danger-item">
                <div class="danger-info">
                  <span class="danger-name">Покинуть чат</span>
                  <span class="danger-desc">Вы покинете этот чат</span>
                </div>
                <button @click="leaveChat" class="danger-btn">
                  Покинуть
                </button>
              </div>

              <div v-if="isOwner" class="danger-item">
                <div class="danger-info">
                  <span class="danger-name">Удалить чат</span>
                  <span class="danger-desc">Это действие необратимо</span>
                </div>
                <button @click="deleteChat" class="danger-btn critical">
                  Удалить чат
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Toast -->
        <Transition name="toast">
          <div v-if="toast.show" class="toast" :class="toast.type">
            {{ toast.message }}
          </div>
        </Transition>

        <!-- Modals -->
        <AntiSpamRuleModal
          v-if="showCreateRule || editingRule"
          :rule="editingRule"
          :chat-id="chatId"
          @close="closeRuleModal"
          @save="handleRuleSave"
        />

        <ScheduleMessageModal
          v-if="showScheduleMessage"
          :chat-id="chatId"
          :chat-type="chatType"
          @close="showScheduleMessage = false"
          @scheduled="handleScheduled"
        />
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  XMarkIcon,
  PhotoIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  ArrowDownTrayIcon,
  ArrowPathIcon,
  BellIcon,
  PaintBrushIcon,
  TagIcon,
  ClockIcon,
  ShieldCheckIcon,
  CalendarIcon,
  ArchiveBoxIcon,
  ExclamationTriangleIcon,
  CheckIcon
} from '@heroicons/vue/24/outline'
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue'
import AntiSpamRuleModal from './AntiSpamRuleModal.vue'
import ScheduleMessageModal from './ScheduleMessageModal.vue'
import apiClient from '@/api/client'

interface Props {
  chatId: number
  chatType: 'group' | 'private'
  isOwner?: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'settings-changed'])

// State
const activeSection = ref('wallpaper')
const loading = ref(true)
const saving = ref(false)
const wallpaperInput = ref<HTMLInputElement | null>(null)

const toast = ref({
  show: false,
  message: '',
  type: 'success' as 'success' | 'error'
})

// Sections
const sections = [
  { id: 'wallpaper', name: 'Обои', icon: PaintBrushIcon },
  { id: 'theme', name: 'Тема', icon: PaintBrushIcon },
  { id: 'notifications', name: 'Уведомления', icon: BellIcon },
  { id: 'tags', name: 'Теги', icon: TagIcon },
  { id: 'slowmode', name: 'Медленный режим', icon: ClockIcon },
  { id: 'antispam', name: 'Анти-спам', icon: ShieldCheckIcon },
  { id: 'scheduled', name: 'Запланированные', icon: CalendarIcon },
  { id: 'backups', name: 'Резервные копии', icon: ArchiveBoxIcon },
  { id: 'danger', name: 'Опасная зона', icon: ExclamationTriangleIcon }
]

// Types
interface ChatWallpaper {
  id: number
  wallpaper_type: 'solid' | 'gradient' | 'pattern' | 'image'
  wallpaper_color: string
  wallpaper_color2?: string
  wallpaper_intensity: number
  wallpaper_blur: number
  wallpaper_motion: string
  wallpaper_image?: string
  wallpaper_image_url?: string
  is_preset: boolean
  preset_name?: string
  created_at: string
}

interface ChatTheme {
  id?: number
  theme: string
  message_color: string
  message_color_other: string
  bubble_style: string
  font_size: string
  time_format: string
  message_animation: string
  reaction_animation: string
  emoji_set: string
  emoji_size: string
  chat?: number
  private_chat?: number
}

interface ChatTag {
  id: number
  name: string
  color: string
  emoji?: string
}

interface AntiSpamRule {
  id: number
  chat: number
  rule_type: string
  rule_type_display: string
  threshold: number
  time_window: number
  action: string
  action_display: string
  enabled: boolean
  created_at: string
  updated_at: string
}

interface ChatBackup {
  id: number
  messages_count: number
  file_size_mb: number
  created_at: string
}

interface ScheduledMessage {
  id: number
  text?: string
  scheduled_at: string
  status: string
}

// Wallpaper
const wallpaperPresets = ref<ChatWallpaper[]>([])
const currentWallpaperId = ref<number | null>(null)
const wallpaperPreview = ref<string | null>(null)

const customWallpaper = ref({
  wallpaper_type: 'solid' as 'solid' | 'gradient' | 'image',
  wallpaper_color: '#1a1a1a',
  wallpaper_color2: '#2d2d2d',
  wallpaper_intensity: 100,
  wallpaper_blur: 0,
  wallpaper_motion: 'none'
})

const wallpaperTypes = [
  { value: 'solid', label: 'Заливка' },
  { value: 'gradient', label: 'Градиент' },
  { value: 'image', label: 'Изображение' }
]

// Theme
const currentTheme = ref<Partial<ChatTheme>>({
  theme: 'default',
  message_color: '#3b82f6',
  message_color_other: '#2a2a2a',
  bubble_style: 'modern',
  font_size: 'medium',
  time_format: '24h',
  message_animation: 'slide',
  reaction_animation: 'bounce',
  emoji_set: 'default',
  emoji_size: 'medium'
})

const themes = [
  { value: 'default', label: 'По умолчанию' },
  { value: 'dark', label: 'Тёмная' },
  { value: 'light', label: 'Светлая' },
  { value: 'anime', label: 'Аниме' }
]

const bubbleStyles = [
  { value: 'modern', label: 'Современный' },
  { value: 'classic', label: 'Классический' },
  { value: 'rounded', label: 'Округлый' }
]

const fontSizes = [
  { value: 'small', label: 'Мелкий' },
  { value: 'medium', label: 'Средний' },
  { value: 'large', label: 'Крупный' }
]

const timeFormats = [
  { value: '12h', label: '12-часовой' },
  { value: '24h', label: '24-часовой' }
]

const emojiSets = [
  { value: 'default', label: 'Стандартные' },
  { value: 'twitter', label: 'Twitter' },
  { value: 'google', label: 'Google' },
  { value: 'anime', label: 'Аниме' }
]

const enableMessageAnimation = ref(true)
const enableReactionAnimation = ref(true)

// Notifications
const notifications = ref({
  enabled: true,
  sound: true,
  preview: true,
  mentionsOnly: false,
  muteDuration: ''
})

// Tags
const chatTags = ref<ChatTag[]>([])
const userTags = ref<ChatTag[]>([])
const newTag = ref({
  name: '',
  color: '#3b82f6',
  emoji: ''
})

const tagColors = [
  '#ef4444', '#f97316', '#eab308', '#22c55e',
  '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280'
]

// Slow Mode
const slowMode = ref({
  id: null as number | null,
  enabled: false,
  delay: 30,
  exempt_admins: true,
  exempt_moderators: true
})

const delayOptions = [
  { value: 10, label: '10 сек' },
  { value: 30, label: '30 сек' },
  { value: 60, label: '1 мин' },
  { value: 300, label: '5 мин' },
  { value: 600, label: '10 мин' }
]

// Anti-spam
const antiSpamRules = ref<AntiSpamRule[]>([])
const showCreateRule = ref(false)
const editingRule = ref<AntiSpamRule | null>(null)

// Scheduled messages
const scheduledMessages = ref<ScheduledMessage[]>([])
const showScheduleMessage = ref(false)

// Backups
const backups = ref<ChatBackup[]>([])
const creatingBackup = ref(false)

// Methods
const showToast = (message: string, type: 'success' | 'error' = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const getWallpaperStyle = (preset: ChatWallpaper) => {
  if (preset.wallpaper_type === 'solid') {
    return { backgroundColor: preset.wallpaper_color }
  } else if (preset.wallpaper_type === 'gradient') {
    return {
      background: `linear-gradient(135deg, ${preset.wallpaper_color}, ${preset.wallpaper_color2 || '#2d2d2d'})`
    }
  }
  return {}
}

// ==================== WALLPAPER ====================

const selectWallpaper = async (preset: ChatWallpaper) => {
  saving.value = true
  try {
    const response = await apiClient.put(`/social/chats/${props.chatId}/wallpaper/`, {
      wallpaper_type: preset.wallpaper_type,
      wallpaper_color: preset.wallpaper_color,
      wallpaper_color2: preset.wallpaper_color2,
      wallpaper_intensity: preset.wallpaper_intensity,
      wallpaper_blur: preset.wallpaper_blur,
      type: props.chatType
    })
    currentWallpaperId.value = response.data?.id || preset.id
    showToast('Обои применены')
    emit('settings-changed', { 
      type: 'wallpaper', 
      wallpaper: response.data || preset 
    })
  } catch (error: any) {
    console.error('Error applying wallpaper:', error)
    showToast(error.response?.data?.error || 'Ошибка применения обоев', 'error')
  } finally {
    saving.value = false
  }
}

const handleWallpaperUpload = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      wallpaperPreview.value = e.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

const applyCustomWallpaper = async () => {
  saving.value = true
  try {
    const response = await apiClient.put(`/social/chats/${props.chatId}/wallpaper/`, {
      ...customWallpaper.value,
      type: props.chatType
    })
    currentWallpaperId.value = response.data?.id || null
    showToast('Обои применены')
    emit('settings-changed', { 
      type: 'wallpaper', 
      wallpaper: response.data 
    })
  } catch (error: any) {
    console.error('Error applying wallpaper:', error)
    showToast(error.response?.data?.error || 'Ошибка применения обоев', 'error')
  } finally {
    saving.value = false
  }
}

// ==================== THEME ====================

const saveTheme = async () => {
  saving.value = true
  try {
    const data: any = {
      ...currentTheme.value,
      message_animation: enableMessageAnimation.value ? 'slide' : 'none',
      reaction_animation: enableReactionAnimation.value ? 'bounce' : 'none'
    }
    
    if (props.chatType === 'group') {
      data.chat = props.chatId
    } else {
      data.private_chat = props.chatId
    }
    
    // Проверяем, есть ли уже тема для этого чата
    if (currentTheme.value?.id) {
      await apiClient.patch(`/social/chat-themes/${currentTheme.value.id}/`, data)
    } else {
      const response = await apiClient.post('/social/chat-themes/', data)
      currentTheme.value = response.data
    }
    
    showToast('Тема сохранена')
    emit('settings-changed', { type: 'theme' })
  } catch (error: any) {
    console.error('Error saving theme:', error)
    showToast(error.response?.data?.error || 'Ошибка сохранения темы', 'error')
  } finally {
    saving.value = false
  }
}

// ==================== NOTIFICATIONS ====================

const saveNotifications = async () => {
  saving.value = true
  try {
    if (props.chatType === 'private') {
      const data: any = {
        user1_notifications: notifications.value.enabled
      }
      
      if (notifications.value.muteDuration) {
        const now = new Date()
        let muteUntil: Date | null = null
        
        switch (notifications.value.muteDuration) {
          case '1h':
            muteUntil = new Date(now.getTime() + 60 * 60 * 1000)
            break
          case '8h':
            muteUntil = new Date(now.getTime() + 8 * 60 * 60 * 1000)
            break
          case '1d':
            muteUntil = new Date(now.getTime() + 24 * 60 * 60 * 1000)
            break
          case '1w':
            muteUntil = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
            break
          case 'always':
            muteUntil = new Date('2099-12-31')
            break
        }
        
        if (muteUntil) {
          data.user1_muted_until = muteUntil.toISOString()
        }
      }
      
      await apiClient.patch(`/social/private-chats/${props.chatId}/`, data)
    }
    
    showToast('Настройки уведомлений сохранены')
    emit('settings-changed', { type: 'notifications' })
  } catch (error: any) {
    console.error('Error saving notifications:', error)
    showToast(error.response?.data?.error || 'Ошибка сохранения', 'error')
  } finally {
    saving.value = false
  }
}

// ==================== TAGS ====================

const createTag = async () => {
  if (!newTag.value.name.trim()) return
  
  saving.value = true
  try {
    const response = await apiClient.post('/social/chat-tags/', newTag.value)
    userTags.value.push(response.data)
    newTag.value = { name: '', color: '#3b82f6', emoji: '' }
    showToast('Тег создан')
  } catch (error: any) {
    console.error('Error creating tag:', error)
    showToast(error.response?.data?.error || 'Ошибка создания тега', 'error')
  } finally {
    saving.value = false
  }
}

const assignTag = async (tag: ChatTag) => {
  saving.value = true
  try {
    await apiClient.post('/social/chat-tag-assignments/', {
      tag: tag.id,
      group_chat: props.chatType === 'group' ? props.chatId : null,
      private_chat: props.chatType === 'private' ? props.chatId : null
    })
    chatTags.value.push(tag)
    showToast('Тег добавлен к чату')
  } catch (error: any) {
    console.error('Error assigning tag:', error)
    showToast(error.response?.data?.error || 'Ошибка добавления тега', 'error')
  } finally {
    saving.value = false
  }
}

const removeTag = async (tag: ChatTag) => {
  try {
    const response = await apiClient.get('/social/chat-tag-assignments/', {
      params: {
        tag: tag.id,
        group_chat: props.chatType === 'group' ? props.chatId : undefined,
        private_chat: props.chatType === 'private' ? props.chatId : undefined
      }
    })
    
    const data = response.data as any
    const assignments = Array.isArray(data) ? data : (data?.results || [])
    
    if (assignments.length > 0) {
      await apiClient.delete(`/social/chat-tag-assignments/${assignments[0].id}/`)
      chatTags.value = chatTags.value.filter(t => t.id !== tag.id)
      showToast('Тег удалён')
    }
  } catch (error: any) {
    console.error('Error removing tag:', error)
    showToast(error.response?.data?.error || 'Ошибка удаления тега', 'error')
  }
}

// ==================== SLOW MODE ====================

const saveSlowMode = async () => {
  saving.value = true
  try {
    if (slowMode.value.id) {
      await apiClient.patch(`/social/chat-slow-modes/${slowMode.value.id}/`, slowMode.value)
    } else {
      const response = await apiClient.post('/social/chat-slow-modes/', {
        chat: props.chatId,
        ...slowMode.value
      })
      slowMode.value.id = response.data.id
    }
    showToast('Настройки медленного режима сохранены')
    emit('settings-changed', { type: 'slowmode' })
  } catch (error: any) {
    console.error('Error saving slow mode:', error)
    showToast(error.response?.data?.error || 'Ошибка сохранения', 'error')
  } finally {
    saving.value = false
  }
}

// ==================== ANTI-SPAM ====================

const getRuleDescription = (rule: AntiSpamRule) => {
  const descriptions: Record<string, string> = {
    'flood': `${rule.threshold} сообщений за ${rule.time_window} сек`,
    'spam': `${rule.threshold} одинаковых сообщений`,
    'links': `${rule.threshold} ссылок за ${rule.time_window} сек`,
    'mentions': `${rule.threshold} упоминаний за ${rule.time_window} сек`,
    'caps': `${rule.threshold}% заглавных букв`
  }
  return descriptions[rule.rule_type] || ''
}

const updateRule = async (rule: AntiSpamRule) => {
  try {
    await apiClient.patch(`/social/anti-spam-rules/${rule.id}/`, {
      enabled: rule.enabled
    })
    showToast(rule.enabled ? 'Правило включено' : 'Правило отключено')
  } catch (error: any) {
    console.error('Error updating rule:', error)
    showToast(error.response?.data?.error || 'Ошибка обновления', 'error')
  }
}

const editRule = (rule: AntiSpamRule) => {
  editingRule.value = rule
}

const deleteRule = async (rule: AntiSpamRule) => {
  if (!confirm('Удалить правило?')) return
  
  try {
    await apiClient.delete(`/social/anti-spam-rules/${rule.id}/`)
    antiSpamRules.value = antiSpamRules.value.filter(r => r.id !== rule.id)
    showToast('Правило удалено')
  } catch (error: any) {
    console.error('Error deleting rule:', error)
    showToast(error.response?.data?.error || 'Ошибка удаления', 'error')
  }
}

const closeRuleModal = () => {
  showCreateRule.value = false
  editingRule.value = null
}

const handleRuleSave = (rule: AntiSpamRule) => {
  const index = antiSpamRules.value.findIndex(r => r.id === rule.id)
  if (index >= 0) {
    antiSpamRules.value[index] = rule
  } else {
    antiSpamRules.value.push(rule)
  }
  closeRuleModal()
}

// ==================== SCHEDULED MESSAGES ====================

const formatScheduledTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const sendScheduledNow = async (msg: ScheduledMessage) => {
  try {
    await apiClient.post(`/social/scheduled-messages/${msg.id}/send_now/`)
    scheduledMessages.value = scheduledMessages.value.filter(m => m.id !== msg.id)
    showToast('Сообщение отправлено')
  } catch (error: any) {
    console.error('Error sending message:', error)
    showToast(error.response?.data?.error || 'Ошибка отправки', 'error')
  }
}

const cancelScheduled = async (msg: ScheduledMessage) => {
  try {
    await apiClient.post(`/social/scheduled-messages/${msg.id}/cancel/`)
    scheduledMessages.value = scheduledMessages.value.filter(m => m.id !== msg.id)
    showToast('Сообщение отменено')
  } catch (error: any) {
    console.error('Error cancelling message:', error)
    showToast(error.response?.data?.error || 'Ошибка отмены', 'error')
  }
}

const handleScheduled = (msg: ScheduledMessage) => {
  scheduledMessages.value.push(msg)
  showScheduleMessage.value = false
}

// ==================== BACKUPS ====================

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const createBackup = async () => {
  creatingBackup.value = true
  try {
    const response = await apiClient.post('/social/chat-backups/', {
      chat: props.chatId
    })
    backups.value.unshift(response.data)
    showToast('Резервная копия создаётся...')
  } catch (error: any) {
    console.error('Error creating backup:', error)
    showToast(error.response?.data?.error || 'Ошибка создания копии', 'error')
  } finally {
    creatingBackup.value = false
  }
}

const downloadBackup = async (backup: ChatBackup) => {
  try {
    const response = await apiClient.get(`/social/chat-backups/${backup.id}/download/`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `chat_backup_${backup.id}.json`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error: any) {
    console.error('Error downloading backup:', error)
    showToast(error.response?.data?.error || 'Ошибка скачивания', 'error')
  }
}

const restoreBackup = async (backup: ChatBackup) => {
  if (!confirm('Восстановить чат из копии? Текущие сообщения будут заменены.')) return
  
  try {
    await apiClient.post(`/social/chat-backups/${backup.id}/restore/`)
    showToast('Восстановление начато...')
    emit('settings-changed', { type: 'restore' })
  } catch (error: any) {
    console.error('Error restoring backup:', error)
    showToast(error.response?.data?.error || 'Ошибка восстановления', 'error')
  }
}

// ==================== DANGER ZONE ====================

const clearHistory = async () => {
  if (!confirm('Вы уверены, что хотите удалить все сообщения?')) return
  if (!confirm('Это действие необратимо!')) return

  try {
    await apiClient.post(`/social/group-chats/${props.chatId}/clear_history/`)
    showToast('История очищена')
    emit('settings-changed', { type: 'clear' })
  } catch (error: any) {
    console.error('Error clearing history:', error)
    showToast(error.response?.data?.error || 'Ошибка очистки', 'error')
  }
}

const leaveChat = async () => {
  if (!confirm('Вы уверены, что хотите покинуть чат?')) return

  try {
    await apiClient.post(`/social/group-chats/${props.chatId}/leave/`)
    emit('close')
    emit('settings-changed', { type: 'leave' })
  } catch (error: any) {
    console.error('Error leaving chat:', error)
    showToast(error.response?.data?.error || 'Ошибка', 'error')
  }
}

const deleteChat = async () => {
  if (!confirm('Вы уверены, что хотите удалить чат? Это действие необратимо.')) return
  if (!confirm('ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ! Чат будет удалён навсегда.')) return

  try {
    await apiClient.delete(`/social/group-chats/${props.chatId}/`)
    emit('close')
    emit('settings-changed', { type: 'delete' })
  } catch (error: any) {
    console.error('Error deleting chat:', error)
    showToast(error.response?.data?.error || 'Ошибка удаления', 'error')
  }
}

// ==================== LOAD DATA ====================

const loadSettings = async () => {
  loading.value = true
  try {
    // Load wallpaper presets
    const presetsRes = await apiClient.get('/social/wallpapers/presets/')
    const presetsData = presetsRes.data as any
    wallpaperPresets.value = Array.isArray(presetsData) ? presetsData : (presetsData?.results || [])

    // Load current wallpaper for this chat
    const wallpaperRes = await apiClient.get('/social/chat-wallpapers/', {
      params: {
        chat_id: props.chatId
      }
    })
    const wallpaperData = wallpaperRes.data as any
    const wallpapers = Array.isArray(wallpaperData) ? wallpaperData : (wallpaperData?.results || [])
    if (wallpapers.length > 0) {
      currentWallpaperId.value = wallpapers[0].id
    }

    // Load tags
    const tagsRes = await apiClient.get('/social/chat-tags/')
    const tagsData = tagsRes.data as any
    userTags.value = Array.isArray(tagsData) ? tagsData : (tagsData?.results || [])

    // Load chat tags
    const chatTagsRes = await apiClient.get('/social/chat-tag-assignments/', {
      params: {
        group_chat: props.chatType === 'group' ? props.chatId : undefined,
        private_chat: props.chatType === 'private' ? props.chatId : undefined
      }
    })
    const chatTagsData = chatTagsRes.data as any
    const chatTagsList = Array.isArray(chatTagsData) ? chatTagsData : (chatTagsData?.results || [])
    chatTags.value = chatTagsList.map((a: any) => a.tag).filter(Boolean)

    // Load anti-spam rules (только для групповых чатов)
    if (props.chatType === 'group') {
      const rulesRes = await apiClient.get('/social/anti-spam-rules/', {
        params: { chat: props.chatId }
      })
      const rulesData = rulesRes.data as any
      antiSpamRules.value = Array.isArray(rulesData) ? rulesData : (rulesData?.results || [])

      // Load slow mode
      const slowModeRes = await apiClient.get('/social/chat-slow-modes/', {
        params: { chat: props.chatId }
      })
      const slowModeData = slowModeRes.data as any
      const slowModeList = Array.isArray(slowModeData) ? slowModeData : (slowModeData?.results || [])
      const sm = slowModeList?.[0]
      if (sm) {
        slowMode.value = {
          id: sm.id,
          enabled: sm.enabled,
          delay: sm.delay,
          exempt_admins: sm.exempt_admins,
          exempt_moderators: sm.exempt_moderators
        }
      }
    }

    // Load scheduled messages
    const scheduledRes = await apiClient.get('/social/scheduled-messages/', {
      params: {
        chat: props.chatType === 'group' ? props.chatId : undefined,
        private_chat: props.chatType === 'private' ? props.chatId : undefined
      }
    })
    const scheduledData = scheduledRes.data as any
    const scheduledList = Array.isArray(scheduledData) ? scheduledData : (scheduledData?.results || [])
    scheduledMessages.value = scheduledList.filter((m: ScheduledMessage) => m.status === 'scheduled')

    // Load backups (только для групповых чатов)
    if (props.chatType === 'group') {
      const backupsRes = await apiClient.get('/social/chat-backups/', {
        params: { chat: props.chatId }
      })
      const backupsData = backupsRes.data as any
      backups.value = Array.isArray(backupsData) ? backupsData : (backupsData?.results || [])
    }

    // Load theme
    const themesRes = await apiClient.get('/social/chat-themes/')
    const themesData = themesRes.data as any
    const themesList = Array.isArray(themesData) ? themesData : (themesData?.results || [])
    const existingTheme = themesList.find((t: ChatTheme) => 
      (props.chatType === 'group' && t.chat === props.chatId) ||
      (props.chatType === 'private' && t.private_chat === props.chatId)
    )
    if (existingTheme) {
      currentTheme.value = existingTheme
      enableMessageAnimation.value = existingTheme.message_animation !== 'none'
      enableReactionAnimation.value = existingTheme.reaction_animation !== 'none'
    }

  } catch (error) {
    console.error('Error loading settings:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
/* Modal Overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 9999;
}

.chat-settings-modal {
  display: flex;
  height: 85vh;
  width: 100%;
  max-width: 64rem;
  background: #111827;
  color: white;
  border-radius: 1rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  z-index: 10000;
}

.settings-sidebar {
  width: 14rem;
  border-right: 1px solid #374151;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid #374151;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
}

.close-btn {
  padding: 0.375rem;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: #374151;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: 0.5rem;
  text-align: left;
  transition: all 0.2s;
  font-size: 0.875rem;
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
}

.nav-item:hover {
  background: #1f2937;
}

.nav-item.active {
  background: #2563eb;
  color: white;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 0.75rem;
  color: #9ca3af;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid #3b82f6;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.section {
  max-width: 48rem;
  margin: 0 auto;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}

/* Wallpaper */
.wallpaper-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.wallpaper-item {
  position: relative;
  aspect-ratio: 16/9;
  border-radius: 0.5rem;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  overflow: hidden;
}

.wallpaper-item:hover {
  border-color: #3b82f6;
}

.wallpaper-item.active {
  border-color: #3b82f6;
}

.preset-label {
  position: absolute;
  bottom: 0.5rem;
  left: 0.5rem;
  font-size: 0.75rem;
  background: rgba(0, 0, 0, 0.6);
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.check-icon {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  color: white;
  background: #3b82f6;
  border-radius: 50%;
  padding: 0.125rem;
}

.custom-wallpaper {
  border-top: 1px solid #374151;
  padding-top: 1.5rem;
}

.custom-wallpaper h4 {
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 1rem;
}

.wallpaper-type-select {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.wallpaper-type-select button {
  flex: 1;
  padding: 0.5rem;
  border-radius: 0.5rem;
  border: 1px solid #4b5563;
  transition: all 0.2s;
  font-size: 0.875rem;
  background: transparent;
  color: white;
  cursor: pointer;
}

.wallpaper-type-select button.active {
  background: #3b82f6;
  border-color: #3b82f6;
}

.color-picker {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.color-picker label,
.color-picker span {
  font-size: 0.875rem;
  color: #9ca3af;
}

.color-picker input[type="color"] {
  width: 100%;
  height: 3rem;
  border-radius: 0.5rem;
  cursor: pointer;
  border: none;
}

.gradient-picker {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.image-upload .upload-btn {
  width: 100%;
  padding: 0.75rem;
  border: 2px dashed #4b5563;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s;
  background: transparent;
  color: white;
  cursor: pointer;
}

.image-upload .upload-btn:hover {
  border-color: #3b82f6;
  background: #1f2937;
}

.image-upload .preview {
  margin-top: 1rem;
  border-radius: 0.5rem;
  overflow: hidden;
}

.image-upload .preview img {
  width: 100%;
  height: 10rem;
  object-fit: cover;
}

.wallpaper-settings {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.slider-setting {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.slider-setting label {
  font-size: 0.875rem;
  color: #9ca3af;
}

.slider-setting input[type="range"] {
  width: 100%;
  accent-color: #3b82f6;
}

.apply-btn,
.save-btn {
  width: 100%;
  padding: 0.75rem;
  background: #3b82f6;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: background-color 0.2s;
  margin-top: 1rem;
  border: none;
  color: white;
  cursor: pointer;
}

.apply-btn:hover,
.save-btn:hover {
  background: #2563eb;
}

.apply-btn:disabled,
.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Theme */
.theme-options {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option-group > label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #9ca3af;
}

.theme-select,
.bubble-styles,
.font-sizes,
.time-formats,
.emoji-sets,
.delay-options {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.theme-select button,
.bubble-styles button,
.font-sizes button,
.time-formats button,
.emoji-sets button,
.delay-options button {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid #4b5563;
  transition: all 0.2s;
  font-size: 0.875rem;
  background: transparent;
  color: white;
  cursor: pointer;
}

.theme-select button.active,
.bubble-styles button.active,
.font-sizes button.active,
.time-formats button.active,
.emoji-sets button.active,
.delay-options button.active {
  background: #3b82f6;
  border-color: #3b82f6;
}

.color-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.animation-settings {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Notifications */
.notification-settings {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #374151;
}

.setting-info {
  display: flex;
  flex-direction: column;
}

.setting-name {
  font-weight: 500;
}

.setting-desc {
  font-size: 0.875rem;
  color: #9ca3af;
}

.mute-select {
  padding: 0.5rem 1rem;
  background: #1f2937;
  border: 1px solid #4b5563;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: white;
}

/* Tags */
.current-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.tag-chip {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  border-radius: 9999px;
  border: 1px solid;
  font-size: 0.875rem;
}

.remove-tag {
  padding: 0.125rem;
  border-radius: 0.25rem;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
}

.remove-tag:hover {
  background: rgba(255, 255, 255, 0.1);
}

.empty-tags {
  color: #9ca3af;
  font-size: 0.875rem;
}

.add-tag {
  margin-bottom: 1.5rem;
}

.add-tag h4 {
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.tag-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-input {
  flex: 1;
  min-width: 12rem;
  padding: 0.5rem 0.75rem;
  background: #1f2937;
  border: 1px solid #4b5563;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: white;
}

.tag-colors {
  display: flex;
  gap: 0.25rem;
}

.color-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  border: 2px solid transparent;
  transition: transform 0.2s;
  cursor: pointer;
}

.color-btn.active {
  border-color: white;
  transform: scale(1.1);
}

.emoji-input {
  width: 4rem;
  padding: 0.5rem 0.75rem;
  background: #1f2937;
  border: 1px solid #4b5563;
  border-radius: 0.5rem;
  text-align: center;
  font-size: 0.875rem;
  color: white;
}

.create-tag-btn {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
  font-size: 0.875rem;
  border: none;
  color: white;
  cursor: pointer;
}

.create-tag-btn:hover {
  background: #2563eb;
}

.create-tag-btn:disabled {
  opacity: 0.5;
}

.your-tags h4 {
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.875rem;
}

.tag-item:hover {
  background: #1f2937;
}

/* Slow Mode */
.slowmode-config {
  margin-top: 1rem;
  padding: 1rem;
  background: #1f2937;
  border-radius: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Anti-spam */
.antispam-rules {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.rule-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #1f2937;
  border-radius: 0.5rem;
}

.rule-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.rule-info {
  display: flex;
  flex-direction: column;
}

.rule-name {
  font-weight: 500;
}

.rule-desc {
  font-size: 0.875rem;
  color: #9ca3af;
}

.rule-actions {
  display: flex;
  gap: 0.5rem;
}

.edit-btn,
.delete-btn {
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: all 0.2s;
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
}

.edit-btn:hover,
.delete-btn:hover {
  background: #374151;
}

.delete-btn:hover {
  color: #ef4444;
}

.add-rule-btn {
  width: 100%;
  padding: 0.75rem;
  border: 2px dashed #4b5563;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s;
  background: transparent;
  color: white;
  cursor: pointer;
}

.add-rule-btn:hover {
  border-color: #3b82f6;
  background: #1f2937;
}

/* Scheduled */
.scheduled-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.scheduled-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #1f2937;
  border-radius: 0.5rem;
}

.scheduled-info {
  display: flex;
  flex-direction: column;
}

.scheduled-text {
  font-weight: 500;
}

.scheduled-time {
  font-size: 0.875rem;
  color: #9ca3af;
}

.scheduled-actions {
  display: flex;
  gap: 0.5rem;
}

.send-btn {
  padding: 0.375rem 0.75rem;
  background: #16a34a;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  transition: background-color 0.2s;
  border: none;
  color: white;
  cursor: pointer;
}

.send-btn:hover {
  background: #15803d;
}

.cancel-btn {
  padding: 0.375rem 0.75rem;
  background: #dc2626;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  transition: background-color 0.2s;
  border: none;
  color: white;
  cursor: pointer;
}

.cancel-btn:hover {
  background: #b91c1c;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}

.add-scheduled-btn {
  width: 100%;
  padding: 0.75rem;
  border: 2px dashed #4b5563;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s;
  background: transparent;
  color: white;
  cursor: pointer;
}

.add-scheduled-btn:hover {
  border-color: #3b82f6;
  background: #1f2937;
}

/* Backups */
.backups-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.backup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #1f2937;
  border-radius: 0.5rem;
}

.backup-info {
  display: flex;
  flex-direction: column;
}

.backup-date {
  font-weight: 500;
}

.backup-stats {
  font-size: 0.875rem;
  color: #9ca3af;
}

.backup-actions {
  display: flex;
  gap: 0.5rem;
}

.download-btn {
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
}

.download-btn:hover {
  background: #374151;
}

.restore-btn {
  padding: 0.375rem 0.75rem;
  background: #3b82f6;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  transition: background-color 0.2s;
  border: none;
  color: white;
  cursor: pointer;
}

.restore-btn:hover {
  background: #2563eb;
}

.create-backup-btn {
  width: 100%;
  padding: 0.75rem;
  background: #3b82f6;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: background-color 0.2s;
  border: none;
  color: white;
  cursor: pointer;
}

.create-backup-btn:hover {
  background: #2563eb;
}

.create-backup-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Danger Zone */
.danger-zone {
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.danger-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.danger-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #374151;
}

.danger-info {
  display: flex;
  flex-direction: column;
}

.danger-name {
  font-weight: 500;
  color: #f87171;
}

.danger-desc {
  font-size: 0.875rem;
  color: #9ca3af;
}

.danger-btn {
  padding: 0.5rem 1rem;
  background: #dc2626;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
  font-size: 0.875rem;
  border: none;
  color: white;
  cursor: pointer;
}

.danger-btn:hover {
  background: #b91c1c;
}

.danger-btn.critical {
  background: #b91c1c;
  font-weight: 500;
}

.danger-btn.critical:hover {
  background: #991b1b;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  z-index: 10001;
}

.toast.success {
  background: #16a34a;
  color: white;
}

.toast.error {
  background: #dc2626;
  color: white;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
