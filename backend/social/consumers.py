"""
WebSocket consumers for real-time chat functionality
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from users.models import User
from .models import PrivateChat, GroupChat, Message
from core.online_status import online_status, typing_status


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
        """Handle marking messages as read"""
        message_ids = data.get('message_ids', [])
        if message_ids and self.user_id:
            await self.mark_messages_read(message_ids, self.user_id)
    
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
            msg_data = {'text': text, 'sender_id': self.user_id}
            
            if self.chat_type == 'private':
                msg_data['private_chat_id'] = self.chat_id
            else:
                msg_data['chat_id'] = self.chat_id
            
            msg = Message.objects.create(**msg_data)
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
