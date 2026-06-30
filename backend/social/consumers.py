"""
WebSocket consumers for real-time chat functionality
"""

import json
import asyncio
import threading
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from users.models import User
from .models import PrivateChat, GroupChat, Message
from core.online_status import online_status, typing_status
import redis
from django.conf import settings


class GlobalEventsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for global events (chat created, user online, etc.)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_id = None
        self.redis_listener_thread = None
        self.should_listen = True

    async def connect(self):
        """Handle WebSocket connection"""
        # Get token from query string
        token = self.scope.get("query_string", b"").decode()
        if "token=" in token:
            token = token.split("token=")[1].split("&")[0]
        else:
            token = None

        if token:
            self.user = await self.get_user_from_token(token)

        if not self.user:
            await self.close(code=4001)
            return

        self.user_id = self.user.id

        # Join user-specific group for personal notifications
        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)

        await self.accept()

        # Start Redis listener in background
        self.should_listen = True
        self.redis_listener_thread = threading.Thread(
            target=self._listen_redis, daemon=True
        )
        self.redis_listener_thread.start()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        self.should_listen = False

        if self.user_id:
            await self.channel_layer.group_discard(
                f"user_{self.user_id}", self.channel_name
            )

    def _listen_redis(self):
        """Listen to Redis pub/sub in background thread"""
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            redis_client.ping()

            pubsub = redis_client.pubsub()
            pubsub.subscribe("realtime_updates")

            for message in pubsub.listen():
                if not self.should_listen:
                    break
                if message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        # Run async send in event loop
                        asyncio.run(self._send_event_to_client(event))
                    except:
                        pass
        except redis.ConnectionError:
            print(f"Redis connection failed - real-time updates disabled")
        except Exception as e:
            print(f"Redis listener error: {e}")

    async def _send_event_to_client(self, event):
        """Send event to WebSocket client"""
        try:
            event_type = event.get("type")
            data = event.get("data", {})

            # Check if this event is for this user
            target_users = event.get("target_users")
            if target_users and self.user_id not in target_users:
                return

            # Send appropriate action based on event type
            if event_type == "chat_created":
                await self.send(
                    text_data=json.dumps({"action": "chat_created", "chat": data})
                )
            elif event_type == "chat_deleted":
                await self.send(
                    text_data=json.dumps(
                        {
                            "action": "chat_deleted",
                            "chat_id": data.get("chat_id"),
                            "chat_type": data.get("chat_type"),
                        }
                    )
                )
            elif event_type == "user_online":
                await self.send(
                    text_data=json.dumps(
                        {
                            "action": "user_online",
                            "user_id": data.get("user_id"),
                            "username": data.get("username"),
                        }
                    )
                )
            elif event_type == "user_offline":
                await self.send(
                    text_data=json.dumps(
                        {"action": "user_offline", "user_id": data.get("user_id")}
                    )
                )
            elif event_type == "user_typing":
                await self.send(
                    text_data=json.dumps(
                        {
                            "action": "user_typing",
                            "chat_id": data.get("chat_id"),
                            "user_id": data.get("user_id"),
                            "username": data.get("username"),
                            "is_typing": data.get("is_typing"),
                        }
                    )
                )
            elif event_type == "message_sent":
                await self.send(
                    text_data=json.dumps({"action": "new_message", "message": data})
                )
            elif event_type == "new_post":
                await self.send(
                    text_data=json.dumps({"type": "new_post", "data": data})
                )
            elif event_type == "post_liked":
                await self.send(
                    text_data=json.dumps({"type": "post_liked", "data": data})
                )
            elif event_type == "post_commented":
                await self.send(
                    text_data=json.dumps({"type": "post_commented", "data": data})
                )
            elif event_type == "post_reposted":
                await self.send(
                    text_data=json.dumps({"type": "post_reposted", "data": data})
                )
            elif event_type == "new_follower":
                await self.send(
                    text_data=json.dumps({"type": "new_follower", "data": data})
                )
        except Exception as e:
            print(f"Error sending event to client: {e}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "ping":
                await self.send(text_data=json.dumps({"action": "pong"}))
            elif action == "subscribe_chat":
                chat_id = data.get("chat_id")
                if chat_id:
                    await self.channel_layer.group_add(
                        f"chat_{chat_id}", self.channel_name
                    )
            elif action == "unsubscribe_chat":
                chat_id = data.get("chat_id")
                if chat_id:
                    await self.channel_layer.group_discard(
                        f"chat_{chat_id}", self.channel_name
                    )
        except json.JSONDecodeError:
            pass

    async def notification_event(self, event):
        """
        Handle notification events sent via channel_layer.group_send().
        NotificationService sends: {'type': 'notification_event', 'action': 'notification', 'notification': {...}}
        """
        try:
            await self.send(
                text_data=json.dumps(
                    {
                        "action": event.get("action", "notification"),
                        "notification": event.get("notification", {}),
                    }
                )
            )
        except Exception as e:
            print(f"Error sending notification event: {e}")

    async def chat_message(self, event):
        """Forward chat messages from channel layer to WebSocket."""
        try:
            await self.send(
                text_data=json.dumps(
                    {
                        "action": "new_message",
                        "message": event.get("message", {}),
                    }
                )
            )
        except Exception as e:
            print(f"Error sending chat message: {e}")

    @database_sync_to_async
    def get_user_from_token(self, token):
        """Get user from JWT token"""
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return None


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat messages
    Handles real-time message delivery and typing status
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_id = None
        self.chat_type = None
        self.user = None
        self.user_id = None
        self.group_name = None
        self.typing_task = None
        self.topic_id = None

    async def connect(self):
        """Handle WebSocket connection"""
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.group_name = f"chat_{self.chat_id}"

        # Authenticate user from token
        token = (
            self.scope.get("query_string", b"").decode().split("=")[-1]
            if "token=" in self.scope.get("query_string", b"").decode()
            else None
        )

        if token:
            self.user = await self.get_user_from_token(token)

        if not self.user:
            # Try to get user from session
            if self.scope.get("user") and self.scope["user"].is_authenticated:
                self.user = self.scope["user"]
            else:
                # Allow connection for anonymous users (for demo)
                self.user = None

        if self.user:
            self.user_id = self.user.id
            # Set user online
            self.set_user_online()

            # Подписываемся на события онлайн статуса этого пользователя
            self.user_online_group = f"user_online_{self.user_id}"
            await self.channel_layer.group_add(self.user_online_group, self.channel_name)

            # ВАЖНО: Подписываемся на личную группу пользователя для получения событий о прочтении
            self.user_personal_group = f"chat_user_{self.user_id}"
            await self.channel_layer.group_add(self.user_personal_group, self.channel_name)
            print(f"DEBUG: User {self.user_id} subscribed to {self.user_personal_group}")

        # Determine chat type
        self.chat_type = await self.get_chat_type()

        if not self.chat_type:
            await self.close(code=4004)
            return

        # Join chat group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

        # Send initial data
        await self.send_initial_data()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, "group_name") and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        if hasattr(self, "user_online_group") and self.user_online_group:
            await self.channel_layer.group_discard(self.user_online_group, self.channel_name)

        # Отписываемся от личной группы пользователя
        if hasattr(self, "user_personal_group") and self.user_personal_group:
            await self.channel_layer.group_discard(self.user_personal_group, self.channel_name)

        if self.user_id:
            # Set user offline
            self.set_user_offline()

        # Cancel typing task if exists
        if self.typing_task:
            self.typing_task.cancel()

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "send_message":
                await self.handle_send_message(data)
            elif action == "typing_start":
                await self.handle_typing_start()
            elif action == "typing_stop":
                await self.handle_typing_stop()
            elif action == "mark_read":
                await self.handle_mark_read(data)
            elif action == "get_messages":
                await self.send_initial_data()
            elif action == "set_topic":
                self.topic_id = data.get("topic_id")
                await self.send_initial_data()
            elif action == "ping":
                await self.send(text_data=json.dumps({"action": "pong"}))
            elif action == "subscribe_user_online":
                # Подписка на статус онлайн другого пользователя
                other_user_id = data.get("user_id")
                if other_user_id:
                    self.other_user_online_group = f"user_online_{other_user_id}"
                    await self.channel_layer.group_add(self.other_user_online_group, self.channel_name)
                    # Отправим текущий статус
                    is_online = online_status.is_online(other_user_id)
                    await self.send(
                        text_data=json.dumps({
                            "action": "user_online",
                            "user_id": other_user_id,
                            "is_online": is_online,
                        })
                    )
        except Exception as e:
            print(f"WebSocket receive error: {e}")

    async def handle_send_message(self, data):
        """Handle sending a message through WebSocket"""
        if not self.user:
            await self.send(text_data=json.dumps({"error": "Authentication required"}))
            return

        text = data.get("text", "").strip()
        reply_to_id = data.get("reply_to")  # Получаем ID сообщения для ответа

        if not text and not reply_to_id:
            return

        topic_id = data.get("topic_id", self.topic_id)

        # Create message с reply_to если указан
        message = await self.create_message(text, topic_id, reply_to_id)

        if message:
            # Broadcast to all users in chat
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat_message",
                    "message": await self.serialize_message(message),
                    "sender_id": self.user_id,
                },
            )

            # Stop typing status
            await self.handle_typing_stop()

    async def handle_typing_start(self):
        """Handle typing start event"""
        if not self.user or not self.chat_id:
            return

        # Set typing status in Redis
        self.set_typing_status(True)

        # Broadcast to other users
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_status",
                "user_id": self.user_id,
                "username": getattr(self.user, "username", "Unknown"),
                "is_typing": True,
            },
        )

        # Auto-stop typing after 5 seconds
        if self.typing_task:
            self.typing_task.cancel()
        self.typing_task = asyncio.get_event_loop().call_later(
            5.0, lambda: asyncio.create_task(self.auto_stop_typing())
        )

    async def handle_typing_stop(self):
        """Handle typing stop event"""
        if not self.user or not self.chat_id:
            return

        self.set_typing_status(False)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_status",
                "user_id": self.user_id,
                "is_typing": False,
            },
        )

    async def auto_stop_typing(self):
        """Automatically stop typing status"""
        self.set_typing_status(False)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_status",
                "user_id": self.user_id,
                "is_typing": False,
            },
        )

    async def handle_mark_read(self, data):
        """Обработка отметки о прочтении сообщений"""
        message_ids = data.get("message_ids", [])

        if not message_ids or not self.user_id:
            return

        # Отмечаем сообщения как прочитанные в БД
        await self.mark_messages_read(message_ids)

        # Получаем отправителей этих сообщений чтобы отправить им уведомление
        senders = await self.get_message_senders(message_ids)

        print(f"DEBUG: messages_read - user {self.user_id} read messages {message_ids}, senders: {senders}")

        # Отправляем событие другим участникам чата (кроме себя)
        # Но особенно важно отправить отправителям сообщений
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "messages_read_event",
                "user_id": self.user_id,
                "message_ids": message_ids,
                "read_at": timezone.now().isoformat(),
                "sender_ids": list(senders),  # Кому конкретно отправить
            },
        )

    @database_sync_to_async
    def get_message_senders(self, message_ids):
        """Получить уникальных отправителей сообщений"""
        from .models import Message
        senders = Message.objects.filter(
            id__in=message_ids
        ).values_list('sender_id', flat=True).distinct()
        return set(senders)

    async def messages_read_event(self, event):
        """Отправка события о прочтении сообщений клиенту"""
        # Отправляем только если мы получатель (отправитель прочитанных сообщений)
        # или если это не мы прочитали (чтобы знать что прочитал другой)
        reading_user_id = event.get("user_id")
        sender_ids = event.get("sender_ids", [])
        
        print(f"DEBUG: messages_read_event - user_id={self.user_id}, reading_user_id={reading_user_id}, sender_ids={sender_ids}")
        print(f"DEBUG: Should send? user_id in sender_ids: {self.user_id in sender_ids}, reading_user_id != user_id: {reading_user_id != self.user_id}")
        
        # Отправляем событие если:
        # 1. Мы отправили эти сообщения (sender_ids включает наш user_id)
        # 2. Или мы не тот кто читал (чтобы все видели кто что прочитал)
        if self.user_id in sender_ids or reading_user_id != self.user_id:
            print(f"DEBUG: Sending messages_read event to user {self.user_id}")
            
            # Преобразуем read_at в строку если это datetime
            read_at = event.get("read_at")
            if hasattr(read_at, 'isoformat'):
                read_at = read_at.isoformat()
            
            await self.send(
                text_data=json.dumps(
                    {
                        "action": "messages_read",
                        "user_id": reading_user_id,
                        "message_ids": event["message_ids"],
                        "read_at": read_at,
                    }
                )
            )
        else:
            print(f"DEBUG: NOT sending messages_read event to user {self.user_id}")

    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Отметить сообщения как прочитанные в БД"""
        from .models import MessageReadStatus

        created_count = 0
        for message_id in message_ids:
            obj, created = MessageReadStatus.objects.get_or_create(
                message_id=message_id, user_id=self.user_id
            )
            if created:
                created_count += 1
            print(f"DEBUG mark_messages_read: msg={message_id}, user={self.user_id}, created={created}")

        print(f"DEBUG mark_messages_read: total created={created_count} for user={self.user_id}")

    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "action": "new_message",
                    "message": event["message"],
                }
            )
        )

    async def typing_status(self, event):
        """Send typing status to WebSocket"""
        await self.send(
            text_data=json.dumps(
                {
                    "action": "typing_status",
                    "user_id": event.get("user_id"),
                    "username": event.get("username"),
                    "is_typing": event.get("is_typing", False),
                }
            )
        )

    async def user_online(self, event):
        """Send online status update"""
        await self.send(
            text_data=json.dumps(
                {
                    "action": "user_online",
                    "user_id": event.get("user_id"),
                    "is_online": event.get("is_online", True),
                    "username": event.get("username"),
                }
            )
        )

    async def message_deleted(self, event):
        """Send message deleted event"""
        await self.send(
            text_data=json.dumps(
                {
                    "action": "message_deleted",
                    "message_id": event.get("message_id"),
                }
            )
        )

    async def send_initial_data(self):
        """Send initial chat data on connection"""
        import json
        from django.utils.functional import Promise
        from datetime import datetime, date
        
        messages = await self.get_recent_messages()
        online_users = await self.get_online_users()

        # Для личных чатов добавляем информацию о собеседнике
        other_user_data = None
        if self.chat_type == "private" and self.user:
            other_user_data = await self.get_other_user_data()

        # Кастомный JSON encoder для обработки datetime объектов
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                if isinstance(obj, Promise):
                    return str(obj)
                return super().default(obj)
        
        # Сериализуем через наш encoder
        data_str = json.dumps({
            "action": "init",
            "messages": messages,
            "online_users": online_users,
            "other_user": other_user_data,
        }, cls=DateTimeEncoder)
        
        await self.send(text_data=data_str)

    @database_sync_to_async
    def get_other_user_data(self):
        """Get data about the other user in private chat"""
        try:
            from core.online_status import online_status as online_status_service
            
            private_chat = PrivateChat.objects.get(id=self.chat_id)
            other_user = private_chat.other_user(self.user)
            
            if other_user:
                is_online = online_status_service.is_online(other_user.id)
                return {
                    "id": other_user.id,
                    "username": other_user.username,
                    "display_name": other_user.display_name,
                    "avatar": other_user.avatar.url if other_user.avatar else None,
                    "is_online": is_online,
                }
        except Exception as e:
            print(f"Error getting other user data: {e}")
        return None

    @database_sync_to_async
    def get_user_from_token(self, token):
        """Get user from JWT token"""
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return None

    @database_sync_to_async
    def get_chat_type(self):
        """Determine if chat is private or group"""
        if PrivateChat.objects.filter(id=self.chat_id).exists():
            return "private"
        elif GroupChat.objects.filter(id=self.chat_id).exists():
            return "group"
        return None

    @database_sync_to_async
    def get_recent_messages(self):
        """Get recent messages for the chat"""
        from .serializers import MessageSerializer

        messages = []
        msg_qs = None

        if self.chat_type == "private":
            msg_qs = (
                Message.objects.filter(private_chat_id=self.chat_id)
                .select_related("sender", "reply_to__sender")
                .prefetch_related("read_statuses")
                .order_by("-created_at")[:50]
            )
        elif self.chat_type == "group":
            # Фильтрация по topic_id:
            # Если топик выбран (число) - только сообщения этого топика
            # Если топик = 0 (главный) - показываем ВСЕ сообщения
            # Если топик не выбран (None) - все сообщения
            if self.topic_id is not None and self.topic_id != 0:
                # Конкретный топик - только этот топик
                msg_qs = (
                    Message.objects.filter(chat_id=self.chat_id, topic_id=self.topic_id)
                    .select_related("sender", "reply_to__sender")
                    .prefetch_related("read_statuses")
                    .order_by("-created_at")[:50]
                )
            else:
                # Главный топик (0) или не выбран (None) - все сообщения
                msg_qs = (
                    Message.objects.filter(chat_id=self.chat_id)
                    .select_related("sender", "reply_to__sender")
                    .prefetch_related("read_statuses")
                    .order_by("-created_at")[:50]
                )

        if msg_qs:
            # Создаем mock request для serializer
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                @property
                def is_authenticated(self):
                    return True
                def build_absolute_uri(self, location=None):
                    if location:
                        if location.startswith('http://') or location.startswith('https://'):
                            return location
                        return f"https://anisphere.org{location}" if not location.startswith('/') else f"https://anisphere.org{location}"
                    return "https://anisphere.org"
            
            mock_request = MockRequest(self.user) if self.user else None
            
            # Используем MessageSerializer для корректной сериализации с is_read_by_other
            for m in msg_qs:
                try:
                    serializer = MessageSerializer(m, context={"request": mock_request})
                    messages.append(serializer.data)
                except Exception as e:
                    print(f"Error serializing message {m.id}: {e}")
                    # Fallback
                    messages.append({
                        "id": m.id,
                        "text": m.text,
                        "sender_id": m.sender_id,
                        "sender_username": m.sender.username if m.sender else "Unknown",
                        "created_at": m.created_at.isoformat(),
                    })

        return list(reversed(messages))

    @database_sync_to_async
    def create_message(self, text, topic_id=None, reply_to_id=None):
        """Create a new message"""
        try:
            from core.redis_events import event_publisher

            msg_data = {"text": text, "sender_id": self.user_id}

            if self.chat_type == "private":
                msg_data["private_chat_id"] = self.chat_id
            else:
                msg_data["chat_id"] = self.chat_id

            if topic_id:
                msg_data["topic_id"] = topic_id

            # Добавляем reply_to если указан
            if reply_to_id:
                try:
                    reply_to_message = Message.objects.get(id=reply_to_id)
                    msg_data["reply_to"] = reply_to_message
                except Message.DoesNotExist:
                    print(f"Reply-to message {reply_to_id} not found")

            msg = Message.objects.create(**msg_data)

            # Публикуем событие о новом сообщении
            try:
                event_publisher.publish_event(
                    "new_message",
                    {
                        "message_id": msg.id,
                        "chat_id": self.chat_id,
                        "chat_type": self.chat_type,
                        "sender_id": msg.sender.id,
                        "sender_username": msg.sender.username,
                        "sender_display_name": msg.sender.display_name
                        or msg.sender.username,
                        "text": msg.text,
                        "created_at": msg.created_at.isoformat(),
                    },
                )
            except Exception as e:
                print(f"Error publishing message event: {e}")

            return msg
        except Exception as e:
            print(f"Error creating message: {e}")
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for JSON"""
        from .serializers import MessageSerializer
        from rest_framework.renderers import JSONRenderer
        from django.contrib.auth import get_user_model
        from django.contrib.sites.shortcuts import get_current_site

        # Загружаем сообщение с связанными объектами для корректной сериализации
        message = Message.objects.select_related("sender", "reply_to__sender").get(
            id=message.id
        )

        # Создаем минимальный mock request для serializer context
        User = get_user_model()
        class MockRequest:
            def __init__(self, user):
                self.user = user
            @property
            def is_authenticated(self):
                return True
            def build_absolute_uri(self, location=None):
                """Build absolute URI for media files"""
                if location:
                    # Проверяем если это уже абсолютный URL
                    if location.startswith('http://') or location.startswith('https://'):
                        return location
                    # Иначе строим абсолютный URL
                    return f"https://anisphere.org{location}" if not location.startswith('/') else f"https://anisphere.org{location}"
                return "https://anisphere.org"

        # Используем полноценный сериализатор для сообщения
        try:
            # Создаем mock request с текущим пользователем
            mock_request = MockRequest(self.user) if self.user else None
            
            # DEBUG: Логируем если есть private_chat и это мои сообщения
            if message.private_chat and message.sender_id == (self.user.id if self.user else None):
                from .models import MessageReadStatus
                read_count = MessageReadStatus.objects.filter(message=message).count()
                read_users = list(MessageReadStatus.objects.filter(message=message).values_list('user_id', flat=True))
                print(f"DEBUG serialize_message: msg {message.id}, sender={message.sender_id}, read_count={read_count}, read_users={read_users}")
            
            serializer = MessageSerializer(message, context={"request": mock_request})
            data = serializer.data
            
            # Логируем is_read_by_other из сериализованных данных
            if message.private_chat and message.sender_id == (self.user.id if self.user else None):
                print(f"DEBUG serialize_message: msg {message.id}, is_read_by_other={data.get('is_read_by_other')}")
            
            return data
        except Exception as e:
            print(f"Error serializing message: {e}")
            import traceback
            traceback.print_exc()
            # Fallback к простой сериализации
            reply_to_data = None
            if message.reply_to:
                reply_to_data = {
                    "id": message.reply_to.id,
                    "text": message.reply_to.text,
                    "sender_id": message.reply_to.sender_id,
                    "sender_username": message.reply_to.sender.username
                    if message.reply_to.sender
                    else "Unknown",
                    "sender_avatar": message.reply_to.sender.avatar.url
                    if message.reply_to.sender and message.reply_to.sender.avatar
                    else None,
                    "created_at": message.reply_to.created_at.isoformat(),
                }

            return {
                "id": message.id,
                "text": message.text,
                "sender_id": message.sender_id,
                "sender_username": message.sender.username
                if message.sender
                else "Unknown",
                "sender_avatar": message.sender.avatar.url
                if message.sender and message.sender.avatar
                else None,
                "created_at": message.created_at.isoformat(),
                "media": message.media.url if message.media else None,
                "media_type": message.media_type,
                "topic_id": message.topic_id,
                "reply_to": message.reply_to_id,
                "reply_to_message": reply_to_data,
            }

    @database_sync_to_async
    def mark_messages_read(self, message_ids, user_id):
        """Mark messages as read"""
        Message.objects.filter(id__in=message_ids).update(read_at=timezone.now())

    def set_user_online(self):
        """Set user online in Redis"""
        if self.user:
            online_status.set_online(
                self.user_id, getattr(self.user, "username", "Unknown")
            )

    def set_user_offline(self):
        """Set user offline in Redis"""
        online_status.set_offline(self.user_id)

    def set_typing_status(self, is_typing):
        """Set typing status in Redis"""
        if self.user and self.chat_id:
            if is_typing:
                typing_status.set_typing(
                    self.chat_id,
                    self.user_id,
                    getattr(self.user, "username", "Unknown"),
                )
            else:
                typing_status.stop_typing(self.chat_id, self.user_id)

    @database_sync_to_async
    def get_online_users(self):
        """Get list of online user IDs"""
        return [uid for uid in online_status.get_online_users()]


