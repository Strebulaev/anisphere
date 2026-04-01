<template>
  <div class="dub-group-page">
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

    <template v-else-if="group">
      <!-- Hero Section -->
      <div class="studio-hero">
        <!-- Баннер -->
        <div
          class="hero-banner"
          :style="group.banner_image_url ? `background-image: url('${group.banner_image_url}')` : ''"
        >
          <div class="hero-banner-overlay"></div>

          <!-- Информация поверх баннера -->
          <div class="hero-content">
            <div class="hero-logo">
              <img
                v-if="group.logo_image_url"
                :src="group.logo_image_url"
                :alt="group.name"
                class="hero-logo-img"
                @error="(e) => (e.target as HTMLImageElement).style.display = 'none'"
              />
              <div v-else class="hero-logo-placeholder">{{ group.name.slice(0, 2) }}</div>
            </div>

            <div class="hero-text">
              <div class="hero-title-row">
                <h1 class="hero-title">{{ group.name }}</h1>
                <span v-if="group.is_verified" class="verified-badge">✓</span>
              </div>
              <div v-if="group.name_jp" class="hero-title-jp">【{{ group.name_jp }}】</div>

              <div class="hero-meta">
                <span class="hero-rating">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="#f59e0b" stroke="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                  {{ group.average_rating?.toFixed(1) || '—' }}
                </span>
                <span v-if="group.founded_year">📅 {{ group.founded_year }}</span>
                <span>🎬 {{ group.works_count }} озвучек</span>
                <span class="type-badge" :class="group.translation_type">
                  {{ getTranslationTypeLabel(group.translation_type) }}
                </span>
              </div>

              <div class="hero-actions">
                <button
                  @click="toggleSubscribe"
                  :class="['sub-btn', { subscribed: group.is_subscribed }]"
                >
                  <span>{{ group.is_subscribed ? '✓ Подписан' : '👍 Подписаться' }}</span>
                  <span class="sub-count">{{ formatCount(group.subscribers_count) }}</span>
                </button>
                <a v-if="group.website" :href="group.website" target="_blank" class="hero-link-btn" title="Официальный сайт">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                </a>
                <a v-if="group.vk_url" :href="group.vk_url" target="_blank" class="hero-link-btn" title="VK">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M15 0H9v6h4V24h4V12h2V6h-2V0z"/></svg>
                </a>
                <a v-if="group.telegram_url" :href="group.telegram_url" target="_blank" class="hero-link-btn" title="Telegram">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.248l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295l.213-3.054 5.56-5.023c.242-.213-.054-.334-.373-.121L6.5 17.5l-2.11-.917c-.64-.213-1.067-.326-1.344-.163l-2.79 1.984c-.36.26-.357.26-.656.13L1.5 15.5c-.427-.26-.642-.637-.39-1.017l4.678-4.597 3.12 2.31c.26.213.597.213.856 0l4.78-3.064c.26-.173.596-.26.857-.078l2.546 1.89c.26.173.26.433 0 .606z"/></svg>
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

          <!-- Вкладка: О ГРУППЕ -->
          <div v-if="activeTab === 'about'" class="tab-content">
            <!-- Рейтинги -->
            <div class="content-card">
              <h2 class="card-title">📊 Рейтинг группы</h2>
              <div class="rating-overview">
                <div class="rating-big">{{ group.average_rating?.toFixed(1) || '—' }}</div>
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

            <!-- Описание -->
            <div v-if="group.description" class="content-card">
              <h2 class="card-title">📝 О группе</h2>
              <p class="description-text">{{ group.description }}</p>
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
            <div v-if="worksLoading" class="loading-indicator">Загрузка...</div>
            <div v-else-if="works.length > 0" class="works-grid">
              <component
                v-for="work in works"
                :key="work.id"
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
                  <div v-else class="poster-placeholder">{{ work.anime_title?.slice(0, 2) || '🎬' }}</div>
                </div>
                <div class="work-info">
                  <div class="work-title">{{ work.anime_title }}</div>
                  <div class="work-meta">
                    <span class="work-score" v-if="work.anime_score">
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="#f59e0b" stroke="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                      {{ work.anime_score.toFixed(1) }}
                    </span>
                  </div>
                </div>
              </component>
            </div>
            <div v-else class="empty-tab">Работы не найдены</div>
          </div>

          <!-- Вкладка: КОМАНДА -->
          <div v-if="activeTab === 'staff'" class="tab-content">
            <div v-if="staffLoading" class="loading-indicator">Загрузка...</div>
            <template v-else-if="staff.length > 0">
              <div class="staff-grid">
                <div v-for="actor in staff" :key="actor.id" class="staff-card">
                  <div class="staff-photo">
                    <img v-if="actor.photo_url" :src="actor.photo_url" :alt="actor.name" class="staff-photo-img" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
                    <div v-else class="staff-photo-placeholder">{{ actor.name?.slice(0, 1) || '?' }}</div>
                  </div>
                  <div class="staff-card-name">{{ actor.name }}</div>
                  <div class="staff-card-works">{{ actor.roles_count }} ролей</div>
                </div>
              </div>
            </template>
            <div v-else class="empty-tab">Команда не указана</div>
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
                  <span>💭 {{ item.comments_count }}</span>
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
                  <div v-else class="disc-avatar-placeholder">{{ disc.author_name?.slice(0, 1).toUpperCase() || '?' }}</div>
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
                      💭 <span>{{ disc.replies_count }} ответов</span>
                    </button>
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
                          <div v-else class="disc-avatar-placeholder">{{ reply.author_name?.slice(0,1).toUpperCase() || '?' }}</div>
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
                <span class="review-score">{{ group.average_rating?.toFixed(1) || '—' }}</span>
                <div class="stars-lg">
                  <span v-for="s in 5" :key="s" class="star-lg" :class="{ filled: s <= Math.round(group.average_rating || 0) }">★</span>
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
              <textarea v-model="newReview.comment" placeholder="Ваш отзыв о группе..." class="disc-textarea" rows="4"></textarea>
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
                      <div v-else class="review-avatar-placeholder">{{ rev.user_name?.slice(0, 1).toUpperCase() || '?' }}</div>
                    </div>
                    <span class="review-user">@{{ rev.user_name }}</span>
                  </div>
                  <span class="review-date">{{ timeAgo(rev.created_at) }}</span>
                </div>
                <div class="review-overall-badge">⭐ Общая оценка: {{ rev.overall_rating.toFixed(1) }}/5</div>
                <div class="review-cats">
                  <span>Озвучка: <b>{{ rev.voice_quality }}</b></span>
                  <span>Синхронизация: <b>{{ rev.timing }}</b></span>
                  <span>Перевод: <b>{{ rev.translation }}</b></span>
                  <span>Постоянство: <b>{{ rev.consistency }}</b></span>
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
                :to="`/dub-groups/${s.slug}`"
                class="similar-card"
              >
                <div class="similar-logo">
                  <img v-if="s.logo_image_url" :src="s.logo_image_url" :alt="s.name" class="similar-logo-img" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
                  <div v-else class="similar-logo-placeholder">{{ s.name?.slice(0, 2) || '??' }}</div>
                </div>
                <div class="similar-name">{{ s.name }}</div>
                <div class="similar-rating">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="#f59e0b" stroke="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                  {{ s.average_rating?.toFixed(1) }}
                </div>
                <div class="similar-count">{{ s.works_count }} озвучек</div>
              </router-link>
            </div>
            <div v-else class="empty-tab">Похожие группы не найдены</div>
          </div>

        </div>

        <!-- Боковая панель -->
        <aside class="studio-sidebar">
          <div class="sidebar-card">
            <h3 class="sidebar-title">📊 Статистика</h3>
            <div class="stat-row"><span>Всего озвучек</span><b>{{ group.works_count }}</b></div>
            <div class="stat-row"><span>ТВ сериалов</span><b>{{ group.tv_count }}</b></div>
            <div class="stat-row"><span>Фильмов</span><b>{{ group.movie_count }}</b></div>
            <div class="stat-row"><span>OVA/ONA</span><b>{{ group.ova_count }}</b></div>
            <div class="stat-row"><span>Рейтинг</span><b>{{ group.average_rating?.toFixed(1) }}</b></div>
            <div class="stat-row"><span>Подписчики</span><b>{{ formatCount(group.subscribers_count) }}</b></div>
          </div>

          <div v-if="group.top_anime?.length > 0" class="sidebar-card">
            <h3 class="sidebar-title">🏆 Лучшая работа</h3>
            <router-link :to="group.top_anime![0]!.anime_url ?? `/anime`" class="best-work-link">
              <div class="best-work-poster">
                <img v-if="group.top_anime![0]!.anime_poster" :src="group.top_anime![0]!.anime_poster" :alt="group.top_anime![0]!.anime_title" class="best-poster-img" @error="(e) => (e.target as HTMLImageElement).style.display='none'" />
              </div>
              <div class="best-work-info">
                <div class="best-title">{{ group.top_anime![0]!.anime_title }}</div>
                <div class="best-score" v-if="group.top_anime![0]!.anime_score">
                  ★ {{ group.top_anime![0]!.anime_score!.toFixed(1) }}
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
      <p>Группа озвучки не найдена.</p>
      <router-link to="/dub-groups" class="back-link">← Все группы озвучки</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import dubGroupsApi, { type DubGroupDetail, type DubGroupDiscussion, type DubGroupReview } from '@/api/dubGroups'
