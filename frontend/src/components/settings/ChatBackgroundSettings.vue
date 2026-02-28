<template>
  <div class="settings-section">
    <h2>Фон чатов</h2>

    <div class="settings-group">
      <h3>🎨 Общий фон</h3>
      
      <div class="background-types">
        <label class="bg-type-option" :class="{ active: backgroundType === 'default' }">
          <input type="radio" v-model="backgroundType" value="default" />
          <div class="bg-preview default"></div>
          <span>Системный</span>
        </label>

        <label class="bg-type-option" :class="{ active: backgroundType === 'solid' }">
          <input type="radio" v-model="backgroundType" value="solid" />
          <div class="bg-preview solid" :style="{ background: solidColor }"></div>
          <span>Сплошной цвет</span>
        </label>

        <label class="bg-type-option" :class="{ active: backgroundType === 'gradient' }">
          <input type="radio" v-model="backgroundType" value="gradient" />
          <div class="bg-preview gradient" :style="gradientPreviewStyle"></div>
          <span>Градиент</span>
        </label>

        <label class="bg-type-option" :class="{ active: backgroundType === 'image' }">
          <input type="radio" v-model="backgroundType" value="image" />
          <div class="bg-preview image" :style="{ backgroundImage: `url(${customImage})` }"></div>
          <span>Изображение</span>
        </label>
      </div>

      <!-- Solid Color Picker -->
      <div v-if="backgroundType === 'solid'" class="color-picker-section">
        <label>Выберите цвет:</label>
        <div class="color-palette">
          <button
            v-for="color in presetColors"
            :key="color"
            :class="['color-option', { active: solidColor === color }]"
            :style="{ backgroundColor: color }"
            @click="solidColor = color"
          ></button>
          <button class="color-option custom" @click="showCustomColorPicker = true">
            🌈
          </button>
        </div>
        <div v-if="showCustomColorPicker" class="custom-color-input">
          <input
            v-model="solidColor"
            type="color"
            class="color-input"
          />
          <button @click="showCustomColorPicker = false" class="done-btn">Готово</button>
        </div>
      </div>

      <!-- Gradient Picker -->
      <div v-if="backgroundType === 'gradient'" class="gradient-picker-section">
        <div class="gradient-controls">
          <div class="gradient-color">
            <label>Начальный цвет:</label>
            <input
              v-model="gradientColors.start"
              type="color"
              class="color-input"
            />
          </div>
          <div class="gradient-color">
            <label>Конечный цвет:</label>
            <input
              v-model="gradientColors.end"
              type="color"
              class="color-input"
            />
          </div>
        </div>
        <div class="gradient-presets">
          <label>Пресеты:</label>
          <div class="preset-grid">
            <button
              v-for="(preset, index) in gradientPresets"
              :key="index"
              class="gradient-preset"
              :style="{ background: preset }"
              @click="applyGradientPreset(preset)"
            ></button>
          </div>
        </div>
      </div>

      <!-- Image Upload -->
      <div v-if="backgroundType === 'image'" class="image-upload-section">
        <div class="upload-area" :class="{ 'has-image': customImage }">
          <img v-if="customImage" :src="customImage" class="preview-image" />
          <div v-else class="upload-placeholder">
            <div class="upload-icon">📁</div>
            <p>Перетащите изображение сюда или</p>
            <input
              ref="imageInput"
              type="file"
              accept="image/*"
              @change="handleImageUpload"
              class="hidden-input"
            />
            <button @click="selectImage" class="upload-btn">Выберите файл</button>
            <p class="upload-hint">JPG, PNG, WEBP до 10MB</p>
          </div>
          <button v-if="customImage" @click="removeImage" class="remove-image-btn">🗑️ Удалить</button>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>✨ Эффекты для фона (премиум)</h3>
      
      <div class="effects-list">
        <label class="effect-option">
          <input type="checkbox" v-model="effects.blur" :disabled="!isPremium" />
          <span class="effect-icon">🌫️</span>
          <span>Размытие</span>
          <span v-if="!isPremium" class="premium-badge">👑</span>
        </label>

        <label class="effect-option">
          <input type="checkbox" v-model="effects.darken" :disabled="!isPremium" />
          <span class="effect-icon">🌙</span>
          <span>Затемнение</span>
          <span v-if="!isPremium" class="premium-badge">👑</span>
        </label>

        <label class="effect-option">
          <input type="checkbox" v-model="effects.animation" :disabled="!isPremium" />
          <span class="effect-icon">🎬</span>
          <span>Анимация (медленное движение)</span>
          <span v-if="!isPremium" class="premium-badge">👑</span>
        </label>

        <label class="effect-option">
          <input type="checkbox" v-model="effects.parallax" :disabled="!isPremium" />
          <span class="effect-icon">📐</span>
          <span>Параллакс-эффект</span>
          <span v-if="!isPremium" class="premium-badge">👑</span>
        </label>
      </div>

      <div v-if="!isPremium" class="premium-upsell">
        <p>👑 Разблокируйте все эффекты с Premium!</p>
        <button class="premium-btn">Подробнее о Premium →</button>
      </div>
    </div>

    <div class="settings-group">
      <h3>💬 Индивидуальные фоны для чатов</h3>
      
      <div class="chat-backgrounds-list">
        <div v-for="chat in chatBackgrounds" :key="chat.id" class="chat-bg-item">
          <div class="chat-info">
            <div class="chat-avatar">
              <img v-if="chat.avatar" :src="chat.avatar" />
              <span v-else>{{ chat.name[0] }}</span>
            </div>
            <div class="chat-details">
              <div class="chat-name">{{ chat.name }}</div>
              <div class="chat-type">{{ chat.type === 'group' ? '👥 Группа' : '👤 Личный чат' }}</div>
            </div>
          </div>
          <div class="chat-bg-settings">
            <label class="use-shared-label">
              <input type="checkbox" v-model="chat.useShared" />
              <span>Общий</span>
            </label>
            <button @click="openChatBackgroundSettings(chat)" class="custom-bg-btn">
              {{ chat.useShared ? 'Использует общий' : 'Свой фон' }}
            </button>
          </div>
        </div>
      </div>

      <button class="add-chat-bg-btn">
        ➕ Добавить фон для чата
      </button>
    </div>

    <div class="settings-group">
      <h3>👁️ Предпросмотр</h3>
      
      <div class="preview-container" :style="previewStyle">
        <div class="preview-chat">
          <div class="preview-message other">
            <div class="msg-avatar">👤</div>
            <div class="msg-content">
              <div class="msg-name">User123</div>
              <div class="msg-text">Привет! Как дела?</div>
            </div>
          </div>
          <div class="preview-message user">
            <div class="msg-avatar">👤</div>
            <div class="msg-content">
              <div class="msg-name">Вы</div>
              <div class="msg-text">Отлично! Спасибо что спросил 😊</div>
            </div>
          </div>
          <div class="preview-message other">
            <div class="msg-avatar">👤</div>
            <div class="msg-content">
              <div class="msg-name">User123</div>
              <div class="msg-text">Посмотри новое аниме, которое вышло!</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="saveSettings" :disabled="!hasChanges" class="save-btn">
        💾 Сохранить настройки
      </button>
      <button @click="resetToDefaults" class="reset-btn">
        ↻ Сбросить по умолчанию
      </button>
    </div>

    <!-- Модальное окно -->
    <ChatBackgroundModal
      :show="showChatBgModal"
      :selected-chat="selectedChat ?? undefined"
      @close="showChatBgModal = false"
      @save="saveChatBackground"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'

