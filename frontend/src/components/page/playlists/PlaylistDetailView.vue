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
      <!-- Навигация -->
      <div class="breadcrumb">
        <router-link to="/playlists" class="breadcrumb-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Все плейлисты
        </router-link>
      </div>

      <!-- Шапка плейлиста -->
      <div class="playlist-hero">
        <!-- Превью из постеров -->
        <div class="hero-cover">
          <div class="cover-mosaic">
            <div
              v-for="(item, idx) in coverItems"
              :key="idx"
              :class="['mosaic-cell', `cell-${idx}`]"
            >
              <img
                v-if="item?.anime_poster"
                :src="getMediaUrl(item.anime_poster)"
                :alt="item.anime_title"
                @error="(e: Event) => ((e.target as HTMLImageElement).style.display='none')"
              />
              <div v-else class="mosaic-placeholder">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="2" y="2" width="20" height="20" rx="2"/>
                  <path d="M8 12l3 3 5-5"/>
                </svg>
              </div>
            </div>
            <div v-if="playlist.items_count > 4" class="mosaic-extra">
              +{{ playlist.items_count - 4 }}
            </div>
          </div>
          <!-- Приватность badge -->
          <div class="privacy-hero-badge" :class="privacyClass">
            <span class="privacy-icon">{{ privacyIcon }}</span>
            {{ privacyLabel }}
          </div>
        </div>

        <!-- Информация -->
        <div class="hero-info">
          <h1 class="hero-title">{{ playlist.title }}</h1>

          <div class="hero-meta">
            <div class="author-chip" @click="goToAuthor">
              <img
                v-if="playlist.user?.avatar"
                :src="getMediaUrl(playlist.user.avatar)"
                :alt="playlist.user_username"
                class="author-chip-avatar"
              />
              <div v-else class="author-chip-avatar-ph">
                {{ (playlist.user_username || '?')[0]?.toUpperCase() ?? '?' }}
              </div>
              <span>{{ playlist.user_username }}</span>
            </div>
            <span class="meta-dot">·</span>
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
              {{ playlist.items_count }} аниме
            </span>
            <span class="meta-dot">·</span>
            <span class="meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              {{ formatDate(playlist.created_at) }}
            </span>
          </div>

          <!-- Действия -->
          <div class="hero-actions">
            <!-- Для чужих: В избранное -->
            <button
              v-if="!isOwner"
              @click="toggleFavorite"
              :class="['action-hero-btn', { active: playlist.is_favorited }]"
            >
              <svg width="17" height="17" viewBox="0 0 24 24" :fill="playlist.is_favorited ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              {{ playlist.is_favorited ? 'В избранном' : 'В избранное' }}
            </button>

            <!-- Поделиться -->
            <button @click="sharePlaylist" class="action-hero-btn">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
              </svg>
              Поделиться
            </button>

            <!-- Скопировать все ссылки -->
            <button @click="copyAllLinks" class="action-hero-btn">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              Скопировать ссылки
            </button>

            <!-- Действия владельца -->
            <template v-if="isOwner">
              <button @click="showAddAnimeModal = true" class="action-hero-btn primary">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Добавить аниме
              </button>
              <button @click="showEditModal = true" class="action-hero-btn">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                Редактировать
              </button>
              <button @click="exportPlaylist" class="action-hero-btn">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Экспорт
              </button>
              <button @click="confirmDelete" class="action-hero-btn danger">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
                Удалить
              </button>
            </template>
          </div>

          <!-- Статистика (лайки/избранное) -->
          <div class="hero-stats">
            <span class="stat-chip">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
          </svg>
          Описание
        </div>
        <p class="description-text">{{ playlist.description }}</p>
      </div>

      <!-- Список аниме -->
      <div class="anime-section">
        <div class="section-header">
          <div class="section-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
            Аниме в плейлисте ({{ playlist.items_count }})
          </div>
          <div v-if="isOwner && playlist.items && playlist.items.length > 1" class="drag-hint">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
              <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
            </svg>
            Перетащите для сортировки
          </div>
        </div>

        <!-- Пустой список -->
        <div v-if="!playlist.items || playlist.items.length === 0" class="anime-empty">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
          </svg>
          <p>Плейлист пока пуст</p>
          <button v-if="isOwner" @click="showAddAnimeModal = true" class="btn-add-empty">Добавить аниме</button>
        </div>

        <!-- Строки аниме с drag&drop -->
        <div
          class="anime-list"
          @dragover.prevent
          @drop="handleDrop"
        >
          <div
            v-for="(item, index) in sortedItems"
            :key="item.id"
            :class="['anime-row', { dragging: dragIndex === index, 'drag-over': dragOverIndex === index }]"
            :draggable="isOwner"
            @dragstart="handleDragStart(index, $event)"
            @dragenter="handleDragEnter(index)"
            @dragend="handleDragEnd"
          >
            <!-- Номер и drag handle -->
            <div class="row-index-wrap">
              <span v-if="!isOwner" class="row-index">{{ index + 1 }}</span>
              <div v-else class="drag-handle" title="Перетащить">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="9" cy="5" r="1"/><circle cx="9" cy="12" r="1"/><circle cx="9" cy="19" r="1"/>
                  <circle cx="15" cy="5" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="19" r="1"/>
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
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
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
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                </svg>
                {{ item.notes }}
              </div>
              <div class="row-meta">
                <span v-if="item.anime_year" class="row-meta-chip">{{ item.anime_year }}</span>
                <span v-if="item.anime_score" class="row-meta-chip score">
                  ⭐ {{ item.anime_score.toFixed(1) }}
                </span>
                <span v-if="item.source_url" :class="['row-link-status', getLinkStatusClass(item.source_url)]">
                  {{ getLinkStatusIcon(item.source_url) }} {{ getLinkStatusText(item.source_url) }}
                </span>
              </div>
            </div>

            <!-- Действия строки -->
            <div class="row-actions">
              <router-link
                :to="`/anime/${item.anime}/watch`"
                class="row-action-btn play"
                title="Смотреть"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
              </router-link>

              <button
                v-if="item.source_url"
                @click="copyLink(item.source_url)"
                class="row-action-btn"
                title="Копировать ссылку"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
              </button>

              <button
                v-if="isOwner"
                @click="openEditItem(item)"
                class="row-action-btn"
                title="Редактировать"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>

              <button
                v-if="isOwner"
                @click="removeItem(item)"
                class="row-action-btn danger"
                title="Удалить из плейлиста"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- ===== МОДАЛКА ДОБАВЛЕНИЯ АНИМЕ ===== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="showAddAnimeModal" class="modal-overlay" @click.self="showAddAnimeModal = false">
          <div class="modal-box">
            <div class="modal-header">
              <h3>Добавить аниме в плейлист</h3>
              <button @click="showAddAnimeModal = false" class="modal-close-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="modal-search-wrap">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="modal-search-icon">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                <input
                  v-model="addAnimeSearch"
                  @input="debouncedAnimeSearch"
                  type="text"
                  placeholder="Поиск аниме..."
                  class="modal-search-input"
                  autofocus
                />
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
                  />
                  <div v-else class="modal-result-poster-ph"></div>
                  <div class="modal-result-info">
                    <span class="modal-result-title">{{ anime.title_ru || anime.title_en }}</span>
                    <span class="modal-result-meta">{{ anime.year }}{{ anime.episodes ? ` · ${anime.episodes} эп.` : '' }}</span>
                  </div>
                  <span v-if="isAnimeInPlaylist(anime.id)" class="already-added">✓ Уже добавлено</span>
                  <button v-else class="btn-add-anime">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                  </button>
                </div>
              </div>
              <div v-else-if="addAnimeSearch.length >= 2 && !animeSearchLoading" class="modal-empty">
                Ничего не найдено
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ===== МОДАЛКА РЕДАКТИРОВАНИЯ ПЛЕЙЛИСТА ===== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="showEditModal && playlist" class="modal-overlay" @click.self="showEditModal = false">
          <div class="modal-box">
            <div class="modal-header">
              <h3>Редактировать плейлист</h3>
              <button @click="showEditModal = false" class="modal-close-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
                  <label v-for="opt in privacyOptions" :key="opt.value" :class="['privacy-chip', { active: editForm.is_public === opt.isPublic }]">
                    <input type="radio" :value="opt.isPublic" v-model="editForm.is_public" style="display:none" />
                    <span>{{ opt.icon }}</span> {{ opt.label }}
                  </label>
                </div>
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

    <!-- ===== МОДАЛКА РЕДАКТИРОВАНИЯ ЭЛЕМЕНТА ===== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="editingItem" class="modal-overlay" @click.self="editingItem = null">
          <div class="modal-box">
            <div class="modal-header">
              <h3>Редактировать заметку</h3>
              <button @click="editingItem = null" class="modal-close-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
                <textarea v-model="editItemNotes" class="form-textarea" rows="3" maxlength="300" placeholder="Добавьте заметку к аниме..."></textarea>
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

    <!-- ===== МОДАЛКА ЭКСПОРТА ===== -->
    <Teleport to="body">
      <transition name="modal">
        <div v-if="showExportModal" class="modal-overlay" @click.self="showExportModal = false">
          <div class="modal-box">
            <div class="modal-header">
              <h3>Экспорт плейлиста</h3>
              <button @click="showExportModal = false" class="modal-close-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="export-formats">
                <label v-for="fmt in exportFormats" :key="fmt.value" :class="['export-fmt', { active: exportFormat === fmt.value }]">
                  <input type="radio" :value="fmt.value" v-model="exportFormat" style="display:none" />
                  <span class="fmt-icon">{{ fmt.icon }}</span>
                  <span>{{ fmt.label }}</span>
                </label>
              </div>
              <div class="export-preview">
                <pre class="export-text">{{ exportPreview }}</pre>
              </div>
            </div>
            <div class="modal-footer">
              <button @click="showExportModal = false" class="btn-modal-cancel">Закрыть</button>
              <button @click="copyExport" class="btn-modal-save">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                Скопировать
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
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {{ toastMsg }}
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import playlistsApi, { type Playlist, type PlaylistItem } from '@/api/playlists'
import apiClient, { getMediaUrl } from '@/api/client'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const playlist = ref<Playlist | null>(null)
const loading = ref(true)
const currentUserId = ref<number | undefined>(undefined)

