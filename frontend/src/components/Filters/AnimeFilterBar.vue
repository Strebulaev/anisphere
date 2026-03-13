<template>
  <div class="afb">
    <!-- ── Верхняя строка ──────────────────────────────────── -->
    <div class="afb-top">
      <!-- Поиск -->
      <div class="afb-search">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="search"
          @input="onSearch"
          type="text"
          :placeholder="searchPlaceholder"
          class="afb-search-input"
        />
        <button v-if="search" @click="clearSearch" class="afb-search-clear" type="button">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <!-- Сортировка -->
      <select v-model="ordering" class="afb-select">
        <option v-for="s in sortOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>

      <!-- На странице -->
      <select v-if="showPageSize" v-model="pageSize" class="afb-select afb-select-sm">
        <option :value="20">20</option>
        <option :value="50">50</option>
        <option :value="100">100</option>
      </select>

      <div class="afb-actions">
        <!-- Перетасовать -->
        <button v-if="showShuffle && !isShuffled" @click="$emit('shuffle')" class="afb-btn" title="Перемешать" type="button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/>
            <polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/>
            <line x1="4" y1="4" x2="9" y2="9"/>
          </svg>
        </button>
        <button v-if="showShuffle && isShuffled" @click="$emit('unshuffle')" class="afb-btn afb-btn-active" title="Сбросить перемешку" type="button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>
          </svg>
        </button>

        <!-- Обновить -->
        <button @click="$emit('refresh')" class="afb-btn" title="Обновить" type="button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
        </button>

        <!-- Открыть фильтры -->
        <button
          v-if="showAdvanced"
          @click="panelOpen = !panelOpen"
          :class="['afb-btn', { 'afb-btn-active': panelOpen || activeAdvancedCount > 0 }]"
          :title="panelOpen ? 'Скрыть фильтры' : 'Фильтры'"
          type="button"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>
          </svg>
          <span v-if="activeAdvancedCount > 0" class="afb-badge">{{ activeAdvancedCount }}</span>
        </button>
      </div>
    </div>

    <!-- ── Жанры (всегда видны) ──────────────────────────────── -->
    <div class="afb-genres-row">
      <span class="afb-genres-label">Жанры</span>
      <div class="afb-genres-scroll">
        <button
          :class="['afb-genre-chip', { active: selectedGenres.length === 0 }]"
          @click="clearGenres"
          type="button"
        >Все</button>

        <template v-if="genresLoading">
          <div v-for="i in 14" :key="i" class="afb-genre-skel"></div>
        </template>
        <template v-else>
          <button
            v-for="g in filteredGenreList"
            :key="g"
            :class="['afb-genre-chip', { active: selectedGenres.includes(g) }]"
            @click="toggleGenre(g)"
            type="button"
          >{{ g }}</button>
        </template>
      </div>

      <!-- Поиск жанра -->
      <div class="afb-genre-search">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input v-model="genreSearch" class="afb-genre-search-input" placeholder="Жанр…" type="text"/>
      </div>
    </div>

    <!-- ── Расширенная панель фильтров ──────────────────────── -->
    <transition name="afb-panel">
      <div v-if="panelOpen && showAdvanced" class="afb-panel">

        <!-- ТИП -->
        <div class="afb-group">
          <div class="afb-group-label">Тип</div>
          <div class="afb-chips">
            <button
              v-for="t in TYPE_OPTIONS" :key="t.value"
              :class="['afb-chip', { active: selectedTypes.includes(t.value) }]"
              @click="toggleType(t.value)" type="button"
            >{{ t.label }}</button>
          </div>
        </div>

        <!-- СТАТУС (скрыт для ongoings и announcements) -->
        <div v-if="showStatus" class="afb-group">
          <div class="afb-group-label">Статус</div>
          <div class="afb-chips">
            <button
              v-for="s in STATUS_OPTIONS" :key="s.value"
              :class="['afb-chip', `afb-chip-status-${s.color}`, { active: selectedStatuses.includes(s.value) }]"
              @click="toggleStatus(s.value)" type="button"
            >
              <span class="afb-dot"></span>{{ s.label }}
            </button>
          </div>
        </div>

        <!-- ГОД -->
        <div class="afb-group">
          <div class="afb-group-label">Год выпуска</div>
          <div class="afb-range-row">
            <input v-model.number="yearFrom" type="number" placeholder="От" min="1960" :max="currentYear+1" class="afb-range-input"/>
            <span class="afb-dash">—</span>
            <input v-model.number="yearTo" type="number" placeholder="До" min="1960" :max="currentYear+1" class="afb-range-input"/>
          </div>
          <div class="afb-presets">
            <button v-for="y in YEAR_PRESETS" :key="y.label"
              :class="['afb-preset', { active: yearFrom === y.from && yearTo === y.to }]"
              @click="toggleYearPreset(y)" type="button">{{ y.label }}</button>
          </div>
        </div>

        <!-- РЕЙТИНГ -->
        <div class="afb-group">
          <div class="afb-group-label">Рейтинг</div>
          <div class="afb-range-row">
            <input v-model.number="scoreFrom" type="number" placeholder="От" min="0" max="10" step="0.1" class="afb-range-input"/>
            <span class="afb-dash">—</span>
            <input v-model.number="scoreTo" type="number" placeholder="До" min="0" max="10" step="0.1" class="afb-range-input"/>
          </div>
          <div class="afb-presets">
            <button v-for="r in [9, 8, 7, 6]" :key="r"
              :class="['afb-preset', { active: scoreFrom === r && !scoreTo }]"
              @click="toggleRatingPreset(r)" type="button">{{ r }}+</button>
          </div>
        </div>

        <!-- ЭПИЗОДЫ -->
        <div class="afb-group">
          <div class="afb-group-label">Эпизоды</div>
          <div class="afb-range-row">
            <input v-model.number="episodesFrom" type="number" placeholder="От" min="0" class="afb-range-input"/>
            <span class="afb-dash">—</span>
            <input v-model.number="episodesTo" type="number" placeholder="До" min="0" class="afb-range-input"/>
          </div>
          <div class="afb-presets">
            <button v-for="ep in EPISODE_PRESETS" :key="ep.label"
              :class="['afb-preset', { active: episodesFrom === ep.from && episodesTo === ep.to }]"
              @click="toggleEpPreset(ep)" type="button">{{ ep.label }}</button>
          </div>
        </div>

        <!-- СТУДИЯ -->
        <div class="afb-group afb-group-full">
          <div class="afb-group-label">Студия</div>
          <div class="afb-search-box">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
            <input v-model="studioSearch" type="text" placeholder="Поиск студии…" class="afb-inline-input"/>
          </div>
          <div v-if="studiosLoading" class="afb-chips">
            <div v-for="i in 8" :key="i" class="afb-genre-skel"></div>
          </div>
          <div v-else class="afb-chips afb-chips-scroll">
            <button v-for="s in filteredStudioList" :key="s"
              :class="['afb-chip', { active: selectedStudios.includes(s) }]"
              @click="toggleStudio(s)" type="button">{{ s }}</button>
          </div>
        </div>

        <!-- РЕЖИМ ЖАНРОВ + СБРОС -->
        <div class="afb-panel-footer">
          <div class="afb-logic-wrap">
            <span class="afb-logic-label">Жанры:</span>
            <div class="afb-logic-toggle">
              <button :class="['afb-logic-btn', { active: genreLogic === 'OR' }]"  @click="setGenreLogic('OR')"  type="button">ИЛИ</button>
              <button :class="['afb-logic-btn', { active: genreLogic === 'AND' }]" @click="setGenreLogic('AND')" type="button">И</button>
            </div>
          </div>
          <div class="afb-panel-footer-right">
            <span class="afb-results-count" v-if="resultsCount != null">
              <strong>{{ resultsCount.toLocaleString('ru-RU') }}</strong> результатов
            </span>
            <button @click="resetAll" class="afb-reset-btn" type="button">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
              Сбросить всё
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ── Активные фильтры (чипы) ───────────────────────────── -->
    <div v-if="activeChips.length > 0" class="afb-active-chips">
      <span class="afb-active-label">Фильтры:</span>
      <div class="afb-active-list">
        <span v-for="chip in activeChips" :key="chip.key" class="afb-active-chip">
          {{ chip.label }}
          <button @click="removeChip(chip.key)" type="button">×</button>
        </span>
      </div>
      <button @click="resetAll" class="afb-clear-all" type="button">Сбросить всё</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'