import { useTabState } from '@/composables/useTabState'

const route = useRoute()

// Поддержка обоих маршрутов: /dub-groups/:slug и /dubs/:id (для совместимости)
const slug = computed(() => {
  // Новый маршрут: /dub-groups/:slug
  if (route.params.slug) return route.params.slug as string
  // Старый маршрут: /dubs/:id - преобразуем id в slug через API
  return route.params.id as string
})

// Используем composable для сохранения вкладки (только для slug маршрута)
const tabKey = computed(() => route.params.slug ? `dub-group-${route.params.slug}` : `dub-group-id-${route.params.id}`)
const { activeTab, setTab } = useTabState(tabKey.value, 'about')

const group = ref<DubGroupDetail | null>(null)
const isLoading = ref(true)

const tabs = [
  { value: 'about', label: 'О группе' },
  { value: 'works', label: 'Работы' },
  { value: 'staff', label: 'Команда' },
  { value: 'news', label: 'Новости' },
  { value: 'discussions', label: 'Обсуждения' },
  { value: 'reviews', label: 'Отзывы' },
  { value: 'similar', label: 'Похожие' },
]

// Works
const works = ref<any[]>([])
const worksLoading = ref(false)

// Staff
const staff = ref<any[]>([])
const staffLoading = ref(false)

