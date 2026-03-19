# ==================== ANIME DISCUSSION GROUPS ====================

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
            # Ищем или создаём главную группу франшизы
            chat, created = GroupChat.objects.get_or_create(
                franchise_id=franchise.id,
                defaults={
                    'name': franchise.name,
                    'description': franchise.description or '',
                    'created_by': request.user,
                    'is_public': True,
                    'discussion_type': 'franchise',
                    'folder_type': 'discussions',
                }
            )

            # Убеждаемся, что poster/avatar чата установлен
            if created and not chat.avatar:
                poster = franchise.poster_image_url
                if poster and poster.startswith('/'):
                    # локальный файл — проставляем через поле
                    pass  # avatar — ImageField, не трогаем

            # Убеждаемся что пользователь в чате
            ChatMember.objects.get_or_create(
                chat=chat, user=request.user,
                defaults={'is_admin': created}
            )

            # Импортируем ChatTopic
            from .models_chat import ChatTopic

            # Общая тема
            ChatTopic.objects.get_or_create(
                chat=chat, anime=None,
                defaults={'title': f'Общее о «{franchise.name}»', 'order': 0}
            )

            # Тема для каждой части
            parts = Anime.objects.filter(franchise=franchise).order_by('franchise_order', 'year', 'id')
            for idx, part in enumerate(parts, start=1):
                ChatTopic.objects.get_or_create(
                    chat=chat, anime=part,
                    defaults={'title': part.title_ru or part.title_en or f'Часть #{part.id}', 'order': idx}
                )

            # Сериализуем с топиками
            topics = ChatTopic.objects.filter(chat=chat).order_by('order').select_related('anime')
            topics_data = []
            for t in topics:
                topics_data.append({
                    'id': t.id,
                    'title': t.title,
                    'order': t.order,
                    'anime_id': t.anime_id,
                    'anime_title': (t.anime.title_ru or t.anime.title_en) if t.anime else None,
                })

            chat_data = GroupChatSerializer(chat, context={'request': request}).data
            chat_data['topics'] = topics_data
            chat_data['discussion_type'] = 'franchise'
            chat_data['franchise_id'] = franchise.id
            # Указываем топик для текущего аниме
            current_topic = next((t for t in topics_data if t['anime_id'] == anime_id), None)
            chat_data['current_topic_id'] = current_topic['id'] if current_topic else None
            return Response(chat_data)

        # ── Одиночное аниме (не во франшизе) ──────────────────────────────
        chat, created = GroupChat.objects.get_or_create(
            anime_id=anime_id,
            defaults={
                'name': f'Обсуждение: {anime.title_ru or anime.title_en}',
                'description': f'Группа для обсуждения аниме {anime.title_ru or anime.title_en}',
                'created_by': request.user,
                'is_public': True,
                'discussion_type': 'anime',
                'folder_type': 'discussions',
            }
        )
        ChatMember.objects.get_or_create(
            chat=chat, user=request.user,
            defaults={'is_admin': created}
        )
        chat_data = GroupChatSerializer(chat, context={'request': request}).data
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
        name=f'Обсуждение: {anime.title_ru or anime.title_en}',
        anime_id=anime_id,
        created_by=request.user,
        is_public=True,
        description=f'Группа для обсуждения аниме {anime.title_ru or anime.title_en}',
        discussion_type='anime',
        folder_type='discussions',
    )
    ChatMember.objects.create(user=request.user, chat=chat, is_admin=True)
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