interface ChatBackground {
  id: number
  name: string
  type: 'private' | 'group'
  avatar?: string
  useShared: boolean
  customBackground?: string
}

const backgroundType = ref('default')
const solidColor = ref('#1a1a2e')
const gradientColors = ref({ start: '#667eea', end: '#764ba2' })
const customImage = ref('')

const effects = ref({
  blur: false,
  darken: false,
  animation: false,
  parallax: false
})

const isPremium = ref(false)
const showCustomColorPicker = ref(false)
const imageInput = ref<HTMLInputElement | null>(null)

const chatBackgrounds = ref<ChatBackground[]>([
  { id: 1, name: 'Attack on Titan Fans', type: 'group', useShared: true },
  { id: 2, name: 'User123', type: 'private', useShared: false },
  { id: 3, name: 'One Piece Community', type: 'group', useShared: true }
])

const showChatBgModal = ref(false)
const selectedChat = ref<ChatBackground | null>(null)
const selectedChatBg = ref('shared')

const presetColors = [
  '#1a1a2e', '#16213e', '#0f3460', '#533483', '#e94560',
  '#2d3436', '#636e72', '#b2bec3', '#dfe6e9', '#74b9ff'
]

const gradientPresets = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
]

const originalSettings = ref({})

const gradientPreviewStyle = computed(() => {
  return {
    background: `linear-gradient(135deg, ${gradientColors.value.start} 0%, ${gradientColors.value.end} 100%)`
  }
})

