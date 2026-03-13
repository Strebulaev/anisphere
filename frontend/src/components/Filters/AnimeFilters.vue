<template>
  <div class="af-root">

    <!-- ════════════════════════════════════════════════════════
         БАЗОВЫЕ ФИЛЬТРЫ
    ════════════════════════════════════════════════════════════ -->

    <!-- СОРТИРОВКА -->
    <div class="af-block">
      <div class="af-block-label">
        <span class="af-label-icon">↕</span>
        Сортировка
      </div>
      <div class="af-sort-grid">
        <button
          v-for="opt in SORT_OPTIONS" :key="opt.value"
          :class="['af-sort-btn', { active: localFilters.ordering === opt.value }]"
          @click="setSort(opt.value)" type="button"
        >{{ opt.label }}</button>
      </div>
    </div>

    <!-- РАЗДЕЛИТЕЛЬ -->
    <div class="af-divider"></div>

    <!-- ТИП + СТАТУС -->
    <div class="af-two-col">
      <div class="af-block">
        <div class="af-block-label">
          <span class="af-label-icon">▣</span>
          Тип
          <span v-if="selectedTypes.length" class="af-badge">{{ selectedTypes.length }}</span>
        </div>
        <div class="af-chips">
          <button
            v-for="t in TYPE_OPTIONS" :key="t.value"
            :class="['af-chip', { active: selectedTypes.includes(t.value) }]"
            @click="toggleMulti('type', t.value)" type="button"
          >{{ t.label }}</button>
        </div>
      </div>

      <div class="af-block">
        <div class="af-block-label">
          <span class="af-label-icon">◉</span>
          Статус
          <span v-if="selectedStatuses.length" class="af-badge">{{ selectedStatuses.length }}</span>
        </div>
        <div class="af-chips">
          <button
            v-for="s in STATUS_OPTIONS" :key="s.value"
            :class="['af-chip', `af-chip-status-${s.color}`, { active: selectedStatuses.includes(s.value) }]"
            @click="toggleMulti('status', s.value)" type="button"
          >
            <span class="af-dot"></span>{{ s.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- РАЗДЕЛИТЕЛЬ -->
    <div class="af-divider"></div>

    <!-- ГОД + РЕЙТИНГ -->
    <div class="af-two-col">
      <div class="af-block">
        <div class="af-block-label">
          <span class="af-label-icon">📅</span>
          Год выпуска
        </div>
        <div class="af-range-row">
          <input v-model.number="localFilters.year_from" @change="emitChange" type="number"
            placeholder="От" min="1960" :max="currentYear + 1" class="af-input-range" />
          <span class="af-dash">—</span>
          <input v-model.number="localFilters.year_to" @change="emitChange" type="number"
            placeholder="До" min="1960" :max="currentYear + 1" class="af-input-range" />
        </div>
        <div class="af-presets">
          <button v-for="y in YEAR_PRESETS" :key="y.label"
            :class="['af-preset', { active: localFilters.year_from === y.from && localFilters.year_to === y.to }]"
            @click="toggleYearPreset(y.from, y.to)" type="button">{{ y.label }}</button>
        </div>
      </div>

      <div class="af-block">
        <div class="af-block-label">
          <span class="af-label-icon">★</span>
          Рейтинг
        </div>
        <div class="af-range-row">
          <input v-model.number="localFilters.score_from" @change="emitChange" type="number"
            placeholder="От" min="0" max="10" step="0.1" class="af-input-range" />
          <span class="af-dash">—</span>
          <input v-model.number="localFilters.score_to" @change="emitChange" type="number"
            placeholder="До" min="0" max="10" step="0.1" class="af-input-range" />
        </div>
        <div class="af-presets">
          <button v-for="r in RATING_PRESETS" :key="r"
            :class="['af-preset', { active: localFilters.score_from === r && !localFilters.score_to }]"
            @click="toggleRatingPreset(r)" type="button">{{ r }}+</button>
        </div>
      </div>
    </div>

    <!-- РАЗДЕЛИТЕЛЬ -->
    <div class="af-divider"></div>

    <!-- ЖАНРЫ -->
    <div class="af-block">
      <div class="af-genre-header">
        <div class="af-block-label">
          <span class="af-label-icon">🏷</span>
          Жанры
          <span v-if="selectedGenres.length" class="af-badge">{{ selectedGenres.length }}</span>
        </div>
        <!-- И / ИЛИ — ключевой контрол, видим всегда -->
        <div class="af-logic-wrap">
          <span class="af-logic-label">Режим:</span>
          <div class="af-logic-toggle">
            <button
              :class="['af-logic-btn', { active: genreLogic === 'OR' }]"
              @click="setGenreLogic('OR')" type="button"
              title="Аниме содержит хотя бы один из выбранных жанров"
            >ИЛИ</button>
            <button
              :class="['af-logic-btn', { active: genreLogic === 'AND' }]"
              @click="setGenreLogic('AND')" type="button"
              title="Аниме содержит все выбранные жанры одновременно"
            >И</button>
          </div>
        </div>
      </div>

      <div v-if="selectedGenres.length > 1" class="af-logic-hint">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
        {{ genreLogic === 'AND'
          ? `Поиск аниме со всеми ${selectedGenres.length} жанрами одновременно`
          : `Поиск аниме с хотя бы одним из ${selectedGenres.length} жанров` }}
      </div>

      <div class="af-search-box">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <input v-model="genreSearch" type="text" placeholder="Поиск жанра..." class="af-search-input" />
        <button v-if="genreSearch" @click="genreSearch = ''" class="af-search-clear" type="button">×</button>
      </div>

      <div v-if="genresLoading" class="af-chips af-chips-loading">
        <div v-for="i in 18" :key="i" class="af-skel"></div>
      </div>
      <div v-else-if="filteredGenres.length" class="af-chips af-chips-scroll">
        <button
          v-for="g in filteredGenres" :key="g"
          :class="['af-chip', { active: selectedGenres.includes(g) }]"
          @click="toggleMulti('genres', g)" type="button"
        >{{ g }}</button>
      </div>
      <div v-else class="af-empty-msg">Ничего не найдено</div>

      <div class="af-row-actions">
        <button @click="selectAllVisible" class="af-link-btn" type="button">Выбрать видимые</button>
        <button @click="clearGenres" class="af-link-btn af-link-danger" type="button">Сбросить</button>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════
         РАСШИРЕННЫЕ ФИЛЬТРЫ
    ════════════════════════════════════════════════════════════ -->
    <div class="af-accordion">
      <button
        class="af-accordion-trigger"
        :class="{ open: extOpen }"
        @click="extOpen = !extOpen"
        type="button"
      >
        <span class="af-acc-icon">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 6h18M8 12h8M13 18h-2"/></svg>
        </span>
        <span>Расширенные фильтры</span>
        <span v-if="extActiveCount" class="af-badge af-badge-accent">{{ extActiveCount }}</span>
        <svg class="af-chevron" :class="{ rotated: extOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
      </button>
      <div class="af-accordion-body" :class="{ open: extOpen }">
        <div class="af-accordion-inner">

          <!-- СТУДИЯ -->
          <div class="af-block">
            <div class="af-block-label">
              <span class="af-label-icon">🏠</span>
              Студия
              <span v-if="selectedStudios.length" class="af-badge">{{ selectedStudios.length }}</span>
            </div>
            <div class="af-search-box">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
              <input v-model="studioSearch" type="text" placeholder="Поиск студии..." class="af-search-input" />
              <button v-if="studioSearch" @click="studioSearch = ''" class="af-search-clear" type="button">×</button>
            </div>
            <div v-if="studiosLoading" class="af-chips af-chips-loading">
              <div v-for="i in 8" :key="i" class="af-skel"></div>
            </div>
            <div v-else class="af-chips af-chips-scroll">
              <button v-for="s in filteredStudios" :key="s"
                :class="['af-chip', { active: selectedStudios.includes(s) }]"
                @click="toggleMulti('studio', s)" type="button">{{ s }}</button>
            </div>
            <div class="af-row-actions">
              <button @click="clearStudios" class="af-link-btn af-link-danger" type="button">Сбросить</button>
            </div>
          </div>

          <div class="af-divider"></div>

          <!-- ЭПИЗОДЫ -->
          <div class="af-block">
            <div class="af-block-label">
              <span class="af-label-icon">🎬</span>
              Количество эпизодов
            </div>
            <div class="af-range-row">
              <input v-model.number="localFilters.episodes_from" @change="emitChange" type="number"
                placeholder="От" min="0" class="af-input-range" />
              <span class="af-dash">—</span>
              <input v-model.number="localFilters.episodes_to" @change="emitChange" type="number"
                placeholder="До" min="0" class="af-input-range" />
            </div>
            <div class="af-presets">
              <button v-for="ep in EPISODE_PRESETS" :key="ep.label"
                :class="['af-preset', { active: localFilters.episodes_from === ep.from && localFilters.episodes_to === ep.to }]"
                @click="toggleEpPreset(ep.from, ep.to)" type="button">{{ ep.label }}</button>
            </div>
          </div>

        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════
         ОЧЕНЬ РАСШИРЕННЫЕ ФИЛЬТРЫ
    ════════════════════════════════════════════════════════════ -->
    <div class="af-accordion">
      <button
        class="af-accordion-trigger"
        :class="{ open: deepOpen }"
        @click="deepOpen = !deepOpen"
        type="button"
      >
        <span class="af-acc-icon">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93l-1.41 1.41M4.93 4.93l1.41 1.41M4.93 19.07l1.41-1.41M19.07 19.07l-1.41-1.41M20 12h2M2 12h2M12 20v2M12 2v2"/></svg>
        </span>
        <span>Очень расширенные фильтры</span>
        <span v-if="deepActiveCount" class="af-badge af-badge-accent">{{ deepActiveCount }}</span>
        <svg class="af-chevron" :class="{ rotated: deepOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
      </button>
      <div class="af-accordion-body" :class="{ open: deepOpen }">
        <div class="af-accordion-inner">

          <!-- РЕЖИССЁР + АВТОР -->
          <div class="af-two-col">
            <div class="af-block">
              <div class="af-block-label">
                <span class="af-label-icon">🎥</span>
                Режиссёр
              </div>
              <input v-model="localFilters.director" @input="debouncedEmit"
                type="text" placeholder="Имя режиссёра..." class="af-text-input" />
            </div>
            <div class="af-block">
              <div class="af-block-label">
                <span class="af-label-icon">✍</span>
                Автор оригинала
              </div>
              <input v-model="localFilters.author" @input="debouncedEmit"
                type="text" placeholder="Имя автора..." class="af-text-input" />
            </div>
          </div>

          <div class="af-divider"></div>

          <!-- СТРАНА -->
          <div class="af-block">
            <div class="af-block-label">
              <span class="af-label-icon">🌍</span>
              Страна производства
              <span v-if="selectedCountries.length" class="af-badge">{{ selectedCountries.length }}</span>
            </div>
            <div class="af-chips">
              <button v-for="c in COUNTRY_OPTIONS" :key="c.value"
                :class="['af-chip', { active: selectedCountries.includes(c.value) }]"
                @click="toggleCountry(c.value)" type="button">{{ c.label }}</button>
            </div>
          </div>

          <div class="af-divider"></div>

          <!-- ВОЗРАСТНОЙ РЕЙТИНГ -->
          <div class="af-block">
            <div class="af-block-label">
              <span class="af-label-icon">🔞</span>
              Возрастной рейтинг
              <span v-if="selectedAgeRatings.length" class="af-badge">{{ selectedAgeRatings.length }}</span>
            </div>
            <div class="af-chips">
              <button v-for="a in AGE_OPTIONS" :key="a.value"
                :class="['af-chip', `af-chip-age-${a.color}`, { active: selectedAgeRatings.includes(a.value) }]"
                @click="toggleAgeRating(a.value)" type="button">{{ a.label }}</button>
            </div>
          </div>

          <div class="af-divider"></div>

          <!-- СЕЗОН -->
          <div class="af-block">
            <div class="af-block-label">
              <span class="af-label-icon">🌸</span>
              Сезон выхода
            </div>
            <div class="af-chips">
              <button v-for="s in SEASON_OPTIONS" :key="s.value"
                :class="['af-chip', { active: localFilters.season === s.value }]"
                @click="toggleSeason(s.value)" type="button">{{ s.label }}</button>
            </div>
            <transition name="af-fade">
              <div v-if="localFilters.season" class="af-season-year">
                <label class="af-season-year-label">Год сезона:</label>
                <input v-model.number="localFilters.season_year" @change="emitChange"
                  type="number" :placeholder="String(currentYear)"
                  :min="1960" :max="currentYear + 1" class="af-input-range" style="max-width: 110px" />
              </div>
            </transition>
          </div>

        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════════════════════
         ФУТЕР
    ════════════════════════════════════════════════════════════ -->
    <div class="af-footer">
      <div class="af-results" v-if="resultsCount !== undefined">
        <strong>{{ resultsCount.toLocaleString('ru-RU') }}</strong>
        <span>результатов</span>
      </div>
      <div class="af-footer-btns">
        <button @click="resetAll" class="af-btn af-btn-ghost" type="button">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
          Сбросить всё
        </button>
        <button @click="emitChange" class="af-btn af-btn-primary" type="button">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          Применить
        </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import type { AnimeFilters as AnimeFiltersType } from '@/api/anime'

// Расширяем тип локально — studio/country/age_rating уже есть в AnimeFiltersType
type LocalFilters = AnimeFiltersType & {
  studio?: string[]
  country?: string[]
  age_rating?: string[]
}

const props = defineProps<{
  modelValue?: LocalFilters
  resultsCount?: number
}>()

const emit = defineEmits<{
  'update:modelValue': [v: LocalFilters]
  'filter-change': [v: LocalFilters]
}>()

// ─── Константы ────────────────────────────────────────────────────────────────
const KODIK_TOKEN = '74ecb013335271e4344ebc994956dd75'
const KODIK_BASE  = 'https://kodikapi.com'
const currentYear = new Date().getFullYear()

// created_at — дата добавления записи в БД
// Новые аниме в БД = большее created_at = сортировка DESC (-created_at)
// Старые записи в БД = меньшее created_at = сортировка ASC (created_at)
const SORT_OPTIONS = [
  { value: '-score',      label: 'Рейтинг ↓'            },
  { value: 'score',       label: 'Рейтинг ↑'            },
  { value: '-year',       label: 'Год: новее'            },
  { value: 'year',        label: 'Год: старее'           },
  { value: 'title_ru',    label: 'А → Я'                 },
  { value: '-title_ru',   label: 'Я → А'                 },
  { value: '-episodes',   label: 'Больше серий'          },
  { value: 'episodes',    label: 'Меньше серий'          },
  { value: '-created_at', label: 'Недавно добавлены'     },
  { value: 'created_at',  label: 'Давно добавлены'       },
]

const TYPE_OPTIONS = [
  { value: 'tv',      label: 'TV'      },
  { value: 'movie',   label: 'Фильм'   },
  { value: 'ova',     label: 'OVA'     },
  { value: 'ona',     label: 'ONA'     },
  { value: 'special', label: 'Special' },
  { value: 'music',   label: 'Music'   },
]

// Значения = STATUS_CHOICES в models.py: ongoing/finished/announced/canceled
const STATUS_OPTIONS = [
  { value: 'ongoing',   label: 'Онгоинг',  color: 'green'  },
  { value: 'finished',  label: 'Завершён', color: 'grey'   },
  { value: 'announced', label: 'Анонс',    color: 'yellow' },
  { value: 'canceled',  label: 'Отменён',  color: 'red'    },
]

const YEAR_PRESETS = [
  { label: '2020-е',   from: 2020, to: currentYear },
  { label: '2010-е', from: 2010, to: 2019 },
  { label: '2000-е', from: 2000, to: 2009 },
  { label: '90-е',   from: 1990, to: 1999 },
]

const RATING_PRESETS = [9, 8, 7, 6]

const EPISODE_PRESETS = [
  { label: '1–4',   from: 1,  to: 4         },
  { label: '5–13',  from: 5,  to: 13        },
  { label: '14–26', from: 14, to: 26        },
  { label: '27–52', from: 27, to: 52        },
  { label: '52+',   from: 52, to: undefined },
]

const COUNTRY_OPTIONS = [
  { value: 'Япония', label: '🇯🇵 Япония' },
  { value: 'Китай',  label: '🇨🇳 Китай'  },
  { value: 'Корея',  label: '🇰🇷 Корея'  },
  { value: 'США',    label: '🇺🇸 США'    },
  { value: 'Россия', label: '🇷🇺 Россия' },
]

const AGE_OPTIONS = [
  { value: 'G',     label: 'G',     color: 'green'  },
  { value: 'PG',    label: 'PG',    color: 'blue'   },
  { value: 'PG-13', label: 'PG-13', color: 'yellow' },
  { value: 'R',     label: 'R',     color: 'orange' },
  { value: 'R+',    label: 'R+',    color: 'red'    },
  { value: 'Rx',    label: 'Rx',    color: 'purple' },
]

const SEASON_OPTIONS = [
  { value: 'winter', label: '❄️ Зима'  },
  { value: 'spring', label: '🌸 Весна' },
  { value: 'summer', label: '☀️ Лето'  },
  { value: 'fall',   label: '🍂 Осень' },
]

// ─── Состояние ──────────────────────────────────────────────────────────────
const localFilters = reactive<LocalFilters>({
  ordering:      '-score',
  genres:        [],
  genre_logic:   'OR',
  status:        [],
  type:          [],
  year_from:     undefined,
  year_to:       undefined,
  score_from:    undefined,
  score_to:      undefined,
  episodes_from: undefined,
  episodes_to:   undefined,
  author:        '',
  director:      '',
  studio:        [],
  country:       [],
  age_rating:    [],
  season:        undefined,
  season_year:   undefined,
  
})

// ВАЖНО: genre_logic хранится отдельным ref чтобы обновления были гарантированно
// реактивными и не перетирались при Object.assign из modelValue
const genreLogic = ref<'OR' | 'AND'>('OR')

watch(genreLogic, () => {
  localFilters.genre_logic = genreLogic.value
  emitChange()
})

const genreSearch  = ref('')
const studioSearch = ref('')

const genresLoading  = ref(false)
const studiosLoading = ref(false)

const rawGenres  = ref<string[]>([])
const rawStudios = ref<string[]>([])

const extOpen  = ref(false)
const deepOpen = ref(false)

// ─── Computed ────────────────────────────────────────────────────────────────
const selectedGenres    = computed((): string[] => (localFilters.genres    as string[]) ?? [])
const selectedTypes     = computed((): string[] => (localFilters.type      as string[]) ?? [])
const selectedStatuses  = computed((): string[] => (localFilters.status    as string[]) ?? [])
const selectedStudios   = computed((): string[] =>  localFilters.studio    ?? [])
const selectedCountries = computed((): string[] =>  localFilters.country   ?? [])
const selectedAgeRatings= computed((): string[] =>  localFilters.age_rating ?? [])

const filteredGenres = computed(() => {
  const q = genreSearch.value.trim().toLowerCase()
  const selected = selectedGenres.value
  const pool = q ? rawGenres.value.filter(g => g.toLowerCase().includes(q)) : rawGenres.value
  // Выбранные жанры всегда идут первыми
  const selectedInPool = pool.filter(g => selected.includes(g))
  const unselectedInPool = pool.filter(g => !selected.includes(g))
  return [...selectedInPool, ...unselectedInPool]
})

const filteredStudios = computed(() => {
  const q = studioSearch.value.trim().toLowerCase()
  const selected = selectedStudios.value
  const pool = q ? rawStudios.value.filter(s => s.toLowerCase().includes(q)).slice(0, 80) : rawStudios.value.slice(0, 80)
  // Выбранные студии всегда идут первыми
  const selectedInPool = pool.filter(s => selected.includes(s))
  const unselectedInPool = pool.filter(s => !selected.includes(s))
  return [...selectedInPool, ...unselectedInPool]
})

const extActiveCount = computed(() => {
  let c = 0
  if (selectedStudios.value.length) c++
  if (localFilters.episodes_from != null || localFilters.episodes_to != null) c++
  return c
})

const deepActiveCount = computed(() => {
  let c = 0
  if (localFilters.director)            c++
  if (localFilters.author)              c++
  if (selectedCountries.value.length)   c++
  if (selectedAgeRatings.value.length)  c++
  if (localFilters.season)              c++
  return c
})

// ─── Fetch ───────────────────────────────────────────────────────────────────
const fetchGenres = async () => {
  genresLoading.value = true
  try {
    const res  = await fetch(`${KODIK_BASE}/genres?token=${KODIK_TOKEN}&types=anime-serial,anime&genres_type=shikimori&sort=count`)
    const data = await res.json()
    // count у Kodik = кол-во релизов (серий/переводов), не уникальных аниме —
    // поэтому цифры не показываем вообще, только названия жанров
    rawGenres.value = (data.results ?? []).map((g: any) => String(g.title))
  } catch { /* тихо игнорируем */ }
  finally { genresLoading.value = false }
}

const fetchStudios = async () => {
  studiosLoading.value = true
  try {
    const res  = await fetch(`${KODIK_BASE}/anime_studios?token=${KODIK_TOKEN}&types=anime-serial,anime&sort=count`)
    const data = await res.json()
    rawStudios.value = (data.results ?? []).map((s: any) => String(s.title))
  } catch { /* тихо игнорируем */ }
  finally { studiosLoading.value = false }
}

onMounted(() => {
  fetchGenres()
  fetchStudios()
})

// Синхронизация от родителя — НЕ затираем genreLogic если он уже выставлен
watch(() => props.modelValue, (v) => {
  if (!v) return
  const { genre_logic, ...rest } = v
  Object.assign(localFilters, rest)
  if (genre_logic && genre_logic !== genreLogic.value) {
    genreLogic.value = genre_logic
  }
}, { deep: true, immediate: true })

// ─── Мутаторы ────────────────────────────────────────────────────────────────
function toggleMulti(field: 'genres' | 'type' | 'status' | 'studio', val: string) {
  const cur: string[] = ((localFilters as any)[field] as string[]) ?? []
  const next = cur.includes(val) ? cur.filter(x => x !== val) : [...cur, val]
  ;(localFilters as any)[field] = next
  emitChange()
}

function setGenreLogic(logic: 'OR' | 'AND') {
  genreLogic.value = logic
  // emitChange вызывается через watcher genreLogic
}

const selectAllVisible = () => {
  const existing = selectedGenres.value
  const toAdd = filteredGenres.value.filter(g => !existing.includes(g))
  localFilters.genres = [...existing, ...toAdd]
  emitChange()
}

const clearGenres  = () => { localFilters.genres  = []; emitChange() }
const clearStudios = () => { localFilters.studio  = []; emitChange() }

function toggleCountry(v: string) {
  const arr = [...selectedCountries.value]
  const i = arr.indexOf(v)
  if (i > -1) arr.splice(i, 1); else arr.push(v)
  localFilters.country = arr
  emitChange()
}

function toggleAgeRating(v: string) {
  const arr = [...selectedAgeRatings.value]
  const i = arr.indexOf(v)
  if (i > -1) arr.splice(i, 1); else arr.push(v)
  localFilters.age_rating = arr
  emitChange()
}

function toggleSeason(v: string) {
  if (localFilters.season === (v as any)) {
    localFilters.season      = undefined
    localFilters.season_year = undefined
  } else {
    localFilters.season = v as any
    if (!localFilters.season_year) localFilters.season_year = currentYear
  }
  emitChange()
}

// ─── Пресеты ─────────────────────────────────────────────────────────────────
const setSort = (val: string) => { localFilters.ordering = val as any; emitChange() }

function toggleYearPreset(from: number, to: number) {
  const on = localFilters.year_from === from && localFilters.year_to === to
  localFilters.year_from = on ? undefined : from
  localFilters.year_to   = on ? undefined : to
  emitChange()
}

function toggleRatingPreset(from: number) {
  if (localFilters.score_from === from && !localFilters.score_to) {
    localFilters.score_from = undefined
  } else {
    localFilters.score_from = from
    localFilters.score_to   = undefined
  }
  emitChange()
}

function toggleEpPreset(from: number, to: number | undefined) {
  const on = localFilters.episodes_from === from && localFilters.episodes_to === to
  localFilters.episodes_from = on ? undefined : from
  localFilters.episodes_to   = on ? undefined : to
  emitChange()
}

// ─── Emit / Reset ─────────────────────────────────────────────────────────────
function emitChange() {
  const out: LocalFilters = { ...localFilters, genre_logic: genreLogic.value }
  emit('update:modelValue', out)
  emit('filter-change', out)
}

let _deb: ReturnType<typeof setTimeout> | undefined
const debouncedEmit = () => { clearTimeout(_deb); _deb = setTimeout(emitChange, 380) }

function resetAll() {
  Object.assign(localFilters, {
    ordering: '-score', genres: [], status: [], type: [],
    year_from: undefined, year_to: undefined,
    score_from: undefined, score_to: undefined,
    episodes_from: undefined, episodes_to: undefined,
    author: '', director: '',
    studio: [], country: [], age_rating: [],
    season: undefined, season_year: undefined,
  })
  genreLogic.value = 'OR'
  emitChange()
}
</script>

<style scoped>
/* ══ ROOT ═══════════════════════════════════════════════════════════════════ */
.af-root {
  display: flex;
  flex-direction: column;
  gap: 1.125rem;
}

/* ══ DIVIDER ════════════════════════════════════════════════════════════════ */
.af-divider {
  height: 1px;
  background: var(--color-divider, rgba(255,255,255,.07));
  margin: 0;
}

/* ══ BLOCK ══════════════════════════════════════════════════════════════════ */
.af-block {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.af-block-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--color-text-secondary, #888);
}
.af-label-icon {
  font-size: 0.8rem;
  line-height: 1;
}

/* ══ TWO-COL ════════════════════════════════════════════════════════════════ */
.af-two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.125rem;
}
@media (max-width: 540px) {
  .af-two-col { grid-template-columns: 1fr; }
}

/* ══ SORT ═══════════════════════════════════════════════════════════════════ */
.af-sort-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.af-sort-btn {
  padding: 5px 12px;
  border-radius: 20px;
  border: 1px solid var(--color-divider, rgba(255,255,255,.1));
  background: transparent;
  color: var(--color-text-secondary, #999);
  font-size: 0.775rem;
  font-weight: 600;
  cursor: pointer;
  transition: all .15s;
  white-space: nowrap;
}
.af-sort-btn:hover  { border-color: var(--color-accent, #3a86ff); color: var(--color-accent, #3a86ff); }
.af-sort-btn.active { background: var(--color-accent, #3a86ff); border-color: var(--color-accent, #3a86ff); color: #fff; }

/* ══ CHIPS ══════════════════════════════════════════════════════════════════ */
.af-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.af-chips-scroll {
  max-height: 140px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,.12) transparent;
}
.af-chips-scroll::-webkit-scrollbar { width: 3px; }
.af-chips-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,.15); border-radius: 2px; }

.af-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 11px;
  border-radius: 20px;
  border: 1px solid var(--color-divider, rgba(255,255,255,.1));
  background: transparent;
  color: var(--color-text-secondary, #999);
  font-size: 0.775rem;
  font-weight: 500;
  cursor: pointer;
  transition: all .14s;
  white-space: nowrap;
  user-select: none;
}
.af-chip:hover  { border-color: var(--color-accent, #3a86ff); color: var(--color-text, #fff); }
.af-chip.active { background: var(--color-accent, #3a86ff); border-color: var(--color-accent, #3a86ff); color: #fff; }

/* Status dot */
.af-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
.af-chip-status-green  .af-dot  { background: #22c55e; }
.af-chip-status-grey   .af-dot  { background: #64748b; }
.af-chip-status-yellow .af-dot  { background: #f59e0b; }
.af-chip-status-red    .af-dot  { background: #ef4444; }
.af-chip-status-green.active    { background: #16a34a; border-color: #16a34a; }
.af-chip-status-grey.active     { background: #475569; border-color: #475569; }
.af-chip-status-yellow.active   { background: #d97706; border-color: #d97706; }
.af-chip-status-red.active      { background: #dc2626; border-color: #dc2626; }

/* Age rating */
.af-chip-age-green.active  { background: #15803d; border-color: #15803d; }
.af-chip-age-blue.active   { background: #1d4ed8; border-color: #1d4ed8; }
.af-chip-age-yellow.active { background: #b45309; border-color: #b45309; }
.af-chip-age-orange.active { background: #c2410c; border-color: #c2410c; }
.af-chip-age-red.active    { background: #b91c1c; border-color: #b91c1c; }
.af-chip-age-purple.active { background: #6b21a8; border-color: #6b21a8; }

/* Skeletons */
.af-chips-loading { pointer-events: none; }
.af-skel {
  height: 29px; width: 68px; border-radius: 20px;
  background: linear-gradient(90deg,
    rgba(255,255,255,.04) 25%, rgba(255,255,255,.09) 50%, rgba(255,255,255,.04) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer { to { background-position: -200% 0; } }

/* ══ GENRE HEADER ═══════════════════════════════════════════════════════════ */
.af-genre-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

/* ══ LOGIC TOGGLE ═══════════════════════════════════════════════════════════ */
.af-logic-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.af-logic-label {
  font-size: 0.72rem;
  color: var(--color-text-tertiary, #666);
  font-weight: 600;
  white-space: nowrap;
}
.af-logic-toggle {
  display: flex;
  border: 1px solid var(--color-divider, rgba(255,255,255,.12));
  border-radius: 6px;
  overflow: hidden;
}
.af-logic-btn {
  padding: 4px 13px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary, #999);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: .04em;
  cursor: pointer;
  transition: all .13s;
  position: relative;
}
.af-logic-btn + .af-logic-btn::before {
  content: '';
  position: absolute; left: 0; top: 20%; bottom: 20%;
  width: 1px;
  background: var(--color-divider, rgba(255,255,255,.12));
}
.af-logic-btn:hover { color: var(--color-text, #fff); background: rgba(255,255,255,.05); }
.af-logic-btn.active { background: var(--color-accent, #3a86ff); color: #fff; }

.af-logic-hint {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 9px;
  border-radius: 6px;
  background: rgba(58,134,255,.08);
  border: 1px solid rgba(58,134,255,.2);
  font-size: 0.72rem;
  color: var(--color-accent, #3a86ff);
  font-style: italic;
}

/* ══ SEARCH BOX ═════════════════════════════════════════════════════════════ */
.af-search-box {
  display: flex; align-items: center; gap: 7px;
  padding: 6px 10px;
  border: 1px solid var(--color-divider, rgba(255,255,255,.1));
  border-radius: 8px;
  background: var(--color-background-active, rgba(255,255,255,.04));
  transition: border-color .15s;
}
.af-search-box:focus-within { border-color: var(--color-accent, #3a86ff); }
.af-search-input {
  flex: 1; border: none; background: transparent;
  color: var(--color-text, #fff); font-size: 0.82rem; outline: none;
}
.af-search-input::placeholder { color: var(--color-text-tertiary, #555); }
.af-search-clear {
  background: none; border: none; cursor: pointer;
  color: var(--color-text-tertiary, #555); font-size: 1.1rem; line-height: 1;
  padding: 0; transition: color .15s;
}
.af-search-clear:hover { color: #ef4444; }

/* ══ RANGE ══════════════════════════════════════════════════════════════════ */
.af-range-row { display: flex; align-items: center; gap: 7px; }
.af-input-range {
  flex: 1; min-width: 0;
  padding: 6px 8px;
  border: 1px solid var(--color-divider, rgba(255,255,255,.1));
  border-radius: 7px;
  background: var(--color-background-active, rgba(255,255,255,.04));
  color: var(--color-text, #fff);
  font-size: 0.83rem; font-weight: 600; text-align: center; outline: none;
  transition: border-color .15s;
}
.af-input-range:focus { border-color: var(--color-accent, #3a86ff); }
.af-input-range::placeholder { color: var(--color-text-tertiary, #444); font-weight: 400; }
.af-dash { color: var(--color-text-tertiary, #555); font-weight: 600; flex-shrink: 0; }

/* ══ PRESETS ════════════════════════════════════════════════════════════════ */
.af-presets { display: flex; flex-wrap: wrap; gap: 4px; }
.af-preset {
  padding: 3px 8px; border-radius: 5px;
  border: 1px solid var(--color-divider, rgba(255,255,255,.1));
  background: transparent; color: var(--color-text-secondary, #999);
  font-size: 0.7rem; font-weight: 600; cursor: pointer; transition: all .14s;
}
.af-preset:hover { border-color: var(--color-accent, #3a86ff); color: var(--color-accent, #3a86ff); }
.af-preset.active { background: rgba(58,134,255,.13); border-color: var(--color-accent, #3a86ff); color: var(--color-accent, #3a86ff); }

/* ══ MICRO ACTIONS ══════════════════════════════════════════════════════════ */
.af-row-actions { display: flex; align-items: center; gap: 12px; }
.af-link-btn {
  background: none; border: none; cursor: pointer; padding: 0;
  font-size: 0.73rem; font-weight: 600;
  color: var(--color-text-secondary, #888);
  transition: color .14s;
}
.af-link-btn:hover   { color: var(--color-accent, #3a86ff); }
.af-link-danger:hover { color: #ef4444; }

/* ══ BADGE ══════════════════════════════════════════════════════════════════ */
.af-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 17px; height: 17px; padding: 0 4px;
  border-radius: 8px;
  background: rgba(255,255,255,.13);
  color: #fff; font-size: 0.63rem; font-weight: 800;
}
.af-badge-accent { background: var(--color-accent, #3a86ff); }

/* ══ EMPTY ══════════════════════════════════════════════════════════════════ */
.af-empty-msg { font-size: 0.8rem; color: var(--color-text-tertiary, #555); padding: 4px 0; }

/* ══ TEXT INPUT ═════════════════════════════════════════════════════════════ */
.af-text-input {
  width: 100%; padding: 7px 10px;
  border: 1px solid var(--color-divider, rgba(255,255,255,.1));
  border-radius: 7px;
  background: var(--color-background-active, rgba(255,255,255,.04));
  color: var(--color-text, #fff); font-size: 0.83rem; outline: none;
  transition: border-color .15s;
}
.af-text-input:focus { border-color: var(--color-accent, #3a86ff); }
.af-text-input::placeholder { color: var(--color-text-tertiary, #444); }

/* ══ SEASON YEAR ════════════════════════════════════════════════════════════ */
.af-season-year {
  display: flex; align-items: center; gap: 8px;
  margin-top: 2px;
}
.af-season-year-label { font-size: 0.77rem; color: var(--color-text-secondary, #888); white-space: nowrap; }

/* ══ ACCORDION ══════════════════════════════════════════════════════════════ */
.af-accordion {
  border: 1px solid var(--color-divider, rgba(255,255,255,.1));
  border-radius: 10px;
  overflow: hidden;
}

.af-accordion-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 13px;
  background: var(--color-background-active, rgba(255,255,255,.04));
  border: none;
  color: var(--color-text-secondary, #aaa);
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  text-align: left;
  transition: background .15s, color .15s;
}
.af-accordion-trigger:hover,
.af-accordion-trigger.open {
  background: rgba(255,255,255,.07);
  color: var(--color-text, #fff);
}
.af-acc-icon { display: flex; align-items: center; opacity: .7; }
.af-chevron { margin-left: auto; flex-shrink: 0; transition: transform .25s; opacity: .6; }
.af-chevron.rotated { transform: rotate(180deg); }

.af-accordion-body {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows .28s ease;
  border-top: 0px solid transparent;
}
.af-accordion-body.open {
  grid-template-rows: 1fr;
  border-top: 1px solid var(--color-divider, rgba(255,255,255,.07));
}
.af-accordion-inner {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 0;
  transition: padding .28s ease;
}
.af-accordion-body.open .af-accordion-inner {
  padding: 13px;
}

/* ══ FOOTER ═════════════════════════════════════════════════════════════════ */
.af-footer {
  display: flex; align-items: center; justify-content: space-between;
  gap: 10px; flex-wrap: wrap; padding-top: 2px;
}
.af-results {
  display: flex; align-items: baseline; gap: 4px;
  font-size: 0.82rem; color: var(--color-text-secondary, #888);
}
.af-results strong { color: var(--color-accent, #3a86ff); font-weight: 800; font-size: 0.9rem; }
.af-footer-btns { display: flex; gap: 7px; margin-left: auto; }

.af-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 7px 16px; border-radius: 7px;
  font-size: 0.8rem; font-weight: 700; cursor: pointer; border: 1px solid;
  transition: all .15s;
}
.af-btn-ghost {
  background: transparent;
  border-color: var(--color-divider, rgba(255,255,255,.1));
  color: var(--color-text-secondary, #aaa);
}
.af-btn-ghost:hover { border-color: #ef4444; color: #ef4444; }
.af-btn-primary {
  background: var(--color-accent, #3a86ff);
  border-color: var(--color-accent, #3a86ff);
  color: #fff;
}
.af-btn-primary:hover {
  background: #2563eb; border-color: #2563eb;
  box-shadow: 0 4px 16px rgba(58,134,255,.35);
  transform: translateY(-1px);
}

/* ══ TRANSITION ═════════════════════════════════════════════════════════════ */
.af-fade-enter-active, .af-fade-leave-active { transition: opacity .2s, transform .2s; }
.af-fade-enter-from, .af-fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
