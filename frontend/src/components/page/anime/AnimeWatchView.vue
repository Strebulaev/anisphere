<template>
  <div class="anime-watch-page">
    <div class="watch-container">
      <div class="left-column">

        <!-- Плеер -->
        <div class="player-wrapper">
          <div class="player-container" ref="playerContainer">
            <KodikPlayer
              v-if="kodikLink && !useCustomPlayer"
              :link="kodikLink"
              :autoplay="autoplay"
              :season="currentSeason"
              :episode="currentEpisode"
              :translation-id="selectedTranslation?.id ?? null"
              ref="kodikPlayer"
              @ready="onPlayerReady"
              @play="onPlay"
              @pause="onPause"
              @timeUpdate="onTimeUpdate"
              @durationUpdate="onDurationUpdate"
              @currentEpisode="onCurrentEpisode"
              @videoStarted="onVideoStarted"
              @videoEnded="onVideoEnded"
              @skipButton="onSkipButton"
              @translationChanged="onKodikTranslationChanged"
              @error="onPlayerError"
            />
            <!-- <CustomVideoPlayer
              v-else-if="useCustomPlayer && customVideoUrl"
              :video-url="customVideoUrl"
              :poster="posterSrc ?? undefined"
              :autoplay="autoplay"
              @ready="onPlayerReady"
              @play="onPlay"
              @pause="onPause"
              @timeUpdate="onTimeUpdate"
              @durationUpdate="onDurationUpdate"
              @videoEnded="onVideoEnded"
              @error="onPlayerError"
            /> -->
            <div v-else-if="loading" class="player-placeholder loading">
              <div class="spinner"></div>
              <p>Загрузка плеера...</p>
            </div>
            <div v-else-if="error" class="player-placeholder error">
              <div class="error-icon"><SakuraIcon name="warning" />️</div>
              <p>{{ error }}</p>
              <button @click="retryLoad" class="btn-retry">Попробовать снова</button>
            </div>
            <div v-else class="player-placeholder">
              <div class="no-video-icon"> <SakuraIcon name="play" /> </div>
              <p>Видео недоступно</p>
            </div>


          </div>
        </div>


        <!-- ─── Быстрые кнопки скачивания ─────────────────── -->
        <div class="quick-dl-bar">
          <!-- Опенинг -->
          <div class="qdl-group">
            <button
              class="qdl-btn"
              :class="{ 'qdl-loading': openingVideoState.loading, 'qdl-done': openingVideoState.done, 'qdl-error': openingVideoState.error }"
              :disabled="openingVideoState.loading"
              @click="handleDownloadOpening('video')"
              title="Скачать опенинг этой серии (видео)"
            >
              <span v-if="openingVideoState.loading" class="qdl-spinner"></span>
              <svg v-else-if="openingVideoState.done" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span class="qdl-label">{{ openingVideoState.loading ? `${openingVideoState.progress}%` : openingVideoState.done ? 'Готово' : 'Опенинг MP4' }}</span>
              <div v-if="openingVideoState.loading" class="qdl-bar"><div class="qdl-fill" :style="{ width: openingVideoState.progress + '%' }"></div></div>
            </button>
            <button
              class="qdl-btn qdl-secondary"
              :class="{ 'qdl-loading': openingAudioState.loading, 'qdl-done': openingAudioState.done, 'qdl-error': openingAudioState.error }"
              :disabled="openingAudioState.loading"
              @click="handleDownloadOpening('audio')"
              title="Скачать опенинг этой серии (аудио)"
            >
              <span v-if="openingAudioState.loading" class="qdl-spinner"></span>
              <svg v-else-if="openingAudioState.done" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
              <span class="qdl-label">{{ openingAudioState.loading ? `${openingAudioState.progress}%` : openingAudioState.done ? 'Готово' : 'Опенинг MP3' }}</span>
              <div v-if="openingAudioState.loading" class="qdl-bar"><div class="qdl-fill" :style="{ width: openingAudioState.progress + '%' }"></div></div>
            </button>
          </div>

          <!-- Эндинг -->
          <div class="qdl-group">
            <button
              class="qdl-btn"
              :class="{ 'qdl-loading': endingVideoState.loading, 'qdl-done': endingVideoState.done, 'qdl-error': endingVideoState.error }"
              :disabled="endingVideoState.loading"
              @click="handleDownloadEnding('video')"
              title="Скачать эндинг этой серии (видео)"
            >
              <span v-if="endingVideoState.loading" class="qdl-spinner"></span>
              <svg v-else-if="endingVideoState.done" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span class="qdl-label">{{ endingVideoState.loading ? `${endingVideoState.progress}%` : endingVideoState.done ? 'Готово' : 'Эндинг MP4' }}</span>
              <div v-if="endingVideoState.loading" class="qdl-bar"><div class="qdl-fill" :style="{ width: endingVideoState.progress + '%' }"></div></div>
            </button>
            <button
              class="qdl-btn qdl-secondary"
              :class="{ 'qdl-loading': endingAudioState.loading, 'qdl-done': endingAudioState.done, 'qdl-error': endingAudioState.error }"
              :disabled="endingAudioState.loading"
              @click="handleDownloadEnding('audio')"
              title="Скачать эндинг этой серии (аудио)"
            >
              <span v-if="endingAudioState.loading" class="qdl-spinner"></span>
              <svg v-else-if="endingAudioState.done" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
              <span class="qdl-label">{{ endingAudioState.loading ? `${endingAudioState.progress}%` : endingAudioState.done ? 'Готово' : 'Эндинг MP3' }}</span>
              <div v-if="endingAudioState.loading" class="qdl-bar"><div class="qdl-fill" :style="{ width: endingAudioState.progress + '%' }"></div></div>
            </button>
          </div>

          <!-- Серия целиком -->
          <button
            class="qdl-btn qdl-episode"
            :class="{ 'qdl-loading': episodeDownloadState.loading, 'qdl-done': episodeDownloadState.done, 'qdl-error': episodeDownloadState.error }"
            :disabled="episodeDownloadState.loading"
            @click="handleDownloadEpisode"
            title="Скачать серию целиком"
          >
            <span v-if="episodeDownloadState.loading" class="qdl-spinner"></span>
            <svg v-else-if="episodeDownloadState.done" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
            <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span class="qdl-label">{{ episodeDownloadState.loading ? `${episodeDownloadState.progress}%` : episodeDownloadState.done ? 'Готово' : `Серия ${currentEpisode}` }}</span>
            <div v-if="episodeDownloadState.loading" class="qdl-bar"><div class="qdl-fill" :style="{ width: episodeDownloadState.progress + '%' }"></div></div>
          </button>

          <!-- Произвольный отрезок: кнопка-иконка -->
          <button
            class="qdl-btn qdl-clip-icon"
            :class="{ 'qdl-active': showClipModal }"
            @click="() => { showClipModal = !showClipModal; if (showClipModal) setClipFromCurrent() }"
            title="Вырезать произвольный фрагмент"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/>
              <line x1="20" y1="4" x2="8.12" y2="15.88"/>
              <line x1="14.47" y1="14.48" x2="20" y2="20"/>
              <line x1="8.12" y1="8.12" x2="12" y2="12"/>
            </svg>
            <span class="qdl-label">Фрагмент</span>
          </button>

          <!-- Свернуть в мини-плеер -->
          <button
            class="qdl-btn qdl-float-btn"
            :class="{ 'qdl-active': floatingPlayerVisible }"
            @click="launchFloatingPlayer"
            title="Свернуть в мини-плеер"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="2" width="20" height="20" rx="2"/>
              <rect x="11" y="11" width="9" height="7" rx="1" fill="currentColor" stroke="none"/>
            </svg>
            <span class="qdl-label">Мини</span>
          </button>

          <!-- Ошибки под кнопками -->
          <p v-if="openingVideoState.error || openingAudioState.error" class="qdl-err-text"><SakuraIcon name="warning" /> Опенинг: {{ openingVideoState.error || openingAudioState.error }}</p>
          <p v-if="endingVideoState.error || endingAudioState.error" class="qdl-err-text"><SakuraIcon name="warning" /> Эндинг: {{ endingVideoState.error || endingAudioState.error }}</p>
          <p v-if="episodeDownloadState.error" class="qdl-err-text"><SakuraIcon name="warning" /> Серия: {{ episodeDownloadState.error }}</p>
        </div>

        <!-- Форма произвольного отрезка (inline под кнопками) -->
        <div v-if="showClipModal" class="clip-form-inline">
          <div class="clip-times">
            <div class="clip-time-field">
              <label>Начало</label>
              <input v-model="clipStartInput" class="clip-time-input" placeholder="0:00" :disabled="customState.loading" />
            </div>
            <div class="clip-time-arrow">→</div>
            <div class="clip-time-field">
              <label>Конец</label>
              <input v-model="clipEndInput" class="clip-time-input" placeholder="1:30" :disabled="customState.loading" />
            </div>
          </div>
          <div class="clip-label-row">
            <input v-model="clipLabel" class="clip-label-input" placeholder="Название (необязательно)" :disabled="customState.loading" maxlength="40" />
          </div>
          <div class="clip-hint" v-if="duration > 0">
            Текущее время: <b>{{ formatSec(currentTime) }}</b> / {{ formatSec(duration) }}
            <button class="clip-hint-btn" @click="setClipFromCurrent" :disabled="customState.loading">← Вставить</button>
          </div>
          <div class="clip-actions">
            <button
              class="tdc-btn clip-download-btn"
              :class="{ 'tdc-loading': customState.loading, 'tdc-done': customState.done }"
              :disabled="customState.loading || !clipStartInput || !clipEndInput"
              @click="handleDownloadSegment"
            >
              <span v-if="customState.loading" class="tdc-spinner"></span>
              <span v-else-if="customState.done">✓</span>
              <span v-else><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></span>
              <span class="tdc-label">{{ customState.loading ? `Обработка... ${customState.progress}%` : customState.done ? 'Готово ✓' : 'Скачать MP4' }}</span>
              <div v-if="customState.loading" class="tdc-progress-bar"><div class="tdc-progress-fill" :style="{ width: customState.progress + '%' }"></div></div>
            </button>
            <button class="clip-cancel-btn" @click="showClipModal = false" :disabled="customState.loading">✕</button>
          </div>
          <p v-if="customState.error" class="tdc-error-text"><SakuraIcon name="warning" /> {{ customState.error }}</p>
        </div>

        <!-- Информация под плеером -->
        <div class="anime-info-under">
          <div class="anime-header">
            <h1 class="anime-title">{{ anime?.title_ru || anime?.title_en }}</h1>
            <div class="anime-badges">
              <span v-if="anime?.year" class="badge year-badge">{{ anime.year }}</span>
              <span v-if="anime?.kind" class="badge kind-badge">{{ getKindText(anime.kind) }}</span>
              <span v-if="anime?.episodes" class="badge episodes-badge">{{ anime.episodes }} эп.</span>
              <span class="badge status-badge" :class="anime?.status">
                {{ getStatusText(anime?.status) }}
              </span>
            </div>
          </div>

          <div class="anime-rating" v-if="anime?.score">
            <div class="rating-stars">
              <svg v-for="i in 5" :key="i" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </div>
            <span class="rating-value">{{ anime.score.toFixed(1) }}</span>
          </div>

          <p class="anime-description">{{ anime?.description || 'Описание отсутствует' }}</p>
        </div>

        <!-- Озвучки -->
        <div class="translations-section">
          <div class="section-header">
            <h3>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
              Озвучки
            </h3>
            <!-- <button @click="showAddDubModal = true" class="btn-outline-sm">
              + Добавить
            </button> -->
          </div>

          <div v-if="loadingTranslations" class="loading-row">
            <div class="spinner-sm"></div>
            <p>Загрузка озвучек...</p>
          </div>
          <div v-else-if="translations.length > 0" class="translations-list">
            <div
              v-for="translation in translations"
              :key="translation.id"
              class="translation-item"
              :class="{ active: selectedTranslationId === translation.id, 'custom-dub': translation.is_custom }"
              @click="selectTranslation(translation)"
            >
              <div class="translation-left">
                <div class="translation-avatar">
                  <img v-if="getTranslationAvatar(translation)" :src="getTranslationAvatar(translation)" :alt="translation.name">
                  <span v-else>{{ getTranslationInitials(translation.name) }}</span>
                </div>
                <div class="translation-info">
                  <span class="translation-name">{{ translation.name }}</span>
                  <span class="translation-meta">
                    <span class="t-tag">{{ getTranslationType(translation.type) }}</span>
                    <span v-if="translation.quality" class="t-tag">{{ translation.quality }}</span>
                    <span v-if="translation.is_custom" class="t-tag custom">Пользовательская</span>
                  </span>
                </div>
              </div>
              <svg v-if="selectedTranslationId === translation.id" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="3">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
          </div>
          <div v-else class="no-translations">
            <span> <SakuraIcon name="mic" /> </span>
            <p>Озвучки недоступны</p>
            <!-- <button @click="showAddDubModal = true" class="btn-primary-sm">Добавить первую</button> -->
          </div>
        </div>

      </div>

      <!-- ══════════════════════════════════════════════
           ПРАВАЯ КОЛОНКА: постер + кнопка + серии + жанры
      ══════════════════════════════════════════════ -->
      <div class="right-column">

        <!-- Постер аниме - ПЕРВЫЙ ЭЛЕМЕНТ -->
        <div v-if="posterSrc" class="poster-card">
          <div class="poster-image-wrapper">
            <img
              :src="posterSrc" 
              :alt="anime?.title_ru || anime?.title_en"
              class="anime-poster-img"
              @error="(e) => ((e.target as HTMLImageElement).style.display='none')"
            />
            <div v-if="!posterSrc" class="poster-placeholder">
              <SakuraIcon name="play" />
            </div>
          </div>
        </div>

        <!-- Кнопка «Подробнее» - сразу после постера -->
        <router-link
          :to="`/anime/${anime?.id}`"
          class="more-info-btn"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          <span>Подробнее об аниме</span>
        </router-link>

        <!-- Серии + прогресс -->
        <div v-if="anime?.episodes" class="episodes-card">
          <div class="ec-header">
            <h3>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="7" width="20" height="15" rx="2"/>
                <polyline points="17 2 12 7 7 2"/>
              </svg>
              Серии
            </h3>
            <button class="btn-sync-sm" @click="showSyncModal = true"> <SakuraIcon name="settings" /> </button>
          </div>

          <EpisodeList
            :total-episodes="anime.episodes"
            :current-episode="currentEpisode"
            :episodes="epEpisodes"
            :watched-count="epWatchedCount"
            :progress-percent="epPercent"
            :next-episode="epNextEpisode"
            @select-episode="onSelectEpisodeFromList"
            @mark-watched="onMarkWatched"
            @undo-mark="onUndoMark"
            @skip-episode="onSkipEpisode"
            @open-sync="showSyncModal = true"
          />
        </div>

        <!-- Жанры -->
        <div v-if="anime?.genres && anime.genres.length > 0" class="genres-card">
          <h3>Жанры</h3>
          <div class="genres-list">
            <RouterLink
              v-for="genre in anime.genres"
              :key="typeof genre === 'object' ? genre.id : genre"
              :to="getGenreLink(genre)"
              class="genre-tag"
            >{{ typeof genre === 'object' ? genre.name : genre }}</RouterLink>
          </div>
        </div>

        <!-- Действия -->
        <div class="actions-card">
          <button 
            @click="toggleFavorite" 
            class="action-btn"
            :class="{ 'is-favorite': isInFavorites, 'is-loading': favoriteLoading }"
            :disabled="favoriteLoading"
          >
            <span v-if="favoriteLoading" class="action-spinner"></span>
            <span v-else-if="isInFavorites" class="action-icon-filled"> <SakuraIcon name="heart" /> </span>
            <span v-else class="action-icon">♡</span>
            <span class="action-label">{{ isInFavorites ? 'В избранном' : 'В избранное' }}</span>
          </button>
          <button @click="shareAnime" class="action-btn">
            <span class="action-icon">↗</span>
            <span class="action-label">Поделиться</span>
          </button>
        </div>

      </div>
    </div>

    <!-- Карусель частей франшизы -->
    <div 
      v-if="franchise && franchise.entries?.length > 0" 
      class="franchise-carousel-section"
      ref="franchiseSectionRef"
      id="franchise-section"
    >
      <Carousel
        :title="franchise.name || 'Франшиза'"
        :items-count="franchise.entries.length"
        :scroll-step="4"
      >
        <a
          v-for="entry in franchise.entries"
          :key="entry.id"
          :href="`/anime/${entry.id}/watch`"
          class="franchise-carousel-item"
          :class="{ active: entry.id === anime?.id }"
        >
          <div class="fci-poster">
            <img
              v-if="entry.poster_image_url"
              :src="getMediaUrl(entry.poster_image_url) || entry.poster_image_url"
              :alt="entry.title_ru || entry.title_en"
            />
            <div v-else class="fci-poster-placeholder"> <SakuraIcon name="play" /> </div>
          </div>
          <div class="fci-info">
            <span class="fci-title">{{ entry.title_ru || entry.title_en }}</span>
            <span class="fci-meta">
              <span v-if="entry.year" class="fci-year">{{ entry.year }}</span>
              <span v-if="entry.kind" class="fci-kind">{{ getKindLabel(entry.kind) }}</span>
            </span>
          </div>
          <div v-if="entry.id === anime?.id" class="fci-current-badge">Сейчас смотришь</div>
        </a>
      </Carousel>
    </div>

    <!-- Кнопка прокрутки к франшизе -->
    <Transition name="fade">
      <button 
        v-if="showFranchiseScrollButton"
        class="scroll-to-franchise-btn"
        @click="scrollToFranchise"
        title="Перейти к другим частям франшизы"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M12 5v14M19 12l-7 7-7-7"/>
        </svg>
      </button>
    </Transition>

    <!-- Модалки -->
    <AddCustomDubModal
      :show="showAddDubModal"
      :anime-id="anime?.id"
      :anime-title="anime?.title_ru || anime?.title_en"
      @close="showAddDubModal = false"
      @dub-added="onDubAdded"
    />

    <!-- Плавающий мини-плеер -->
    <FloatingPlayer
      :visible="floatingPlayerVisible"
      :anime-id="anime?.id"
      :anime-title="anime?.title_ru || anime?.title_en || 'Аниме'"
      :episode="currentEpisode"
      :season="currentSeason"
      :player-link="kodikLink"
      :translation-id="selectedTranslation?.id ?? null"
      :start-time="mainPlayerTimeAtFloatOpen"
      @close="handleFloatingPlayerClose"
      @time-update="handleFloatingPlayerTimeUpdate"
      @duration-update="handleFloatingPlayerDurationUpdate"
    />

    <EpisodeProgressModal
      :show="showSyncModal"
      :anime-title="anime?.title_ru || anime?.title_en || ''"
      :total-episodes="anime?.episodes || 0"
      :current-episode="epNextEpisode ?? 1"
      @close="showSyncModal = false"
      @apply="handleSyncApply"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'
import { normalizeKodikPlayerLink } from '@/config/kodik'
import KodikPlayer from '@/components/Players/KodikPlayer.vue'
import CustomVideoPlayer from '@/components/Players/CustomVideoPlayer.vue'
import FloatingPlayer from '@/components/Players/FloatingPlayer.vue'
import AddCustomDubModal from '@/components/modal/anime/AddCustomDubModal.vue'
import EpisodeProgressModal from '@/components/modal/anime/EpisodeProgressModal.vue'
import EpisodeList from '@/components/Cards/EpisodeList.vue'
import Carousel from '@/components/common/Carousel.vue'
import { getTranslationAvatarUrl } from '@/utils/translationAvatars'
import { useEpisodeProgress } from '@/composables/useEpisodeProgress'
import { useToast } from '@/composables/useToast'
import { useAnimeTab } from '@/composables/useAnimeTab'
import { useThemeDownloader } from '@/composables/useThemeDownloader'
import type { CustomSegmentOpts } from '@/composables/useThemeDownloader'
import { getMediaUrl } from '@/api/client'

const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()
const { downloadTheme, downloadSegment } = useThemeDownloader()

// Отдельные состояния для видео и аудио
const openingVideoState = ref({ loading: false, progress: 0, error: '', done: false })
const openingAudioState = ref({ loading: false, progress: 0, error: '', done: false })
const endingVideoState = ref({ loading: false, progress: 0, error: '', done: false })
const endingAudioState = ref({ loading: false, progress: 0, error: '', done: false })

