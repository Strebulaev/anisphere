<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="repost-modal" @click.stop>
      <div class="modal-header">
        <h2>Сделать репост</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- Original Post Preview -->
      <div class="original-post" v-if="post">
        <div class="preview-label">Оригинальный пост:</div>
        <div class="post-preview">
          <img :src="post.author_avatar || defaultAvatar" class="avatar">
          <div class="preview-content">
            <span class="author">{{ post.author_display_name || post.author_username }}</span>
            <span class="text">{{ truncateText(post.text, 100) }}</span>
          </div>
        </div>
      </div>

      <!-- Comment -->
      <div class="comment-section">
        <label>Добавить комментарий:</label>
        <textarea
          v-model="comment"
          placeholder="Ваш комментарий (опционально)"
          maxlength="500"
        ></textarea>
        <span class="char-count">{{ comment.length }}/500</span>
      </div>

      <!-- Destination -->
      <div class="destination-section">
        <label>Куда репостнуть:</label>
        <div class="destination-options">
          <label class="option" :class="{ selected: destination === 'feed' }">
            <input type="radio" value="feed" v-model="destination">
            <span class="icon">📱</span>
            <div class="option-content">
              <span class="title">В мою ленту</span>
              <span class="desc">Пост появится в вашем профиле</span>
            </div>
          </label>

          <label class="option" :class="{ selected: destination === 'group' }">
            <input type="radio" value="group" v-model="destination">
            <span class="icon">👥</span>
            <div class="option-content">
              <span class="title">В группу</span>
              <span class="desc">Выберите группу</span>
            </div>
          </label>

          <label class="option" :class="{ selected: destination === 'chat' }">
            <input type="radio" value="chat" v-model="destination">
            <span class="icon">💬</span>
            <div class="option-content">
              <span class="title">В личные сообщения</span>
              <span class="desc">Отправить другу</span>
            </div>
          </label>
        </div>
      </div>

      <!-- Group Selector -->
      <div v-if="destination === 'group'" class="selector-section">
        <label>Выберите группу:</label>
        <div class="groups-list">
          <div
            v-for="group in groups"
            :key="group.id"
            class="group-item"
            :class="{ selected: selectedGroup?.id === group.id }"
            @click="selectedGroup = group"
          >
            <img :src="group.avatar || defaultAvatar" class="avatar-sm">
            <span>{{ group.name }}</span>
          </div>
          <div v-if="groups.length === 0" class="empty">
            Вы не состоите в группах
          </div>
        </div>
      </div>

      <!-- Chat Selector -->
      <div v-if="destination === 'chat'" class="selector-section">
        <label>Выберите чат:</label>
        <div class="chats-list">
          <div
            v-for="chat in chats"
            :key="chat.id"
            class="chat-item"
            :class="{ selected: selectedChat?.id === chat.id }"
            @click="selectedChat = chat"
          >
            <img :src="chat.avatar || defaultAvatar" class="avatar-sm">
            <span>{{ chat.name }}</span>
          </div>
          <div v-if="chats.length === 0" class="empty">
            Нет чатов
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">Отмена</button>
        <button
          class="btn-repost"
          :disabled="!canRepost || reposting"
          @click="submitRepost"
        >
          {{ reposting ? 'Репост...' : 'Репостнуть' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/api/client'

interface Post {
  id: number
  author_username: string
  author_avatar: string | null
  author_display_name: string | null
  text: string
}

interface Group {
  id: number
  name: string
  avatar: string | null
}

interface Chat {
  id: number
  name: string
  avatar: string | null
}

const props = defineProps<{
  post: Post | null
}>()

const emit = defineEmits<{
  close: []
  reposted: [post: Post]
}>()

const defaultAvatar = '/img/default-avatar.svg'

const comment = ref('')
const destination = ref<'feed' | 'group' | 'chat'>('feed')
const selectedGroup = ref<Group | null>(null)
const selectedChat = ref<Chat | null>(null)
const groups = ref<Group[]>([])
const chats = ref<Chat[]>([])
const reposting = ref(false)

const canRepost = computed(() => {
  if (destination.value === 'feed') return true
  if (destination.value === 'group') return selectedGroup.value !== null
  if (destination.value === 'chat') return selectedChat.value !== null
  return false
})

const truncateText = (text: string, length: number) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const loadGroups = async () => {
  try {
    const response = await apiClient.get('/social/groups/my/')
    groups.value = response.data.results || []
  } catch (error) {
    console.error('Error loading groups:', error)
  }
}

const loadChats = async () => {
  try {
    const response = await apiClient.get('/social/chats/')
    chats.value = response.data.results || []
  } catch (error) {
    console.error('Error loading chats:', error)
  }
}

const submitRepost = async () => {
  if (!props.post || !canRepost.value) return

  reposting.value = true

  try {
    const data: any = {
      comment: comment.value
    }

    if (destination.value === 'group' && selectedGroup.value) {
      data.group_id = selectedGroup.value.id
    } else if (destination.value === 'chat' && selectedChat.value) {
      data.chat_id = selectedChat.value.id
    }

    await apiClient.post(`/social/posts/${props.post.id}/repost/`, data)
    emit('reposted', props.post)
  } catch (error) {
    console.error('Error reposting:', error)
    alert('Ошибка при репосте')
  } finally {
    reposting.value = false
  }
}

onMounted(() => {
  loadGroups()
  loadChats()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.repost-modal {
  background: #111;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.modal-header h2 {
  color: #fff;
  font-size: 1.25rem;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.25rem;
  cursor: pointer;
}

.original-post {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.preview-label {
  color: #666;
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
}

.post-preview {
  display: flex;
  gap: 0.75rem;
  background: #1a1a1a;
  padding: 0.75rem;
  border-radius: 8px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.preview-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.author {
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
}

.text {
  color: #888;
  font-size: 0.85rem;
}

.comment-section {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.comment-section label {
  display: block;
  color: #888;
  margin-bottom: 0.5rem;
}

.comment-section textarea {
  width: 100%;
  min-height: 60px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 0.75rem;
  color: #ddd;
  resize: vertical;
}

.comment-section textarea:focus {
  outline: none;
  border-color: #667eea;
}

.char-count {
  display: block;
  text-align: right;
  color: #555;
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

.destination-section {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.destination-section label {
  display: block;
  color: #888;
  margin-bottom: 0.75rem;
}

.destination-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #1a1a1a;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option:hover {
  background: #252525;
}

.option.selected {
  background: #252525;
  border: 1px solid #667eea;
}

.option input {
  display: none;
}

.option .icon {
  font-size: 1.25rem;
}

.option-content {
  display: flex;
  flex-direction: column;
}

.option-content .title {
  color: #fff;
  font-weight: 500;
}

.option-content .desc {
  color: #666;
  font-size: 0.8rem;
}

.selector-section {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.selector-section label {
  display: block;
  color: #888;
  margin-bottom: 0.75rem;
}

.groups-list,
.chats-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
}

.group-item,
.chat-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.group-item:hover,
.chat-item:hover {
  background: #1a1a1a;
}

.group-item.selected,
.chat-item.selected {
  background: #252525;
  border: 1px solid #667eea;
}

.avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.group-item span,
.chat-item span {
  color: #ddd;
}

.empty {
  color: #666;
  text-align: center;
  padding: 1rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
}

.btn-cancel {
  background: #1a1a1a;
  color: #888;
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
}

.btn-repost {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-repost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