// Модалки
const showAddAnimeModal = ref(false)
const showEditModal = ref(false)
const showExportModal = ref(false)
const editingItem = ref<PlaylistItem | null>(null)

// Состояние drag&drop
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

// Добавление аниме
const addAnimeSearch = ref('')
const animeSearchResults = ref<any[]>([])
const animeSearchLoading = ref(false)
let searchTimer: ReturnType<typeof setTimeout> | null = null

// Редактирование
const editForm = ref({ title: '', description: '', is_public: true })
const editSaving = ref(false)
const editItemNotes = ref('')
const itemSaving = ref(false)

// Экспорт
const exportFormat = ref<'text' | 'text_links' | 'json' | 'csv'>('text')
const exportFormats = [
  { value: 'text', label: 'Текст', icon: '📝' },
  { value: 'text_links', label: 'Текст со ссылками', icon: '🔗' },
  { value: 'json', label: 'JSON', icon: '{ }' },
  { value: 'csv', label: 'CSV', icon: '📊' }
]

const toastMsg = ref('')

const privacyOptions = [
  { value: 'public', label: 'Публичный', icon: '🌍', isPublic: true },
  { value: 'private', label: 'Приватный', icon: '🔒', isPublic: false }
]

// Вычисляемые
const isOwner = computed(() => {
  if (!playlist.value || !currentUserId.value) return false
  return playlist.value.user_id === currentUserId.value
})

