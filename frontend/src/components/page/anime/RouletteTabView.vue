<template>
  <div class="roulette-page">
    <!-- Заголовок -->
    <div class="rp-header">
      <div class="rp-header-content">
        <div class="rp-title-section">
          <span class="rp-icon">🎰</span>
          <div>
            <h1 class="rp-title">Колесо Фортуны</h1>
            <p class="rp-subtitle">Испытай удачу и выбери аниме для просмотра!</p>
          </div>
        </div>
        <div class="rp-header-actions">
          <button class="rp-btn rp-btn-secondary" @click="createNewRoulette" title="Создать новую">
            <SakuraIcon name="plus" :size="18" />
            <span>Новая</span>
          </button>
          <button class="rp-btn rp-btn-secondary" @click="importFromCollection" title="Импортировать из коллекции">
            <SakuraIcon name="download" :size="18" />
            <span>Импорт</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Выбор рулетки -->
    <div class="rp-roulette-selector">
      <div class="rp-selector-card">
        <label class="rp-selector-label">Выберите рулетку</label>
        <div class="rp-selector-wrapper">
          <select v-model="selectedRouletteId" @change="loadRoulette" class="rp-select">
            <option value="">+ Создать новую рулетку</option>
            <option v-for="r in roulettes" :key="r.id" :value="r.id">
              {{ r.name }} — {{ r.items_count }} аниме
            </option>
          </select>
          <div class="rp-selector-actions">
            <button 
              v-if="selectedRouletteId && !selectedRouletteId.startsWith('local-')" 
              class="rp-icon-btn rp-btn-danger" 
              @click="deleteRoulette" 
              title="Удалить рулетку"
            >
              <SakuraIcon name="trash" :size="18" />
            </button>
            <button 
              v-if="currentRoulette?.items?.length" 
              class="rp-icon-btn rp-btn-warning" 
              @click="clearRoulette" 
              title="Очистить все элементы"
            >
              🧹
            </button>
          </div>
        </div>
      </div>
      
      <!-- Статистика -->
      <div v-if="currentRoulette" class="rp-stats-card">
        <div class="rp-stat">
          <span class="rp-stat-value">{{ currentRoulette.items_count || 0 }}</span>
          <span class="rp-stat-label">Аниме</span>
        </div>
        <div class="rp-stat-divider"></div>
        <div class="rp-stat">
          <span class="rp-stat-value">{{ currentRoulette.total_weight || 0 }}</span>
          <span class="rp-stat-label">Общий вес</span>
        </div>
        <div class="rp-stat-divider"></div>
        <div class="rp-stat">
          <span class="rp-stat-value">{{ currentRoulette.spin_duration || 5 }}с</span>
          <span class="rp-stat-label">Время вращения</span>
        </div>
      </div>
    </div>
    
    <!-- Настройки -->
    <div v-if="currentRoulette" class="rp-settings-panel">
      <div class="rp-settings-row">
        <div class="rp-setting-group">
          <label class="rp-setting-label">
            <SakuraIcon name="edit" :size="16" />
            Название
          </label>
          <input
            v-model="currentRoulette.name"
            type="text"
            class="rp-input"
            placeholder="Название рулетки"
            @blur="updateRoulette"
          >
        </div>
        
        <div class="rp-setting-group">
          <label class="rp-setting-label">
            <SakuraIcon name="clock" :size="16" />
            Время вращения
          </label>
          <div class="rp-input-with-suffix">
            <input
              v-model.number="currentRoulette.spin_duration"
              type="number"
              min="3"
              max="15"
              class="rp-input rp-input-sm"
              @blur="updateRoulette"
            >
            <span class="rp-suffix">сек</span>
          </div>
        </div>
        
        <div class="rp-setting-group">
          <label class="rp-setting-label">
            <SakuraIcon name="chart" :size="16" />
            Режим весов
          </label>
          <select v-model="weightMode" @change="weightModeChanged" class="rp-select rp-select-sm">
            <option value="equal">⚖️ Равные</option>
            <option value="manual">🎯 Вручную</option>
            <option value="score">⭐ По рейтингу</option>
          </select>
        </div>
      </div>
      
      <div class="rp-settings-row">
        <div class="rp-setting-group">
          <label class="rp-setting-label">
            <SakuraIcon name="layers" :size="16" />
            Размер колеса
          </label>
          <select v-model="currentRoulette.wheel_size" @change="updateRoulette" class="rp-select rp-select-sm">
            <option value="small">Маленькое (300px)</option>
            <option value="medium">Среднее (400px)</option>
            <option value="large">Большое (500px)</option>
          </select>
        </div>
        
        <div class="rp-setting-group">
          <label class="rp-setting-label">
            <SakuraIcon name="palette" :size="16" />
            Цветовая схема
          </label>
          <select v-model="currentRoulette.color_scheme" @change="updateRoulette" class="rp-select rp-select-sm">
            <option value="rainbow">🌈 Радуга</option>
            <option value="dark">🌙 Тёмная</option>
            <option value="pastel">🎨 Пастель</option>
            <option value="neon">💜 Неон</option>
          </select>
        </div>
      </div>
    </div>
    
    <!-- Панель элементов с весами -->
    <div v-if="currentRoulette?.items?.length" class="rp-items-panel">
      <div class="rp-items-header">
        <div class="rp-items-title">
          <SakuraIcon name="list" :size="18" />
          <span>Элементы колеса</span>
          <span class="rp-badge">{{ currentRoulette.items.length }}</span>
        </div>
        <div class="rp-items-stats">
          <span class="rp-stat-pill">
            <span class="rp-stat-pill-value">{{ currentRoulette.total_weight }}</span>
            <span class="rp-stat-pill-label">вес</span>
          </span>
          <span class="rp-stat-pill">
            <span class="rp-stat-pill-value">{{ Math.round((currentRoulette.total_weight / currentRoulette.items.length) * 10) / 10 }}</span>
            <span class="rp-stat-pill-label">средний</span>
          </span>
        </div>
      </div>
      
      <div class="rp-items-scroll">
        <div class="rp-items-list">
          <div
            v-for="(item, index) in currentRoulette.items"
            :key="item.id"
            class="rp-item"
            :style="{ borderLeftColor: item.color }"
          >
            <span class="rp-item-index">{{ index + 1 }}</span>
            <img
              v-if="item.anime_poster"
              :src="item.anime_poster"
              :alt="item.anime_title"
              class="rp-item-poster"
              @error="handleImageError"
            >
            <div class="rp-item-poster-placeholder" v-else>
              <SakuraIcon name="play" :size="20" />
            </div>
            <div class="rp-item-info">
              <div class="rp-item-title">{{ item.anime_title }}</div>
              <div class="rp-item-meta">
                <span :style="{ color: item.color }" class="rp-weight-dot">●</span>
                <span class="rp-weight-percent">{{ Math.round((item.weight / (currentRoulette.total_weight || 1)) * 100) }}%</span>
                <span class="rp-weight-value">вес: {{ item.weight }}</span>
              </div>
            </div>
            <div class="rp-item-weight">
              <input
                v-if="weightMode === 'manual'"
                type="number"
                :value="item.weight"
                min="1"
                max="100"
                class="rp-weight-input"
                @change="(e) => updateWeight(item.id, Number((e.target as HTMLInputElement).value))"
              >
              <div v-else class="rp-weight-bar">
                <div 
                  class="rp-weight-fill" 
                  :style="{ width: `${(item.weight / (currentRoulette.total_weight || 1)) * 100}%`, backgroundColor: item.color }"
                ></div>
              </div>
            </div>
            <button class="rp-item-remove" @click="removeItem(item.id)" title="Удалить">
              <SakuraIcon name="trash" :size="16" />
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="rp-main-content">
      <!-- Колесо -->
      <div class="rp-wheel-section">
        <div class="rp-wheel-card">
          <FortuneWheel
            :items="currentRoulette?.items || []"
            :total-weight="currentRoulette?.total_weight || 0"
            :is-spinning="isSpinning"
            :rotation-angle="rotationAngle"
            :winner="winner"
            :size="getWheelSize"
            @spin="spin"
          />
          
          <!-- Кнопка вращения -->
          <div class="rp-spin-control">
            <button
              v-if="!isSpinning"
              class="rp-spin-btn"
              :disabled="!currentRoulette?.items?.length"
              @click="spin"
            >
              <span class="rp-spin-icon">🎰</span>
              <span class="rp-spin-text">
                {{ currentRoulette?.items?.length ? 'Крутить колесо!' : 'Добавьте аниме' }}
              </span>
            </button>
            <div v-else class="rp-spinning-indicator">
              <div class="rp-spinner"></div>
              <span>Вращение...</span>
            </div>
          </div>
          
          <!-- Результат -->
          <transition name="rp-result-fade">
            <div v-if="winner && !isSpinning" class="rp-result-panel">
              <div class="rp-result-header">
                <span class="rp-result-icon">🎉</span>
                <span class="rp-result-title">Выпало:</span>
              </div>
              <div class="rp-result-content">
                <img
                  v-if="winner.anime_poster"
                  :src="winner.anime_poster"
                  :alt="winner.anime_title"
                  class="rp-result-poster"
                >
                <div class="rp-result-poster-placeholder" v-else>
                  <SakuraIcon name="play" :size="40" />
                </div>
                <div class="rp-result-info">
                  <h3 class="rp-result-title-text">{{ winner.anime_title }}</h3>
                  <div class="rp-result-meta">
                    <span class="rp-result-weight">Вес: {{ winner.weight }}</span>
                    <span class="rp-result-chance">{{ Math.round((winner.weight / (currentRoulette?.total_weight || 1)) * 100) }}% шанс</span>
                  </div>
                </div>
              </div>
              <button class="rp-result-action" @click="watchAnime(winner)">
                <SakuraIcon name="play" :size="16" />
                Смотреть
              </button>
            </div>
          </transition>
        </div>
      </div>
      
      <!-- Менеджер элементов -->
      <div class="rp-manager-section">
        <div class="rp-manager-card">
          <div class="rp-manager-header">
            <h3 class="rp-manager-title">
              <SakuraIcon name="search" :size="20" />
              Добавить аниме
            </h3>
          </div>
          <AnimeSelector
            :current-items="currentRoulette?.items || []"
            @add="handleAddItems"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { rouletteApi, type Roulette, type RouletteItem } from '@/api/roulette'
