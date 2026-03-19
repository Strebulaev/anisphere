<template>
  <Teleport to="body">
    <div class="gs-backdrop" @click="$emit('close')">
      <div class="gs-modal" @click.stop>

        <div class="gs-header">
          <span class="gs-title">⚙️ Настройки стиля чатов</span>
          <button class="gs-close" @click="$emit('close')">✕</button>
        </div>

        <div class="gs-body">
          <p class="gs-hint">
            Глобальные стилевые настройки применяются ко всем чатам.
            Настройки конкретного чата имеют приоритет над этими.
          </p>

          <!-- Фон -->
          <section class="gs-section">
            <h3 class="gs-section-title">Фон чата</h3>
            <div class="gs-row">
              <label class="gs-label">Тип фона</label>
              <select v-model="form.wallpaper_type" class="gs-select">
                <option value="solid">Сплошной цвет</option>
                <option value="gradient">Градиент</option>
                <option value="pattern">Паттерн</option>
              </select>
            </div>
            <div class="gs-row" v-if="form.wallpaper_type !== 'pattern'">
              <label class="gs-label">Цвет 1</label>
              <input type="color" v-model="form.wallpaper_color" class="gs-color" />
            </div>
            <div class="gs-row" v-if="form.wallpaper_type === 'gradient'">
              <label class="gs-label">Цвет 2</label>
              <input type="color" v-model="form.wallpaper_color2" class="gs-color" />
            </div>
          </section>

          <!-- Пузыри -->
          <section class="gs-section">
            <h3 class="gs-section-title">Пузыри сообщений</h3>
            <div class="gs-row">
              <label class="gs-label">Стиль пузырей</label>
              <div class="gs-radio-group">
                <label v-for="s in bubbleStyles" :key="s.value" class="gs-radio">
                  <input type="radio" :value="s.value" v-model="form.bubble_style" />
                  {{ s.label }}
                </label>
              </div>
            </div>
            <div class="gs-row">
              <label class="gs-label">Акцентный цвет</label>
              <input type="color" v-model="form.accent_color" class="gs-color" />
            </div>
          </section>

          <!-- Шрифт -->
          <section class="gs-section">
            <h3 class="gs-section-title">Текст</h3>
            <div class="gs-row">
              <label class="gs-label">Размер шрифта</label>
              <div class="gs-radio-group">
                <label v-for="s in fontSizes" :key="s.value" class="gs-radio">
                  <input type="radio" :value="s.value" v-model="form.font_size" />
                  {{ s.label }}
                </label>
              </div>
            </div>
            <div class="gs-row">
              <label class="gs-label">Формат времени</label>
              <div class="gs-radio-group">
                <label class="gs-radio"><input type="radio" value="24h" v-model="form.time_format" /> 24ч</label>
                <label class="gs-radio"><input type="radio" value="12h" v-model="form.time_format" /> 12ч</label>
              </div>
            </div>
          </section>

          <!-- Анимации -->
          <section class="gs-section">
            <h3 class="gs-section-title">Анимации</h3>
            <div class="gs-row">
              <label class="gs-label">Появление сообщений</label>
              <select v-model="form.message_animation" class="gs-select">
                <option value="slide">Слайд</option>
                <option value="fade">Затухание</option>
                <option value="pop">Всплытие</option>
                <option value="none">Нет</option>
              </select>
            </div>
          </section>

          <!-- Эмодзи -->
          <section class="gs-section">
            <h3 class="gs-section-title">Эмодзи</h3>
            <div class="gs-row">
              <label class="gs-label">Набор эмодзи</label>
              <select v-model="form.emoji_set" class="gs-select">
                <option value="default">По умолчанию</option>
                <option value="twitter">Twitter (Twemoji)</option>
                <option value="google">Google (Noto)</option>
                <option value="samsung">Samsung</option>
                <option value="anime">Аниме</option>
              </select>
            </div>
          </section>
        </div>

        <div class="gs-footer">
          <button class="gs-btn-reset" @click="resetDefaults">Сбросить</button>
          <button class="gs-btn-save" @click="save" :disabled="saving">
            {{ saving ? 'Сохранение…' : 'Сохранить' }}
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const emit = defineEmits<{ close: [] }>()

