<template>
  <div class="chat-detail-view">
    <!-- Франшизное обсуждение — отдельный рендер -->
    <FranchiseDiscussionChat
      v-if="isFranchiseDiscussion && franchiseParts.length > 0"
      :franchise-id="chat?.franchise_id"
      :franchise-name="chat?.name"
      :franchise-poster="franchisePosterUrl || chat?.avatar_url || ''"
      :parts="franchiseParts"
      :highlight-anime-id="highlightAnimeId"
    />

    <!-- Обычный чат -->
    <template v-else>
    <div class="chat-header">
      <div class="chat-info">
        <button @click="showSettings = true" title="Настройки чата">
          <img :src="chatAvatar" :alt="chatName" class="chat-avatar">
        </button>
        <div class="chat-details">
          <h2 class="chat-name">{{ chatName }}</h2>
          <div class="chat-status" v-if="chat?.type === 'private' && otherUser">
            <template v-if="isOtherTyping">
              <span class="typing-indicator">
                <span class="dot"></span><span class="dot"></span><span class="dot"></span>
              </span>
              печатает...
            </template>
            <template v-else-if="isUserOnline(otherUser?.id)">
              <span class="status-dot online"></span>онлайн
            </template>
            <template v-else>
              <span class="status-dot offline"></span>оффлайн
            </template>
          </div>
          <div class="chat-members" v-else-if="chat?.type === 'group'">
            {{ chat.participants_usernames?.length || 0 }} участников
          </div>
        </div>
      </div>
      <div class="header-actions">
        <button v-if="isGroup && canManageChat" @click="handleInvite" class="invite-btn" title="Пригласить участников"> <SakuraIcon name="users" /> </button>
        <!-- <button @click="showSearch = true" class="search-btn" title="Поиск сообщений"> <SakuraIcon name="search" /> </button> -->
        <button @click="showChatInfo = !showChatInfo" class="info-btn" title="Информация о чате">⋮</button>
      </div>  
    </div>

    <div class="messages-container" ref="messagesContainer" :style="wallpaperStyle">
      <!-- Псевдоэлемент для размытого фона -->
      <div class="wallpaper-bg" :style="wallpaperBgStyle"></div>
      <!-- Панель закрепленных сообщений -->
      <div v-if="pinnedMessages.length > 0 && showPinnedBar" class="pinned-messages-bar">
        <span class="pinned-label"><SakuraIcon name="pin" /> Закреплено:</span>
        <div class="pinned-message-preview">
          {{ pinnedMessages[0].text || 'Медиа-сообщение' }}
        </div>
        <button @click="showPinnedBar = false" class="pinned-close">×</button>
      </div>

      <div v-if="loadingMessages" class="loading">Загрузка...</div>
      <div v-else-if="messages.length === 0" class="no-messages">Нет сообщений</div>
      <div v-else class="messages-list">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-item', { 'own-message': message.sender_id === user?.id }]"
          :data-message-id="message.id"
          @contextmenu.prevent="showMessageMenu(message, $event)"
        >
          <div class="message-content">
            <!-- Имя отправителя для групповых чатов -->
            <div v-if="isGroup && message.sender_id !== user?.id" class="message-sender">
              {{ message.sender_username || 'Unknown' }}
            </div>

            <!-- Цитата (ответ на сообщение) -->
            <div v-if="message.reply_to_message" class="message-reply-quote" @click="scrollToMessage(message.reply_to_message.id)">
              <div class="reply-quote-author" :style="{ color: getMessageAuthorColor(message.reply_to_message.sender_id) }">
                {{ message.reply_to_message.sender_username || 'Пользователь' }}
              </div>
              <div v-if="message.reply_to_message.text" class="reply-quote-text">
                {{ truncateText(message.reply_to_message.text, 100) }}
              </div>
              <div v-if="message.reply_to_message.media && message.reply_to_message.media_type === 'image'" class="reply-quote-image">
                <img :src="message.reply_to_message.media" alt="attachment" />
              </div>
            </div>

            <!-- Текст сообщения -->
            <div class="message-text" v-if="message.text">{{ message.text }}</div>
            
            <!-- Медиа -->
            <img v-if="message.media && message.media_type === 'image'" :src="message.media" class="message-image" />
            <div v-if="message.media && message.media_type !== 'image'" class="message-file">
              <a :href="message.media" target="_blank">📎 {{ getFileName(message.media) }}</a>
            </div>

            <!-- Прикреплённый пост -->
            <div v-if="message.shared_post_data" class="message-shared-content">
              <div class="forwarded-label">
                <span class="forwarded-icon">↗️</span>
                <span class="forwarded-text">Переслано из</span>
                <span class="forwarded-source">@{{ message.shared_post_data.author_username }}</span>
              </div>
              <div class="shared-post" @click="goToPost(message.shared_post_data.id)">
                <img v-if="message.shared_post_data.image_url" :src="message.shared_post_data.image_url" class="shared-image" />
                <div class="shared-info">
                  <span class="shared-title">{{ message.shared_post_data.text || 'Пост' }}</span>
                  <div class="shared-meta">
                    <span class="shared-author">@{{ message.shared_post_data.author_username }}</span>
                    <span class="shared-date">{{ formatMessageTime(message.shared_post_data.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Прикреплённое аниме -->
            <div v-if="message.shared_anime_data" class="message-shared-content">
              <div class="shared-label"><SakuraIcon name="play" /> Аниме</div>
              <div class="shared-anime">
                <img :src="message.shared_anime_data.poster_url" class="shared-poster" @error="handleImageError" />
                <div class="shared-info">
                  <span class="shared-title">{{ message.shared_anime_data.title_ru }}</span>
                  <span v-if="message.shared_anime_data.title_en" class="shared-subtitle">{{ message.shared_anime_data.title_en }}</span>
                </div>
              </div>
            </div>

            <!-- Прикреплённый плейлист -->
            <div v-if="message.shared_playlist_data" class="message-shared-content">
              <div class="shared-label"><SakuraIcon name="clipboard" /> Плейлист</div>
              <div class="shared-playlist">
                <div class="shared-playlist-posters">
                  <img 
                    v-for="(poster, idx) in (message.shared_playlist_data.posters || []).slice(0, 4)" 
                    :key="idx" 
                    :src="poster" 
                    class="shared-poster-grid"
                  />
                </div>
                <div class="shared-info">
                  <span class="shared-title">{{ message.shared_playlist_data.title }}</span>
                  <span class="shared-subtitle">{{ message.shared_playlist_data.items_count }} аниме</span>
                </div>
              </div>
            </div>

            <!-- Прикреплённый shorts -->
            <div v-if="message.shared_shorts_data" class="message-shared-content">
              <div class="shared-label"><SakuraIcon name="film" /> Shorts</div>
              <div class="shared-shorts">
                <video 
                  v-if="message.shared_shorts_data.video_url" 
                  :src="message.shared_shorts_data.video_url" 
                  class="shared-video"
                  controls
                />
                <div v-else-if="message.shared_shorts_data.thumbnail_url" class="shared-shorts-thumb">
                  <img :src="message.shared_shorts_data.thumbnail_url" class="shared-poster" />
                  <span class="play-icon"> <SakuraIcon name="play" /> </span>
                </div>
                <div class="shared-info">
                  <span class="shared-author">@{{ message.shared_shorts_data.author?.username }}</span>
                  <span v-if="message.shared_shorts_data.anime" class="shared-anime-tag">
                    {{ message.shared_shorts_data.anime.title_ru }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Реакции отображаются внутри блока сообщения -->
            <div v-if="getMessageReactions(message.id).length > 0" class="message-reactions">
              <span
                v-for="(reaction, idx) in getGroupedReactions(message.id)"
                :key="idx"
                class="reaction-badge"
                :class="{ 'reaction-collapsed': idx >= 4 }"
                @click.stop="handleReaction(message.id, reaction.emoji)"
              >
                {{ reaction.emoji }} {{ reaction.count }}
              </span>
            </div>

            <!-- Информация о сообщении: время и галочки -->
            <div class="message-footer" :class="{ 'own-footer': message.sender_id === user?.id }">
              <span v-if="message.is_pinned" class="message-pinned"> <SakuraIcon name="pin" /> </span>
              <span v-if="message.is_edited" class="message-edited"> <SakuraIcon name="edit" /> </span>
              <span class="message-time">{{ formatMessageTime(message.created_at) }}</span>
              
              <!-- Статусы сообщения - ТОЛЬКО для своих сообщений -->
              <template v-if="message.sender_id === user?.id">
                <!-- Для личных чатов показываем статус прочтения -->
                <template v-if="chat?.type === 'private'">
                  <span 
                    v-if="message.is_read_by_other" 
                    class="message-status read" 
                    title="Прочитано"
                  >
                    ✓✓
                  </span>
                  <span 
                    v-else 
                    class="message-status sent" 
                    title="Отправлено"
                  >
                    ✓
                  </span>
                </template>
                
                <!-- Для групповых чатов показываем счётчик прочитавших (если есть) -->
                <template v-else-if="chat?.type === 'group'">
                  <span 
                    v-if="message.read_count && message.read_count > 0" 
                    class="message-status group-read" 
                    :title="`Прочитано ${message.read_count} ${pluralize(message.read_count, ['участником', 'участниками', 'участниками'])}`"
                  >
                    ✓{{ message.read_count }}
                  </span>
                  <span 
                    v-else 
                    class="message-status sent" 
                    title="Отправлено"
                  >
                    ✓
                  </span>
                </template>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="message-input-area">
      <!-- Превью ответа на сообщение -->
      <MessageReplyPreview
        v-if="replyToMessage"
        :message="replyToMessage"
        :author="replyToMessage.sender_username || replyToMessage.sender?.username || 'Пользователь'"
        :author-color="getMessageAuthorColor(replyToMessage.sender_id)"
        @close="cancelReply"
        @click="scrollToMessage(replyToMessage.id)"
      />
      
      <form @submit.prevent="sendMessage" class="message-form">
        <input v-model="newMessage" type="text" placeholder="Сообщение..." class="message-input"
          :disabled="sending || !wsConnected" @input="handleTyping" />
        <input ref="fileInput" type="file" @change="handleFileSelect" style="display:none" accept="image/*,video/*,audio/*,.pdf,.doc*" />
        <button type="button" @click="attachFile" class="attach-btn" :disabled="sending || !wsConnected" title="Прикрепить файл">📎</button>
        <button type="button" @click="showAttachPlaylist = true" class="attach-btn" :disabled="sending || !wsConnected" title="Поделиться плейлистом">📚</button>
        <button type="button" @click="showAttachAnime = true" class="attach-btn" :disabled="sending || !wsConnected" title="Поделиться аниме">🎬</button>
        <button type="submit" class="send-btn" :disabled="!newMessage.trim() || sending || !wsConnected">
          <SakuraIcon v-if="!sending" name="send" :size="18" />
          <SakuraIcon v-else name="hourglass" :size="18" />
        </button>
      </form>
      <div v-if="!wsConnected && reconnectAttempts > 0" class="ws-status">
        Переподключение... ({{ reconnectAttempts }})
      </div>

      <!-- Modal for playlist selection -->
      <div v-if="showAttachPlaylist" class="attach-modal-overlay" @click="showAttachPlaylist = false">
        <div class="attach-modal" @click.stop>
          <h3>Выберите плейлист</h3>
          <div class="attach-list">
            <!-- Load and display user playlists -->
            <div class="attach-item" v-for="playlist in userPlaylists" :key="playlist.id" @click="selectedPlaylist = playlist">
              <img v-if="playlist.cover_image" :src="playlist.cover_image" alt="" class="attach-thumb">
              <div class="attach-info">
                <div class="attach-title">{{ playlist.name }}</div>
                <div class="attach-meta">{{ playlist.items_count }} аниме</div>
              </div>
            </div>
          </div>
          <div class="attach-actions">
            <button @click="showAttachPlaylist = false">Отмена</button>
            <button @click="sendPlaylist" :disabled="!selectedPlaylist">Отправить</button>
          </div>
        </div>
      </div>

      <!-- Modal for anime selection -->
      <div v-if="showAttachAnime" class="attach-modal-overlay" @click="showAttachAnime = false">
        <div class="attach-modal" @click.stop>
          <h3>Выберите аниме</h3>
          <input v-model="animeSearch" type="text" placeholder="Поиск аниме..." class="search-input">
          <div class="attach-list">
            <div class="attach-item" v-for="anime in filteredAnimes.slice(0, 10)" :key="anime.id" @click="selectedAnime = anime">
              <img v-if="anime.poster_url" :src="anime.poster_url" alt="" class="attach-thumb">
              <div class="attach-info">
                <div class="attach-title">{{ anime.title_ru || anime.title_en }}</div>
                <div class="attach-meta">{{ anime.year }} • {{ anime.kind }}</div>
              </div>
            </div>
          </div>
          <div class="attach-actions">
            <button @click="showAttachAnime = false">Отмена</button>
            <button @click="sendAnime" :disabled="!selectedAnime">Отправить</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showChatInfo" class="chat-info-sidebar" @click.self="showChatInfo = false">
      <div class="sidebar-header">
        <h3>О чате</h3>
      </div>
      <div class="sidebar-content">
        <div class="chat-avatar-large-row">
          <div class="chat-avatar-large">
            <img :src="chatAvatar" :alt="chatName">
          </div>
          <button @click="showChatInfo = false" class="close-btn" title="Закрыть">✕</button>
        </div>
        <h4>{{ chatName }}</h4>
        <p v-if="chat?.description">{{ chat.description }}</p>
        <div v-if="chat?.type === 'group'" class="participants-list">
          <h5>Участники ({{ chat.participants_usernames?.length || 0 }})</h5>
          <div v-for="username in chat.participants_usernames" :key="username" class="participant">
            <span>{{ username }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно настроек чата -->
    <ChatSettingsModal
      v-if="showSettings && currentChatId"
      :chat-id="currentChatId"
      :chat-type="chat?.type || 'group'"
      :chat-name="chatName"
      :chat-avatar="chatAvatar"
      :is-owner="canManageChat"
      @close="showSettings = false"
      @settings-changed="handleSettingsChanged"
    />

    <!-- Модальное окно поиска сообщений -->
    <MessageSearchModal
      :is-open="showSearch"
      :chat-id="currentChatId || 0"
      @close="showSearch = false"
      @message-selected="(id) => scrollToMessage(id)"
    />

    <!-- Модальное окно пересылки сообщений -->
    <ForwardMessageModal
      :is-open="showForward"
      :message="messageToForward"
      :available-chats="chatsForForward"
      @close="showForward = false"
      @forwarded="handleForwardComplete"
    />

    <!-- Модальное окно приглашений -->
    <ChatInviteModal
      :is-open="showInvite"
      :chat-id="currentChatId || 0"
      @close="showInvite = false"
    />

    <!-- Контекстное меню сообщения + пикер реакций (единый блок) -->
    <div
      v-if="contextMenu.visible"
      class="message-actions-popup"
      :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }"
      @click.stop
    >
      <!-- Пикер реакций (всегда сверху) -->
      <div class="reaction-picker-container">
        <button
          v-for="emoji in reactionEmojis"
          :key="emoji"
          class="reaction-emoji-btn"
          @click="addReaction(emoji)"
        >
          {{ emoji }}
        </button>
      </div>
      
      <!-- Кнопки действий (всегда снизу) -->
      <div class="context-menu-actions">
        <button class="context-menu-item" @click="handleReply(selectedMessage)">
          <span class="context-menu-icon">↩️</span> Ответить
        </button>
        <!-- Закомментировано: <button class="context-menu-item" @click="handleForward(selectedMessage)">
          <span class="context-menu-icon"> <SakuraIcon name="arrow-up-right" /> </span> Переслать
        </button> -->
        <button class="context-menu-item delete" v-if="selectedMessage?.sender_id === user?.id" @click="handleDelete(selectedMessage.id)">
          <span class="context-menu-icon"> <SakuraIcon name="trash" /> </span> Удалить
        </button>
      </div>
    </div>
    </template><!-- end v-else ordinary chat -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatExtrasStore } from '@/stores/chatExtras'
import { usePrivateChatStore } from '@/stores/privateChat'
import { useGroupChatStore } from '@/stores/groupChat'
import { useAvatar } from '@/composables/useAvatar'
import { useOnlineStatus } from '@/composables/useOnlineStatus'
import ChatSettingsModal from '@/components/Chats/ChatSettingsModal.vue'
import FranchiseDiscussionChat from '@/components/Chats/FranchiseDiscussionChat.vue'
import MessageReplyPreview from '@/components/Chats/MessageReplyPreview.vue'
import MessageSearchModal from '@/components/modal/chats/MessageSearchModal.vue'
import ForwardMessageModal from '@/components/modal/chats/ForwardMessageModal.vue'
import ChatInviteModal from '@/components/modal/chats/ChatInviteModal.vue'
import { chatsApi, messageActionsApi } from '@/api/chats'
import apiClient, { getMediaUrl } from '@/api/client'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'

interface Props {
  chatId?: number
}
const props = defineProps<Props>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const chatExtrasStore = useChatExtrasStore()
const privateChatStore = usePrivateChatStore()
const groupChatStore = useGroupChatStore()
const { getAvatarUrl } = useAvatar()
const { isUserOnline } = useOnlineStatus()

const chat = ref<any>(null)
const messages = ref<any[]>([])
const loadingMessages = ref(false)
const sending = ref(false)
const showChatInfo = ref(false)
const showSettings = ref(false)
const showSearch = ref(false)
const showInvite = ref(false)
const showForward = ref(false)
const showAttachPlaylist = ref(false)
const showAttachAnime = ref(false)
const selectedPlaylist = ref<any>(null)
const selectedAnime = ref<any>(null)
const userPlaylists = ref<any[]>([])
const animeSearch = ref('')
const allAnimes = ref<any[]>([])

const filteredAnimes = computed(() => {
  if (!animeSearch.value) return allAnimes.value.slice(0, 20)
  const search = animeSearch.value.toLowerCase()
  return allAnimes.value.filter(anime =>
    (anime.title_ru && anime.title_ru.toLowerCase().includes(search)) ||
    (anime.title_en && anime.title_en.toLowerCase().includes(search))
  ).slice(0, 20)
})
const messageToForward = ref<any>(null)
const selectedMessage = ref<any>(null)
const replyToMessage = ref<any>(null)
const showPinnedBar = ref(false)
const newMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const fileInput = ref<HTMLInputElement>()
const isOtherTyping = ref(false)
const wsConnected = ref(false)
const reconnectAttempts = ref(0)
const availableChats = ref<any[]>([])
const loadingChats = ref(false)
const currentWallpaper = ref<any>(null)
const currentTheme = ref<any>(null)

// Контекстное меню + пикер реакций (единый блок)
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0
})

// Единая позиция для popup
const popupPosition = ref({ x: 0, y: 0 })

const reactionEmojis = ['👍', '😢', '😮', '😠', '🎉', '🔥', '👀', '🙏']

// Computed для получения ID чата - из prop или route
const currentChatId = computed(() => {
  // Приоритет пропа, так как компонент может использоваться внутри ChatsView
  if (props.chatId) {
    return props.chatId
  }
  // Иначе берём из route
  const routeId = route.params.id
  if (routeId && routeId !== 'undefined') {
    const parsed = parseInt(routeId as string)
    // Проверяем, что получили валидное число
    return isNaN(parsed) ? undefined : parsed
  }
  return undefined
})

let ws: WebSocket | null = null
let globalWs: WebSocket | null = null
let typingDebounceTimer: number | null = null
let messageObserver: IntersectionObserver | null = null
const readMessages = new Set<number>()

const user = computed(() => authStore.user)
const apiUrl = import.meta.env.VITE_API_URL || 'https://anisphere.org'

const chatName = computed(() => {
  if (!chat.value) return 'Загрузка...'
  
  // Если есть кастомное название (для личных чатов оно приходит в name)
  if (chat.value.name && chat.value.type === 'private') {
    // name уже содержит custom_name если он есть
    const other = (chat.value as any).other_user 
    return chat.value.name || other?.display_name || other?.username || 'Личный чат'
  }
  
  if (chat.value.user1 && chat.value.user2) {
    // Личный чат без кастомного названия
    const other = (chat.value as any).other_user 
      || (chat.value.user1?.id === authStore.user?.id ? chat.value.user2 : chat.value.user1)
    return other?.display_name || other?.username || 'Личный чат'
  }
  // Для групп обсуждений показываем название аниме
  if (chat.value.type === 'group' && chat.value.anime_title) {
    return chat.value.anime_title
  }
  return chat.value.name || 'Групповой чат'
})

const otherUser = computed(() => {
  if (chat.value?.type === 'private') return (chat.value as any).other_user || null
  return null
})

const chatAvatar = computed(() => {
  // Если это группа обсуждения с аниме - используем постер аниме
  if (chat.value?.type === 'group' && chat.value.anime_poster) {
    return getMediaUrl(chat.value.anime_poster)
  }
  if (chat.value?.type === 'private' && otherUser.value?.avatar) {
    return getAvatarUrl(otherUser.value.avatar)
  }
  return getAvatarUrl(chat.value?.avatar_url)
})

const isGroup = computed(() => chat.value?.type === 'group')

// Франшизное обсуждение — групповой чат с franchise_id
const isFranchiseDiscussion = computed(() =>
  chat.value?.type === 'group' && !!chat.value?.franchise_id
)

const franchiseParts = ref<any[]>([])  // части франшизы для FranchiseDiscussionChat
const franchisePosterUrl = ref<string>('')
const highlightAnimeId = ref<number | undefined>(undefined)

// Загружаем данные франшизы через franchise-discussion/init/
const loadFranchiseParts = async () => {
  if (!isFranchiseDiscussion.value) return
  const franchiseId = chat.value?.franchise_id
  if (!franchiseId) return

  try {
    // Сначала получаем список аниме франшизы
    const { data: franchiseData } = await apiClient.get(`/anime/franchises/${franchiseId}/`)
    const animeIds: number[] = (franchiseData.entries || franchiseData.anime_list || franchiseData.parts || []).map((a: any) => a.id)

    // Инициализируем franchise discussion — получаем топики с постерами
    const { data } = await apiClient.post('/social/franchise-discussion/init/', {
      franchise_id: franchiseId,
      anime_ids: animeIds,
    })

    // Строим parts из topics бэкенда (всё кроме general)
    franchiseParts.value = (data.topics || [])
      .filter((t: any) => t.anime_id !== null)
      .map((t: any) => ({
        id: t.anime_id,
        title_ru: t.title,
        title_en: t.title,
        franchise_order: t.order,
      }))

    if (data.franchise_poster) {
      franchisePosterUrl.value = data.franchise_poster
    }
  } catch {
    // Фолбек: показываем обычный чат если не удалось загрузить
    franchiseParts.value = []
  }
}

const canManageChat = computed(() => {
  if (!authStore.user || !isGroup.value) return false
  const isAdmin = chat.value?.admins?.some((a: any) => a.id === authStore.user?.id)
  const isCreator = chat.value?.created_by?.id === authStore.user?.id
  return isAdmin || isCreator
})

const pinnedMessages = computed(() => messages.value.filter(m => m.is_pinned))

// Функция для склонения слов (для групповых чатов)
const pluralize = (count: number, words: [string, string, string]) => {
  const cases = [2, 0, 1, 1, 1, 2];
  const mod10 = count % 10;
  const mod100 = count % 100;
  
  const caseIndex = mod100 > 4 && mod100 < 20 ? 2 : Math.min(mod10, 5);
  const index = cases[caseIndex] ?? 2; // если undefined, используем 2
  
  return words[index] ?? words[2]; // если индекс невалидный, используем последнее слово
}

const chatsForForward = computed(() => {
  if (!Array.isArray(availableChats.value)) return []
  const currentId = currentChatId.value
  return availableChats.value.filter(c => {
    // Исключаем текущий чат
    if (currentId && c.id === currentId) return false

    // Форматируем имя и тип для модального окна
    return {
      id: c.id,
      name: c.type === 'group' ? c.name : (c.other_user?.username || 'Чат'),
      avatar_url: c.type === 'group' ? c.avatar_url : c.other_user?.avatar,
      type: c.type
    }
  })
})

const getFileName = (url: string) => {
  if (!url) return 'Файл'
  try {
    return new URL(url).pathname.split('/').pop() || 'Файл'
  } catch {
    return url.split('/').pop() || 'Файл'
  }
}

const truncateText = (text: string, maxLen: number): string => {
  if (!text) return ''
  const cleaned = text.replace(/\n/g, ' ').trim()
  return cleaned.length > maxLen ? cleaned.substring(0, maxLen) + '...' : cleaned
}

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement | null
  if (target) {
    target.style.display = 'none'
  }
}

