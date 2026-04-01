<template>
  <div class="feed-page">
    <div class="container">
      <!-- Feed Header with Tabs -->
      <div class="feed-header">
        <div class="feed-tabs">
          <button
            v-for="tab in feedTabs"
            :key="tab.id"
            @click="switchTab(tab.id)"
            :class="['tab-btn', { active: activeTab === tab.id }]"
          >
            {{ tab.label }}
            <span v-if="tab.id === 'feed' && newPostsCount > 0" class="new-posts-badge">
              {{ newPostsCount }}
            </span>
          </button>
        </div>
        <button @click="openCreatePostModal()" class="btn-create-post">
          <span>Создать пост</span>
        </button>
      </div>

      <!-- Filters and Sort Bar (only for Feed tab) -->
      <div v-if="activeTab === 'feed'" class="filters-bar">
        <div class="filters-section">
          <button @click="showFilters = !showFilters" class="filter-toggle">
            <span>Фильтры</span>
            <span class="arrow" :class="{ open: showFilters }">▼</span>
          </button>
          
          <!-- Collapsible Filters -->
          <div v-if="showFilters" class="filters-dropdown">
            <div class="filter-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="filters.myPosts" @change="applyFilters">
                Мои посты
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="filters.subscriptions" @change="applyFilters">
                Подписки
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="filters.groups" @change="applyFilters">
                Из групп
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="filters.withAnime" @change="applyFilters">
                С аниме
              </label>
            </div>
            
            <div class="filter-group">
              <label>За период:</label>
              <select v-model="filters.period" @change="applyFilters" class="filter-select">
                <option value="all">Всё время</option>
                <option value="month">Месяц</option>
                <option value="week">Неделя</option>
                <option value="day">День</option>
              </select>
            </div>
          </div>
        </div>

        <div class="sort-section">
          <select v-model="filters.sort" @change="applyFilters" class="sort-select">
            <option value="new">Новые</option>
            <option value="old">Старые</option>
            <option value="best">Лучшие</option>
            <option value="discussed">Обсуждаемые</option>
          </select>
        </div>
      </div>

      <!-- Active Filters Tags -->
      <div v-if="activeTab === 'feed' && activeFilterTags.length > 0" class="active-filters">
        <span 
          v-for="tag in activeFilterTags" 
          :key="tag.key" 
          class="filter-tag"
          @click="removeFilter(tag.key)"
        >
          {{ tag.label }} ✕
        </span>
        <button class="clear-all" @click="clearAllFilters">Очистить всё</button>
      </div>

      <div class="feed-layout">
        <!-- Main Content Area -->
        <main class="feed-main">
          <!-- SUBSCRIPTIONS TAB - Shows profile cards with sub-tabs -->
          <div v-if="activeTab === 'subscriptions'" class="subscriptions-tab">
            <!-- Sub-tabs -->
            <div class="sub-tabs">
              <button
                :class="['sub-tab-btn', { active: subscriptionsSubTab === 'profiles' }]"
                @click="subscriptionsSubTab = 'profiles'"
              >
                👤 Профили
              </button>
              <button
                :class="['sub-tab-btn', { active: subscriptionsSubTab === 'favorites' }]"
                @click="subscriptionsSubTab = 'favorites'; loadFavoritePosts()"
              >
                ⭐ Избранные посты
              </button>
            </div>
            
            <!-- Profiles Sub-tab -->
            <div v-if="subscriptionsSubTab === 'profiles'">
              <div class="tab-header">
                <input
                  v-model="subscriptionsSearch"
                  placeholder="Поиск подписок..."
                  class="search-input"
                  @input="debouncedSearchSubscriptions"
                >
                <select v-model="subscriptionsSort" @change="loadSubscriptions" class="sort-select">
                  <option value="date">По дате</option>
                  <option value="name">По имени</option>
                  <option value="activity">По активности</option>
                </select>
              </div>

              <div v-if="loadingSubscriptions" class="loading-state">
                <div class="skeleton-user" v-for="i in 5" :key="i">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line short"></div>
                  </div>
                </div>
              </div>

              <div v-else-if="subscriptions.length === 0" class="empty-state">
                <div class="empty-icon">👥</div>
                <h3>Нет подписок</h3>
                <p>Подпишитесь на интересных авторов!</p>
              </div>

              <div v-else class="subscriptions-grid">
                <div v-for="user in subscriptions" :key="user.id" class="subscription-card clickable" @click="goToProfile(user.id)">
                  <img :src="user.avatar_url || user.avatar || defaultAvatar" class="avatar-lg" alt="">
                  <div class="user-info">
                    <h4>{{ user.display_name || user.username }}</h4>
                    <span class="username">@{{ user.username }}</span>
                    <span class="followers">{{ user.followers_count || 0 }} подписчиков</span>
                  </div>
                  <div class="user-actions" @click.stop>
                    <button class="btn-following" @click="unfollowUser(user.id)">
                      ✓ Подписан
                    </button>
                    <button class="btn-message" @click="openChat(user.id)">
                      💬
                    </button>
                  </div>
                </div>
              </div>

              <div v-if="hasMoreSubscriptions" class="load-more">
                <button @click="loadMoreSubscriptions" :disabled="loadingMoreSubscriptions" class="btn-load-more">
                  {{ loadingMoreSubscriptions ? 'Загрузка...' : 'Загрузить ещё' }}
                </button>
              </div>
            </div>

            <!-- Favorites Posts Sub-tab -->
            <div v-else-if="subscriptionsSubTab === 'favorites'">
              <div v-if="loadingFavoritePosts" class="loading-state">
                <div class="skeleton-post" v-for="i in 3" :key="i">
                  <div class="skeleton-header">
                    <div class="skeleton-avatar"></div>
                    <div class="skeleton-info">
                      <div class="skeleton-line short"></div>
                      <div class="skeleton-line"></div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else-if="favoritePosts.length === 0" class="empty-state">
                <div class="empty-icon">⭐</div>
                <h3>Нет избранных постов</h3>
                <p>Добавляйте посты в избранное, чтобы они появились здесь</p>
              </div>

              <div v-else class="posts-list">
                <PostCard
                  v-for="post in favoritePosts"
                  :key="post.id"
                  :post="post"
                  @like="handleLike"
                  @dislike="handleDislike"
                  @bookmark="toggleBookmark"
                  @menu="openPostMenu"
                />
              </div>
            </div>
          </div>

          <!-- BOOKMARKS TAB — Избранные посты -->
          <div v-else-if="activeTab === 'bookmarks'" class="bookmarks-tab">
            <div class="tab-header">
              <input
                v-model="bookmarkSearch"
                placeholder="Поиск в сохранённых..."
                class="search-input"
              >
            </div>
            <div v-if="loadingBookmarks" class="loading-state">
              <div class="skeleton-post" v-for="i in 4" :key="i">
                <div class="skeleton-header">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-line"></div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="filteredBookmarks.length === 0" class="empty-state">
              <div class="empty-icon">★</div>
              <h3>Нет избранных постов</h3>
              <p>Добавляйте посты в избранное, чтобы они появились здесь</p>
            </div>
            <div v-else class="posts-list">
              <PostCard
                v-for="post in filteredBookmarks"
                :key="post.id"
                :post="post"
                @like="handleLike"
                @dislike="handleDislike"
                @bookmark="toggleBookmark"
                @menu="openPostMenu"
                @repost="openRepostModal"
                @comment="openComments"
              />
            </div>
          </div>

          <!-- PINNED TAB — Закреплённые посты -->
          <div v-else-if="activeTab === 'pinned'" class="pinned-tab">
            <div v-if="loadingPinned" class="loading-state">
              <div class="skeleton-post" v-for="i in 3" :key="i">
                <div class="skeleton-header">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-line"></div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="pinnedPosts.length === 0" class="empty-state">
              <div class="empty-icon">📌</div>
              <h3>Нет закреплённых постов</h3>
              <p>Закрепляйте посты через меню поста, чтобы они появились здесь</p>
            </div>
            <div v-else class="posts-list">
              <div v-for="post in pinnedPosts" :key="post.id" class="pinned-post-wrapper">
                <PostCard
                  :post="post"
                  @like="handleLike"
                  @dislike="handleDislike"
                  @bookmark="toggleBookmark"
                  @menu="openPostMenu"
                  @repost="openRepostModal"
                  @comment="openComments"
                />
                <button class="btn-unpin" @click="unpinPostFromTab(post)">📌 Открепить</button>
              </div>
            </div>
          </div>

          <!-- NOT INTERESTED TAB -->
          <div v-else-if="activeTab === 'not_interested'" class="not-interested-tab">
            <!-- Sub-tabs -->
            <div class="sub-tabs">
              <button
                :class="['sub-tab-btn', { active: notInterestedSubTab === 'profiles' }]"
                @click="notInterestedSubTab = 'profiles'"
              >
                👤 Скрытые профили
              </button>
              <button
                :class="['sub-tab-btn', { active: notInterestedSubTab === 'posts' }]"
                @click="notInterestedSubTab = 'posts'; loadHiddenPosts()"
              >
                📝 Скрытые посты
              </button>
            </div>

            <!-- Profiles Sub-tab -->
            <div v-if="notInterestedSubTab === 'profiles'">
              <div class="tab-header">
                <input
                  v-model="notInterestedSearch"
                  placeholder="Поиск скрытых..."
                  class="search-input"
                  @input="debouncedSearchNotInterested"
                >
              </div>

              <div v-if="loadingNotInterested" class="loading-state">
                <div class="skeleton-user" v-for="i in 3" :key="i">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line short"></div>
                  </div>
                </div>
              </div>

              <div v-else-if="notInterestedUsers.length === 0" class="empty-state">
                <div class="empty-icon">🙈</div>
                <h3>Нет скрытых профилей</h3>
                <p>Профили, которые вы скроете, появятся здесь</p>
              </div>

              <div v-else class="subscriptions-grid">
                <div v-for="user in notInterestedUsers" :key="user.id" class="subscription-card blocked clickable" @click="goToProfile(user.id)">
                  <img :src="user.avatar_url || user.avatar || defaultAvatar" class="avatar-lg" alt="">
                  <div class="user-info">
                    <h4>{{ user.display_name || user.username }}</h4>
                    <span class="username">@{{ user.username }}</span>
                    <span class="hidden-date">🚫 Заблокирован: {{ formatDate(user.hidden_at) }}</span>
                    <span v-if="user.reason" class="reason">{{ user.reason }}</span>
                  </div>
                  <div class="user-actions" @click.stop>
                    <button class="btn-unblock" @click="unhideUser(user.id)">
                      Разблокировать
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Posts Sub-tab -->
            <div v-else-if="notInterestedSubTab === 'posts'">
              <div v-if="loadingHiddenPosts" class="loading-state">
                <div class="skeleton-post" v-for="i in 3" :key="i">
                  <div class="skeleton-header">
                    <div class="skeleton-avatar"></div>
                    <div class="skeleton-info">
                      <div class="skeleton-line short"></div>
                      <div class="skeleton-line"></div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else-if="hiddenPosts.length === 0" class="empty-state">
                <div class="empty-icon">📝</div>
                <h3>Нет скрытых постов</h3>
                <p>Посты, которые вы отметите как "Не интересно", появятся здесь</p>
              </div>

              <div v-else class="posts-list">
                <div v-for="item in hiddenPosts" :key="item.id" class="hidden-post-card">
                  <div class="hidden-post-info" @click="openHiddenPost(item)">
                    <span class="hidden-post-title">{{ item.post_preview || 'Пост #' + item.post_id }}</span>
                    <span class="hidden-date">Скрыт: {{ formatDate(item.hidden_at) }}</span>
                  </div>
                  <button class="btn-restore" @click="restorePost(item.post_id)">
                    Восстановить
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- POPULAR TAB - Shows popular posts -->
          <div v-else-if="activeTab === 'popular'" class="popular-tab">
            <div class="tab-header">
              <select v-model="popularPeriod" @change="loadPopularPosts" class="sort-select">
                <option value="day">За день</option>
                <option value="week">За неделю</option>
                <option value="month">За месяц</option>
                <option value="all">За всё время</option>
              </select>
            </div>

            <div v-if="loadingPopular" class="loading-state">
              <div class="skeleton-post" v-for="i in 5" :key="i">
                <div class="skeleton-header">
                  <div class="skeleton-avatar"></div>
                  <div class="skeleton-info">
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-line"></div>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="popularPosts.length === 0" class="empty-state">
              <div class="empty-icon">🔥</div>
              <h3>Нет популярных постов</h3>
              <p>Популярные посты появятся здесь</p>
            </div>

            <div v-else class="posts-list">
              <PostCard
                v-for="(post, index) in popularPosts"
                :key="post.id"
                :post="post"
                @like="handleLike"
                @dislike="handleDislike"
                @bookmark="toggleBookmark"
                @menu="openPostMenu"
              />
            </div>
          </div>

          <!-- REPORTS TAB - For moderators -->
          <div v-else-if="activeTab === 'reports'" class="reports-tab">
            <div class="tab-header">
              <select v-model="reportsFilter.status" @change="loadReports" class="filter-select">
                <option value="">Все статусы</option>
                <option value="pending">Новые</option>
                <option value="in_progress">В процессе</option>
                <option value="resolved">Рассмотренные</option>
              </select>
              <select v-model="reportsFilter.reason" @change="loadReports" class="filter-select">
                <option value="">Все причины</option>
                <option value="copyright">Авторские права</option>
                <option value="inappropriate">Неприемлемый контент</option>
                <option value="spam">Спам</option>
                <option value="harassment">Оскорбления</option>
                <option value="spoiler">Спойлер</option>
                <option value="other">Другое</option>
              </select>
            </div>
            
            <div v-if="loadingReports" class="loading-state">
              <div class="skeleton-report" v-for="i in 3" :key="i">
                <div class="skeleton-line"></div>
                <div class="skeleton-line medium"></div>
              </div>
            </div>
            
            <div v-else-if="reports.length === 0" class="empty-state">
              <div class="empty-icon">📋</div>
              <h3>Нет жалоб</h3>
              <p>Нет жалоб для рассмотрения</p>
            </div>
            
            <div v-else class="reports-list">
              <div v-for="report in reports" :key="report.id" class="report-card">
                <div class="report-header">
                  <span class="report-type">{{ getContentTypeLabel(report.content_type) }}</span>
                  <span :class="['report-status', report.status]">{{ getStatusLabel(report.status) }}</span>
                </div>
                <div class="report-content">
                  <p class="report-reason">{{ getReasonLabel(report.reason) }}</p>
                  <p v-if="report.description" class="report-description">{{ report.description }}</p>
                  <div class="report-meta">
                    <span>От: {{ report.reporter?.username || 'Анон' }}</span>
                    <span>Дата: {{ formatDate(report.created_at) }}</span>
                  </div>
                </div>
                <div class="report-actions">
                  <button class="btn-review" @click="openReportDetail(report)">
                    Рассмотреть
                  </button>
                  <button class="btn-reject" @click="rejectReport(report.id)">
                    Отклонить
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- FEED TAB - Shows posts -->
          <div v-else class="feed-tab">
            <!-- Create Post Card - simplified, no quick attachment buttons -->
            <div class="create-post-card" @click="openCreatePostModal()">
              <img :src="currentUser?.avatar || defaultAvatar" class="avatar" alt="Avatar">
              <span class="placeholder">Что у вас нового?</span>
            </div>

            <!-- Posts Feed -->
            <div class="posts-list" ref="postsContainer">
              <!-- Loading State -->
              <div v-if="loading && posts.length === 0" class="loading-state">
                <div class="skeleton-post" v-for="i in 3" :key="i">
                  <div class="skeleton-header">
                    <div class="skeleton-avatar"></div>
                    <div class="skeleton-info">
                      <div class="skeleton-line short"></div>
                      <div class="skeleton-line"></div>
                    </div>
                  </div>
                  <div class="skeleton-content">
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line medium"></div>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div v-else-if="!loading && posts.length === 0" class="empty-state">
                <div class="empty-icon">📝</div>
                <h3>Пока нет постов</h3>
                <p>Подпишитесь на интересных авторов или создайте свой первый пост!</p>
                <button @click="openCreatePostModal()" class="btn-primary">Создать пост</button>
              </div>

              <!-- Posts -->
              <div v-else>
                <div v-if="newPostsCount > 0" class="new-posts-bar" @click="loadNewPosts">
                  <span>Показать {{ newPostsCount }} новых постов</span>
                </div>

                <PostCard
                  v-for="post in posts"
                  :key="post.id"
                  :post="post"
                  :data-post-id="post.id"
                  @like="handleLike"
                  @dislike="handleDislike"
                  @comment="openComments"
                  @repost="openRepostModal"
                  @share="sharePost"
                  @bookmark="toggleBookmark"
                  @menu="openPostMenu"
                  @report="openReportModal"
                />

                <!-- Load More -->
                <div v-if="hasMore" class="load-more">
                  <button @click="loadMorePosts" :disabled="loadingMore" class="btn-load-more">
                    {{ loadingMore ? 'Загрузка...' : 'Показать ещё' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
        <!-- 
        <aside class="feed-right-sidebar">
          <div class="sidebar-card trending">
            <h3>🔥 Популярное</h3>
            <div class="trending-posts">
              <div v-for="trend in trendingPosts" :key="trend.id" class="trending-item" @click="openTrendingPost(trend)">
                <span class="trend-rank">{{ trend.rank }}</span>
                <div class="trend-content">
                  <span class="trend-title">{{ trend.title }}</span>
                  <span class="trend-stats">{{ trend.likes_count }} лайков</span>
                </div>
              </div>
            </div>
          </div>
        </aside> -->
      </div>
    </div>

    <!-- Modals -->
    <CreatePostModal v-if="showCreatePost" :initial-type="createPostType" @close="showCreatePost = false" @created="onPostCreated" />
    <EditPostModal v-if="showEditPost && selectedPost" :post="selectedPost" @close="showEditPost = false" @updated="onPostEdited" />
    <CommentsModal v-if="showComments" :post="selectedPost" @close="showComments = false" @comment-added="onCommentAdded" />
    <RepostModal v-if="showRepost" :post="selectedPost" @close="showRepost = false" @reposted="onReposted" />
    <PostMenu v-if="showMenu && selectedPost" :post="selectedPost" @close="showMenu = false" @edit="editPost" @delete="deletePost" @pin="pinPost" @report="openReportModal" @bookmark="toggleBookmark" @hide="hidePost" @hide-author="hidePostByAuthor" @repost="openRepostModal" @forward="openForwardModal" />
    <ForwardModal v-if="showForward && selectedPost" :post="selectedPost" @close="showForward = false" />
    <ReportModal v-if="showReport" content-type="post" :content-id="selectedPost?.id" @close="showReport = false" />
    <PostDetailModal v-if="showPostDetail" :post="selectedPost" @close="showPostDetail = false" />
    
    <!-- Report Detail Modal -->
    <div v-if="showReportDetail" class="modal-overlay" @click="showReportDetail = false">
      <div class="report-detail-modal" @click.stop>
        <div class="modal-header">
          <h3>Рассмотрение жалобы #{{ selectedReport?.id }}</h3>
          <button class="close-btn" @click="showReportDetail = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="report-full-info">
            <p><strong>Тип контента:</strong> {{ getContentTypeLabel(selectedReport?.content_type) }}</p>
            <p><strong>Причина:</strong> {{ getReasonLabel(selectedReport?.reason) }}</p>
            <p v-if="selectedReport?.description"><strong>Описание:</strong> {{ selectedReport.description }}</p>
            <p><strong>Жалобщик:</strong> {{ selectedReport?.reporter?.username }}</p>
            <p><strong>Дата:</strong> {{ formatDate(selectedReport?.created_at) }}</p>
          </div>
          <div class="report-actions-full">
            <label>Действие:</label>
            <select v-model="reportAction" class="action-select">
              <option value="delete_content">Удалить контент</option>
              <option value="warn_author">Вынести предупреждение</option>
              <option value="ban_author">Заблокировать автора</option>
            </select>
            <textarea v-model="moderationComment" placeholder="Комментарий модератора" class="comment-textarea"></textarea>
            <button class="btn-submit" @click="submitReportDecision">Принять решение</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiClient from '@/api/client'
import PostCard from '@/components/feed/PostCard.vue'
import CreatePostModal from '@/components/feed/CreatePostModal.vue'
import EditPostModal from '@/components/feed/EditPostModal.vue'
import CommentsModal from '@/components/feed/CommentsModal.vue'
import RepostModal from '@/components/feed/RepostModal.vue'
import PostMenu from '@/components/feed/PostMenu.vue'
import ForwardModal from '@/components/feed/ForwardModal.vue'
import ReportModal from '@/components/feed/ReportModal.vue'
import PostDetailModal from '@/components/feed/PostDetailModal.vue'
import type { FeedPost } from '@/api/feed'
import { postsApi, subscriptionsApi, bookmarksApi } from '@/api/feed'
import { normalizePost } from '@/utils/normalizers'

type Post = FeedPost & {
  image_file: string | null
  video_file: string | null
  is_following: boolean
}

interface User {
  id: number
  username: string
  display_name: string
  avatar: string
  followers_count?: number
  is_following: boolean
  hidden_at?: string
  reason?: string
  is_moderator?: boolean
  is_staff?: boolean
}

interface TrendingPost {
  id: number
  rank: number
  title: string
  likes_count: number
}

interface Report {
  id: number
  content_type: string
  content_id: number
  reason: string
  description?: string
  status: string
  reporter: { username: string }
  created_at: string
}

interface FilterState {
  myPosts: boolean
  subscriptions: boolean
  groups: boolean
  withAnime: boolean
  period: string
  sort: string
}

const router = useRouter()
const route = useRoute()

// State
const posts = ref<Post[]>([])
const loading = ref(true)
const loadingMore = ref(false)
const hasMore = ref(true)
const page = ref(1)
const activeTab = ref('feed')
const newPostsCount = ref(0)

// Filters
const showFilters = ref(false)
const filters = ref<FilterState>({
  myPosts: false,
  subscriptions: false,
  groups: false,
  withAnime: false,
  period: 'all',
  sort: 'new'
})

// Subscriptions tab state
const subscriptions = ref<any[]>([])
const loadingSubscriptions = ref(false)
const loadingMoreSubscriptions = ref(false)
const hasMoreSubscriptions = ref(true)
const subscriptionsPage = ref(1)
const subscriptionsSearch = ref('')
const subscriptionsSort = ref('date')
const subscriptionsSubTab = ref<'profiles' | 'favorites'>('profiles')
const favoritePosts = ref<Post[]>([])
const loadingFavoritePosts = ref(false)

// Bookmarks tab state (Избранное)
const bookmarkedPosts = ref<Post[]>([])
const loadingBookmarks = ref(false)
const bookmarkSearch = ref('')

// Pinned posts tab state
const pinnedPosts = ref<Post[]>([])
const loadingPinned = ref(false)

// Not Interested tab state
const notInterestedUsers = ref<any[]>([])
const loadingNotInterested = ref(false)
const notInterestedSearch = ref('')
const notInterestedSubTab = ref<'profiles' | 'posts'>('profiles')
const hiddenPosts = ref<any[]>([])
const loadingHiddenPosts = ref(false)

// Popular tab state
const popularPosts = ref<Post[]>([])
const loadingPopular = ref(false)
const popularPeriod = ref('week')

// Reports tab state
const reports = ref<any[]>([])
const loadingReports = ref(false)
const reportsFilter = ref({ status: '', reason: '' })
const showReportDetail = ref(false)
const selectedReport = ref<Report | null>(null)
const reportAction = ref('delete_content')
const moderationComment = ref('')

// UI State
const showCreatePost = ref(false)
const showEditPost = ref(false)
const showComments = ref(false)
const showRepost = ref(false)
const showMenu = ref(false)
const showReport = ref(false)
const showPostDetail = ref(false)
const showForward = ref(false)
const createPostType = ref<string | null>(null)

// Selected items
const selectedPost = ref<Post | null>(null)

// User
const currentUser = ref<User | null>(null)
const defaultAvatar = '/img/default-avatar.svg'

// Feed tabs
const feedTabs = computed(() => {
  const tabs = [
    { id: 'feed',        label: 'Лента' },
    { id: 'popular',     label: 'Популярное' },
    { id: 'subscriptions', label: 'Подписки' },
    // { id: 'bookmarks',   label: '★ Избранное' },
    { id: 'pinned',      label: 'Пины' },
    { id: 'not_interested', label: 'Не интересно' }
  ]
  if (currentUser.value?.is_moderator || currentUser.value?.is_staff) {
    tabs.push({ id: 'reports', label: 'Жалобы' })
  }
  return tabs
})

// Trending posts
const trendingPosts = ref<TrendingPost[]>([])

// Active filter tags
const activeFilterTags = computed(() => {
  const tags: { key: string; label: string }[] = []
  if (filters.value.myPosts) tags.push({ key: 'myPosts', label: 'Мои посты' })
  if (filters.value.subscriptions) tags.push({ key: 'subscriptions', label: 'Подписки' })
  if (filters.value.groups) tags.push({ key: 'groups', label: 'Из групп' })
  if (filters.value.withAnime) tags.push({ key: 'withAnime', label: 'С аниме' })
  if (filters.value.period !== 'all') {
    const periodLabels: Record<string, string> = { month: 'Месяц', week: 'Неделя', day: 'День' }
    const label = periodLabels[filters.value.period]
    if (label) tags.push({ key: 'period', label })
  }
  if (filters.value.sort !== 'new') {
    const sortLabels: Record<string, string> = { old: 'Старые', best: 'Лучшие', discussed: 'Обсуждаемые' }
    const label = sortLabels[filters.value.sort]
    if (label) tags.push({ key: 'sort', label })
  }
  return tags
})

// Methods
const loadPosts = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: 20,
      sort: filters.value.sort
    }
    
    if (filters.value.myPosts) params.my_posts = 'true'
    if (filters.value.subscriptions) params.subscriptions = 'true'
    if (filters.value.groups) params.groups = 'true'
    if (filters.value.withAnime) params.anime_id = 'has'
    if (filters.value.period !== 'all') params.date_range = filters.value.period
    
    const response = await apiClient.get('/social/feed/extended/', { params })
    posts.value = response.data.results || []
    newPostsCount.value = 0
    hasMore.value = !!response.data.next
  } catch (error) {
    console.error('Error loading posts:', error)
    // Fallback
    try {
      const response = await apiClient.get('/social/feed/weighted/')
      posts.value = response.data.posts || response.data.results || []
    } catch (fallbackError) {
      console.error('Fallback feed also failed:', fallbackError)
    }
  } finally {
    loading.value = false
  }
}

