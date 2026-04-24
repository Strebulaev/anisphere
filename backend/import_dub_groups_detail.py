"""
Детальный анализ групп - привязка к аниме с сайта
Запуск: python manage.py shell < import_dub_groups_detail.py
"""
import os
import requests
import time

KODIK_TOKEN = os.environ.get('KODIK_API_TOKEN', '74ecb013335271e4344ebc994956dd75')
KODIK_URL = 'https://kodik-api.com'

def analyze_groups_detail():
    """
    Детальный анализ групп - привязка к аниме с сайта
    """
    from dubs.models import DubGroup, Dub
    from anime.models import Anime
    
    print("🔍 Детальный анализ групп (привязка к аниме сайта)...")
    print("=" * 50)
    
    # Берём группы с наибольшим количеством аниме
    groups = DubGroup.objects.filter(works_count__gt=10).order_by('-works_count')
    
    print(f"Найдено групп для анализа: {groups.count()}")
    
    total_linked = 0
    processed = 0
    
    for group in groups:
        processed += 1
        print(f"\n[{processed}] 📺 {group.name} (ID: {group.id})...")
        
        # Ищем ID озвучки в Kodik
        try:
            # Пробуем найти через поиск
            trans_params = {
                'token': KODIK_TOKEN,
                'title': group.name,
                'limit': 5,
            }
            trans_response = requests.get(f'{KODIK_URL}/search', params=trans_params, timeout=15)
            trans_data = trans_response.json()
            results = trans_data.get('results', [])
            
            if not results:
                print(f"   ⚠️ Не найдено в Kodik")
                continue
            
            # Берём первую озвучку которая совпала
            translation_id = None
            for r in results:
                trans = r.get('translation', {})
                if trans and trans.get('title') == group.name:
                    translation_id = trans.get('id')
                    break
            
            if not translation_id:
                # Если точное совпадение не найдено, берём первую
                first = results[0]
                translation_id = first.get('translation', {}).get('id')
            
            if not translation_id:
                print(f"   ⚠️ Нет translation_id")
                continue
            
            # Получаем аниме этой озвучки
            params = {
                'token': KODIK_TOKEN,
                'translation_id': translation_id,
                'types': 'anime-serial,anime',
                'limit': 100,
                'with_material_data': 'true',
            }
            
            response = requests.get(f'{KODIK_URL}/search', params=params, timeout=20)
            data = response.json()
            anime_list = data.get('results', [])
            
        except Exception as e:
            print(f"   ❌ Ошибка API: {e}")
            continue
        
        if not anime_list:
            print(f"   ⚠️ Нет аниме")
            continue
        
        tv_count = 0
        movie_count = 0
        ova_count = 0
        genres = {}
        ratings = []
        linked = 0
        
        for anime in anime_list:
            kind = anime.get('type', '')
            material = anime.get('material_data', {})
            
            # Тип аниме
            if 'movie' in kind.lower():
                movie_count += 1
            elif 'ova' in kind.lower() or 'ona' in kind.lower() or 'special' in kind.lower():
                ova_count += 1
            else:
                tv_count += 1
            
            # Жанры
            anime_genres = material.get('anime_genres', []) or material.get('all_genres', []) or []
            for g in anime_genres:
                genres[g] = genres.get(g, 0) + 1
            
            # Рейтинг
            rating = material.get('shikimori_rating') or material.get('kinopoisk_rating')
            if rating:
                try:
                    ratings.append(float(rating))
                except:
                    pass
            
            # Пытаемся привязать к аниме на сайте
            shikimori_id = anime.get('shikimori_id')
            kinopoisk_id = anime.get('kinopoisk_id')
            
            if shikimori_id or kinopoisk_id:
                anime_obj = None
                
                if shikimori_id:
                    try:
                        anime_obj = Anime.objects.filter(shikimori_id=str(shikimori_id)).first()
                    except:
                        pass
                
                if not anime_obj and kinopoisk_id:
                    try:
                        anime_obj = Anime.objects.filter(kinopoisk_id=str(kinopoisk_id)).first()
                    except:
                        pass
                
                if anime_obj:
                    # Создаём связь Dub если её нет
                    dub, dub_created = Dub.objects.get_or_create(
                        anime=anime_obj,
                        group=group,
                        defaults={
                            'dub_type': 'full',
                            'total_episodes': anime.get('episodes_count'),
                            'is_complete': True,
                            'average_rating': float(rating) if rating else 0,
                        }
                    )
                    if dub_created:
                        linked += 1
                        total_linked += 1
        
        # Обновляем статистику группы
        group.tv_count = tv_count
        group.movie_count = movie_count
        group.ova_count = ova_count
        
        sorted_genres = dict(sorted(genres.items(), key=lambda x: x[1], reverse=True)[:5])
        group.genre_stats = sorted_genres
        
        if ratings:
            group.average_rating = round(sum(ratings) / len(ratings), 2)
        
        group.save()
        
        print(f"   ✅ Всего аниме: {len(anime_list)}, Привязано: {linked}, Рейтинг: {group.average_rating}")
        
        time.sleep(0.3)
    
    print("\n" + "=" * 50)
    print(f"✅ Детальный анализ завершён!")
    print(f"   Всего привязано аниме: {total_linked}")


if __name__ == '__main__':
    import django
    import sys
    sys.path.insert(0, '/var/www/www-root/data/www/anisphere.org')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    analyze_groups_detail()