const formatMessageTime = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const connectWebSocket = () => {
  const chatId = currentChatId.value
  console.log('WebSocket: chatId из route:', chatId, 'тип:', typeof chatId)
  
  if (!chatId) {
    console.error('Нет chatId для WebSocket')
    return
  }
  const token = localStorage.getItem('access_token') || localStorage.getItem('access_token')
  if (!token) return

  // Используем правильный протокол (ws или wss)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/ws/chat/${chatId}/?token=${token}`
  console.log('Подключаемся к WebSocket:', wsUrl)
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    wsConnected.value = true
    reconnectAttempts.value = 0
  }
  
  ws.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.action === 'init') {
        console.log('WS init: user.id =', user.value?.id, 'messages count =', data.messages?.length)
        
        // Просто сохраняем сообщения как есть, без принудительной пометки
        messages.value = data.messages || []
        
        await nextTick()
        scrollToBottom()
        
        // Наблюдаем за новыми сообщениями
        setupMessageObserver()
      } else if (data.action === 'new_message') {
        // Проверяем, есть ли временное сообщение с таким же текстом и отправителем
        const existingIndex = messages.value.findIndex(msg =>
          msg.id < 0 && msg.text === data.message.text && msg.sender_id === data.message.sender_id
        )

        if (existingIndex !== -1) {
          // Заменяем временное сообщение на реальное
          messages.value[existingIndex] = data.message
        } else {
          // Добавляем новое сообщение
          messages.value.push(data.message)
        }
        messages.value = [...messages.value]
        await nextTick()
        scrollToBottom()

        // Если сообщение от другого пользователя и чат открыт - отмечаем как прочитанное
        if (data.message.sender_id !== user.value?.id) {
          await markMessagesAsRead([data.message.id])
        }

        // Обновить observer для нового сообщения
        nextTick(() => setupMessageObserver())

        // Обновить списки чатов
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
      } else if (data.action === 'messages_read') {
        // Кто-то прочитал сообщения
        console.log('Messages read event:', data)
        
        // Обновляем статусы прочитанных сообщений
        if (data.message_ids && data.message_ids.length > 0) {
          const updatedMessages = messages.value.map(msg => {
            if (data.message_ids.includes(msg.id)) {
              return { ...msg, is_read_by_other: true }
            }
            return msg
          })
          messages.value = updatedMessages
        }
      } else if (data.action === 'typing_status') {
        if (data.user_id !== user.value?.id) {
          isOtherTyping.value = data.is_typing
        }
      } else if (data.action === 'user_online') {
        if (chat.value?.other_user?.id === data.user_id) {
          chat.value.other_user.is_online = data.is_online
        }
      } else if (data.action === 'message_deleted') {
        messages.value = messages.value.filter(m => m.id !== data.message_id)
      }
    } catch (e) {
      console.error('WS message error:', e)
    }
  }
    
  ws.onclose = () => {
    wsConnected.value = false
    ws = null
    setTimeout(() => {
      reconnectAttempts.value++
      connectWebSocket()
    }, 3000)
  }
  
  ws.onerror = (error) => console.error('WS error:', error)
}