import FortuneWheel from '@/components/roulette/FortuneWheel.vue'
import AnimeSelector from '@/components/roulette/AnimeSelector.vue'
import { useToast } from '@/composables/useToast'

const toast = useToast()

// LocalStorage ключи
const STORAGE_KEY = 'anisphere_roulette'
const ROULETTES_KEY = 'anisphere_roulettes_list'

const roulettes = ref<Roulette[]>([])
const selectedRouletteId = ref('')
const currentRoulette = ref<Roulette | null>(null)
const isSpinning = ref(false)
const rotationAngle = ref(0)
const winner = ref<RouletteItem | null>(null)
const weightMode = ref<'equal' | 'manual' | 'score'>('equal')

// Вычисляемый размер колеса
const getWheelSize = computed(() => {
  if (!currentRoulette.value?.wheel_size) return 400
  const sizes: Record<string, number> = {
    small: 300,
    medium: 400,
    large: 500
  }
  return sizes[currentRoulette.value.wheel_size] || 400
})

// Сохранение в localStorage
const saveToStorage = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      selectedRouletteId: selectedRouletteId.value,
      currentRoulette: currentRoulette.value,
      weightMode: weightMode.value
    }))
  } catch (e) {
    console.error('Failed to save to localStorage:', e)
  }
}