interface Props {
  /** Показывать фильтр по статусу */
  showStatus?: boolean
  /** Показывать расширенную панель (тип, год, рейтинг и т.д.) */
  showAdvanced?: boolean
  /** Показывать кнопку перемешки */
  showShuffle?: boolean
  /** Текущее состояние перемешки */
  isShuffled?: boolean
  /** Кол-во результатов для отображения */
  resultsCount?: number
  /** Дефолтная сортировка */
  defaultOrdering?: string
  /** Доступные опции сортировки */
  sortOptions?: { value: string; label: string }[]
  /** Показывать выбор кол-ва на странице */
  showPageSize?: boolean
  /** Плейсхолдер поиска */
  searchPlaceholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  showStatus: true,
  showAdvanced: true,
  showShuffle: false,
  isShuffled: false,
  defaultOrdering: '-score',
  showPageSize: false,
  searchPlaceholder: 'Поиск аниме...',
  sortOptions: () => [
    { value: '-score',      label: 'Рейтинг ↓'        },
    { value: 'score',       label: 'Рейтинг ↑'        },
    { value: '-year',       label: 'Год: новее'        },
    { value: 'year',        label: 'Год: старее'       },
    { value: 'title_ru',    label: 'А → Я'             },
    { value: '-title_ru',   label: 'Я → А'             },
    { value: '-episodes',   label: 'Больше серий'      },
    { value: 'episodes',    label: 'Меньше серий'      },
    { value: '-created_at', label: 'Недавно добавлены' },
  ],
})