const loadMorePosts = async () => {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  try {
    page.value++
    const response = await apiClient.get('/social/feed/extended/', { 
      params: { page: page.value, sort: filters.value.sort } 
    })
    const newPosts = response.data.results || []
    posts.value.push(...newPosts)
    hasMore.value = !!response.data.next
  } catch (error) {
    console.error('Error loading more posts:', error)
  } finally {
    loadingMore.value = false
  }
}

const loadNewPosts = async () => {
  page.value = 1
  await loadPosts()
}

const switchTab = async (tabId: string) => {
  activeTab.value = tabId
  page.value = 1
  
  if (tabId === 'feed') {
    await loadPosts()
  } else if (tabId === 'popular') {
    await loadPopularPosts()
  } else if (tabId === 'subscriptions') {
    await loadSubscriptions()
  } else if (tabId === 'bookmarks') {
    await loadBookmarks()
  } else if (tabId === 'pinned') {
    await loadPinnedPosts()
  } else if (tabId === 'not_interested') {
    await loadNotInterested()
  } else if (tabId === 'reports') {
    await loadReports()
  }
}

// ── Избранные посты ────────────────────────────────────────
const loadBookmarks = async () => {
  loadingBookmarks.value = true
  try {
    const { data } = await bookmarksApi.getPosts()
    bookmarkedPosts.value = (data.results || []).map(normalizePost)
  } catch (e) {
    console.error('Error loading bookmarks:', e)
    bookmarkedPosts.value = []
  } finally {
    loadingBookmarks.value = false
  }
}