const sortedItems = computed(() => {
  if (!playlist.value?.items) return []
  return [...playlist.value.items].sort((a, b) => (a.position ?? 0) - (b.position ?? 0))
})

const coverItems = computed(() => {
  if (!playlist.value?.items) return Array(4).fill(null)
  const items = sortedItems.value.slice(0, 4)
  while (items.length < 4) items.push(null as any)
  return items
})

const privacyClass = computed(() => {
  if (!playlist.value) return ''
  return playlist.value.is_public ? 'privacy-public' : 'privacy-private'
})

const privacyIcon = computed(() => {
  if (!playlist.value) return '🌍'
  return playlist.value.is_public ? '🌍' : '🔒'
})

const privacyLabel = computed(() => {
  if (!playlist.value) return ''
  return playlist.value.is_public ? 'Публичный' : 'Приватный'
})

const exportPreview = computed(() => {
  if (!playlist.value) return ''
  const items = sortedItems.value

  if (exportFormat.value === 'text') {
    return `Плейлист: ${playlist.value.title}\nАвтор: @${playlist.value.user_username}\n\n` +
      items.map((item, i) => `${i + 1}. ${item.anime_title}${item.notes ? `\n   Заметка: ${item.notes}` : ''}`).join('\n')
  }
  if (exportFormat.value === 'text_links') {
    return `Плейлист: ${playlist.value.title}\nАвтор: @${playlist.value.user_username}\n\n` +
      items.map((item, i) => `${i + 1}. ${item.anime_title}${item.source_url ? `\n   Ссылка: ${item.source_url}` : ''}${item.notes ? `\n   Заметка: ${item.notes}` : ''}`).join('\n')
  }
  if (exportFormat.value === 'json') {
    return JSON.stringify({
      title: playlist.value.title,
      author: playlist.value.user_username,
      items: items.map(item => ({
        title: item.anime_title,
        source_url: item.source_url || null,
        notes: item.notes || null
      }))
    }, null, 2)
  }
  if (exportFormat.value === 'csv') {
    const header = 'Название,Ссылка,Заметка'
    const rows = items.map(item => `"${item.anime_title}","${item.source_url || ''}","${item.notes || ''}"`)
    return [header, ...rows].join('\n')
  }
  return ''
})