const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}

const connectGlobalWebSocket = () => {
  const token = localStorage.getItem('access_token')
  if (!token) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/ws/global/?token=${token}`
  
  globalWs = new WebSocket(wsUrl)
  
  globalWs.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.action === 'chat_created') {
        // Новый чат создан - перезагрузим список
        privateChatStore.loadChats()
        // Если это текущий чат, обновим данные
        const newChatId = data.chat?.chat_id
        if (newChatId && newChatId == route.params.id) {
          loadChat()
        }
      } else if (data.action === 'chat_deleted') {
        // Чат удалён - перезагрузим список
        privateChatStore.loadChats()

      } else if (data.action === 'user_typing') {
        // Показываем индикатор печати
        if (data.chat_id == route.params.id && data.user_id !== user.value?.id) {
          isOtherTyping.value = data.is_typing
        }
      } else if (data.action === 'new_message') {
        // Новое сообщение в чате
        if (data.message?.chat_id == route.params.id) {
          messages.value.push(data.message)
          nextTick(() => scrollToBottom())
        }
        // Обновить непрочитанные и списки чатов
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
      } else if (data.action === 'unread_updated') {
        // Обновить счётчик непрочитанных
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
      } else if (data.action === 'message_sent') {
        // Сообщение отправлено - обновить списки чатов
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
      } else if (data.action === 'unread_count_updated') {
        // Обновить счётчик непрочитанных
        privateChatStore.loadChats()
      }
    } catch (e) {
      console.error('Global WS error:', e)
    }
  }
    
  globalWs.onclose = () => {
    setTimeout(connectGlobalWebSocket, 5000)
  }
}

const sendTypingStart = () => {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'typing_start', user_id: user.value?.id, username: user.value?.username }))
  }
}

const sendTypingStop = () => {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'typing_stop', user_id: user.value?.id }))
  }
}

const handleTyping = () => {
  sendTypingStart()
  if (typingDebounceTimer) clearTimeout(typingDebounceTimer)
  typingDebounceTimer = window.setTimeout(sendTypingStop, 3000)
}

// Применение темы к DOM (определяем перед loadChat)
const applyThemeToDom = (theme: any) => {
  if (!theme) return
  const root = document.documentElement
  
  // Цвета сообщений
  if (theme.message_color_mine) root.style.setProperty(`--chat-msg-mine-bg`, theme.message_color_mine)
  if (theme.message_color_other) root.style.setProperty(`--chat-msg-other-bg`, theme.message_color_other)
  if (theme.message_text_color_mine) root.style.setProperty(`--chat-msg-mine-text`, theme.message_text_color_mine)
  if (theme.message_text_color_other) root.style.setProperty(`--chat-msg-other-text`, theme.message_text_color_other)
  
  // Шрифт
  if (theme.font_size_px) root.style.setProperty(`--chat-font-size`, theme.font_size_px + 'px')
  if (theme.font_family) root.style.setProperty(`--chat-font-family`, theme.font_family)
  if (theme.font_weight) root.style.setProperty(`--chat-font-weight`, theme.font_weight)
  
  // Пузыри
  if (theme.bubble_border_radius) root.style.setProperty(`--chat-bubble-radius`, theme.bubble_border_radius + 'px')
  if (theme.bubble_shadow !== undefined) root.style.setProperty(`--chat-bubble-shadow`, theme.bubble_shadow ? '0 2px 8px rgba(0,0,0,0.3)' : 'none')
  
  // Интерфейс
  if (theme.background_color) root.style.setProperty(`--chat-bg`, theme.background_color)
  if (theme.header_color) root.style.setProperty(`--chat-header-bg`, theme.header_color)
  if (theme.input_color) root.style.setProperty(`--chat-input-bg`, theme.input_color)
  if (theme.accent_color) root.style.setProperty(`--chat-accent`, theme.accent_color)
}

const loadChat = async () => {
  const chatId = currentChatId.value
  if (!chatId) {
    console.warn('Нет chatId для загрузки чата')
    return
  }
  try {
    const response = await apiClient.get(`/social/chats/${chatId}/`)
    if (response.data) {
      chat.value = response.data
      chat.value.type = (chat.value.user1 && chat.value.user2) ? 'private' : 'group'
      
      // Загружаем обои и тему параллельно
      const [wallpaperRes, themeRes] = await Promise.allSettled([
        apiClient.get(`/social/chat-settings/${chat.value.type}/${chatId}/wallpaper/`),
        apiClient.get(`/social/chat-settings/${chat.value.type}/${chatId}/theme/`)
      ])
      
      if (wallpaperRes.status === 'fulfilled' && wallpaperRes.value.data?.wallpaper) {
        currentWallpaper.value = wallpaperRes.value.data.wallpaper
      }
      
      if (themeRes.status === 'fulfilled' && themeRes.value.data?.theme) {
        currentTheme.value = themeRes.value.data.theme
        applyThemeToDom(themeRes.value.data.theme)
      }
    }
  } catch (error) {
    console.error('Chat load error:', error)
  }
}

const loadChatsForForward = async () => {
  loadingChats.value = true
  try {
    const response = await chatsApi.list()
    availableChats.value = (response as any).results || response
  } catch (error) {
    console.error('Error loading chats list:', error)
  } finally {
    loadingChats.value = false
  }
}

const sendMessageWithAttachment = async (type: string, objectId: number) => {
  if (!wsConnected.value || sending.value) return

  try {
    sending.value = true

    const chatId = currentChatId.value
    const messageData = {
      type: 'message',
      chat_id: chatId,
      text: '',
      reply_to: replyToMessage.value?.id || null,
      attachment_type: type,
      attachment_id: objectId,
    }

    ws?.send(JSON.stringify(messageData))

    // Reset
    replyToMessage.value = null
  } catch (error) {
    console.error('Failed to send message:', error)
  } finally {
    sending.value = false
  }
}

const sendMessage = async () => {
  const text = newMessage.value.trim()
  if (!text && !replyToMessage.value) return

  sending.value = true
  try {
    if (ws?.readyState === WebSocket.OPEN) {
      const messageData: any = { action: 'send_message', text }

      // Добавляем reply_to если есть ответ
      if (replyToMessage.value) {
        messageData.reply_to = replyToMessage.value.id
      }

      // Создаем временное сообщение для немедленного отображения
      const tempMessage = {
        id: -Date.now(), // Временный отрицательный ID
        text: text,
        sender_id: user.value?.id,
        sender_username: user.value?.username,
        sender_avatar: user.value?.avatar,
        created_at: new Date().toISOString(),
        reply_to: replyToMessage.value?.id,
        reply_to_message: replyToMessage.value ? {
          id: replyToMessage.value.id,
          sender_id: replyToMessage.value.sender_id,
          sender_username: replyToMessage.value.sender_username,
          sender_avatar: replyToMessage.value.sender_avatar || null,
          text: replyToMessage.value.text,
          media: replyToMessage.value.media || null,
          media_type: replyToMessage.value.media_type || null,
          created_at: replyToMessage.value.created_at
        } : null,
        is_edited: false,
        media: null,
        media_type: null,
        attachments: [],
        reactions: [],
        is_read_by_other: false,
        read_count: 0,
        is_mine: true
      }

      // Добавляем сообщение локально
      messages.value.push(tempMessage)
      messages.value = [...messages.value] // Триггерим реактивность
      await nextTick()
      scrollToBottom()

      ws.send(JSON.stringify(messageData))
      newMessage.value = ''
      replyToMessage.value = null
      sendTypingStop()

      // Обновить список чатов после отправки
      privateChatStore.loadChats()
      groupChatStore.loadGroupChats()
      chatExtrasStore.loadUnreadChats()
    } else {
      // WebSocket не доступен, используем HTTP
      try {
        const messageData: any = { text }

        // Добавляем reply_to если есть ответ
        if (replyToMessage.value) {
          messageData.reply_to = replyToMessage.value.id
        }

        if (chat.value?.user1 && chat.value?.user2) {
          messageData.private_chat = route.params.id
        } else {
          messageData.chat = route.params.id
        }

        const response = await apiClient.post('/social/messages/', messageData)

        if (response.data) {
          messages.value.push(response.data)
          await nextTick()
          scrollToBottom()
        }
        newMessage.value = ''
        replyToMessage.value = null

        // Обновить список чатов после отправки
        privateChatStore.loadChats()
        groupChatStore.loadGroupChats()
        chatExtrasStore.loadUnreadChats()
      } catch (error) {
        console.error('HTTP send error:', error)
      }
    }
  } catch (error) {
    console.error('Send error:', error)
  } finally {
    sending.value = false
  }
}

const attachFile = () => fileInput.value?.click()

const sendPlaylist = () => {
  if (!selectedPlaylist.value) return
  sendMessageWithAttachment('playlist', selectedPlaylist.value.id)
  showAttachPlaylist.value = false
  selectedPlaylist.value = null
}

const sendAnime = () => {
  if (!selectedAnime.value) return
  sendMessageWithAttachment('anime', selectedAnime.value.id)
  showAttachAnime.value = false
  selectedAnime.value = null
}

const loadPlaylists = async () => {
  try {
    const response = await apiClient.get('/playlists/playlists/my/')
    userPlaylists.value = response.data
  } catch (error) {
    console.error('Failed to load playlists:', error)
  }
}

const loadAnimes = async () => {
  try {
    const response = await apiClient.get('/anime/?limit=100')
    allAnimes.value = response.data.results || []
  } catch (error) {
    console.error('Failed to load animes:', error)
  }
}

const handleFileSelect = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  
  sending.value = true
  try {
    const formData = new FormData()
    formData.append('media', file)
    formData.append('text', '')
    
    if (chat.value?.user1 && chat.value?.user2) {
      formData.append('private_chat', String(route.params.id))
    } else {
      formData.append('chat', String(route.params.id))
    }
    
    const response = await apiClient.post('/social/messages/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    if (response.data) {
      messages.value.push(response.data)
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('Upload error:', error)
  } finally {
    sending.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

// Reactions
const handleReaction = async (messageId: number, emoji: string) => {
  try {
    await chatExtrasStore.toggleReaction(messageId, emoji)
  } catch (error) {
    console.error('Reaction error:', error)
  }
}

const getMessageReactions = (messageId: number) => {
  return chatExtrasStore.getReactionsForMessage(messageId)
}

const getReactionCount = (messageId: number, emoji: string) => {
  return chatExtrasStore.getReactionCount(messageId, emoji)
}



// Pinned Messages
const togglePinMessage = async (message: any) => {
  try {
    if (message.is_pinned) {
      await chatExtrasStore.unpinMessage(message.id)
      message.is_pinned = false
    } else {
      await chatExtrasStore.pinMessage(message.id)
      message.is_pinned = true
    }
  } catch (error) {
    console.error('Pin error:', error)
  }
}

// Message Actions
const handleReply = (message: any) => {
  replyToMessage.value = message
  ;(document.querySelector('.message-input') as HTMLInputElement)?.focus()
}

const cancelReply = () => {
  replyToMessage.value = null
}

const getMessageAuthorColor = (senderId: number): string => {
  const colors = ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a', '#fee140']
  const index = senderId % colors.length
  return colors[index] || '#667eea'
}

const handleForward = (message: any) => {
  messageToForward.value = message
  showForward.value = true
  // Загружаем список чатов если ещё не загружен
  if (availableChats.value.length === 0) {
    loadChatsForForward()
  }
}

const handleDelete = async (messageId: number) => {
  if (!confirm('Удалить сообщение?')) return

  try {
    await messageActionsApi.delete(messageId)
    messages.value = messages.value.filter(m => m.id !== messageId)
    closeContextMenu()
  } catch (error) {
    console.error('Delete error:', error)
  }
}

const showMessageMenu = (message: any, event: MouseEvent) => {
  event.preventDefault()
  selectedMessage.value = message
  
  const messageEl = (event.target as HTMLElement).closest('.message-content')
  if (!messageEl) return
  
  const messageRect = messageEl.getBoundingClientRect()
  const isOwnMessage = message.sender_id === user.value?.id
  
  const popupWidth = 180
  const popupHeight = 130
  
  const screenWidth = window.innerWidth
  const screenHeight = window.innerHeight
  
  let baseX: number
  let baseY = messageRect.top
  
  if (isOwnMessage) {
    baseX = messageRect.right + 12
  } else {
    baseX = messageRect.left - popupWidth - 12
  }
  
  if (baseX + popupWidth > screenWidth - 15) {
    baseX = screenWidth - popupWidth - 15
  }
  if (baseX < 15) {
    baseX = 15
  }
  
  if (baseY + popupHeight > screenHeight - 15) {
    baseY = messageRect.bottom - popupHeight - 8
    if (baseY < 15) {
      baseY = 15
    }
  }
  
  popupPosition.value = { x: baseX, y: baseY }
  contextMenu.value.visible = true
}

const closeContextMenu = () => {
  contextMenu.value.visible = false
}

const addReaction = async (emoji: string) => {
  if (selectedMessage.value) {
    await handleReaction(selectedMessage.value.id, emoji)
  }
  contextMenu.value.visible = false
}

// Invite
const handleInvite = () => {
  showInvite.value = true
}

const handleForwardComplete = () => {
  showForward.value = false
  messageToForward.value = null
}

const goToPost = (postId: number) => {
  window.open(`/post/${postId}`, '_blank')
}

// Сгруппировать реакции
const getGroupedReactions = (messageId: number): { emoji: string; count: number }[] => {
  const reactions = getMessageReactions(messageId)
  const grouped: Record<string, { emoji: string; count: number }> = {}
  
  reactions.forEach(r => {
    const emoji = r.emoji
    if (!grouped[emoji]) {
      grouped[emoji] = { emoji, count: 0 }
    }
    grouped[emoji]!.count++
  })
  
  const values = Object.values(grouped)
  return values as { emoji: string; count: number }[]
}

// Прокрутка к сообщению
const scrollToMessage = (messageId: number) => {
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`) as HTMLElement | null
  if (!messageElement) return

  messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
  messageElement.classList.add('highlighted')
  setTimeout(() => {
    messageElement.classList.remove('highlighted')
  }, 2000)
}