const filteredBookmarks = computed(() => {
  if (!bookmarkSearch.value.trim()) return bookmarkedPosts.value
  const q = bookmarkSearch.value.toLowerCase()
  return bookmarkedPosts.value.filter(p =>
    (p.text || '').toLowerCase().includes(q) ||
    (p.title || '').toLowerCase().includes(q)
  )
})

// ── Закреплённые посты ───────────────────────────────────────
const loadPinnedPosts = async () => {
  loadingPinned.value = true
  try {
    const { data } = await apiClient.get('/social/posts/', { params: { pinned: true, my_pins: true } })
    pinnedPosts.value = (data.results || []).map(normalizePost)
  } catch (e) {
    // fallback: ищем пины среди постов текущего пользователя
    try {
      const { data: me } = await apiClient.get('/users/me/')
      const { data: userPosts } = await apiClient.get('/social/posts/', { params: { author: me.id, is_pinned: true } })
      pinnedPosts.value = (userPosts.results || []).map(normalizePost)
    } catch {
      pinnedPosts.value = []
    }
  } finally {
    loadingPinned.value = false
  }
}

const unpinPostFromTab = async (post: any) => {
  try {
    await apiClient.post(`/social/posts/${post.id}/unpin/`)
    pinnedPosts.value = pinnedPosts.value.filter(p => p.id !== post.id)
  } catch (e) { console.error('Error unpinning:', e) }
}