// News
const news = ref<any[]>([])
const newsLoading = ref(false)

// Discussions
const discussions = ref<DubGroupDiscussion[]>([])
const discussionsLoading = ref(false)
const discussionOrdering = ref('-created_at')
const showDiscussionForm = ref(false)
const newDiscTitle = ref('')
const newDiscContent = ref('')
const activeDiscussion = ref<DubGroupDiscussion | null>(null)
const replyContent = ref('')
const discReplies = ref<Record<number, any[]>>({})

// Reviews
const reviews = ref<DubGroupReview[]>([])
const reviewsLoading = ref(false)
const showReviewForm = ref(false)
const reviewCategories = [
  { key: 'voice_quality', label: 'Качество озвучки' },
  { key: 'timing', label: 'Синхронизация' },
  { key: 'translation', label: 'Перевод' },
  { key: 'consistency', label: 'Постоянство' },
]
const newReview = ref<any>({ voice_quality: 5, timing: 5, translation: 5, consistency: 5, comment: '' })

// Similar
const similar = ref<any[]>([])
const similarLoading = ref(false)

// Computed
const ratingDistribution = computed(() => {
  if (!group.value) return {}
  const dist = group.value.rating_distribution || {}
  return Object.fromEntries([5, 4, 3, 2, 1].map(k => [k, dist[k] || 0]))
})

const genreStats = computed(() => {
  if (!group.value?.genre_stats) return []
  return Object.entries(group.value.genre_stats)
    .map(([name, pct]) => ({ name, pct: Number(pct) }))
    .sort((a, b) => b.pct - a.pct)
    .slice(0, 8)
})

// Methods
const fetchGroup = async () => {
  isLoading.value = true
  try {
    const res = await dubGroupsApi.getGroup(slug.value)
    group.value = res.data
  } catch (e) {
    group.value = null
  } finally {
    isLoading.value = false
  }
}

const fetchWorks = async () => {
  worksLoading.value = true
  try {
    const res = await dubGroupsApi.getWorks(slug.value, { page_size: 50 })
    works.value = res.data.results || []
  } catch (e) {}
  finally { worksLoading.value = false }
}

