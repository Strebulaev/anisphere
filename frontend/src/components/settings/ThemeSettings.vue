<template>
  <div class="settings-section">
    <transition name="toast">
      <div v-if="toast.visible" :class="['toast-notif', toast.type]">{{ toast.message }}</div>
    </transition>
    <h2>Тема и оформление</h2>

    <div class="settings-group">
      <h3>🎭 Выбор темы</h3>
      <div class="theme-grid">
        <label class="theme-option" :class="{ active: currentTheme === 'light' }">
          <input type="radio" :checked="currentTheme === 'light'" @change="setTheme('light')">
          <div class="theme-preview light">
            <div class="preview-header"></div>
            <div class="preview-content">
              <div class="preview-bubble user"></div>
              <div class="preview-bubble other"></div>
            </div>
          </div>
          <span>Светлая</span>
        </label>

        <label class="theme-option" :class="{ active: currentTheme === 'dark' }">
          <input type="radio" :checked="currentTheme === 'dark'" @change="setTheme('dark')">
          <div class="theme-preview dark">
            <div class="preview-header"></div>
            <div class="preview-content">
              <div class="preview-bubble user"></div>
              <div class="preview-bubble other"></div>
            </div>
          </div>
          <span>Темная</span>
        </label>

        <label class="theme-option" :class="{ active: currentTheme === 'system' }">
          <input type="radio" :checked="currentTheme === 'system'" @change="setTheme('system')">
          <div class="theme-preview system">
            <div class="preview-header gradient"></div>
            <div class="preview-content">
              <div class="preview-bubble user"></div>
              <div class="preview-bubble other"></div>
            </div>
          </div>
          <span>Как в системе</span>
        </label>

        <label class="theme-option" :class="{ active: currentTheme === 'blue' }">
          <input type="radio" :checked="currentTheme === 'blue'" @change="setTheme('blue')">
          <div class="theme-preview blue">
            <div class="preview-header"></div>
            <div class="preview-content">
              <div class="preview-bubble user"></div>
              <div class="preview-bubble other"></div>
            </div>
          </div>
          <span>Синяя</span>
        </label>

        <label class="theme-option" :class="{ active: currentTheme === 'green' }">
          <input type="radio" :checked="currentTheme === 'green'" @change="setTheme('green')">
          <div class="theme-preview green">
            <div class="preview-header"></div>
            <div class="preview-content">
              <div class="preview-bubble user"></div>
              <div class="preview-bubble other"></div>
            </div>
          </div>
          <span>Зеленая</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="palette" /> Акцентный цвет</h3>
      <div class="color-palette">
        <button
          v-for="color in accentColors"
          :key="color.value"
          :class="['color-option', { active: accentColor === color.value }]"
          :style="{ backgroundColor: color.value }"
          @click="handleAccentColorChange(color.value)"
        ></button>
        <button class="color-option custom" @click="showCustomColor = true"> <SakuraIcon name="rainbow" /> </button>
      </div>

      <div v-if="showCustomColor" class="custom-color-input">
        <input
          v-model="customColor"
          type="color"
          class="color-picker"
          @change="handleAccentColorChange(customColor)"
        >
        <button @click="showCustomColor = false" class="done-btn">Готово</button>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="image" /> Фон чатов</h3>
      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="useSharedBackground">
          <span>Использовать общий фон для всех чатов</span>
        </label>
      </div>

      <div class="background-selector" v-if="useSharedBackground">
        <select v-model="selectedBackground" class="background-select">
          <option value="default">Градиент синий</option>
          <option value="stars">Звездное небо</option>
          <option value="mountains">Горы</option>
          <option value="ocean">Океан</option>
        </select>
      </div>

      <div class="background-preview" v-if="useSharedBackground && selectedBackground">
        <div class="preview-container" :class="selectedBackground">
          <div class="preview-chat">
            <div class="preview-message user">Привет! Как дела?</div>
            <div class="preview-message other">Отлично! Спасибо что спросил <SakuraIcon name="blush" /></div>
          </div>
        </div>
      </div>

      <div class="background-actions">
        <button class="action-btn">
          <SakuraIcon name="image" /> Мои фоны (3)
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3>🔤 Шрифты</h3>
      <div class="font-settings">
        <div class="setting-item">
          <label>Основной шрифт:</label>
          <select v-model="selectedFont" class="font-select">
            <option value="Roboto">Roboto</option>
            <option value="Open Sans">Open Sans</option>
            <option value="Lato">Lato</option>
            <option value="Montserrat">Montserrat</option>
          </select>
        </div>

        <div class="setting-item">
          <label>Размер шрифта:</label>
          <div class="size-slider">
            <span>Маленький</span>
            <input
              v-model="fontSize"
              type="range"
              min="12"
              max="18"
              step="1"
              class="slider"
            >
            <span>Большой</span>
          </div>
        </div>

        <div class="setting-item">
          <label>Межстрочный интервал:</label>
          <div class="spacing-slider">
            <span>Узкий</span>
            <input
              v-model="lineSpacing"
              type="range"
              min="1.0"
              max="1.8"
              step="0.1"
              class="slider"
            >
            <span>Широкий</span>
          </div>
        </div>

        <div class="setting-item">
          <label>Жирность:</label>
          <select v-model="fontWeight" class="weight-select">
            <option value="normal">Обычный</option>
            <option value="bold">Жирный</option>
          </select>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="gamepad" /> Эффекты и анимации</h3>
      <div class="effect-settings">
        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="smoothAnimations">
            <span>Плавные анимации</span>
          </label>
        </div>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="scrollEffects">
            <span>Эффекты прокрутки</span>
          </label>
        </div>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="parallaxEffect">
            <span>Параллакс эффект</span>
          </label>
        </div>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="truncateNames">
            <span>Сокращать длинные имена</span>
          </label>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="phone" /> Компактный режим</h3>
      <div class="compact-settings">
        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="compactLists">
            <span>Компактные списки чатов</span>
          </label>
        </div>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="hideAvatars">
            <span>Скрывать аватары в чатах</span>
          </label>
        </div>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="showTimeEverywhere">
            <span>Показывать время каждого сообщения</span>
          </label>
        </div>

        <div class="setting-item">
          <label class="setting-label">
            <input type="checkbox" v-model="smallEmojis">
            <span>Уменьшенные эмодзи</span>
          </label>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="eye" /> Высокая контрастность</h3>
      <div class="contrast-setting">
        <label class="setting-label">
          <input type="checkbox" v-model="highContrast">
          <span>Включить для улучшения читаемости</span>
        </label>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="previewSettings" class="preview-btn">
        <SakuraIcon name="eye" /> Предпросмотр
      </button>
      <button @click="saveSettings" :disabled="!hasChanges" class="save-btn">
        <SakuraIcon name="save" /> Сохранить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import * as settingsApi from '@/api/settings'