// Состояние для кастомного клипа
const customState = ref({ loading: false, progress: 0, error: '', done: false })

// ── Трекер активной вкладки («Сейчас смотрят») ──
// animeId может быть недоступен при первом рендере, поэтому берём из роута
const _routeAnimeId = Number(route.params.id) || 0
let animeTab: ReturnType<typeof useAnimeTab> | null = null
if (_routeAnimeId) {
  animeTab = useAnimeTab(_routeAnimeId)
}

// Состояние скачивания серии целиком
const episodeDownloadState = ref({ loading: false, progress: 0, error: '', done: false })

// ── Мини-плеер (FloatingPlayer) ─────────────────────────────────
const floatingPlayerVisible = ref(false)
// Время в основном плеере на момент открытия мини-плеера
const mainPlayerTimeAtFloatOpen = ref(0)
// Флаг: был ли мини-плеер открыт
const wasFloatingPlayerOpened = ref(false)

const launchFloatingPlayer = () => {
  mainPlayerTimeAtFloatOpen.value = currentTime.value
  wasFloatingPlayerOpened.value = true
  floatingPlayerVisible.value = true
  if (kodikPlayer.value) {
    kodikPlayer.value.pause()
  }
}

// Отправляем время обратно в основной плеер при обновлении в мини-плеере
const handleFloatingPlayerTimeUpdate = (time: number) => {
  // Обновляем currentTime в реальном времени только если мини-плеер открыт
  if (floatingPlayerVisible.value) {
    currentTime.value = time
  }
}

// Обработка закрытия мини-плеера с временем
const handleFloatingPlayerClose = (floatTime?: number) => {
  floatingPlayerVisible.value = false
  
  // Если было время от мини-плеера - обновляем основной плеер
  if (floatTime !== undefined && floatTime > 0) {
    // Обновляем currentTime
    currentTime.value = floatTime
    // Перематываем основной плеер
    if (kodikPlayer.value) {
      kodikPlayer.value.seek(floatTime)
    }
  }
  
  wasFloatingPlayerOpened.value = false
}

// Обработка обновления длительности из мини-плеера
const handleFloatingPlayerDurationUpdate = (dur: number) => {
  duration.value = dur
}

// Быстрая скачка опенинга
const handleDownloadOpening = (format: 'video' | 'audio' = 'video') => {
  if (!anime.value?.id) return
  const state = format === 'video' ? openingVideoState : openingAudioState
  if (state.value.loading) return

  downloadTheme({
    animeId: anime.value.id,
    kind: 'opening',
    episode: currentEpisode.value,
    season: currentSeason.value,
    translationId: selectedTranslation.value?.id,
    animeTitle: anime.value?.title_ru || anime.value?.title_en || '',
    format,
    state,
  })
}

const handleDownloadEnding = (format: 'video' | 'audio' = 'video') => {
  if (!anime.value?.id) return
  const state = format === 'video' ? endingVideoState : endingAudioState
  if (state.value.loading) return

  downloadTheme({
    animeId: anime.value.id,
    kind: 'ending',
    episode: currentEpisode.value,
    season: currentSeason.value,
    translationId: selectedTranslation.value?.id,
    animeTitle: anime.value?.title_ru || anime.value?.title_en || '',
    format,
    state,
  })
}



// Скачка серии целиком (0 — конец)
const handleDownloadEpisode = async () => {
  if (!anime.value?.id || episodeDownloadState.value.loading) return
  episodeDownloadState.value = { loading: true, progress: 10, error: '', done: false }
  try {
    const { id } = anime.value
    const params: Record<string, string> = {
      episode: String(currentEpisode.value),
      season:  String(currentSeason.value),
      start:   '0',
      end:     '99999',
      label:   `Episode ${currentEpisode.value}`,
    }
    if (selectedTranslation.value?.id) params.translation_id = String(selectedTranslation.value.id)

    const response = await apiClient.get(`/anime/${id}/clip/`, {
      params,
      responseType: 'blob',
      timeout: 0, // без таймаута — серия может скачиваться долго
      onDownloadProgress: (evt) => {
        if (evt.total && evt.total > 0) {
          episodeDownloadState.value.progress = 10 + Math.round((evt.loaded / evt.total) * 85)
        } else {
          episodeDownloadState.value.progress = Math.min(90, episodeDownloadState.value.progress + 3)
        }
      },
    })

    episodeDownloadState.value.progress = 97
    const animeTitle = anime.value?.title_ru || anime.value?.title_en || 'anime'
    const label = `Episode ${currentEpisode.value}`
    const disposition = response.headers['content-disposition'] || ''
    let filename = `${animeTitle} - ${label}.mp4`
    const fnMatch = disposition.match(/filename\*=UTF-8''([^;\n]+)/) || disposition.match(/filename="?([^";\n]+)"?/)
    if (fnMatch) filename = decodeURIComponent(fnMatch[1])

    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url; a.download = filename
    document.body.appendChild(a); a.click(); document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(url), 5000)

    episodeDownloadState.value = { loading: false, progress: 100, error: '', done: true }
    setTimeout(() => { episodeDownloadState.value.done = false }, 3000)
  } catch (err: any) {
    let message = err?.message || 'Ошибка'
    if (err?.response?.data instanceof Blob) {
      try { message = JSON.parse(await err.response.data.text()).error || message } catch { /**/ }
    }
    episodeDownloadState.value = { loading: false, progress: 0, error: message, done: false }
  }
}

// ── Скачивание произвольного отрезка ─────────────────────────────
const showClipModal   = ref(false)
const clipStartInput  = ref('')   // строка "mm:ss" или секунды
const clipEndInput    = ref('')
const clipLabel       = ref('clip')

const parseTimeInput = (val: string): number => {
  const v = val.trim()
  if (/^\d+$/.test(v)) return parseInt(v, 10)
  const parts = v.split(':').map(Number)
  if (parts.length === 2) return (parts[0] || 0) * 60 + (parts[1] || 0)
  if (parts.length === 3) return (parts[0] || 0) * 3600 + (parts[1] || 0) * 60 + (parts[2] || 0)
  return 0
}

