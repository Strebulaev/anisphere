"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.conf.urls.static import static
import time
import requests
from urllib.parse import urlparse, quote

def api_status(request):
    """Статус всех моделей в системе"""
    # from users.models import User
    from anime.models import Anime, Genre
    from playlists.models import Playlist, PlaylistItem
    from dubs.models import DubGroup, Dub
    from social.models import Comment, Group
    from reactor.models import ReactorPost
    from notifications.models import Complaint, Notification

    return JsonResponse({
        'status': 'ok',
        'message': 'AnimeCore API работает!',
        'timestamp': time.time(),
        'models': {
            # 'users': User.objects.count(),
            'anime': Anime.objects.count(),
            'genres': Genre.objects.count(),
            # 'playlists': Playlist.objects.count(),
            # 'playlist_items': PlaylistItem.objects.count(),
            # 'dub_groups': DubGroup.objects.count(),
            # 'dubs': Dub.objects.count(),
            # 'comments': Comment.objects.count(),
            # 'groups': Group.objects.count(),
            # 'reactor_posts': ReactorPost.objects.count(),
            # 'complaints': Complaint.objects.count(),
            # 'notifications': Notification.objects.count(),
        },
        'endpoints': {
            'anime': '/api/anime/',
            'playlists': '/api/playlists/',
            'users': '/api/users/',
            'dubs': '/api/dubs/',
            'social': '/api/social/',
            'reactor': '/api/reactor/',
            'notifications': '/api/notifications/',
        }
    })


def proxy_image(request, encoded_url):
    """
    Проксирует изображения с внешних сайтов через images.weserv.nl
    для обхода блокировок.
    """
    import logging
    import base64
    import traceback as tb
    
    logger = logging.getLogger(__name__)
    
    try:
        print(f'[PROXY] Starting proxy for: {encoded_url[:30]}...')
        
        # Декодируем URL (поддержка URL-safe base64)
        url_safe = encoded_url.replace('-', '+').replace('_', '/')
        padding = 4 - len(url_safe) % 4
        if padding != 4:
            url_safe += '=' * padding
        
        original_url = base64.b64decode(url_safe).decode('utf-8')
        print(f'[PROXY] Decoded URL: {original_url}')
        
        # Валидация URL
        parsed = urlparse(original_url)
        if not parsed.scheme or not parsed.netloc:
            return HttpResponse('Invalid URL', status=400)
        
        # Используем images.weserv.nl как прокси - он не заблокирован
        # encodeurl для безопасной передачи URL
        from urllib.parse import quote
        encoded_original = quote(original_url, safe='')
        proxy_url = f'https://images.weserv.nl/?url={encoded_original}&w=500&q=80&output=webp'
        
        print(f'[PROXY] Using weserv: {proxy_url[:80]}...')
        
        # Заголовки для изображения
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/*,*/*;q=0.8',
        }
        
        # Загружаем через weserv.nl
        response = requests.get(proxy_url, headers=headers, timeout=20, stream=True)
        print(f'[PROXY] Response status: {response.status_code}')
        
        if response.status_code != 200:
            # Если weserv не работает, пробуем напрямую
            logger.warning(f'[PROXY] weserv failed, trying direct: {response.status_code}')
            response = requests.get(original_url, headers=headers, timeout=15, stream=True)
            if response.status_code != 200:
                return HttpResponse(f'Image not found: {response.status_code}', status=response.status_code)
        
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        http_response = HttpResponse(response.content, content_type=content_type)
        http_response['Cache-Control'] = 'public, max-age=2592000'
        
        print(f'[PROXY] Success!')
        return http_response
        
    except Exception as e:
        error_trace = tb.format_exc()
        logger.error(f'[PROXY] Error: {str(e)}')
        return HttpResponse(f'Proxy error: {str(e)}', status=500)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/status/', api_status),            # Статус системы
    path('api/users/', include('users.urls')),  # Users API
    path('api/anime/', include('anime.urls')),  # Anime API
    path('api/dubs/', include('dubs.urls')),    # Dubs API
    path('api/playlists/', include('playlists.urls')),  # Playlists API
    path('api/social/', include('social.urls')), # Social API
    path('api/reactor/', include('reactor.urls')), # Reactor API
    path('api/notifications/', include('notifications.urls')), # Notifications API
    path('api/studios/', include('studios.urls')),  # Studios API
    path('api/roulette/', include('roulette.urls')),  # Roulette API
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)