const emit = defineEmits<{
  change: [filters: FilterState]
  shuffle: []
  unshuffle: []
  refresh: []
}>()

export interface FilterState {
  search?: string
  genres?: string[]
  genre_logic?: 'OR' | 'AND'
  status?: string[]
  type?: string[]
  year_from?: number
  year_to?: number
  score_from?: number
  score_to?: number
  episodes_from?: number
  episodes_to?: number
  studio?: string[]
  ordering?: string
  page_size?: number
}

// ── Константы ──────────────────────────────────────────────
const currentYear = new Date().getFullYear()

const TYPE_OPTIONS = [
  { value: 'tv',      label: 'TV'      },
  { value: 'movie',   label: 'Фильм'   },
  { value: 'ova',     label: 'OVA'     },
  { value: 'ona',     label: 'ONA'     },
  { value: 'special', label: 'Special' },
  { value: 'music',   label: 'Music'   },
]

const STATUS_OPTIONS = [
  { value: 'ongoing',   label: 'Онгоинг',  color: 'green'  },
  { value: 'finished',  label: 'Завершён', color: 'grey'   },
  { value: 'announced', label: 'Анонс',    color: 'yellow' },
  { value: 'canceled',  label: 'Отменён',  color: 'red'    },
]

const YEAR_PRESETS = [
  { label: '2020-е', from: 2020, to: currentYear },
  { label: '2010-е', from: 2010, to: 2019 },
  { label: '2000-е', from: 2000, to: 2009 },
  { label: '90-е',   from: 1990, to: 1999 },
]

const EPISODE_PRESETS = [
  { label: '1–4',   from: 1,  to: 4   },
  { label: '5–13',  from: 5,  to: 13  },
  { label: '14–26', from: 14, to: 26  },
  { label: '27–52', from: 27, to: 52  },
  { label: '52+',   from: 52, to: undefined as number | undefined },
]

// ── Состояние фильтров ─────────────────────────────────────
const search        = ref('')
const ordering      = ref(props.defaultOrdering)
const pageSize      = ref(50)
const panelOpen     = ref(false)
const genreSearch   = ref('')
const studioSearch  = ref('')
const genreLogic    = ref<'OR' | 'AND'>('OR')

const selectedGenres   = ref<string[]>([])
const selectedTypes    = ref<string[]>([])
const selectedStatuses = ref<string[]>([])
const selectedStudios  = ref<string[]>([])

const yearFrom     = ref<number | undefined>(undefined)
const yearTo       = ref<number | undefined>(undefined)
const scoreFrom    = ref<number | undefined>(undefined)
const scoreTo      = ref<number | undefined>(undefined)
const episodesFrom = ref<number | undefined>(undefined)
const episodesTo   = ref<number | undefined>(undefined)

// ── Жанры и студии (загружаем из Kodik) ────────────────────
const allGenres      = ref<string[]>([])
const allStudios     = ref<string[]>([])
const genresLoading  = ref(false)
const studiosLoading = ref(false)