const formatSec = (s: number) => {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

const setClipFromCurrent = () => {
  clipStartInput.value = formatSec(Math.max(0, currentTime.value - 2))
  clipEndInput.value   = formatSec(Math.min(duration.value || 9999, currentTime.value + 88))
}

const handleDownloadSegment = () => {
  if (!anime.value?.id) return
  const start = parseTimeInput(clipStartInput.value)
  const end   = parseTimeInput(clipEndInput.value)
  if (end <= start) {
    customState.value.error = 'Конец должен быть позже начала'
    return
  }
  customState.value.error = ''
  downloadSegment({
    animeId: anime.value.id,
    episode: currentEpisode.value,
    season: currentSeason.value,
    translationId: selectedTranslation.value?.id,
    startSec: start,
    stopSec: end,
    label: clipLabel.value || 'clip',
    animeTitle: anime.value?.title_ru || anime.value?.title_en || '',
    state: customState,
  })
}

// ── Episode Progress ──────────────────────────────────────────────
let epProgress: ReturnType<typeof useEpisodeProgress> | null = null
const showSyncModal   = ref(false)
const epWatchedCount  = ref(0)
const epPercent       = ref(0)
const epNextEpisode   = ref<number | null>(null)
const epEpisodes      = ref<Map<number, any>>(new Map())
const epTotalEpisodes = ref(0)

const epIsWatched = (num: number) => epEpisodes.value.get(num)?.status === 'watched'

// ── Основное состояние ───────────────────────────────────────────
const anime              = ref<any>(null)
const franchise          = ref<any>(null)  // Данные о франшизе
const kodikLink          = ref('')
const customVideoUrl     = ref('')
const loading            = ref(true)
const loadingTranslations = ref(false)
const error              = ref('')
const autoplay           = ref(false)
const useCustomPlayer    = ref(false)

const currentSeason      = ref(1)
const currentEpisode     = ref(1)
const selectedTranslation = ref<any>(null)
const translations       = ref<any[]>([])
const showAddDubModal    = ref(false)

const currentTime = ref(0)
const duration    = ref(0)
const isPlaying   = ref(false)

const playerContainer = ref<HTMLElement | null>(null)
const kodikPlayer     = ref<InstanceType<typeof KodikPlayer> | null>(null)

// Старая система прогресса (localStorage fallback)
const watchProgress       = ref<Record<number, number>>({})
const isInLibrary         = ref(false)
const libraryItemId       = ref<number | null>(null)
const currentEpisodeData  = ref<any>(null)
const openingStartTime    = ref<number | null>(null)
const endingStartTime     = ref<number | null>(null)
const addedToLibrary      = ref(false)
const episodeMarkedWatched = ref(false)

// Диалог "Пропустить серию?"

// ── Избранное ─────────────────────────────────────────────────
import playlistsApi from '@/api/playlists'

const isInFavorites = ref(false)
const favoriteLoading = ref(false)

const checkIsFavorite = async () => {
  if (!authStore.isAuthenticated || !anime.value?.id) return
  try {
    const response = await playlistsApi.checkAnimeInFavorites(anime.value.id)
    isInFavorites.value = response.data.is_favorite
  } catch (e) {
    console.error('Ошибка проверки избранного:', e)
  }
}

const toggleFavorite = async () => {
  if (!authStore.isAuthenticated) {
    toast.info('Войдите, чтобы добавлять в избранное', { duration: 3000 })
    return
  }
  if (!anime.value?.id) return
  
  favoriteLoading.value = true
  try {
    if (isInFavorites.value) {
      // Удалить из избранного
      await playlistsApi.removeFromFavorites(anime.value.id)
      isInFavorites.value = false
      toast.success('Удалено из избранного')
    } else {
      // Добавить в избранное
      await playlistsApi.addToFavorites(anime.value.id)
      isInFavorites.value = true
      toast.success('Добавлено в избранное')
    }
  } catch (err: any) {
    console.error('Ошибка избранного:', err)
    toast.error('Не удалось обновить избранное')
  } finally {
    favoriteLoading.value = false
  }
}

const getGenreLink = (genre: any) => {
  const genreName = typeof genre === 'object' ? genre.name : genre
  const slug = genreName.toLowerCase().replace(/[^a-zа-яё0-9]/g, '-').replace(/-+/g, '-')
  return `/anime?genres=${encodeURIComponent(slug)}`
}

// ── Кнопка прокрутки к франшизе ───────────────────────────────
const franchiseSectionRef = ref<HTMLElement | null>(null)
const isNearTop = ref(true)

const checkScrollPosition = () => {
  // Всегда показывать кнопку вверху страницы (isNearTop = true)
  // Когда пользователь прокрутит вниз (franchise section будет видна), кнопка скроется
  // Если элемент не найден - считаем что мы вверху
  if (!franchiseSectionRef.value) {
    isNearTop.value = true
    return
  }
  const rect = franchiseSectionRef.value.getBoundingClientRect()
  // Показываем кнопку если верх секции франшизы ниже середины экрана (т.е. нужно прокрутить)
  isNearTop.value = rect.top > window.innerHeight * 0.5
}

const scrollToFranchise = () => {
  franchiseSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// Проверяем, показывать ли кнопку (если есть franchise_id)
const showFranchiseScrollButton = computed(() => {
  // Показываем если есть franchise_id и страница вверху
  return anime.value?.franchise_id && isNearTop.value
})

// ── Вычисляемые ─────────────────────────────────────────────────
const episodeProgress = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const selectedTranslationId = computed(() => selectedTranslation.value?.id?.toString() || '0')

/**
 * Постер — приоритет: локальный файл (poster_image_url / poster) → внешний URL (poster_url).
 * poster_image_url уже возвращает локальный путь /media/anime_posters/... если файл есть.
 */
const posterSrc = computed((): string | null => {
  if (!anime.value) return null
  // poster_image_url — серверный метод: сначала смотрит на локальный файл, потом poster_url
  const local = anime.value.poster_image_url || anime.value.poster
  const result = local ? getMediaUrl(local) || null : anime.value.poster_url || null
  console.log('[AnimeWatch] posterSrc:', {
    poster_image_url: anime.value.poster_image_url,
    poster: anime.value.poster,
    poster_url: anime.value.poster_url,
    result
  })
  return result
})

// ── Хелперы ──────────────────────────────────────────────────────
const syncEpRefs = () => {
  if (!epProgress) return
  epWatchedCount.value = epProgress.watchedCount.value
  epPercent.value      = epProgress.progressPercent.value
  epNextEpisode.value  = epProgress.nextEpisodeToWatch.value
  epEpisodes.value     = new Map(epProgress.episodes.value)
}

// ── Франшиза ───────────────────────────────────────────────────
const loadFranchise = async (franchiseId: number) => {
  try {
    const response = await apiClient.get(`/anime/franchises/${franchiseId}/`)
    franchise.value = {
      id: response.data.id,
      name: response.data.name,
      entries: (response.data.entries || []).sort(
        (a: any, b: any) => (a.franchise_order || 0) - (b.franchise_order || 0)
      )
    }
  } catch (e) {
    console.error('Ошибка загрузки франшизы:', e)
    franchise.value = null
  }
}

const getKindLabel = (kind: string) => ({
  tv: 'TV', movie: 'Фильм', ova: 'OVA', ona: 'ONA', special: 'Спешл', music: 'Клип'
}[kind] || kind.toUpperCase())

const formatTime = (seconds: number) => {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`
  return `${m}:${s.toString().padStart(2,'0')}`
}

const getKindText = (kind: string) => ({
  tv:'ТВ', movie:'Фильм', ova:'OVA', ona:'ONA', special:'Спецвыпуск', music:'Музыка'
}[kind] || kind)

const getStatusText = (status: string) => ({
  ongoing:'Онгоинг', finished:'Завершено', announced:'Анонс', canceled:'Отменено'
}[status] || status)

const getTranslationType = (type: string) => ({
  voice:'Озвучка', subtitles:'Субтитры', raw:'Оригинал'
}[type] || type)

const getTranslationInitials = (name: string) => {
  if (!name) return '?'
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

const getTranslationAvatar = (translation: any): string | undefined => {
  if (translation.logo) return translation.logo
  return getTranslationAvatarUrl(translation.name)
}

// ── Загрузка аниме ───────────────────────────────────────────────
const loadAnime = async () => {
  try {
    loading.value = true
    error.value = ''

    const animeId = route.params.id
    const response = await apiClient.get(`/anime/${animeId}/`)
    anime.value = response.data

    // Отладка: выводим franchise_id в консоль
    console.log('Anime loaded, franchise_id:', anime.value?.franchise_id)

    const episodeFromQuery = route.query.episode
    if (episodeFromQuery) {
      const ep = parseInt(episodeFromQuery as string, 10)
      if (!isNaN(ep) && ep >= 1) {
        currentEpisode.value = ep
        autoplay.value = true
      }
    }

    await checkLibraryStatus()
    await checkIsFavorite()
    await loadTranslations()
    await loadKodikPlayer()
    loadWatchProgress()

    // Инициализируем систему прогресса серий
    if (anime.value?.id) {
      epProgress = useEpisodeProgress(anime.value.id)
      epTotalEpisodes.value = anime.value.episodes || 0
      await epProgress.loadProgress()
      syncEpRefs()

      // Синхронизация: если в библиотеке статус "completed" - отмечаем все эпизоды
      if (authStore.isAuthenticated && isInLibrary.value && libraryItemId.value) {
        await syncCompletedStatusFromLibrary()
      }

      // Загружаем франшизу, если есть franchise_id
      if (anime.value.franchise_id) {
        await loadFranchise(anime.value.franchise_id)
      }

      // Тост "Вы смотрели это аниме ранее?" если нет истории
      if (authStore.isAuthenticated && epProgress.watchedCount.value === 0 && !route.query.episode) {
        setTimeout(() => showFirstVisitToast(), 800)
      }
    }
  } catch (err: any) {
    console.error('Ошибка загрузки аниме:', err)
    error.value = 'Не удалось загрузить аниме'
  } finally {
    loading.value = false
  }
}

// ── Тост первого посещения ───────────────────────────────────────
const showFirstVisitToast = () => {
  toast.info('Вы смотрели это аниме ранее?', {
    duration: 8000,
    action: {
      label: 'Настроить прогресс',
      handler: () => { showSyncModal.value = true },
    },
  })
}

// ── Библиотека ───────────────────────────────────────────────────
const checkLibraryStatus = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const response = await apiClient.get('/users/library/')
    const items: any[] = response.data.results ?? response.data
    if (!Array.isArray(items)) return

    const item = items.find((i: any) => {
      const aid = typeof i.anime === 'object' ? i.anime?.id : i.anime
      return aid === anime.value?.id
    })

    if (item) {
      isInLibrary.value = true
      libraryItemId.value = item.id
      addedToLibrary.value = true
      
      const savedEp = item.current_episode ?? 0
      if (savedEp > 0 && !route.query.episode) {
        currentEpisode.value = savedEp
      }
    } else {
      isInLibrary.value = false
      libraryItemId.value = null
    }
  } catch { isInLibrary.value = false }
}

// Синхронизация прогресса: если статус в библиотеке "completed" - отмечаем все эпизоды
const syncCompletedStatusFromLibrary = async () => {
  if (!libraryItemId.value || !epProgress) return
  
  try {
    const response = await apiClient.get(`/users/library/${libraryItemId.value}/`)
    const item = response.data
    
    console.log('[AnimeWatch] Статус из библиотеки:', item.status, 'current_ep:', item.current_episode, 'episodes_watched:', item.episodes_watched, 'total:', anime.value?.episodes)
    
    const totalEps = anime.value?.episodes || 0
    
    // Синхронизируем если:
    // 1. Статус completed ИЛИ
    // 2. episodes_watched >= totalEpisodes (все эпизоды просмотрены)
    const shouldSync = item.status === 'completed' || 
                       (item.episodes_watched && totalEps && item.episodes_watched >= totalEps)
    
    if (shouldSync && totalEps > 0) {
      console.log('[AnimeWatch] Синхронизация прогресса...')
      
      // Используем bulkSyncUpTo для эффективной синхронизации
      await epProgress.bulkSyncUpTo(totalEps)
      syncEpRefs()
      console.log(`[AnimeWatch] Отмечено ${totalEps} эпизодов как просмотренные`)
    }
  } catch (e) {
    console.warn('[AnimeWatch] Ошибка синхронизации completed статуса:', e)
  }
}

const addToLibraryAutomatically = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const response = await apiClient.post('/users/library/', { anime: anime.value?.id, status: 'started' })
    isInLibrary.value = true
    libraryItemId.value = response.data.id
    await updateLibraryProgress()
  } catch (err: any) {
    if (err.response?.status === 409 || err.response?.status === 400) {
      await checkLibraryStatus()
      if (isInLibrary.value) await updateLibraryProgress()
    }
  }
}

const updateLibraryProgress = async () => {
  if (!libraryItemId.value) return
  try {
    const episodesWatched = Object.values(watchProgress.value).filter(p => p >= 85).length
    // Не меняем статус на 'started' - сохраняем текущий
    await apiClient.patch(`/users/library/${libraryItemId.value}/`, {
      current_episode: currentEpisode.value,
      episodes_watched: episodesWatched,
    })
  } catch { /* silent */ }
}

// ── Озвучки ──────────────────────────────────────────────────────

const loadTranslations = async () => {
  if (!anime.value?.id) return
  try {
    loadingTranslations.value = true
    const response = await apiClient.get(`/anime/${anime.value.id}/kodik_translations/`)
    const kodikTranslations = response.data.translations || []

    try {
      const customResponse = await apiClient.get(`/anime/${anime.value.id}/custom_dubs/`)
      const customDubs = customResponse.data.dubs || []
      translations.value = [
        ...kodikTranslations.map((t: any) => ({ ...t, is_custom: false })),
        ...customDubs.map((d: any) => ({ ...d, is_custom: true, type: 'voice' })),
      ]
    } catch {
      translations.value = kodikTranslations.map((t: any) => ({ ...t, is_custom: false }))
    }

    if (translations.value.length > 0) {
      selectedTranslation.value = translations.value[0]
      if (!selectedTranslation.value.is_custom && selectedTranslation.value.kodik_link) {
        kodikLink.value = normalizeKodikPlayerLink(selectedTranslation.value.kodik_link)
      }
    }
  } catch {
    translations.value = []
  } finally {
    loadingTranslations.value = false
  }
}

const loadKodikPlayer = async () => {
  if (!anime.value?.id) return
  try {
    const response = await apiClient.get(`/anime/${anime.value.id}/kodik_player/`)
    kodikLink.value = normalizeKodikPlayerLink(response.data.kodik_link)
    console.log('[AnimeWatch] Kodik player loaded:', kodikLink.value)
    if (response.data.last_episode) currentEpisode.value = 1
  } catch (err: any) {
    console.error('[AnimeWatch] Error loading kodik player:', err)
    if (err.response?.status === 404) error.value = 'Видео для этого аниме не найдено'
    else if (err.response?.status === 503) error.value = 'Сервис временно недоступен'
    else error.value = 'Не удалось загрузить плеер'
  }
}

const selectTranslation = async (translation: any) => {
  selectedTranslation.value = translation
  if (translation.is_custom) {
    useCustomPlayer.value = true
    try {
      const res = await apiClient.get(`/anime/${anime.value?.id}/custom_dubs/${translation.id}/video/`)
      customVideoUrl.value = res.data.video_url
    } catch { error.value = 'Не удалось загрузить видео' }
  } else {
    useCustomPlayer.value = false
    customVideoUrl.value = ''
    if (translation.kodik_link) kodikLink.value = normalizeKodikPlayerLink(translation.kodik_link)
  }
}

// ── Навигация по сериям ──────────────────────────────────────────
const selectEpisode = (episode: number) => {
  currentEpisode.value = episode
}

/**
 * Переход на серию из списка — проверяем, нужно ли спросить о пропуске
 */
const onSelectEpisodeFromList = (num: number) => {
  if (num === currentEpisode.value) return
  selectEpisode(num)
}


// ── События плеера ───────────────────────────────────────────────
const onPlayerReady = () => {
  loading.value = false
}

const onVideoStarted = () => { }
const onPlay  = () => {
  isPlaying.value = true
  animeTab?.setPlayerActive(true, currentEpisode.value)
}
const onPause = () => {
  isPlaying.value = false
  animeTab?.setPlayerActive(false, currentEpisode.value)
}

const triggerLibraryAdd = () => {
  if (addedToLibrary.value || isInLibrary.value) return
  addedToLibrary.value = true
  addToLibraryAutomatically()
}

const markEpisodeWatched = () => {
  if (episodeMarkedWatched.value) return
  episodeMarkedWatched.value = true
  watchProgress.value[currentEpisode.value] = 100
  saveWatchProgress()
  if (isInLibrary.value && libraryItemId.value) updateLibraryProgress()
  else addToLibraryAutomatically()
}

const onTimeUpdate = (time: number) => {
  currentTime.value = time
  if (duration.value <= 0) return

  const pct = (time / duration.value) * 100
  watchProgress.value[currentEpisode.value] = Math.min(pct, 100)

  // Добавляем в библиотеку после 30 сек
  if (!addedToLibrary.value && !isInLibrary.value && (openingStartTime.value !== null || time >= 30)) {
    triggerLibraryAdd()
  }

  // Засчитываем при эндинге
  if (endingStartTime.value !== null && !episodeMarkedWatched.value && time >= endingStartTime.value) {
    markEpisodeWatched()
    epProgress?.autoMarkWatched(currentEpisode.value).then(syncEpRefs)
  }

  // Засчитываем при 85%
  if (!episodeMarkedWatched.value && pct >= 85) {
    markEpisodeWatched()
    epProgress?.autoMarkWatched(currentEpisode.value).then(syncEpRefs)
  }

  // Сохраняем позицию каждые 10 сек
  if (Math.floor(time) % 10 === 0) {
    saveWatchProgress()
    if (isInLibrary.value && libraryItemId.value) updateLibraryProgress()
    epProgress?.updatePosition(currentEpisode.value, Math.floor(time), duration.value || undefined)
  }
}

const onDurationUpdate = (dur: number) => { duration.value = dur }

/**
 * Пользователь сменил озвучку прямо внутри плеера Kodik.
 * Синхронизируем selectedTranslation с тем, что выбрано в плеере,
 * чтобы при переключении серий передавать правильный only_translations.
 */
const onKodikTranslationChanged = (data: { id: number, title: string }) => {
  console.log('[AnimeWatchView] Kodik сообщил о смене озвучки:', data)

  // Ищем совпадение по числовому id
  const match = translations.value.find(
    (t: any) => Number(t.id) === Number(data.id)
  )

  if (match) {
    // Озвучка есть в нашем списке — просто выделяем её
    selectedTranslation.value = match
    console.log('[AnimeWatchView] Озвучка найдена в списке:', match.name)
  } else {
    // Озвучки нет в списке (например, kodik показал другую) — создаём временный объект
    // чтобы при следующем запросе только_translations передался корректно
    selectedTranslation.value = {
      id: data.id,
      name: data.title || `#${data.id}`,
      type: 'voice',
      is_custom: false,
      kodik_link: kodikLink.value,  // сохраняем текущую ссылку
    }
    console.log('[AnimeWatchView] Озвучка не найдена в списке, создан временный объект:', selectedTranslation.value)
  }
}

