"""
Скрипт для скачивания постеров аниме с Shikimori без VPN.
Пробует разные методы с логированием.
"""

import os
import sys
import logging
import time
import requests
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional
import socket

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Константы
TEST_SHIKIMORI_URL = "https://shikimori.one/uploads/poster/animes/45649/e25661ced16b056e47918a867ddfb3aa.jpeg"
OUTPUT_DIR = Path("downloads")
OUTPUT_DIR.mkdir(exist_ok=True)


def check_connection() -> None:
    """Проверка интернет-соединения."""
    logger.info("Проверка интернет-соединения...")
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        logger.info("✓ Интернет соединение есть")
    except Exception as e:
        logger.error(f"✗ Нет интернет-соединения: {e}")
        sys.exit(1)


def method_direct(url: str) -> Optional[bytes]:
    """Метод 1: Прямой запрос (без прокси)."""
    logger.info("  [1/6] Пробуем прямой запрос...")
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            logger.info(f"  ✓ Успешно! Размер: {len(response.content)} байт")
            return response.content
        else:
            logger.warning(f"  ✗ Ошибка {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"  ✗ Исключение: {e}")
        return None


def method_cdn_myanimelist(url: str) -> Optional[bytes]:
    """Метод 2: Скачивание через CDN MyAnimeList."""
    logger.info("  [2/6] Пробуем CDN MyAnimeList...")
    
    # Пробуем разные форматы URL
    url_variants = [
        url.replace("shikimori.one", "cdn.myanimelist.net"),
        url.replace("shikimori.one", "myanimelist.cdn-dena.com"),
        # Пробуем известные ID из URL
        "https://cdn.myanimelist.net/images/anime/1441/112277.jpg",  # тестовый
    ]
    
    for test_url in url_variants:
        try:
            logger.info(f"    → {test_url[:80]}...")
            response = requests.get(test_url, timeout=15)
            if response.status_code == 200:
                logger.info(f"  ✓ Успешно! Размер: {len(response.content)} байт")
                return response.content
        except Exception as e:
            continue
    
    logger.warning("  ✗ Ни один CDN не ответил")
    return None


def method_shikimori_mirrors(url: str) -> Optional[bytes]:
    """Метод 3: Разные зеркала Shikimori."""
    logger.info("  [3/6] Пробуем зеркала Shikimori...")
    
    mirrors = [
        url.replace("shikimori.one", "shikimori.me"),
        url.replace("shikimori.one", "shikimoristream.org"),
        url.replace("shikimori.one", "shikimori.org"),
        # HTTP версия
        url.replace("https://", "http://"),
    ]
    
    for mirror_url in mirrors:
        try:
            logger.info(f"    → {mirror_url[:80]}...")
            response = requests.get(mirror_url, timeout=15, allow_redirects=True)
            if response.status_code == 200:
                logger.info(f"  ✓ Успешно! Размер: {len(response.content)} байт")
                return response.content
        except Exception as e:
            continue
    
    logger.warning("  ✗ Ни одно зеркало не ответило")
    return None


def method_public_proxies(url: str) -> Optional[bytes]:
    """Метод 4: Публичные прокси."""
    logger.info("  [4/6] Пробуем публичные прокси...")
    
    # Список публичных прокси (можно обновлять)
    proxies_list = [
        "http://185.212.171.1:3128",
        "http://91.92.109.43:3128",
        "http://103.152.242.18:80",
        "http://154.86.183.106:80",
    ]
    
    for proxy in proxies_list:
        try:
            logger.info(f"    → Прокси: {proxy}")
            response = requests.get(url, proxies={"http": proxy, "https": proxy}, timeout=20)
            if response.status_code == 200:
                logger.info(f"  ✓ Успешно через прокси! Размер: {len(response.content)} байт")
                return response.content
            else:
                logger.warning(f"    → Код {response.status_code}")
        except Exception as e:
            logger.warning(f"    → Ошибка: {type(e).__name__}")
            continue
    
    logger.warning("  ✗ Ни один прокси не сработал")
    return None


def method_tor(url: str) -> Optional[bytes]:
    """Метод 5: Через Tor сеть."""
    logger.info("  [5/6] Пробуем через Tor...")
    
    try:
        # Проверяем доступность Tor
        test_tor = requests.get("http://check.torproject.org/api/ip", timeout=10)
        if "true" not in test_tor.text.lower():
            logger.warning("  ✗ Tor не подключён")
            return None
        
        logger.info("  ✓ Tor подключён, скачиваем...")
        
        session = requests.Session()
        session.proxies = {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050'
        }
        
        response = session.get(url, timeout=60)
        if response.status_code == 200:
            logger.info(f"  ✓ Успешно через Tor! Размер: {len(response.content)} байт")
            return response.content
    except ImportError:
        logger.warning("  ✗ Не установлены библиотеки для Tor (pip install requests[socks])")
    except Exception as e:
        logger.warning(f"  ✗ Ошибка Tor: {e}")
    
    return None


def method_jikan_api(shikimori_id: int) -> Optional[bytes]:
    """Метод 6: Через Jikan API (MyAnimeList)."""
    logger.info("  [6/6] Пробуем Jikan API (MyAnimeList)...")
    
    try:
        # Jikan API - бесплатный API для MyAnimeList
        response = requests.get(
            f"https://api.jikan.moe/v4/anime/{shikimori_id}",
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "images" in data["data"]:
                poster_url = data["data"]["images"]["jpg"]["image_url"]
                logger.info(f"    → Получен URL: {poster_url[:60]}...")
                
                # Скачиваем картинку
                img_response = requests.get(poster_url, timeout=15)
                if img_response.status_code == 200:
                    logger.info(f"  ✓ Успешно! Размер: {len(img_response.content)} байт")
                    return img_response.content
        else:
            logger.warning(f"  ✗ Jikan API вернул {response.status_code}")
            
    except Exception as e:
        logger.warning(f"  ✗ Ошибка Jikan: {e}")
    
    return None


def extract_shikimori_id(url: str) -> Optional[int]:
    """Извлекает ID аниме из URL Shikimori."""
    import re
    
    # Формат: /animes/45649-...
    match = re.search(r'/animes/(\d+)', url)
    if match:
        return int(match.group(1))
    
    # Пробуем из имени файла
    # e25661ced16b056e47918a867ddfb3aa - это хэш, не ID
    
    return None


def download_poster(url: str, output_path: Optional[Path] = None) -> bool:
    """
    Скачивает постер, пробуя все методы.
    Возвращает True если успешно.
    """
    logger.info("=" * 60)
    logger.info(f"URL: {url}")
    logger.info("=" * 60)
    
    # Определяем имя файла
    if output_path is None:
        filename = url.split("/")[-1] or "poster.jpg"
        output_path = OUTPUT_DIR / filename
    
    # Пробуем все методы по очереди
    methods = [
        ("Прямой запрос", lambda: method_direct(url)),
        ("CDN MyAnimeList", lambda: method_cdn_myanimelist(url)),
        ("Зеркала Shikimori", lambda: method_shikimori_mirrors(url)),
        ("Публичные прокси", lambda: method_public_proxies(url)),
        ("Tor", lambda: method_tor(url)),
    ]
    
    # Пробуем Jikan если есть ID
    shikimori_id = extract_shikimori_id(url)
    if shikimori_id:
        methods.append(("Jikan API", lambda: method_jikan_api(shikimori_id)))
    
    for method_name, method_func in methods:
        content = method_func()
        if content:
            # Сохраняем
            with open(output_path, "wb") as f:
                f.write(content)
            logger.info(f"✓ Сохранено: {output_path}")
            return True
        
        time.sleep(0.5)  # небольшая пауза между попытками
    
    logger.error("✗ Не удалось скачать ни одним способом")
    return False


def main():
    """Главная функция для тестирования."""
    logger.info("Скрипт скачивания постеров Shikimori без VPN")
    logger.info(f"Папка для сохранения: {OUTPUT_DIR.absolute()}")
    logger.info("")
    
    # Проверяем соединение
    check_connection()
    
    # Тестовый URL
    test_url = TEST_SHIKIMORI_URL
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        logger.info(f"Используем URL из аргумента: {test_url}")
    
    # Скачиваем
    success = download_poster(test_url)
    
    if success:
        logger.info("\n✓ Тест пройден успешно!")
        sys.exit(0)
    else:
        logger.info("\n✗ Тест не пройден")
        sys.exit(1)


if __name__ == "__main__":
    main()