// Popular posts methods
const loadPopularPosts = async () => {
  loadingPopular.value = true
  try {
    const params: Record<string, any> = { limit: 20 }
    if (popularPeriod.value !== 'all') {
      const now = new Date()
      let days = 7
      if (popularPeriod.value === 'day') days = 1
      else if (popularPeriod.value === 'month') days = 30
      params.days = days
    }
    const { data } = await apiClient.get('/social/feed/top/', { params })
    popularPosts.value = (data.results || data || []).map(normalizePost)
  } catch (error) {
    console.error('Error loading popular posts:', error)
    // Fallback to regular feed sorted by likes
    try {
      const { data } = await apiClient.get('/social/feed/extended/', { params: { sort: 'best', page_size: 20 } })
      popularPosts.value = (data.results || []).map(normalizePost)
    } catch (fallbackError) {
      console.error('Fallback popular feed also failed:', fallbackError)
    }
  } finally {
    loadingPopular.value = false
  }
}

// Favorite posts methods
const loadFavoritePosts = async () => {
  loadingFavoritePosts.value = true
  try {
    const { data } = await bookmarksApi.getPosts()
    favoritePosts.value = (data.results || []).map(normalizePost)
  } catch (error) {
    console.error('Error loading favorite posts:', error)
    favoritePosts.value = []
  } finally {
    loadingFavoritePosts.value = false
  }
}