const fetchStaff = async () => {
  staffLoading.value = true
  try {
    const res = await dubGroupsApi.getStaff(slug.value)
    staff.value = res.data || []
  } catch (e) {} finally { staffLoading.value = false }
}

const fetchNews = async () => {
  newsLoading.value = true
  try {
    const res = await dubGroupsApi.getNews(slug.value)
    news.value = (res.data as any).results || []
  } catch (e) {} finally { newsLoading.value = false }
}

const fetchDiscussions = async () => {
  discussionsLoading.value = true
  try {
    const res = await dubGroupsApi.getDiscussions(slug.value, discussionOrdering.value)
    discussions.value = (res.data as any).results || []
  } catch (e) {} finally { discussionsLoading.value = false }
}

const fetchReviews = async () => {
  reviewsLoading.value = true
  try {
    const res = await dubGroupsApi.getReviews(slug.value)
    reviews.value = (res.data as any).results || []
  } catch (e) {} finally { reviewsLoading.value = false }
}

const fetchSimilar = async () => {
  similarLoading.value = true
  try {
    const res = await dubGroupsApi.getSimilar(slug.value)
    similar.value = res.data || []
  } catch (e) {} finally { similarLoading.value = false }
}

const toggleSubscribe = async () => {
  if (!group.value) return
  try {
    if (group.value.is_subscribed) {
      const res = await dubGroupsApi.unsubscribe(slug.value)
      group.value.is_subscribed = false
      group.value.subscribers_count = res.data.subscribers_count
    } else {
      const res = await dubGroupsApi.subscribe(slug.value)
      group.value.is_subscribed = true
      group.value.subscribers_count = res.data.subscribers_count
    }
  } catch (e) {}
}

const createDiscussion = async () => {
  if (!newDiscTitle.value || !newDiscContent.value) return
  try {
    await dubGroupsApi.createDiscussion(slug.value, { title: newDiscTitle.value, content: newDiscContent.value })
    newDiscTitle.value = ''
    newDiscContent.value = ''
    showDiscussionForm.value = false
    fetchDiscussions()
  } catch (e) {}
}

const openDiscussion = async (disc: DubGroupDiscussion) => {
  if (activeDiscussion.value?.id === disc.id) {
    activeDiscussion.value = null
    return
  }
  activeDiscussion.value = disc
  replyContent.value = ''
  if (!discReplies.value[disc.id]) {
    try {
      const res = await dubGroupsApi.getDiscussionReplies(slug.value, disc.id)
      discReplies.value[disc.id] = res.data || []
    } catch (e) {
      discReplies.value[disc.id] = []
    }
  }
}

const likeDiscussion = async (disc: any) => {
  try {
    const res = await dubGroupsApi.likeDiscussion(slug.value, disc.id)
    disc.likes_count = res.data.likes_count ?? disc.likes_count
    disc.liked = res.data.liked
  } catch (e) {}
}

const dislikeDiscussion = async (disc: any) => {
  try {
    const res = await dubGroupsApi.dislikeDiscussion(slug.value, disc.id)
    disc.dislikes_count = res.data.dislikes_count ?? disc.dislikes_count
    disc.disliked = res.data.disliked
  } catch (e) {}
}

const submitReply = async (disc: DubGroupDiscussion) => {
  if (!replyContent.value.trim()) return
  try {
    const res = await dubGroupsApi.createDiscussionReply(slug.value, disc.id, replyContent.value)
    if (!discReplies.value[disc.id]) discReplies.value[disc.id] = []
    discReplies.value[disc.id]!.push(res.data)
    disc.replies_count++
    replyContent.value = ''
  } catch (e) {}
}

const submitReview = async () => {
  try {
    await dubGroupsApi.createReview(slug.value, newReview.value)
    showReviewForm.value = false
    newReview.value = { voice_quality: 5, timing: 5, translation: 5, consistency: 5, comment: '' }
    fetchReviews()
    fetchGroup()
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

const getTranslationTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    voice: '🎤 Озвучка',
    subtitles: '📝 Субтитры',
    both: '🎤📝 Оба',
  }
  return map[type] || type
}