// Методы
const loadPlaylist = async () => {
  const id = route.params.id
  if (!id) return

  loading.value = true
  try {
    const response = await playlistsApi.getPlaylist(parseInt(id as string))
    playlist.value = response.data
    if (isOwner.value) {
      editForm.value = {
        title: response.data.title,
        description: response.data.description || '',
        is_public: response.data.is_public ?? true
      }
    }
  } catch (err) {
    console.error('Ошибка загрузки плейлиста:', err)
    playlist.value = null
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}

const goToAuthor = () => {
  if (playlist.value?.user_id) {
    router.push(`/profile/${playlist.value.user_id}`)
  }
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

const sharePlaylist = () => {
  navigator.clipboard.writeText(window.location.href)
  showToast('Ссылка скопирована!')
}

const copyAllLinks = () => {
  if (!playlist.value?.items) return
  const links = sortedItems.value
    .filter(i => i.source_url)
    .map(i => `${i.anime_title}: ${i.source_url}`)
    .join('\n')
  if (!links) { showToast('Нет ссылок для копирования'); return }
  navigator.clipboard.writeText(links)
  showToast('Все ссылки скопированы!')
}

const copyLink = (url: string) => {
  navigator.clipboard.writeText(url)
  showToast('Ссылка скопирована!')
}

const exportPlaylist = () => {
  showExportModal.value = true
}

const copyExport = () => {
  navigator.clipboard.writeText(exportPreview.value)
  showToast('Скопировано!')
}

const confirmDelete = async () => {
  if (!playlist.value || !confirm(`Удалить плейлист «${playlist.value.title}»?`)) return
  try {
    await playlistsApi.deletePlaylist(playlist.value.id)
    router.push('/playlists')
  } catch {}
}

// Добавление аниме
const debouncedAnimeSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  if (addAnimeSearch.value.length < 2) { animeSearchResults.value = []; return }
  searchTimer = setTimeout(async () => {
    animeSearchLoading.value = true
    try {
      const res = await apiClient.get('/anime/anime/', { params: { search: addAnimeSearch.value, page_size: 10 } })
      animeSearchResults.value = res.data.results || res.data
    } catch {} finally {
      animeSearchLoading.value = false
    }
  }, 350)
}

const isAnimeInPlaylist = (animeId: number) => {
  if (!playlist.value?.items) return false
  return playlist.value.items.some(i => i.anime === animeId || (i as any).anime_id === animeId)
}

const addAnimeToPlaylist = async (anime: any) => {
  if (!playlist.value || isAnimeInPlaylist(anime.id)) return
  try {
    await playlistsApi.addItemToPlaylist(playlist.value.id, { anime: anime.id })
    await loadPlaylist()
    addAnimeSearch.value = ''
    animeSearchResults.value = []
    showToast('Аниме добавлено в плейлист!')
  } catch (err: any) {
    showToast(err.response?.data?.error || 'Ошибка добавления')
  }
}

// Удаление элемента
const removeItem = async (item: PlaylistItem) => {
  if (!playlist.value || !confirm('Удалить аниме из плейлиста?')) return
  try {
    await playlistsApi.removeFromPlaylist(playlist.value.id, item.id)
    await loadPlaylist()
    showToast('Аниме удалено из плейлиста')
  } catch {}
}

// Редактирование заметки
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

// Сохранение плейлиста
const saveEdit = async () => {
  if (!playlist.value || !editForm.value.title.trim()) return
  editSaving.value = true
  try {
    const res = await playlistsApi.updatePlaylist(playlist.value.id, {
      title: editForm.value.title.trim(),
      description: editForm.value.description,
      is_public: editForm.value.is_public
    })
    Object.assign(playlist.value, res.data)
    showEditModal.value = false
    showToast('Плейлист обновлён!')
  } catch {} finally {
    editSaving.value = false
  }
}

// Drag & drop
const handleDragStart = (index: number, event: DragEvent) => {
  dragIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

const handleDragEnter = (index: number) => {
  dragOverIndex.value = index
}

const handleDrop = async () => {
  if (dragIndex.value === null || dragOverIndex.value === null || !playlist.value) {
    dragIndex.value = null; dragOverIndex.value = null; return
  }
  const items = [...sortedItems.value]
  const [moved] = items.splice(dragIndex.value, 1)
  if (moved) {
    items.splice(dragOverIndex.value, 0, moved)
  }

  // Обновляем позиции
  const reorderData = items.map((item, idx) => ({ id: item.id, position: idx + 1 }))

  try {
    await playlistsApi.reorderPlaylistItems(playlist.value.id, reorderData)
    items.forEach((item, idx) => { item.position = idx + 1 })
    if (playlist.value.items) {
      playlist.value.items = items
    }
  } catch {}

  dragIndex.value = null
  dragOverIndex.value = null
}

const handleDragEnd = () => {
  dragIndex.value = null
  dragOverIndex.value = null
}

// Статус ссылки
const getLinkStatusClass = (url: string) => {
  if (!url) return ''
  if (url.includes('jut.su') || url.includes('animego') || url.includes('anilibria')) return 'status-ok'
  return 'status-unknown'
}
const getLinkStatusIcon = (url: string) => {
  const cls = getLinkStatusClass(url)
  if (cls === 'status-ok') return '✅'
  return '⚠️'
}
const getLinkStatusText = (url: string) => {
  const cls = getLinkStatusClass(url)
  if (cls === 'status-ok') return 'Работает'
  return 'Неизвестно'
}

const showToast = (msg: string) => {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = '' }, 3000)
}