// Загрузка из localStorage
const loadFromStorage = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const data = JSON.parse(saved)
      selectedRouletteId.value = data.selectedRouletteId || ''
      currentRoulette.value = data.currentRoulette || null
      weightMode.value = data.weightMode || 'equal'
      return true
    }
  } catch (e) {
    console.error('Failed to load from localStorage:', e)
  }
  return false
}

// Обработка ошибки изображения
const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
}

const loadRoulettes = async () => {
  try {
    const response = await rouletteApi.getRoulettes()
    const data = response.data || []
    roulettes.value = Array.isArray(data) ? data : []
    
    // Если есть сохранённая рулетка, используем её
    if (!selectedRouletteId.value && roulettes.value.length > 0) {
      const firstRoulette = roulettes.value[0]
      if (firstRoulette?.id) {
        selectedRouletteId.value = firstRoulette.id
      }
    }
    
    if (selectedRouletteId.value) {
      await loadRoulette()
    } else {
      // Пробуем загрузить из localStorage
      if (!loadFromStorage()) {
        // Создаём новую рулетку если ничего нет
        await createNewRoulette()
      }
    }
  } catch (error) {
    console.error('Failed to load roulettes:', error)
    // Используем localStorage как fallback
    if (!loadFromStorage()) {
      // Создаём локальную рулетку
      createLocalRoulette()
    }
  }
}