// Обработка изменений настроек
const handleSettingsChanged = async (data: any) => {
  console.log('Settings changed:', data)
  
  if (data?.type === 'wallpaper') {
    // Перезагружаем обои с сервера для получения актуальных данных
    await loadWallpaper()
  } else if (data?.type === 'theme') {
    // Перезагружаем тему
    await loadTheme()
  } else if (data?.type === 'organize') {
    // Обновляем настройки организации
    await loadChat()
  } else if (data?.type === 'clear' || data?.type === 'restore') {
    messages.value = []
  } else if (data?.type === 'leave') {
    // Выход из группы
    router.push('/chats')
  } else if (data?.type === 'delete') {
    // Удаление личного чата
    if (confirm('Удалить этот чат? Это действие нельзя отменить.')) {
      const chatId = currentChatId.value
      if (chatId) {
        await apiClient.delete(`/social/private-chats/${chatId}/`)
        router.push('/chats')
      }
    }
  }
}

// Загрузка обоев
const loadWallpaper = async () => {
  const chatId = currentChatId.value
  if (!chatId || !chat.value) return
  
  try {
    const chatType = chat.value.type
    const response = await apiClient.get(`/social/chat-settings/${chatType}/${chatId}/wallpaper/`)
    const data = response.data as any
    
    if (data?.wallpaper) {
      currentWallpaper.value = data.wallpaper
      console.log('Wallpaper loaded:', currentWallpaper.value)
    } else {
      currentWallpaper.value = null
    }
  } catch (error) {
    console.log('No wallpaper for this chat')
    currentWallpaper.value = null
  }
}