class TypingConsumer(AsyncWebsocketConsumer):
    """
    Dedicated WebSocket consumer for typing status
    Lightweight consumer focused only on typing indicators
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_id = None
        self.group_name = None

    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.group_name = f"typing_{self.chat_id}"

        # Accept connection
        await self.accept()

        # Join typing group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "typing_start":
                await self.handle_typing_start(data)
            elif action == "typing_stop":
                await self.handle_typing_stop(data)
            elif action == "ping":
                await self.send(text_data=json.dumps({"action": "pong"}))
        except json.JSONDecodeError:
            pass

    async def handle_typing_start(self, data):
        """Broadcast typing start"""
        user_id = data.get("user_id")
        username = data.get("username", "Unknown")

        typing_status.set_typing(self.chat_id, user_id, username)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_indicator",
                "action": "typing_start",
                "user_id": user_id,
                "username": username,
            },
        )

    async def handle_typing_stop(self, data):
        """Broadcast typing stop"""
        user_id = data.get("user_id")

        typing_status.stop_typing(self.chat_id, user_id)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_indicator",
                "action": "typing_stop",
                "user_id": user_id,
            },
        )

    async def typing_indicator(self, event):
        """Send typing indicator to client"""
        await self.send(
            text_data=json.dumps(
                {
                    "action": event["action"],
                    "user_id": event.get("user_id"),
                    "username": event.get("username"),
                }
            )
        )
