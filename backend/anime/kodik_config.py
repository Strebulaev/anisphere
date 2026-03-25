# ═══════════════════════════════════════════════════════════════
# KODIK DOMAINS CONFIG
# Обновляй только здесь — все views.py и сервисы используют эти константы
# ═══════════════════════════════════════════════════════════════

KODIK_API_TOKEN = '74ecb013335271e4344ebc994956dd75'

# Актуальные домены (обновлено после смены домена на kodikres.com)
KODIK_API_BASE    = 'https://kodik-api.com'     # API
KODIK_PLAYER_BASE = 'https://kodikplayer.com'   # Плеер (было: kodik.cc / kodik.info)
KODIK_DB_BASE     = 'https://bd.kodikres.com'   # База данных
KODIK_SOCIAL_BASE = 'https://kodikonline.com'   # Плеер для соцсетей
KODIK_VIDEO_BASE  = 'https://kodikres.com'      # video-links API (ранее был kodikres.com)

# Старые домены для замены в уже сохранённых ссылках
KODIK_OLD_DOMAINS = [
    'kodik.cc',
    'kodik.info',
    'kodik.biz',
    'kodikai.com',
]


def normalize_kodik_player_link(link: str) -> str:
    """
    Заменяет старые домены плеера на актуальный kodikplayer.com.
    Используй перед отдачей kodik_link на фронтенд.
    """
    if not link:
        return link

    # Убеждаемся что схема есть
    if link.startswith('//'):
        link = 'https:' + link
    elif not link.startswith('http'):
        link = 'https://' + link

    for old in ['kodik.cc', 'kodik.info', 'kodik.biz', 'kodikai.com']:
        if old in link:
            link = link.replace(old, 'kodikplayer.com')
            break

    return link


def normalize_kodik_api_base(url: str) -> str:
    """Заменяет старый kodikapi.com на kodik-api.com в API URL."""
    if not url:
        return url
    return url.replace('kodikapi.com', 'kodik-api.com')