import { useTheme } from '@/composables/useTheme'

// ── Toast ────────────────────────────────────────────────────────
const toast = ref({ visible: false, message: '', type: 'success' as 'success' | 'error' })
let _toastTimer: ReturnType<typeof setTimeout> | null = null
const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
  if (_toastTimer) clearTimeout(_toastTimer)
  toast.value = { visible: true, message: msg, type }
  _toastTimer = setTimeout(() => (toast.value.visible = false), 3000)
}

const { currentTheme, accentColor, setTheme, setAccentColor } = useTheme()

// Reactive data
const showCustomColor = ref(false)
const customColor = ref('#0084FF')
const useSharedBackground = ref(true)
const selectedBackground = ref('default')
const selectedFont = ref('Roboto')
const fontSize = ref(14)
const lineSpacing = ref(1.2)
const fontWeight = ref('normal')
const smoothAnimations = ref(true)
const scrollEffects = ref(true)
const parallaxEffect = ref(false)
const truncateNames = ref(true)
const compactLists = ref(true)
const hideAvatars = ref(false)
const showTimeEverywhere = ref(false)
const smallEmojis = ref(true)
const highContrast = ref(false)

const accentColors = [
  { value: '#0084FF' }, // Blue
  { value: '#00C853' }, // Green
  { value: '#AA00FF' }, // Purple
  { value: '#FF6D00' }, // Orange
  { value: '#D50000' }, // Red
  { value: '#FFD600' }  // Yellow
]

