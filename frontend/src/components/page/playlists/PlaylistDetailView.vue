<template>
  <div class="playlist-detail-page">
    <!-- Загрузка -->
    <div v-if="loading" class="detail-loading">
      <div class="loading-cover-skeleton"></div>
      <div class="loading-info-skeleton">
        <div class="sk-line w-60"></div>
        <div class="sk-line w-40"></div>
        <div class="sk-line w-80"></div>
        <div class="sk-actions">
          <div class="sk-btn"></div><div class="sk-btn"></div><div class="sk-btn"></div>
        </div>
      </div>
    </div>

    <!-- Не найден -->
    <div v-else-if="!playlist" class="not-found">
      <div class="not-found-icon">🎵</div>
      <h2>Плейлист не найден</h2>
      <p>Возможно, он был удалён или у вас нет доступа</p>
      <router-link to="/playlists" class="btn-back-link">← Все плейлисты</router-link>
    </div>

    <!-- Контент -->
    <template v-else>
      <div class="breadcrumb">
        <router-link to="/playlists" class="breadcrumb-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Все плейлисты
        </router-link>
      </div>

      <!-- Шапка -->
      <div class="playlist-hero">
        <div class="hero-cover">
          <div :class="['cover-mosaic', `items-${coverItems.length}`]">
            <div v-for="(item, idx) in coverItems" :key="idx" class="mosaic-cell">
              <img
                v-if="item?.anime_poster"
                :src="getMediaUrl(item.anime_poster)"
                :alt="item.anime_title"
                @error="(e: Event) => ((e.target as HTMLImageElement).style.display='none')"
              />
              <div v-else class="mosaic-placeholder">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="2" y="2" width="20" height="20" rx="2"/><path d="M8 12l3 3 5-5"/>
                </svg>
              </div>
            </div>
            <div v-if="playlist.items_count > 3" class="mosaic-extra">+{{ playlist.items_count - 3 }}</div>
          </div>
          <div class="privacy-hero-badge" :class="`privacy-${currentVisibility}`">
            <span>{{ privacyIcon }}</span> {{ privacyLabel }}
          </div>
        </div>

        <div class="hero-info">
          <h1 class="hero-title">{{ playlist.title }}</h1>
          <div class="hero-meta">
            <div class="author-chip" @click="goToAuthor">
              <img v-if="playlist.user?.avatar" :src="getMediaUrl(playlist.user.avatar)" class="author-chip-avatar" />
              <div v-else class="author-chip-avatar-ph">{{ (playlist.user_username || '?')[0]?.toUpperCase() ?? '?' }}</div>
              <span>{{ playlist.user_username }}</span>
            </div>
            <span class="meta-dot">·</span>
            <span class="meta-item">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
              {{ playlist.items_count }} аниме
            </span>
            <span class="meta-dot">·</span>
            <span class="meta-item">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              {{ formatDate(playlist.created_at) }}
            </span>
          </div>

          <div class="hero-actions">
            <button @click="toggleFavorite" :class="['action-hero-btn', { active: playlist.is_favorited }]">
              <svg width="16" height="16" viewBox="0 0 24 24" :fill="playlist.is_favorited ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              {{ playlist.is_favorited ? 'В избранном' : 'В избранное' }}
            </button>

            <button @click="sharePlaylist" class="action-hero-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
              </svg>
              Поделиться
            </button>

            <button @click="copyAllLinks" class="action-hero-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              Ссылки
            </button>

            <template v-if="isOwner">
              <button @click="showAddAnimeModal = true" class="action-hero-btn primary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Добавить
              </button>
              <button @click="openEditModal" class="action-hero-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                Изменить
              </button>
              <button @click="showExportModal = true" class="action-hero-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Экспорт
              </button>
              <button @click="showDeleteConfirm = true" class="action-hero-btn danger">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
                Удалить
              </button>
            </template>
          </div>

          <div class="hero-stats">
            <span class="stat-chip">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              {{ playlist.favorites_count }} в избранном
            </span>
          </div>
        </div>
      </div>

      <!-- Описание -->
      <div v-if="playlist.description" class="description-section">
        <div class="section-label">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
          </svg>
          Описание
        </div>
        <p class="description-text">{{ playlist.description }}</p>
      </div>

      <!-- Список аниме -->
      <div class="anime-section">
        <div class="section-header">
          <div class="section-label">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
            Аниме в плейлисте ({{ playlist.items_count }})
          </div>
          <div v-if="isOwner && sortedItems.length > 1" class="drag-hint">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
              <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
            </svg>
            Перетащите для сортировки
          </div>
        </div>

        <div v-if="!playlist.items || playlist.items.length === 0" class="anime-empty">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
          </svg>
          <p>Плейлист пока пуст</p>
          <button v-if="isOwner" @click="showAddAnimeModal = true" class="btn-add-empty">Добавить аниме</button>
        </div>

        <!-- Список с pointer-based drag&drop -->
        <div class="anime-list" ref="listRef">
          <div
            v-for="(item, index) in sortedItems"
            :key="item.id"
            :data-index="index"
            :class="[
              'anime-row',
              { 'is-dragging': dragState.activeIndex === index },
              { 'drag-above': dragState.overIndex === index && dragState.overEdge === 'above' && dragState.activeIndex !== index },
              { 'drag-below': dragState.overIndex === index && dragState.overEdge === 'below' && dragState.activeIndex !== index },
            ]"
            :style="dragState.activeIndex === index ? dragItemStyle : {}"
          >
            <!-- Drag handle -->
            <div
              class="row-index-wrap"
              :class="{ 'is-handle': isOwner }"
              @mousedown.prevent="isOwner ? startDrag($event, index) : null"
            >
              <span v-if="!isOwner" class="row-index">{{ index + 1 }}</span>
              <div v-else class="drag-handle">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <circle cx="9" cy="5" r="1.2" fill="currentColor"/><circle cx="9" cy="12" r="1.2" fill="currentColor"/><circle cx="9" cy="19" r="1.2" fill="currentColor"/>
                  <circle cx="15" cy="5" r="1.2" fill="currentColor"/><circle cx="15" cy="12" r="1.2" fill="currentColor"/><circle cx="15" cy="19" r="1.2" fill="currentColor"/>
                </svg>
              </div>
            </div>

            <!-- Постер -->
            <router-link :to="`/anime/${item.anime}`" class="row-poster-link">
              <div class="row-poster">
                <img
                  v-if="item.anime_poster"
                  :src="getMediaUrl(item.anime_poster)"
                  :alt="item.anime_title"
                  @error="(e: Event) => ((e.target as HTMLImageElement).style.display='none')"
                />
                <div v-else class="row-poster-ph">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="2" y="2" width="20" height="20" rx="2"/>
                  </svg>
                </div>
              </div>
            </router-link>

            <!-- Инфо -->
            <div class="row-info">
              <router-link :to="`/anime/${item.anime}`" class="row-title">
                {{ item.anime_title }}
              </router-link>
              <div v-if="item.notes" class="row-note">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                </svg>
                {{ item.notes }}
              </div>
              <div class="row-meta">
                <span v-if="item.anime_year" class="row-meta-chip">{{ item.anime_year }}</span>
                <span v-if="item.anime_score" class="row-meta-chip score">⭐ {{ item.anime_score.toFixed(1) }}</span>
              </div>
            </div>

            <!-- Действия -->
            <div class="row-actions">
              <router-link :to="`/anime/${item.anime}/watch`" class="row-action-btn play" title="Смотреть">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
              </router-link>

              <button
                @click="copyAnimeLink(item)"
                class="row-action-btn"
                :title="item.source_url ? 'Копировать ссылку' : 'Копировать ссылку на аниме'"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
              </button>

              <template v-if="isOwner">
                <button @click="openEditItem(item)" class="row-action-btn" title="Редактировать заметку">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button @click="openRemoveItem(item)" class="row-action-btn danger" title="Удалить">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ======== МОДАЛКА: Добавить аниме ======== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="showAddAnimeModal" class="modal-overlay" @click.self="showAddAnimeModal = false">
          <div class="modal-box">
            <div class="modal-header">
              <h3>Добавить аниме</h3>
              <button @click="showAddAnimeModal = false" class="modal-close-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="modal-search-wrap">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="modal-search-icon">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <input
                  v-model="addAnimeSearch"
                  @input="debouncedAnimeSearch"
                  type="text"
                  placeholder="Название аниме..."
                  class="modal-search-input"
                  autofocus
                />
                <button v-if="addAnimeSearch" @click="addAnimeSearch = ''; animeSearchResults = []" class="modal-search-clear">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              </div>
              <div v-if="animeSearchLoading" class="modal-loading">
                <div class="spinner-sm"></div> Поиск...
              </div>
              <div v-else-if="animeSearchResults.length > 0" class="modal-results">
                <div
                  v-for="anime in animeSearchResults"
                  :key="anime.id"
                  @click="addAnimeToPlaylist(anime)"
                  :class="['modal-result-item', { disabled: isAnimeInPlaylist(anime.id) }]"
                >
                  <img
                    v-if="anime.poster_url"
                    :src="getMediaUrl(anime.poster_url)"
                    :alt="anime.title_ru"
                    class="modal-result-poster"
                    @error="(e: Event) => ((e.target as HTMLImageElement).style.display='none')"
                  />
                  <div v-else class="modal-result-poster-ph"></div>
                  <div class="modal-result-info">
                    <span class="modal-result-title">{{ anime.title_ru || anime.title_en }}</span>
                    <span class="modal-result-meta">
                      {{ anime.year }}{{ anime.episodes ? ` · ${anime.episodes} эп.` : '' }}
                      {{ anime.score ? ` · ⭐ ${Number(anime.score).toFixed(1)}` : '' }}
                    </span>
                  </div>
                  <span v-if="isAnimeInPlaylist(anime.id)" class="already-added">✓ Добавлено</span>
                  <button v-else class="btn-add-anime" type="button">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div v-else-if="addAnimeSearch.length >= 2 && !animeSearchLoading" class="modal-empty">
                Ничего не найдено по запросу «{{ addAnimeSearch }}»
              </div>
              <div v-else-if="!addAnimeSearch" class="modal-empty-hint">
                Начните вводить название аниме для поиска
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ======== МОДАЛКА: Редактировать плейлист ======== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="showEditModal && playlist" class="modal-overlay" @click.self="showEditModal = false">
          <div class="modal-box">
            <div class="modal-header">
              <h3>Редактировать плейлист</h3>
              <button @click="showEditModal = false" class="modal-close-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Название <span class="req">*</span></label>
                <input v-model="editForm.title" type="text" class="form-input" maxlength="100" />
              </div>
              <div class="form-group">
                <label class="form-label">Описание</label>
                <textarea v-model="editForm.description" class="form-textarea" rows="3" maxlength="500"></textarea>
              </div>
              <div class="form-group">
                <label class="form-label">Видимость</label>
                <div class="privacy-chips">
                  <label
                    v-for="opt in visibilityOptions"
                    :key="opt.value"
                    :class="['privacy-chip', { active: editForm.visibility === opt.value }]"
                  >
                    <input type="radio" :value="opt.value" v-model="editForm.visibility" style="display:none" />
                    <span>{{ opt.icon }}</span> {{ opt.label }}
                  </label>
                </div>
                <p v-if="editForm.visibility === 'link'" class="visibility-hint">
                  🔗 После сохранения будет сгенерирована уникальная ссылка
                </p>
              </div>
            </div>
            <div class="modal-footer">
              <button @click="showEditModal = false" class="btn-modal-cancel">Отмена</button>
              <button @click="saveEdit" :disabled="!editForm.title.trim() || editSaving" class="btn-modal-save">
                <div v-if="editSaving" class="spinner-sm"></div>
                {{ editSaving ? 'Сохранение...' : 'Сохранить' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ======== МОДАЛКА: Редактировать заметку ======== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="editingItem" class="modal-overlay" @click.self="editingItem = null">
          <div class="modal-box modal-box-sm">
            <div class="modal-header">
              <h3>Заметка к аниме</h3>
              <button @click="editingItem = null" class="modal-close-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="anime-edit-preview">
                <img v-if="editingItem.anime_poster" :src="getMediaUrl(editingItem.anime_poster)" class="edit-preview-poster" />
                <span class="edit-preview-title">{{ editingItem.anime_title }}</span>
              </div>
              <div class="form-group">
                <label class="form-label">Заметка</label>
                <textarea v-model="editItemNotes" class="form-textarea" rows="3" maxlength="300" placeholder="Добавьте заметку..."></textarea>
              </div>
            </div>
            <div class="modal-footer">
              <button @click="editingItem = null" class="btn-modal-cancel">Отмена</button>
              <button @click="saveItemNotes" :disabled="itemSaving" class="btn-modal-save">
                {{ itemSaving ? 'Сохранение...' : 'Сохранить' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ======== МОДАЛКА: Удалить аниме из плейлиста ======== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="removingItem" class="modal-overlay" @click.self="removingItem = null">
          <div class="modal-box modal-box-sm">
            <div class="modal-header">
              <h3>Удалить аниме?</h3>
              <button @click="removingItem = null" class="modal-close-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="modal-body confirm-body">
              <div class="confirm-anime-row">
                <img v-if="removingItem.anime_poster" :src="getMediaUrl(removingItem.anime_poster)" class="confirm-poster" />
                <div v-else class="confirm-poster-ph"></div>
                <span class="confirm-anime-title">{{ removingItem.anime_title }}</span>
              </div>
              <p class="confirm-text">Вы уверены, что хотите удалить это аниме из плейлиста?</p>
            </div>
            <div class="modal-footer">
              <button @click="removingItem = null" class="btn-modal-cancel">Отмена</button>
              <button @click="confirmRemoveItem" class="btn-modal-danger">Удалить</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ======== МОДАЛКА: Удалить плейлист ======== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
          <div class="modal-box modal-box-sm">
            <div class="modal-header">
              <h3>Удалить плейлист?</h3>
              <button @click="showDeleteConfirm = false" class="modal-close-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="modal-body confirm-body">
              <div class="confirm-icon">🗑️</div>
              <p class="confirm-text">
                Вы хотите удалить плейлист<br/>
                <strong>«{{ playlist?.title }}»</strong>?<br/>
                Это действие необратимо.
              </p>
            </div>
            <div class="modal-footer">
              <button @click="showDeleteConfirm = false" class="btn-modal-cancel">Отмена</button>
              <button @click="confirmDeletePlaylist" :disabled="isDeleting" class="btn-modal-danger">
                <div v-if="isDeleting" class="spinner-sm-dark"></div>
                {{ isDeleting ? 'Удаление...' : 'Удалить навсегда' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ======== МОДАЛКА: Экспорт ======== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="showExportModal" class="modal-overlay" @click.self="showExportModal = false">
          <div class="modal-box">
            <div class="modal-header">
              <h3>Экспорт плейлиста</h3>
              <button @click="showExportModal = false" class="modal-close-btn">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <!-- Формат -->
              <div class="form-group">
                <label class="form-label">Формат</label>
                <div class="export-formats">
                  <label v-for="fmt in exportFormats" :key="fmt.value" :class="['export-fmt', { active: exportFormat === fmt.value }]">
                    <input type="radio" :value="fmt.value" v-model="exportFormat" style="display:none" />
                    <span class="fmt-icon">{{ fmt.icon }}</span>
                    <div>
                      <div class="fmt-label">{{ fmt.label }}</div>
                      <div class="fmt-desc">{{ fmt.desc }}</div>
                    </div>
                  </label>
                </div>
              </div>
              <!-- Превью -->
              <div class="form-group">
                <label class="form-label">Предпросмотр</label>
                <div class="export-preview">
                  <pre class="export-text">{{ exportPreview }}</pre>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button @click="showExportModal = false" class="btn-modal-cancel">Закрыть</button>
              <button @click="copyExport" class="btn-modal-save outline">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                Скопировать
              </button>
              <button @click="downloadExport" class="btn-modal-save">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Скачать
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <transition name="toast">
        <div v-if="toastMsg" class="toast-notification">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {{ toastMsg }}
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import playlistsApi, { type Playlist, type PlaylistItem, type PlaylistVisibility } from '@/api/playlists'
import apiClient, { getMediaUrl } from '@/api/client'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const playlist = ref<Playlist | null>(null)
const loading = ref(true)
const currentUserId = ref<number | undefined>(undefined)
const listRef = ref<HTMLElement | null>(null)

// Модалки
const showAddAnimeModal = ref(false)
const showEditModal = ref(false)
const showExportModal = ref(false)
const showDeleteConfirm = ref(false)
const editingItem = ref<PlaylistItem | null>(null)
const removingItem = ref<PlaylistItem | null>(null)
const isDeleting = ref(false)

// ─── Pointer-based Drag & Drop ───
interface DragState {
  active: boolean
  activeIndex: number | null
  overIndex: number | null
  overEdge: 'above' | 'below' | null
  startY: number
  currentY: number
  itemHeight: number
  offsetY: number
  draggedElement: HTMLElement | null
}
const dragState = reactive<DragState>({
  active: false,
  activeIndex: null,
  overIndex: null,
  overEdge: null,
  startY: 0,
  currentY: 0,
  itemHeight: 0,
  offsetY: 0,
  draggedElement: null,
})

const dragItemStyle = computed(() => {
  if (!dragState.active || dragState.activeIndex === null) return {}
  const dy = dragState.currentY - dragState.startY
  return {
    transform: `translateY(${dy}px)`,
    zIndex: '1000',
    boxShadow: '0 12px 32px rgba(0,0,0,0.45)',
    opacity: '0.92',
    transition: 'none',
    position: 'relative' as const,
    willChange: 'transform',
  }
})

const startDrag = (e: MouseEvent, index: number) => {
  if (!listRef.value) return
  const row = listRef.value.querySelector(`[data-index="${index}"]`) as HTMLElement
  if (!row) return

  // Получаем реальную позицию элемента в отсортированном списке
  const sortedIdx = sortedItems.value.findIndex((_, i) => i === index)
  const actualRow = listRef.value.querySelector(`[data-index="${sortedIdx}"]`) as HTMLElement
  if (!actualRow) return

  const rect = actualRow.getBoundingClientRect()
  dragState.active = true
  dragState.activeIndex = sortedIdx
  dragState.overIndex = sortedIdx
  dragState.overEdge = null
  dragState.startY = e.clientY
  dragState.currentY = e.clientY
  dragState.itemHeight = rect.height
  dragState.offsetY = e.clientY - rect.top
  dragState.draggedElement = actualRow

  // Добавляем класс для визуального эффекта
  actualRow.classList.add('is-being-dragged')

  document.addEventListener('mousemove', onDragMove, { passive: true })
  document.addEventListener('mouseup', onDragEnd)
  document.body.style.userSelect = 'none'
  document.body.style.cursor = 'grabbing'
  document.body.style.overflow = 'hidden'
}

const onDragMove = (e: MouseEvent) => {
  if (!dragState.active || dragState.activeIndex === null || !listRef.value) return
  dragState.currentY = e.clientY

  // Находим элемент под курсором более надёжно
  const rows = Array.from(listRef.value.querySelectorAll('.anime-row')) as HTMLElement[]
  let closestIndex: number | null = null
  let closestEdge: 'above' | 'below' = 'above'

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i]
    if (!row || row.classList.contains('is-being-dragged')) continue
    
    const rect = row.getBoundingClientRect()
    const midY = rect.top + rect.height * 0.5
    
    // Проверяем, находится ли курсор в зоне элемента
    if (e.clientY >= rect.top - 10 && e.clientY <= rect.bottom + 10) {
      closestIndex = i
      closestEdge = e.clientY < midY ? 'above' : 'below'
      break
    }
  }

  // Если не найден элемент напрямую, ищем ближайший
  if (closestIndex === null && rows.length > 0) {
    let minDistance = Infinity
    rows.forEach((row, i) => {
      if (!row || row.classList.contains('is-being-dragged')) return
      const rect = row.getBoundingClientRect()
      const distance = Math.min(
        Math.abs(e.clientY - rect.top),
        Math.abs(e.clientY - rect.bottom)
      )
      if (distance < minDistance) {
        minDistance = distance
        closestIndex = i
        const midY = rect.top + rect.height * 0.5
        closestEdge = e.clientY < midY ? 'above' : 'below'
      }
    })
  }

  dragState.overIndex = closestIndex
  dragState.overEdge = closestIndex !== null ? closestEdge : null
}

const onDragEnd = async () => {
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
  document.body.style.overflow = ''

  // Убираем класс с перетаскиваемого элемента
  if (dragState.draggedElement) {
    dragState.draggedElement.classList.remove('is-being-dragged')
    dragState.draggedElement = null
  }

  const from = dragState.activeIndex
  const to = dragState.overIndex
  const edge = dragState.overEdge

  dragState.active = false
  dragState.activeIndex = null
  dragState.overIndex = null
  dragState.overEdge = null

  if (from === null || to === null || from === to || !playlist.value) return

  // Вычисляем целевую позицию с учётом направления
  let insertAt = to
  if (edge === 'below') insertAt = to + 1
  // Корректировка при перетаскивании вниз
  if (from < to && edge === 'below') insertAt = to
  // Корректировка при перетаскивании вверх  
  if (from > to && edge === 'above') insertAt = to

  if (insertAt === from) return

  // Оптимистичное обновление
  const items = [...sortedItems.value]
  const [moved] = items.splice(from, 1)
  if (moved) items.splice(insertAt, 0, moved)
  items.forEach((item, idx) => { item.position = idx + 1 })
  playlist.value.items = items

  // Сохраняем на сервере
  try {
    await playlistsApi.reorderPlaylistItems(
      playlist.value.id,
      items.map((item, idx) => ({ id: item.id, position: idx + 1 }))
    )
  } catch {
    // Откатываем при ошибке
    await loadPlaylist()
  }
}

// Добавление аниме
const addAnimeSearch = ref('')
const animeSearchResults = ref<any[]>([])
const animeSearchLoading = ref(false)
let searchTimer: ReturnType<typeof setTimeout> | null = null

// Редактирование
const editForm = ref({ title: '', description: '', visibility: 'public' as PlaylistVisibility })
const editSaving = ref(false)
const editItemNotes = ref('')
const itemSaving = ref(false)

// Экспорт
const exportFormat = ref<'text' | 'text_links' | 'json' | 'csv' | 'markdown'>('text')
const exportFormats = [
  { value: 'text', label: 'Текст', icon: '📝', desc: 'Простой список' },
  { value: 'text_links', label: 'Со ссылками', icon: '🔗', desc: 'Список со ссылками' },
  { value: 'markdown', label: 'Markdown', icon: '✍️', desc: 'Формат .md' },
  { value: 'json', label: 'JSON', icon: '{ }', desc: 'Структурированный JSON' },
  { value: 'csv', label: 'CSV', icon: '📊', desc: 'Таблица для Excel' },
]

const visibilityOptions = [
  { value: 'public', label: 'Публичный', icon: '🌍' },
  { value: 'private', label: 'Приватный', icon: '🔒' },
  { value: 'link', label: 'По ссылке', icon: '🔗' },
]

const toastMsg = ref('')

// ─── Computed ───
const isOwner = computed(() => {
  if (!playlist.value || !currentUserId.value) return false
  return playlist.value.user_id === currentUserId.value
})

const sortedItems = computed(() => {
  if (!playlist.value?.items) return []
  return [...playlist.value.items].sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
})

const coverItems = computed(() => {
  // Показываем только реальные элементы (1-3), без пустых плейсхолдеров
  return sortedItems.value.slice(0, 3)
})

const currentVisibility = computed((): PlaylistVisibility => {
  if (!playlist.value) return 'public'
  return playlist.value.visibility || (playlist.value.is_public ? 'public' : 'private')
})

const privacyIcon = computed(() => {
  if (currentVisibility.value === 'private') return '🔒'
  if (currentVisibility.value === 'link') return '🔗'
  return '🌍'
})

const privacyLabel = computed(() => {
  if (currentVisibility.value === 'private') return 'Приватный'
  if (currentVisibility.value === 'link') return 'По ссылке'
  return 'Публичный'
})

const exportPreview = computed(() => {
  if (!playlist.value) return ''
  const items = sortedItems.value
  const title = playlist.value.title
  const author = playlist.value.user_username

  if (exportFormat.value === 'text') {
    return `Плейлист: ${title}\nАвтор: @${author}\nАниме: ${items.length}\n\n` +
      items.map((item, i) => `${i + 1}. ${item.anime_title}${item.notes ? `\n   └ ${item.notes}` : ''}`).join('\n')
  }
  if (exportFormat.value === 'text_links') {
    return `Плейлист: ${title}\nАвтор: @${author}\n\n` +
      items.map((item, i) => {
        const animeUrl = `${window.location.origin}/anime/${item.anime}`
        let str = `${i + 1}. ${item.anime_title}\n   └ ${animeUrl}`
        if (item.source_url) str += `\n   └ Источник: ${item.source_url}`
        if (item.notes) str += `\n   └ Заметка: ${item.notes}`
        return str
      }).join('\n\n')
  }
  if (exportFormat.value === 'markdown') {
    return `# ${title}\n> Автор: @${author} · ${items.length} аниме\n\n` +
      items.map((item, i) => {
        const animeUrl = `${window.location.origin}/anime/${item.anime}`
        let str = `${i + 1}. [${item.anime_title}](${animeUrl})`
        if (item.anime_year || item.anime_score) str += ` *(${[item.anime_year, item.anime_score ? `⭐${item.anime_score.toFixed(1)}` : ''].filter(Boolean).join(', ')})*`
        if (item.notes) str += `\n   > ${item.notes}`
        return str
      }).join('\n')
  }
  if (exportFormat.value === 'json') {
    return JSON.stringify({
      title,
      author,
      url: window.location.href,
      exported_at: new Date().toISOString(),
      items: items.map((item, i) => ({
        position: i + 1,
        title: item.anime_title,
        year: item.anime_year || null,
        score: item.anime_score || null,
        url: `${window.location.origin}/anime/${item.anime}`,
        source_url: item.source_url || null,
        notes: item.notes || null,
      }))
    }, null, 2)
  }
  if (exportFormat.value === 'csv') {
    const header = '№,Название,Год,Рейтинг,Ссылка на аниме,Источник,Заметка'
    const rows = items.map((item, i) =>
      [
        i + 1,
        `"${item.anime_title.replace(/"/g, '""')}"`,
        item.anime_year || '',
        item.anime_score ? item.anime_score.toFixed(1) : '',
        `"${window.location.origin}/anime/${item.anime}"`,
        `"${(item.source_url || '').replace(/"/g, '""')}"`,
        `"${(item.notes || '').replace(/"/g, '""')}"`,
      ].join(',')
    )
    return [header, ...rows].join('\n')
  }
  return ''
})

// ─── Методы ───
const loadPlaylist = async () => {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const response = await playlistsApi.getPlaylist(parseInt(id as string))
    playlist.value = response.data
  } catch {
    playlist.value = null
  } finally {
    loading.value = false
  }
}

const openEditModal = () => {
  if (!playlist.value) return
  editForm.value = {
    title: playlist.value.title,
    description: playlist.value.description || '',
    visibility: currentVisibility.value,
  }
  showEditModal.value = true
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}

const goToAuthor = () => {
  if (playlist.value?.user_id) router.push(`/profile/${playlist.value.user_id}`)
}

const toggleFavorite = async () => {
  if (!playlist.value) return
  try {
    if (playlist.value.is_favorited) {
      await playlistsApi.removePlaylistFromFavorites(playlist.value.id)
      playlist.value.is_favorited = false
      playlist.value.favorites_count = Math.max(0, playlist.value.favorites_count - 1)
      showToast('Убрано из избранного')
    } else {
      await playlistsApi.addPlaylistToFavorites(playlist.value.id)
      playlist.value.is_favorited = true
      playlist.value.favorites_count++
      showToast('Добавлено в избранное ⭐')
    }
  } catch {}
}

const sharePlaylist = async () => {
  try {
    if (currentVisibility.value === 'link') {
      // Генерируем/получаем share-ссылку
      const res = await playlistsApi.generateShareLink(playlist.value!.id)
      const url = `${window.location.origin}/playlist/shared/${res.data.token}`
      await navigator.clipboard.writeText(url)
      showToast('Ссылка по токену скопирована!')
    } else {
      await navigator.clipboard.writeText(window.location.href)
      showToast('Ссылка скопирована!')
    }
  } catch {
    navigator.clipboard.writeText(window.location.href)
    showToast('Ссылка скопирована!')
  }
}

const copyAllLinks = async () => {
  if (!playlist.value?.items) return
  const lines = sortedItems.value.map((item, i) => {
    const animeUrl = `${window.location.origin}/anime/${item.anime}`
    return `${i + 1}. ${item.anime_title} — ${animeUrl}${item.source_url ? `\n   Источник: ${item.source_url}` : ''}`
  })
  const text = lines.join('\n')
  try {
    await navigator.clipboard.writeText(text)
    showToast(`Скопированы ссылки на ${lines.length} аниме`)
  } catch {
    fallbackCopyText(text)
    showToast(`Скопированы ссылки на ${lines.length} аниме`)
  }
}

const copyAnimeLink = async (item: PlaylistItem) => {
  const url = (item.source_url && item.source_url.trim()) 
    ? item.source_url.trim() 
    : `${window.location.origin}/anime/${item.anime}`
  try {
    await navigator.clipboard.writeText(url)
    showToast('Ссылка скопирована!')
  } catch {
    // Fallback для старых браузеров
    fallbackCopyText(url)
    showToast('Ссылка скопирована!')
  }
}

// Fallback для старых браузеров
const fallbackCopyText = (text: string) => {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    document.execCommand('copy')
  } catch (e) {
    console.error('Copy failed:', e)
  }
  document.body.removeChild(textarea)
}

const copyExport = async () => {
  await navigator.clipboard.writeText(exportPreview.value)
  showToast('Скопировано в буфер обмена!')
}

const downloadExport = () => {
  const ext: Record<string, string> = {
    text: 'txt', text_links: 'txt', markdown: 'md', json: 'json', csv: 'csv'
  }
  const mime: Record<string, string> = {
    text: 'text/plain', text_links: 'text/plain', markdown: 'text/markdown',
    json: 'application/json', csv: 'text/csv'
  }
  const safeName = (playlist.value?.title || 'playlist').replace(/[^a-zA-Zа-яА-Я0-9]/g, '_').slice(0, 50)
  const filename = `${safeName}.${ext[exportFormat.value]}`
  const blob = new Blob([exportPreview.value], { type: mime[exportFormat.value] + ';charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
  showToast(`Файл ${filename} скачан`)
}

// Поиск аниме
const debouncedAnimeSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  if (addAnimeSearch.value.length < 2) { animeSearchResults.value = []; return }
  searchTimer = setTimeout(async () => {
    animeSearchLoading.value = true
    try {
      // Используем правильный endpoint для поиска
      const res = await apiClient.get('/anime/', { params: { search: addAnimeSearch.value, page_size: 12 } })
      animeSearchResults.value = res.data.results || res.data || []
    } catch (e) {
      console.error('Search error:', e)
      animeSearchResults.value = []
    } finally {
      animeSearchLoading.value = false
    }
  }, 300)
}

const isAnimeInPlaylist = (animeId: number) => {
  if (!playlist.value?.items) return false
  return playlist.value.items.some(i => i.anime === animeId || i.anime_id === animeId)
}

const addAnimeToPlaylist = async (anime: any) => {
  if (!playlist.value || isAnimeInPlaylist(anime.id)) return
  try {
    await playlistsApi.addItemToPlaylist(playlist.value.id, { anime: anime.id })
    await loadPlaylist()
    showToast(`«${anime.title_ru || anime.title_en}» добавлено!`)
  } catch (err: any) {
    showToast(err.response?.data?.error || 'Ошибка добавления')
  }
}

const openRemoveItem = (item: PlaylistItem) => {
  removingItem.value = item
}

const confirmRemoveItem = async () => {
  if (!playlist.value || !removingItem.value) return
  try {
    await playlistsApi.removeFromPlaylist(playlist.value.id, removingItem.value.id)
    await loadPlaylist()
    showToast('Аниме удалено из плейлиста')
    removingItem.value = null
  } catch {}
}

const openEditItem = (item: PlaylistItem) => {
  editingItem.value = item
  editItemNotes.value = item.notes || ''
}

const saveItemNotes = async () => {
  if (!playlist.value || !editingItem.value) return
  itemSaving.value = true
  try {
    await playlistsApi.updatePlaylistItemNotes(playlist.value.id, editingItem.value.id, editItemNotes.value)
    editingItem.value.notes = editItemNotes.value
    editingItem.value = null
    showToast('Заметка сохранена')
  } catch {} finally {
    itemSaving.value = false
  }
}

const saveEdit = async () => {
  if (!playlist.value || !editForm.value.title.trim()) return
  editSaving.value = true
  try {
    const res = await playlistsApi.updatePlaylist(playlist.value.id, {
      title: editForm.value.title.trim(),
      description: editForm.value.description,
      visibility: editForm.value.visibility,
    } as any)
    Object.assign(playlist.value, res.data)
    showEditModal.value = false
    showToast('Плейлист обновлён!')
  } catch {} finally {
    editSaving.value = false
  }
}

const confirmDeletePlaylist = async () => {
  if (!playlist.value) return
  isDeleting.value = true
  try {
    await playlistsApi.deletePlaylist(playlist.value.id)
    router.push('/playlists')
  } catch {} finally {
    isDeleting.value = false
  }
}

const showToast = (msg: string) => {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = '' }, 3000)
}

onMounted(async () => {
  if (authStore.user) currentUserId.value = authStore.user.id
  await loadPlaylist()
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
})
</script>

<style scoped>
.playlist-detail-page {
  padding: 1.5rem;
  max-width: 960px;
  margin: 0 auto;
  min-height: 100vh;
}

/* ── Загрузка ── */
.detail-loading { display: flex; gap: 2rem; padding: 2rem 0; }
.loading-cover-skeleton {
  width: 260px; flex-shrink: 0; aspect-ratio: 1;
  background: var(--color-background-active); border-radius: var(--radius-lg); animation: shimmer 1.5s infinite;
}
.loading-info-skeleton { flex: 1; display: flex; flex-direction: column; gap: 1rem; padding-top: 0.5rem; }
.sk-line { height: 13px; background: var(--color-background-active); border-radius: 6px; animation: shimmer 1.5s infinite; }
.w-60 { width: 60%; } .w-40 { width: 40%; } .w-80 { width: 80%; }
.sk-actions { display: flex; gap: 0.75rem; margin-top: 0.5rem; }
.sk-btn { width: 110px; height: 38px; background: var(--color-background-active); border-radius: 0.5rem; animation: shimmer 1.5s infinite; }
@keyframes shimmer { 0%,100% { opacity: 1; } 50% { opacity: 0.45; } }

/* ── Не найден ── */
.not-found { text-align: center; padding: 6rem 2rem; }
.not-found-icon { font-size: 4rem; margin-bottom: 1rem; }
.not-found h2 { font-size: 1.5rem; font-weight: 700; color: var(--color-text); margin: 0 0 0.5rem; }
.not-found p { color: var(--color-text-secondary); margin: 0 0 1.5rem; }
.btn-back-link { display: inline-flex; align-items: center; gap: 0.375rem; color: var(--color-accent); text-decoration: none; font-weight: 600; }

/* ── Breadcrumb ── */
.breadcrumb { margin-bottom: 1.25rem; }
.breadcrumb-link { display: inline-flex; align-items: center; gap: 0.25rem; color: var(--color-text-secondary); font-size: 0.875rem; text-decoration: none; transition: color 0.2s; }
.breadcrumb-link:hover { color: var(--color-accent); }

/* ── Hero ── */
.playlist-hero { display: flex; gap: 2rem; margin-bottom: 1.75rem; align-items: flex-start; }
.hero-cover { width: 240px; flex-shrink: 0; position: relative; }
.cover-mosaic {
  width: 100%; aspect-ratio: 1;
  display: grid;
  gap: 3px; border-radius: var(--radius-lg); overflow: hidden;
  background: var(--color-background-active);
}
/* 1 элемент - на всю ширину */
.cover-mosaic.items-1 {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
}
/* 2 элемента - горизонтально */
.cover-mosaic.items-2 {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr;
}
/* 3 элемента - первый большой, два маленьких справа */
.cover-mosaic.items-3 {
  grid-template-columns: 2fr 1fr;
  grid-template-rows: 1fr 1fr;
}
.cover-mosaic.items-3 .mosaic-cell:first-child {
  grid-row: span 2;
}
.mosaic-cell { position: relative; background: var(--color-background-active); overflow: hidden; }
.mosaic-cell img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }
.playlist-hero:hover .mosaic-cell img { transform: scale(1.05); }
.mosaic-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: var(--color-text-tertiary); }
.mosaic-extra { position: absolute; bottom: 8px; right: 8px; background: rgba(0,0,0,0.75); color: #fff; font-size: 0.72rem; font-weight: 700; padding: 2px 7px; border-radius: 999px; backdrop-filter: blur(4px); }
.privacy-hero-badge { position: absolute; top: 8px; left: 8px; display: inline-flex; align-items: center; gap: 0.25rem; padding: 3px 9px; border-radius: 999px; font-size: 0.7rem; font-weight: 700; backdrop-filter: blur(6px); }
.privacy-public { background: rgba(34,197,94,0.85); color: #fff; }
.privacy-private { background: rgba(239,68,68,0.85); color: #fff; }
.privacy-link { background: rgba(58,134,255,0.85); color: #fff; }

.hero-info { flex: 1; }
.hero-title { font-size: 1.6rem; font-weight: 800; color: var(--color-text); margin: 0 0 0.75rem; line-height: 1.3; }
.hero-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1.1rem; font-size: 0.85rem; color: var(--color-text-secondary); }
.author-chip { display: inline-flex; align-items: center; gap: 0.35rem; cursor: pointer; transition: color 0.2s; }
.author-chip:hover { color: var(--color-accent); }
.author-chip-avatar { width: 20px; height: 20px; border-radius: 50%; object-fit: cover; }
.author-chip-avatar-ph { width: 20px; height: 20px; border-radius: 50%; background: var(--color-accent); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.58rem; font-weight: 700; }
.meta-dot { color: var(--color-divider-light); }
.meta-item { display: inline-flex; align-items: center; gap: 0.25rem; }

.hero-actions { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.875rem; }
.action-hero-btn {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.55rem 0.9rem;
  background: var(--color-background-active); border: 1px solid var(--color-divider-light);
  border-radius: var(--radius-lg); font-size: 0.8rem; font-weight: 600;
  color: var(--color-text); cursor: pointer; transition: all 0.18s; white-space: nowrap;
}
.action-hero-btn:hover { background: var(--color-background-surface); border-color: var(--color-accent); color: var(--color-accent); }
.action-hero-btn.active { background: rgba(251,191,36,0.15); border-color: #f59e0b; color: #f59e0b; }
.action-hero-btn.primary { background: var(--color-accent); border-color: var(--color-accent); color: #fff; }
.action-hero-btn.primary:hover { background: var(--color-accent-hover); border-color: var(--color-accent-hover); color: #fff; }
.action-hero-btn.danger:hover { background: rgba(239,68,68,0.1); border-color: #ef4444; color: #ef4444; }

.hero-stats { display: flex; gap: 0.75rem; }
.stat-chip { display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.8rem; color: var(--color-text-tertiary); }

/* ── Описание ── */
.description-section { background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: var(--radius-lg); padding: 1.1rem 1.25rem; margin-bottom: 1.5rem; }
.section-label { display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.78rem; font-weight: 700; color: var(--color-text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
.description-text { font-size: 0.9375rem; color: var(--color-text-secondary); line-height: 1.7; margin: 0; white-space: pre-wrap; }

/* ── Список аниме ── */
.anime-section { margin-bottom: 2rem; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }
.drag-hint { display: inline-flex; align-items: center; gap: 0.25rem; font-size: 0.75rem; color: var(--color-text-tertiary); }

.anime-empty {
  text-align: center; padding: 3rem 1rem; color: var(--color-text-tertiary);
  background: var(--color-background-surface); border: 1px dashed var(--color-divider-light);
  border-radius: var(--radius-lg); display: flex; flex-direction: column; align-items: center; gap: 0.75rem;
}
.btn-add-empty { padding: 0.6rem 1.25rem; background: var(--color-accent); color: #fff; border: none; border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600; cursor: pointer; }

.anime-list { display: flex; flex-direction: column; gap: 3px; }

.anime-row {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: var(--color-background-surface); border: 1px solid var(--color-divider-light);
  border-radius: 0.625rem; transition: border-color 0.15s, background 0.15s, box-shadow 0.2s, transform 0.15s;
  position: relative;
  touch-action: none;
}
.anime-row:hover { border-color: var(--color-accent); background: var(--color-background-active); }
.anime-row.is-dragging { 
  background: var(--color-background-active); 
  border-color: var(--color-accent); 
  cursor: grabbing !important;
  z-index: 100;
}
.anime-row.is-being-dragged {
  cursor: grabbing !important;
}
.anime-row.drag-above { 
  border-top: 2px solid var(--color-accent); 
  margin-top: -1px;
}
.anime-row.drag-below { 
  border-bottom: 2px solid var(--color-accent); 
  margin-bottom: -1px;
}

/* Drag handle */
.row-index-wrap { width: 26px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.row-index-wrap.is-handle { cursor: grab; touch-action: none; }
.row-index-wrap.is-handle:active { cursor: grabbing; }
.row-index { font-size: 0.78rem; font-weight: 600; color: var(--color-text-tertiary); }
.drag-handle { 
  width: 32px; 
  height: 36px; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  color: var(--color-text-tertiary); 
  border-radius: 6px; 
  transition: all 0.15s; 
  flex-shrink: 0;
}
.drag-handle:hover { 
  color: var(--color-accent); 
  background: rgba(58, 134, 255, 0.1); 
}
.drag-handle:active {
  cursor: grabbing;
  transform: scale(1.1);
}

/* Постер */
.row-poster-link { flex-shrink: 0; }
.row-poster { width: 44px; height: 62px; border-radius: 4px; overflow: hidden; background: var(--color-background-active); flex-shrink: 0; }
.row-poster img { width: 100%; height: 100%; object-fit: cover; }
.row-poster-ph { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: var(--color-text-tertiary); }

/* Инфо */
.row-info { flex: 1; min-width: 0; }
.row-title { display: block; font-size: 0.9rem; font-weight: 700; color: var(--color-text); text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: color 0.15s; margin-bottom: 0.15rem; }
.row-title:hover { color: var(--color-accent); }
.row-note { display: flex; align-items: center; gap: 0.25rem; font-size: 0.78rem; color: var(--color-text-secondary); margin-bottom: 0.15rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row-meta { display: flex; align-items: center; gap: 0.3rem; flex-wrap: wrap; }
.row-meta-chip { font-size: 0.7rem; padding: 1px 5px; background: var(--color-background-active); border-radius: 4px; color: var(--color-text-tertiary); font-weight: 600; }
.row-meta-chip.score { color: #f59e0b; }

/* Действия строки */
.row-actions { display: flex; align-items: center; gap: 1px; flex-shrink: 0; }
.row-action-btn {
  width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
  background: transparent; border: none; border-radius: 0.375rem;
  color: var(--color-text-tertiary); cursor: pointer; transition: all 0.15s; text-decoration: none;
}
.row-action-btn:hover { background: var(--color-background-active); color: var(--color-text); }
.row-action-btn.play:hover { background: rgba(58,134,255,0.12); color: var(--color-accent); }
.row-action-btn.danger:hover { background: rgba(239,68,68,0.1); color: #ef4444; }

/* ── Модалки ── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.72);
  backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 1rem;
}
.modal-box {
  background: var(--color-background-surface); border-radius: 1rem;
  width: 100%; max-width: 520px; max-height: 90vh; overflow: hidden;
  display: flex; flex-direction: column; box-shadow: 0 24px 64px rgba(0,0,0,0.5);
}
.modal-box-sm { max-width: 400px; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 1.1rem 1.4rem; border-bottom: 1px solid var(--color-divider); }
.modal-header h3 { font-size: 1.05rem; font-weight: 700; color: var(--color-text); margin: 0; }
.modal-close-btn { width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; background: transparent; border: none; border-radius: 0.5rem; color: var(--color-text-secondary); cursor: pointer; transition: all 0.15s; }
.modal-close-btn:hover { background: var(--color-background-active); color: var(--color-text); }
.modal-body { padding: 1.1rem 1.4rem; overflow-y: auto; flex: 1; }
.modal-footer { display: flex; gap: 0.6rem; padding: 1.1rem 1.4rem; border-top: 1px solid var(--color-divider); }

.btn-modal-cancel { flex: 1; padding: 0.7rem; background: transparent; border: 1px solid var(--color-divider-light); border-radius: 0.5rem; font-size: 0.875rem; font-weight: 600; color: var(--color-text-secondary); cursor: pointer; transition: all 0.15s; }
.btn-modal-cancel:hover { background: var(--color-background-active); }
.btn-modal-save {
  flex: 2; padding: 0.7rem; background: var(--color-accent); border: none; border-radius: 0.5rem;
  font-size: 0.875rem; font-weight: 700; color: #fff; cursor: pointer; transition: all 0.15s;
  display: flex; align-items: center; justify-content: center; gap: 0.35rem;
}
.btn-modal-save:hover:not(:disabled) { background: var(--color-accent-hover); }
.btn-modal-save:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-modal-save.outline { flex: 1; background: transparent; color: var(--color-accent); border: 1px solid var(--color-accent); }
.btn-modal-save.outline:hover { background: rgba(58,134,255,0.08); }
.btn-modal-danger {
  flex: 2; padding: 0.7rem; background: #ef4444; border: none; border-radius: 0.5rem;
  font-size: 0.875rem; font-weight: 700; color: #fff; cursor: pointer; transition: all 0.15s;
  display: flex; align-items: center; justify-content: center; gap: 0.35rem;
}
.btn-modal-danger:hover:not(:disabled) { background: #dc2626; }
.btn-modal-danger:disabled { opacity: 0.5; cursor: not-allowed; }

/* Поиск в модалке */
.modal-search-wrap { position: relative; display: flex; align-items: center; margin-bottom: 0.875rem; }
.modal-search-icon { position: absolute; left: 0.75rem; color: var(--color-text-tertiary); pointer-events: none; }
.modal-search-input { width: 100%; padding: 0.7rem 2.5rem 0.7rem 2.5rem; border: 1px solid var(--color-divider-light); border-radius: 0.625rem; font-size: 0.9rem; color: var(--color-text); background: var(--color-background-active); outline: none; transition: border-color 0.2s; }
.modal-search-input:focus { border-color: var(--color-accent); }
.modal-search-clear { position: absolute; right: 0.6rem; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; background: transparent; border: none; color: var(--color-text-tertiary); cursor: pointer; border-radius: 50%; }
.modal-loading { display: flex; align-items: center; gap: 0.5rem; justify-content: center; padding: 1.5rem; color: var(--color-text-tertiary); font-size: 0.875rem; }
.modal-results { display: flex; flex-direction: column; gap: 1px; max-height: 360px; overflow-y: auto; }
.modal-result-item { display: flex; align-items: center; gap: 0.7rem; padding: 0.55rem 0.5rem; border-radius: 0.5rem; cursor: pointer; transition: all 0.12s; }
.modal-result-item:hover:not(.disabled) { background: var(--color-background-active); }
.modal-result-item.disabled { opacity: 0.55; cursor: default; }
.modal-result-poster { width: 36px; height: 50px; object-fit: cover; border-radius: 3px; flex-shrink: 0; }
.modal-result-poster-ph { width: 36px; height: 50px; background: var(--color-background-active); border-radius: 3px; flex-shrink: 0; }
.modal-result-info { flex: 1; min-width: 0; }
.modal-result-title { display: block; font-size: 0.875rem; font-weight: 600; color: var(--color-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.modal-result-meta { font-size: 0.72rem; color: var(--color-text-tertiary); }
.already-added { font-size: 0.72rem; color: #22c55e; font-weight: 600; flex-shrink: 0; }
.btn-add-anime { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: var(--color-accent); border: none; border-radius: 50%; color: #fff; cursor: pointer; flex-shrink: 0; transition: all 0.15s; }
.btn-add-anime:hover { background: var(--color-accent-hover); transform: scale(1.1); }
.modal-empty { text-align: center; padding: 2rem; color: var(--color-text-tertiary); font-size: 0.875rem; }
.modal-empty-hint { text-align: center; padding: 2rem; color: var(--color-text-tertiary); font-size: 0.875rem; opacity: 0.6; }

/* Confirm модалка */
.confirm-body { text-align: center; padding: 0.5rem 0; }
.confirm-icon { font-size: 3rem; margin-bottom: 0.5rem; }
.confirm-anime-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; padding: 0.625rem; background: var(--color-background-active); border-radius: 0.5rem; }
.confirm-poster { width: 36px; height: 50px; object-fit: cover; border-radius: 3px; }
.confirm-poster-ph { width: 36px; height: 50px; background: var(--color-background-surface); border-radius: 3px; flex-shrink: 0; }
.confirm-anime-title { font-size: 0.875rem; font-weight: 600; color: var(--color-text); text-align: left; }
.confirm-text { font-size: 0.9rem; color: var(--color-text-secondary); line-height: 1.6; margin: 0; }

/* Формы */
.form-group { margin-bottom: 1rem; }
.form-label { display: block; font-size: 0.85rem; font-weight: 600; color: var(--color-text); margin-bottom: 0.35rem; }
.req { color: #f43f5e; }
.form-input, .form-textarea { width: 100%; padding: 0.7rem; font-family: inherit; border: 1px solid var(--color-divider-light); border-radius: 0.5rem; font-size: 0.9rem; color: var(--color-text); background: var(--color-background-surface); outline: none; transition: border-color 0.2s; box-sizing: border-box; }
.form-input:focus, .form-textarea:focus { border-color: var(--color-accent); }
.form-textarea { resize: vertical; min-height: 76px; }
.privacy-chips { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.privacy-chip { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.9rem; background: var(--color-background-active); border: 1px solid var(--color-divider-light); border-radius: 0.5rem; font-size: 0.85rem; font-weight: 600; color: var(--color-text); cursor: pointer; transition: all 0.15s; }
.privacy-chip.active { background: rgba(58,134,255,0.12); border-color: var(--color-accent); color: var(--color-accent); }
.visibility-hint { font-size: 0.8rem; color: var(--color-text-tertiary); margin: 0.5rem 0 0; }

/* Редактирование заметки */
.anime-edit-preview { display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem; background: var(--color-background-active); border-radius: 0.5rem; margin-bottom: 0.875rem; }
.edit-preview-poster { width: 38px; height: 54px; object-fit: cover; border-radius: 3px; }
.edit-preview-title { font-size: 0.9rem; font-weight: 700; color: var(--color-text); }

/* Экспорт */
.export-formats { display: flex; flex-direction: column; gap: 0.35rem; }
.export-fmt { display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0.875rem; background: var(--color-background-active); border: 1px solid var(--color-divider-light); border-radius: 0.5rem; cursor: pointer; transition: all 0.15s; }
.export-fmt.active { background: rgba(58,134,255,0.08); border-color: var(--color-accent); }
.fmt-icon { font-size: 1.2rem; flex-shrink: 0; }
.fmt-label { font-size: 0.875rem; font-weight: 600; color: var(--color-text); }
.fmt-desc { font-size: 0.72rem; color: var(--color-text-tertiary); }
.export-preview { background: var(--color-background-active); border-radius: 0.5rem; padding: 0.75rem; max-height: 200px; overflow-y: auto; }
.export-text { margin: 0; font-size: 0.78rem; color: var(--color-text-secondary); white-space: pre-wrap; font-family: 'Courier New', monospace; line-height: 1.5; }

/* Spinner */
.spinner-sm { width: 15px; height: 15px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
.spinner-sm-dark { width: 15px; height: 15px; border: 2px solid var(--color-divider); border-top-color: #ef4444; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Toast */
.toast-notification { position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); display: flex; align-items: center; gap: 0.45rem; padding: 0.7rem 1.1rem; background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 2rem; font-size: 0.85rem; font-weight: 600; color: var(--color-text); box-shadow: 0 8px 24px rgba(0,0,0,0.35); z-index: 9999; white-space: nowrap; }
.toast-notification svg { color: #22c55e; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from { opacity: 0; transform: translateX(-50%) translateY(16px); }
.toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

/* Модал анимации */
.modal-enter-active, .modal-leave-active { transition: all 0.22s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-box, .modal-leave-to .modal-box { transform: scale(0.96) translateY(12px); }

/* Responsive */
@media (max-width: 767px) {
  .playlist-detail-page { padding: 1rem; }
  .playlist-hero { flex-direction: column; }
  .hero-cover { width: 100%; max-width: 280px; }
  .detail-loading { flex-direction: column; }
  .hero-title { font-size: 1.3rem; }
  .hero-actions { gap: 0.3rem; }
  .action-hero-btn { padding: 0.5rem 0.7rem; font-size: 0.75rem; }
  .row-actions { gap: 0; }
}
</style>