const filteredGenreList = computed(() => {
  const q = genreSearch.value.trim().toLowerCase()
  const pool = q ? allGenres.value.filter(g => g.toLowerCase().includes(q)) : allGenres.value

  // Выбранные жанры показываем в начале списка
  if (selectedGenres.value.length === 0) return pool

  const selected = new Set(selectedGenres.value)
  const selectedItems: string[] = []
  const otherItems: string[] = []

  for (const g of pool) {
    if (selected.has(g)) selectedItems.push(g)
    else otherItems.push(g)
  }

  return [...selectedItems, ...otherItems]
})

const filteredStudioList = computed(() => {
  const q = studioSearch.value.trim().toLowerCase()
  const pool = allStudios.value.slice(0, 80)
  return q ? allStudios.value.filter(s => s.toLowerCase().includes(q)).slice(0, 80) : pool
})

onMounted(async () => {
  // Загрузка жанров
  genresLoading.value = true
  try {
    const res  = await fetch('https://kodikapi.com/genres?token=74ecb013335271e4344ebc994956dd75&types=anime-serial,anime&genres_type=shikimori&sort=count')
    const data = await res.json()
    allGenres.value = (data.results || []).map((g: any) => String(g.title))
  } catch { allGenres.value = [] }
  finally { genresLoading.value = false }

  // Загрузка студий через бэкенд-прокси (CORS блокирует прямой доступ к Kodik)
  studiosLoading.value = true
  try {
    const res = await fetch('/api/anime/kodik/studios/')
    const data = await res.json()
    // Бэкенд возвращает { studios: [{name, count}], total, source }
    allStudios.value = (data.studios || data.results || []).map((s: any) => String(s.name || s.title))
  } catch { allStudios.value = [] }
  finally { studiosLoading.value = false }
})

// ── Debounce поиска ─────────────────────────────────────────
let searchTimer: ReturnType<typeof setTimeout>
const onSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(emitChange, 320)
}

const clearSearch = () => { search.value = ''; emitChange() }

// ── Тоглы ──────────────────────────────────────────────────
const toggleGenre  = (g: string) => { toggle(selectedGenres,   g); emitChange() }
const toggleType   = (t: string) => { toggle(selectedTypes,    t); emitChange() }
const toggleStatus = (s: string) => { toggle(selectedStatuses, s); emitChange() }
const toggleStudio = (s: string) => { toggle(selectedStudios,  s); emitChange() }
const clearGenres  = () => { selectedGenres.value = []; emitChange() }

function toggle(arr: { value: string[] }, val: string) {
  const idx = arr.value.indexOf(val)
  if (idx === -1) arr.value = [...arr.value, val]
  else arr.value = arr.value.filter((_, i) => i !== idx)
}

const setGenreLogic = (l: 'OR' | 'AND') => { genreLogic.value = l; emitChange() }

const toggleYearPreset = (y: { from: number; to: number }) => {
  if (yearFrom.value === y.from && yearTo.value === y.to) {
    yearFrom.value = undefined; yearTo.value = undefined
  } else {
    yearFrom.value = y.from; yearTo.value = y.to
  }
  emitChange()
}

const toggleRatingPreset = (r: number) => {
  if (scoreFrom.value === r && !scoreTo.value) { scoreFrom.value = undefined }
  else { scoreFrom.value = r; scoreTo.value = undefined }
  emitChange()
}

const toggleEpPreset = (ep: { from: number; to: number | undefined }) => {
  if (episodesFrom.value === ep.from && episodesTo.value === ep.to) {
    episodesFrom.value = undefined; episodesTo.value = undefined
  } else {
    episodesFrom.value = ep.from; episodesTo.value = ep.to
  }
  emitChange()
}

// ── Активные фильтры (чипы) ─────────────────────────────────
const activeAdvancedCount = computed(() => {
  let c = 0
  if (selectedTypes.value.length)    c++
  if (selectedStatuses.value.length) c++
  if (yearFrom.value || yearTo.value) c++
  if (scoreFrom.value || scoreTo.value) c++
  if (episodesFrom.value || episodesTo.value) c++
  if (selectedStudios.value.length)  c++
  return c
})

