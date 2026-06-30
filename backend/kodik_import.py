#!/usr/bin/env python
"""
Fast Kodik Importer - массовый импорт за 2 минуты
Использует bulk операции и игнорирует дубликаты

Использование:
    python fast_kodik_import.py                    # Полный импорт
    python fast_kodik_import.py --limit 25        # Импорт только 25 записей (для теста)
    python fast_kodik_import.py --limit 100 --debug  # Импорт 100 записей с детальным логгированием
    python fast_kodik_import.py --replace         # Полная перезапись базы данных
"""

import os
import sys
import django
import json
import time
import argparse
import logging
from typing import Dict, Set, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import requests
from django.db import transaction
from django.db.models import Q
from anime.models import Anime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

KODIK_TOKEN = '74ecb013335271e4344ebc994956dd75'
BATCH_SIZE = 100  # Размер батча для bulk_create
MAX_PAGES = 200   # Максимальное количество страниц для безопасности

# Глобальные переменные для статистики
STATS = {
    'api_requests': 0,
    'api_errors': 0,
    'total_duration': 0,
    'processing_time': 0,
    'db_operations': 0,
    'duplicates_skipped': 0,
    'new_records': 0,
    'errors': 0,
    'updated_records': 0,
}


def map_status(kodik_status: Optional[str]) -> str:
    """Маппинг статусов Kodik -> Django модель"""
    mapping = {
        'ongoing': 'ongoing',
        'released': 'released',
        'anons': 'announced',
        'canceled': 'canceled',
        'on_hold': 'on_hold',
    }
    return mapping.get(kodik_status, 'finished') if kodik_status else 'finished'


def map_kind(kodik_type: Optional[str]) -> str:
    """Маппинг типов Kodik -> Django модель"""
    mapping = {
        'anime': 'tv',
        'anime-serial': 'tv',
        'foreign-movie': 'movie',
        'russian-movie': 'movie',
        'soviet-cartoon': 'movie',
        'foreign-cartoon': 'movie',
        'russian-cartoon': 'movie',
        'anime': 'tv',
        'ova': 'ova',
        'ona': 'ona',
        'special': 'special',
    }
    return mapping.get(kodik_type, 'tv') if kodik_type else 'tv'


def get_episodes_count_correct(item: Dict) -> int:
    """
    Правильное определение количества эпизодов из Kodik API
    Использует episodes_count и last_episode, берет максимальное значение
    """
    # Прямо из item (на уровне самого аниме)
    episodes_count = item.get('episodes_count') or 0
    last_episode = item.get('last_episode') or 0
    
    # Также проверяем в material_data
    material_data = item.get('material_data', {})
    episodes_total = material_data.get('episodes_total') or 0
    episodes_aired = material_data.get('episodes_aired') or 0
    
    # Берем максимальное значение из всех источников
    values = [
        int(episodes_count) if episodes_count else 0,
        int(last_episode) if last_episode else 0,
        int(episodes_total) if episodes_total else 0,
        int(episodes_aired) if episodes_aired else 0,
    ]
    
    # Для длинных онгоингов (Ван-Пис) last_episode может быть больше
    return max(values)


def get_existing_ids() -> tuple[Set[int], Set[str]]:
    """Получение всех существующих ID"""
    try:
        logger.info("🔍 Получение существующих ID из базы данных...")
        start_time = time.time()
        
        # Получаем все существующие shikimori_id
        existing_shikimori = set(
            Anime.objects.filter(shikimori_id__isnull=False)
            .values_list('shikimori_id', flat=True)
        )
        
        # Получаем все существующие kodik_id
        existing_kodik = set(
            Anime.objects.filter(kodik_id__isnull=False)
            .values_list('kodik_id', flat=True)
        )
        
        duration = time.time() - start_time
        logger.info(f"  ✅ Найдено: {len(existing_shikimori)} shikimori_id и {len(existing_kodik)} kodik_id за {duration:.2f} сек")
        return existing_shikimori, existing_kodik
    except Exception as e:
        logger.error(f"  ❌ Ошибка получения существующих ID: {e}")
        return set(), set()