onMounted(async () => {
  if (authStore.user) currentUserId.value = authStore.user.id
  await loadPlaylist()
})
</script>

<style scoped>
.playlist-detail-page {
  padding: 1.5rem;
  max-width: 960px;
  margin: 0 auto;
  min-height: 100vh;
}

/* Загрузка */
.detail-loading {
  display: flex;
  gap: 2rem;
  padding: 2rem 0;
}
.loading-cover-skeleton {
  width: 280px;
  flex-shrink: 0;
  aspect-ratio: 1;
  background: var(--color-background-active);
  border-radius: var(--radius-lg, 0.75rem);
  animation: shimmer 1.5s infinite;
}
.loading-info-skeleton {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-top: 0.5rem;
}
.sk-line {
  height: 14px;
  background: var(--color-background-active);
  border-radius: 7px;
  animation: shimmer 1.5s infinite;
}
.w-60 { width: 60%; }
.w-40 { width: 40%; }
.w-80 { width: 80%; }
.sk-actions { display: flex; gap: 0.75rem; margin-top: 0.5rem; }
.sk-btn { width: 120px; height: 40px; background: var(--color-background-active); border-radius: 0.5rem; animation: shimmer 1.5s infinite; }
@keyframes shimmer { 0%,100% { opacity: 1; } 50% { opacity: 0.45; } }

/* Не найден */
.not-found {
  text-align: center;
  padding: 6rem 2rem;
}
.not-found-icon { font-size: 4rem; margin-bottom: 1rem; }
.not-found h2 { font-size: 1.5rem; font-weight: 700; color: var(--color-text); margin: 0 0 0.5rem; }
.not-found p { color: var(--color-text-secondary); margin: 0 0 1.5rem; }
.btn-back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 600;
}

