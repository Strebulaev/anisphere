"""
API Views для управления задачами на вырезку видео и скриншоты
"""

from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import ClipTask, Anime
from .serializers import ClipTaskSerializer, ClipTaskCreateSerializer
from .tasks import process_clip_task


class ClipTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления задачами на вырезку видео/скриншоты
    
    endpoints:
    - POST /api/anime/clips/ - Создать задачу
    - GET /api/anime/clips/ - Список задач пользователя
    - GET /api/anime/clips/{id}/ - Детали задачи
    - GET /api/anime/clips/{id}/status/ - Статус задачи
    - DELETE /api/anime/clips/{id}/ - Удалить задачу
    """
    queryset = ClipTask.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClipTaskCreateSerializer
        return ClipTaskSerializer
    
    def get_queryset(self):
        """Возвращаем задачи текущего пользователя + анонимные (для polling)"""
        if self.request.user.is_authenticated:
            return ClipTask.objects.filter(
                Q(user=self.request.user) | Q(user__isnull=True)
            ).order_by('-created_at')
        return ClipTask.objects.filter(user__isnull=True).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Создаём задачу и запускаем Celery task"""
        anime = serializer.validated_data.get('anime')
        
        # Проверка прав на аниме (опционально)
        if not anime:
            raise serializers.ValidationError({'anime': 'Аниме не указано'})
        
        # Сохраняем задачу
        instance = serializer.save(user=self.request.user if self.request.user.is_authenticated else None)
        
        # Запускаем фоновую обработку
        process_clip_task.delay(str(instance.id))
        
        return instance
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Получить статус задачи"""
        task = self.get_object()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Повторить неудачную задачу"""
        task = self.get_object()
        
        if task.status != 'failed':
            return Response(
                {'error': 'Можно повторить только неудачные задачи'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Сбрасываем статус
        task.status = 'pending'
        task.error_message = ''
        task.started_at = None
        task.completed_at = None
        task.save()
        
        # Перезапускаем
        process_clip_task.delay(str(task.id))
        
        return Response({'status': 'pending', 'message': 'Задача перезапущена'})


class ScreenshotView(APIView):
    """
    Быстрое создание скриншота (для совместимости со старым API)
    
    POST /api/anime/screenshot/
    {
        "anime_id": 123,
        "episode": 1,
        "timestamp": 125.5  # секунды
    }
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def post(self, request):
        from .serializers import ClipTaskCreateSerializer
        
        anime_id = request.data.get('anime_id')
        timestamp = request.data.get('timestamp')
        episode = request.data.get('episode', 1)
        
        if not anime_id or not timestamp:
            return Response(
                {'error': 'Требуется anime_id и timestamp'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response(
                {'error': 'Аниме не найдено'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Создаём задачу
        serializer = ClipTaskCreateSerializer(data={
            'anime': anime_id,
            'task_type': 'screenshot',
            'episode': episode,
            'timestamp': float(timestamp),
            'quality': '720',
        })
        
        if serializer.is_valid():
            task = serializer.save(user=request.user if request.user.is_authenticated else None)
            process_clip_task.delay(str(task.id))
            
            return Response({
                'task_id': str(task.id),
                'status': 'pending',
                'message': 'Скриншот создаётся'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClipCreateView(APIView):
    """
    Быстрое создание видео фрагмента (для совместимости со старым API)
    
    POST /api/anime/clip/create/
    {
        "anime_id": 123,
        "episode": 1,
        "start": 30.0,    # секунды
        "end": 60.0,      # секунды
        "label": "Эпичная сцена"
    }
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def post(self, request):
        from .serializers import ClipTaskCreateSerializer
        
        anime_id = request.data.get('anime_id')
        start = request.data.get('start')
        end = request.data.get('end')
        episode = request.data.get('episode', 1)
        label = request.data.get('label', 'clip')
        
        if not anime_id or not start or not end:
            return Response(
                {'error': 'Требуется anime_id, start и end'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return Response(
                {'error': 'Аниме не найдено'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Создаём задачу
        serializer = ClipTaskCreateSerializer(data={
            'anime': anime_id,
            'task_type': 'clip',
            'episode': episode,
            'season': 1,
            'start_time': float(start),
            'end_time': float(end),
            'label': label,
            'quality': '720',
        })
        
        if serializer.is_valid():
            task = serializer.save(user=request.user if request.user.is_authenticated else None)
            process_clip_task.delay(str(task.id))
            
            return Response({
                'task_id': str(task.id),
                'status': 'pending',
                'message': 'Видео фрагмент создаётся'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
