# ==================== ANIME DISCUSSION GROUPS ====================
# Этот файл импортируется через: from ._discussion_views_patch import get_anime_discussion_group

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import GroupChat, ChatMember
from .serializers import GroupChatSerializer
from .models_chat import ChatTopic


def _get_poster_url(obj, request=None):
    """Получить абсолютный URL постера для Anime или Franchise."""
    if obj is None:
        return None
    # Пробуем локальный ImageField
    if getattr(obj, 'poster', None) and hasattr(obj.poster, 'url'):
        url = obj.poster.url
        if request:
            return request.build_absolute_uri(url)
        return url
    # Пробуем внешний URL
    if getattr(obj, 'poster_url', None):
        return obj.poster_url
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_anime_discussion_group(request, anime_id):
    """Получить или создать групповой чат для обсуждения аниме.

    Если аниме входит во франшизу — возвращаем franchise-группу (с топиками),
    автоматически создавая её при первом обращении.
    Для одиночного аниме создаём обычный discussion-чат.
    """
    try:
        from anime.models import Anime, Franchise
        anime = Anime.objects.select_related('franchise').get(id=anime_id)
    except Exception:
        return Response({'error': 'Аниме не найдено'}, status=404)

    try:
        # ── Аниме входит во франшизу ──────────────────────────────────────
        if anime.franchise_id:
            franchise = anime.franchise

            # Постер франшизы — берём у первой части (по franchise_order)
            first_part = (
                Anime.objects.filter(franchise=franchise)
                .order_by('franchise_order', 'year', 'id')
                .first()
            )
            franchise_poster_url = _get_poster_url(franchise, request) or _get_poster_url(first_part, request)

            # Ищем или создаём главную группу франшизы
            # Название — только имя франшизы, без префиксов
            chat, created = GroupChat.objects.get_or_create(
                franchise_id=franchise.id,
                defaults={
                    'name': franchise.name,  # только название, без «Обсуждение:»
                    'description': franchise.description or '',
                    'created_by': request.user,
                    'is_public': True,
                    'discussion_type': 'franchise',
                    'folder_type': 'discussions',
                }
            )

            # Если уже существовало — исправляем название если оно содержит лишние префиксы
            if not created:
                dirty = False
                clean_name = franchise.name
                if chat.name != clean_name and (
                    chat.name.startswith('Обсуждение:') or
                    chat.name.startswith('Обсуждение ') or
                    chat.name.lower().startswith('обсуждение')
                ):
                    chat.name = clean_name
                    dirty = True
                if dirty:
                    chat.save(update_fields=['name'])

            # Убеждаемся что пользователь в чате
            ChatMember.objects.get_or_create(
                chat=chat, user=request.user,
                defaults={'is_admin': created}
            )

            # Импортируем ChatTopic
            from .models_chat import ChatTopic

            # Общая тема (без постера)
            ChatTopic.objects.get_or_create(
                chat=chat, anime=None,
                defaults={'title': franchise.name, 'order': 0}
            )

            # Тема для каждой части
            parts = Anime.objects.filter(franchise=franchise).order_by('franchise_order', 'year', 'id')
            for idx, part in enumerate(parts, start=1):
                ChatTopic.objects.get_or_create(
                    chat=chat, anime=part,
                    defaults={
                        'title': part.title_ru or part.title_en or f'Часть #{part.id}',
                        'order': idx,
                    }
                )

            # Сериализуем с топиками + постерами
            topics = ChatTopic.objects.filter(chat=chat).order_by('order').select_related('anime')
            topics_data = []
            for t in topics:
                poster = _get_poster_url(t.anime, request) if t.anime else franchise_poster_url
                topics_data.append({
                    'id': t.id,
                    'title': t.title,
                    'order': t.order,
                    'anime_id': t.anime_id,
                    'anime_title': (t.anime.title_ru or t.anime.title_en) if t.anime else None,
                    'poster_url': poster,
                })

            chat_data = GroupChatSerializer(chat, context={'request': request}).data
            # Переопределяем аватар чата постером первой части
            if not chat_data.get('avatar') and franchise_poster_url:
                chat_data['avatar'] = franchise_poster_url
            chat_data['topics'] = topics_data
            chat_data['discussion_type'] = 'franchise'
            chat_data['franchise_id'] = franchise.id
            chat_data['franchise_poster'] = franchise_poster_url
            # Указываем топик для текущего аниме
            current_topic = next((t for t in topics_data if t['anime_id'] == anime_id), None)
            chat_data['current_topic_id'] = current_topic['id'] if current_topic else None
            return Response(chat_data)

        # ── Одиночное аниме (не во франшизе) ──────────────────────────────
        anime_poster = _get_poster_url(anime, request)
        chat, created = GroupChat.objects.get_or_create(
            anime_id=anime_id,
            defaults={
                'name': anime.title_ru or anime.title_en,  # только название
                'description': anime.description[:500] if anime.description else '',
                'created_by': request.user,
                'is_public': True,
                'discussion_type': 'anime',
                'folder_type': 'discussions',
            }
        )
        # Исправить старое название если оно с префиксом
        if not created and (
            chat.name.startswith('Обсуждение:') or chat.name.startswith('Обсуждение ')
        ):
            chat.name = anime.title_ru or anime.title_en
            chat.save(update_fields=['name'])

        ChatMember.objects.get_or_create(
            chat=chat, user=request.user,
            defaults={'is_admin': created}
        )
        chat_data = GroupChatSerializer(chat, context={'request': request}).data
        if not chat_data.get('avatar') and anime_poster:
            chat_data['avatar'] = anime_poster
        chat_data['discussion_type'] = 'anime'
        chat_data['topics'] = []
        chat_data['current_topic_id'] = None
        return Response(chat_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_anime_discussion_group(request, anime_id):
    """Создать групповой чат для обсуждения аниме"""
    try:
        from anime.models import Anime
        anime = Anime.objects.get(id=anime_id)
    except Exception:
        return Response({'error': 'Аниме не найдено'}, status=404)

    if GroupChat.objects.filter(anime_id=anime_id).exists():
        return Response({'error': 'Чат для этого аниме уже существует'}, status=400)

    chat = GroupChat.objects.create(
        name=anime.title_ru or anime.title_en,  # только название
        anime_id=anime_id,
        created_by=request.user,
        is_public=True,
        description=anime.description[:500] if anime.description else '',
        discussion_type='anime',
        folder_type='discussions',
    )
    # Исправляем старое название если оно с префиксом
    if chat.name.startswith('Обсуждение:') or chat.name.startswith('Обсуждение '):
        chat.name = anime.title_ru or anime.title_en
        chat.save(update_fields=['name'])
    ChatMember.objects.get_or_create(user=request.user, chat=chat, defaults={'is_admin': True})
    serializer = GroupChatSerializer(chat, context={'request': request})
    return Response(serializer.data, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_anime_discussion_group(request, anime_id):
    """Присоединиться к групповому чату аниме"""
    try:
        chat = GroupChat.objects.get(anime_id=anime_id)
    except GroupChat.DoesNotExist:
        return Response({'error': 'Чат не найден'}, status=404)

    if ChatMember.objects.filter(chat=chat, user=request.user).exists():
        return Response({'message': 'Вы уже участник этого чата', 'chat_id': chat.id})

    if chat.members.count() >= chat.max_members:
        return Response({'error': 'Чат переполнен'}, status=400)

    ChatMember.objects.create(user=request.user, chat=chat)
