"""
Сервис для получения прямых ссылок на видео через Kodik API.
Использует существующую логику из KodikClipDownloadView.
"""
import hashlib
import hmac
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests
from django.core.cache import cache

from anime.kodik_config import KODIK_API_TOKEN, KODIK_PRIVATE_KEY, KODIK_API_BASE, KODIK_VIDEO_BASE
from anime.models import Anime

logger = logging.getLogger(__name__)

# TTL кэша
CACHE_SEARCH_TTL = 3600      # 1 час
CACHE_EPISODES_TTL = 600     # 10 минут
CACHE_VIDEO_URL_TTL = 3600   # 1 час


def _get_cache_key(prefix: str, *parts) -> str:
    """Генерирует ключ кэша."""
    key = ":".join(str(p) for p in parts)
    return f"kodik:{prefix}:{hashlib.md5(key.encode()).hexdigest()}"


def get_episode_player_url(anime: Anime, episode: int, season: int = 1, translation_id: Optional[str] = None) -> Optional[str]:
    """
    Возвращает URL вида //kodik.info/seria/... для конкретной серии.
    Использует Kodik API search с with_episodes=True.
    """
    cache_key = _get_cache_key("ep_url", anime.id, episode, season, translation_id or "any")
    cached = cache.get(cache_key)
    if cached:
        return cached

    season_key = str(season)
    ep_key = str(episode)

    try:
        params = {
            "token": KODIK_API_TOKEN,
            "with_material_data": False,
            "with_episodes": True,
            "limit": 100,
        }
        if anime.shikimori_id:
            params["shikimori_id"] = anime.shikimori_id
        elif anime.kodik_id:
            params["id"] = anime.kodik_id
        else:
            return None

        if translation_id:
            params["translation_id"] = translation_id

        resp = requests.get(f"{KODIK_API_BASE}/search", params=params, timeout=10)
        resp.raise_for_status()

        for res in resp.json().get("results", []):
            if translation_id:
                tid = (res.get("translation") or {}).get("id")
                if str(tid) != str(translation_id):
                    continue

            s_data = ((res.get("seasons") or {}).get(season_key)) or {}
            ep_data = s_data.get("episodes") or {}
            ep_url = ep_data.get(ep_key) or ep_data.get(
                int(ep_key) if ep_key.isdigit() else ep_key
            )

            if ep_url:
                url = ep_url.strip()
                cache.set(cache_key, url, CACHE_EPISODES_TTL)
                return url

    except Exception as e:
        logger.warning("get_episode_player_url error: %s", e)

    return None


def get_m3u8_url(episode_url: str, user_ip: str = "1.1.1.1", quality: str = "720") -> Optional[str]:
    """
    Получает прямой m3u8 URL через kodikres.com/api/video-links с HMAC-подписью.
    """
    cache_key = _get_cache_key("m3u8", episode_url, quality)
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Нормализуем ссылку: убираем https: если есть, оставляем //...
    link = episode_url.strip()
    if link.startswith("https:"):
        link = link[6:]
    elif link.startswith("http:"):
        link = link[5:]

    # Deadline: UTC now + 6 часов, формат YYYYMMDDHH
    deadline_dt = datetime.now(timezone.utc) + timedelta(hours=6)
    deadline = deadline_dt.strftime("%Y%m%d%H")

    # HMAC-SHA256 подпись
    sign_string = f"{link}:{user_ip}:{deadline}"
    signature = hmac.new(
        KODIK_PRIVATE_KEY.encode("utf-8"),
        sign_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    params = {
        "link": link,
        "p": KODIK_API_TOKEN,
        "ip": user_ip,
        "d": deadline,
        "s": signature,
    }

    try:
        resp = requests.get(
            f"{KODIK_VIDEO_BASE}/api/video-links", params=params, timeout=15
        )
        resp.raise_for_status()
        data = resp.json()

        links = data.get("links") or {}
        # Сначала ищем запрошенное качество, потом по убыванию
        qualities = [quality, "720", "1080", "480", "360", "240"]
        seen = set()
        for q in qualities:
            if q in seen:
                continue
            seen.add(q)
            ql = links.get(q)
            if not ql:
                continue
            items = ql if isinstance(ql, list) else [ql]
            for item in items:
                src = (
                    item.get("Src")
                    or item.get("src")
                    or item.get("File")
                    or item.get("file")
                    or ""
                )
                if src:
                    if src.startswith("//"):
                        src = "https:" + src
                    cache.set(cache_key, src, CACHE_VIDEO_URL_TTL)
                    return src

    except Exception as e:
        logger.warning("get_m3u8_url error: %s", e)

    return None


def get_anime_m3u8(anime_id: int, episode: int = 1, season: int = 1,
                   translation_id: Optional[str] = None,
                   user_ip: str = "1.1.1.1", quality: str = "720") -> Optional[str]:
    """
    Полный pipeline: anime → episode_url → m3u8_url.
    """
    cache_key = _get_cache_key("full", anime_id, episode, season, translation_id or "any", quality)
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        anime = Anime.objects.get(pk=anime_id)
    except Anime.DoesNotExist:
        return None

    ep_url = get_episode_player_url(anime, episode, season, translation_id)
    if not ep_url:
        return None

    m3u8 = get_m3u8_url(ep_url, user_ip, quality)
    if m3u8:
        cache.set(cache_key, m3u8, CACHE_VIDEO_URL_TTL)
    return m3u8