// Загрузка темы
const loadTheme = async () => {
  const chatId = currentChatId.value
  if (!chatId || !chat.value) return
  
  try {
    const chatType = chat.value.type
    const response = await apiClient.get(`/social/chat-settings/${chatType}/${chatId}/theme/`)
    const data = response.data as any
    
    if (data?.theme) {
      currentTheme.value = data.theme
      applyThemeToDom(data.theme)
    } else {
      currentTheme.value = null
    }
  } catch (error) {
    console.log('No theme for this chat')
    currentTheme.value = null
  }
}

// Стили обоев - blur применяется к псевдоэлементу, а не к контейнеру
const wallpaperStyle = computed(() => {
  if (!currentWallpaper.value) return {}
  
  const wp = currentWallpaper.value as any
  
  if (wp.wallpaper_type === 'solid') {
    return {
      '--wp-bg': wp.wallpaper_color || '#0f0f1a',
      '--wp-blur': '0px',
      '--wp-intensity': '1'
    }
  } else if (wp.wallpaper_type === 'gradient') {
    const angle = wp.gradient_angle || 135
    const color1 = wp.wallpaper_color || '#1a1a2e'
    const color2 = wp.wallpaper_color2 || '#0f0f1a'
    return {
      '--wp-bg': `linear-gradient(${angle}deg, ${color1}, ${color2})`,
      '--wp-blur': '0px',
      '--wp-intensity': '1'
    }
  } else if (wp.wallpaper_type === 'image') {
    const imageUrl = wp.wallpaper_image_url || wp.wallpaper_image
    if (imageUrl) {
      const blur = wp.wallpaper_blur ?? 0
      const intensity = (wp.wallpaper_intensity ?? 100) / 100
      return {
        '--wp-bg': `url(${imageUrl})`,
        '--wp-blur': `${blur}px`,
        '--wp-intensity': String(intensity)
      }
    }
  } else if (wp.wallpaper_type === 'pattern') {
    return {
      '--wp-bg': wp.wallpaper_color || '#0f0f1a',
      '--wp-blur': '0px',
      '--wp-intensity': '1'
    }
  }
  
  return {}
})