// Hidden posts methods
const loadHiddenPosts = async () => {
  loadingHiddenPosts.value = true
  try {
    const { data } = await subscriptionsApi.getHiddenPosts()
    hiddenPosts.value = data.results || []
  } catch (error) {
    console.error('Error loading hidden posts:', error)
    hiddenPosts.value = []
  } finally {
    loadingHiddenPosts.value = false
  }
}

const restorePost = async (postId: number) => {
  try {
    await subscriptionsApi.restoreHiddenPost(postId)
    hiddenPosts.value = hiddenPosts.value.filter(p => p.post_id !== postId)
  } catch (error) {
    console.error('Error restoring post:', error)
  }
}

const openHiddenPost = (item: any) => {
  if (item.post_id) {
    router.push(`/post/${item.post_id}`)
  }
}

const applyFilters = () => {
  page.value = 1
  loadPosts()
}

const removeFilter = (key: string) => {
  if (key === 'myPosts') filters.value.myPosts = false
  else if (key === 'subscriptions') filters.value.subscriptions = false
  else if (key === 'groups') filters.value.groups = false
  else if (key === 'withAnime') filters.value.withAnime = false
  else if (key === 'period') filters.value.period = 'all'
  else if (key === 'sort') filters.value.sort = 'new'
  applyFilters()
}

const clearAllFilters = () => {
  filters.value = { myPosts: false, subscriptions: false, groups: false, withAnime: false, period: 'all', sort: 'new' }
  applyFilters()
}

// Subscriptions methods
const loadSubscriptions = async () => {
  loadingSubscriptions.value = true
  try {
    const { data } = await subscriptionsApi.getSubscriptions(subscriptionsPage.value, subscriptionsSearch.value, subscriptionsSort.value)
    subscriptions.value = data.results || []
    hasMoreSubscriptions.value = !!data.next
  } catch (error) {
    console.error('Error loading subscriptions:', error)
  } finally {
    loadingSubscriptions.value = false
  }
}

const loadMoreSubscriptions = async () => {
  if (loadingMoreSubscriptions.value || !hasMoreSubscriptions.value) return
  loadingMoreSubscriptions.value = true
  try {
    subscriptionsPage.value++
    const { data } = await subscriptionsApi.getSubscriptions(subscriptionsPage.value, subscriptionsSearch.value, subscriptionsSort.value)
    subscriptions.value.push(...(data.results || []))
    hasMoreSubscriptions.value = !!data.next
  } catch (error) {
    console.error('Error loading more subscriptions:', error)
  } finally {
    loadingMoreSubscriptions.value = false
  }
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null
const debouncedSearchSubscriptions = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    subscriptionsPage.value = 1
    loadSubscriptions()
  }, 300)
}

const unfollowUser = async (userId: number) => {
  try {
    await subscriptionsApi.unfollow(userId)
    subscriptions.value = subscriptions.value.filter(u => u.id !== userId)
  } catch (error) {
    console.error('Error unfollowing:', error)
  }
}

const openChat = (userId: number) => {
  router.push(`/chats?user=${userId}`)
}

// Not Interested methods
const loadNotInterested = async () => {
  loadingNotInterested.value = true
  try {
    const { data } = await subscriptionsApi.getNotInterested(1, notInterestedSearch.value)
    notInterestedUsers.value = data.results || []
  } catch (error) {
    console.error('Error loading not interested:', error)
  } finally {
    loadingNotInterested.value = false
  }
}

