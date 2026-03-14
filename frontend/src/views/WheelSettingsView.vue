<template>
  <div class="wheel-settings-view">
    <div class="page-header">
      <router-link to="/wheel" class="btn-back">← Назад</router-link>
      <h1>⚙️ Настройки колеса</h1>
    </div>

    <div v-if="currentRoulette" class="settings-content">
      <!-- Внешний вид -->
      <section class="settings-section">
        <h2>🎨 Внешний вид</h2>
        <div class="settings-grid">
          <div class="setting-item">
            <label>Тема колеса</label>
            <select v-model="settings.theme" @change="saveSettings">
              <option value="light">🌞 Светлая</option>
              <option value="dark">🌙 Тёмная</option>
              <option value="anime">🎨 Аниме-тема</option>
            </select>
          </div>

          <div class="setting-item">
            <label>Размер колеса</label>
            <select v-model="settings.wheel_size" @change="saveSettings">
              <option value="small">Малый (300px)</option>
              <option value="medium">Средний (400px)</option>
              <option value="large">Большой (500px)</option>
            </select>
          </div>

          <div class="setting-item">
            <label>Отображение</label>
            <select v-model="settings.display_mode" @change="saveSettings">
              <option value="posters">🖼️ Постеры</option>
              <option value="titles">📝 Названия</option>
              <option value="both">🖼️+📝 И то и другое</option>
            </select>
          </div>

          <div class="setting-item">
            <label>Цветовая схема</label>
            <select v-model="settings.color_scheme" @change="saveSettings">
              <option value="rainbow">🌈 Радуга</option>
              <option value="rating">🎯 По рейтингу</option>
              <option value="monochrome">🎨 Монохром</option>
            </select>
          </div>

          <div class="setting-item">
            <label>Анимация кручения</label>
            <select v-model="settings.animation_style" @change="saveSettings">
              <option value="smooth">💫 Плавная</option>
              <option value="fast">⚡ Быстрая</option>
              <option value="cinematic">🎬 Кинематографичная</option>
            </select>
          </div>

          <div class="setting-item">
            <label>Звук при кручении</label>
            <div class="toggle-group">
              <button
                :class="['toggle-btn', { active: settings.sound_enabled }]"
                @click="settings.sound_enabled = true; saveSettings()"
              >
                🔊 Вкл
              </button>
              <button
                :class="['toggle-btn', { active: !settings.sound_enabled }]"
                @click="settings.sound_enabled = false; saveSettings()"
              >
                🔇 Выкл
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Поведение -->
      <section class="settings-section">
        <h2>🎲 Поведение</h2>
        <div class="settings-grid">
          <div class="setting-item">
            <label>Количество по умолчанию</label>
            <input
              v-model.number="settings.default_spin_count"
              type="number"
              min="1"
              max="50"
              @change="saveSettings"
              class="number-input"
            >
          </div>

          <div class="setting-item">
            <label>Расчёт весов</label>
            <select v-model="settings.weight_mode" @change="saveSettings">
              <option value="proportional">⚖️ Пропорционально</option>
              <option value="rating">🎯 Только рейтинг</option>
              <option value="manual">📊 Ручные</option>
            </select>
          </div>

          <div class="setting-item">
            <label>Исключать недавно выпавшие</label>
            <div class="toggle-group">
              <button
                :class="['toggle-btn', { active: settings.exclude_recent }]"
                @click="settings.exclude_recent = true; saveSettings()"
              >
                🔄 Да
              </button>
              <button
                :class="['toggle-btn', { active: !settings.exclude_recent }]"
                @click="settings.exclude_recent = false; saveSettings()"
              >
                ❌ Нет
              </button>
            </div>
          </div>

          <div v-if="settings.exclude_recent" class="setting-item">
            <label>Период исключения</label>
            <select v-model.number="settings.exclusion_period" @change="saveSettings">
              <option :value="1">1 день</option>
              <option :value="3">3 дня</option>
              <option :value="7">7 дней</option>
              <option :value="30">30 дней</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Лимиты -->
      <section class="settings-section">
        <h2>📊 Лимиты</h2>
        <div class="settings-grid">
          <div class="setting-item">
            <label>Максимум аниме в колесе</label>
            <select v-model.number="settings.max_items" @change="saveSettings">
              <option :value="50">50</option>
              <option :value="100">100</option>
              <option :value="200">200</option>
              <option :value="9999">Без лимита</option>
            </select>
          </div>

          <div class="setting-item">
            <label>Максимум аниме за раз</label>
            <select v-model.number="settings.max_spin_items" @change="saveSettings">
              <option :value="10">10</option>
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="9999">Без лимита</option>
            </select>
          </div>

          <div class="setting-item">
            <label>Сохранять историю</label>
            <select v-model.number="settings.history_limit" @change="saveSettings">
              <option :value="100">Да, 100 записей</option>
              <option :value="500">Да, 500 записей</option>
              <option :value="0">❌ Нет</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Автоматическое добавление -->
      <section class="settings-section">
        <h2>🔄 Автоматическое добавление</h2>
        <div class="settings-grid">
          <div class="setting-item">
            <label>Из коллекции</label>
            <div class="toggle-group">
              <button
                :class="['toggle-btn', { active: settings.auto_add_from_collection }]"
                @click="settings.auto_add_from_collection = true; saveSettings()"
              >
                📚 Да
              </button>
              <button
                :class="['toggle-btn', { active: !settings.auto_add_from_collection }]"
                @click="settings.auto_add_from_collection = false; saveSettings()"
              >
                ❌ Нет
              </button>
            </div>
          </div>

          <div class="setting-item">
            <label>Из плейлистов</label>
            <div class="toggle-group">
              <button
                :class="['toggle-btn', { active: settings.auto_add_from_playlists }]"
                @click="settings.auto_add_from_playlists = true; saveSettings()"
              >
                📁 Да
              </button>
              <button
                :class="['toggle-btn', { active: !settings.auto_add_from_playlists }]"
                @click="settings.auto_add_from_playlists = false; saveSettings()"
              >
                ❌ Нет
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Сохранённые наборы -->
      <section class="settings-section">
        <h2>💾 Сохранённые наборы</h2>
        <div class="presets-grid">
          <div
            v-for="preset in presets"
            :key="preset.id"
            class="preset-card"
          >
            <div class="preset-icon">📁</div>
            <div class="preset-info">
              <h3>{{ preset.name }}</h3>
              <p>{{ preset.items_count }} аниме</p>
            </div>
            <div class="preset-actions">
              <button class="btn-icon-sm" @click="applyPreset(preset.id)" title="Применить">
                ↻
              </button>
              <button class="btn-icon-sm" @click="editPreset(preset.id)" title="Редактировать">
                ✎
              </button>
              <button class="btn-icon-sm btn-danger" @click="deletePreset(preset.id)" title="Удалить">
                ✖️
              </button>
            </div>
          </div>
        </div>

        <div class="presets-actions">
          <button class="btn-secondary" @click="saveCurrentAsPreset">
            ➕ Сохранить текущий набор
          </button>
          <button class="btn-secondary" @click="exportPresets">
            📤 Экспорт
          </button>
          <button class="btn-secondary" @click="importPresets">
            📥 Импорт
          </button>
        </div>
      </section>
    </div>

    <!-- Сохранение -->
    <div class="save-indicator" :class="{ visible: isSaving }">
      💾 Сохранение...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { rouletteApi, type RouletteSettings, type RoulettePreset } from '@/api/roulette'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const toast = useToast()