const saving = ref(false)

const DEFAULTS = {
  wallpaper_type: 'solid',
  wallpaper_color: '#0f0f0f',
  wallpaper_color2: '#1a1a2e',
  bubble_style: 'modern',
  accent_color: '#6C5CE7',
  font_size: 'medium',
  message_animation: 'slide',
  emoji_set: 'default',
  time_format: '24h',
}

const form = ref({ ...DEFAULTS })

const bubbleStyles = [
  { value: 'modern',  label: 'Современный' },
  { value: 'classic', label: 'Классический' },
  { value: 'rounded', label: 'Округлый' },
]
const fontSizes = [
  { value: 'small',  label: 'Маленький' },
  { value: 'medium', label: 'Средний'   },
  { value: 'large',  label: 'Большой'   },
]

const load = async () => {
  try {
    const { data } = await apiClient.get('/social/chat-settings/global/')
    if (data) form.value = { ...DEFAULTS, ...data }
  } catch { /* используем defaults */ }
}

const save = async () => {
  saving.value = true
  try {
    await apiClient.put('/social/chat-settings/global/', form.value)
    // Сохраняем локально для клиентского применения
    localStorage.setItem('globalChatStyle', JSON.stringify(form.value))
    emit('close')
  } catch (e) {
    console.error('Ошибка сохранения глобального стиля:', e)
    // Сохраняем хотя бы локально
    localStorage.setItem('globalChatStyle', JSON.stringify(form.value))
    emit('close')
  } finally {
    saving.value = false
  }
}

const resetDefaults = () => {
  form.value = { ...DEFAULTS }
}

onMounted(load)
</script>

<style scoped>
.gs-backdrop {
  position: fixed; inset: 0; z-index: 10000;
  background: rgba(0,0,0,.6);
  display: flex; align-items: center; justify-content: center;
  padding: 1rem;
}
.gs-modal {
  background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 16px;
  width: 100%; max-width: 460px; max-height: 90vh;
  display: flex; flex-direction: column;
  box-shadow: 0 12px 40px rgba(0,0,0,.6);
}
.gs-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid #2a2a2a; flex-shrink: 0;
}
.gs-title { color: #e0e0e0; font-weight: 700; font-size: 1rem; }
.gs-close  { background: none; border: none; color: #666; cursor: pointer; font-size: 1.1rem; }
.gs-body   { flex: 1; overflow-y: auto; padding: 16px 20px; display: flex; flex-direction: column; gap: 16px; }
.gs-hint   { color: #666; font-size: .8rem; line-height: 1.5; margin: 0; }

.gs-section { display: flex; flex-direction: column; gap: 10px; }
.gs-section-title { font-size: .75rem; font-weight: 700; color: #888; text-transform: uppercase; letter-spacing: .06em; margin: 0; }
.gs-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.gs-label { color: #ccc; font-size: .875rem; flex-shrink: 0; }
.gs-select {
  background: #111; border: 1px solid #333; border-radius: 6px;
  color: #ddd; padding: 5px 8px; font-size: .85rem; cursor: pointer;
}
.gs-color { width: 40px; height: 30px; border: none; border-radius: 6px; cursor: pointer; padding: 2px; background: transparent; }
.gs-radio-group { display: flex; gap: 12px; flex-wrap: wrap; }
.gs-radio { display: flex; align-items: center; gap: 5px; color: #ccc; font-size: .85rem; cursor: pointer; }
.gs-radio input { accent-color: #6C5CE7; }

.gs-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 14px 20px; border-top: 1px solid #2a2a2a; flex-shrink: 0;
}
.gs-btn-reset {
  background: #111; border: 1px solid #333; color: #888; border-radius: 8px;
  padding: 8px 16px; cursor: pointer; font-size: .875rem;
}
.gs-btn-reset:hover { background: #1a1a1a; color: #ccc; }
.gs-btn-save {
  background: #6C5CE7; border: none; color: #fff; border-radius: 8px;
  padding: 8px 20px; cursor: pointer; font-weight: 600; font-size: .875rem;
}
.gs-btn-save:hover:not(:disabled) { background: #5a4bd4; }
.gs-btn-save:disabled { opacity: .5; cursor: not-allowed; }
</style>
