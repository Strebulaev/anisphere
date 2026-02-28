from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<chat_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/typing/(?P<chat_id>\d+)/$', consumers.TypingConsumer.as_asgi()),
    re_path(r'ws/global/$', consumers.GlobalEventsConsumer.as_asgi()),
]