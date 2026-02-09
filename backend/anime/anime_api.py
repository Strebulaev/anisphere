from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Anime, Genre
from .serializers import AnimeSerializer, GenreSerializer


class AnimeAPI(viewsets.ModelViewSet):
    """ViewSet для работы с аниме"""
    queryset = Anime.objects.all()
    serializer_class = AnimeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Настройка queryset с оптимизацией"""
        return Anime.objects.select_related().prefetch_related('genres', 'studios')
    
    def list(self, request, *args, **kwargs):
        """Список аниме с пагинацией и фильтрацией"""
        print(f"=== AnimeAPI.list called ===")
        print(f"Query params: {request.query_params}")
        
        queryset = self.get_queryset()
        print(f"Initial queryset count: {queryset.count()}")
        
        # Поиск по названию
        search = request.query_params.get('search')
        if search:
            print(f"Search filter: {search}")
            queryset = queryset.filter(
                title_ru__icontains=search
            ) | queryset.filter(
                title_en__icontains=search
            ) | queryset.filter(
                title_jp__icontains=search
            )
            print(f"After search filter count: {queryset.count()}")

        # Фильтр по статусу
        status = request.query_params.get('status')
        if status:
            print(f"Status filter: {status}")
            queryset = queryset.filter(status=status)
            print(f"After status filter count: {queryset.count()}")
        
        # Фильтр по жанрам
        genres = request.query_params.get('genres')
        if genres:
            print(f"Genres filter: {genres}")
            genre_ids = [int(g) for g in genres.split(',') if g.strip().isdigit()]
            # Получаем названия жанров по ID
            genre_names = list(Genre.objects.filter(id__in=genre_ids).values_list('name', flat=True))
            print(f"Genre names: {genre_names}")
            # Фильтруем аниме, у которых есть хотя бы один из выбранных жанров
            if genre_names:
                queryset = queryset.filter(genres__overlap=genre_names)
                print(f"After genres filter count: {queryset.count()}")
        
        # Фильтр по году
        year_from = request.query_params.get('year_from')
        year_to = request.query_params.get('year_to')
        if year_from:
            print(f"Year from filter: {year_from}")
            queryset = queryset.filter(year__gte=int(year_from))
        if year_to:
            print(f"Year to filter: {year_to}")
            queryset = queryset.filter(year__lte=int(year_to))
        
        # Сортировка
        ordering = request.query_params.get('ordering', '-score')
        print(f"Ordering: {ordering}")
        queryset = queryset.order_by(ordering)
        
        # Пагинация
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        serializer = self.get_serializer(queryset[start:end], many=True)
        
        print(f"Final count: {total_count}, page: {page}, page_size: {page_size}")
        
        return Response({
            'results': serializer.data,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        })
    
    @action(detail=True, methods=['get'])
    def get_video_link(self, request, pk=None):
        """Получение ссылки на видео для просмотра"""
        print(f"=== AnimeAPI.get_video_link called ===")
        print(f"Class: {self.__class__.__name__}")
        print(f"Module: {self.__class__.__module__}")
        anime = self.get_object()

        # Получаем параметры
        episode = int(request.query_params.get('episode', 1))
        translation_id = request.query_params.get('translation_id', '0')
        quality = request.query_params.get('quality', '720')
        
        # Получаем ссылку в зависимости от источника данных
        try:
            video_data = None
            
            if anime.shikimori_id:
                video_data = self._get_kodik_link(
                    anime.shikimori_id, 
                    episode, 
                    translation_id, 
                    quality
                )
            
            if video_data:
                return Response({
                    'video_url': video_data['url'],
                    'quality': video_data['quality'],
                    'episode': episode,
                    'translation_id': translation_id,
                    'source': video_data.get('source', 'unknown')
                })
            else:
                return Response(
                    {'error': 'Видео не найдено для данного аниме'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            return Response(
                {'error': f'Ошибка получения видео: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_kodik_link(self, shikimori_id: int, episode: int, translation_id: str, quality: str):
        """Получение ссылки через Kodik с демо-фоллбеком"""
        
        try:
            from anime_parsers_ru import KodikParser
            
            # Получаем токен автоматически
            try:
                token = KodikParser.get_token()
                parser = KodikParser(token)
            except Exception:
                # Если не удалось получить токен, пробуем без него
                parser = KodikParser()
            
            # Формируем правильный ID для Kodik (с префиксом 'z')
            kodik_id = f"z{shikimori_id}"
            
            # Получаем ссылку на видео
            video_data = parser.get_link(
                id=kodik_id,
                id_type="shikimori",
                seria_num=episode,
                translation_id=translation_id
            )
        
            if video_data:
                base_url, max_quality = video_data
                
                # Формируем полную ссылку
                # Добавляем https:// в начало, если нет
                if not base_url.startswith(('http:', 'https:')):
                    full_url = f"https:{base_url}"
                else:
                    full_url = base_url
                    
                # Добавляем качество.mp4 в конец
                quality_map = {'360': '360', '480': '480', '720': '720'}
                selected_quality = quality_map.get(quality, '720')
                
                # Если запрашиваемое качество недоступно, используем максимальное
                if int(selected_quality) > int(max_quality):
                    selected_quality = str(max_quality)
                
                video_url = f"{full_url}{selected_quality}.mp4"
                
                return {
                    'url': video_url,
                    'quality': int(selected_quality),
                    'source': 'kodik'
                }
            
        except Exception as e:
            print(f"Ошибка получения видео через Kodik: {e}")
        
        # Возвращаем None в случае ошибки или отсутствия данных
        return None


class GenresAPI(APIView):
    """Получение списка всех жанров"""
    
    def get(self, request, format=None):
        try:
            genres = Genre.objects.all()
            serializer = GenreSerializer(genres, many=True)
            return Response({'genres': serializer.data})
        except Exception as e:
            return Response(
                {'error': f'Ошибка получения жанров: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )