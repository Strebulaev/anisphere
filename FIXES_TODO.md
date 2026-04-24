# Список исправлений для Anisphere

## 1. ❌ Чат/группа открывается как отдельная страница

**Проблема:** Чат открывается по `/chat/{id}` как отдельная страница, а не как под-компонент страницы чатов.

**Решение:**
- Изменить роутинг в `frontend/src/router/index.ts`
- Чат должен быть child route `/chats/:id` вместо отдельного `/chat/:id`

---

## 2. ⚠️ API 500: `/social/group-chats/` Error creating chat

**Проблема:** Повреждён метод `get_queryset()` в `GroupChatViewSet` (backend/social/views.py, строка ~2418)

**Исправление:**
```python
def get_queryset(self):
    try:
        return GroupChat.objects.filter(
            members__user=self.request.user
        ).select_related('created_by').prefetch_related('members', 'members__user').order_by('-last_message_at', '-created_at')
    except Exception as e:
        print(f"DEBUG GroupChatViewSet get_queryset error: {e}")
        import traceback
        traceback.print_exc()
        return GroupChat.objects.none()

def perform_create(self, serializer):
    """Создание группового чата"""
    try:
        chat = serializer.save(created_by=self.request.user)
        
        # Создаём запись о создателе как админе
        ChatMember.objects.create(
            user=self.request.user,
            chat=chat,
            is_admin=True,
            is_owner=True
        )
        
        # Логируем создание
        ChatAdminLog.objects.create(
            chat=chat,
            user=self.request.user,
            action='chat_created',
            details={'chat_name': chat.name}
        )
    except Exception as e:
        print(f"DEBUG GroupChatViewSet perform_create error: {e}")
        import traceback
        traceback.print_exc()
        raise
```

---

## 3. ⚠️ API 500: `/social/users/22/posts/`

**Проблема:** Ошибка при загрузке постов пользователя

**Причина:** Возможно проблема в сериализаторе PostSerializer при обработке медиафайлов или полей с null значениями.

**Решение:** Проверить `get_user_posts` в backend/social/views.py (строка ~1442) и добавить обработку ошибок:

```python
@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_posts(request, user_id):
    """Получить посты конкретного пользователя"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=404)

    posts = Post.objects.filter(
        author=user,
        status='published'
    ).order_by('-created_at')

    # Пагинация
    page = int(request.query_params.get('page', 1))
    limit = int(request.query_params.get('limit', 20))
    offset = (page - 1) * limit

    total = posts.count()
    posts = posts[offset:offset + limit]

    try:
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response({
            'count': total,
            'page': page,
            'limit': limit,
            'results': serializer.data
        })
    except Exception as e:
        import logging
        logging.error(f"Error serializing posts for user {user_id}: {e}", exc_info=True)
        return Response({'error': 'Ошибка при сериализации постов', 'detail': str(e)}, status=500)
```

---

## 4. 💬 Цитата сообщения исчезает после отправки

**Проблема:** При ответе на сообщение цитата появляется, но после отправки исчезает вместо того чтобы остаться у сообщения.

**Причина:** 
- Фронтенд: `replyToMessage.value = null` после отправки (это правильно)
- Бэкенд: reply_to сохраняется, но `reply_to_message` может не возвращаться корректно

**Решение:**
1. Проверить, что WebSocket обработчик сохраняет `reply_to`
2. Проверить, что MessageSerializer возвращает `reply_to_message`
3. На фронтенде отображать `message.reply_to_message` для каждого сообщения

**Файлы:**
- `backend/social/consumers.py` - обработчик WebSocket
- `frontend/src/components/page/chats/ChatDetailView.vue` - отображение цитаты в сообщении

---

## 5. 📋 Список чатов при репосте/пересылке неверный

**Проблема:** В модальных окнах репоста и пересылки список чатов загружается некорректно.

**Решение:**
- Проверить `chatsApi.list()` в `frontend/src/api/chats.ts`
- Убедиться, что endpoint `/social/chats/` возвращает объединённый список личных и групповых чатов
- Проверить `CombinedChatsView` в backend

---

## 6. 🎵 Кнопки плейлистов в профиле не работают

**Проблема:** В профиле пользователя в разделе плейлисты не работают кнопки:
- "Добавить в избранное"
- "Поделиться"  
- "Изменить" (только для владельца)
- "Удалить" (только для владельца)

**Решение:**
- Проверить компонент `frontend/src/components/page/profile/ProfilePlaylists.vue`
- Добавить обработчики событий для кнопок
- Проверить права доступа для кнопок "Изменить"/"Удалить"

---

## 7. 📱 Адаптация для мобильных

**Проблема:** На мобильных устройствах чат занимает весь экран, нет кнопки "назад"

**Решение:**
- Добавить кнопку "назад" в шапку чата для мобильных устройств
- Реализовать навигацию назад к списку чатов

---

## Приоритеты:

1. **Критично:** Исправить API 500 ошибки (пункты 2, 3)
2. **Важно:** Исправить цитирование сообщений (пункт 4)
3. **Важно:** Исправить роутинг чатов (пункт 1)
4. **Средне:** Исправить список чатов (пункт 5)
5. **Средне:** Исправить кнопки плейлистов (пункт 6)