const previewStyle = computed(() => {
  const bgStyle: any = {}

  if (backgroundType.value === 'default') {
    bgStyle.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  } else if (backgroundType.value === 'solid') {
    bgStyle.background = solidColor.value
  } else if (backgroundType.value === 'gradient') {
    bgStyle.background = gradientPreviewStyle.value.background
  } else if (backgroundType.value === 'image' && customImage.value) {
    bgStyle.backgroundImage = `url(${customImage.value})`
    bgStyle.backgroundSize = 'cover'
    bgStyle.backgroundPosition = 'center'
  }

  if (effects.value.blur) {
    bgStyle.filter = 'blur(2px)'
  }
  if (effects.value.darken) {
    bgStyle.filter = bgStyle.filter ? `${bgStyle.filter} brightness(0.7)` : 'brightness(0.7)'
  }

  return bgStyle
})

const hasChanges = computed(() => {
  return JSON.stringify({
    backgroundType: backgroundType.value,
    solidColor: solidColor.value,
    gradientColors: gradientColors.value,
    customImage: customImage.value,
    effects: effects.value
  }) !== JSON.stringify(originalSettings.value)
})

const fetchBackgroundSettings = async () => {
  try {
    const data = await settingsApi.getChatBackgroundSettings()
    backgroundType.value = data.background_type || 'default'
    solidColor.value = data.solid_color || '#1a1a2e'
    gradientColors.value = data.gradient_colors || gradientColors.value
    customImage.value = data.custom_image || ''
    effects.value = data.effects || effects.value
    isPremium.value = data.is_premium || false

    originalSettings.value = {
      backgroundType: backgroundType.value,
      solidColor: solidColor.value,
      gradientColors: { ...gradientColors.value },
      customImage: customImage.value,
      effects: { ...effects.value }
    }
  } catch (error) {
    console.error('Error fetching background settings:', error)
  }
}

const applyGradientPreset = (preset: string) => {
  const colors = preset.match(/#[a-fA-F0-9]{6}/g)
  if (colors && colors.length >= 2) {
    gradientColors.value.start = colors[0]!
    gradientColors.value.end = colors[1]!
  }
}

const selectImage = () => {
  imageInput.value?.click()
}

const handleImageUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (file) {
    if (file.size > 10 * 1024 * 1024) {
      alert('Размер файла не должен превышать 10MB')
      return
    }

    try {
      const data = await settingsApi.uploadChatBackground(file, 'Custom Background')
      customImage.value = data.url
    } catch (error) {
      console.error('Error uploading background:', error)
      alert('Ошибка при загрузке изображения')
    }
  }
}

const removeImage = async () => {
  try {
    await settingsApi.deleteChatBackground()
    customImage.value = ''
  } catch (error) {
    console.error('Error removing background:', error)
    alert('Ошибка при удалении изображения')
  }
}

const openChatBackgroundSettings = (chat: ChatBackground) => {
  selectedChat.value = chat
  selectedChatBg.value = chat.useShared ? 'shared' : 'custom'
  showChatBgModal.value = true
}

const saveChatBackground = (background: string) => {
  if (selectedChat.value) {
    selectedChat.value.useShared = background === 'shared'
  }
  showChatBgModal.value = false
}

const saveSettings = async () => {
  try {
    await settingsApi.updateChatBackgroundSettings({
      background_type: backgroundType.value,
      solid_color: solidColor.value,
      gradient_colors: gradientColors.value,
      custom_image: customImage.value,
      effects: effects.value
    })
    originalSettings.value = {
      backgroundType: backgroundType.value,
      solidColor: solidColor.value,
      gradientColors: { ...gradientColors.value },
      customImage: customImage.value,
      effects: { ...effects.value }
    }
    alert('Настройки сохранены!')
  } catch (error) {
    console.error('Error saving background settings:', error)
    alert('Ошибка при сохранении настроек')
  }
}

const resetToDefaults = () => {
  backgroundType.value = 'default'
  solidColor.value = '#1a1a2e'
  gradientColors.value = { start: '#667eea', end: '#764ba2' }
  customImage.value = ''
  effects.value = { blur: false, darken: false, animation: false, parallax: false }
}