const createLocalRoulette = () => {
  const localId = `local-${Date.now()}`
  currentRoulette.value = {
    id: localId,
    name: 'Моя рулетка',
    spin_duration: 5,
    items: [],
    total_weight: 0,
    items_count: 0,
    wheel_size_px: 400,
    last_result: null,
    last_spin_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    theme: 'dark',
    wheel_size: 'medium',
    display_mode: 'titles',
    color_scheme: 'rainbow',
    animation_style: 'smooth',
    sound_enabled: true,
    sound_type: 'click',
    default_spin_count: 1,
    weight_mode: 'equal',
    exclude_recent: false,
    exclusion_period: 7,
    max_items: 50,
    max_spin_items: 10,
    history_limit: 100,
    auto_add_from_collection: false,
    auto_add_from_playlists: false
  }
  selectedRouletteId.value = localId
  saveToStorage()
}

const importFromCollection = async () => {
  if (!currentRoulette.value) {
    toast.error('Сначала создайте или выберите рулетку')
    return
  }
  
  try {
    // Здесь будет логика импорта из коллекции
    // Для простоты - переключаем на вкладку коллекции в AnimeSelector
    toast.info('Перейдите во вкладку "Коллекция" для добавления аниме')
  } catch (error) {
    console.error('Import from collection failed:', error)
    toast.error('Ошибка импорта')
  }
}

const createNewRoulette = async () => {
  try {
    const response = await rouletteApi.createRoulette({
      name: 'Моя рулетка',
      spin_duration: 5
    })
    const data = response.data
    if (data && data.id) {
      roulettes.value.unshift(data)
      selectedRouletteId.value = data.id
      currentRoulette.value = data
      saveToStorage()
    }
  } catch (error) {
    console.error('Failed to create roulette:', error)
    // Создаём локальную
    createLocalRoulette()
  }
}

const loadRoulette = async () => {
  // Проверяем локальную рулетку
  if (selectedRouletteId.value.startsWith('local-')) {
    loadFromStorage()
    return
  }
  
  if (!selectedRouletteId.value) {
    await createNewRoulette()
    return
  }
  
  try {
    const response = await rouletteApi.getRoulette(selectedRouletteId.value)
    currentRoulette.value = response.data || null
    saveToStorage()
  } catch (error) {
    console.error('Failed to load roulette:', error)
    // Пробуем localStorage
    if (!loadFromStorage()) {
      createLocalRoulette()
    }
  }
}

const updateRoulette = async () => {
  if (!currentRoulette.value) return
  
  // Если локальная рулетка
  if (currentRoulette.value.id.startsWith('local-')) {
    saveToStorage()
    return
  }
  
  try {
    await rouletteApi.updateRoulette(currentRoulette.value.id, {
      name: currentRoulette.value.name,
      spin_duration: currentRoulette.value.spin_duration
    })
    saveToStorage()
  } catch (error) {
    console.error('Failed to update roulette:', error)
  }
}

const deleteRoulette = async () => {
  if (!selectedRouletteId.value) return
  if (!confirm('Удалить рулетку?')) return
  
  // Локальная рулетка
  if (selectedRouletteId.value.startsWith('local-')) {
    localStorage.removeItem(STORAGE_KEY)
    currentRoulette.value = null
    selectedRouletteId.value = ''
    createLocalRoulette()
    return
  }
  
  try {
    await rouletteApi.deleteRoulette(selectedRouletteId.value)
    roulettes.value = roulettes.value.filter(r => r.id !== selectedRouletteId.value)
    selectedRouletteId.value = ''
    currentRoulette.value = null
    localStorage.removeItem(STORAGE_KEY)
    
    if (roulettes.value.length > 0 && roulettes.value[0]) {
      selectedRouletteId.value = roulettes.value[0].id
      await loadRoulette()
    } else {
      createLocalRoulette()
    }
  } catch (error) {
    console.error('Failed to delete roulette:', error)
  }
}