interface Chip { key: string; label: string }
const activeChips = computed((): Chip[] => {
  const chips: Chip[] = []
  if (search.value)              chips.push({ key: 'search',   label: `Поиск: "${search.value}"` })
  if (selectedGenres.value.length)   chips.push({ key: 'genres',   label: `Жанры: ${selectedGenres.value.length}` })
  if (selectedTypes.value.length)    chips.push({ key: 'type',     label: `Тип: ${selectedTypes.value.join(', ')}` })
  if (selectedStatuses.value.length) chips.push({ key: 'status',   label: `Статус: ${selectedStatuses.value.length}` })
  if (yearFrom.value || yearTo.value)   chips.push({ key: 'year',   label: `Год: ${yearFrom.value || '?'}–${yearTo.value || '?'}` })
  if (scoreFrom.value || scoreTo.value) chips.push({ key: 'score',  label: `Рейтинг: ${scoreFrom.value || 0}–${scoreTo.value || 10}` })
  if (selectedStudios.value.length)  chips.push({ key: 'studio',   label: `Студия: ${selectedStudios.value.length}` })
  return chips
})

const removeChip = (key: string) => {
  switch (key) {
    case 'search':  search.value = '';          break
    case 'genres':  selectedGenres.value = [];  break
    case 'type':    selectedTypes.value = [];   break
    case 'status':  selectedStatuses.value = [];break
    case 'year':    yearFrom.value = undefined; yearTo.value = undefined; break
    case 'score':   scoreFrom.value = undefined; scoreTo.value = undefined; break
    case 'studio':  selectedStudios.value = []; break
  }
  emitChange()
}

const resetAll = () => {
  search.value = ''
  ordering.value = props.defaultOrdering
  selectedGenres.value = []
  selectedTypes.value = []
  selectedStatuses.value = []
  selectedStudios.value = []
  yearFrom.value = undefined; yearTo.value = undefined
  scoreFrom.value = undefined; scoreTo.value = undefined
  episodesFrom.value = undefined; episodesTo.value = undefined
  genreLogic.value = 'OR'
  panelOpen.value = false
  emitChange()
}

// ── Emit ────────────────────────────────────────────────────
const emitChange = () => {
  const filters: FilterState = {
    search:        search.value || undefined,
    genres:        selectedGenres.value.length ? selectedGenres.value : undefined,
    genre_logic:   genreLogic.value,
    status:        selectedStatuses.value.length ? selectedStatuses.value : undefined,
    type:          selectedTypes.value.length ? selectedTypes.value : undefined,
    year_from:     yearFrom.value,
    year_to:       yearTo.value,
    score_from:    scoreFrom.value,
    score_to:      scoreTo.value,
    episodes_from: episodesFrom.value,
    episodes_to:   episodesTo.value,
    studio:        selectedStudios.value.length ? selectedStudios.value : undefined,
    ordering:      ordering.value,
    page_size:     pageSize.value,
  }
  emit('change', filters)
}

// watch на числовые поля и селекты (без @change на нативных элементах)
watch([ordering, pageSize, yearFrom, yearTo, scoreFrom, scoreTo, episodesFrom, episodesTo], () => emitChange())

// Первоначальный emit при маунте
onMounted(() => emitChange())
</script>

<style scoped>
/* ══ ROOT ════════════════════════════════════════════════════ */
.afb {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  margin-bottom: var(--space-5);
}

