<template>
  <div class="roulette-tab">
    <!-- Заголовок -->
    <div class="rt-header">
      <h2>🎰 Рулетка аниме</h2>
      <p>Добавьте аниме и крутите колесо фортуны!</p>
    </div>
    
    <!-- Выбор рулетки -->
    <div class="rt-selector">
      <select v-model="selectedRouletteId" @change="loadRoulette">
        <option value="">+ Создать рулетку</option>
        <option v-for="r in roulettes" :key="r.id" :value="r.id">
          {{ r.name }} ({{ r.items_count }})
        </option>
      </select>
      <button v-if="selectedRouletteId" class="rt-delete-btn" @click="deleteRoulette">
        🗑️
      </button>
      <button class="rt-clear-btn" @click="clearRoulette" title="Очистить">
        🧹
      </button>
    </div>
    
    <!-- Настройки -->
    <div v-if="currentRoulette" class="rt-settings">
      <input
        v-model="currentRoulette.name"
        type="text"
        class="rt-name-input"
        placeholder="Название рулетки"
        @blur="updateRoulette"
      >
      <label class="rt-duration">
        Время: 
        <input
          v-model.number="currentRoulette.spin_duration"
          type="number"
          min="3"
          max="15"
          @blur="updateRoulette"
        > сек
      </label>
      <label class="rt-weight-mode">
        Веса:
        <select v-model="weightMode" @change="weightModeChanged">
          <option value="equal">Равные</option>
          <option value="manual">Вручную</option>
          <option value="score">По рейтингу</option>
        </select>
      </label>
    </div>
    
    <!-- Список элементов колеса с весами -->
    <div v-if="currentRoulette?.items?.length" class="rt-items-panel">
      <div class="rt-items-header">
        <span>Элементы колеса ({{ currentRoulette.items.length }})</span>
        <span class="rt-total-weight">Общий вес: {{ currentRoulette.total_weight }}</span>
      </div>
      <div class="rt-items-list">
        <div
          v-for="item in currentRoulette.items"
          :key="item.id"
          class="rt-item"
        >
          <img
            v-if="item.anime_poster"
            :src="item.anime_poster"
            :alt="item.anime_title"
            class="rt-item-poster"
            @error="handleImageError"
          >
          <div class="rt-item-poster-placeholder" v-else>🎬</div>
          <div class="rt-item-info">
            <div class="rt-item-title">{{ item.anime_title }}</div>
            <div class="rt-item-meta">
              <span :style="{ color: item.color }">●</span>
              {{ Math.round((item.weight / (currentRoulette.total_weight || 1)) * 100) }}%
            </div>
          </div>
          <div class="rt-item-weight">
            <input
              v-if="weightMode === 'manual'"
              type="number"
              :value="item.weight"
              min="1"
              max="100"
              class="weight-input"
              @change="(e) => updateWeight(item.id, Number((e.target as HTMLInputElement).value))"
            >
            <span v-else class="weight-display">{{ item.weight }}</span>
          </div>
          <button class="rt-item-remove" @click="removeItem(item.id)">✕</button>
        </div>
      </div>
    </div>
    
    <div class="rt-content">
      <!-- Колесо -->
      <div class="rt-wheel-section">
        <FortuneWheel
          :items="currentRoulette?.items || []"
          :total-weight="currentRoulette?.total_weight || 0"
          :is-spinning="isSpinning"
          :rotation-angle="rotationAngle"
          :winner="winner"
          @spin="spin"
        />
      </div>
      
      <!-- Управление -->
      <div class="rt-manager-section">
        <AnimeSelector
          :current-items="currentRoulette?.items || []"
          @add="handleAddItems"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { rouletteApi, type Roulette, type RouletteItem } from '@/api/roulette'
import FortuneWheel from '@/components/roulette/FortuneWheel.vue'
import AnimeSelector from '@/components/roulette/AnimeSelector.vue'
import { useToast } from '@/composables/useToast'

const toast = useToast()

// LocalStorage ключи
const STORAGE_KEY = 'animecore_roulette'
const ROULETTES_KEY = 'animecore_roulettes_list'