// Lazy load tab data
watch(activeTab, (tab) => {
  if (tab === 'works' && works.value.length === 0) fetchWorks()
  if (tab === 'staff' && staff.value.length === 0) fetchStaff()
  if (tab === 'news' && news.value.length === 0) fetchNews()
  if (tab === 'discussions' && discussions.value.length === 0) fetchDiscussions()
  if (tab === 'reviews' && reviews.value.length === 0) fetchReviews()
  if (tab === 'similar' && similar.value.length === 0) fetchSimilar()
})

watch(slug, () => {
  fetchGroup()
})

onMounted(() => {
  fetchGroup()
})
</script>

<style scoped>
.dub-group-page {
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
  margin: 0 0 1rem;
  color: var(--color-text);
}

/* Rating Overview */
.rating-overview {
  display: flex;
  gap: 2rem;
  align-items: center;
}
.rating-big {
  font-size: 3rem;
  font-weight: 900;
  color: #f59e0b;
}
.rating-bars {
  flex: 1;
}
.rating-bar-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.375rem;
  font-size: 0.8rem;
}
.bar-label { width: 30px; color: var(--color-text-secondary); }
.bar-track { flex: 1; height: 8px; background: var(--color-background-active); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; background: #f59e0b; border-radius: 4px; transition: width 0.3s; }
.bar-pct { width: 35px; text-align: right; color: var(--color-text-secondary); font-size: 0.75rem; }

/* Description */
.description-text {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Genre bars */
.genre-bars { display: flex; flex-direction: column; gap: 0.5rem; }
.genre-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
.genre-name { width: 100px; color: var(--color-text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.genre-track { flex: 1; height: 6px; background: var(--color-background-active); border-radius: 3px; overflow: hidden; }
.genre-fill { height: 100%; background: var(--color-accent); border-radius: 3px; }
.genre-pct { width: 35px; text-align: right; color: var(--color-text-secondary); }

/* Works Grid */
.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 1rem;
}
.work-card {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  overflow: hidden;
  text-decoration: none;
  transition: all 0.2s;
}
.work-card:hover { transform: translateY(-2px); border-color: var(--color-accent); }
.work-poster { position: relative; aspect-ratio: 2/3; background: var(--color-background-active); }
.work-poster img { width: 100%; height: 100%; object-fit: cover; }
.poster-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; color: var(--color-text-tertiary); }
.work-info { padding: 0.5rem; }
.work-title { font-size: 0.8rem; font-weight: 600; color: var(--color-text); margin-bottom: 0.25rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.work-meta { display: flex; gap: 0.5rem; font-size: 0.7rem; color: var(--color-text-secondary); }
.work-score { color: #f59e0b; display: flex; align-items: center; gap: 0.125rem; }

/* Staff Grid */
.staff-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 1rem; }
.staff-card { background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 0.5rem; padding: 1rem; text-align: center; }
.staff-photo { width: 60px; height: 60px; border-radius: 50%; overflow: hidden; margin: 0 auto 0.5rem; background: var(--color-background-active); display: flex; align-items: center; justify-content: center; }
.staff-photo-img { width: 100%; height: 100%; object-fit: cover; }
.staff-photo-placeholder { font-size: 1.25rem; font-weight: 700; color: var(--color-text-tertiary); }
.staff-card-name { font-size: 0.85rem; font-weight: 600; color: var(--color-text); margin-bottom: 0.25rem; }
.staff-card-works { font-size: 0.7rem; color: var(--color-text-secondary); }

/* News List */
.news-list { display: flex; flex-direction: column; gap: 1rem; }
.news-card { background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 0.75rem; padding: 1rem; }
.news-date { font-size: 0.75rem; color: var(--color-text-secondary); margin-bottom: 0.5rem; }
.news-title { font-size: 1rem; font-weight: 700; margin: 0 0 0.5rem; color: var(--color-text); }
.news-preview { font-size: 0.85rem; color: var(--color-text-secondary); margin: 0 0 0.75rem; line-height: 1.5; }
.news-footer { display: flex; gap: 1rem; font-size: 0.75rem; color: var(--color-text-tertiary); }

/* Discussions */
.discussions-toolbar { display: flex; gap: 1rem; margin-bottom: 1rem; align-items: center; }
.new-disc-btn { padding: 0.5rem 1rem; background: var(--color-accent); color: #fff; border: none; border-radius: 0.5rem; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.works-select { padding: 0.5rem; background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 0.5rem; font-size: 0.85rem; color: var(--color-text); }
.disc-form { background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 0.75rem; padding: 1rem; margin-bottom: 1rem; }
.disc-input { width: 100%; padding: 0.625rem; background: var(--color-background-active); border: 1px solid var(--color-divider-light); border-radius: 0.5rem; font-size: 0.9rem; color: var(--color-text); margin-bottom: 0.75rem; box-sizing: border-box; }
.disc-textarea { width: 100%; padding: 0.625rem; background: var(--color-background-active); border: 1px solid var(--color-divider-light); border-radius: 0.5rem; font-size: 0.9rem; color: var(--color-text); resize: vertical; box-sizing: border-box; }
.disc-form-actions { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
.submit-btn { padding: 0.5rem 1rem; background: var(--color-accent); color: #fff; border: none; border-radius: 0.5rem; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.cancel-btn { padding: 0.5rem 1rem; background: var(--color-background-active); color: var(--color-text-secondary); border: 1px solid var(--color-divider-light); border-radius: 0.5rem; font-size: 0.85rem; cursor: pointer; }
.discussions-list { display: flex; flex-direction: column; gap: 1rem; }
.discussion-card { display: flex; gap: 0.75rem; background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 0.75rem; padding: 1rem; }
.discussion-card.pinned { border-color: #f59e0b; background: rgba(245, 158, 11, 0.05); }
.disc-author-avatar { flex-shrink: 0; width: 40px; height: 40px; border-radius: 50%; overflow: hidden; background: var(--color-background-active); display: flex; align-items: center; justify-content: center; }
.disc-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.disc-avatar-placeholder { font-size: 1rem; font-weight: 700; color: var(--color-text-tertiary); }
.disc-body { flex: 1; min-width: 0; }
.disc-header { display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; margin-bottom: 0.375rem; }
.disc-author { font-weight: 600; color: var(--color-accent); }
.disc-pin-badge { color: #f59e0b; font-size: 0.7rem; }
.disc-time { color: var(--color-text-tertiary); }
.disc-title { font-size: 1rem; font-weight: 700; margin: 0 0 0.375rem; color: var(--color-text); }
.disc-preview { font-size: 0.85rem; color: var(--color-text-secondary); margin: 0 0 0.75rem; }
.disc-actions { display: flex; gap: 0.75rem; align-items: center; }
.disc-action-btn { background: none; border: none; font-size: 0.8rem; color: var(--color-text-secondary); cursor: pointer; display: flex; align-items: center; gap: 0.25rem; }
.disc-action-btn:hover { color: var(--color-text); }
.disc-action-btn.active { color: var(--color-accent); }
.disc-reply-form { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--color-divider-light); }
.disc-replies { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.75rem; }
.disc-reply-item { display: flex; gap: 0.5rem; }
.disc-reply-avatar { width: 28px; height: 28px; border-radius: 50%; overflow: hidden; background: var(--color-background-active); flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.disc-reply-body { flex: 1; }
.disc-reply-author { font-weight: 600; font-size: 0.8rem; color: var(--color-accent); margin-right: 0.5rem; }
.disc-reply-time { font-size: 0.7rem; color: var(--color-text-tertiary); }
.disc-reply-text { font-size: 0.85rem; color: var(--color-text); margin: 0.25rem 0 0; }

/* Reviews */
.reviews-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.review-overall { display: flex; align-items: center; gap: 0.75rem; }
.review-score { font-size: 2rem; font-weight: 900; color: #f59e0b; }
.stars-lg { display: flex; gap: 0.125rem; }
.star-lg { font-size: 1.25rem; color: var(--color-divider-light); }
.star-lg.filled { color: #f59e0b; }
.leave-review-btn { padding: 0.5rem 1rem; background: var(--color-accent); color: #fff; border: none; border-radius: 0.5rem; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.review-form { background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 0.75rem; padding: 1rem; margin-bottom: 1rem; }
.category-ratings { margin-bottom: 1rem; }
.cat-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; }
.cat-label { font-size: 0.85rem; color: var(--color-text-secondary); }
.cat-stars { display: flex; gap: 0.25rem; }
.cat-star { font-size: 1.25rem; color: var(--color-divider-light); cursor: pointer; }
.cat-star.filled { color: #f59e0b; }
.reviews-list { display: flex; flex-direction: column; gap: 1rem; }
.review-card { background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 0.75rem; padding: 1rem; }
.review-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.review-user-info { display: flex; align-items: center; gap: 0.5rem; }
.review-avatar { width: 32px; height: 32px; border-radius: 50%; overflow: hidden; background: var(--color-background-active); display: flex; align-items: center; justify-content: center; }
.review-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.review-avatar-placeholder { font-size: 0.875rem; font-weight: 700; color: var(--color-text-tertiary); }
.review-user { font-weight: 600; font-size: 0.85rem; color: var(--color-text); }
.review-date { font-size: 0.75rem; color: var(--color-text-tertiary); }
.review-overall-badge { display: inline-block; padding: 0.25rem 0.5rem; background: rgba(245, 158, 11, 0.1); border-radius: 0.25rem; font-size: 0.8rem; font-weight: 600; color: #f59e0b; margin-bottom: 0.5rem; }
.review-cats { display: flex; flex-wrap: wrap; gap: 0.75rem; font-size: 0.8rem; color: var(--color-text-secondary); margin-bottom: 0.5rem; }
.review-cats b { color: var(--color-text); }
.review-comment { font-size: 0.9rem; color: var(--color-text); margin: 0; line-height: 1.5; }

/* Similar */
.similar-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1rem; }
.similar-card { background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 0.75rem; padding: 1rem; text-align: center; text-decoration: none; transition: all 0.2s; }
.similar-card:hover { transform: translateY(-2px); border-color: var(--color-accent); }
.similar-logo { width: 60px; height: 60px; border-radius: 0.5rem; overflow: hidden; margin: 0 auto 0.75rem; background: var(--color-background-active); display: flex; align-items: center; justify-content: center; }
.similar-logo-img { width: 100%; height: 100%; object-fit: contain; }
.similar-logo-placeholder { font-size: 1.5rem; font-weight: 700; color: var(--color-text-tertiary); }
.similar-name { font-size: 0.9rem; font-weight: 600; color: var(--color-text); margin-bottom: 0.25rem; }
.similar-rating { font-size: 0.8rem; color: #f59e0b; display: flex; align-items: center; justify-content: center; gap: 0.25rem; }
.similar-count { font-size: 0.7rem; color: var(--color-text-secondary); }

/* Sidebar */
.studio-sidebar { display: flex; flex-direction: column; gap: 1rem; }
.sidebar-card { background: var(--color-background-surface); border: 1px solid var(--color-divider-light); border-radius: 0.75rem; padding: 1rem; }
.sidebar-title { font-size: 0.9rem; font-weight: 700; margin: 0 0 0.75rem; color: var(--color-text); }
.stat-row { display: flex; justify-content: space-between; font-size: 0.85rem; padding: 0.375rem 0; border-bottom: 1px solid var(--color-divider-light); }
.stat-row:last-child { border-bottom: none; }
.stat-row span { color: var(--color-text-secondary); }
.stat-row b { color: var(--color-text); }
.best-work-link { display: flex; gap: 0.75rem; text-decoration: none; }
.best-work-poster { width: 50px; flex-shrink: 0; border-radius: 0.375rem; overflow: hidden; aspect-ratio: 2/3; background: var(--color-background-active); }
.best-poster-img { width: 100%; height: 100%; object-fit: cover; }
.best-work-info { flex: 1; min-width: 0; }
.best-title { font-size: 0.85rem; font-weight: 600; color: var(--color-text); margin-bottom: 0.25rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.best-score { font-size: 0.8rem; color: #f59e0b; }
.genre-tag-row { display: flex; justify-content: space-between; font-size: 0.8rem; padding: 0.25rem 0; }
.genre-tag { color: var(--color-accent); }
.genre-tag-pct { color: var(--color-text-secondary); }

/* Type Badge */
.type-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}
.type-badge.voice { background: #10b98122; color: #10b981; }
.type-badge.subtitles { background: #f59e0b22; color: #f59e0b; }
.type-badge.both { background: #8b5cf622; color: #8b5cf6; }

/* Empty & Loading */
.empty-tab, .loading-indicator {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-secondary);
}
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem 2rem;
  color: var(--color-text-tertiary);
  gap: 0.75rem;
}
.back-link {
  color: var(--color-accent);
  text-decoration: none;
}
.back-link:hover { text-decoration: underline; }

/* Responsive */
@media (max-width: 900px) {
  .studio-body { grid-template-columns: 1fr; }
  .studio-sidebar { display: none; }
}
</style>