/* Breadcrumb */
.breadcrumb { margin-bottom: 1.5rem; }
.breadcrumb-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  text-decoration: none;
  transition: color 0.2s;
}
.breadcrumb-link:hover { color: var(--color-accent); }

/* ===== HERO ===== */
.playlist-hero {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
  align-items: flex-start;
}

.hero-cover {
  width: 260px;
  flex-shrink: 0;
  position: relative;
}

.cover-mosaic {
  width: 100%;
  aspect-ratio: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 3px;
  border-radius: var(--radius-lg, 0.75rem);
  overflow: hidden;
  background: var(--color-background-active);
}
.mosaic-cell {
  position: relative;
  background: var(--color-background-active);
  overflow: hidden;
}
.mosaic-cell img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}
.playlist-hero:hover .mosaic-cell img { transform: scale(1.05); }
.mosaic-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
}
.mosaic-extra {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0,0,0,0.75);
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 999px;
  backdrop-filter: blur(4px);
}

.privacy-hero-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  backdrop-filter: blur(6px);
}
.privacy-public { background: rgba(34,197,94,0.85); color: #fff; }
.privacy-private { background: rgba(239,68,68,0.85); color: #fff; }

.hero-info { flex: 1; }
.hero-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-text);
  margin: 0 0 0.875rem;
  line-height: 1.3;
}

.hero-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}
.author-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  cursor: pointer;
  transition: color 0.2s;
}
.author-chip:hover { color: var(--color-accent); }
.author-chip-avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  object-fit: cover;
}
.author-chip-avatar-ph {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
  font-weight: 700;
}
.meta-dot { color: var(--color-divider-light); }
.meta-item { display: inline-flex; align-items: center; gap: 0.25rem; }

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.action-hero-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.625rem 1rem;
  background: var(--color-background-active);
  border: 1px solid var(--color-divider-light);
  border-radius: var(--radius-lg, 0.625rem);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.action-hero-btn:hover {
  background: var(--color-background-surface);
  border-color: var(--color-accent);
  color: var(--color-accent);
}
.action-hero-btn.active {
  background: rgba(251,191,36,0.15);
  border-color: #f59e0b;
  color: #f59e0b;
}
.action-hero-btn.primary {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}
.action-hero-btn.primary:hover {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  color: #fff;
}
.action-hero-btn.danger:hover {
  background: rgba(239,68,68,0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.hero-stats { display: flex; gap: 0.75rem; }
.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
}

/* Описание */
.description-section {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: var(--radius-lg, 0.75rem);
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}
.section-label {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
}
.description-text {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin: 0;
  white-space: pre-wrap;
}

/* Список аниме */
.anime-section { margin-bottom: 2rem; }
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.875rem;
}
.drag-hint {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.anime-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-tertiary);
  background: var(--color-background-surface);
  border: 1px dashed var(--color-divider-light);
  border-radius: var(--radius-lg, 0.75rem);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.btn-add-empty {
  padding: 0.625rem 1.25rem;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.anime-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.anime-row {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.75rem 0.875rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.625rem;
  transition: all 0.2s;
}
.anime-row:hover { border-color: var(--color-accent); background: var(--color-background-active); }
.anime-row.dragging { opacity: 0.4; }
.anime-row.drag-over { border-color: var(--color-accent); box-shadow: 0 0 0 2px rgba(58,134,255,0.25); }

.row-index-wrap { width: 28px; text-align: center; flex-shrink: 0; }
.row-index { font-size: 0.8125rem; font-weight: 600; color: var(--color-text-tertiary); }
.drag-handle {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  cursor: grab;
  border-radius: 4px;
  transition: all 0.2s;
}
.drag-handle:hover { background: var(--color-background-active); color: var(--color-text); }
.drag-handle:active { cursor: grabbing; }

.row-poster-link { flex-shrink: 0; }
.row-poster {
  width: 48px;
  height: 68px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--color-background-active);
  flex-shrink: 0;
}
.row-poster img { width: 100%; height: 100%; object-fit: cover; }
.row-poster-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
}

