# Интеграция ответов и репостов в стиле Telegram

## Обзор

Реализована универсальная система ответов/репостов в стиле Telegram для всех компонентов приложения:
- Посты (репосты с комментарием)
- Сообщения чатов (ответы на сообщения)
- Комментарии (вложенные ответы)

## Созданные компоненты

### 1. QuoteCard.vue — Компонент цитирования

**Файл**: `frontend/src/components/ui/QuoteCard.vue`

Универсальный компонент для отображения цитат с:
- Аватаром и именем автора (кликабельно)
- Префиксом слева (3px accent border)
- Обрезкой текста до 2 строк с "..."
- Иконками для медиа-типов (изображение, видео, аудио, файл)
- Поддержкой карточек аниме
- Временными метками ("мин. назад", "ч. назад")

**Интерфейс**:
```typescript
interface QuoteData {
  id: number
  author?: {
    id: number
    username: string
    avatar_url?: string | null
  }
  content?: string
  type?: 'text' | 'image' | 'video' | 'audio' | 'file'
  anime?: {
    id: number
    title_ru: string
    poster_url?: string
  }
  timestamp?: string
  post_id?: number
  message_id?: number
  comment_id?: number
}
```

## Измененные файлы

### Frontend

#### 1. PostCard.vue
- Добавлена интеграция QuoteCard для репостов
- Отображение оригинального поста с цитатой
- Комментарий к репосту
- Превью оригинала при сворачивании

**Стили**:
```css
.repost-wrap { /* Контейнер репоста */ }
.repost-comment { /* Комментарий к репосту */ }
.original-post-preview { /* Превью оригинала */ }
```

#### 2. CommentItem.vue
- Полная переработка компонента
- Поддержка цитат через QuoteCard
- Улучшенная структура и стилизация
- Вложенные ответы с отступами

**Новые поля в интерфейсе**:
```typescript
interface Comment {
  // ... существующие поля
  reply_to?: {
    id: number
    author_id: number
    author_username: string
    author_avatar: string | null
    text: string
    created_at: string
  }
  is_edited: boolean
}
```

#### 3. ChatMessageInput.vue
- Добавлено поле для ответа на сообщение
- Превью ответа через QuoteCard
- Кнопка отмены ответа
- Передача `reply_to` в данные сообщения

**Props**:
```typescript
interface Props {
  chatId: number
  chatType: 'group' | 'private'
  replyToMessage?: ReplyToMessage | null
}
```

#### 4. types/chat.ts
- Добавлено поле `reply_to_message` в интерфейс Message
- Полная информация о цитируемом сообщении

```typescript
export interface Message {
  // ... существующие поля
  reply_to?: number
  reply_to_message?: {
    id: number
    sender_id: number
    sender_username: string
    sender_avatar?: string
    text: string
    created_at: string
  }
}
```

#### 5. assets/css/main.css
- Добавлены глобальные стили для чекбоксов (20px, accent-color)
- Унифицированный стиль для всех чекбоксов в приложении

#### 6. assets/base.css
- Добавлена переменная `--danger-hover: #b91c1c`

### Backend

#### 1. social/models.py
- Добавлено поле `reply_to` в модель Comment
- Добавлено поле `is_edited` в модель Comment
- Добавлены индексы для полей `parent` и `reply_to`

```python
class Comment(models.Model):
    # ...
    reply_to = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='answer_to'
    )
    is_edited = models.BooleanField(default=False)
```

#### 2. social/serializers.py
- Обновлен CommentSerializer с полем `reply_to_data`
- Добавлен метод `get_reply_to_data()` для полной информации о цитируемом комментарии

```python
class CommentSerializer(serializers.ModelSerializer):
    reply_to_data = serializers.SerializerMethodField()
    
    def get_reply_to_data(self, obj):
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'author_id': obj.reply_to.author_id,
                'author_username': obj.reply_to.author.username,
                'author_avatar': obj.reply_to.author.avatar.url if obj.reply_to.author.avatar else None,
                'text': obj.reply_to.text,
                'created_at': obj.reply_to.created_at.isoformat(),
            }
        return None
```

- MessageSerializer уже поддерживал `reply_to`, `reply_text`, `reply_sender_username`

## API Endpoints

### Комментарии
```
GET  /api/social/comments/{id}/     # Получение комментария с reply_to_data
POST /api/social/comments/           # Создание комментария
     {
       "text": "Ответ",
       "content_type": "post",
       "object_id": 123,
       "parent": 456,        # Родительский комментарий (дерево)
       "reply_to": 789       # Комментарий для цитаты (стиль Telegram)
     }
```

### Сообщения чатов
```
POST /api/social/messages/           # Создание сообщения
     {
       "text": "Ответ на сообщение",
       "chat": 1,
       "reply_to": 42        # ID сообщения для цитаты
     }
```

### Посты (репосты)
```
POST /api/social/posts/              # Создание репоста
     {
       "post_type": "repost",
       "original_post": 123,
       "repost_comment": "Мое мнение"
     }
```

## Использование

### 1. Ответ на сообщение в чате