const handleAddItems = async (newItems: Array<{ anime_id: number; anime_title: string; anime_poster?: string; weight: number }>) => {
  // Локальная рулетка - добавляем локально
  if (!currentRoulette.value || currentRoulette.value.id.startsWith('local-')) {
    if (!currentRoulette.value) {
      createLocalRoulette()
    }
    
    const roulette = currentRoulette.value
    if (!roulette) return
    
    const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7', '#fa709a', '#fee140']
    const startIndex = roulette.items?.length ?? 0
    
    for (let i = 0; i < newItems.length; i++) {
      const anime = newItems[i]
      if (!anime) continue
      
      const newItem: RouletteItem = {
        id: `local-item-${Date.now()}-${i}`,
        anime_id: anime.anime_id,
        anime_title: anime.anime_title || `Аниме ${anime.anime_id}`,
        anime_poster: anime.anime_poster || null,
        weight: weightMode.value === 'score' ? Math.round(anime.weight * 2) : (anime.weight || 1),
        color: colors[(startIndex + i) % colors.length] ?? '#667eea',
        order: startIndex + i + 1,
        created_at: new Date().toISOString()
      }
      
      if (!roulette.items) {
        roulette.items = []
      }
      roulette.items.push(newItem)
      roulette.total_weight = (roulette.total_weight || 0) + newItem.weight
      roulette.items_count = (roulette.items_count || 0) + 1
    }
    
    saveToStorage()
    toast.success(`Добавлено ${newItems.length} аниме`)
    return
  }
  
  // Серверная рулетка
  const roulette = currentRoulette.value
  for (const anime of newItems) {
    if (!anime) continue
    try {
      const response = await rouletteApi.addItem(roulette.id, {
        anime_id: anime.anime_id,
        anime_title: anime.anime_title || `Аниме ${anime.anime_id}`,
        anime_poster: anime.anime_poster,
        weight: weightMode.value === 'score' ? Math.round(anime.weight * 2) : (anime.weight || 1)
      })
      const data = response.data
      if (data && roulette) {
        if (!roulette.items) {
          roulette.items = []
        }
        roulette.items.push(data)
        roulette.total_weight = (roulette.total_weight || 0) + data.weight
        roulette.items_count = (roulette.items_count || 0) + 1
      }
    } catch (error) {
      console.error('Failed to add item:', error)
    }
  }
  saveToStorage()
}

const removeItem = async (itemId: string) => {
  if (!currentRoulette.value) return
  
  // Локальная рулетка
  if (currentRoulette.value.id.startsWith('local-')) {
    if (currentRoulette.value.items) {
      const item = currentRoulette.value.items.find(i => i.id === itemId)
      if (item) {
        currentRoulette.value.total_weight = (currentRoulette.value.total_weight || 0) - item.weight
      }
      currentRoulette.value.items = currentRoulette.value.items.filter(i => i.id !== itemId)
      currentRoulette.value.items_count = Math.max(0, (currentRoulette.value.items_count || 1) - 1)
    }
    saveToStorage()
    return
  }
  
  try {
    await rouletteApi.removeItem(currentRoulette.value.id, itemId)
    if (currentRoulette.value.items) {
      const item = currentRoulette.value.items.find(i => i.id === itemId)
      if (item && currentRoulette.value.total_weight !== undefined) {
        currentRoulette.value.total_weight -= item.weight
      }
      currentRoulette.value.items = currentRoulette.value.items.filter(i => i.id !== itemId)
      currentRoulette.value.items_count = Math.max(0, (currentRoulette.value.items_count || 1) - 1)
    }
    saveToStorage()
  } catch (error) {
    console.error('Failed to remove item:', error)
  }
}

const updateWeight = async (itemId: string, weight: number) => {
  if (!currentRoulette.value?.items) return
  
  const item = currentRoulette.value.items.find(i => i.id === itemId)
  if (!item) return
  
  const oldWeight = item.weight
  const newWeight = Math.max(1, Math.min(100, weight))
  
  // Локальная рулетка
  if (currentRoulette.value.id.startsWith('local-')) {
    item.weight = newWeight
    currentRoulette.value.total_weight = (currentRoulette.value.total_weight || 0) - oldWeight + newWeight
    saveToStorage()
    return
  }
  
  try {
    await rouletteApi.updateWeights(currentRoulette.value.id, { [itemId]: newWeight })
    item.weight = newWeight
    if (currentRoulette.value.total_weight !== undefined) {
      currentRoulette.value.total_weight += (newWeight - oldWeight)
    }
    saveToStorage()
  } catch (error) {
    console.error('Failed to update weight:', error)
  }
}

const weightModeChanged = () => {
  if (!currentRoulette.value?.items) return
  
  if (weightMode.value === 'equal') {
    // Все веса равны 1
    currentRoulette.value.items.forEach(item => {
      item.weight = 1
    })
    currentRoulette.value.total_weight = currentRoulette.value.items.length
  }
  
  saveToStorage()
}

