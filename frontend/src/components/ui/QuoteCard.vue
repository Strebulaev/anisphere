<template>
  <div class="quote-card" @click="handleClick" :class="{ 'clickable': canClick }">
    <div class="quote-header">
      <Avatar 
        v-if="showAvatar" 
        :user="quote.author" 
        :size="avatarSize" 
        class="quote-avatar"
      />
      <div class="quote-author-row">
        <span class="quote-author" v-if="quote.author">
          {{ quote.author.username }}
        </span>
        <span class="quote-time" v-if="quote.timestamp">
          {{ formatTime(quote.timestamp) }}
        </span>
      </div>
    </div>
    
    <div class="quote-content" @click.stop="handleContentClick">
      <!-- Текстовый контент -->
      <p class="quote-text" v-if="quote.type === 'text' || !quote.type">
        {{ truncateText(quote.content || quote.preview_text || '', maxLines) }}
      </p>
      
      <!-- Медиа контент -->
      <div v-else-if="quote.type === 'image'" class="quote-media">
        <SakuraIcon name="image" :size="20" />
        <span>Фото</span>
      </div>
      
      <div v-else-if="quote.type === 'video'" class="quote-media">
        <SakuraIcon name="video" :size="20" />
        <span>Видео</span>
      </div>
      
      <div v-else-if="quote.type === 'audio'" class="quote-media">
        <SakuraIcon name="music" :size="20" />
        <span>Аудио</span>
      </div>
      
      <div v-else-if="quote.type === 'file'" class="quote-media">
        <SakuraIcon name="file" :size="20" />
        <span>Файл</span>
      </div>
      
      <!-- Сообщение с аниме -->
      <div v-else-if="quote.anime" class="quote-anime">
        <div class="anime-mini">
          <img 
            v-if="quote.anime.poster_url" 
            :src="quote.anime.poster_url" 
            :alt="quote.anime.title_ru"
            class="anime-poster"
          />
          <div class="anime-info">
            <div class="anime-title">{{ quote.anime.title_ru || quote.anime.title_en }}</div>
            <div class="anime-meta">
              <span v-if="quote.anime.episode" class="episode">
                Эпизод {{ quote.anime.episode }}
              </span>
              <span v-if="quote.anime.score" class="score">
                ⭐ {{ quote.anime.score }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Заглушка для других типов -->
      <div v-else class="quote-fallback">
        <SakuraIcon name="info" :size="16" />
        <span>Сообщение</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import Avatar from '@/components/ui/Avatar.vue'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'

interface QuoteAuthor {
  id: number | string
  username: string
  avatar_url?: string
}

interface QuoteAnime {
  id: number
  title_ru: string
  title_en?: string
  poster_url?: string | null
  episode?: number
  score?: number
}

export interface QuoteData {
  id?: number | string
  author?: QuoteAuthor
  content?: string
  preview_text?: string
  type?: 'text' | 'image' | 'video' | 'audio' | 'file'
  anime?: QuoteAnime
  timestamp?: string | number
  post_id?: number
  message_id?: number
  comment_id?: number
  chat_id?: number
}

const props = withDefaults(defineProps<{
  quote: QuoteData
  canClick?: boolean
  showAvatar?: boolean
  avatarSize?: 'xs' | 'sm' | 'md' | 'lg'
  maxLines?: number
  onClick?: (quote: QuoteData) => void
  onContentClick?: (quote: QuoteData) => void
}>(), {
  canClick: true,
  showAvatar: true,
  avatarSize: 'sm',
  maxLines: 2
})

const emit = defineEmits<{
  (e: 'click', quote: QuoteData): void
  (e: 'content-click', quote: QuoteData): void
}>()

const handleClick = () => {
  if (props.canClick && props.onClick) {
    props.onClick(props.quote)
    emit('click', props.quote)
  }
}

const handleContentClick = () => {
  if (props.onContentClick) {
    props.onContentClick(props.quote)
    emit('content-click', props.quote)
  }
}

const truncateText = (text: string, maxLines: number) => {
  if (!text) return ''
  
  const charsPerLine = 80
  const maxChars = charsPerLine * maxLines
  
  if (text.length <= maxChars) return text
  
  return text.substring(0, maxChars - 3) + '...'
}

const formatTime = (timestamp: string | number) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffMins < 1) return 'только что'
  if (diffMins < 60) return `${diffMins} мин назад`
  if (diffHours < 24) return `${diffHours} ч назад`
  if (diffDays < 7) return `${diffDays} дн назад`
  
  return date.toLocaleDateString('ru-RU')
}
</script>

<style scoped>
.quote-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  background: var(--surface-4);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-md);
  transition: all 0.15s var(--ease-petal);
  cursor: default;
}

.quote-card.clickable {
  cursor: pointer;
}

.quote-card.clickable:hover {
  background: var(--surface-5);
  transform: translateX(2px);
}

.quote-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quote-avatar {
  flex-shrink: 0;
}

.quote-author-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.quote-author {
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--accent-bright);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quote-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.quote-content {
  display: flex;
  align-items: center;
  min-height: 20px;
}

.quote-text {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-primary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: v-bind(maxLines);
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quote-media,
.quote-fallback {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  padding: 4px 0;
}

.quote-anime {
  width: 100%;
}

.anime-mini {
  display: flex;
  gap: 8px;
  align-items: center;
}

.anime-poster {
  width: 36px;
  height: 50px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.anime-info {
  flex: 1;
  min-width: 0;
}

.anime-title {
  font-weight: 500;
  font-size: var(--text-sm);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.anime-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.episode {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.score {
  font-size: var(--text-xs);
  color: var(--warning);
  font-weight: 600;
}
</style>
