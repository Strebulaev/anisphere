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
        token = self.scope.get('query_string', b'').decode()
        if 'token=' in token:
            token = token.split('token=')[1].split('&')[0]
        else:
            token = None
        
        if token:
            self.user = await self.get_user_from_token(token)
        
        if not self.user:
            await self.close(code=4001)
            return
        
        self.user_id = self.user.id
        
        # Join user-specific group for personal notifications
        await self.channel_layer.group_add(
            f'user_{self.user_id}',
            self.channel_name
        )
        
        await self.accept()
        
        # Start Redis listener in background
        self.should_listen = True
        self.redis_listener_thread = threading.Thread(
            target=self._listen_redis,
            daemon=True
        )
        self.redis_listener_thread.start()
        
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        self.should_listen = False
        
        if self.user_id:
            await self.channel_layer.group_discard(
                f'user_{self.user_id}',
                self.channel_name
            )
    
    def _listen_redis(self):
        """Listen to Redis pub/sub in background thread"""
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            pubsub = redis_client.pubsub()
            pubsub.subscribe('realtime_updates')
            
            for message in pubsub.listen():
                if not self.should_listen:
                    break
                if message['type'] == 'message':
                    try:
                        event = json.loads(message['data'])
                        # Run async send in event loop
                        asyncio.run(self._send_event_to_client(event))
                    except:
                        pass
        except Exception as e:
            print(f"Redis listener error: {e}")
    
    async def _send_event_to_client(self, event):
        """Send event to WebSocket client"""
        try:
            event_type = event.get('type')
            data = event.get('data', {})
            
            # Check if this event is for this user
            target_users = event.get('target_users')
            if target_users and self.user_id not in target_users:
                return
            
            # Send appropriate action based on event type
            if event_type == 'chat_created':
                await self.send(text_data=json.dumps({
                    'action': 'chat_created',
                    'chat': data
                }))
            elif event_type == 'chat_deleted':
                await self.send(text_data=json.dumps({
                    'action': 'chat_deleted',
                    'chat_id': data.get('chat_id'),
                    'chat_type': data.get('chat_type')
                }))
            elif event_type == 'user_online':
                await self.send(text_data=json.dumps({
                    'action': 'user_online',
                    'user_id': data.get('user_id'),
                    'username': data.get('username')
                }))
            elif event_type == 'user_offline':
                await self.send(text_data=json.dumps({
                    'action': 'user_offline',
                    'user_id': data.get('user_id')
                }))
            elif event_type == 'user_typing':
                await self.send(text_data=json.dumps({
                    'action': 'user_typing',
                    'chat_id': data.get('chat_id'),
                    'user_id': data.get('user_id'),
                    'username': data.get('username'),
                    'is_typing': data.get('is_typing')
                }))
            elif event_type == 'message_sent':
                await self.send(text_data=json.dumps({
                    'action': 'new_message',
                    'message': data
                }))
            elif event_type == 'new_post':
                await self.send(text_data=json.dumps({
                    'type': 'new_post',
                    'data': data
                }))
            elif event_type == 'post_liked':
                await self.send(text_data=json.dumps({
                    'type': 'post_liked',
                    'data': data
                }))
            elif event_type == 'post_commented':
                await self.send(text_data=json.dumps({
                    'type': 'post_commented',
                    'data': data
                }))
            elif event_type == 'post_reposted':
                await self.send(text_data=json.dumps({
                    'type': 'post_reposted',
                    'data': data
                }))
            elif event_type == 'new_follower':
                await self.send(text_data=json.dumps({
                    'type': 'new_follower',
                    'data': data
                }))
        except Exception as e:
            print(f"Error sending event to client: {e}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'ping':
                await self.send(text_data=json.dumps({'action': 'pong'}))
            elif action == 'subscribe_chat':
                chat_id = data.get('chat_id')
                if chat_id:
                    await self.channel_layer.group_add(
                        f'chat_{chat_id}',
                        self.channel_name
                    )
            elif action == 'unsubscribe_chat':
                chat_id = data.get('chat_id')
                if chat_id:
                    await self.channel_layer.group_discard(
                        f'chat_{chat_id}',
                        self.channel_name
                    )
        except json.JSONDecodeError:
            pass
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """Get user from JWT token"""
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
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
        
    async def connect(self):
        """Handle WebSocket connection"""
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.group_name = f'chat_{self.chat_id}'
        
        # Authenticate user from token
        token = self.scope.get('query_string', b'').decode().split('=')[-1] if 'token=' in self.scope.get('query_string', b'').decode() else None
        
        if token:
            self.user = await self.get_user_from_token(token)
        
        if not self.user:
            # Try to get user from session
            if self.scope.get('user') and self.scope['user'].is_authenticated:
                self.user = self.scope['user']
            else:
                # Allow connection for anonymous users (for demo)
                self.user = None
        
        if self.user:
            self.user_id = self.user.id
            # Set user online
            self.set_user_online()
        
        # Determine chat type
        self.chat_type = await self.get_chat_type()
        
        if not self.chat_type:
            await self.close(code=4004)
            return
        
        # Join chat group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
    
        await self.accept()
        
        # Send initial data
        await self.send_initial_data()
        
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'group_name') and self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        
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
            action = data.get('action')
            
            if action == 'send_message':
                await self.handle_send_message(data)
            elif action == 'typing_start':
                await self.handle_typing_start()
            elif action == 'typing_stop':
                await self.handle_typing_stop()
            elif action == 'mark_read':
                await self.handle_mark_read(data)
            elif action == 'get_messages':
                await self.send_initial_data()
            elif action == 'ping':
                await self.send(text_data=json.dumps({'action': 'pong'}))
                
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"WebSocket receive error: {e}")
    
    async def handle_send_message(self, data):
        """Handle sending a message through WebSocket"""
        if not self.user:
            await self.send(text_data=json.dumps({
                'error': 'Authentication required'
            }))
            return
        
        text = data.get('text', '').strip()
        if not text:
            return
        
        # Create message
        message = await self.create_message(text)
        
        if message:
            # Broadcast to all users in chat
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': await self.serialize_message(message),
                    'sender_id': self.user_id,
                }
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
                'type': 'typing_status',
                'user_id': self.user_id,
                'username': getattr(self.user, 'username', 'Unknown'),
                'is_typing': True,
            }
        )
    
        # Auto-stop typing after 5 seconds
        if self.typing_task:
            self.typing_task.cancel()
        self.typing_task = asyncio.get_event_loop().call_later(
            5.0, 
            lambda: asyncio.create_task(self.auto_stop_typing())
        )
    
    async def handle_typing_stop(self):
        """Handle typing stop event"""
        if not self.user or not self.chat_id:
            return
        
        self.set_typing_status(False)
        
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'typing_status',
                'user_id': self.user_id,
                'is_typing': False,
            }
        )
    
    async def auto_stop_typing(self):
        """Automatically stop typing status"""
        self.set_typing_status(False)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'typing_status',
                'user_id': self.user_id,
                'is_typing': False,
            }
        )
    
    async def handle_mark_read(self, data):
        """Обработка отметки о прочтении сообщений"""
        message_ids = data.get('message_ids', [])
        
        if not message_ids or not self.user_id:
            return
        
        # Отмечаем сообщения как прочитанные в БД
        await self.mark_messages_read(message_ids)
        
        # Отправляем событие другим участникам чата
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'messages_read_event',
                'user_id': self.user_id,
                'message_ids': message_ids,
                'read_at': timezone.now().isoformat()
            }
        )
    
    async def messages_read_event(self, event):
        """Отправка события о прочтении сообщений клиенту"""
        await self.send(text_data=json.dumps({
            'action': 'messages_read',
            'user_id': event['user_id'],
            'message_ids': event['message_ids'],
            'read_at': event['read_at']
        }))
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Отметить сообщения как прочитанные в БД"""
        from .models import MessageReadStatus
        
        for message_id in message_ids:
            MessageReadStatus.objects.get_or_create(
                message_id=message_id,
                user_id=self.user_id
            )
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'action': 'new_message',
            'message': event['message'],
        }))

    async def typing_status(self, event):
        """Send typing status to WebSocket"""
        await self.send(text_data=json.dumps({
            'action': 'typing_status',
            'user_id': event.get('user_id'),
            'username': event.get('username'),
            'is_typing': event.get('is_typing', False),
        }))
    
    async def user_online(self, event):
        """Send online status update"""
        await self.send(text_data=json.dumps({
            'action': 'user_online',
            'user_id': event.get('user_id'),
            'is_online': event.get('is_online', True),
        }))
    
    async def send_initial_data(self):
        """Send initial chat data on connection"""
        messages = await self.get_recent_messages()
        online_users = await self.get_online_users()
        
        await self.send(text_data=json.dumps({
            'action': 'init',
            'messages': messages,
            'online_users': online_users,
        }))
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """Get user from JWT token"""
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return None
    
    @database_sync_to_async
    def get_chat_type(self):
        """Determine if chat is private or group"""
        if PrivateChat.objects.filter(id=self.chat_id).exists():
            return 'private'
        elif GroupChat.objects.filter(id=self.chat_id).exists():
            return 'group'
        return None
    
    @database_sync_to_async
    def get_recent_messages(self):
        """Get recent messages for the chat"""
        messages = []
        msg_qs = None
        
        if self.chat_type == 'private':
            msg_qs = Message.objects.filter(
                private_chat_id=self.chat_id
            ).select_related('sender').order_by('-created_at')[:50]
        elif self.chat_type == 'group':
            msg_qs = Message.objects.filter(
                chat_id=self.chat_id
            ).select_related('sender').order_by('-created_at')[:50]
        
        if msg_qs:
            messages = list(reversed([
                {
                    'id': m.id,
                    'text': m.text,
                    'sender_id': m.sender_id,
                    'sender_username': m.sender.username if m.sender else 'Unknown',
                    'sender_avatar': m.sender.avatar.url if m.sender and m.sender.avatar else None,
                    'created_at': m.created_at.isoformat(),
                    'media': m.media.url if m.media else None,
                    'media_type': m.media_type,
                }
                for m in msg_qs
            ]))
        
        return messages
    
    @database_sync_to_async
    def create_message(self, text):
        """Create a new message"""
        try:
            from core.redis_events import event_publisher

            msg_data = {'text': text, 'sender_id': self.user_id}
            
            if self.chat_type == 'private':
                msg_data['private_chat_id'] = self.chat_id
            else:
                msg_data['chat_id'] = self.chat_id
            
            msg = Message.objects.create(**msg_data)
            
            # Публикуем событие о новом сообщении
            try:
                sender = User.objects.get(id=self.user_id)
                event_publisher.publish_event('new_message', {
                    'message_id': msg.id,
                    'chat_id': self.chat_id,
                    'chat_type': self.chat_type,
                    'sender_id': sender.id,
                    'sender_username': sender.username,
                    'sender_display_name': sender.display_name or sender.username,
                    'text': msg.text,
                    'created_at': msg.created_at.isoformat(),
                })
            except Exception as e:
                print(f"Error publishing message event: {e}")
            
            return msg
        except Exception as e:
            print(f"Error creating message: {e}")
            return None
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Serialize message for JSON"""
        return {
            'id': message.id,
            'text': message.text,
            'sender_id': message.sender_id,
            'sender_username': message.sender.username if message.sender else 'Unknown',
            'sender_avatar': message.sender.avatar.url if message.sender and message.sender.avatar else None,
            'created_at': message.created_at.isoformat(),
            'media': message.media.url if message.media else None,
            'media_type': message.media_type,
        }
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids, user_id):
        """Mark messages as read"""
        Message.objects.filter(
            id__in=message_ids
        ).update(read_at=timezone.now())
    
    def set_user_online(self):
        """Set user online in Redis"""
        if self.user:
            online_status.set_online(
                self.user_id,
                getattr(self.user, 'username', 'Unknown')
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
                    getattr(self.user, 'username', 'Unknown')
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
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.group_name = f'typing_{self.chat_id}'
        
        # Accept connection
        await self.accept()
        
        # Join typing group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'typing_start':
                await self.handle_typing_start(data)
            elif action == 'typing_stop':
                await self.handle_typing_stop(data)
            elif action == 'ping':
                await self.send(text_data=json.dumps({'action': 'pong'}))
        except json.JSONDecodeError:
            pass
    
    async def handle_typing_start(self, data):
        """Broadcast typing start"""
        user_id = data.get('user_id')
        username = data.get('username', 'Unknown')
        
        typing_status.set_typing(self.chat_id, user_id, username)
        
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'typing_indicator',
                'action': 'typing_start',
                'user_id': user_id,
                'username': username,
            }
        )
    
    async def handle_typing_stop(self, data):
        """Broadcast typing stop"""
        user_id = data.get('user_id')
        
        typing_status.stop_typing(self.chat_id, user_id)
        
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'typing_indicator',
                'action': 'typing_stop',
                'user_id': user_id,
            }
        )
    
    async def typing_indicator(self, event):
        """Send typing indicator to client"""
        await self.send(text_data=json.dumps({
            'action': event['action'],
            'user_id': event.get('user_id'),
            'username': event.get('username'),
        }))