const roulettes = ref<Roulette[]>([])
const selectedRouletteId = ref('')
const currentRoulette = ref<Roulette | null>(null)
const isSpinning = ref(false)
const rotationAngle = ref(0)
const winner = ref<RouletteItem | null>(null)
const weightMode = ref<'equal' | 'manual' | 'score'>('equal')

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
        }
      }, (data.spin_duration || 5) * 1000)
    }
  } catch (error) {
    console.error('Failed to spin:', error)
    isSpinning.value = false
    toast.error('Ошибка при вращении')
  }
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
.roulette-tab {
  padding: 1rem 0;
}

.rt-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.rt-header h2 {
  color: var(--text-primary);
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.rt-header p {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.rt-selector {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-bottom: 1rem;
}

.rt-selector select {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-lg);
  font-size: 0.9rem;
  min-width: 250px;
  cursor: pointer;
}

.rt-selector select:focus {
  outline: none;
  border-color: var(--accent);
}

.rt-delete-btn {
  background: var(--danger);
  color: #fff;
  border: none;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.rt-delete-btn:hover {
  background: #b91c1c;
}

.rt-settings {
  display: flex;
  gap: 1rem;
  justify-content: center;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.rt-name-input {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.4rem 0.75rem;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  min-width: 200px;
}

.rt-name-input:focus {
  outline: none;
  border-color: var(--accent);
}

.rt-duration {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.rt-duration input {
  width: 50px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  text-align: center;
}

.rt-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.rt-wheel-section {
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.rt-manager-section {
  min-height: 400px;
}

@media (max-width: 900px) {
  .rt-content {
    grid-template-columns: 1fr;
  }
  
  .rt-wheel-section {
    order: 2;
  }
  
  .rt-manager-section {
    order: 1;
  }
}

@media (max-width: 500px) {
  .rt-selector select {
    min-width: 180px;
  }
  
  .rt-header h2 {
    font-size: 1.25rem;
  }
}

/* Кнопка очистки */
.rt-clear-btn {
  background: var(--surface-3);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.rt-clear-btn:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

/* Режим весов */
.rt-weight-mode {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.rt-weight-mode select {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  cursor: pointer;
}

.rt-weight-mode select:focus {
  outline: none;
  border-color: var(--accent);
}

/* Панель элементов */
.rt-items-panel {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  margin: 0 1rem 1.5rem;
  max-height: 200px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.rt-items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--surface-3);
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.rt-total-weight {
  color: var(--accent);
  font-weight: 600;
}

.rt-items-list {
  overflow-y: auto;
  flex: 1;
  padding: 0.5rem;
}

.rt-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: var(--surface-1);
  border-radius: var(--radius-md);
  margin-bottom: 0.5rem;
}

.rt-item:last-child {
  margin-bottom: 0;
}

.rt-item-poster {
  width: 36px;
  height: 50px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.rt-item-poster-placeholder {
  width: 36px;
  height: 50px;
  background: var(--surface-3);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.rt-item-info {
  flex: 1;
  min-width: 0;
}

.rt-item-title {
  color: var(--text-primary);
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rt-item-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.rt-item-weight {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.weight-input {
  width: 50px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.25rem;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  text-align: center;
}

.weight-input:focus {
  outline: none;
  border-color: var(--accent);
}

.weight-display {
  color: var(--text-secondary);
  font-size: 0.85rem;
  min-width: 30px;
  text-align: center;
}

.rt-item-remove {
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0.25rem;
  font-size: 0.9rem;
  opacity: 0.6;
  transition: all 0.2s;
}

.rt-item-remove:hover {
  opacity: 1;
  color: var(--danger);
}

/* Статус бадж */
.status-badge {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.65rem;
  text-transform: uppercase;
  font-weight: 600;
}

.status-badge.started {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.status-badge.completed {
  background: rgba(67, 233, 123, 0.2);
  color: #43e97b;
}

.status-badge.on_hold {
  background: rgba(254, 225, 64, 0.2);
  color: #fee140;
}

.status-badge.dropped {
  background: rgba(245, 87, 108, 0.2);
  color: #f5576c;
}

.status-badge.planned {
  background: rgba(160, 174, 192, 0.2);
  color: #a0aec0;
}
</style>
