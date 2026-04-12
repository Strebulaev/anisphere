# UI Компоненты

## QuoteCard — Компонент цитирования

Универсальный компонент для отображения цитат/ответов в стиле Telegram.

### Использование

```vue
<template>
  <QuoteCard
    :quote="quoteData"
    :can-click="true"
    :show-avatar="true"
    @click="goToOriginal"
    @content-click="handleContentClick"
  />
</template>

<script setup lang="ts">
import QuoteCard from '@/components/ui/QuoteCard.vue'

const quoteData = {
  id: 123,
  author: {
    id: 456,
    username: 'username',
    avatar_url: 'https://example.com/avatar.jpg'
  },
  content: 'Текст цитируемого сообщения...',
  type: 'text', // 'text' | 'image' | 'video' | 'audio' | 'file'
  timestamp: '2024-01-15T10:30:00Z',
  post_id: 789, // или message_id, comment_id
  anime: {
    id: 1,
    title_ru: 'Название аниме',
    poster_url: 'https://example.com/poster.jpg'
  }
}

const goToOriginal = () => {
  // Переход к оригинальному сообщению/посту
}
</script>
```

### Props

| Поле | Тип | Обязательный | Описание |
|------|-----|--------------|----------|
| `quote` | `QuoteData` | Да | Данные цитаты |
| `canClick` | `boolean` | Нет | Разрешить клик (default: true) |
| `showAvatar` | `boolean` | Нет | Показывать аватар автора (default: true) |

### QuoteData Interface

```typescript
interface QuoteAuthor {
  id: number
  username: string
  avatar_url?: string | null
}

interface QuoteAnime {
  id: number
  title_ru: string
  poster_url?: string
}

interface QuoteData {
  id: number
  author?: QuoteAuthor
  content?: string
  type?: 'text' | 'image' | 'video' | 'audio' | 'file'
  anime?: QuoteAnime
  timestamp?: string
  post_id?: number
  message_id?: number
  comment_id?: number
}
```

### Events

| Событие | Аргументы | Описание |
|---------|-----------|----------|
| `click` | `quote.id` | Клик по всей цитате |
| `content-click` | `quote.id` | Клик по контенту цитаты |

### Особенности

- **Автоматическое определение типа контента**:
  - Текст: обрезается до 2 строк с "..."
  - Изображения: иконка 🖼️
  - Видео: иконка 🎬
  - Аудио: иконка 🎵
  - Файлы: иконка 📎
  
- **Аниме-карточки**: Мини-постер + название
- **Временные метки**: "мин. назад", "ч. назад", "дн. назад"
- **Адаптивность**: Работает на мобильных и десктопах
- **Стилизация**: Использует CSS-переменные темы

### Примеры использования

#### В постах (репосты)

```vue
<QuoteCard
  :quote="{
    author: post.original_post.author,
    content: post.original_post.text,
    type: getQuoteType(post.original_post),
    post_id: post.original_post.id
  }"
  @click="goToPost(post.original_post.id)"
/>
```

#### В чатах (ответы на сообщения)

```vue
<QuoteCard
  :quote="{
    author: {
      id: message.sender_id,
      username: message.sender_username,
      avatar_url: message.sender_avatar
    },
    content: message.text,
    timestamp: message.created_at,
    message_id: message.id
  }"
  @click="scrollToMessage(message.id)"
/>
```

#### В комментариях (ответы)

```vue
<QuoteCard
  :quote="{
    author: {
      id: comment.reply_to.author_id,
      username: comment.reply_to.author_username,
      avatar_url: comment.reply_to.author_avatar
    },
    content: comment.reply_to.text,
    timestamp: comment.reply_to.created_at,
    comment_id: comment.reply_to.id
  }"
  @click="focusComment(comment.reply_to.id)"
/>
```

### Стилизация

Компонент использует CSS-переменные темы:

```css
--accent
--accent-bright
--text-primary
--text-tertiary
--surface-4
--border-subtle
```

Можно переопределить для кастомизации:

```css
.quote-card {
  --quote-bg: #1a1a1a;
  --quote-border: #ff8a8a;
}
```