const onCurrentEpisode = (data: any) => {
  if (data.episode && data.episode !== currentEpisode.value) {
    currentEpisode.value = data.episode
    openingStartTime.value = null
    endingStartTime.value  = null
    episodeMarkedWatched.value = false
    addedToLibrary.value = isInLibrary.value
    // Уведомляем трекер о смене серии
    animeTab?.setEpisode(data.episode)
  }
  if (data.season) currentSeason.value = data.season
}

const onVideoEnded = () => {
  isPlaying.value = false
  markEpisodeWatched()
  epProgress?.autoMarkWatched(currentEpisode.value).then(syncEpRefs)
  if (currentEpisode.value < (anime.value?.episodes || 1)) {
    selectEpisode(currentEpisode.value + 1)
    autoplay.value = true
  }
}

const onSkipButton = (data: { title: string }) => {
  const title = data?.title?.toLowerCase() || ''
  const isOpening = title.includes('опенинг') || title.includes('opening') || title.includes('intro')
  const isEnding  = title.includes('эндинг') || title.includes('ending') || title.includes('outro') || title.includes('титры')

  if (isOpening && openingStartTime.value === null) {
    openingStartTime.value = currentTime.value
    triggerLibraryAdd()
  }
  if (isEnding && endingStartTime.value === null && currentTime.value > 0) {
    endingStartTime.value = currentTime.value
    markEpisodeWatched()
    epProgress?.autoMarkWatched(currentEpisode.value).then(syncEpRefs)
  }
}