const debouncedSearchNotInterested = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadNotInterested()
  }, 300)
}

const unhideUser = async (userId: number) => {
  try {
    await subscriptionsApi.removeNotInterested(userId)
    notInterestedUsers.value = notInterestedUsers.value.filter(u => u.id !== userId)
  } catch (error) {
    console.error('Error unhiding user:', error)
  }
}

const goToProfile = (userId: number) => {
  router.push(`/profile/${userId}`)
}

// Reports methods
const loadReports = async () => {
  loadingReports.value = true
  try {
    const { data } = await subscriptionsApi.getReports({
      status: reportsFilter.value.status || undefined,
      reason: reportsFilter.value.reason || undefined
    })
    reports.value = data.results || []
  } catch (error) {
    console.error('Error loading reports:', error)
  } finally {
    loadingReports.value = false
  }
}

const openReportDetail = (report: Report) => {
  selectedReport.value = report
  showReportDetail.value = true
}

const rejectReport = async (reportId: number) => {
  try {
    await subscriptionsApi.rejectReport(reportId)
    reports.value = reports.value.filter(r => r.id !== reportId)
  } catch (error) {
    console.error('Error rejecting report:', error)
  }
}

const submitReportDecision = async () => {
  if (!selectedReport.value) return
  try {
    await subscriptionsApi.resolveReport(selectedReport.value.id, reportAction.value, moderationComment.value)
    showReportDetail.value = false
    loadReports()
  } catch (error) {
    console.error('Error resolving report:', error)
  }
}

const getContentTypeLabel = (type?: string) => {
  const labels: Record<string, string> = { post: 'Пост', comment: 'Комментарий', user: 'Пользователь' }
  return labels[type || ''] || type
}

const getStatusLabel = (status?: string) => {
  const labels: Record<string, string> = { pending: 'Новая', in_progress: 'В процессе', resolved: 'Рассмотрена', rejected: 'Отклонена' }
  return labels[status || ''] || status
}

const getReasonLabel = (reason?: string) => {
  const labels: Record<string, string> = { copyright: 'Авторские права', inappropriate: 'Неприемлемый контент', spam: 'Спам', harassment: 'Оскорбления', spoiler: 'Спойлер', other: 'Другое' }
  return labels[reason || ''] || reason
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('ru-RU')
}

// Post actions
const openCreatePostModal = (type?: string) => {
  createPostType.value = type || null
  showCreatePost.value = true
}

const handleCreateImage = () => openCreatePostModal('image')
const handleCreateVideo = () => openCreatePostModal('video')
const handleCreatePlaylist = () => openCreatePostModal('playlist')
const handleCreateAnime = () => openCreatePostModal('anime')

const openComments = (post: any) => { selectedPost.value = post; showComments.value = true }
const openRepostModal = (post: any) => { selectedPost.value = post; showRepost.value = true }
const openPostMenu = (post: any) => { selectedPost.value = post; showMenu.value = true }
const openReportModal = (post: any) => { selectedPost.value = post; showReport.value = true }
// Removed: clicking on post should NOT open modal
// const openPostDetail = (post: any) => { selectedPost.value = post; showPostDetail.value = true }

// Load specific post from route and scroll to it
const loadPostFromRoute = async () => {
  const postId = route.params.id || route.name === 'post-detail' ? route.params.id : null
  if (!postId) return

  try {
    // Load the specific post
    const { data } = await apiClient.get(`/social/posts/${postId}/`)
    const post = normalizePost(data)

    // Load feed posts if not loaded
    if (posts.value.length === 0) {
      await loadPosts()
    }

    // Check if post is already in the list
    const existingIndex = posts.value.findIndex(p => p.id === Number(postId))
    if (existingIndex === -1) {
      // Add post to the beginning of the list
      posts.value.unshift(post)
    }

    // Wait for DOM update
    await nextTick()

    // Scroll to the post
    setTimeout(() => {
      const postElement = document.querySelector(`[data-post-id="${postId}"]`)
      if (postElement) {
        postElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        postElement.classList.add('highlight-post')
        setTimeout(() => postElement.classList.remove('highlight-post'), 3000)
      }
    }, 100)
  } catch (error) {
    console.error('Error loading post from route:', error)
    // Fallback: just load the feed
    await loadPosts()
  }
}

const openTrendingPost = (trend: TrendingPost) => {
  const post: Post = {
    id: trend.id, author: 0, author_username: '', author_avatar: null, author_display_name: null,
    title: trend.title, post_type: 'text', text: '', image_url: null, image_file: null,
    video_url: null, video_file: null, anime: null, anime_rating: null, playlist: null,
    group: null, original_post: null, repost_comment: '', likes_count: trend.likes_count,
    dislikes_count: 0, comments_count: 0, reposts_count: 0, views_count: 0, shares_count: 0,
    is_pinned: false, is_deleted: false, allow_comments: true, status: 'published',
    visibility: 'public', reactor_post: null, published_at: null, created_at: '',
    updated_at: '', edited_at: null, is_spoiler: false, media_files: [], hashtags: [],
    is_liked: false, is_disliked: false, is_bookmarked: false, is_following: false,
    can_edit: false, can_delete: false
  }
  selectedPost.value = post
  showPostDetail.value = true
}

const handleLike = async (post: any) => {
  try {
    if (post.is_liked) {
      await apiClient.post(`/social/posts/${post.id}/dislike/`)
      post.is_liked = false
      post.likes_count--
    } else {
      await apiClient.post(`/social/posts/${post.id}/like/`)
      post.is_liked = true
      post.likes_count++
      if (post.is_disliked) { post.is_disliked = false; post.dislikes_count-- }
    }
  } catch (error) { console.error('Error toggling like:', error) }
}

const handleDislike = async (post: any) => {
  try {
    if (post.is_disliked) {
      await apiClient.post(`/social/posts/${post.id}/dislike/`)
      post.is_disliked = false
      post.dislikes_count--
    } else {
      await apiClient.post(`/social/posts/${post.id}/dislike/`)
      post.is_disliked = true
      post.dislikes_count++
      if (post.is_liked) { post.is_liked = false; post.likes_count-- }
    }
  } catch (error) { console.error('Error toggling dislike:', error) }
}

const toggleBookmark = async (post: any) => {
  try {
    await apiClient.post('/social/bookmarks/toggle/', { post_id: post.id })
    post.is_bookmarked = !post.is_bookmarked
  } catch (error) { console.error('Error toggling bookmark:', error) }
}

const sharePost = (post: any) => {
  selectedPost.value = post
  showRepost.value = true
}

const editPost = (post: any) => { 
  selectedPost.value = post
  showMenu.value = false
  showEditPost.value = true 
}

