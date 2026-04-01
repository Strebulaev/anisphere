"""
Скрипт импорта опенингов/эндингов из платного Kodik API
Запуск: python import_oped.py
"""
import os
import sys
import django
import requests
import hmac
import hashlib
from datetime import datetime, timedelta, timezone

# Настройка Django
sys.path.insert(0, '/var/www/www-root/data/www/anisphere.ru/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime, AnimeOPED
from anime.kodik_config import KODIK_API_TOKEN

# Настройки платного API (получить из настроек)
KODIK_PUBLIC_KEY = '74ecb013335271e4344ebc994956dd75'
KODIK_PRIVATE_KEY = '692e74fa70fed3493e922cfcb6b0eab7'

# Новые домены Kodik
KODIK_BD = 'https://bd.kodikres.com'
KODIK_PLAYER = 'https://kodikplayer.com'
KODIK_API = 'https://kodik-api.com'
KODIK_PRIV_API = 'https://kodikres.com/api'
KODIK_VIDEO_BASE     = 'https://kodikres.com'

def generate_signature(link: str, ip: str, deadline: str) -> str:
    """Генерация подписи HMAC-SHA256"""
    data = f"{link}:{ip}:{deadline}"
    return hmac.new(
        KODIK_PRIVATE_KEY.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


def get_episode_url(anime_obj, episode: int = 1, season: int = 1, translation_id: int = None) -> str:
    """
    Получает URL конкретной серии через Kodik API
    Сначала пробует with_episodes=True, затем fallback на базовый линк
    """
    # Попытка 1: с with_episodes=True
    params = {
        'token': KODIK_API_TOKEN,
        'with_material_data': False,
        'with_episodes': True,
        'limit': 100,
    }
    
    if anime_obj.shikimori_id:
        params['shikimori_id'] = anime_obj.shikimori_id
    elif anime_obj.kodik_id:
        params['id'] = anime_obj.kodik_id
    else:
        return None
    
    if translation_id:
        params['translation_id'] = translation_id
    
    try:
        response = requests.get(f'{KODIK_API}/search', params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        
        if results:
            season_key = str(season)
            ep_key = str(episode)
            
            for res in results:
                if translation_id:
                    tid = (res.get('translation') or {}).get('id')
                    if str(tid) != str(translation_id):
                        continue
                
                s_data = ((res.get('seasons') or {}).get(season_key)) or {}
                ep_data = s_data.get('episodes') or {}
                ep_url = ep_data.get(ep_key) or ep_data.get(int(ep_key) if ep_key.isdigit() else ep_key)
                
                if ep_url:
                    return ep_url.strip()
    except Exception as e:
        print(f"   [ERROR] Ошибка получения URL серии: {e}")
    
    # Попытка 2: fallback - берём базовый link и добавляем параметры эпизода
    # ВАЖНО: video-links API не работает с query params, нужен формат /seria/ID/hash/720p
    try:
        params2 = {
            'token': KODIK_API_TOKEN,
            'with_material_data': False,
            'limit': 10,
        }
        if anime_obj.shikimori_id:
            params2['shikimori_id'] = anime_obj.shikimori_id
        elif anime_obj.kodik_id:
            params2['id'] = anime_obj.kodik_id
        else:
            return None
        
        response2 = requests.get(f'{KODIK_API}/search', params=params2, timeout=15)
        response2.raise_for_status()
        data2 = response2.json()
        results2 = data2.get('results', [])
        
        for res in results2:
            # Пробуем разные форматы ссылок
            link = res.get('link')
            if not link:
                continue
            
            if 'kodikplayer.com/serial/' in link:
                # link = link.replace('kodikplayer.com/serial/', 'kodik.info/seria/')
                return link
        
            if 'kodikplayer.com/video/' in link:
                # Убираем все query params
                link = link.split('?')[0]
                return link
            
            # Формат 3: kodik.info/seria/...
            if 'kodik.info/seria/' in link:
                return link
        
    except Exception as e:
        print(f"   [ERROR] Fallback ошибка: {e}")
    
    return None


def get_video_link_with_segments(anime_obj, episode: int = 1, season: int = 1, translation_id: int = None) -> dict:
    """
    Получает сегменты (опенинг/эндинг) через платный API
    """
    # 1. Получаем URL конкретной серии
    episode_url = get_episode_url(anime_obj, episode, season, translation_id)
    
    if not episode_url:
        return {'error': f'Не удалось получить URL серии для "{anime_obj.title_ru}"'}
    
    print(f"   [DEBUG] URL серии: {episode_url}")
        
    # 2. Запрашиваем платный API с сегментами
    user_ip = '5.178.56.14'  # Внешний IP сервера
    
    # Deadline: текущее время UTC + 6 часов
    deadline = datetime.now(timezone.utc) + timedelta(hours=6)
    deadline_str = deadline.strftime('%Y%m%d%H')
    
    link = episode_url
    # Нормализуем ссылку - убираем https: или http:, оставляем //...
    if link.startswith('https:'):
        link = link[6:]  # убираем https:
    elif link.startswith('http:'):
        link = link[5:]  # убираем http:
    # Оставляем ссылку как есть (//kodik.info/seria/...)
    
    print(f"   [DEBUG] Преобразованная ссылка: {link}")
    
    signature = generate_signature(link, user_ip, deadline_str)
    
    api_params = {
        'link': link,
        'p': KODIK_PUBLIC_KEY,
        'ip': user_ip,
        'd': deadline_str,
        's': signature,
        'skip_segments': 'true',
        'auto_proxy': 'true',
    }
    
    try:
        response = requests.get(f'{KODIK_VIDEO_BASE}/api/video-links', params=api_params, timeout=30)
        
        # Отладочный вывод для ошибок
        if response.status_code != 200:
            print(f"   [DEBUG] HTTP {response.status_code}: {response.text[:300]}")
        
        response.raise_for_status()
        data = response.json()
        
        # Проверка что data - словарь
        if not isinstance(data, dict):
            return {'error': f'Неверный формат ответа API: {type(data)}', 'raw': str(data)[:200]}
        
        # Отладочный вывод
        if data.get('error'):
            print(f"   [DEBUG] Ошибка API: {data.get('error')}")
        
        if not data.get('segments'):
            print(f"   [DEBUG] Ответ API (без сегментов): {data}")
        
        return {
            'link': link,
            'segments': data.get('segments', {}),
            'raw': data
        }
        
    except Exception as e:
        return {'error': f'Ошибка API: {e}'}


def import_oped_for_anime(anime, max_episodes: int = 3):
    """
    Импортирует OP/ED для конкретного аниме
    """
    from anime.models import AnimeOPED
    
    print(f"\n📺 {anime.title_ru} (ID: {anime.id})")
    
    imported = 0
    
    # Пробуем для нескольких эпизодов (обычно тайминги одинаковые)
    for ep in range(1, max_episodes + 1):
        result = get_video_link_with_segments(anime, episode=ep)
        
        if 'error' in result:
            print(f"   Эпизод {ep}: {result['error']}")
            break
        
        segments = result.get('segments', {})
        skip_segments = segments.get('skip', [])
        
        if not skip_segments:
            print(f"   Эпизод {ep}: нет сегментов для пропуска")
            continue
    
        # Анализируем сегменты
        # Обычно: первый = опенинг, последний = эндинг
        if len(skip_segments) >= 1:
            op = skip_segments[0]
            op_start = int(op['start'])
            op_end = int(op['end'])
            
            # Сохраняем опенинг (одинаковый для всех эпизодов)
            oped, created = AnimeOPED.objects.update_or_create(
                anime=anime,
                episode_number=None,  # Общий для всех
                defaults={
                    'op_start': op_start,
                    'op_end': op_end,
                    'data_source': 'kodik_paid',
                }
            )
            print(f"   ✅ OP: {op_start}-{op_end} сек")
            imported += 1
        
        if len(skip_segments) >= 2:
            ed = skip_segments[-1]
            ed_start = int(ed['start'])
            ed_end = int(ed['end'])
            
            # Сохраняем эндинг
            oped, created = AnimeOPED.objects.update_or_create(
                anime=anime,
                episode_number=None,
                defaults={
                    'ed_start': ed_start,
                    'ed_end': ed_end,
                    'data_source': 'kodik_paid',
                }
            )
            print(f"   ✅ ED: {ed_start}-{ed_end} сек")
            imported += 1
        
        # Если тайминги одинаковые для всех эпизодов - не продолжаем
        break
    
    return imported


def import_all_oped(limit: int = 100):
    """
    Импортирует OP/ED для всех аниме
    """
    from anime.models import Anime, AnimeOPED
    
    print("🚀 Начинаем импорт OP/ED")
    print("=" * 50)
    
    # Берём аниме которые есть в базе и не имеют OP/ED
    anime_list = Anime.objects.filter(
        shikimori_id__isnull=False
    ).exclude(
        id__in=AnimeOPED.objects.values_list('anime_id', flat=True)
    ).order_by('-score')[:limit]  # Сначала популярные
    
    total = anime_list.count()
    print(f"Найдено аниме для обработки: {total}")
    
    imported = 0
    no_episodes = 0  # Нет эпизодов в API
    errors = 0
    
    for i, anime in enumerate(anime_list, 1):
        try:
            result = import_oped_for_anime(anime, max_episodes=1)
            if isinstance(result, dict):
                if result.get('error'):
                    if "не удалось получить URL" in result.get('error', ''):
                        no_episodes += 1
                    else:
                        errors += 1
                elif result > 0:
                    imported += 1
            elif isinstance(result, int) and result > 0:
                imported += 1
            else:
                errors += 1
            
            if i % 20 == 0:
                print(f"\n📊 Прогресс: {i}/{total} (импорт: {imported}, без эпизодов: {no_episodes}, ошибок: {errors})")
                
        except Exception as e:
            import traceback
            print(f"  ❌ Ошибка: {e}")
            print(f"     Traceback: {traceback.format_exc()[:200]}")
            errors += 1
            continue
    
    print("\n" + "=" * 50)
    print(f"✅ Импорт завершён!")
    print(f"   Импортировано: {imported}")
    print(f"   Без эпизодов в API: {no_episodes}")
    print(f"   Ошибок: {errors}")
    print(f"   Всего OP/ED в базе: {AnimeOPED.objects.count()}")


if __name__ == '__main__':
    import sys
    from anime.models import Anime
    
    # Запуск
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        import_all_oped(limit=500)  # Обработка по 500 за раз
    else:
        # Импорт для одного аниме (по ID)
        anime_id = int(input("Введите ID аниме: ").strip())
        anime = Anime.objects.get(id=anime_id)
        import_oped_for_anime(anime)