const onPlayerError = (err: string) => { error.value = err }

// ── Прогресс (localStorage) ──────────────────────────────────────
const loadWatchProgress = () => {
  const animeId = anime.value?.id
  if (!animeId) return
  const saved = localStorage.getItem(`anime_progress_${animeId}`)
  if (saved) {
    try { watchProgress.value = JSON.parse(saved) } catch { /* ignore */ }
  }
}

const saveWatchProgress = async () => {
  localStorage.setItem(`anime_progress_${anime.value?.id}`, JSON.stringify(watchProgress.value))
  if (!anime.value?.id || !authStore.isAuthenticated) return
  try {
    if (isInLibrary.value && libraryItemId.value) await updateLibraryProgress()
  } catch { /* silent */ }
}

// ── Обработчики EpisodeList ──────────────────────────────────────
const handleSyncApply = async (payload: { mode: string; watchedUpTo?: number }) => {
  if (!epProgress) return
  if (payload.mode === 'new' || payload.mode === 'restart') {
    await epProgress.resetProgress()
  } else if (payload.mode === 'continue' && payload.watchedUpTo) {
    await epProgress.bulkSyncUpTo(payload.watchedUpTo)
    const next = payload.watchedUpTo + 1
    if (next <= (anime.value?.episodes || 1)) selectEpisode(next)
  }
  syncEpRefs()
}

const onMarkWatched = async (num: number) => {
  if (!epProgress) return
  await epProgress.markWatched(num)
  syncEpRefs()
}

const onUndoMark = async (num: number) => {
  if (!epProgress) return
  await epProgress.undoMark(num)
  syncEpRefs()
}

const onSkipEpisode = async (num: number) => {
  if (!epProgress) return
  await epProgress.skipEpisode(num)
  syncEpRefs()
}

// ── Прочие действия ──────────────────────────────────────────────
const retryLoad = () => loadKodikPlayer()

// handleDownloadTheme оставлен как заглушка (логика перенесена в handleDownloadSegment)

const shareAnime = () => {
  if (navigator.share) {
    navigator.share({ title: anime.value?.title_ru, url: window.location.href })
  } else {
    navigator.clipboard.writeText(window.location.href)
    toast.success('Ссылка скопирована!')
  }
}

const onDubAdded = () => {
  loadTranslations()
  showAddDubModal.value = false
}

// ── Горячие клавиши ──────────────────────────────────────────────
const handleKeyPress = (event: KeyboardEvent) => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return
  switch (event.code) {
    case 'ArrowLeft':
      event.preventDefault()
      if (currentEpisode.value > 1) selectEpisode(currentEpisode.value - 1)
      break
    case 'ArrowRight':
      event.preventDefault()
      if (currentEpisode.value < (anime.value?.episodes || 1)) selectEpisode(currentEpisode.value + 1)
      break
  }
}

// ── Lifecycle ────────────────────────────────────────────────────
onMounted(() => {
  loadAnime()
  document.addEventListener('keydown', handleKeyPress)
  window.addEventListener('scroll', checkScrollPosition)

  // Проверяем позицию скролла после загрузки
  setTimeout(checkScrollPosition, 500)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyPress)
  window.removeEventListener('scroll', checkScrollPosition)
  saveWatchProgress()
  const ro = (window as any)._playerRO
  if (ro) { ro.disconnect(); delete (window as any)._playerRO }
})

watch(() => route.params.id, () => { loadAnime() })
watch(libraryItemId, () => {
  // При изменении libraryItemId перезагружаем прогресс
  if (libraryItemId.value) checkLibraryStatus()
})
watch(selectedTranslation, (v) => {
  if (v && !v.is_custom && v.kodik_link) kodikLink.value = normalizeKodikPlayerLink(v.kodik_link)
})
</script>

<style scoped>
/* ════════════════════════════════════════════════════════
   LAYOUT
════════════════════════════════════════════════════════ */
.anime-watch-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
  color: #fff;
  padding: 1.5rem;
}

.watch-container {
  max-width: 1600px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 2rem;
}

.left-column  { display: flex; flex-direction: column; gap: 2rem; }
.right-column { display: flex; flex-direction: column; gap: 1.5rem; align-self: start; }

/* ════════════════════════════════════════════════════════
   ПЛЕЕР
════════════════════════════════════════════════════════ */
.player-wrapper {
  background: #000;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.player-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
}

.player-placeholder {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 100%; color: #a0a0a0;
}

.player-placeholder .spinner {
  width: 44px; height: 44px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

.error-icon, .no-video-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }

.btn-retry {
  margin-top: 0.75rem;
  padding: 0.6rem 1.25rem;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}


/* ════════════════════════════════════════════════════════
   ИНФО ПОД ПЛЕЕРОМ
════════════════════════════════════════════════════════ */
.anime-info-under { display: flex; flex-direction: column; gap: 1.25rem; }

/* Постер в описании */
.anime-poster-inline {
  display: flex;
  justify-content: center;
  margin: 1rem 0;
}

