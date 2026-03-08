"""
Скрипт для скачивания ВСЕХ постеров из БД.
Запускать через: python manage.py shell < download_all_posters.py
Или: python -c "
import os, sys
sys.path.insert(0, '.')
exec(open('download_all_posters.py').read())
"
"""

import os
import sys
import getpass
import logging
import hashlib
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==================== КОНФИГУРАЦИЯ ====================
# Папка для сохранения постеров
MEDIA_ROOT = Path("media")
POSTERS_DIR = MEDIA_ROOT / "anime_posters"
FRANCHISE_DIR = MEDIA_ROOT / "franchise_posters"

# Настройки загрузки
MAX_WORKERS = 5  # Параллельных загрузок
TIMEOUT = 30

# Прокси (нужно включить VPN перед запуском!)
USE_PROXY = False
PROXY_URL = None  # "http://user:pass@host:port"


def get_proxy():
    """Запрашивает прокси у пользователя."""
    global USE_PROXY, PROXY_URL
    
    use = input("\nИспользовать прокси/VPN? (y/n): ").strip().lower()
    if use == 'y':
        proxy = input("Введите прокси (например http://user:pass@host:port): ").strip()
        if proxy:
            USE_PROXY = True
            PROXY_URL = proxy
            print(f"✓ Прокси установлен: {proxy}")
        else:
            print("✗ Прокси не введён, будет использован прямой запрос")
    else:
        print("Используем прямой запрос (нужен включённый VPN!)")


def get_session():
    """Создаёт сессию с прокси если нужно."""
    session = requests.Session()
    
    if USE_PROXY and PROXY_URL:
        session.proxies = {
            "http": PROXY_URL,
            "https": PROXY_URL
        }
    
    return session


def generate_filename(url: str, anime_id: int) -> str:
    """Генерирует уникальное имя файла."""
    # Получаем расширение из URL
    ext = ".jpg"
    if url.endswith(".png"):
        ext = ".png"
    elif url.endswith(".webp"):
        ext = ".webp"
    
    # Хэшируем URL чтобы избежать проблем с длинными именами
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    
    return f"{anime_id}_{url_hash}{ext}"


def download_poster(session: requests.Session, url: str, save_path: Path) -> bool:
    """Скачивает один постер."""
    try:
        response = session.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(response.content)
            return True
        else:
            logger.warning(f"  Код {response.status_code}: {url[:50]}...")
            return False
            
    except requests.exceptions.Timeout:
        logger.warning(f"  Таймаут: {url[:50]}...")
        return False
    except Exception as e:
        logger.warning(f"  Ошибка: {type(e).__name__} - {url[:50]}...")
        return False


def download_all_posters():
    """Основная функция."""
    import django
    from django.conf import settings
    
    # Инициализация Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    from anime.models import Anime, Franchise
    
    logger.info("=" * 60)
    logger.info("СКАЧИВАНИЕ ВСЕХ ПОСТЕРОВ ИЗ БД")
    logger.info("=" * 60)
    
    # Создаём директории
    POSTERS_DIR.mkdir(parents=True, exist_ok=True)
    FRANCHISE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Запрашиваем прокси
    get_proxy()
    
    session = get_session()
    
    # ==================== ANIME ====================
    logger.info("\n[1/2] Обработка Anime...")
    
    # Находим аниме с poster_url но без local poster
    anime_list = Anime.objects.filter(
        poster_url__isnull=False,
        poster_url__gt=""
    ).exclude(
        poster_url=""
    ).filter(
        poster=""
    )
    
    total_anime = anime_list.count()
    logger.info(f"  Найдено аниме с URL постера: {total_anime}")
    
    if total_anime > 0:
        success_count = 0
        fail_count = 0
        
        for anime in anime_list:
            url = anime.poster_url
            filename = generate_filename(url, anime.id)
            save_path = POSTERS_DIR / filename
            
            logger.info(f"  [{anime.id}] {anime.title_ru[:40]}...")
            logger.info(f"    URL: {url[:60]}...")
            
            if download_poster(session, url, save_path):
                # Обновляем запись в БД
                anime.poster = f"anime_posters/{filename}"
                anime.save(update_fields=['poster'])
                logger.info(f"    ✓ Сохранён: {filename}")
                success_count += 1
            else:
                fail_count += 1
            
            # Небольшая пауза чтобы не спамить сервер
            import time
            time.sleep(0.2)
        
        logger.info(f"  Итого: ✓ {success_count}, ✗ {fail_count}")
    else:
        logger.info("  Нет аниме для обработки")
    
    # ==================== FRANCHISE ====================
    logger.info("\n[2/2] Обработка Franchise...")
    
    franchise_list = Franchise.objects.filter(
        poster_url__isnull=False,
        poster_url__gt=""
    ).exclude(
        poster_url=""
    ).filter(
        poster=""
    )
    
    total_franchise = franchise_list.count()
    logger.info(f"  Найдено франшиз с URL постера: {total_franchise}")
    
    if total_franchise > 0:
        success_count = 0
        fail_count = 0
        
        for franchise in franchise_list:
            url = franchise.poster_url
            filename = generate_filename(url, franchise.id)
            save_path = FRANCHISE_DIR / filename
            
            logger.info(f"  [{franchise.id}] {franchise.name[:40]}...")
            
            if download_poster(session, url, save_path):
                franchise.poster = f"franchise_posters/{filename}"
                franchise.save(update_fields=['poster'])
                logger.info(f"    ✓ Сохранён: {filename}")
                success_count += 1
            else:
                fail_count += 1
            
            import time
            time.sleep(0.2)
        
        logger.info(f"  Итого: ✓ {success_count}, ✗ {fail_count}")
    else:
        logger.info("  Нет франшиз для обработки")
    
    # ==================== ИТОГИ ====================
    logger.info("\n" + "=" * 60)
    logger.info("ГОТОВО!")
    logger.info(f"Постеры сохранены в: {MEDIA_ROOT.absolute()}")
    logger.info("=" * 60)


if __name__ == "__main__":
    download_all_posters()