const clearRoulette = async () => {
  if (!currentRoulette.value?.id) return
  if (!confirm('Очистить рулетку?')) return
  
  // Локальная рулетка
  if (currentRoulette.value.id.startsWith('local-')) {
    currentRoulette.value.items = []
    currentRoulette.value.total_weight = 0
    currentRoulette.value.items_count = 0
    saveToStorage()
    return
  }
  
  try {
    await rouletteApi.clear(currentRoulette.value.id)
    currentRoulette.value.items = []
    currentRoulette.value.total_weight = 0
    currentRoulette.value.items_count = 0
    saveToStorage()
  } catch (error) {
    console.error('Failed to clear roulette:', error)
  }
}

const spin = async () => {
  const roulette = currentRoulette.value
  if (!roulette?.id || isSpinning.value) return
  
  // Проверяем есть ли элементы
  if (!roulette.items?.length) {
    toast.error('Добавьте аниме в колесо!')
    return
  }
  
  isSpinning.value = true
  winner.value = null
  
  // Локальное вращение
  if (roulette.id.startsWith('local-')) {
    const items = roulette.items
    const totalWeight = items.reduce((sum, item) => sum + item.weight, 0)
    const randomValue = Math.random() * totalWeight
    
    let currentWeight = 0
    let selectedItem: RouletteItem | null = null
    
    for (const item of items) {
      currentWeight += item.weight
      if (randomValue <= currentWeight) {
        selectedItem = item
        break
      }
    }
    
    if (!selectedItem) {
      selectedItem = items[items.length - 1] ?? null
    }
    
    if (!selectedItem) {
      isSpinning.value = false
      return
    }
    
    // Вычисляем угол поворота
    const itemIndex = items.indexOf(selectedItem)
    const sectorSize = 360 / items.length
    const randomOffset = Math.random() * sectorSize * 0.8
    rotationAngle.value = (4 * 360) + (itemIndex * sectorSize) + randomOffset
    
    setTimeout(() => {
      isSpinning.value = false
      winner.value = selectedItem
      if (selectedItem) {
        toast.success(`Выпало: ${selectedItem.anime_title}`)
        
        // Сохраняем в историю
        roulette.last_result = selectedItem
        roulette.last_spin_at = new Date().toISOString()
        saveToStorage()
      }
    }, 5000)
    
    return
  }
  
  // Серверное вращение
  try {
    const response = await rouletteApi.spin(roulette.id)
    const data = response.data
    if (data) {
      rotationAngle.value = data.rotation_angle || 0
      
      setTimeout(() => {
        isSpinning.value = false
        winner.value = data.winner || null
        if (data.winner) {
          toast.success(`Выпало: ${data.winner.anime_title}`)
          
          // Сохраняем в историю
          roulette.last_result = data.winner
          roulette.last_spin_at = new Date().toISOString()
          saveToStorage()
        }
      }, (data.spin_duration || 5) * 1000)
    }
  } catch (error) {
    console.error('Failed to spin:', error)
    isSpinning.value = false
    toast.error('Ошибка при вращении')
  }
}

const watchAnime = (item: RouletteItem) => {
  if (item.anime_id) {
    window.open(`/anime/${item.anime_id}`, '_blank')
  }
}

// Helper функции для статусов
const formatStatus = (status: string): string => {
  const map: Record<string, string> = {
    'ongoing': 'Онгоинг',
    'finished': 'Завершён',
    'released': 'Вышел',
    'announced': 'Анонс',
    'canceled': 'Отменён'
  }
  return map[status] || status
}

const getStatusClass = (status: string): string => {
  const map: Record<string, string> = {
    'ongoing': 'ongoing',
    'finished': 'finished',
    'released': 'released',
    'announced': 'announced',
    'canceled': 'canceled'
  }
  return map[status] || ''
}

// Сохраняем при изменениях
watch([currentRoulette, selectedRouletteId, weightMode], () => {
  saveToStorage()
}, { deep: true })

onMounted(() => {
  loadRoulettes()
})
</script>

<style scoped>
/* ═══ ROOT ═══════════════════════════════════════════════════ */
.roulette-page {
  padding: 1.5rem 2rem;
  max-width: 1600px;
  margin: 0 auto;
}

/* ═══ HEADER ══════════════════════════════════════════════════ */
.rp-header {
  margin-bottom: 2rem;
}

.rp-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.rp-title-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.rp-icon {
  font-size: 2.5rem;
  filter: drop-shadow(0 4px 12px rgba(102, 126, 234, 0.3));
}

.rp-title {
  font-size: 2rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  line-height: 1.2;
}

