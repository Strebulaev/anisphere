<template>
  <div class="studio-detail-page">
    <!-- Загрузка -->
    <div v-if="isLoading" class="loading-hero">
      <div class="sk-banner"></div>
      <div class="sk-info-row">
        <div class="sk-logo-lg"></div>
        <div class="sk-text-block">
          <div class="sk-line wide"></div>
          <div class="sk-line mid"></div>
          <div class="sk-line short"></div>
        </div>
      </div>
    </div>

    <template v-else-if="studio">
      <!-- Hero Section -->
      <div class="studio-hero">
        <!-- Баннер -->
        <div
          class="hero-banner"
          :style="studio.banner_image_url ? `background-image: url('${studio.banner_image_url}')` : ''"
        >
          <div class="hero-banner-overlay"></div>

          <!-- Информация поверх баннера -->
          <div class="hero-content">
            <div class="hero-logo">
              <img
                v-if="studio.logo_image_url"
                :src="studio.logo_image_url"
                :alt="studio.name"
                class="hero-logo-img"
                @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
              />
              <div v-else class="hero-logo-placeholder">{{ studio.name.slice(0, 2) }}</div>
            </div>

            <div class="hero-text">
              <div class="hero-title-row">
                <h1 class="hero-title">{{ studio.name }}</h1>
                <span v-if="studio.is_verified" class="verified-badge">✓</span>
              </div>
              <div v-if="studio.name_jp" class="hero-title-jp">【{{ studio.name_jp }}】</div>

              <div class="hero-meta">
                <span class="hero-rating">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="#f59e0b" stroke="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                  {{ studio.average_rating?.toFixed(1) || '—' }}
                </span>
                <span v-if="studio.founded_year">📅 {{ studio.founded_year }}</span>
                <span>🌍 {{ studio.country }}</span>
                <span>🎬 {{ studio.total_anime }} аниме</span>
                <span v-if="studio.employees_count">🏢 {{ studio.employees_count }} сотрудников</span>
              </div>

              <div class="hero-actions">
                <button
                  @click="toggleSubscribe"
                  :class="['sub-btn', { subscribed: studio.is_subscribed }]"
                >
                  <span>{{ studio.is_subscribed ? '✓ Подписан' : '👍 Подписаться' }}</span>
                  <span class="sub-count">{{ formatCount(studio.subscribers_count) }}</span>
                </button>
                <a v-if="studio.website" :href="studio.website" target="_blank" class="hero-link-btn" title="Официальный сайт">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                </a>
                <a v-if="studio.twitter" :href="studio.twitter" target="_blank" class="hero-link-btn" title="Twitter/X">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </a>
              </div>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <nav class="studio-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            @click="activeTab = tab.value"
            :class="['tab-btn', { active: activeTab === tab.value }]"
          >{{ tab.label }}</button>
        </nav>
      </div>

      <!-- Content Area -->
      <div class="studio-body">
        <!-- Main Content -->
        <div class="studio-main">

          <!-- Вкладка: О СТУДИИ -->
          <div v-if="activeTab === 'about'" class="tab-content">
            <!-- Рейтинги -->
            <div class="content-card">
              <h2 class="card-title">📊 Рейтинг студии</h2>
              <div class="rating-overview">
                <div class="rating-big">{{ studio.average_rating?.toFixed(1) || '—' }}</div>
                <div class="rating-bars">
                  <div v-for="(val, star) in ratingDistribution" :key="star" class="rating-bar-row">
                    <span class="bar-label">{{ star }} ★</span>
                    <div class="bar-track">
                      <div class="bar-fill" :style="{ width: val + '%' }"></div>
                    </div>
                    <span class="bar-pct">{{ val }}%</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Жанры -->
            <div v-if="genreStats.length > 0" class="content-card">
              <h2 class="card-title">🎭 Жанровая статистика</h2>
              <div class="genre-bars">
                <div v-for="g in genreStats" :key="g.name" class="genre-row">
                  <span class="genre-name">{{ g.name }}</span>
                  <div class="genre-track">
                    <div class="genre-fill" :style="{ width: g.pct + '%' }"></div>
                  </div>
                  <span class="genre-pct">{{ g.pct }}%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Вкладка: РАБОТЫ -->
          <div v-if="activeTab === 'works'" class="tab-content">
            <div class="works-filters">
              <input
                v-model="worksSearch"
                @input="debouncedFetchWorks"
                placeholder="Поиск по работам..."
                class="works-search"
              />
              <select v-model="worksKind" @change="fetchWorks" class="works-select">
                <option value="">Все типы</option>
                <option value="tv">ТВ сериалы</option>
                <option value="movie">Фильмы</option>
                <option value="ova">OVA</option>
                <option value="ona">ONA</option>
              </select>
              <select v-model="worksOrdering" @change="fetchWorks" class="works-select">
                <option value="-anime_year">По году ↓</option>
                <option value="anime_year">По году ↑</option>
                <option value="-anime_score">По рейтингу ↓</option>
                <option value="anime_title">По названию</option>
              </select>
            </div>

            <!-- Группировка по годам -->
            <div v-if="worksByYear.length > 0">
              <div v-for="group in worksByYear" :key="group.year ?? 'unknown'" class="year-group">
                <h3 class="year-heading">{{ group.year || 'Неизвестный год' }}</h3>
                <div class="works-grid">
                  <component
                    v-for="work in group.items"
                    :key="work.kodik_id"
                    :is="work.anime_url ? 'router-link' : 'div'"
                    :to="work.anime_url || undefined"
                    class="work-card"
                    :class="{ 'work-card-linked': !!work.anime_url }"
                  >
                    <div class="work-poster">
                      <img
                        v-if="work.anime_poster"
                        :src="work.anime_poster"
                        :alt="work.anime_title"
                        class="poster-img"
                        @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
                      />
                      <div v-else class="poster-placeholder">{{ work.anime_title.slice(0, 2) }}</div>
                      <div class="work-kind-badge">{{ kindLabel(work.anime_kind) }}</div>
                      <div v-if="statusBadge(work.anime_status)" :class="['work-status-badge', `status-${work.anime_status}`]">
                        {{ statusBadge(work.anime_status) }}
                      </div>
                    </div>
                    <div class="work-info">
                      <div class="work-title">{{ work.anime_title }}</div>
                      <div v-if="work.anime_title_en" class="work-title-en">{{ work.anime_title_en }}</div>
                      <div class="work-meta">
                        <span class="work-score" v-if="work.anime_score">
                          <svg width="10" height="10" viewBox="0 0 24 24" fill="#f59e0b" stroke="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                          {{ work.anime_score.toFixed(1) }}
                        </span>
                        <span v-if="work.episodes_total" class="work-eps">
                          {{ work.episodes_total }} эп.
                        </span>
                      </div>
                    </div>
                  </component>
                </div>
              </div>
            </div>
            <div v-else-if="!worksLoading" class="empty-tab">Работы не найдены</div>
            <div v-if="worksLoading" class="works-grid">
              <div v-for="i in 10" :key="i" class="work-card-skeleton"></div>
            </div>
          </div>

          <!-- Вкладка: КОМАНДА -->
          <div v-if="activeTab === 'staff'" class="tab-content">
            <div v-if="staffLoading" class="loading-indicator">Загрузка...</div>
            <template v-else-if="staff.length > 0">
              <div v-for="role in staffGroups" :key="role.key" class="staff-group">
                <h2 class="card-title">{{ role.icon }} {{ role.label }}</h2>
                <div v-if="role.key === 'director' || role.key === 'founder' || role.key === 'ceo'" class="staff-cards">
                  <div v-for="member in role.members" :key="member.id" class="staff-card">
                    <div class="staff-photo">
                      <img v-if="member.photo_url" :src="member.photo_url" :alt="member.name" class="staff-photo-img" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
                      <div v-else class="staff-photo-placeholder">{{ member.name.slice(0, 1) }}</div>
                    </div>
                    <div class="staff-card-name">{{ member.name }}</div>
                    <div v-if="member.name_jp" class="staff-card-jp">{{ member.name_jp }}</div>
                    <div class="staff-card-works">{{ member.works_count }} работ</div>
                  </div>
                </div>
                <div v-else class="staff-list">
                  <div v-for="member in role.members" :key="member.id" class="staff-list-item">
                    <span class="staff-list-name">{{ member.name }}</span>
                    <span v-if="member.role_detail" class="staff-list-detail">({{ member.role_detail }})</span>
                    <span class="staff-list-works">— {{ member.works_count }} работ</span>
                  </div>
                </div>
              </div>
              <div v-if="staffGroups.length === 0" class="empty-tab">Команда не указана</div>
            </template>
            <div v-else class="empty-tab">Информация о команде пока не добавлена</div>
          </div>

          <!-- Вкладка: НОВОСТИ -->
          <div v-if="activeTab === 'news'" class="tab-content">
            <div v-if="newsLoading" class="loading-indicator">Загрузка...</div>
            <div v-else-if="news.length > 0" class="news-list">
              <div v-for="item in news" :key="item.id" class="news-card">
                <div class="news-date">📢 {{ formatDate(item.created_at) }}</div>
                <h3 class="news-title">{{ item.title }}</h3>
                <p class="news-preview">{{ item.content.slice(0, 200) }}{{ item.content.length > 200 ? '...' : '' }}</p>
                <div class="news-footer">
                  <span>💬 {{ item.comments_count }}</span>
                  <span>👍 {{ item.likes_count }}</span>
                </div>
              </div>
            </div>
            <div v-else class="empty-tab">Новостей пока нет</div>
          </div>

          <!-- Вкладка: ОБСУЖДЕНИЯ -->
          <div v-if="activeTab === 'discussions'" class="tab-content">
            <div class="discussions-toolbar">
              <button @click="showDiscussionForm = !showDiscussionForm" class="new-disc-btn">➕ Новая тема</button>
              <select v-model="discussionOrdering" @change="fetchDiscussions" class="works-select">
                <option value="-created_at">По дате</option>
                <option value="-likes_count">По лайкам</option>
                <option value="-replies_count">По ответам</option>
              </select>
            </div>

            <!-- Форма создания новой темы -->
            <div v-if="showDiscussionForm" class="disc-form">
              <input v-model="newDiscTitle" placeholder="Заголовок темы..." class="disc-input" />
              <textarea v-model="newDiscContent" placeholder="Содержание..." class="disc-textarea" rows="3"></textarea>
              <div class="disc-form-actions">
                <button @click="createDiscussion" class="submit-btn" :disabled="!newDiscTitle || !newDiscContent">Создать</button>
                <button @click="showDiscussionForm = false" class="cancel-btn">Отмена</button>
              </div>
            </div>

            <div v-if="discussionsLoading" class="loading-indicator">Загрузка...</div>
            <div v-else-if="discussions.length > 0" class="discussions-list">
              <div
                v-for="disc in discussions"
                :key="disc.id"
                class="discussion-card"
                :class="{ pinned: disc.is_pinned }"
              >
                <!-- Аватар автора -->
                <div class="disc-author-avatar">
                  <img
                    v-if="disc.author_avatar"
                    :src="disc.author_avatar"
                    :alt="disc.author_name"
                    class="disc-avatar-img"
                    @error="(e) => (e.target as HTMLImageElement).style.display='none'"
                  />
                  <div v-else class="disc-avatar-placeholder">{{ disc.author_name.slice(0, 1).toUpperCase() }}</div>
                </div>

                <div class="disc-body">
                  <div class="disc-header">
                    <span class="disc-author">@{{ disc.author_name }}</span>
                    <span v-if="disc.is_pinned" class="disc-pin-badge">📌 Закреплено</span>
                    <span class="disc-time">{{ timeAgo(disc.created_at) }}</span>
                  </div>
                  <h3 class="disc-title" @click="openDiscussion(disc)" style="cursor:pointer">{{ disc.title }}</h3>
                  <p v-if="disc.content" class="disc-preview">{{ disc.content.slice(0, 150) }}{{ disc.content.length > 150 ? '...' : '' }}</p>

                  <!-- Действия -->
                  <div class="disc-actions">
                    <button @click="likeDiscussion(disc)" :class="['disc-action-btn', { active: (disc as any).liked }]">
                      👍 <span>{{ disc.likes_count }}</span>
                    </button>
                    <button @click="dislikeDiscussion(disc)" :class="['disc-action-btn', { active: (disc as any).disliked }]">
                      👎 <span>{{ disc.dislikes_count }}</span>
                    </button>
                    <button @click="openDiscussion(disc)" class="disc-action-btn">
                      💬 <span>{{ disc.replies_count }} ответов</span>
                    </button>
                    <span v-if="disc.last_reply_at" class="disc-last-reply">
                      Посл. ответ {{ timeAgo(disc.last_reply_at) }}
                    </span>
                  </div>

                  <!-- Форма быстрого ответа -->
                  <div v-if="activeDiscussion?.id === disc.id" class="disc-reply-form">
                    <textarea
                      v-model="replyContent"
                      placeholder="Напишите ответ..."
                      class="disc-textarea"
                      rows="2"
                    ></textarea>
                    <div class="disc-form-actions">
                      <button @click="submitReply(disc)" class="submit-btn" :disabled="!replyContent.trim()">Ответить</button>
                      <button @click="activeDiscussion = null" class="cancel-btn">Отмена</button>
                    </div>
                    <!-- Ответы -->
                    <div v-if="discReplies[disc.id]?.length" class="disc-replies">
                      <div v-for="reply in discReplies[disc.id]" :key="reply.id" class="disc-reply-item">
                        <div class="disc-reply-avatar">
                          <img v-if="reply.author_avatar" :src="reply.author_avatar" :alt="reply.author_name" class="disc-avatar-img" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
                          <div v-else class="disc-avatar-placeholder">{{ reply.author_name.slice(0,1).toUpperCase() }}</div>
                        </div>
                        <div class="disc-reply-body">
                          <span class="disc-reply-author">@{{ reply.author_name }}</span>
                          <span class="disc-reply-time">{{ timeAgo(reply.created_at) }}</span>
                          <p class="disc-reply-text">{{ reply.content }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-tab">Обсуждений пока нет. Начните первым!</div>
          </div>

          <!-- Вкладка: ОТЗЫВЫ -->
          <div v-if="activeTab === 'reviews'" class="tab-content">
            <div class="reviews-header">
              <div class="review-overall">
                <span class="review-score">{{ studio.average_rating?.toFixed(1) || '—' }}</span>
                <div class="stars-lg">
                  <span v-for="s in 5" :key="s" class="star-lg" :class="{ filled: s <= Math.round(studio.average_rating || 0) }">★</span>
                </div>
              </div>
              <button @click="showReviewForm = !showReviewForm" class="leave-review-btn">Оставить отзыв</button>
            </div>

            <!-- Форма отзыва -->
            <div v-if="showReviewForm" class="review-form">
              <div class="category-ratings">
                <div v-for="cat in reviewCategories" :key="cat.key" class="cat-row">
                  <span class="cat-label">{{ cat.label }}</span>
                  <div class="cat-stars">
                    <span
                      v-for="s in 5"
                      :key="s"
                      @click="newReview[cat.key] = s"
                      :class="['cat-star', { filled: s <= newReview[cat.key] }]"
                    >★</span>
                  </div>
                </div>
              </div>
              <textarea v-model="newReview.comment" placeholder="Ваш отзыв о студии..." class="disc-textarea" rows="4"></textarea>
              <div class="disc-form-actions">
                <button @click="submitReview" class="submit-btn">Опубликовать</button>
                <button @click="showReviewForm = false" class="cancel-btn">Отмена</button>
              </div>
            </div>

            <div v-if="reviewsLoading" class="loading-indicator">Загрузка...</div>
            <div v-else-if="reviews.length > 0" class="reviews-list">
              <div v-for="rev in reviews" :key="rev.id" class="review-card">
                <div class="review-card-header">
                  <div class="review-user-info">
                    <div class="review-avatar">
                      <img v-if="rev.user_avatar" :src="rev.user_avatar" :alt="rev.user_name" class="review-avatar-img" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
                      <div v-else class="review-avatar-placeholder">{{ rev.user_name.slice(0, 1).toUpperCase() }}</div>
                    </div>
                    <span class="review-user">@{{ rev.user_name }}</span>
                  </div>
                  <span class="review-date">{{ timeAgo(rev.created_at) }}</span>
                </div>
                <div class="review-overall-badge">⭐ Общая оценка: {{ rev.overall_rating.toFixed(1) }}/5</div>
                <div class="review-cats">
                  <span>Анимация: <b>{{ rev.animation_quality }}</b></span>
                  <span>Режиссура: <b>{{ rev.directing }}</b></span>
                  <span>Саундтрек: <b>{{ rev.soundtrack }}</b></span>
                  <span>Адаптация: <b>{{ rev.adaptation }}</b></span>
                </div>
                <p v-if="rev.comment" class="review-comment">{{ rev.comment }}</p>
              </div>
            </div>
            <div v-else class="empty-tab">Отзывов пока нет. Будьте первым!</div>
          </div>

          <!-- Вкладка: ПОХОЖИЕ -->
          <div v-if="activeTab === 'similar'" class="tab-content">
            <div v-if="similarLoading" class="loading-indicator">Загрузка...</div>
            <div v-else-if="similar.length > 0" class="similar-grid">
              <router-link
                v-for="s in similar"
                :key="s.id"
                :to="`/studios/${s.slug}`"
                class="similar-card"
              >
                <div class="similar-logo">
                  <img v-if="s.logo_image_url" :src="s.logo_image_url" :alt="s.name" class="similar-logo-img" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
                  <div v-else class="similar-logo-placeholder">{{ s.name.slice(0, 2) }}</div>
                </div>
                <div class="similar-name">{{ s.name }}</div>
                <div class="similar-rating">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="#f59e0b" stroke="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                  {{ s.average_rating?.toFixed(1) }}
                </div>
                <div class="similar-count">{{ s.total_anime }} аниме</div>
              </router-link>
            </div>
            <div v-else class="empty-tab">Похожие студии не найдены</div>
          </div>

        </div>

        <!-- Боковая панель -->
        <aside class="studio-sidebar">
          <div class="sidebar-card">
            <h3 class="sidebar-title">📊 Статистика</h3>
            <div class="stat-row"><span>Всего аниме</span><b>{{ studio.total_anime }}</b></div>
            <div class="stat-row"><span>ТВ сериалов</span><b>{{ studio.tv_count }}</b></div>
            <div class="stat-row"><span>Фильмов</span><b>{{ studio.movie_count }}</b></div>
            <div class="stat-row"><span>OVA/ONA</span><b>{{ studio.ova_count }}</b></div>
            <div class="stat-row"><span>Рейтинг</span><b>{{ studio.average_rating?.toFixed(1) }}</b></div>
            <div class="stat-row"><span>Подписчики</span><b>{{ formatCount(studio.subscribers_count) }}</b></div>
          </div>

          <div v-if="studio.top_anime?.length > 0" class="sidebar-card">
            <h3 class="sidebar-title">🏆 Лучшая работа</h3>
            <router-link :to="studio.top_anime![0]!.anime_url ?? `/anime?search=${encodeURIComponent(studio.top_anime![0]!.anime_title)}`" class="best-work-link">
              <div class="best-work-poster">
                <img v-if="studio.top_anime![0]!.anime_poster" :src="studio.top_anime![0]!.anime_poster" :alt="studio.top_anime![0]!.anime_title" class="best-poster-img" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
              </div>
              <div class="best-work-info">
                <div class="best-title">{{ studio.top_anime![0]!.anime_title }}</div>
                <div class="best-score" v-if="studio.top_anime![0]!.anime_score">
                  ★ {{ studio.top_anime![0]!.anime_score!.toFixed(1) }}
                </div>
              </div>
            </router-link>
          </div>

          <div v-if="genreStats.length > 0" class="sidebar-card">
            <h3 class="sidebar-title">🔥 Популярные жанры</h3>
            <div v-for="g in genreStats.slice(0, 5)" :key="g.name" class="genre-tag-row">
              <span class="genre-tag">#{{ g.name }}</span>
              <span class="genre-tag-pct">{{ g.pct }}%</span>
            </div>
          </div>
        </aside>
      </div>
    </template>

    <!-- Ошибка -->
    <div v-else class="error-state">
      <p>Студия не найдена.</p>
      <router-link to="/studios" class="back-link">← Все студии</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import studiosApi, { type StudioDetail, type StudioAnime, type StudioStaff, type StudioNews, type StudioAward, type StudioDiscussion, type StudioReview } from '@/api/studios'

const route = useRoute()
const slug = computed(() => route.params.slug as string)

const studio = ref<StudioDetail | null>(null)
const isLoading = ref(true)

// Tab state
const activeTab = ref('about')
const tabs = [
  { value: 'about', label: 'О студии' },
  { value: 'works', label: 'Работы' },
  { value: 'staff', label: 'Команда' },
  { value: 'news', label: 'Новости' },
  { value: 'discussions', label: 'Обсуждения' },
  { value: 'reviews', label: 'Отзывы' },
  { value: 'similar', label: 'Похожие' },
]

const descExpanded = ref(false)

// Works
const works = ref<StudioAnime[]>([])
const worksLoading = ref(false)
const worksSearch = ref('')
const worksKind = ref('')
const worksOrdering = ref('-anime_year')
let worksTimer: ReturnType<typeof setTimeout> | null = null

// Staff
const staff = ref<StudioStaff[]>([])
const staffLoading = ref(false)

// News
const news = ref<StudioNews[]>([])
const newsLoading = ref(false)

// Awards
const awards = ref<StudioAward[]>([])
const awardsLoading = ref(false)

// Discussions
const discussions = ref<StudioDiscussion[]>([])
const discussionsLoading = ref(false)
const discussionOrdering = ref('-created_at')
const showDiscussionForm = ref(false)
const newDiscTitle = ref('')
const newDiscContent = ref('')
const activeDiscussion = ref<StudioDiscussion | null>(null)
const replyContent = ref('')
const discReplies = ref<Record<number, any[]>>({})

// Reviews
const reviews = ref<StudioReview[]>([])
const reviewsLoading = ref(false)
const showReviewForm = ref(false)
const reviewCategories = [
  { key: 'animation_quality', label: 'Качество анимации' },
  { key: 'directing', label: 'Режиссура' },
  { key: 'soundtrack', label: 'Саундтрек' },
  { key: 'adaptation', label: 'Адаптация' },
]
const newReview = ref<any>({ animation_quality: 5, directing: 5, soundtrack: 5, adaptation: 5, comment: '' })

// Similar
const similar = ref<any[]>([])
const similarLoading = ref(false)

// Computed
const ratingDistribution = computed(() => {
  if (!studio.value) return {}
  const dist = studio.value.rating_distribution || {}
  return Object.fromEntries([5, 4, 3, 2, 1].map(k => [k, dist[k] || 0]))
})

const genreStats = computed(() => {
  if (!studio.value?.genre_stats) return []
  return Object.entries(studio.value.genre_stats)
    .map(([name, pct]) => ({ name, pct: Number(pct) }))
    .sort((a, b) => b.pct - a.pct)
    .slice(0, 8)
})

const worksByYear = computed(() => {
  const map = new Map<number | null, StudioAnime[]>()
  for (const w of works.value) {
    const yr = w.anime_year || 0
    if (!map.has(yr)) map.set(yr, [])
    map.get(yr)!.push(w)
  }
  const descYear = worksOrdering.value !== 'anime_year'
  return [...map.entries()]
    .sort(([a], [b]) => descYear ? (b || 0) - (a || 0) : (a || 0) - (b || 0))
    .map(([year, items]) => ({ year: year || null, items }))
})

const staffGroups = computed(() => {
  const roles = [
    { key: 'founder', label: 'Основатели', icon: '🏛' },
    { key: 'ceo', label: 'Руководство', icon: '👔' },
    { key: 'director', label: 'Режиссёры', icon: '🎬' },
    { key: 'animator', label: 'Аниматоры', icon: '🎨' },
    { key: 'composer', label: 'Композиторы', icon: '🎵' },
    { key: 'voice_actor', label: 'Актёры озвучки (Сейю)', icon: '🎙️' },
    { key: 'other', label: 'Другие', icon: '👥' },
  ]
  return roles
    .map(r => ({ ...r, members: staff.value.filter(s => s.role === r.key) }))
    .filter(r => r.members.length > 0)
})

const awardsByYear = computed(() => {
  const map = new Map<number, StudioAward[]>()
  for (const a of awards.value) {
    if (!map.has(a.year)) map.set(a.year, [])
    map.get(a.year)!.push(a)
  }
  return [...map.entries()].sort(([a], [b]) => b - a).map(([year, awards]) => ({ year, awards }))
})

// Methods
const fetchStudio = async () => {
  isLoading.value = true
  try {
    const res = await studiosApi.getStudio(slug.value)
    studio.value = res.data
  } catch (e) {
    studio.value = null
  } finally {
    isLoading.value = false
  }
}

const fetchWorks = async () => {
  worksLoading.value = true
  try {
    const params: any = { ordering: worksOrdering.value, page_size: 500 }
    if (worksKind.value) params.kind = worksKind.value
    if (worksSearch.value) params.search = worksSearch.value
    const res = await studiosApi.getWorks(slug.value, params)
    const raw: StudioAnime[] = Array.isArray(res.data) ? res.data as any : (res.data.results ?? [])
    const seen = new Map<string, StudioAnime>()
    for (const w of raw) {
      const key = w.shikimori_id
        ? `shiki:${w.shikimori_id}:${w.anime_title}`
        : `notitle:${w.anime_title}:${w.anime_year ?? ''}`
      if (!seen.has(key)) {
        seen.set(key, w)
      } else {
        const existing = seen.get(key)!
        if (!existing.anime_db_id && w.anime_db_id) seen.set(key, w)
      }
    }
    works.value = [...seen.values()]
  } catch (e) {}
  finally { worksLoading.value = false }
}

const debouncedFetchWorks = () => {
  if (worksTimer) clearTimeout(worksTimer)
  worksTimer = setTimeout(fetchWorks, 300)
}

const fetchStaff = async () => {
  staffLoading.value = true
  try {
    const res = await studiosApi.getStaff(slug.value)
    staff.value = Array.isArray(res.data) ? res.data : (res.data as any).results || []
  } catch (e) {} finally { staffLoading.value = false }
}

const fetchNews = async () => {
  newsLoading.value = true
  try {
    const res = await studiosApi.getNews(slug.value)
    news.value = (res.data as any).results || (Array.isArray(res.data) ? res.data : [])
  } catch (e) {} finally { newsLoading.value = false }
}

const fetchAwards = async () => {
  awardsLoading.value = true
  try {
    const res = await studiosApi.getAwards(slug.value)
    awards.value = Array.isArray(res.data) ? res.data : (res.data as any).results || []
  } catch (e) {} finally { awardsLoading.value = false }
}

const fetchDiscussions = async () => {
  discussionsLoading.value = true
  try {
    const res = await studiosApi.getDiscussions(slug.value, discussionOrdering.value)
    discussions.value = (res.data as any).results || (Array.isArray(res.data) ? res.data : [])
  } catch (e) {} finally { discussionsLoading.value = false }
}

const fetchReviews = async () => {
  reviewsLoading.value = true
  try {
    const res = await studiosApi.getReviews(slug.value)
    reviews.value = (res.data as any).results || (Array.isArray(res.data) ? res.data : [])
  } catch (e) {} finally { reviewsLoading.value = false }
}

const fetchSimilar = async () => {
  similarLoading.value = true
  try {
    const res = await studiosApi.getSimilar(slug.value)
    similar.value = Array.isArray(res.data) ? res.data : (res.data as any).results || []
  } catch (e) {} finally { similarLoading.value = false }
}

const toggleSubscribe = async () => {
  if (!studio.value) return
  try {
    if (studio.value.is_subscribed) {
      const res = await studiosApi.unsubscribe(slug.value)
      studio.value.is_subscribed = false
      studio.value.subscribers_count = res.data.subscribers_count
    } else {
      const res = await studiosApi.subscribe(slug.value)
      studio.value.is_subscribed = true
      studio.value.subscribers_count = res.data.subscribers_count
    }
  } catch (e) {}
}

const createDiscussion = async () => {
  if (!newDiscTitle.value || !newDiscContent.value) return
  try {
    await studiosApi.createDiscussion(slug.value, { title: newDiscTitle.value, content: newDiscContent.value })
    newDiscTitle.value = ''
    newDiscContent.value = ''
    showDiscussionForm.value = false
    fetchDiscussions()
  } catch (e) {}
}

const openDiscussion = async (disc: StudioDiscussion) => {
  if (activeDiscussion.value?.id === disc.id) {
    activeDiscussion.value = null
    return
  }
  activeDiscussion.value = disc
  replyContent.value = ''
  if (!discReplies.value[disc.id]) {
    try {
      const res = await studiosApi.getDiscussionReplies(slug.value, disc.id)
      discReplies.value[disc.id] = Array.isArray(res.data) ? res.data : (res.data as any).results || []
    } catch (e) {
      discReplies.value[disc.id] = []
    }
  }
}

const likeDiscussion = async (disc: any) => {
  try {
    const res = await studiosApi.likeDiscussion(slug.value, disc.id)
    disc.likes_count = res.data.likes_count ?? disc.likes_count
    disc.liked = res.data.liked
  } catch (e) {}
}

const dislikeDiscussion = async (disc: any) => {
  try {
    const res = await studiosApi.dislikeDiscussion(slug.value, disc.id)
    disc.dislikes_count = res.data.dislikes_count ?? disc.dislikes_count
    disc.disliked = res.data.disliked
  } catch (e) {}
}

const submitReply = async (disc: StudioDiscussion) => {
  if (!replyContent.value.trim()) return
  try {
    const res = await studiosApi.createDiscussionReply(slug.value, disc.id, replyContent.value)
    if (!discReplies.value[disc.id]) discReplies.value[disc.id] = []
    discReplies.value[disc.id]!.push(res.data)
    disc.replies_count++
    replyContent.value = ''
  } catch (e) {}
}

const submitReview = async () => {
  try {
    await studiosApi.createReview(slug.value, newReview.value)
    showReviewForm.value = false
    newReview.value = { animation_quality: 5, directing: 5, soundtrack: 5, adaptation: 5, comment: '' }
    fetchReviews()
    fetchStudio()
  } catch (e) {}
}

const formatCount = (n: number) => {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return String(n)
}

const formatDate = (d: string) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

const timeAgo = (d: string) => {
  if (!d) return ''
  const diff = Date.now() - new Date(d).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins} мин. назад`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} ч. назад`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days} дн. назад`
  return formatDate(d)
}

const kindLabel = (kind: string) => {
  const map: Record<string, string> = { tv: 'TV', movie: 'Фильм', ova: 'OVA', ona: 'ONA', special: 'SP', music: 'MV' }
  return map[kind] || kind.toUpperCase()
}

const statusBadge = (status: string) => {
  const map: Record<string, string> = {
    ongoing: 'Онгоинг',
    anons: 'Анонс',
    released: '',
  }
  return map[status] ?? ''
}

// Lazy load tab data
watch(activeTab, (tab) => {
  if (tab === 'works' && works.value.length === 0) fetchWorks()
  if (tab === 'staff' && staff.value.length === 0) fetchStaff()
  if (tab === 'news' && news.value.length === 0) fetchNews()
  if (tab === 'awards' && awards.value.length === 0) fetchAwards()
  if (tab === 'discussions' && discussions.value.length === 0) fetchDiscussions()
  if (tab === 'reviews' && reviews.value.length === 0) fetchReviews()
  if (tab === 'similar' && similar.value.length === 0) fetchSimilar()
})

watch(slug, () => {
  fetchStudio()
})

onMounted(() => {
  fetchStudio()
})
</script>

<style scoped>
.studio-detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 0 2rem;
}

/* Loading skeletons */
.loading-hero { padding: 1rem; }
.sk-banner { height: 200px; background: var(--color-background-active); border-radius: 1rem; margin-bottom: 1rem; animation: pulse 1.5s infinite; }
.sk-info-row { display: flex; gap: 1rem; }
.sk-logo-lg { width: 80px; height: 80px; border-radius: 0.75rem; background: var(--color-background-active); flex-shrink: 0; animation: pulse 1.5s infinite; }
.sk-text-block { flex: 1; display: flex; flex-direction: column; gap: 0.5rem; }
.sk-line { height: 18px; background: var(--color-background-active); border-radius: 4px; animation: pulse 1.5s infinite; }
.sk-line.wide { width: 60%; }
.sk-line.mid { width: 40%; }
.sk-line.short { width: 25%; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

/* Hero */
.studio-hero { margin-bottom: 0; }
.hero-banner {
  position: relative;
  min-height: 220px;
  background-color: var(--color-background-surface);
  background-size: cover;
  background-position: center;
  border-radius: 0 0 1rem 1rem;
}
.hero-banner-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.7) 100%);
  border-radius: inherit;
}
.hero-content {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 1.5rem;
  padding: 2rem 1.5rem 1.5rem;
  align-items: flex-end;
}
.hero-logo {
  width: 90px;
  height: 90px;
  border-radius: 1rem;
  overflow: hidden;
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(8px);
  border: 2px solid rgba(255,255,255,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.hero-logo-img { width: 100%; height: 100%; object-fit: contain; }
.hero-logo-placeholder { font-size: 2rem; font-weight: 800; color: #fff; }
.hero-text { flex: 1; }
.hero-title-row { display: flex; align-items: center; gap: 0.5rem; }
.hero-title { font-size: 1.75rem; font-weight: 900; color: #fff; margin: 0; text-shadow: 0 2px 8px rgba(0,0,0,0.5); }
.verified-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: var(--color-accent);
  color: #fff;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 700;
}
.hero-title-jp { font-size: 0.875rem; color: rgba(255,255,255,0.7); margin: 0.25rem 0 0.5rem; }
.hero-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 0.875rem;
  color: rgba(255,255,255,0.85);
  margin-bottom: 0.75rem;
}
.hero-rating { display: flex; align-items: center; gap: 0.25rem; font-weight: 700; color: #f59e0b; }
.hero-actions { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
.sub-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.25rem;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: 9999px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.sub-btn:hover { opacity: 0.85; }
.sub-btn.subscribed {
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.3);
}
.sub-count {
  font-size: 0.8rem;
  font-weight: 500;
  opacity: 0.85;
}
.hero-link-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  color: #fff;
  text-decoration: none;
  transition: all 0.2s;
}
.hero-link-btn:hover { background: rgba(255,255,255,0.3); }

/* Tabs */
.studio-tabs {
  display: flex;
  gap: 0;
  padding: 0 1.5rem;
  border-bottom: 1px solid var(--color-divider-light);
  background: var(--color-background-surface);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.studio-tabs::-webkit-scrollbar { display: none; }
.tab-btn {
  padding: 0.875rem 1.125rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  margin-bottom: -1px;
}
.tab-btn:hover { color: var(--color-text); }
.tab-btn.active { color: var(--color-accent); border-bottom-color: var(--color-accent); }

/* Body layout */
.studio-body {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 1.5rem;
  padding: 1.5rem;
}
.studio-main { min-width: 0; }

/* Cards */
.content-card {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin-bottom: 1rem;
}
.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 0.875rem;
}
.description-text {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.65;
  margin: 0;
  white-space: pre-line;
}
.description-text.collapsed {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.expand-btn {
  margin-top: 0.5rem;
  background: transparent;
  border: none;
  color: var(--color-accent);
  font-size: 0.875rem;
  cursor: pointer;
  padding: 0;
}

/* Rating */
.rating-overview { display: flex; gap: 1.5rem; align-items: flex-start; }
.rating-big { font-size: 3rem; font-weight: 900; color: var(--color-text); line-height: 1; }
.rating-bars { flex: 1; }
.rating-bar-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.375rem; }
.bar-label { font-size: 0.8125rem; color: var(--color-text-secondary); width: 28px; text-align: right; }
.bar-track { flex: 1; height: 8px; background: var(--color-background-active); border-radius: 9999px; overflow: hidden; }
.bar-fill { height: 100%; background: #f59e0b; border-radius: 9999px; transition: width 0.6s ease; }
.bar-pct { font-size: 0.75rem; color: var(--color-text-tertiary); width: 30px; }

/* Genres */
.genre-bars { display: flex; flex-direction: column; gap: 0.5rem; }
.genre-row { display: flex; align-items: center; gap: 0.75rem; }
.genre-name { font-size: 0.875rem; color: var(--color-text-secondary); width: 100px; }
.genre-track { flex: 1; height: 8px; background: var(--color-background-active); border-radius: 9999px; overflow: hidden; }
.genre-fill { height: 100%; background: var(--color-accent); border-radius: 9999px; }
.genre-pct { font-size: 0.75rem; color: var(--color-text-tertiary); width: 35px; text-align: right; }

/* Links */
.links-list { display: flex; flex-direction: column; gap: 0.5rem; }
.official-link {
  font-size: 0.9375rem;
  color: var(--color-accent);
  text-decoration: none;
  padding: 0.375rem 0;
}
.official-link:hover { text-decoration: underline; }
.no-links { font-size: 0.875rem; color: var(--color-text-tertiary); margin: 0; }

/* Works */
.works-filters { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
.works-search {
  flex: 1;
  min-width: 150px;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background: var(--color-background-surface);
  outline: none;
}
.works-search:focus { border-color: var(--color-accent); }
.works-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background: var(--color-background-surface);
  outline: none;
  cursor: pointer;
}
.year-group { margin-bottom: 1.5rem; }
.year-heading {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-secondary);
  margin: 0 0 0.75rem;
  border-left: 3px solid var(--color-accent);
  padding-left: 0.625rem;
}
.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.75rem;
}
.work-card {
  text-decoration: none;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}
.work-card:hover .poster-img { opacity: 0.85; transform: scale(1.02); }
.work-poster {
  position: relative;
  aspect-ratio: 2/3;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--color-background-active);
}
.poster-img { width: 100%; height: 100%; object-fit: cover; transition: all 0.2s; }
.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-accent);
}
.work-kind-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  background: rgba(0,0,0,0.7);
  color: #fff;
  font-size: 0.625rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}
.work-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.work-score {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}
.work-card-skeleton {
  aspect-ratio: 2/3;
  border-radius: 0.5rem;
  background: var(--color-background-active);
  animation: pulse 1.5s infinite;
}
.work-card-linked:hover .poster-img { opacity: 0.85; transform: scale(1.02); }
.work-title-en {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 1px;
}
.work-meta {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}
.work-eps { font-size: 0.7rem; color: var(--color-text-tertiary); }
.work-status-badge {
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 0.55rem;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 4px;
  text-transform: uppercase;
}
.status-ongoing { background: rgba(16,185,129,0.85); color: #fff; }
.status-anons { background: rgba(59,130,246,0.85); color: #fff; }

/* Staff */
.staff-group { margin-bottom: 1.5rem; }
.staff-cards { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.staff-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.875rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  width: 110px;
}
.staff-photo {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
}
.staff-photo-img { width: 100%; height: 100%; object-fit: cover; }
.staff-photo-placeholder { font-size: 1.5rem; font-weight: 800; color: var(--color-accent); }
.staff-card-name { font-size: 0.8125rem; font-weight: 700; color: var(--color-text); text-align: center; }
.staff-card-jp { font-size: 0.6875rem; color: var(--color-text-tertiary); text-align: center; }
.staff-card-works { font-size: 0.75rem; color: var(--color-text-secondary); }
.staff-list { display: flex; flex-direction: column; gap: 0.375rem; }
.staff-list-item { font-size: 0.9rem; color: var(--color-text-secondary); }
.staff-list-name { font-weight: 600; color: var(--color-text); }
.staff-list-detail { color: var(--color-text-tertiary); margin: 0 0.25rem; }
.staff-list-works { color: var(--color-text-tertiary); }

/* News */
.news-list { display: flex; flex-direction: column; gap: 0.75rem; }
.news-card {
  padding: 1rem 1.25rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
}
.news-date { font-size: 0.8125rem; color: var(--color-accent); font-weight: 600; margin-bottom: 0.375rem; }
.news-title { font-size: 1rem; font-weight: 700; color: var(--color-text); margin: 0 0 0.375rem; }
.news-preview { font-size: 0.875rem; color: var(--color-text-secondary); margin: 0 0 0.75rem; line-height: 1.5; }
.news-footer { display: flex; gap: 0.75rem; font-size: 0.8125rem; color: var(--color-text-tertiary); }

/* Discussions */
.discussions-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
.new-disc-btn {
  padding: 0.5rem 1rem;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.new-disc-btn:hover { opacity: 0.85; }
.disc-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  margin-bottom: 1rem;
}
.disc-input, .disc-textarea {
  padding: 0.625rem 0.875rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text);
  background: var(--color-background);
  outline: none;
  resize: vertical;
}
.disc-input:focus, .disc-textarea:focus { border-color: var(--color-accent); }
.disc-form-actions { display: flex; gap: 0.5rem; }
.submit-btn {
  padding: 0.5rem 1.25rem;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.cancel-btn {
  padding: 0.5rem 1.25rem;
  background: transparent;
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  cursor: pointer;
}
.discussions-list { display: flex; flex-direction: column; gap: 0.625rem; }
.discussion-card {
  display: flex;
  gap: 0.875rem;
  padding: 1rem 1.25rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  transition: background 0.15s;
}
.discussion-card:hover { background: var(--color-background-active); }
.discussion-card.pinned { border-color: var(--color-accent); }
.disc-author-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 0.125rem;
}
.disc-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.disc-avatar-placeholder {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-accent);
}
.disc-body { flex: 1; min-width: 0; }
.disc-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem; flex-wrap: wrap; }
.disc-author { font-size: 0.875rem; font-weight: 700; color: var(--color-text); }
.disc-pin-badge { font-size: 0.75rem; color: var(--color-accent); font-weight: 600; }
.disc-time { font-size: 0.8rem; color: var(--color-text-tertiary); margin-left: auto; }
.disc-title { font-size: 0.9375rem; font-weight: 700; color: var(--color-text); margin: 0 0 0.25rem; transition: color 0.15s; }
.disc-title:hover { color: var(--color-accent); }
.disc-preview { font-size: 0.875rem; color: var(--color-text-secondary); margin: 0 0 0.5rem; line-height: 1.5; }
.disc-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 0.375rem;
}
.disc-action-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.625rem;
  border: 1px solid var(--color-divider-light);
  border-radius: 9999px;
  background: transparent;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.disc-action-btn:hover { border-color: var(--color-accent); color: var(--color-accent); }
.disc-action-btn.active { background: var(--color-accent); border-color: var(--color-accent); color: #fff; }
.disc-last-reply { font-size: 0.75rem; color: var(--color-text-tertiary); margin-left: auto; }
.disc-reply-form {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-divider-light);
}
.disc-replies { margin-top: 0.75rem; display: flex; flex-direction: column; gap: 0.5rem; }
.disc-reply-item { display: flex; gap: 0.5rem; align-items: flex-start; }
.disc-reply-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.disc-reply-body { flex: 1; min-width: 0; }
.disc-reply-author { font-size: 0.8125rem; font-weight: 700; color: var(--color-text); margin-right: 0.375rem; }
.disc-reply-time { font-size: 0.75rem; color: var(--color-text-tertiary); }
.disc-reply-text { font-size: 0.875rem; color: var(--color-text-secondary); margin: 0.125rem 0 0; line-height: 1.5; }

/* Reviews */
.reviews-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.75rem; }
.review-overall { display: flex; align-items: center; gap: 0.75rem; }
.review-score { font-size: 2.5rem; font-weight: 900; color: var(--color-text); }
.stars-lg { display: flex; gap: 2px; }
.star-lg { font-size: 1.5rem; color: var(--color-divider); }
.star-lg.filled { color: #f59e0b; }
.leave-review-btn {
  padding: 0.5rem 1.25rem;
  background: var(--color-accent);
  color: #fff;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}
.review-form {
  padding: 1rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  margin-bottom: 1rem;
}
.category-ratings { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 0.75rem; }
.cat-row { display: flex; align-items: center; justify-content: space-between; }
.cat-label { font-size: 0.875rem; color: var(--color-text-secondary); }
.cat-stars { display: flex; gap: 2px; }
.cat-star { font-size: 1.25rem; color: var(--color-divider); cursor: pointer; transition: color 0.1s; }
.cat-star.filled, .cat-star:hover { color: #f59e0b; }
.reviews-list { display: flex; flex-direction: column; gap: 0.75rem; }
.review-card {
  padding: 1rem 1.25rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
}
.review-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.375rem; }
.review-user-info { display: flex; align-items: center; gap: 0.5rem; }
.review-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.review-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.review-avatar-placeholder { font-size: 0.875rem; font-weight: 700; color: var(--color-accent); }
.review-user { font-size: 0.875rem; font-weight: 700; color: var(--color-text); }
.review-date { font-size: 0.8125rem; color: var(--color-text-tertiary); }
.review-overall-badge { font-size: 0.875rem; font-weight: 700; color: var(--color-accent); margin-bottom: 0.375rem; }
.review-cats { display: flex; gap: 0.75rem; flex-wrap: wrap; font-size: 0.8125rem; color: var(--color-text-secondary); margin-bottom: 0.5rem; }
.review-comment { font-size: 0.9rem; color: var(--color-text-secondary); margin: 0; line-height: 1.5; }

/* Similar */
.similar-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.75rem;
}
.similar-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.375rem;
  padding: 0.875rem 0.625rem;
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  text-decoration: none;
  transition: all 0.2s;
}
.similar-card:hover { transform: translateY(-2px); border-color: var(--color-accent); }
.similar-logo {
  width: 56px;
  height: 56px;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--color-background-active);
  display: flex;
  align-items: center;
  justify-content: center;
}
.similar-logo-img { width: 100%; height: 100%; object-fit: contain; }
.similar-logo-placeholder { font-size: 1rem; font-weight: 800; color: var(--color-accent); }
.similar-name { font-size: 0.8125rem; font-weight: 700; color: var(--color-text); text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }
.similar-rating { display: flex; align-items: center; gap: 0.2rem; font-size: 0.8125rem; font-weight: 600; color: var(--color-text-secondary); }
.similar-count { font-size: 0.75rem; color: var(--color-text-tertiary); }

/* Sidebar */
.studio-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  align-self: start;
  position: sticky;
  top: 1rem;
}
.sidebar-card {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  padding: 1rem;
}
.sidebar-title { font-size: 0.9375rem; font-weight: 700; color: var(--color-text); margin: 0 0 0.75rem; }
.stat-row { display: flex; justify-content: space-between; font-size: 0.875rem; color: var(--color-text-secondary); padding: 0.25rem 0; border-bottom: 1px solid var(--color-divider-light); }
.stat-row:last-child { border-bottom: none; }
.stat-row b { color: var(--color-text); }
.best-work-link { display: flex; gap: 0.75rem; text-decoration: none; align-items: center; }
.best-work-poster { width: 52px; height: 72px; border-radius: 0.375rem; overflow: hidden; background: var(--color-background-active); flex-shrink: 0; }
.best-poster-img { width: 100%; height: 100%; object-fit: cover; }
.best-title { font-size: 0.875rem; font-weight: 700; color: var(--color-text); margin-bottom: 0.25rem; }
.best-score { font-size: 0.8125rem; color: #f59e0b; font-weight: 700; }
.genre-tag-row { display: flex; justify-content: space-between; align-items: center; padding: 0.25rem 0; }
.genre-tag { font-size: 0.875rem; color: var(--color-accent); font-weight: 500; }
.genre-tag-pct { font-size: 0.8125rem; color: var(--color-text-tertiary); }

/* Misc */
.loading-indicator { padding: 2rem; text-align: center; color: var(--color-text-secondary); }
.empty-tab { padding: 3rem 2rem; text-align: center; color: var(--color-text-tertiary); font-size: 0.9375rem; }
.error-state { padding: 4rem 2rem; text-align: center; }
.back-link { color: var(--color-accent); text-decoration: none; font-size: 0.9375rem; }

/* Stars */
.stars-row { display: flex; gap: 1px; }
.star { font-size: 1rem; color: var(--color-divider); }
.star.filled { color: #f59e0b; }

/* Responsive */
@media (max-width: 960px) {
  .studio-body { grid-template-columns: 1fr; }
  .studio-sidebar { position: static; }
}
@media (max-width: 768px) {
  .hero-content { padding: 1.25rem 1rem 1rem; flex-direction: column; align-items: flex-start; gap: 1rem; }
  .hero-title { font-size: 1.375rem; }
  .studio-body { padding: 1rem; gap: 1rem; }
  .works-grid { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }
}
</style>