.poster-inline-image {
  max-width: 200px;
  width: 100%;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

/* Постер (общий стиль) */
.poster-image {
  width: 100%;
  height: auto;
  border-radius: 8px;
  display: block;
}

.anime-header { display: flex; flex-direction: column; gap: 0.6rem; }

.anime-title {
  font-size: 1.875rem;
  font-weight: 800;
  margin: 0;
  line-height: 1.2;
  background: linear-gradient(135deg, #fff 0%, #9ca3af 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.anime-badges { display: flex; flex-wrap: wrap; gap: 0.4rem; }

.badge {
  padding: 0.3rem 0.75rem;
  border-radius: 7px;
  font-size: 0.75rem;
  font-weight: 600;
}

.year-badge     { background: rgba(59,130,246,0.2); color: #3b82f6; }
.kind-badge     { background: rgba(139,92,246,0.2);  color: #a78bfa; }
.episodes-badge { background: rgba(34,197,94,0.2);   color: #22c55e; }
.status-badge   { background: rgba(251,191,36,0.2);  color: #fbbf24; }
.status-badge.ongoing  { background: rgba(34,197,94,0.2); color: #22c55e; }
.status-badge.finished { background: rgba(156,163,175,0.15); color: #9ca3af; }

.anime-rating { display: flex; align-items: center; gap: 0.75rem; }
.rating-stars { display: flex; gap: 0.2rem; color: #fbbf24; }
.rating-value { font-size: 1.375rem; font-weight: 800; color: #fbbf24; }

.anime-description { color: #9ca3af; line-height: 1.75; font-size: 0.95rem; }

/* ════════════════════════════════════════════════════════
   ОЗВУЧКИ
════════════════════════════════════════════════════════ */
.translations-section {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.375rem;
  border: 1px solid rgba(255,255,255,0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h3 {
  display: flex; align-items: center; gap: 0.4rem;
  margin: 0; font-size: 1rem; font-weight: 600;
}

.btn-outline-sm {
  padding: 0.35rem 0.875rem;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.05);
  color: #9ca3af;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all .2s;
}
.btn-outline-sm:hover { background: rgba(255,255,255,0.1); color: #fff; }

.loading-row { display: flex; align-items: center; gap: 0.75rem; padding: 1.5rem; color: #9ca3af; }

.spinner-sm {
  width: 20px; height: 20px;
  border: 2px solid rgba(255,255,255,0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.translations-list { display: flex; flex-direction: column; gap: 0.5rem; max-height: 440px; overflow-y: auto; }

.translation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 10px;
  cursor: pointer;
  transition: all .15s;
}
.translation-item:hover { background: rgba(255,255,255,0.06); }
.translation-item.active { background: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.35); }
.translation-item.custom-dub { background: rgba(139,92,246,0.08); border-color: rgba(139,92,246,0.25); }

.translation-left { display: flex; align-items: center; gap: 0.875rem; flex: 1; min-width: 0; }

.translation-avatar {
  width: 42px; height: 42px;
  border-radius: 9px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; font-weight: 700; color: #fff;
  overflow: hidden; flex-shrink: 0;
}
.translation-avatar img { width: 100%; height: 100%; object-fit: cover; }

.translation-info { display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; }
.translation-name { font-size: 0.9rem; font-weight: 600; color: #fff; }
.translation-meta { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; }

.t-tag {
  font-size: 0.7rem; color: #9ca3af;
  padding: 0.1rem 0.4rem;
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
}
.t-tag.custom { background: rgba(139,92,246,0.25); color: #a78bfa; }

.no-translations { text-align: center; padding: 2rem 1rem; color: #9ca3af; }
.no-translations span { font-size: 2.5rem; }
.no-translations p { margin: 0.5rem 0 1rem; }

.btn-primary-sm {
  padding: 0.5rem 1.25rem;
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
}

/* ════════════════════════════════════════════════════════
   ПРАВАЯ КОЛОНКА
════════════════════════════════════════════════════════ */

/* Серии */
.episodes-card {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.25rem;
  border: 1px solid rgba(255,255,255,0.06);
}

/* Кнопка «Подробнее» */
.more-info-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(59,130,246,0.15) 0%, rgba(139,92,246,0.15) 100%);
  border: 1px solid rgba(59,130,246,0.3);
  border-radius: 12px;
  color: #60a5fa;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s var(--ease-petal);
  margin-bottom: 1.5rem;
}

.more-info-btn:hover {
  background: linear-gradient(135deg, rgba(59,130,246,0.25) 0%, rgba(139,92,246,0.25) 100%);
  border-color: rgba(59,130,246,0.5);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59,130,246,0.2);
}

.more-info-btn svg {
  flex-shrink: 0;
}

.ec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.ec-header h3 {
  display: flex; align-items: center; gap: 0.4rem;
  margin: 0; font-size: 0.95rem; font-weight: 600;
}

.btn-sync-sm {
  width: 28px; height: 28px;
  border-radius: 7px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  color: #9ca3af;
  font-size: 0.85rem;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.btn-sync-sm:hover { background: rgba(255,255,255,0.1); color: #fff; }

/* Жанры */
.genres-card {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.25rem;
  border: 1px solid rgba(255,255,255,0.06);
}

.genres-card h3 {
  margin: 0 0 0.875rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.72rem;
}

.genres-list { display: flex; flex-wrap: wrap; gap: 0.4rem; }

.genre-tag {
  padding: 0.3rem 0.7rem;
  background: rgba(139,92,246,0.12);
  color: #a78bfa;
  border-radius: 7px;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid rgba(139,92,246,0.25);
  cursor: pointer;
  transition: all .15s;
  text-decoration: none;
  display: inline-block;
}
.genre-tag:hover { 
  background: rgba(139,92,246,0.22); 
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(139,92,246,0.2);
}

/* Постер в правой колонке */
.poster-card {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.25rem;
  border: 1px solid rgba(255,255,255,0.06);
  text-align: center;
}

.poster-image-wrapper {
  position: relative;
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(0,0,0,0.3);
}

.anime-poster-img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 10px;
  transition: transform 0.3s;
}

.anime-poster-img:hover {
  transform: scale(1.03);
}

.poster-placeholder {
  width: 100%;
  aspect-ratio: 2/3;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  color: #444;
  font-size: 3rem;
}

/* Действия */
.actions-card {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.25rem;
  border: 1px solid rgba(255,255,255,0.06);
  display: flex;
  flex-direction: row;
  gap: 1rem;
  justify-content: space-between;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
}

.action-btn:hover {
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.2);
}

.action-btn.is-favorite {
  background: rgba(251,191,36,0.15);
  border-color: #fbbf24;
  color: #fbbf24;
}

.action-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.action-icon-filled {
  font-size: 1.2rem;
  color: #fbbf24;
}

.action-icon {
  font-size: 1.2rem;
}

.action-label {
  font-size: 0.9rem;
}

/* ════════════════════════════════════════════════════════
   СКАЧАТЬ ТЕМУ (ОПЕНИНГ/ЭНДИНГ)
════════════════════════════════════════════════════════ */
/* ─── Быстрые кнопки скачивания под плеером ────────────────────── */
.quick-dl-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.625rem 0.875rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  margin-top: -0.5rem;
}

.qdl-group {
  display: flex;
  gap: 0.25rem;
}

.qdl-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 80px;
  justify-content: center;
}

.qdl-btn.qdl-secondary {
  background: var(--color-surface-3);
  border-color: var(--color-border-light);
}
.qdl-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #fff;
}
.qdl-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.qdl-btn.qdl-loading {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.3);
  color: #93c5fd;
}
.qdl-btn.qdl-done {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.3);
  color: #4ade80;
}
.qdl-btn.qdl-error {
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}
.qdl-btn.qdl-episode {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.25);
  color: #c4b5fd;
}
.qdl-btn.qdl-episode:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.18);
  border-color: rgba(139, 92, 246, 0.4);
  color: #ddd6fe;
}
.qdl-btn.qdl-clip-icon {
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}
.qdl-btn.qdl-clip-icon:hover:not(:disabled),
.qdl-btn.qdl-clip-icon.qdl-active {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.35);
  color: #fde68a;
}

/* Кнопка мини-плеера */
.qdl-btn.qdl-float-btn {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.25);
  color: #34d399;
  margin-left: auto; /* прижимаем к правом краю */
}
.qdl-btn.qdl-float-btn:hover:not(:disabled),
.qdl-btn.qdl-float-btn.qdl-active {
  background: rgba(16, 185, 129, 0.18);
  border-color: rgba(16, 185, 129, 0.45);
  color: #6ee7b7;
}

.qdl-label { flex: 1; min-width: 0; }

.qdl-spinner {
  width: 11px; height: 11px;
  border: 2px solid rgba(147, 197, 253, 0.3);
  border-top-color: #93c5fd;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

.qdl-bar {
  position: absolute;
  bottom: 0; left: 0;
  width: 100%; height: 2px;
  background: rgba(59, 130, 246, 0.15);
}
.qdl-fill {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s;
}

.qdl-err-text {
  width: 100%;
  margin: 0;
  font-size: 0.7rem;
  color: #f87171;
}

/* Форма фрагмента inline (inline версия под баром) */
.clip-form-inline {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem 0.875rem;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-top: none;
  border-radius: 0 0 10px 10px;
  margin-top: -2px;
}

/* ─── …старый theme-download-card (если ещё где-то есть) ─── */
.theme-download-card {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.125rem;
  border: 1px solid rgba(255,255,255,0.06);
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.tdc-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.1rem;
}

.tdc-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 1rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  color: #d1d5db;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all .2s;
  overflow: hidden;
  text-align: left;
}

.tdc-btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.1);
  color: #fff;
  transform: translateY(-1px);
}

.tdc-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.tdc-btn.tdc-loading {
  border-color: rgba(59,130,246,0.4);
  background: rgba(59,130,246,0.08);
  color: #93c5fd;
}

.tdc-btn.tdc-done {
  border-color: rgba(34,197,94,0.4);
  background: rgba(34,197,94,0.08);
  color: #86efac;
}

.tdc-btn.tdc-error {
  border-color: rgba(239,68,68,0.35);
  background: rgba(239,68,68,0.07);
  color: #fca5a5;
}

.tdc-label { flex: 1; }

.tdc-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.15);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

.tdc-progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(59,130,246,0.2);
}

.tdc-progress-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 0 2px 2px 0;
  transition: width 0.4s ease;
}