const onPostEdited = (updatedPost: any) => {
  // Обновляем пост в списке
  const idx = posts.value.findIndex(p => p.id === updatedPost.id)
  if (idx !== -1) {
    posts.value[idx] = normalizePost(updatedPost)
  }
  showEditPost.value = false
}
const deletePost = async (post: any) => {
  try {
    await apiClient.delete(`/social/posts/${post.id}/`)
    posts.value = posts.value.filter(p => p.id !== post.id)
    showMenu.value = false
  } catch (error) { console.error('Error deleting post:', error) }
}
const pinPost = async (post: any) => {
  try { await apiClient.post(`/social/posts/${post.id}/pin/`); post.is_pinned = true; showMenu.value = false }
  catch (error) { console.error('Error pinning post:', error) }
}
const hidePost = async (post: any) => {
  try {
    await postsApi.notInterestedPost(post.id)
  } catch (error) {
    console.error('Error hiding post:', error)
  }
  posts.value = posts.value.filter(p => p.id !== post.id)
  showMenu.value = false
}

const hidePostByAuthor = async (post: any) => {
  try {
    await apiClient.post(`/social/users/${post.author}/hide/`)
  } catch (error) {
    console.error('Error hiding author:', error)
  }
  posts.value = posts.value.filter(p => p.author !== post.author)
  showMenu.value = false
}

const openForwardModal = (post: any) => { selectedPost.value = post; showForward.value = true; showMenu.value = false }

const onPostCreated = (post: any) => { posts.value.unshift(post); showCreatePost.value = false }
const onCommentAdded = (_comment: any) => { if (selectedPost.value && selectedPost.value.comments_count !== undefined) selectedPost.value.comments_count++ }
const onReposted = (_post: any) => { if (selectedPost.value) selectedPost.value.reposts_count++; showRepost.value = false }

// Fetch current user
const fetchCurrentUser = async () => {
  try {
    const response = await apiClient.get('/users/me/')
    currentUser.value = response.data
  } catch (error) { console.error('Error fetching current user:', error) }
}

const handleScroll = () => {
  const scrollTop = window.scrollY
  const windowHeight = window.innerHeight ?? 0
  const documentHeight = document.documentElement.scrollHeight
  if (scrollTop + windowHeight >= documentHeight - 500) {
    if (activeTab.value === 'feed') loadMorePosts()
    else if (activeTab.value === 'subscriptions') loadMoreSubscriptions()
  }
}