const originalSettings = ref({})

const hasChanges = computed(() => {
  return JSON.stringify({
    currentTheme: currentTheme.value,
    accentColor: accentColor.value,
    useSharedBackground: useSharedBackground.value,
    selectedBackground: selectedBackground.value,
    selectedFont: selectedFont.value,
    fontSize: fontSize.value,
    lineSpacing: lineSpacing.value,
    fontWeight: fontWeight.value,
    smoothAnimations: smoothAnimations.value,
    scrollEffects: scrollEffects.value,
    parallaxEffect: parallaxEffect.value,
    truncateNames: truncateNames.value,
    compactLists: compactLists.value,
    hideAvatars: hideAvatars.value,
    showTimeEverywhere: showTimeEverywhere.value,
    smallEmojis: smallEmojis.value,
    highContrast: highContrast.value,
  }) !== JSON.stringify(originalSettings.value)
})

// Methods
const fetchSettings = async () => {
  try {
    const data = await settingsApi.getThemeSettings()
    useSharedBackground.value = data.use_shared_background ?? true
    selectedBackground.value = data.custom_background || 'default'
    smoothAnimations.value = data.smooth_animations ?? true
    scrollEffects.value = data.scroll_effects ?? true
    parallaxEffect.value = data.parallax_effect ?? false
    truncateNames.value = data.truncate_names ?? true
    compactLists.value = data.compact_lists ?? true
    hideAvatars.value = data.hide_avatars ?? false
    showTimeEverywhere.value = data.show_time_everywhere ?? false
    smallEmojis.value = data.small_emojis ?? true
    highContrast.value = data.high_contrast ?? false

    originalSettings.value = {
      currentTheme: currentTheme.value,
      accentColor: accentColor.value,
      useSharedBackground: useSharedBackground.value,
      selectedBackground: selectedBackground.value,
      selectedFont: selectedFont.value,
      fontSize: fontSize.value,
      lineSpacing: lineSpacing.value,
      fontWeight: fontWeight.value,
      smoothAnimations: smoothAnimations.value,
      scrollEffects: scrollEffects.value,
      parallaxEffect: parallaxEffect.value,
      truncateNames: truncateNames.value,
      compactLists: compactLists.value,
      hideAvatars: hideAvatars.value,
      showTimeEverywhere: showTimeEverywhere.value,
      smallEmojis: smallEmojis.value,
      highContrast: highContrast.value,
    }
  } catch (error) {
    console.error('Error fetching theme settings:', error)
  }
}

const saveSettings = async () => {
  try {
    await settingsApi.updateThemeSettings({
      theme: currentTheme.value,
      accent_color: accentColor.value,
      use_shared_background: useSharedBackground.value,
      custom_background: selectedBackground.value,
      smooth_animations: smoothAnimations.value,
      scroll_effects: scrollEffects.value,
      parallax_effect: parallaxEffect.value,
      truncate_names: truncateNames.value,
      compact_lists: compactLists.value,
      hide_avatars: hideAvatars.value,
      show_time_everywhere: showTimeEverywhere.value,
      small_emojis: smallEmojis.value,
      high_contrast: highContrast.value,
    })
    originalSettings.value = {
      currentTheme: currentTheme.value,
      accentColor: accentColor.value,
      useSharedBackground: useSharedBackground.value,
      selectedBackground: selectedBackground.value,
      selectedFont: selectedFont.value,
      fontSize: fontSize.value,
      lineSpacing: lineSpacing.value,
      fontWeight: fontWeight.value,
      smoothAnimations: smoothAnimations.value,
      scrollEffects: scrollEffects.value,
      parallaxEffect: parallaxEffect.value,
      truncateNames: truncateNames.value,
      compactLists: compactLists.value,
      hideAvatars: hideAvatars.value,
      showTimeEverywhere: showTimeEverywhere.value,
      smallEmojis: smallEmojis.value,
      highContrast: highContrast.value,
    }
    showToast('Тема сохранена ✓')
  } catch (error) {
    console.error('Error saving theme settings:', error)
    showToast('Ошибка при сохранении', 'error')
  }
}

