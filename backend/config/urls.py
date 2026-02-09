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
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
import time

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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)