.row-info { flex: 1; min-width: 0; }
.row-title {
  display: block;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.2s;
  margin-bottom: 0.2rem;
}
.row-title:hover { color: var(--color-accent); }
.row-note {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.2rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.row-meta { display: flex; align-items: center; gap: 0.375rem; flex-wrap: wrap; }
.row-meta-chip {
  font-size: 0.72rem;
  padding: 2px 6px;
  background: var(--color-background-active);
  border-radius: 4px;
  color: var(--color-text-tertiary);
  font-weight: 600;
}
.row-meta-chip.score { color: #f59e0b; }
.row-link-status { font-size: 0.72rem; }
.status-ok { color: #22c55e; }
.status-unknown { color: #f59e0b; }

.row-actions { display: flex; align-items: center; gap: 0.25rem; flex-shrink: 0; }
.row-action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.375rem;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
}
.row-action-btn:hover { background: var(--color-background-active); color: var(--color-text); }
.row-action-btn.play:hover { background: rgba(58,134,255,0.15); color: var(--color-accent); }
.row-action-btn.danger:hover { background: rgba(239,68,68,0.1); color: #ef4444; }

/* ===== МОДАЛКИ ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}
.modal-box {
  background: var(--color-background-surface);
  border-radius: 1rem;
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 64px rgba(0,0,0,0.5);
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-divider);
}
.modal-header h3 { font-size: 1.1rem; font-weight: 700; color: var(--color-text); margin: 0; }
.modal-close-btn {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: none;
  border-radius: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer; transition: all 0.2s;
}
.modal-close-btn:hover { background: var(--color-background-active); color: var(--color-text); }
.modal-body { padding: 1.25rem 1.5rem; overflow-y: auto; flex: 1; }
.modal-footer {
  display: flex; gap: 0.75rem; padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--color-divider);
}
.btn-modal-cancel {
  flex: 1; padding: 0.75rem; background: transparent;
  border: 1px solid var(--color-divider-light); border-radius: 0.5rem;
  font-size: 0.875rem; font-weight: 600; color: var(--color-text-secondary);
  cursor: pointer; transition: all 0.2s;
}
.btn-modal-cancel:hover { background: var(--color-background-active); }
.btn-modal-save {
  flex: 2; padding: 0.75rem; background: var(--color-accent);
  border: none; border-radius: 0.5rem;
  font-size: 0.875rem; font-weight: 700; color: #fff;
  cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center; gap: 0.375rem;
}
.btn-modal-save:hover:not(:disabled) { background: var(--color-accent-hover); }
.btn-modal-save:disabled { opacity: 0.5; cursor: not-allowed; }

/* Поиск в модалке */
.modal-search-wrap {
  position: relative; display: flex; align-items: center; margin-bottom: 1rem;
}
.modal-search-icon { position: absolute; left: 0.875rem; color: var(--color-text-tertiary); }
.modal-search-input {
  width: 100%; padding: 0.75rem 0.875rem 0.75rem 2.75rem;
  border: 1px solid var(--color-divider-light); border-radius: 0.625rem;
  font-size: 0.9375rem; color: var(--color-text); background: var(--color-background-active);
  outline: none; transition: border-color 0.2s;
}
.modal-search-input:focus { border-color: var(--color-accent); }
.modal-loading {
  display: flex; align-items: center; gap: 0.5rem;
  justify-content: center; padding: 1.5rem; color: var(--color-text-tertiary);
}
.modal-results { display: flex; flex-direction: column; gap: 0.25rem; max-height: 350px; overflow-y: auto; }
.modal-result-item {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.625rem; border-radius: 0.5rem;
  cursor: pointer; transition: all 0.15s;
}
.modal-result-item:hover:not(.disabled) { background: var(--color-background-active); }
.modal-result-item.disabled { opacity: 0.6; cursor: default; }
.modal-result-poster {
  width: 38px; height: 54px; object-fit: cover;
  border-radius: 3px; flex-shrink: 0;
}
.modal-result-poster-ph {
  width: 38px; height: 54px; background: var(--color-background-active);
  border-radius: 3px; flex-shrink: 0;
}
.modal-result-info { flex: 1; min-width: 0; }
.modal-result-title {
  display: block; font-size: 0.875rem; font-weight: 600; color: var(--color-text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.modal-result-meta { font-size: 0.75rem; color: var(--color-text-tertiary); }
.already-added { font-size: 0.75rem; color: #22c55e; font-weight: 600; flex-shrink: 0; }
.btn-add-anime {
  width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
  background: var(--color-accent); border: none; border-radius: 50%;
  color: #fff; cursor: pointer; flex-shrink: 0; transition: all 0.2s;
}
.btn-add-anime:hover { background: var(--color-accent-hover); transform: scale(1.1); }
.modal-empty { text-align: center; padding: 2rem; color: var(--color-text-tertiary); }

/* Формы */
.form-group { margin-bottom: 1rem; }
.form-label { display: block; font-size: 0.875rem; font-weight: 600; color: var(--color-text); margin-bottom: 0.375rem; }
.req { color: var(--color-accent-pink); }
.form-input, .form-textarea {
  width: 100%; padding: 0.75rem; font-family: inherit;
  border: 1px solid var(--color-divider-light); border-radius: 0.5rem;
  font-size: 0.9375rem; color: var(--color-text); background: var(--color-background-surface);
  outline: none; transition: border-color 0.2s;
}
.form-input:focus, .form-textarea:focus { border-color: var(--color-accent); }
.form-textarea { resize: vertical; min-height: 80px; }
.privacy-chips { display: flex; gap: 0.5rem; }
.privacy-chip {
  display: inline-flex; align-items: center; gap: 0.375rem;
  padding: 0.5rem 1rem; background: var(--color-background-active);
  border: 1px solid var(--color-divider-light); border-radius: 0.5rem;
  font-size: 0.875rem; font-weight: 600; color: var(--color-text);
  cursor: pointer; transition: all 0.2s;
}
.privacy-chip.active {
  background: rgba(58,134,255,0.12); border-color: var(--color-accent); color: var(--color-accent);
}

/* Редактирование элемента */
.anime-edit-preview {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.75rem; background: var(--color-background-active);
  border-radius: 0.5rem; margin-bottom: 1rem;
}
.edit-preview-poster {
  width: 40px; height: 56px; object-fit: cover; border-radius: 3px;
}
.edit-preview-title { font-size: 0.9375rem; font-weight: 700; color: var(--color-text); }

/* Экспорт */
.export-formats { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
.export-fmt {
  display: inline-flex; align-items: center; gap: 0.375rem;
  padding: 0.5rem 0.875rem; background: var(--color-background-active);
  border: 1px solid var(--color-divider-light); border-radius: 0.5rem;
  font-size: 0.8125rem; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.export-fmt.active {
  background: rgba(58,134,255,0.12); border-color: var(--color-accent); color: var(--color-accent);
}
.export-preview {
  background: var(--color-background-active); border-radius: 0.5rem;
  padding: 0.875rem; max-height: 240px; overflow-y: auto;
}
.export-text { margin: 0; font-size: 0.8125rem; color: var(--color-text-secondary); white-space: pre-wrap; font-family: inherit; }

/* Spinner */
.spinner-sm {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Toast */
.toast-notification {
  position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 2rem; font-size: 0.875rem; font-weight: 600;
  color: var(--color-text); box-shadow: 0 8px 24px rgba(0,0,0,0.35);
  z-index: 9999; white-space: nowrap;
}
.toast-notification svg { color: #22c55e; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from { opacity: 0; transform: translateX(-50%) translateY(16px); }
.toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

/* Transitions */
.modal-enter-active, .modal-leave-active { transition: all 0.25s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-box, .modal-leave-to .modal-box { transform: scale(0.95) translateY(16px); }

/* ===== RESPONSIVE ===== */
@media (max-width: 767px) {
  .playlist-detail-page { padding: 1rem; }
  .playlist-hero { flex-direction: column; }
  .hero-cover { width: 100%; }
  .detail-loading { flex-direction: column; }
  .loading-cover-skeleton { width: 100%; max-width: 260px; }
  .anime-row { padding: 0.625rem; }
  .hero-title { font-size: 1.375rem; }
  .hero-actions { gap: 0.375rem; }
  .action-hero-btn { padding: 0.5rem 0.75rem; font-size: 0.75rem; }
  .row-actions { gap: 0; }
}
</style>