const previewSettings = () => {
  // Применяем настройки временно для предпросмотра
  setTheme(currentTheme.value as any)
  setAccentColor(accentColor.value)
  console.log('Preview settings applied')
}

const handleAccentColorChange = async (color: string) => {
  await setAccentColor(color)
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 12px;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.theme-option:hover {
  border-color: var(--primary-color);
}

.theme-option.active {
  border-color: var(--primary-color);
  background: var(--hover-bg);
}

.theme-option input[type="radio"] {
  display: none;
}

.theme-preview {
  width: 80px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.theme-preview.light {
  background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
}

.theme-preview.dark {
  background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
}

.theme-preview.system {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.theme-preview.blue {
  background: linear-gradient(135deg, #0084FF 0%, #0059cc 100%);
}

.theme-preview.green {
  background: linear-gradient(135deg, #00C853 0%, #009624 100%);
}

.preview-header {
  height: 15px;
  background: rgba(0, 0, 0, 0.1);
}

.preview-content {
  padding: 3px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.preview-bubble {
  height: 8px;
  border-radius: 4px;
}

.preview-bubble.user {
  background: var(--primary-color);
  align-self: flex-end;
  width: 70%;
}

.preview-bubble.other {
  background: rgba(255, 255, 255, 0.8);
  align-self: flex-start;
  width: 60%;
}

.color-palette {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 15px;
}

.color-option {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 3px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.color-option.active {
  border-color: var(--text-color);
}

.color-option.custom {
  background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57);
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

.color-picker {
  width: 60px;
  height: 40px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.done-btn {
  padding: 8px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.setting-item {
  margin-bottom: 15px;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
}

.setting-label input[type="checkbox"] {
  margin: 0;
}

.background-selector {
  margin-top: 15px;
}

.background-select {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
  color: var(--text-color);
}

.background-preview {
  margin-top: 15px;
}

.preview-container {
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.preview-container.default {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.preview-chat {
  position: absolute;
  bottom: 10px;
  left: 10px;
  right: 10px;
}

.preview-message {
  padding: 8px 12px;
  border-radius: 12px;
  margin-bottom: 5px;
  font-size: 12px;
  max-width: 70%;
}

.preview-message.user {
  background: rgba(255, 255, 255, 0.9);
  color: #000;
  margin-left: auto;
}

.preview-message.other {
  background: rgba(0, 0, 0, 0.3);
  color: white;
}

.background-actions {
  margin-top: 15px;
}

.action-btn {
  padding: 8px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
}

.font-settings, .effect-settings, .compact-settings {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.font-settings .setting-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.font-select, .weight-select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
  color: var(--text-color);
  min-width: 120px;
}

.size-slider, .spacing-slider {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.slider {
  flex: 1;
  height: 6px;
  background: var(--hover-bg);
  border-radius: 3px;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
}

.contrast-setting {
  margin-top: 15px;
}

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.preview-btn, .save-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.preview-btn {
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
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

.toast-notif {
  position: fixed; top: 24px; right: 24px; z-index: 9999;
  padding: 11px 18px; border-radius: 10px; font-size: 14px; font-weight: 500;
  box-shadow: 0 4px 20px rgba(0,0,0,.3); pointer-events: none;
}
.toast-notif.success { background: #22c55e; color: #fff; }
.toast-notif.error   { background: #ef4444; color: #fff; }
.toast-enter-active, .toast-leave-active { transition: all .25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(-10px); }
</style>