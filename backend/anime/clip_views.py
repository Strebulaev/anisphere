"""
Новый API для асинхронной нарезки - не трогает существующий KodikClipDownloadView
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from celery.result import AsyncResult
from django.core.cache import cache
from celery import current_app

from .clip_tasks import create_clip_async

# Принудительно устанавливаем бэкенд для Celery
current_app.conf.update(
    result_backend='redis://localhost:6379/0',
    broker_url='redis://localhost:6379/0',
)


class ClipCreateView(APIView):
    """
    POST /api/anime/clip/create/
    
    Создаёт задачу на нарезку клипа (не блокирует запрос)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Получаем параметры
        anime_id = request.data.get('anime_id')
        episode = int(request.data.get('episode', 1))
        season = int(request.data.get('season', 1))
        translation_id = request.data.get('translation_id')
        start_sec = int(request.data.get('start', 0))
        end_sec = int(request.data.get('end', 105))
        
        if not anime_id:
            return Response({"error": "anime_id required"}, status=400)
        
        # Ключ для проверки готовности
        cache_key = f"clip:{anime_id}:{episode}:{season}:{translation_id}:{start_sec}:{end_sec}"
        
        # Проверяем, может уже готово
        cached_url = cache.get(cache_key)
        if cached_url:
            return Response({
                "status": "ready",
                "url": cached_url,
                "task_id": None
            })
        
        # Создаём задачу
        user_ip = request.META.get('REMOTE_ADDR', '1.1.1.1')
        task = create_clip_async.delay(
            anime_id, episode, season, translation_id, start_sec, end_sec, user_ip
        )
        
        return Response({
            "status": "processing",
            "task_id": task.id,
            "message": "Клип нарезается. Используйте /api/anime/clip/status/ для проверки"
        }, status=202)


class ClipStatusView(APIView):
    """
    GET /api/anime/clip/status/?task_id=xxx
    
    Проверяет статус задачи нарезки
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({"error": "task_id required"}, status=400)
        
        from celery.result import AsyncResult
        
        try:
            result = AsyncResult(task_id)
            
            # Проверяем статус без вызова failed()
            if result.status == 'FAILURE':
                return Response({
                    "status": "failed",
                    "error": str(result.info)
                }, status=500)
            
            if result.status == 'SUCCESS':
                data = result.result
                return Response({
                    "status": "ready",
                    "url": data.get('url'),
                    "data": data
                })
            
            return Response({
                "status": "processing",
                "task_id": task_id
            })
            
        except Exception as e:
            return Response({
                "status": "failed", 
                "error": str(e)
            }, status=500)