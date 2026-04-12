import re

with open('backend/anime/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = '''def get(self, request, pk):
        # Проверка подписки
        from core.permissions import check_user_premium
        if not check_user_premium(request.user):
            return Response({
                'error': 'Для скачивания необходима подписка. Активировать подписку можно в настройках профиля.',
                'code': 'premium_required'
            }, status=403)'''

new_code = '''def get(self, request, pk):
        label = request.query_params.get('label', '').lower()
        
        # Если запрашивается опенинг или эндинг - сначала проверяем, есть ли они
        if label in ['opening', 'ending']:
            episode = int(request.query_params.get('episode', 1))
            season = int(request.query_params.get('season', 1))
            translation_id = request.query_params.get('translation_id')
            
            user_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '1.1.1.1')
            
            try:
                anime = Anime.objects.get(pk=pk)
            except Anime.DoesNotExist:
                return Response({'error': 'Аниме не найдено'}, status=404)
            
            episode_url = self._get_episode_player_url(anime, episode, season, translation_id)
            if not episode_url:
                return Response({'error': 'У этого аниме нет опенинга' if label == 'opening' else 'У этого аниме нет эндинга', 'code': 'no_theme'}, status=404)
            
            opening, ending = self._get_segments(episode_url, user_ip=user_ip)
            
            if label == 'opening' and not opening:
                return Response({'error': 'У этого аниме нет опенинга', 'code': 'no_opening'}, status=404)
            if label == 'ending' and not ending:
                return Response({'error': 'У этого аниме нет эндинга', 'code': 'no_ending'}, status=404)
        
        # Проверка подписки
        from core.permissions import check_user_premium
        if not check_user_premium(request.user):
            return Response({
                'error': 'Для скачивания необходима подписка. Активировать подписку можно в настройках профиля.',
                'code': 'premium_required'
            }, status=403)'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('backend/anime/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Changes applied!")
else:
    print("ERROR: Old code not found")
    # Try to find similar patterns
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def get(self, request, pk):' in line and i > 2000:
            print(f"Found at line {i+1}: {repr(line)}")
            print(f"Next lines: {repr(lines[i+1:i+5])}")