.rp-subtitle {
  color: var(--text-tertiary);
  font-size: 0.95rem;
  margin: 0.25rem 0 0 0;
}

.rp-header-actions {
  display: flex;
  gap: 0.75rem;
}

.rp-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid transparent;
  white-space: nowrap;
}

.rp-btn-secondary {
  background: var(--surface-3);
  border-color: var(--border-subtle);
  color: var(--text-secondary);
}

.rp-btn-secondary:hover {
  background: var(--surface-4);
  border-color: var(--accent);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.rp-icon-btn {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: var(--surface-3);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  font-size: 1.1rem;
}

.rp-icon-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.rp-btn-danger:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: #ef4444;
  color: #ef4444;
}

.rp-btn-warning:hover {
  background: rgba(245, 158, 11, 0.15);
  border-color: #f59e0b;
  color: #f59e0b;
}

/* ═══ ROULETTE SELECTOR ═══════════════════════════════════════ */
.rp-roulette-selector {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.rp-selector-card,
.rp-stats-card {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1rem 1.25rem;
}

.rp-selector-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
  margin-bottom: 0.5rem;
}

.rp-selector-wrapper {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.rp-select {
  flex: 1;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.625rem 0.875rem;
  border-radius: var(--radius-lg);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 280px;
}

.rp-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.rp-selector-actions {
  display: flex;
  gap: 0.5rem;
}

.rp-stats-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 280px;
}

.rp-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.125rem;
}

.rp-stat-value {
  font-size: 1.25rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.rp-stat-label {
  font-size: 0.65rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.rp-stat-divider {
  width: 1px;
  height: 32px;
  background: var(--border-subtle);
}

/* ═══ SETTINGS PANEL ══════════════════════════════════════════ */
.rp-settings-panel {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.rp-settings-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
}

.rp-settings-row + .rp-settings-row {
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border-subtle);
}

.rp-setting-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.rp-setting-label {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
}

.rp-input {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  transition: all 0.2s;
}

.rp-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.rp-input-sm {
  padding: 0.5rem 0.625rem;
  font-size: 0.85rem;
}

.rp-select-sm {
  padding: 0.5rem 0.625rem;
  font-size: 0.85rem;
  min-width: 140px;
}

.rp-input-with-suffix {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rp-suffix {
  font-size: 0.85rem;
  color: var(--text-tertiary);
  font-weight: 600;
  white-space: nowrap;
}

/* ═══ ITEMS PANEL ═════════════════════════════════════════════ */
.rp-items-panel {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.rp-items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: var(--surface-3);
  border-bottom: 1px solid var(--border-subtle);
}

.rp-items-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.rp-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 0.125rem 0.5rem;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 800;
}

.rp-items-stats {
  display: flex;
  gap: 0.75rem;
}

.rp-stat-pill {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.125rem;
  padding: 0.25rem 0.75rem;
  background: var(--surface-1);
  border-radius: var(--radius-md);
}

.rp-stat-pill-value {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
}

.rp-stat-pill-label {
  font-size: 0.6rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  font-weight: 600;
}

.rp-items-scroll {
  max-height: 280px;
  overflow-y: auto;
}

.rp-items-list {
  padding: 0.75rem;
}

.rp-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  background: var(--surface-1);
  border-radius: var(--radius-lg);
  margin-bottom: 0.5rem;
  border-left: 3px solid;
  transition: all 0.2s;
}

.rp-item:hover {
  background: var(--surface-3);
  transform: translateX(2px);
}

.rp-item:last-child {
  margin-bottom: 0;
}