```vue
<template>
  <div>
    <ChatMessageInput
      :chat-id="chatId"
      :chat-type="chatType"
      :reply-to-message="currentReplyTo"
      @send="handleSendMessage"
    />
    
    <!-- Кнопка ответа на сообщение -->
    <button @click="startReply(message)">
      Ответить
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ChatMessageInput from '@/components/Chats/ChatMessageInput.vue'

const currentReplyTo = ref<ReplyToMessage | null>(null)

const startReply = (message: Message) => {
  currentReplyTo.value = {
    id: message.id,
    sender_id: message.sender_id,
    sender_username: message.sender_username,
    sender_avatar: message.sender_avatar,
    text: message.text,
    created_at: message.created_at
  }
}

const handleSendMessage = async (data: any) => {
  // data.reply_to будет автоматически установлен
  await sendMessage(data)
  currentReplyTo.value = null
}
</script>
```

### 2. Отображение репоста

```vue
<template>
  <PostCard
    v-if="post.post_type === 'repost'"
    :post="post"
  />
</template>

<!-- Внутри PostCard.vue -->
<QuoteCard
  :quote="{
    author: post.original_post.author,
    content: post.original_post.text,
    type: getQuoteType(post.original_post),
    anime: post.original_post.anime,
    post_id: post.original_post.id
  }"
  @click="goToPost(post.original_post.id)"
/>
```

### 3. Ответ на комментарий

```vue
<template>
  <CommentItem
    :comment="comment"
    @reply="handleReply"
  />
</template>

<!-- Внутри CommentItem.vue -->
<QuoteCard
  v-if="comment.reply_to"
  :quote="{
    id: comment.reply_to.id,
    author: {
      id: comment.reply_to.author_id,
      username: comment.reply_to.author_username,
      avatar_url: comment.reply_to.author_avatar
    },
    content: comment.reply_to.text,
    timestamp: comment.reply_to.created_at,
    comment_id: comment.reply_to.id
  }"
  @click="goToComment(comment.reply_to.id)"
/>
```

## Создание миграции

Запустите команду для создания миграции:

```bash
cd backend
python manage.py makemigrations social
python manage.py migrate
```

Миграция добавит:
- Поле `reply_to` в таблицу `social_comment`
- Поле `is_edited` в таблицу `social_comment`
- Индексы для оптимизации запросов

## Тестирование

### Ручное тестирование

1. **Ответы в чатах**:
   - Откройте чат
   - Нажмите "Ответить" на сообщение
   - Убедитесь, что появляется превью цитаты
   - Отправьте ответ
   - Проверьте отображение цитаты в сообщении

2. **Репосты**:
   - Создайте пост с репостом
   - Убедитесь, что оригинальный пост отображается с цитатой
   - Проверьте клик по цитате (должен перейти к оригиналу)

3. **Ответы на комментарии**:
   - Ответьте на комментарий
   - Проверьте отображение цитаты
   - Проверьте вложенность ответов

### Автоматические тесты

```bash
# Backend
cd backend
python manage.py test social.tests

# Frontend
cd frontend
npm run test:unit
```

## Стилизация

### CSS-переменные

Компонент использует следующие переменные темы:
- `--accent` — Основной цвет
- `--accent-bright` — Яркий акцент (для имён пользователей)
- `--text-primary` — Основной текст
- `--text-tertiary` — Вторичный текст (время)
- `--surface-4` — Фон цитаты
- `--border-subtle` — Границы

### Кастомизация

```css
/* Переопределение стилей QuoteCard */
:root {
  --quote-bg: #1a1a1a;
  --quote-border: #ff8a8a;
  --quote-border-width: 3px;
}
```

## Масштабируемость

### Добавление новых типов контента

Для поддержки новых типов контента в цитатах:

1. Добавьте тип в `QuoteData.type`:
```typescript
type?: 'text' | 'image' | 'video' | 'audio' | 'file' | 'poll'
```

2. Добавьте обработку в `QuoteCard.vue`:
```vue
<template>
  <div v-if="quote.type === 'poll'" class="quote-poll">
    <!-- Отображение опроса -->
  </div>
</template>
```

3. Добавьте иконку в `getQuoteIcon()`:
```typescript
const getQuoteIcon = (type: string) => {
  const icons = {
    // ...
    poll: '📊',
  }
  return icons[type] || '📎'
}
```

## Будущие улучшения

- [ ] Поддержка упоминаний в цитатах (@username)
- [ ] Поддержка хэштегов в цитатах (#тег)
- [ ] Цитирование нескольких сообщений одновременно
- [ ] Редактирование цитат после создания
- [ ] Анимации при появлении цитат
- [ ] Поддержка стикеров в ответах
- [ ] Экспорт/импорт цитат

## Известные ограничения

1. Максимум 2 строки текста в цитате (можно изменить в `QuoteCard.vue`)
2. Один уровень вложенности для ответов на комментарии (избегаем бесконечной рекурсии)
3. Цитаты не кэшируются отдельно (загружаются с родительским объектом)

## Заключение

Система ответов и репостов полностью интегрирована во все компоненты приложения. Компонент `QuoteCard` является переиспользуемым и может быть использован в любых местах где нужно отображение цитат.