onMounted(async () => {
  await fetchCurrentUser()

  // Check if we're on a specific post route
  const postId = route.params.id
  if (postId && route.name === 'post-detail') {
    await loadPostFromRoute()
  } else {
    await loadPosts()
  }

  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => { window.removeEventListener('scroll', handleScroll) })
</script>

<style scoped>
.feed-page { min-height: 100vh; background: #0a0a0a; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 1rem; }

.feed-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid #1f1f1f; position: sticky; top: 0; background: #0a0a0a; z-index: 10; }
.feed-tabs { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.tab-btn { display: flex; align-items: center; gap: 0.5rem; background: none; border: none; padding: 0.75rem 1rem; font-size: 0.9rem; font-weight: 500; color: #888; cursor: pointer; border-radius: 8px; transition: all 0.2s; }
.tab-btn:hover { background: #151515; color: #fff; }
.tab-btn.active { background: #1a1a1a; color: #fff; }
.new-posts-badge { background: #ef4444; color: white; font-size: 0.7rem; padding: 0.1rem 0.4rem; border-radius: 10px; }

.btn-create-post { display: flex; align-items: center; gap: 0.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 0.75rem 1.25rem; border-radius: 10px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
.btn-create-post:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }

.filters-bar { display: flex; justify-content: space-between; align-items: flex-start; padding: 1rem 0; gap: 1rem; flex-wrap: wrap; }
.filters-section { position: relative; }
.filter-toggle { display: flex; align-items: center; gap: 0.5rem; background: #111; color: #888; border: none; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; }
.filter-toggle .arrow { font-size: 0.7rem; transition: transform 0.2s; }
.filter-toggle .arrow.open { transform: rotate(180deg); }
.filters-dropdown { position: absolute; top: 100%; left: 0; margin-top: 0.5rem; background: #111; border-radius: 8px; padding: 1rem; z-index: 20; min-width: 200px; }
.filter-group { margin-bottom: 1rem; }
.filter-group:last-child { margin-bottom: 0; }
.filter-group label { display: block; margin-bottom: 0.5rem; color: #888; font-size: 0.85rem; }
.checkbox-label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; padding: 0.3rem 0; color: #ccc !important; }
.checkbox-label input { accent-color: #667eea; }
.filter-select, .sort-select { background: #111; color: #ccc; border: 1px solid #333; padding: 0.5rem; border-radius: 6px; cursor: pointer; }
.sort-section { display: flex; align-items: center; }

.active-filters { display: flex; flex-wrap: wrap; gap: 0.5rem; padding-bottom: 1rem; align-items: center; }
.filter-tag { background: #1a1a1a; color: #888; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 0.3rem; }
.filter-tag:hover { background: #252525; color: #fff; }
.clear-all { background: none; border: none; color: #667eea; cursor: pointer; font-size: 0.8rem; }

/* Sub-tabs */
.sub-tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; border-bottom: 1px solid #1f1f1f; padding-bottom: 0.5rem; }
.sub-tab-btn { background: none; border: none; color: #666; padding: 0.5rem 1rem; font-size: 0.85rem; cursor: pointer; border-radius: 8px; transition: all 0.2s; }
.sub-tab-btn:hover { background: #1a1a1a; color: #aaa; }
.sub-tab-btn.active { background: #667eea; color: #fff; }

/* Subscription cards */
.subscription-card.clickable { cursor: pointer; }
.subscription-card.clickable:hover { background: #1f1f1f; }
.subscription-card.blocked { border: 1px solid #ef444440; background: #1a0a0a; }
.subscription-card.blocked .user-info h4 { color: #ef4444; }
.btn-unblock { background: #ef4444; color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 500; }
.btn-unblock:hover { background: #dc2626; }

/* Hidden post cards */
.hidden-post-card { display: flex; justify-content: space-between; align-items: center; background: #111; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem; }
.hidden-post-info { display: flex; flex-direction: column; gap: 0.25rem; cursor: pointer; }
.hidden-post-info:hover .hidden-post-title { color: #667eea; }
.hidden-post-title { color: #ddd; font-size: 0.9rem; }
.hidden-date { color: #555; font-size: 0.8rem; }
.btn-restore { background: #1a1a1a; color: #888; border: 1px solid #333; padding: 0.4rem 0.8rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
.btn-restore:hover { background: #252525; color: #fff; }

.feed-layout { display: grid; grid-template-columns: 1fr 280px; gap: 1.5rem; padding: 1.5rem 0; }
.feed-main { min-height: 500px; }

.create-post-card { display: flex; align-items: center; gap: 1rem; background: #111; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; cursor: pointer; transition: background 0.2s; }
.create-post-card:hover { background: #151515; }
.create-post-card .avatar { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; }
.create-post-card .placeholder { flex: 1; color: #555; font-size: 0.95rem; }
.create-actions { display: flex; gap: 0.5rem; }
.create-actions button { background: none; border: none; font-size: 1.2rem; padding: 0.5rem; cursor: pointer; border-radius: 8px; transition: background 0.2s; }
.create-actions button:hover { background: #1f1f1f; }

.posts-list { display: flex; flex-direction: column; gap: 1rem; }
.new-posts-bar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 0.75rem; border-radius: 10px; cursor: pointer; font-weight: 500; }
.new-posts-bar:hover { transform: scale(1.02); }
.load-more { text-align: center; padding: 1rem; }
.btn-load-more { background: #1a1a1a; color: #888; border: none; padding: 0.75rem 2rem; border-radius: 8px; cursor: pointer; font-weight: 500; }
.btn-load-more:hover:not(:disabled) { background: #252525; color: #fff; }
.btn-load-more:disabled { opacity: 0.5; cursor: not-allowed; }

.loading-state { display: flex; flex-direction: column; gap: 1rem; }
.skeleton-post { background: #111; border-radius: 12px; padding: 1.5rem; }
.skeleton-header { display: flex; gap: 1rem; margin-bottom: 1rem; }
.skeleton-avatar { width: 44px; height: 44px; border-radius: 50%; background: #1f1f1f; animation: pulse 1.5s infinite; }
.skeleton-info { flex: 1; display: flex; flex-direction: column; gap: 0.5rem; }
.skeleton-line { height: 12px; background: #1f1f1f; border-radius: 4px; animation: pulse 1.5s infinite; }
.skeleton-line.short { width: 40%; }
.skeleton-line.medium { width: 70%; }
.skeleton-content { display: flex; flex-direction: column; gap: 0.5rem; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.empty-state { text-align: center; padding: 4rem 2rem; background: #111; border-radius: 12px; }
.empty-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-state h3 { color: #fff; margin-bottom: 0.5rem; }
.empty-state p { color: #666; margin-bottom: 1.5rem; }
.btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600; cursor: pointer; }

.feed-right-sidebar { display: none; }
@media (min-width: 900px) { .feed-right-sidebar { display: block; } }
.sidebar-card { background: #111; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; }
.sidebar-card h3 { font-size: 0.9rem; color: #888; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.5px; }
.trending-item { display: flex; gap: 0.75rem; padding: 0.5rem 0; cursor: pointer; }
.trending-item:hover { background: #1a1a1a; border-radius: 8px; }
.trend-rank { color: #667eea; font-weight: 700; font-size: 1.1rem; }
.trend-content { display: flex; flex-direction: column; }
.trend-title { color: #fff; font-size: 0.9rem; }
.trend-stats { color: #666; font-size: 0.75rem; }

/* Subscriptions Tab */
.subscriptions-tab, .not-interested-tab, .reports-tab { padding: 1rem 0; }
.tab-header { display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
.search-input { flex: 1; min-width: 200px; background: #111; border: 1px solid #333; color: #fff; padding: 0.75rem 1rem; border-radius: 8px; }
.search-input:focus { outline: none; border-color: #667eea; }

.subscriptions-grid { display: flex; flex-direction: column; gap: 1rem; }
.subscription-card { display: flex; align-items: center; gap: 1rem; background: #111; border-radius: 12px; padding: 1rem; }
.avatar-lg { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; }
.subscription-card .user-info { flex: 1; }
.subscription-card h4 { color: #fff; margin: 0 0 0.25rem; font-size: 1rem; }
.subscription-card .username { color: #666; font-size: 0.85rem; display: block; }
.subscription-card .followers, .subscription-card .hidden-date { color: #888; font-size: 0.8rem; }
.subscription-card .reason { color: #ef4444; font-size: 0.8rem; display: block; margin-top: 0.25rem; }
.user-actions { display: flex; gap: 0.5rem; }
.btn-following { background: #1a1a1a; color: #667eea; border: 1px solid #667eea; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; }
.btn-unhide { background: #1a1a1a; color: #ef4444; border: 1px solid #ef4444; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; }
.btn-message, .btn-profile { background: #1a1a1a; color: #888; border: none; padding: 0.5rem; border-radius: 8px; cursor: pointer; font-size: 1.1rem; }

/* Reports Tab */
.reports-list { display: flex; flex-direction: column; gap: 1rem; }
.report-card { background: #111; border-radius: 12px; padding: 1rem; }
.report-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.report-type { color: #667eea; font-weight: 600; }
.report-status { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
.report-status.pending { background: #fef3c7; color: #92400e; }
.report-status.resolved { background: #d1fae5; color: #065f46; }
.report-status.rejected { background: #fee2e2; color: #991b1b; }
.report-content p { margin: 0.25rem 0; color: #ccc; }
.report-meta { color: #666; font-size: 0.8rem; margin-top: 0.5rem; display: flex; gap: 1rem; }
.report-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.btn-review { background: #667eea; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
.btn-reject { background: #333; color: #888; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }

/* Report Detail Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem; }
.report-detail-modal { background: #111; border-radius: 16px; width: 100%; max-width: 500px; max-height: 90vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; border-bottom: 1px solid #1f1f1f; }
.modal-header h3 { color: #fff; margin: 0; }
.close-btn { background: none; border: none; color: #666; font-size: 1.25rem; cursor: pointer; }
.modal-body { padding: 1.5rem; }
.report-full-info p { margin: 0.5rem 0; color: #ccc; }
.report-actions-full { margin-top: 1.5rem; }
.report-actions-full label { display: block; color: #888; margin-bottom: 0.5rem; }
.action-select { width: 100%; background: #1a1a1a; color: #fff; border: 1px solid #333; padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; }
.comment-textarea { width: 100%; background: #1a1a1a; color: #fff; border: 1px solid #333; padding: 0.75rem; border-radius: 8px; min-height: 100px; resize: vertical; }
.btn-submit { width: 100%; background: #667eea; color: white; border: none; padding: 0.75rem; border-radius: 8px; font-weight: 600; cursor: pointer; margin-top: 1rem; }
.btn-submit:hover { background: #5a6fd6; }

@media (min-width: 768px) { .feed-layout { grid-template-columns: 1fr 300px; } }

/* Highlight effect for post loaded from route */
.highlight-post { animation: highlight-fade 3s ease-out; }
@keyframes highlight-fade {
  0% { box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.8); }
  100% { box-shadow: 0 0 0 0 transparent; }
}

/* Bookmarks & Pinned tabs */
.bookmarks-tab, .pinned-tab { padding: 1rem 0; }
.pinned-post-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.btn-unpin {
  align-self: flex-end;
  background: #1a1a1a;
  border: 1px solid #333;
  color: #888;
  padding: 4px 12px;
  border-radius: 0 0 8px 8px;
  cursor: pointer;
  font-size: .8rem;
  margin-top: -4px;
  transition: background .2s, color .2s;
}
.btn-unpin:hover { background: #252525; color: #fff; }
</style>