.tdc-error-text {
  font-size: 0.75rem;
  color: #f87171;
  margin: 0;
  padding: 0.25rem 0.5rem;
  background: rgba(239,68,68,0.07);
  border-radius: 6px;
  word-break: break-word;
}

.tdc-open-btn {
  width: 100%;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.7rem 1rem;
  background: rgba(59,130,246,0.1);
  border-color: rgba(59,130,246,0.25);
  color: #93c5fd;
}
.tdc-open-btn:hover:not(:disabled) {
  background: rgba(59,130,246,0.2);
  color: #bfdbfe;
}

/* Форма отрезка */
.clip-form {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.clip-times {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
}

.clip-time-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.clip-time-field label {
  font-size: 0.68rem;
  color: #6b7280;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.clip-time-input {
  width: 100%;
  padding: 0.5rem 0.625rem;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  color: #fff;
  font-size: 0.95rem;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  outline: none;
  text-align: center;
  transition: border-color .15s;
}
.clip-time-input:focus {
  border-color: rgba(59,130,246,0.5);
}
.clip-time-input:disabled {
  opacity: 0.5;
}

.clip-time-arrow {
  color: #4b5563;
  font-size: 1rem;
  padding-bottom: 0.4rem;
  flex-shrink: 0;
}

.clip-label-row {
  width: 100%;
}

.clip-label-input {
  width: 100%;
  padding: 0.4rem 0.625rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 7px;
  color: #9ca3af;
  font-size: 0.8rem;
  outline: none;
  transition: border-color .15s;
  box-sizing: border-box;
}
.clip-label-input:focus {
  border-color: rgba(255,255,255,0.18);
  color: #d1d5db;
}
.clip-label-input:disabled { opacity: 0.5; }

.clip-hint {
  font-size: 0.72rem;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.clip-hint b { color: #93c5fd; }

.clip-hint-btn {
  padding: 0.2rem 0.5rem;
  font-size: 0.7rem;
  background: rgba(59,130,246,0.12);
  border: 1px solid rgba(59,130,246,0.25);
  border-radius: 5px;
  color: #93c5fd;
  cursor: pointer;
  transition: all .15s;
}
.clip-hint-btn:hover:not(:disabled) {
  background: rgba(59,130,246,0.25);
}
.clip-hint-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.clip-actions {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.clip-download-btn {
  flex: 1;
  justify-content: center;
  padding: 0.65rem 0.875rem;
}

.clip-cancel-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.04);
  color: #6b7280;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all .15s;
  align-self: center;
}
.clip-cancel-btn:hover:not(:disabled) {
  background: rgba(239,68,68,0.12);
  color: #f87171;
  border-color: rgba(239,68,68,0.25);
}
.clip-cancel-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ════════════════════════════════════════════════════════
   ФРАНШИЗА
════════════════════════════════════════════════════════ */
.franchise-card {
  background: rgba(255,255,255,0.03);
  border-radius: 14px;
  padding: 1.25rem;
  border: 1px solid rgba(255,255,255,0.06);
  max-height: 400px;
  overflow-y: auto;
}

.franchise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.franchise-header h3 {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: #9ca3af;
}

.franchise-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.franchise-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 10px;
  text-decoration: none;
  color: inherit;
  transition: all .15s;
}

.franchise-item:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.1);
  transform: translateX(2px);
}

.franchise-item.active {
  background: rgba(59,130,246,0.1);
  border-color: rgba(59,130,246,0.3);
}

.fi-poster {
  width: 36px;
  height: 54px;
  border-radius: 5px;
  overflow: hidden;
  flex-shrink: 0;
  background: rgba(255,255,255,0.05);
  display: flex;
  align-items: center;
  justify-content: center;
}

.fi-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.fi-poster-placeholder {
  font-size: 1rem;
  opacity: 0.4;
}

.fi-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.fi-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #e5e7eb;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fi-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.fi-year {
  font-size: 0.7rem;
  color: #6b7280;
}

.fi-kind {
  font-size: 0.65rem;
  padding: 0.1rem 0.35rem;
  background: rgba(139,92,246,0.15);
  color: #a78bfa;
  border-radius: 4px;
}

.fi-current-icon {
  color: #3b82f6;
  flex-shrink: 0;
}

/* ════════════════════════════════════════════════════════
   АНИМАЦИИ
════════════════════════════════════════════════════════ */

/* ── Карусель частей франшизы ─────────────────────────── */
.franchise-carousel-section {
  width: 100%;
}

/* Показываем стрелки всегда, а не только при наведении */
.franchise-carousel-section :deep(.carousel-arrow) {
  opacity: 1 !important;
}

/* Фиксированные размеры карточек */
.franchise-carousel-section :deep(.carousel-card) {
  flex: 0 0 160px;
  width: 160px;
}

.franchise-carousel-item {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  transition: all .2s;
  position: relative;
  width: 160px;
  height: 260px;
  flex-shrink: 0;
}

.franchise-carousel-item:hover {
  transform: translateY(-4px);
  border-color: rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.06);
}

.franchise-carousel-item.active {
  border-color: rgba(59,130,246,0.5);
  background: rgba(59,130,246,0.1);
}

.fci-poster {
  width: 100%;
  height: 200px;
  background: rgba(255,255,255,0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.fci-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.fci-poster-placeholder {
  font-size: 2rem;
  opacity: 0.3;
}

.fci-info {
  padding: 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.fci-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #e5e7eb;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.fci-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.fci-year {
  font-size: 0.7rem;
  color: #6b7280;
}

.fci-kind {
  font-size: 0.6rem;
  padding: 0.1rem 0.35rem;
  background: rgba(139,92,246,0.15);
  color: #a78bfa;
  border-radius: 4px;
  font-weight: 500;
}

.fci-current-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 0.25rem 0.5rem;
  background: rgba(59,130,246,0.85);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 600;
  border-radius: 4px;
  backdrop-filter: blur(4px);
}

/* Адаптивность карусели франшизы */
@media (max-width: 767px) {
  .franchise-carousel-section :deep(.carousel-card) {
    flex: 0 0 120px !important;
    width: 120px !important;
  }
  
  .franchise-carousel-item {
    width: 120px !important;
    height: 200px !important;
  }
  
  .fci-poster {
    height: 150px !important;
  }
  
  .fci-info {
    padding: 0.4rem;
  }
  
  .fci-title {
    font-size: 0.7rem;
  }
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ── Кнопка прокрутки к франшизе ─────────────────────── */
.scroll-to-franchise-btn {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.85);
  border: 1px solid rgba(59, 130, 246, 0.5);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
  transition: all .2s;
}

.scroll-to-franchise-btn:hover {
  background: rgba(59, 130, 246, 1);
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(59, 130, 246, 0.5);
}

/* Адаптивность кнопки */
@media (max-width: 767px) {
  .scroll-to-franchise-btn {
    bottom: 16px;
    right: 16px;
    width: 44px;
    height: 44px;
  }
}

/* Transition для кнопки */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ════════════════════════════════════════════════════════
   АДАПТИВНОСТЬ
════════════════════════════════════════════════════════ */
@media (max-width: 1200px) {
  .watch-container { grid-template-columns: 1fr 300px; }
}

@media (max-width: 1024px) {
  .watch-container { grid-template-columns: 1fr; }

  .right-column {
    flex-direction: column;
    gap: 1rem;
  }

  .episodes-card { flex: 1; }
  .genres-card, .actions-card { flex: 1; }
}

@media (max-width: 768px) {
  .anime-watch-page { padding: 0.75rem; }
  .anime-title { font-size: 1.375rem; }
  .watch-container { gap: 1.25rem; }
  .translations-section, .episodes-card { padding: 1rem; }
}

@media (max-width: 480px) {
  .anime-title { font-size: 1.125rem; }
  .section-header { flex-direction: column; align-items: flex-start; gap: 0.75rem; }
  .btn-outline-sm { width: 100%; justify-content: center; }
}
</style>