def fetch_all_results(limit: Optional[int] = None, debug: bool = False) -> List[Dict]:
    """Загрузка всех данных из Kodik API с пагинацией"""
    all_results = []
    url = 'https://kodik-api.com/list'
    params = {
        'token': KODIK_TOKEN,
        'limit': 100,
        'types': 'anime,anime-serial',
        'with_material_data': 'true',
    }
    
    page = 1
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; Kodik-Importer/1.0)',
        'Accept': 'application/json',
    })
    
    logger.info(f"📥 Загрузка данных из Kodik API...")
    if limit:
        logger.info(f"  ⚠️ Тестовый режим: будет загружено только {limit} записей")
    
    while page <= MAX_PAGES:
        try:
            STATS['api_requests'] += 1
            request_start = time.time()
            
            resp = session.get(url, params=params, timeout=30)
            request_duration = time.time() - request_start
            
            if debug:
                logger.debug(f"  📡 Запрос {STATS['api_requests']}: {request_duration:.2f} сек, статус {resp.status_code}")
            
            if resp.status_code != 200:
                STATS['api_errors'] += 1
                logger.error(f"  ❌ Ошибка API: {resp.status_code}")
                try:
                    error_data = resp.json()
                    logger.error(f"  Ошибка: {error_data}")
                except:
                    logger.error(f"  Ответ: {resp.text[:200]}")
                break
            
            try:
                data = resp.json()
            except json.JSONDecodeError as e:
                STATS['api_errors'] += 1
                logger.error(f"  ❌ Ошибка парсинга JSON: {e}")
                logger.error(f"  Ответ: {resp.text[:200]}")
                break
            
            results = data.get('results', [])
            total = data.get('total', 0)
            
            if not results:
                logger.warning(f"  ⚠️ Нет результатов на странице {page}")
                break
            
            # Добавляем результаты с учетом лимита
            if limit:
                remaining = limit - len(all_results)
                if remaining <= 0:
                    break
                results_to_add = results[:remaining]
                all_results.extend(results_to_add)
            else:
                all_results.extend(results)
            
            logger.info(f"  📄 Стр. {page}: +{len(results)} аниме (всего: {len(all_results)}/{total})")
            
            # Если достигнут лимит, выходим
            if limit and len(all_results) >= limit:
                logger.info(f"  ✅ Достигнут лимит в {limit} записей")
                break
            
            # Получаем следующий URL из ответа
            next_page = data.get('next_page')
            if not next_page:
                logger.info(f"  ✅ Все страницы загружены (всего: {len(all_results)} записей)")
                break
            
            url = next_page
            params = {}
            page += 1
            
            if page % 10 == 0:
                time.sleep(0.1)
                
        except requests.exceptions.Timeout:
            STATS['api_errors'] += 1
            logger.warning(f"  ⚠️ Таймаут на странице {page}, повторная попытка...")
            time.sleep(1)
            continue
        except requests.exceptions.ConnectionError as e:
            STATS['api_errors'] += 1
            logger.error(f"  ❌ Ошибка соединения: {e}")
            break
        except Exception as e:
            STATS['api_errors'] += 1
            logger.error(f"  ❌ Неожиданная ошибка: {e}")
            break
    
    session.close()
    
    logger.info(f"📊 Итого загружено: {len(all_results)} записей за {STATS['api_requests']} запросов")
    return all_results


