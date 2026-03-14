<template>
  <div class="wheel-view">
    <div class="page-header">
      <div class="header-content">
        <h1>🎡 Колесо фортуны</h1>
        <p class="subtitle">Случайный выбор аниме для просмотра</p>
      </div>
      <div class="header-actions">
        <router-link to="/wheel/history" class="btn-icon" title="История">📊</router-link>
        <router-link to="/wheel/settings" class="btn-icon" title="Настройки">⚙️</router-link>
      </div>
    </div>

    <div class="roulette-selector">
      <select v-model="selectedRouletteId" @change="onRouletteChange">
        <option value="">+ Создать новую рулетку</option>
        <option v-for="r in roulettes" :key="r.id" :value="r.id">
          {{ r.name }} ({{ r.items_count || 0 }} аниме)
        </option>
      </select>
      <button v-if="currentRoulette" class="btn-delete" @click="deleteRoulette" title="Удалить рулетку">🗑️</button>
    </div>

    <div class="wheel-content" v-if="currentRoulette">
      <div class="wheel-column">
        <transition name="result-fade">
          <div v-if="winner && showResult" class="result-panel">
            <div class="result-header">
              <span class="result-icon">🎯</span>
              <span class="result-title">Выпало:</span>
            </div>
            <div class="result-anime">
              <img v-if="winner.anime_poster" :src="winner.anime_poster" :alt="winner.anime_title" class="result-poster">
              <div class="result-poster-placeholder" v-else>🎬</div>
              <div class="result-info">
                <h3>{{ winner.anime_title }}</h3>
                <div class="result-meta">
                  <span class="weight-badge">⚖️ {{ winner.weight }}</span>
                </div>
                <div class="result-actions">
                  <router-link :to="`/anime/${winner.anime_id}`" class="btn-primary">🎬 Смотреть</router-link>
                </div>
              </div>
            </div>
          </div>
        </transition>

        <div class="wheel-wrapper">
          <FortuneWheel :items="currentRoulette.items" :total-weight="currentRoulette.total_weight" :is-spinning="isSpinning" :rotation-angle="rotationAngle" :winner="winner" :size="wheelSizePx" @spin="spin" />
        </div>

        <div class="spin-controls">
          <button class="btn-spin" :disabled="isSpinning || itemsCount === 0" @click="spin">🎲 Крутить</button>
          <button class="btn-spin-multi" :disabled="isSpinning || itemsCount < 3" @click="spinMultiple(3)">🎲×3</button>
          <button class="btn-spin-multi" :disabled="isSpinning || itemsCount < 5" @click="spinMultiple(5)">🎲×5</button>
        </div>

        <div v-if="recentHistory.length > 0" class="recent-history">
          <h3>📜 Последние</h3>
          <div class="history-list">
            <div v-for="h in recentHistory" :key="h.id" class="history-item">
              <span class="history-title">{{ h.winner?.anime_title || '—' }}</span>
              <span class="history-time">{{ formatTime(h.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="manager-column">
        <div class="current-items">
          <div class="items-header">
            <h3>В колесе ({{ itemsCount }})</h3>
            <button v-if="itemsCount > 0" class="btn-clear-all" @click="clearRoulette">Очистить</button>
          </div>
          <div v-if="itemsCount === 0" class="empty-items"><span>Добавьте аниме</span></div>
          <div v-else class="items-list">
            <div v-for="item in currentRoulette.items" :key="item.id" class="item-row">
              <img v-if="item.anime_poster" :src="item.anime_poster" :alt="item.anime_title" class="item-poster">
              <div class="item-poster-placeholder" v-else>🎬</div>
              <div class="item-info">
                <div class="item-title">{{ item.anime_title }}</div>
                <div class="item-weight">
                  <button class="weight-btn" @click="changeWeight(item.id, -1)">−</button>
                  <span>{{ item.weight }}</span>
                  <button class="weight-btn" @click="changeWeight(item.id, 1)">+</button>
                </div>
              </div>
              <div class="item-percent">{{ getPercent(item.weight) }}%</div>
              <button class="btn-remove" @click="removeItem(item.id)">✕</button>
            </div>
          </div>
          <div class="items-footer"><span>Вес: {{ currentRoulette.total_weight || 0 }}</span></div>
        </div>

        <div class="anime-selector-wrapper">
          <AnimeSelector :current-items="currentRoulette.items" @add="handleAddItems" />
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">🎡</div>
      <h2>Создайте рулетку</h2>
      <p>Добавьте аниме и крутите колесо!</p>
      <button class="btn-create" @click="createRoulette">➕ Создать рулетку</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { rouletteApi, type Roulette, type RouletteItem, type SpinHistory } from '@/api/roulette'
import FortuneWheel from '@/components/roulette/FortuneWheel.vue'
import AnimeSelector from '@/components/roulette/AnimeSelector.vue'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const roulettes = ref<Roulette[]>([])
const selectedRouletteId = ref('')
const currentRoulette = ref<Roulette | null>(null)
const isSpinning = ref(false)
const rotationAngle = ref(0)
const winner = ref<RouletteItem | null>(null)
const showResult = ref(false)
const history = ref<SpinHistory[]>([])

const itemsCount = computed(() => currentRoulette.value?.items?.length || 0)
const wheelSizePx = computed(() => currentRoulette.value?.wheel_size_px || 400)
const recentHistory = computed(() => history.value.slice(0, 5))

const getPercent = (weight: number) => {
  const total = currentRoulette.value?.total_weight || 1
  return total > 0 ? ((weight / total) * 100).toFixed(1) : '0'
}

const loadRoulettes = async () => {
  console.log('[Roulette] Loading roulettes...')
  try {
    const { data } = await rouletteApi.getRoulettes()
    console.log('[Roulette] Loaded:', data?.length || 0)

    if (data && data.length > 0) {
      const firstRoulette = data[0]
      if (firstRoulette?.id) {
        roulettes.value = data
        selectedRouletteId.value = firstRoulette.id
        await loadRoulette()
        return
      }
    }
    // Нет рулеток - создаём новую
    console.log('[Roulette] No roulettes found, creating new...')
    await createRoulette()
  } catch (error: any) {
    console.error('[Roulette] Failed to load:', error?.message || error)
    // При ошибке создаём локальную рулетку
    await createRoulette()
  }
}

const loadRoulette = async () => {
  if (!selectedRouletteId.value) { await createRoulette(); return }
  try {
    const { data } = await rouletteApi.getRoulette(selectedRouletteId.value)
    if (data) {
      currentRoulette.value = data
      try { const { data: hd } = await rouletteApi.getHistory(selectedRouletteId.value); history.value = hd || [] } catch { history.value = [] }
    }
  } catch (error) { console.error('Failed to load roulette:', error); await createRoulette() }
}

const onRouletteChange = async () => selectedRouletteId.value ? await loadRoulette() : await createRoulette()

const createLocalRoulette = (): Roulette => {
  return {
    id: 'local-' + Date.now(),
    name: 'Моя рулетка',
    spin_duration: 5,
    items: [],
    total_weight: 0,
    items_count: 0,
    wheel_size_px: 400,
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
    auto_add_from_playlists: false,
    last_result: null,
    last_spin_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
}

const createRoulette = async () => {
  try {
    console.log('[Roulette] Creating roulette...')

    // Всегда создаём локальную рулетку сразу
    const localRoulette = createLocalRoulette()
    console.log('[Roulette] Local roulette created:', localRoulette.id)

    // Обновляем состояние ДО вызова API
    if (!roulettes.value.find(r => r.id === localRoulette.id)) {
      roulettes.value.unshift(localRoulette)
    }
    selectedRouletteId.value = localRoulette.id
    currentRoulette.value = localRoulette
    console.log('[Roulette] State updated, currentRoulette:', currentRoulette.value?.id)

    // Пробуем создать на сервере (тихо, без блокировки UI)
    try {
      console.log('[Roulette] Attempting to create on server...')
      const { data } = await rouletteApi.createRoulette({ name: 'Моя рулетка', spin_duration: 5 })
      console.log('[Roulette] Server response:', data)

      if (data && data.id) {
        // Заменяем локальную на серверную
        const index = roulettes.value.findIndex(r => r.id === localRoulette.id)
        if (index > -1) {
          roulettes.value[index] = data
        }
        selectedRouletteId.value = data.id
        currentRoulette.value = data
        toast.success('Рулетка создана')
      }
    } catch (error: any) {
      console.warn('[Roulette] Server unavailable or error:', error?.message || error)
      // Локальная рулетка уже создана и отображается
      toast.info('Рулетка создана (локально)')
    }
  } catch (err: any) {
    console.error('[Roulette] FATAL error in createRoulette:', err)
    toast.error('Ошибка: ' + (err?.message || 'unknown'))
  }
}

const deleteRoulette = async () => {
  const rouletteId = currentRoulette.value?.id
  if (!rouletteId || rouletteId.startsWith('local-')) {
    if (!confirm('Удалить рулетку?')) return
    const currentId = currentRoulette.value?.id
    roulettes.value = roulettes.value.filter(r => r.id !== currentId)
    selectedRouletteId.value = ''
    currentRoulette.value = null
    if (roulettes.value.length > 0) {
      const firstRoulette = roulettes.value[0]
      if (firstRoulette?.id) {
        selectedRouletteId.value = firstRoulette.id
        await loadRoulette()
      }
    }
    return
  }
  if (!confirm('Удалить рулетку?')) return
  try {
    await rouletteApi.deleteRoulette(rouletteId)
    roulettes.value = roulettes.value.filter(r => r.id !== rouletteId)
    selectedRouletteId.value = ''
    currentRoulette.value = null
    if (roulettes.value.length > 0) {
      const firstRoulette = roulettes.value[0]
      if (firstRoulette?.id) {
        selectedRouletteId.value = firstRoulette.id
        await loadRoulette()
      }
    }
    toast.success('Рулетка удалена')
  } catch (error) { console.error('Failed to delete roulette:', error); toast.error('Ошибка удаления') }
}

const spin = async () => {
  if (!currentRoulette.value || isSpinning.value || itemsCount.value === 0) return
  isSpinning.value = true; winner.value = null; showResult.value = false
  try {
    const { data } = await rouletteApi.spin(currentRoulette.value.id)
    rotationAngle.value = data.rotation_angle
    const spinDuration = currentRoulette.value?.spin_duration || 5
    setTimeout(() => {
      isSpinning.value = false; winner.value = data.winner ?? null; showResult.value = true
      history.value.unshift({ id: data.spin_id || 'spin-' + Date.now(), winner: data.winner, winners: [], spin_type: 'single', rotation_angle: data.rotation_angle, spin_duration: data.spin_duration, items_count: 1, is_favorite: false, notes: '', created_at: new Date().toISOString() })
    }, spinDuration * 1000)
  } catch (error) { console.error('Failed to spin:', error); simulateSpin() }
}

const simulateSpin = () => {
  if (!currentRoulette.value || itemsCount.value === 0) return
  const items = currentRoulette.value.items
  if (!items || items.length === 0) return
  const totalWeight = currentRoulette.value.total_weight || 1
  let random = Math.random() * totalWeight
  let selectedItem: RouletteItem | null = null
  for (const item of items) { random -= item.weight; if (random <= 0) { selectedItem = item; break } }
  if (!selectedItem) selectedItem = items[items.length - 1] ?? null
  if (!selectedItem) return
  const spinDuration = currentRoulette.value.spin_duration || 5
  rotationAngle.value = Math.random() * 360 + 720
  setTimeout(() => {
    isSpinning.value = false; winner.value = selectedItem; showResult.value = true
    history.value.unshift({ id: 'local-' + Date.now(), winner: selectedItem, winners: [], spin_type: 'single', rotation_angle: rotationAngle.value, spin_duration: spinDuration, items_count: 1, is_favorite: false, notes: '', created_at: new Date().toISOString() })
  }, spinDuration * 1000)
}

const spinMultiple = async (count: number) => {
  if (!currentRoulette.value || isSpinning.value || itemsCount.value < count) return
  isSpinning.value = true; winner.value = null; showResult.value = false
  try {
    const rouletteId = currentRoulette.value.id
    const { data } = await rouletteApi.spinMultiple(rouletteId, count)
    const spinDuration = currentRoulette.value?.spin_duration || 5
    setTimeout(() => {
      isSpinning.value = false
      if (data.winners && data.winners.length > 0) { winner.value = data.winners[0] ?? null; showResult.value = true; toast.success(`Выбрано ${data.winners.length} аниме!`) }
    }, spinDuration * 1000)
  } catch (error) { console.error('Failed to spin multiple:', error); simulateMultipleSpin(count) }
}

const simulateMultipleSpin = (count: number) => {
  if (!currentRoulette.value || itemsCount.value < count) return
  const items = [...currentRoulette.value.items]
  if (!items || items.length === 0) return
  const selected: RouletteItem[] = []
  const spinDuration = currentRoulette.value.spin_duration || 5
  for (let i = 0; i < count; i++) {
    if (items.length === 0) break
    const totalWeight = items.reduce((sum, item) => sum + (item?.weight ?? 0), 0)
    let random = Math.random() * totalWeight
    let selectedIndex = -1
    for (let j = 0; j < items.length; j++) {
      const item = items[j]
      if (item) {
        random -= item.weight
        if (random <= 0) { selectedIndex = j; break }
      }
    }
    if (selectedIndex === -1) selectedIndex = items.length - 1
    const selectedItem = items[selectedIndex]
    if (selectedItem) {
      selected.push(selectedItem)
      items.splice(selectedIndex, 1)
    }
  }
  rotationAngle.value = Math.random() * 360 + 720
  setTimeout(() => {
    isSpinning.value = false
    const firstWinner = selected[0]
    if (firstWinner) {
      winner.value = firstWinner
      showResult.value = true
      toast.success(`Выбрано ${selected.length} аниме!`)
    }
  }, spinDuration * 1000)
}

const handleAddItems = async (items: Array<{ anime_id: number; anime_title: string; anime_poster?: string; weight: number }>) => {
  if (!currentRoulette.value) { await createRoulette() }
  if (!currentRoulette.value) return
  const colors = ['#667eea', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']
  const rouletteItems = currentRoulette.value.items
  for (const item of items) {
    if (rouletteItems.some(i => i.anime_id === item.anime_id)) continue
    const color = colors[rouletteItems.length % colors.length] ?? '#667eea'
    const newItem: RouletteItem = {
      id: 'item-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9),
      anime_id: item.anime_id, anime_title: item.anime_title, anime_poster: item.anime_poster || null,
      weight: item.weight, color: color,
      order: rouletteItems.length, created_at: new Date().toISOString()
    }
    rouletteItems.push(newItem)
    currentRoulette.value.total_weight = (currentRoulette.value.total_weight || 0) + item.weight
    currentRoulette.value.items_count = (currentRoulette.value.items_count || 0) + 1
  }
  try {
    const rouletteId = currentRoulette.value?.id
    if (rouletteId && !rouletteId.startsWith('local-')) {
      for (const item of items) {
        try { await rouletteApi.addItem(rouletteId, item) } catch (e) { console.warn('Failed to sync item:', e) }
      }
    }
  } catch (error) { console.warn('Failed to sync with server:', error) }
  toast.success(`Добавлено ${items.length} аниме`)
}

const removeItem = async (itemId: string) => {
  if (!currentRoulette.value) return
  const index = currentRoulette.value.items.findIndex(i => i.id === itemId)
  if (index > -1) {
    const item = currentRoulette.value.items[index]
    if (item) {
      currentRoulette.value.total_weight -= item.weight
      currentRoulette.value.items.splice(index, 1)
      currentRoulette.value.items_count = currentRoulette.value.items.length
      try {
        const rouletteId = currentRoulette.value?.id
        if (rouletteId && !rouletteId.startsWith('local-')) await rouletteApi.removeItem(rouletteId, itemId)
      } catch (error) { console.warn('Failed to sync removal:', error) }
    }
  }
}

const changeWeight = async (itemId: string, delta: number) => {
  if (!currentRoulette.value) return
  const item = currentRoulette.value.items.find(i => i.id === itemId)
  if (!item) return
  const newWeight = Math.max(1, item.weight + delta)
  const oldWeight = item.weight
  item.weight = newWeight
  currentRoulette.value.total_weight += (newWeight - oldWeight)
  try { if (currentRoulette.value.id && !currentRoulette.value.id.startsWith('local-')) await rouletteApi.updateWeights(currentRoulette.value.id, { [itemId]: newWeight }) } catch (error) { console.warn('Failed to sync weight:', error) }
}

const clearRoulette = async () => {
  if (!currentRoulette.value) return
  if (!confirm('Очистить рулетку?')) return
  currentRoulette.value.items = []; currentRoulette.value.total_weight = 0; currentRoulette.value.items_count = 0
  try { if (currentRoulette.value.id && !currentRoulette.value.id.startsWith('local-')) await rouletteApi.clear(currentRoulette.value.id) } catch (error) { console.warn('Failed to sync clear:', error) }
  toast.success('Рулетка очищена')
}

const formatTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'сейчас'
  if (minutes < 60) return `${minutes} мин`
  if (minutes < 1440) return `${Math.floor(minutes / 60)} ч`
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

onMounted(() => { 
  console.log('[Roulette] Component mounted, starting load...')
  loadRoulettes() 
})
</script>

<style scoped>
.wheel-view { max-width: 1400px; margin: 0 auto; padding: 1.5rem; min-height: 100vh; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.header-content h1 { color: #fff; font-size: 1.75rem; margin-bottom: 0.25rem; }
.subtitle { color: #666; font-size: 0.9rem; }
.header-actions { display: flex; gap: 0.5rem; }
.btn-icon { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: #2a2a2a; border-radius: 8px; text-decoration: none; font-size: 1.2rem; transition: all 0.2s; }
.btn-icon:hover { background: #3a3a3a; transform: translateY(-2px); }
.roulette-selector { display: flex; gap: 0.75rem; justify-content: center; margin-bottom: 1.5rem; }
.roulette-selector select { background: #1a1a1a; border: 1px solid #2a2a2a; color: #fff; padding: 0.625rem 1rem; border-radius: 8px; font-size: 0.95rem; min-width: 280px; cursor: pointer; }
.roulette-selector select:focus { outline: none; border-color: #667eea; }
.btn-delete { background: #dc2626; color: #fff; border: none; padding: 0.625rem 0.875rem; border-radius: 8px; cursor: pointer; font-size: 1rem; transition: all 0.2s; }
.btn-delete:hover { background: #b91c1c; }
.wheel-content { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.wheel-column { display: flex; flex-direction: column; gap: 1rem; }
.wheel-wrapper { display: flex; justify-content: center; padding: 1rem 0; }
.result-panel { background: linear-gradient(135deg, #1a1a2e, #16213e); border: 2px solid #667eea; border-radius: 12px; padding: 1rem; }
.result-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.result-icon { font-size: 1.25rem; }
.result-title { color: #fbbf24; font-size: 1rem; font-weight: 600; }
.result-anime { display: flex; gap: 0.75rem; background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 0.75rem; }
.result-poster { width: 60px; height: 85px; object-fit: cover; border-radius: 6px; }
.result-poster-placeholder { width: 60px; height: 85px; background: #2a2a2a; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
.result-info { flex: 1; }
.result-info h3 { color: #fff; font-size: 0.95rem; margin-bottom: 0.5rem; }
.result-meta { margin-bottom: 0.5rem; }
.weight-badge { background: rgba(102, 126, 234, 0.2); color: #667eea; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.75rem; }
.result-actions { display: flex; gap: 0.5rem; }
.btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; border: none; padding: 0.4rem 0.75rem; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 0.8rem; transition: all 0.2s; }
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4); }
.spin-controls { display: flex; gap: 0.5rem; justify-content: center; }
.btn-spin { flex: 1; max-width: 140px; padding: 0.75rem 1rem; background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; border: none; border-radius: 10px; cursor: pointer; font-size: 0.95rem; font-weight: 600; transition: all 0.2s; }
.btn-spin:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
.btn-spin:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-spin-multi { flex: 1; max-width: 100px; padding: 0.75rem 1rem; background: #2a2a2a; color: #fff; border: 1px solid #3a3a3a; border-radius: 10px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }
.btn-spin-multi:hover:not(:disabled) { background: #3a3a3a; border-color: #667eea; }
.btn-spin-multi:disabled { opacity: 0.5; cursor: not-allowed; }
.recent-history { background: #1a1a1a; border-radius: 10px; padding: 0.75rem; }
.recent-history h3 { color: #fff; font-size: 0.9rem; margin-bottom: 0.5rem; }
.history-list { display: flex; flex-direction: column; gap: 0.35rem; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0.5rem; background: #0a0a0a; border-radius: 6px; }
.history-title { color: #ccc; font-size: 0.8rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px; }
.history-time { color: #555; font-size: 0.7rem; white-space: nowrap; }
.manager-column { display: flex; flex-direction: column; gap: 1rem; }
.current-items { background: #1a1a1a; border-radius: 10px; padding: 0.75rem; }
.items-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.items-header h3 { color: #fff; font-size: 0.95rem; margin: 0; }
.btn-clear-all { background: #dc2626; color: #fff; border: none; padding: 0.3rem 0.5rem; border-radius: 6px; font-size: 0.7rem; cursor: pointer; transition: all 0.2s; }
.btn-clear-all:hover { background: #b91c1c; }
.empty-items { text-align: center; padding: 1.5rem; color: #555; }
.items-list { display: flex; flex-direction: column; gap: 0.5rem; max-height: 250px; overflow-y: auto; }
.item-row { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; background: #0a0a0a; border-radius: 6px; }
.item-poster { width: 35px; height: 50px; object-fit: cover; border-radius: 4px; }
.item-poster-placeholder { width: 35px; height: 50px; background: #2a2a2a; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 1rem; }
.item-info { flex: 1; min-width: 0; }
.item-title { color: #fff; font-size: 0.8rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-weight { display: flex; align-items: center; gap: 0.25rem; margin-top: 0.25rem; }
.weight-btn { width: 20px; height: 20px; background: #2a2a2a; border: none; color: #fff; border-radius: 4px; cursor: pointer; font-size: 0.8rem; display: flex; align-items: center; justify-content: center; }
.weight-btn:hover { background: #667eea; }
.item-weight span { color: #667eea; font-size: 0.8rem; min-width: 20px; text-align: center; }
.item-percent { color: #888; font-size: 0.7rem; min-width: 35px; text-align: right; }
.btn-remove { width: 20px; height: 20px; background: transparent; border: none; color: #666; cursor: pointer; font-size: 0.7rem; opacity: 0; transition: all 0.2s; }
.item-row:hover .btn-remove { opacity: 1; }
.btn-remove:hover { color: #dc2626; }
.items-footer { margin-top: 0.75rem; padding-top: 0.5rem; border-top: 1px solid #2a2a2a; color: #666; font-size: 0.8rem; text-align: center; }
.anime-selector-wrapper { flex: 1; min-height: 400px; }
.empty-state { text-align: center; padding: 4rem 2rem; }
.empty-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-state h2 { color: #fff; font-size: 1.5rem; margin-bottom: 0.5rem; }
.empty-state p { color: #666; margin-bottom: 2rem; }
.btn-create { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; border: none; padding: 0.875rem 2rem; border-radius: 10px; cursor: pointer; font-size: 1rem; font-weight: 600; transition: all 0.2s; }
.btn-create:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); }
.result-fade-enter-active, .result-fade-leave-active { transition: all 0.4s ease; }
.result-fade-enter-from, .result-fade-leave-to { opacity: 0; transform: translateY(-10px); }
@media (max-width: 1024px) { .wheel-content { grid-template-columns: 1fr; } }
@media (max-width: 600px) { .wheel-view { padding: 1rem; } .page-header { flex-direction: column; align-items: flex-start; gap: 1rem; } .header-content h1 { font-size: 1.5rem; } .roulette-selector select { min-width: 200px; } .spin-controls { flex-wrap: wrap; } .btn-spin, .btn-spin-multi { max-width: none; } }
</style>