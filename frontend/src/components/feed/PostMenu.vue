<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="post-menu" @click.stop>
      <!-- Edit (only for own posts within 5 min) -->
      <button v-if="post.can_edit" @click="$emit('edit', post)" class="menu-item">
        <span class="icon">✏️</span>
        <span>Редактировать</span>
      </button>

      <!-- Delete (only for own posts) -->
      <button v-if="post.can_delete" @click="$emit('delete', post)" class="menu-item danger">
        <span class="icon">🗑️</span>
        <span>Удалить</span>
      </button>

      <!-- Pin (only for own posts) -->
      <button v-if="post.can_edit && !post.is_pinned" @click="$emit('pin', post)" class="menu-item">
        <span class="icon">📌</span>
        <span>Закрепить в профиле</span>
      </button>

      <div class="menu-divider"></div>

      <!-- Report -->
      <button @click="$emit('report', post)" class="menu-item">
        <span class="icon">🚩</span>
        <span>Пожаловаться</span>
      </button>

      <!-- Bookmark -->
      <button @click="$emit('bookmark', post)" class="menu-item">
        <span class="icon">{{ post.is_bookmarked ? '⭐' : '☆' }}</span>
        <span>{{ post.is_bookmarked ? 'Удалить из закладок' : 'Сохранить в закладки' }}</span>
      </button>

      <!-- Hide -->
      <button @click="$emit('hide', post)" class="menu-item">
        <span class="icon">👁️</span>
        <span>Не интересно</span>
      </button>

      <div class="menu-divider"></div>

      <!-- Copy Link -->
      <button @click="copyLink" class="menu-item">
        <span class="icon">🔗</span>
        <span>Копировать ссылку</span>
      </button>

      <!-- Copy Text -->
      <button v-if="post.text" @click="copyText" class="menu-item">
        <span class="icon">📋</span>
        <span>Копировать текст</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Post {
  id: number
  text: string
  can_edit: boolean
  can_delete: boolean
  is_pinned: boolean
  is_bookmarked: boolean
}

const props = defineProps<{
  post: Post
}>()

defineEmits<{
  close: []
  edit: [post: Post]
  delete: [post: Post]
  pin: [post: Post]
  report: [post: Post]
  bookmark: [post: Post]
  hide: [post: Post]
}>()

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(`${window.location.origin}/post/${window.location.hash}`)
  } catch (error) {
    console.error('Error copying link:', error)
  }
}

const copyText = async () => {
  try {
    await navigator.clipboard.writeText(props.post.text)
  } catch (error) {
    console.error('Error copying text:', error)
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.post-menu {
  background: #111;
  border-radius: 12px;
  padding: 0.5rem;
  width: 90%;
  max-width: 300px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  background: none;
  border: none;
  color: #ddd;
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: background 0.2s;
  text-align: left;
}

.menu-item:hover {
  background: #1a1a1a;
}

.menu-item.danger:hover {
  background: #2a1515;
  color: #ef4444;
}

.menu-item .icon {
  font-size: 1.1rem;
}

.menu-divider {
  height: 1px;
  background: #1f1f1f;
  margin: 0.5rem 0;
}
</style>