// Стили для фонового псевдоэлемента с blur
const wallpaperBgStyle = computed(() => {
  if (!currentWallpaper.value) return {}
  
  const wp = currentWallpaper.value as any
  const blur = wp.wallpaper_blur ?? 0
  const intensity = (wp.wallpaper_intensity ?? 100) / 100
  
  if (wp.wallpaper_type === 'image') {
    const imageUrl = wp.wallpaper_image_url || wp.wallpaper_image
    if (imageUrl) {
      return {
        backgroundImage: `url(${imageUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        filter: blur > 0 ? `blur(${blur}px) brightness(${intensity})` : `brightness(${intensity})`
      }
    }
  } else if (wp.wallpaper_type === 'gradient') {
    const angle = wp.gradient_angle || 135
    const color1 = wp.wallpaper_color || '#1a1a2e'
    const color2 = wp.wallpaper_color2 || '#0f0f1a'
    return {
      background: `linear-gradient(${angle}deg, ${color1}, ${color2})`
    }
  } else if (wp.wallpaper_type === 'solid') {
    return {
      background: wp.wallpaper_color || '#0f0f1a'
    }
  }
  
  return {}
})

// Загрузка списка чатов для пересылки
const loadChatsList = async () => {
  loadingChats.value = true
  try {
    const response = await chatsApi.list()
    availableChats.value = (response as any).results || response
  } catch (error) {
    console.error('Error loading chats list:', error)
  } finally {
    loadingChats.value = false
  }
}

// Отметить конкретные сообщения как прочитанные
const markMessagesAsRead = async (messageIds: number[]) => {
  if (!messageIds.length) return
  
  try {
    const chatId = route.params.id
    const chatType = chat.value?.type
    const endpoint = chatType === 'private'
      ? `/social/private-chats/${chatId}/mark_as_read/`
      : `/social/group-chats/${chatId}/mark_as_read/`
    
    // Отправляем IDs сообщений, которые нужно отметить
    await apiClient.post(endpoint, { message_ids: messageIds })
    
    // Обновляем статусы в локальном массиве
    const updatedMessages = messages.value.map(msg => {
      if (messageIds.includes(msg.id)) {
        return { ...msg, is_read_by_other: true }
      }
      return msg
    })
    messages.value = updatedMessages
    
  } catch (e) {
    console.log('Error marking messages as read:', e)
  }
}

// Автоматическое отметка сообщений как прочитанных при скролле
const setupMessageObserver = () => {
  if (!messagesContainer.value) return
  
  // Очищаем предыдущий observer
  if (messageObserver) {
    messageObserver.disconnect()
  }
  
  messageObserver = new IntersectionObserver(
    (entries) => {
      // Собираем IDs сообщений, которые стали видимыми
      const visibleMessageIds: number[] = []
      
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const messageEl = entry.target as HTMLElement
          const messageId = parseInt(messageEl.dataset.messageId || '0')
          const message = messages.value.find(m => m.id === messageId)
          
          // Отмечаем только сообщения от других пользователей, которые ещё не прочитаны
          if (message && 
              message.sender_id !== user.value?.id && 
              !message.is_read_by_other && 
              !readMessages.has(messageId)) {
            
            readMessages.add(messageId)
            visibleMessageIds.push(messageId)
          }
        }
      })
      
      // Отправляем запрос на отметку всех видимых сообщений
      if (visibleMessageIds.length > 0) {
        markMessagesAsRead(visibleMessageIds)
      }
    },
    {
      root: messagesContainer.value,
      threshold: 0.3 // Сообщение должно быть видно на 30%
    }
  )
  
  // Наблюдаем за всеми сообщениями
  nextTick(() => {
    const messageElements = messagesContainer.value?.querySelectorAll('.message-item')
    messageElements?.forEach((el) => {
      messageObserver?.observe(el)
    })
  })
}

onMounted(async () => {
  document.addEventListener('click', closeContextMenu)
  
  const chatId = currentChatId.value
  if (chatId) {
    await loadChat()
    await loadFranchiseParts()
    connectWebSocket()
    
    try {
      const chatType = chat.value?.type
      const endpoint = chatType === 'private'
        ? `/social/private-chats/${chatId}/mark_as_read/`
        : `/social/group-chats/${chatId}/mark_as_read/`
      await apiClient.post(endpoint)
    } catch (e) {
      console.error('Error marking all as read:', e)
    }
    
    nextTick(() => { setupMessageObserver() })
  }
  connectGlobalWebSocket()
  loadChatsList()
  chatExtrasStore.loadUnreadChats()
})

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
  disconnectWebSocket()
  if (globalWs) {
    globalWs.close()
    globalWs = null
  }
  if (typingDebounceTimer) clearTimeout(typingDebounceTimer)
  if (messageObserver) {
    messageObserver.disconnect()
    messageObserver = null
  }
  readMessages.clear()
})

// Следим за изменением prop.chatId (ChatsView) или route.params.id
watch(currentChatId, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    disconnectWebSocket()
    messages.value = []
    readMessages.clear()
    await loadChat()
    connectWebSocket()
    
    try {
      const chatType = chat.value?.type
      const endpoint = chatType === 'private'
        ? `/social/private-chats/${newId}/mark_as_read/`
        : `/social/group-chats/${newId}/mark_as_read/`
      await apiClient.post(endpoint)
    } catch (e) {
      console.error('Error marking all as read:', e)
    }
  }
})
</script>

<style scoped>
/* Стили обновлены с темой Sakura Bloom */
.chat-detail-view {
  height: 100dvh;
  max-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--surface-1);
  position: relative;
}

/* Фоновый узор */
.chat-detail-view::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 10% 90%, rgba(255,126,179,0.03) 0%, transparent 40%),
    radial-gradient(circle at 90% 10%, rgba(168,197,226,0.03) 0%, transparent 40%);
  pointer-events: none;
}

/* Мобильная адаптация - отступ сверху под мобильную навигацию */
@media (max-width: 767px) {
  .chat-detail-view {
    height: 100dvh;
    max-height: 100dvh;
    padding-top: 56px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
  }
  
  .chat-header {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
  }
  
  .messages-container {
    padding: 0.75rem;
  }
  
  .message-input-area {
    padding: 0.75rem;
  }
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: linear-gradient(180deg, var(--surface-2) 0%, var(--surface-3) 100%);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.back-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: var(--radius-md);
  transition: all var(--duration-base) var(--ease-petal);
}

.back-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.chat-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  flex-shrink: 0;
  border: 2px solid var(--accent-subtle);
  box-shadow: var(--shadow-petal-sm);
}

.chat-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.chat-name {
  font-weight: 600;
  color: var(--text-primary);
}

.chat-status, .chat-members {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online { 
  background: linear-gradient(135deg, var(--success) 0%, #34d399 100%);
  box-shadow: 0 0 8px var(--success);
}

.status-dot.offline { 
  background: var(--text-tertiary); 
}

.typing-indicator {
  display: inline-flex;
  gap: 2px;
}

.typing-indicator .dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--accent);
  animation: typing 1s infinite;
}

.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing { 
  0%, 100% { opacity: 0.4; } 
  50% { opacity: 1; } 
}

.info-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  top: 5px;
  cursor: pointer;
  opacity: 100;
  transform: translateY(-5px);
  color: var(--text-secondary);
  transition: color var(--duration-base) var(--ease-petal);
}

.info-btn:hover {
  color: var(--accent);
}

.header-actions { display: flex; gap: 0.5rem; }

.settings-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  transition: all var(--duration-base) var(--ease-petal);
}

.settings-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  min-height: 0;
  background: var(--surface-1);
  position: relative;
}

/* Псевдоэлемент для размытого фона обоев */
.wallpaper-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
  /* Изолируем blur от дочерних элементов */
  isolation: isolate;
  transform: translateZ(0);
  -webkit-transform: translateZ(0);
  will-change: transform;
}

/* Контент сообщений поверх фона */
.messages-container > *:not(.wallpaper-bg) {
  position: relative;
  z-index: 1;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.message-item {
  display: flex;
}

.message-item.own-message {
  justify-content: flex-end;
}

.message-content {
  max-width: 70%;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-xl);
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-subtle);
  font-size: var(--chat-font-size, 14px);
  font-family: var(--chat-font-family, system-ui);
  transition: all var(--duration-base) var(--ease-petal);
}

.own-message .message-content {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  border: none;
  box-shadow: var(--shadow-petal-sm);
}

.message-text {
  word-wrap: break-word;
  color: inherit;
  line-height: 1.4;
}

.message-image {
  max-width: 100%;
  border-radius: var(--radius-md);
}

.message-file a {
  color: var(--accent);
  text-decoration: none;
  transition: all var(--duration-base) var(--ease-petal);
}

.message-file a:hover {
  text-decoration: underline;
  color: var(--accent-press);
}

.message-time {
  font-size: 0.7rem;
  opacity: 0.9;
  margin-top: 0.15rem;
  color: var(--text-tertiary) !important;
}

.own-message .message-time {
  color: rgba(0,0,0,0.5) !important;
}

.message-input-area {
  padding: 1rem;
  background: linear-gradient(180deg, var(--surface-2) 0%, var(--surface-3) 100%);
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.message-form {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.message-input {
  flex: 1;
  padding: 1rem;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  outline: none;
  background: var(--surface-4);
  color: var(--text-primary);
  height: 3.5rem;
  font-size: 1rem;
  transition: all var(--duration-base) var(--ease-petal);
}

.message-input:focus {
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.message-input::placeholder {
  color: var(--text-tertiary);
}

.attach-btn, .send-btn {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--duration-base) var(--ease-petal);
}

.attach-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.attach-btn:hover:not(:disabled) {
  background: var(--surface-4);
  color: var(--text-primary);
}

.attach-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.attach-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attach-modal {
  background: var(--surface-2);
  border-radius: var(--radius-xl);
  padding: 20px;
  max-width: 400px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.attach-modal h3 {
  margin: 0 0 16px 0;
  color: var(--text-primary);
}

.search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--surface-1);
  color: var(--text-primary);
  margin-bottom: 16px;
}

.attach-list {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.attach-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
}

.attach-item:hover {
  background: var(--surface-4);
}

.attach-thumb {
  width: 40px;
  height: 60px;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.attach-info {
  flex: 1;
  min-width: 0;
}

.attach-title {
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attach-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

.attach-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.attach-actions button {
  padding: 8px 16px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--surface-1);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s;
}

.attach-actions button:hover {
  background: var(--surface-4);
}

.attach-actions button:last-child {
  background: var(--accent);
  color: var(--text-on-accent);
  border-color: var(--accent);
}

.attach-actions button:last-child:hover {
  background: var(--accent-hover);
}

.attach-btn:hover {
  background: var(--surface-5);
  color: var(--accent);
  border-color: var(--accent);
}

.send-btn {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  box-shadow: var(--shadow-petal-sm);
}

.send-btn:hover:not(:disabled) {
  box-shadow: var(--shadow-glow-sm);
  transform: scale(1.05);
}

.send-btn:disabled { 
  opacity: 0.5; 
  cursor: not-allowed; 
}

.ws-status {
  font-size: 0.75rem;
  color: var(--warning);
  text-align: center;
  padding-top: 0.25rem;
}

.chat-info-sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 280px;
  height: 100vh;
  background: var(--surface-2);
  border-left: 1px solid var(--border-default);
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--border-subtle);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text-secondary);
  transition: color var(--duration-base) var(--ease-petal);
}

.close-btn:hover {
  color: var(--accent);
}

.sidebar-content { 
  padding: 1rem; 
}

.sidebar-content h3,
.sidebar-content h4,
.sidebar-content h5,
.sidebar-content p {
  color: var(--text-primary);
}

.chat-avatar-large-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.chat-avatar-large {
  text-align: center;
}

.chat-avatar-large-row .close-btn {
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 1rem;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--duration-base) var(--ease-petal);
  flex-shrink: 0;
}

.chat-avatar-large-row .close-btn:hover {
  background: var(--danger-subtle);
  color: var(--danger);
  border-color: var(--danger);
}

.chat-avatar-large img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--accent);
  box-shadow: var(--shadow-petal-sm);
}

.participants-list { 
  margin-top: 1.5rem; 
}

.participants-list h5 {
  color: var(--text-tertiary);
  margin-bottom: 0.5rem;
}

.participant {
  padding: 0.5rem;
  border-radius: var(--radius-md);
  color: var(--text-primary);
  transition: all var(--duration-base) var(--ease-petal);
}

.participant:hover {
  background: var(--surface-4);
}

.loading, .no-messages {
  text-align: center;
  padding: 2rem;
  color: var(--text-tertiary);
}

/* Закрепленные сообщения */
.pinned-messages-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--warning-subtle);
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.875rem;
}

.pinned-label {
  color: var(--warning);
  font-weight: 500;
}

.pinned-message-preview {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
}

.pinned-close {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 1.25rem;
  padding: 0;
  transition: color var(--duration-base) var(--ease-petal);
}

.pinned-close:hover {
  color: var(--danger);
}

/* Сообщения */
.message-sender {
  font-size: 0.75rem;
  color: var(--accent);
  margin-bottom: 0.25rem;
  font-weight: 500;
}

/* Цитата (ответ на сообщение) */
.message-reply-quote {
  margin-bottom: 0.5rem;
  padding: 0.5rem 0.65rem;
  background: rgba(0, 0, 0, 0.15);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-base) var(--ease-petal);
  max-width: 100%;
  overflow: hidden;
}

.message-reply-quote:hover {
  background: rgba(0, 0, 0, 0.2);
}

.reply-quote-author {
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reply-quote-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reply-quote-image {
  margin-top: 0.35rem;
}

.reply-quote-image img {
  max-width: 100px;
  max-height: 60px;
  object-fit: cover;
  border-radius: var(--radius-sm);
}

.own-message .message-reply-quote {
  background: rgba(255, 255, 255, 0.15);
  border-left-color: rgba(255, 255, 255, 0.5);
}

.own-message .message-reply-quote:hover {
  background: rgba(255, 255, 255, 0.2);
}

.own-message .reply-quote-text {
  color: rgba(255, 255, 255, 0.8);
}

.message-footer {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.65rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.message-footer.own-footer {
  justify-content: flex-end;
}

.message-status {
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.25rem;
}

.message-status.sent, 
.message-status.read,
.message-status.group-read {
  color: rgba(0,0,0,0.5) !important;
}

.message-pinned, .message-edited {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.message-reactions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.35rem;
  margin-bottom: 0.25rem;
  max-width: calc(100% - 80px);
  padding-bottom: 0.25rem;
}

.reaction-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: var(--surface-3, rgba(0, 0, 0, 0.1));
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  cursor: pointer;
  transition: background var(--duration-base) var(--ease-petal);
  user-select: none;
}

.reaction-badge:hover {
  background: var(--surface-4, rgba(0, 0, 0, 0.15));
}

.reaction-collapsed {
  opacity: 0.5;
}

.message-actions {
  display: flex;
  gap: 0.25rem;
  margin-top: 0.5rem;
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-petal);
}

.message-item:hover .message-actions {
  opacity: 1;
}

.action-btn {
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  font-size: 0.75rem;
  color: var(--text-secondary);
  transition: all var(--duration-base) var(--ease-petal);
}

.action-btn:hover {
  background: var(--surface-5);
  border-color: var(--accent);
  color: var(--accent);
}

.action-btn.delete-btn:hover {
  background: var(--danger-subtle);
  border-color: var(--danger);
  color: var(--danger);
}

/* Кнопки заголовка */
.invite-btn, .search-btn {
  background: none;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.25rem;
  color: var(--text-secondary);
  transition: color var(--duration-base) var(--ease-petal);
}

.invite-btn:hover, .search-btn:hover {
  color: var(--accent);
}

/* Подсветка сообщения */
.message-item.highlighted {
  background: var(--accent-subtle);
  animation: highlight-pulse 2s ease-out;
}

@keyframes highlight-pulse {
  0%, 100% { background: var(--accent-subtle); }
  50% { background: rgba(255,126,179,0.15); }
}

/* Скрытый input для файлов */
.file-input {
  display: none;
}

/* Прокрутка */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: var(--surface-1);
}

.messages-container::-webkit-scrollbar-thumb {
  background: var(--surface-5);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: var(--accent-subtle);
}

.context-menu {
  position: fixed;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 0.25rem;
  z-index: 1000;
  min-width: 150px;
  box-shadow: var(--shadow-modal);
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: none;
  background: none;
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  border-radius: var(--radius-sm);
  text-align: left;
  transition: background var(--duration-base) var(--ease-petal);
}

.context-menu-item:hover {
  background: var(--surface-4);
}

.context-menu-item.delete:hover {
  background: var(--danger-subtle);
  color: var(--danger);
}

.context-menu-icon {
  font-size: 1rem;
}

/* Пикер реакций */
.reaction-picker {
  position: fixed;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  padding: 0.5rem;
  display: flex;
  gap: 0.25rem;
  z-index: 999;
  box-shadow: var(--shadow-modal);
}

.reaction-emoji-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  padding: 0.25rem;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background var(--duration-base) var(--ease-petal), transform 0.1s;
}

.reaction-emoji-btn:hover {
  background: var(--surface-4);
  transform: scale(1.2);
}

/* Единый popup с реакциями и контекстным меню */
.message-actions-popup {
  position: fixed;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  z-index: 1000;
  box-shadow: var(--shadow-modal);
  overflow: hidden;
}

.reaction-picker-container {
  display: flex;
  gap: 0.15rem;
  padding: 0.5rem;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border-subtle);
  flex-wrap: wrap;
  justify-content: center;
  max-width: 200px;
}

.reaction-picker-container .reaction-emoji-btn {
  font-size: 1.25rem;
  padding: 0.3rem;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background var(--duration-base) var(--ease-petal), transform 0.1s;
}

.reaction-picker-container .reaction-emoji-btn:hover {
  background: var(--surface-4);
  transform: scale(1.25);
}

.context-menu-actions {
  display: flex;
  flex-direction: column;
  padding: 0.25rem;
}

.context-menu-actions .context-menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: none;
  background: none;
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  border-radius: var(--radius-sm);
  text-align: left;
  transition: background var(--duration-base) var(--ease-petal);
}

.context-menu-actions .context-menu-item:hover {
  background: var(--surface-4);
}

.context-menu-actions .context-menu-item.delete:hover {
  background: var(--danger-subtle);
  color: var(--danger);
}

.context-menu-actions .context-menu-icon {
  font-size: 1rem;
}

/* Прикреплённый контент (посты, аниме, плейлисты, shorts) */
.message-shared-content {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: var(--surface-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

.forwarded-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.4rem;
  cursor: pointer;
}

.forwarded-icon {
  font-size: 0.85rem;
}

.forwarded-text {
  color: var(--text-tertiary);
}

.forwarded-source {
  color: var(--accent);
  font-weight: 500;
}

.shared-post,
.shared-anime,
.shared-playlist,
.shared-shorts {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: var(--radius-sm);
  transition: background var(--duration-fast);
}

.shared-post:hover,
.shared-anime:hover,
.shared-playlist:hover,
.shared-shorts:hover {
  background: var(--surface-4);
}

.shared-image {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.shared-poster {
  width: 40px;
  height: 56px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  background: var(--surface-3);
}

.shared-poster-grid {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 3px;
}

.shared-playlist-posters {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2px;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.shared-video {
  width: 100%;
  max-width: 200px;
  border-radius: var(--radius-md);
  background: #000;
}

.shared-shorts-thumb {
  position: relative;
  width: 80px;
  height: 120px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--surface-3);
}

.shared-shorts-thumb .play-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 1.5rem;
  color: white;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.shared-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.shared-author {
  font-size: 0.8rem;
  color: var(--accent);
  font-weight: 500;
}

.shared-title {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.shared-subtitle {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.shared-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.shared-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.7rem;
  color: var(--text-tertiary);
  margin-top: 0.1rem;
}

.shared-date {
  font-size: 0.7rem;
  color: var(--text-tertiary);
}

.shared-anime-tag {
  font-size: 0.7rem;
  color: var(--warning);
  background: var(--warning-subtle);
  padding: 0.15rem 0.4rem;
  border-radius: var(--radius-sm);
  display: inline-block;
  width: fit-content;
  margin-top: 0.25rem;
}
</style>