/* ══ ВЕРХНЯЯ СТРОКА ══════════════════════════════════════════ */
.afb-top {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

/* Поиск */
.afb-search {
  position: relative;
  flex: 1;
  min-width: 200px;
}
.afb-search svg:first-child {
  position: absolute; left: 11px; top: 50%; transform: translateY(-50%);
  color: var(--text-tertiary); pointer-events: none;
}
.afb-search-input {
  width: 100%; height: 38px;
  padding: 0 34px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  outline: none;
  transition: border-color .15s;
}
.afb-search-input:focus { border-color: var(--accent); }
.afb-search-input::placeholder { color: var(--text-tertiary); }
.afb-search-clear {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: var(--text-tertiary); cursor: pointer;
  padding: 3px; display: flex; transition: color .15s;
}
.afb-search-clear:hover { color: var(--text-primary); }

/* Select */
.afb-select {
  height: 38px; padding: 0 var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  cursor: pointer; outline: none;
  min-width: 165px;
  transition: border-color .15s;
}
.afb-select:focus { border-color: var(--accent); }
.afb-select-sm { min-width: 80px; }

/* Кнопки действий */
.afb-actions { display: flex; gap: var(--space-2); flex-shrink: 0; }
.afb-btn {
  position: relative;
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all .15s;
}
.afb-btn:hover { background: var(--surface-5); color: var(--text-primary); border-color: var(--border-default); }
.afb-btn-active { background: var(--accent-subtle); border-color: var(--accent); color: var(--accent); }
.afb-btn-active:hover { background: var(--accent); color: white; }

.afb-badge {
  position: absolute; top: -5px; right: -5px;
  min-width: 16px; height: 16px; padding: 0 3px;
  background: var(--accent); color: white;
  border-radius: 8px; font-size: 10px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}

/* ══ ЖАНРЫ ═══════════════════════════════════════════════════ */
.afb-genres-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.afb-genres-label {
  font-size: var(--text-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-tertiary);
  white-space: nowrap;
  flex-shrink: 0;
}
.afb-genres-scroll {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  flex: 1;
  padding-bottom: 2px;
  align-items: center;
}
.afb-genres-scroll::-webkit-scrollbar { display: none; }

.afb-genre-chip {
  flex-shrink: 0;
  height: 28px; padding: 0 11px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  font-size: var(--text-xs); font-weight: 500;
  cursor: pointer; white-space: nowrap;
  transition: all .15s;
}
.afb-genre-chip:hover { background: var(--surface-5); color: var(--text-primary); }
.afb-genre-chip.active { background: var(--accent); border-color: var(--accent); color: white; }

.afb-genre-skel {
  flex-shrink: 0; height: 28px; width: 64px;
  border-radius: var(--radius-full);
  background: linear-gradient(90deg, var(--surface-3) 25%, var(--surface-4) 50%, var(--surface-3) 75%);
  background-size: 400% 100%;
  animation: afb-sk 1.4s ease-in-out infinite;
}
@keyframes afb-sk { from { background-position: 200% 0; } to { background-position: -200% 0; } }

.afb-genre-search {
  display: flex; align-items: center;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  padding: 0 10px;
  gap: 5px;
  flex-shrink: 0;
}
.afb-genre-search svg { color: var(--text-tertiary); flex-shrink: 0; }
.afb-genre-search-input {
  width: 80px; height: 26px;
  background: none; border: none; outline: none;
  color: var(--text-primary); font-size: var(--text-xs);
  transition: width .2s;
}
.afb-genre-search-input:focus { width: 110px; }
.afb-genre-search-input::placeholder { color: var(--text-tertiary); }

/* ══ РАСШИРЕННАЯ ПАНЕЛЬ ══════════════════════════════════════ */
.afb-panel {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}

.afb-group { display: flex; flex-direction: column; gap: 6px; }
.afb-group-full { grid-column: 1 / -1; }

.afb-group-label {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--text-tertiary);
}

.afb-chips {
  display: flex; flex-wrap: wrap; gap: 5px;
}
.afb-chips-scroll { max-height: 100px; overflow-y: auto; scrollbar-width: thin; }

.afb-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-xs); font-weight: 500;
  cursor: pointer; white-space: nowrap;
  transition: all .14s;
}
.afb-chip:hover { border-color: var(--accent); color: var(--text-primary); }
.afb-chip.active { background: var(--accent); border-color: var(--accent); color: white; }