def process_results(all_results: List[Dict], existing_shikimori: Set[int], existing_kodik: Set[str], 
                   debug: bool = False, replace: bool = False) -> tuple[int, int, int, int]:
    """Обработка и создание объектов в БД с полным игнорированием дубликатов"""
    anime_objects = []
    created = 0
    skipped_duplicates = 0
    skipped_invalid = 0
    errors = 0
    updated = 0
    
    logger.info(f"\n🔄 Обработка {len(all_results)} записей...")
    logger.info(f"  📊 Уже в БД: {len(existing_shikimori)} записей")
    if replace:
        logger.info(f"  ⚠️ РЕЖИМ ПЕРЕЗАПИСИ: обновление существующих записей")
    
    start_time = time.time()
    
    # Обновляем статистику
    STATS['duplicates_skipped'] = 0
    
    with transaction.atomic():
        for i, item in enumerate(all_results):
            try:
                # Проверка на наличие shikimori_id
                shikimori_id = item.get('shikimori_id')
                if not shikimori_id:
                    skipped_invalid += 1
                    if debug:
                        logger.debug(f"    ⚠️ Нет shikimori_id: {item.get('id', 'unknown')}")
                    continue
                
                try:
                    shikimori_id = int(shikimori_id)
                except (ValueError, TypeError):
                    skipped_invalid += 1
                    if debug:
                        logger.debug(f"    ⚠️ Неверный shikimori_id: {shikimori_id}")
                    continue
                
                # Получаем kodik_id для дополнительной проверки
                kodik_id = item.get('id', '')
                
                # Проверка на существование
                is_existing = shikimori_id in existing_shikimori or (kodik_id and kodik_id in existing_kodik)
                
                # Если запись существует и не в режиме перезаписи - пропускаем
                if is_existing and not replace:
                    skipped_duplicates += 1
                    STATS['duplicates_skipped'] += 1
                    if debug:
                        logger.debug(f"    ⏭️ Дубликат: shikimori_id={shikimori_id}")
                    continue
                
                material_data = item.get('material_data', {})
                if not material_data:
                    skipped_invalid += 1
                    if debug:
                        logger.debug(f"    ⚠️ Нет material_data для shikimori_id={shikimori_id}")
                    continue
                
                # Извлечение данных
                title_ru = material_data.get('anime_title') or material_data.get('title', '')
                if not title_ru:
                    skipped_invalid += 1
                    if debug:
                        logger.debug(f"    ⚠️ Нет названия для shikimori_id={shikimori_id}")
                    continue
                
                title_en = material_data.get('title_en', '')
                title_jp = ''
                
                other_titles_jp = material_data.get('other_titles_jp', [])
                if other_titles_jp and isinstance(other_titles_jp, list):
                    title_jp = other_titles_jp[0] if other_titles_jp else ''
                
                # ПРАВИЛЬНОЕ определение количества эпизодов
                episodes = get_episodes_count_correct(item)
                
                # Год
                year = material_data.get('year', 0)
                if year:
                    try:
                        year = int(year)
                    except (ValueError, TypeError):
                        year = 0
                
                # Рейтинг
                score = material_data.get('shikimori_rating', 0.0)
                if score:
                    try:
                        score = float(score)
                    except (ValueError, TypeError):
                        score = 0.0
                
                # Статус и тип
                status = map_status(material_data.get('anime_status'))
                kind = map_kind(item.get('type'))
                
                # Собираем жанры - внимательно проверяем тип
                genres = []
                raw_genres = material_data.get('genres', [])
                if raw_genres:
                    if isinstance(raw_genres, list):
                        for g in raw_genres:
                            if isinstance(g, dict) and 'name' in g:
                                genres.append(g['name'])
                            elif isinstance(g, str):
                                genres.append(g)
                    elif isinstance(raw_genres, str):
                        genres = [g.strip() for g in raw_genres.split(',') if g.strip()]
                
                # Собираем студии
                studios = []
                raw_studios = material_data.get('anime_studios', [])
                if raw_studios:
                    if isinstance(raw_studios, list):
                        for s in raw_studios:
                            if isinstance(s, dict) and 'name' in s:
                                studios.append(s['name'])
                            elif isinstance(s, str):
                                studios.append(s)
                    elif isinstance(raw_studios, str):
                        studios = [s.strip() for s in raw_studios.split(',') if s.strip()]
                
                # Собираем переводы
                translations = []
                translation = item.get('translation')
                if translation:
                    if isinstance(translation, dict):
                        title = translation.get('title', '')
                        if title:
                            translations.append(title)
                    elif isinstance(translation, str):
                        translations.append(translation)
                
                if debug and (created < 5 or updated < 5):
                    logger.debug(f"    📝 {'Обновление' if is_existing else 'Создание'}: {title_ru} (shikimori_id={shikimori_id}, episodes={episodes})")
                
                # Получаем или создаем объект
                if is_existing and replace:
                    try:
                        anime = Anime.objects.get(shikimori_id=shikimori_id)
                        # Обновляем поля
                        anime.title_ru = title_ru[:255]
                        anime.title_en = title_en[:255] if title_en else ''
                        anime.title_jp = title_jp[:255] if title_jp else ''
                        anime.status = status
                        anime.kind = kind
                        anime.episodes = episodes  # Используем правильное значение
                        anime.year = year
                        anime.score = score
                        anime.poster_url = material_data.get('anime_poster_url', '') or material_data.get('poster_url', '')
                        anime.kodik_id = kodik_id[:255] if kodik_id else ''
                        anime.kodik_link = item.get('link', '')[:500]
                        anime.description = (material_data.get('anime_description') or material_data.get('description', '') or '')[:5000]
                        anime.genres = genres
                        anime.studios = studios
                        anime.translations = translations
                        anime.data_source = 'kodik'
                        anime.save()
                        updated += 1
                        STATS['updated_records'] += 1
                        if debug:
                            logger.debug(f"    ✅ Обновлено: {title_ru} (episodes={episodes})")
                    except Anime.DoesNotExist:
                        # Если не нашли по shikimori_id, пробуем создать
                        is_existing = False
                    except Exception as e:
                        logger.error(f"    ❌ Ошибка обновления {title_ru}: {e}")
                        errors += 1
                        continue
                
                # Если запись новая или не найдена при обновлении
                if not is_existing:
                    anime = Anime(
                        shikimori_id=shikimori_id,
                        title_ru=title_ru[:255],
                        title_en=title_en[:255] if title_en else '',
                        title_jp=title_jp[:255] if title_jp else '',
                        status=status,
                        kind=kind,
                        episodes=episodes,  # Используем правильное значение
                        year=year,
                        score=score,
                        poster_url=material_data.get('anime_poster_url', '') or material_data.get('poster_url', ''),
                        kodik_id=kodik_id[:255] if kodik_id else '',
                        kodik_link=item.get('link', '')[:500],
                        description=(material_data.get('anime_description') or material_data.get('description', '') or '')[:5000],
                        genres=genres,
                        studios=studios,
                        translations=translations,
                        data_source='kodik',
                    )
                    anime_objects.append(anime)
                    created += 1
                    STATS['new_records'] += 1
                
                # Bulk create при достижении размера батча (только для новых записей)
                if len(anime_objects) >= BATCH_SIZE:
                    try:
                        db_start = time.time()
                        Anime.objects.bulk_create(anime_objects, ignore_conflicts=True)
                        db_duration = time.time() - db_start
                        STATS['db_operations'] += 1
                        logger.info(f"  💾 Создано батч: {len(anime_objects)} аниме за {db_duration:.2f} сек")
                    except Exception as e:
                        logger.error(f"  ❌ Ошибка bulk_create: {e}")
                        for obj in anime_objects:
                            try:
                                if not Anime.objects.filter(shikimori_id=obj.shikimori_id).exists():
                                    obj.save()
                                    created += 1
                                    STATS['new_records'] += 1
                                else:
                                    skipped_duplicates += 1
                                    STATS['duplicates_skipped'] += 1
                            except Exception as save_error:
                                errors += 1
                                STATS['errors'] += 1
                                logger.error(f"    ❌ Ошибка сохранения {obj.title_ru}: {save_error}")
                    anime_objects = []
                
                # Прогресс
                if (i + 1) % 50 == 0:
                    logger.info(f"  📊 Прогресс: {i + 1}/{len(all_results)} (создано: {created}, обновлено: {updated}, дубликаты: {skipped_duplicates})")
                    
            except Exception as e:
                errors += 1
                STATS['errors'] += 1
                logger.error(f"  ❌ Ошибка обработки записи {i}: {e}")
                if debug:
                    import traceback
                    logger.debug(traceback.format_exc())
                continue
        
        # Создаем оставшиеся объекты
        if anime_objects:
            try:
                db_start = time.time()
                Anime.objects.bulk_create(anime_objects, ignore_conflicts=True)
                db_duration = time.time() - db_start
                STATS['db_operations'] += 1
                logger.info(f"  💾 Создано финальный батч: {len(anime_objects)} аниме за {db_duration:.2f} сек")
            except Exception as e:
                logger.error(f"  ❌ Ошибка финального bulk_create: {e}")
                for obj in anime_objects:
                    try:
                        if not Anime.objects.filter(shikimori_id=obj.shikimori_id).exists():
                            obj.save()
                            created += 1
                            STATS['new_records'] += 1
                        else:
                            skipped_duplicates += 1
                            STATS['duplicates_skipped'] += 1
                    except Exception as save_error:
                        errors += 1
                        STATS['errors'] += 1
    
    STATS['processing_time'] = time.time() - start_time
    
    # Финальная статистика
    logger.info(f"\n📊 Детальная статистика обработки:")
    logger.info(f"  ✅ Создано новых: {created}")
    logger.info(f"  🔄 Обновлено: {updated}")
    logger.info(f"  ⏭️  Пропущено дубликатов: {skipped_duplicates}")
    logger.info(f"  ⚠️  Пропущено (невалидные): {skipped_invalid}")
    logger.info(f"  ❌ Ошибок: {errors}")
    logger.info(f"  ⏱️  Время обработки: {STATS['processing_time']:.2f} сек")
    
    return created, skipped_duplicates, errors, updated


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='Fast Kodik Importer - массовый импорт аниме из Kodik API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python fast_kodik_import.py                        # Полный импорт (только новые)
  python fast_kodik_import.py --replace             # Полная перезапись всех данных
  python fast_kodik_import.py --limit 25            # Импорт 25 записей (тест)
  python fast_kodik_import.py --limit 100 --debug   # Импорт 100 записей с детальным логгированием
  python fast_kodik_import.py --verbose             # Подробный вывод
  python fast_kodik_import.py --fix-episodes        # Только исправить количество эпизодов
        """
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Количество записей для импорта (для тестирования)'
    )
    
    parser.add_argument(
        '--replace',
        action='store_true',
        help='Полная перезапись существующих записей (обновление всех полей)'
    )
    
    parser.add_argument(
        '--fix-episodes',
        action='store_true',
        help='Только исправить количество эпизодов у существующих записей (без импорта)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Включить режим отладки с детальным выводом'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Включить подробный вывод (без отладки)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Размер батча для bulk_create (по умолчанию: 100)'
    )
    
    return parser.parse_args()


def fix_episodes_only(limit: Optional[int] = None, debug: bool = False):
    """Только исправление количества эпизодов у существующих записей"""
    logger.info("\n" + "=" * 60)
    logger.info("🔄 ИСПРАВЛЕНИЕ КОЛИЧЕСТВА ЭПИЗОДОВ")
    logger.info("=" * 60)
    
    # Получаем аниме для обработки
    anime_list = list(Anime.objects.filter(
        shikimori_id__isnull=False
    ).exclude(shikimori_id=0)[:limit or 10000])
    
    logger.info(f"📊 Найдено аниме для обработки: {len(anime_list)}")
    logger.info(f"{'Название':<45} | {'Было':<6} | {'Стало':<6}")
    logger.info("-" * 60)
    
    updated = 0
    failed = 0
    skipped = 0
    start_time = time.time()
    
    # Используем сессию для ускорения запросов
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; Kodik-Importer/1.0)',
        'Accept': 'application/json',
    })
    
    for idx, anime in enumerate(anime_list):
        try:
            # Получаем данные из Kodik
            params = {
                'token': KODIK_TOKEN,
                'shikimori_id': anime.shikimori_id,
                'with_material_data': 'true',
                'limit': 10,
            }
            
            response = session.get('https://kodik-api.com/search', params=params, timeout=10)
            
            if response.status_code != 200:
                failed += 1
                continue
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                failed += 1
                continue
            
            item = results[0]
            
            # Используем правильную функцию для подсчета эпизодов
            new_episodes = get_episodes_count_correct(item)
            
            if new_episodes and new_episodes != anime.episodes:
                old_episodes = anime.episodes
                anime.episodes = new_episodes
                anime.save(update_fields=['episodes', 'updated_at'])
                logger.info(f"{anime.title_ru[:45]:<45} | {old_episodes:<6} | {new_episodes:<6}")
                updated += 1
            else:
                skipped += 1
                
            # Прогресс
            if (idx + 1) % 50 == 0:
                logger.info(f"  📊 Прогресс: {idx + 1}/{len(anime_list)} (обновлено: {updated}, пропущено: {skipped}, ошибок: {failed})")
                
            time.sleep(0.1)  # Небольшая задержка
            
        except Exception as e:
            failed += 1
            if debug:
                logger.debug(f"  ❌ Ошибка обработки {anime.title_ru}: {e}")
            time.sleep(0.5)
    
    session.close()
    
    duration = time.time() - start_time
    
    logger.info("-" * 60)
    logger.info(f"✅ Обновлено: {updated}")
    logger.info(f"⏭️  Пропущено (уже правильно): {skipped}")
    logger.info(f"❌ Ошибок: {failed}")
    logger.info(f"⏱️  Время: {duration:.2f} сек")
    logger.info("=" * 60)


def fast_import(limit: Optional[int] = None, debug: bool = False, verbose: bool = False, 
                batch_size: int = 100, replace: bool = False, fix_episodes: bool = False):
    """Основная функция импорта"""
    
    # Если только исправление эпизодов
    if fix_episodes:
        fix_episodes_only(limit=limit, debug=debug)
        return
    
    global BATCH_SIZE
    BATCH_SIZE = batch_size
    
    # Настройка уровня логирования
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 Включен режим отладки")
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
        logger.setLevel(logging.INFO)
    
    print("\n" + "=" * 80)
    print("🚀 FAST KODIK IMPORTER")
    print("=" * 80)
    
    if replace:
        print("🔄 РЕЖИМ ПОЛНОЙ ПЕРЕЗАПИСИ: все существующие записи будут обновлены")
    if limit:
        print(f"🧪 ТЕСТОВЫЙ РЕЖИМ: будет импортировано только {limit} записей")
    print("=" * 80)
    
    start_time = datetime.now()
    STATS['total_duration'] = time.time()
    
    # 1. Получение существующих ID
    logger.info("\n" + "-" * 60)
    logger.info("ШАГ 1: Проверка существующих данных")
    logger.info("-" * 60)
    
    existing_shikimori, existing_kodik = get_existing_ids()
    print(f"  ✅ Уже в базе: {len(existing_shikimori)} аниме")
    
    # 2. Загрузка данных из Kodik
    logger.info("\n" + "-" * 60)
    logger.info("ШАГ 2: Загрузка данных из Kodik API")
    logger.info("-" * 60)
    
    all_results = fetch_all_results(limit=limit, debug=debug)
    
    if not all_results:
        logger.error("\n❌ Нет данных для импорта")
        return
    
    print(f"\n✅ Загружено: {len(all_results)} записей")
    
    # 3. Обработка и создание
    logger.info("\n" + "-" * 60)
    logger.info("ШАГ 3: Обработка и импорт данных")
    if replace:
        logger.info("  (режим перезаписи - обновление существующих записей)")
    else:
        logger.info("  (режим добавления - только новые записи)")
    logger.info("-" * 60)
    
    created, skipped_duplicates, errors, updated = process_results(
        all_results, 
        existing_shikimori, 
        existing_kodik, 
        debug=debug,
        replace=replace
    )
    
    # 4. Итоги
    STATS['total_duration'] = time.time() - STATS['total_duration']
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Получаем финальное количество
    total_anime = Anime.objects.count()
    
    print("\n" + "=" * 80)
    print("🎉 ИМПОРТ ЗАВЕРШЕН!")
    print("=" * 80)
    print(f"⏱️  Общее время выполнения: {duration:.2f} сек")
    if replace:
        print(f"🔄 Обновлено записей: {updated}")
    print(f"✅ Создано новых записей: {created}")
    print(f"⏭️  Пропущено дубликатов: {skipped_duplicates}")
    print(f"❌ Ошибок: {errors}")
    print(f"📊 Всего аниме в базе: {total_anime}")
    print(f"📈 Скорость: {(created + updated) / STATS['total_duration']:.1f} записей/сек" if STATS['total_duration'] > 0 else "")
    
    print("\n" + "-" * 60)
    print("📊 Статистика API:")
    print(f"  API запросов: {STATS['api_requests']}")
    print(f"  Ошибок API: {STATS['api_errors']}")
    print(f"  Операций с БД: {STATS['db_operations']}")
    print("=" * 80)
    
    # Сохраняем лог в файл если есть ошибки
    if errors > 0:
        log_file = f"kodik_import_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Kodik Import Log\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"Дата: {datetime.now()}\n")
            f.write(f"Режим: {'Перезапись' if replace else 'Добавление'}\n")
            f.write(f"Создано: {created}\n")
            f.write(f"Обновлено: {updated}\n")
            f.write(f"Пропущено дубликатов: {skipped_duplicates}\n")
            f.write(f"Ошибок: {errors}\n")
            f.write(f"Всего в базе: {total_anime}\n")
        logger.info(f"📝 Лог сохранен в файл: {log_file}")


if __name__ == '__main__':
    args = parse_arguments()
    fast_import(
        limit=args.limit,
        debug=args.debug,
        verbose=args.verbose,
        batch_size=args.batch_size,
        replace=args.replace,
        fix_episodes=args.fix_episodes
    )