const currentRoulette = ref<any>(null)
const presets = ref<RoulettePreset[]>([])
const isSaving = ref(false)

const settings = reactive<RouletteSettings>({
  theme: 'dark',
  wheel_size: 'medium',
  display_mode: 'both',
  color_scheme: 'rainbow',
  animation_style: 'smooth',
  sound_enabled: true,
  sound_type: 'default',
  default_spin_count: 1,
  weight_mode: 'proportional',
  exclude_recent: false,
  exclusion_period: 7,
  max_items: 50,
  max_spin_items: 10,
  history_limit: 100,
  auto_add_from_collection: false,
  auto_add_from_playlists: false
})

// Загрузка настроек
const loadSettings = async () => {
  try {
    // Загружаем первую рулетку пользователя
    const { data: roulettes } = await rouletteApi.getRoulettes()
    if (roulettes.length > 0) {
      currentRoulette.value = roulettes[0]
      const { data } = await rouletteApi.getSettings(currentRoulette.value.id)
      Object.assign(settings, data)
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
    toast.error('Ошибка загрузки настроек')
  }
}

// Сохранение настроек
const saveSettings = async () => {
  if (!currentRoulette.value) return

  isSaving.value = true

  try {
    await rouletteApi.updateSettings(currentRoulette.value.id, settings)
    setTimeout(() => {
      isSaving.value = false
    }, 500)
  } catch (error) {
    console.error('Failed to save settings:', error)
    toast.error('Ошибка сохранения')
    isSaving.value = false
  }
}

// Загрузка пресетов
const loadPresets = async () => {
  try {
    const { data } = await rouletteApi.getPresets()
    presets.value = data
  } catch (error) {
    console.error('Failed to load presets:', error)
  }
}

// Применить пресет
const applyPreset = async (presetId: string) => {
  if (!currentRoulette.value) return

  try {
    await rouletteApi.applyPreset(presetId, currentRoulette.value.id)
    toast.success('Пресет применён')
    // Перезагружаем рулетку
    await loadSettings()
  } catch (error) {
    console.error('Failed to apply preset:', error)
    toast.error('Ошибка применения пресета')
  }
}

// Редактировать пресет
const editPreset = (presetId: string) => {
  // TODO: Реализовать редактирование пресета
  toast.info('Редактирование пресета')
}

// Удалить пресет
const deletePreset = async (presetId: string) => {
  if (!confirm('Удалить пресет?')) return

  try {
    await rouletteApi.deletePreset(presetId)
    presets.value = presets.value.filter(p => p.id !== presetId)
    toast.success('Пресет удалён')
  } catch (error) {
    console.error('Failed to delete preset:', error)
    toast.error('Ошибка удаления пресета')
  }
}

// Сохранить текущий набор как пресет
const saveCurrentAsPreset = async () => {
  if (!currentRoulette.value) return

  const name = prompt('Название набора:')
  if (!name) return

  try {
    const itemsData = currentRoulette.value.items.map((item: any) => ({
      anime_id: item.anime_id,
      anime_title: item.anime_title,
      anime_poster: item.anime_poster,
      weight: item.weight,
      color: item.color
    }))

    await rouletteApi.createPreset({
      name,
      items_data: itemsData,
      settings_snapshot: { ...settings },
      is_public: false
    })

    await loadPresets()
    toast.success('Набор сохранён')
  } catch (error) {
    console.error('Failed to save preset:', error)
    toast.error('Ошибка сохранения набора')
  }
}

// Экспорт пресетов
const exportPresets = () => {
  const data = JSON.stringify(presets.value, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'wheel-presets.json'
  a.click()
  URL.revokeObjectURL(url)
  toast.success('Пресеты экспортированы')
}

// Импорт пресетов
const importPresets = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      const data = JSON.parse(text)

      for (const preset of data) {
        await rouletteApi.createPreset(preset)
      }

      await loadPresets()
      toast.success('Пресеты импортированы')
    } catch (error) {
      console.error('Failed to import presets:', error)
      toast.error('Ошибка импорта')
    }
  }
  input.click()
}