.rp-item-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-4);
  border-radius: var(--radius-md);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.rp-item-poster {
  width: 40px;
  height: 56px;
  object-fit: cover;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.rp-item-poster-placeholder {
  width: 40px;
  height: 56px;
  background: var(--surface-3);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.rp-item-info {
  flex: 1;
  min-width: 0;
}

.rp-item-title {
  color: var(--text-primary);
  font-size: 0.875rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0.25rem;
}

.rp-item-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.rp-weight-dot {
  flex-shrink: 0;
}

.rp-weight-percent {
  font-weight: 700;
  color: var(--accent);
}

.rp-weight-value {
  opacity: 0.7;
}

/* ═══ STATUS BADGES ═══════════════════════════════════════════ */
.status-badge {
  font-size: 10px !important;
  font-weight: 600 !important;
  padding: 4px 10px !important;
  border-radius: 12px !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
  line-height: 1.1 !important;
  white-space: nowrap !important;
  background: var(--surface-4);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

.status-badge.ongoing {
  background: rgba(59, 130, 246, 0.08);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.2);
}

.status-badge.finished,
.status-badge.released {
  background: rgba(34, 197, 94, 0.08);
  color: #86efac;
  border-color: rgba(34, 197, 94, 0.2);
}

.status-badge.announced {
  background: rgba(168, 85, 247, 0.08);
  color: #d8b4fe;
  border-color: rgba(168, 85, 247, 0.2);
}

.status-badge.canceled,
.status-badge.dropped {
  background: rgba(239, 68, 68, 0.08);
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.2);
}

.status-badge.on_hold,
.status-badge.on-hold {
  background: rgba(251, 191, 36, 0.08);
  color: #fcd34d;
  border-color: rgba(251, 191, 36, 0.2);
}

.status-badge.planned {
  background: rgba(156, 163, 175, 0.08);
  color: #d1d5db;
  border-color: rgba(107, 114, 128, 0.2);
}

.rp-item-weight {
  width: 120px;
  flex-shrink: 0;
}

.rp-weight-input {
  width: 100%;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.375rem;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  text-align: center;
  font-weight: 600;
}

.rp-weight-input:focus {
  outline: none;
  border-color: var(--accent);
}

.rp-weight-bar {
  width: 100%;
  height: 8px;
  background: var(--surface-3);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.rp-weight-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

.rp-item-remove {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.rp-item-remove:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* ═══ MAIN CONTENT ════════════════════════════════════════════ */
.rp-main-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.rp-wheel-section {
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.rp-wheel-card {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  max-width: 600px;
}

.rp-spin-control {
  width: 100%;
  display: flex;
  justify-content: center;
}

.rp-spin-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: var(--radius-xl);
  color: #fff;
  font-size: 1.125rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.3s var(--transition-smooth);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.rp-spin-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
}

.rp-spin-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rp-spin-icon {
  font-size: 1.5rem;
}

.rp-spinning-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2rem;
  background: var(--surface-3);
  border-radius: var(--radius-xl);
  color: var(--text-secondary);
  font-weight: 600;
}

.rp-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid var(--border-subtle);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Result panel */
.rp-result-panel {
  width: 100%;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 2px solid var(--accent);
  border-radius: var(--radius-xl);
  padding: 1.25rem;
  animation: rp-result-pop 0.5s ease-out;
}

@keyframes rp-result-pop {
  0% {
    opacity: 0;
    transform: scale(0.9) translateY(20px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.rp-result-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.rp-result-icon {
  font-size: 1.5rem;
}

.rp-result-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.rp-result-content {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
}

.rp-result-poster {
  width: 80px;
  height: 112px;
  object-fit: cover;
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.rp-result-poster-placeholder {
  width: 80px;
  height: 112px;
  background: var(--surface-3);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.rp-result-info {
  flex: 1;
  min-width: 0;
}

.rp-result-title-text {
  color: var(--text-primary);
  font-size: 1.125rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  line-height: 1.3;
}

.rp-result-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.rp-result-weight,
.rp-result-chance {
  font-weight: 600;
}

.rp-result-chance {
  color: var(--accent);
}

.rp-result-action {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: var(--radius-lg);
  color: #fff;
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.rp-result-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* Manager section */
.rp-manager-section {
  min-height: 500px;
}

.rp-manager-card {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 1.25rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.rp-manager-header {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-subtle);
}

.rp-manager-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

/* Result fade transition */
.rp-result-fade-enter-active,
.rp-result-fade-leave-active {
  transition: all 0.5s ease;
}

.rp-result-fade-enter-from,
.rp-result-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* ═══ RESPONSIVE ══════════════════════════════════════════════ */
@media (max-width: 1200px) {
  .rp-main-content {
    grid-template-columns: 1fr;
  }
  
  .rp-wheel-section {
    order: 2;
  }
  
  .rp-manager-section {
    order: 1;
  }
}

@media (max-width: 768px) {
  .roulette-page {
    padding: 1rem;
  }
  
  .rp-header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .rp-title {
    font-size: 1.5rem;
  }
  
  .rp-roulette-selector {
    grid-template-columns: 1fr;
  }
  
  .rp-stats-card {
    min-width: 100%;
  }
  
  .rp-settings-row {
    grid-template-columns: 1fr;
  }
  
  .rp-items-scroll {
    max-height: 200px;
  }
}
</style>