.afb-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
.afb-chip-status-green  .afb-dot { background: #22c55e; }
.afb-chip-status-grey   .afb-dot { background: #64748b; }
.afb-chip-status-yellow .afb-dot { background: #f59e0b; }
.afb-chip-status-red    .afb-dot { background: #ef4444; }
.afb-chip-status-green.active  { background: #16a34a; border-color: #16a34a; }
.afb-chip-status-grey.active   { background: #475569; border-color: #475569; }
.afb-chip-status-yellow.active { background: #d97706; border-color: #d97706; }
.afb-chip-status-red.active    { background: #dc2626; border-color: #dc2626; }

.afb-range-row { display: flex; align-items: center; gap: 6px; }
.afb-range-input {
  flex: 1; min-width: 0;
  padding: 5px 7px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-4);
  color: var(--text-primary);
  font-size: var(--text-xs); font-weight: 600;
  text-align: center; outline: none;
  transition: border-color .15s;
}
.afb-range-input:focus { border-color: var(--accent); }
.afb-range-input::placeholder { color: var(--text-tertiary); font-weight: 400; }
.afb-dash { color: var(--text-tertiary); flex-shrink: 0; font-size: var(--text-xs); }

.afb-presets { display: flex; flex-wrap: wrap; gap: 4px; }
.afb-preset {
  padding: 3px 7px; border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: transparent; color: var(--text-secondary);
  font-size: 0.68rem; font-weight: 600; cursor: pointer; transition: all .14s;
}
.afb-preset:hover { border-color: var(--accent); color: var(--accent); }
.afb-preset.active { background: rgba(var(--accent-rgb, 124 92 252) / .15); border-color: var(--accent); color: var(--accent); }

.afb-search-box {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 9px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-4);
}
.afb-search-box svg { color: var(--text-tertiary); flex-shrink: 0; }
.afb-inline-input {
  flex: 1; border: none; background: transparent;
  color: var(--text-primary); font-size: var(--text-xs); outline: none;
}
.afb-inline-input::placeholder { color: var(--text-tertiary); }

/* Футер панели */
.afb-panel-footer {
  grid-column: 1 / -1;
  display: flex; align-items: center; justify-content: space-between;
  gap: var(--space-3); flex-wrap: wrap;
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-subtle);
}
.afb-panel-footer-right { display: flex; align-items: center; gap: var(--space-4); margin-left: auto; }

.afb-logic-wrap { display: flex; align-items: center; gap: 6px; }
.afb-logic-label { font-size: var(--text-xs); color: var(--text-tertiary); font-weight: 600; white-space: nowrap; }
.afb-logic-toggle {
  display: flex;
  border: 1px solid var(--border-subtle);
  border-radius: 6px; overflow: hidden;
}
.afb-logic-btn {
  padding: 4px 12px; border: none;
  background: transparent; color: var(--text-secondary);
  font-size: var(--text-xs); font-weight: 700; cursor: pointer;
  transition: all .13s;
}
.afb-logic-btn:hover { background: var(--surface-5); color: var(--text-primary); }
.afb-logic-btn.active { background: var(--accent); color: white; }

.afb-results-count {
  font-size: var(--text-sm); color: var(--text-secondary);
}
.afb-results-count strong { color: var(--accent); font-weight: 700; }

.afb-reset-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: transparent; color: var(--text-secondary);
  font-size: var(--text-xs); font-weight: 600; cursor: pointer;
  transition: all .15s;
}
.afb-reset-btn:hover { border-color: #ef4444; color: #ef4444; }

/* ══ АКТИВНЫЕ ЧИПЫ ═══════════════════════════════════════════ */
.afb-active-chips {
  display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap;
}
.afb-active-label {
  font-size: var(--text-xs); font-weight: 600;
  color: var(--text-tertiary); white-space: nowrap;
}
.afb-active-list { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
.afb-active-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px;
  background: var(--accent); color: white;
  border-radius: var(--radius-full);
  font-size: var(--text-xs); font-weight: 500;
}
.afb-active-chip button {
  display: flex; align-items: center; justify-content: center;
  width: 15px; height: 15px;
  background: rgba(255,255,255,.25); border: none; border-radius: 50%;
  color: white; font-size: 13px; cursor: pointer;
  transition: background .15s; line-height: 1;
}
.afb-active-chip button:hover { background: rgba(255,255,255,.45); }
.afb-clear-all {
  padding: 3px 10px;
  background: none; border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full); font-size: var(--text-xs);
  color: var(--text-secondary); cursor: pointer; transition: all .15s;
  white-space: nowrap;
}
.afb-clear-all:hover { border-color: #ef4444; color: #ef4444; }

/* ══ ПЕРЕХОД ════════════════════════════════════════════════ */
.afb-panel-enter-active,
.afb-panel-leave-active { transition: opacity .2s, transform .2s; }
.afb-panel-enter-from,
.afb-panel-leave-to { opacity: 0; transform: translateY(-6px); }

/* ══ АДАПТИВ ════════════════════════════════════════════════ */
@media (max-width: 767px) {
  .afb { padding: var(--space-3); }
  .afb-top { flex-wrap: wrap; }
  .afb-search { min-width: 100%; }
  .afb-select { flex: 1; min-width: 120px; }
  .afb-panel { grid-template-columns: 1fr 1fr; }
  .afb-genre-search-input { width: 70px; }
}
</style>