onMounted(() => {
  loadSettings()
  loadPresets()
})
</script>

<style scoped>
.wheel-settings-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.btn-back {
  color: #888;
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.btn-back:hover {
  color: #fff;
}

.page-header h1 {
  color: #fff;
  font-size: 1.5rem;
  margin: 0;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.settings-section {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1.5rem;
}

.settings-section h2 {
  color: #fff;
  font-size: 1.1rem;
  margin: 0 0 1.5rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #2a2a2a;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-item label {
  color: #888;
  font-size: 0.9rem;
}

.setting-item select,
.setting-item input {
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  color: #fff;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.95rem;
}

.setting-item select:focus,
.setting-item input:focus {
  outline: none;
  border-color: #667eea;
}

.number-input {
  width: 100px;
}

.toggle-group {
  display: flex;
  gap: 0.5rem;
}

.toggle-btn {
  flex: 1;
  background: #2a2a2a;
  border: 1px solid #2a2a2a;
  color: #888;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background: #3a3a3a;
}

.toggle-btn.active {
  background: #667eea;
  border-color: #667eea;
  color: #fff;
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.preset-card {
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.preset-icon {
  font-size: 2rem;
}

.preset-info {
  flex: 1;
}

.preset-info h3 {
  color: #fff;
  font-size: 1rem;
  margin: 0 0 0.25rem 0;
}

.preset-info p {
  color: #888;
  font-size: 0.85rem;
  margin: 0;
}

.preset-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon-sm {
  width: 32px;
  height: 32px;
  background: #2a2a2a;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.btn-icon-sm:hover {
  background: #3a3a3a;
}

.btn-icon-sm.btn-danger:hover {
  background: #dc2626;
}

.presets-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn-secondary {
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #3a3a3a;
  border-color: #667eea;
}

.save-indicator {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: #667eea;
  color: #fff;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.9rem;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.3s;
}

.save-indicator.visible {
  opacity: 1;
  transform: translateY(0);
}

@media (max-width: 600px) {
  .wheel-settings-view {
    padding: 1rem;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }

  .presets-grid {
    grid-template-columns: 1fr;
  }

  .presets-actions {
    flex-direction: column;
  }

  .btn-secondary {
    width: 100%;
  }
}
</style>