onMounted(() => {
  fetchBackgroundSettings()
})
</script>

<style scoped>
.settings-group {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.settings-group h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
}

.background-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.bg-type-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 10px;
  border-radius: 6px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.bg-type-option:hover {
  background: var(--card-bg);
}

.bg-type-option.active {
  border-color: var(--primary-color);
  background: rgba(0, 132, 255, 0.1);
}

.bg-type-option input[type="radio"] {
  display: none;
}

.bg-preview {
  width: 80px;
  height: 60px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.bg-preview.default {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.bg-preview.solid {
  background: #1a1a2e;
}

.bg-preview.gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.bg-preview.image {
  background-size: cover;
  background-position: center;
}

.color-picker-section {
  margin-top: 15px;
}

.color-palette {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.color-option {
  width: 35px;
  height: 35px;
  border-radius: 50%;
  border: 3px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.color-option.active {
  border-color: var(--primary-color);
}

.color-option.custom {
  background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.custom-color-input {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 15px;
}

.color-input {
  width: 50px;
  height: 35px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.done-btn {
  padding: 6px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.gradient-picker-section {
  margin-top: 15px;
}

.gradient-controls {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.gradient-color {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.gradient-color label {
  font-size: 13px;
  color: var(--secondary-text);
}

.gradient-presets {
  margin-top: 15px;
}

.gradient-presets label {
  display: block;
  margin-bottom: 10px;
  font-size: 13px;
  color: var(--secondary-text);
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(60px, 1fr));
  gap: 10px;
}

.gradient-preset {
  height: 40px;
  border-radius: 6px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.gradient-preset:hover {
  border-color: var(--primary-color);
}

.image-upload-section {
  margin-top: 15px;
}

.upload-area {
  position: relative;
  min-height: 200px;
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--card-bg);
}

.upload-area.has-image {
  border-style: solid;
}

.preview-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 6px;
}

.upload-placeholder {
  text-align: center;
  padding: 20px;
}

.upload-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.upload-placeholder p {
  color: var(--secondary-text);
  margin-bottom: 10px;
}

.hidden-input {
  display: none;
}

.upload-btn {
  padding: 8px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.upload-hint {
  font-size: 12px;
  color: var(--secondary-text);
  margin-top: 10px;
}

.remove-image-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 8px 12px;
  background: rgba(244, 67, 54, 0.9);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.effects-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.effect-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
}

.effect-option input[type="checkbox"]:disabled {
  opacity: 0.5;
}

.effect-icon {
  font-size: 20px;
}

.premium-badge {
  margin-left: auto;
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.premium-upsell {
  text-align: center;
  padding: 15px;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 165, 0, 0.1));
  border-radius: 6px;
  border: 1px solid rgba(255, 215, 0, 0.3);
}

.premium-upsell p {
  margin: 0 0 10px 0;
  font-weight: 500;
}

.premium-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.chat-backgrounds-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.chat-bg-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--card-bg);
  border-radius: 6px;
}

.chat-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  overflow: hidden;
}

.chat-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.chat-name {
  font-weight: 500;
}

.chat-type {
  font-size: 12px;
  color: var(--secondary-text);
}

.chat-bg-settings {
  display: flex;
  align-items: center;
  gap: 10px;
}

.use-shared-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
}

.custom-bg-btn {
  padding: 6px 12px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.add-chat-bg-btn {
  width: 100%;
  padding: 10px 16px;
  background: var(--hover-bg);
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-color);
  margin-top: 10px;
}

.preview-container {
  border-radius: 8px;
  overflow: hidden;
  min-height: 200px;
  position: relative;
}

.preview-chat {
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-message {
  display: flex;
  gap: 10px;
  max-width: 80%;
}

.preview-message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.msg-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.msg-name {
  font-size: 11px;
  color: var(--secondary-text);
}

.preview-message.user .msg-name {
  text-align: right;
}

.msg-text {
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.4;
}

.preview-message.other .msg-text {
  background: rgba(0, 0, 0, 0.3);
  color: white;
  border-bottom-left-radius: 4px;
}

.preview-message.user .msg-text {
  background: rgba(255, 255, 255, 0.9);
  color: #000;
  border-bottom-right-radius: 4px;
}

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.save-btn, .reset-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.save-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reset-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
}
</style>
