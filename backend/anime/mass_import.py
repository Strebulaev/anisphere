import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
from django.db import transaction
from django.core.management.base import BaseCommand
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from anime.models import Anime, Genre, Studio
from parsers.multi_source import MultiSourceParser

class MassAnimeImporter:
    """Массовый импортёр аниме"""
    
    def __init__(self, max_workers=20):
        self.max_workers = max_workers
        self.parser = MultiSourceParser(max_workers=max_workers)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.stats = {
            'total_attempted': 0,
            'total_imported': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def import_100k(self):
        """Импорт 100000 аниме"""
        print("=" * 80)
        print("НАЧАЛО МАССОВОГО ИМПОРТА 100000+ АНИМЕ")
        print("=" * 80)

        self.stats['start_time'] = datetime.now()

        strategies = [
            self._strategy_popular_ids,      # 40000
            self._strategy_year_ranges,      # 30000
            self._strategy_genre_based,      # 20000
            self._strategy_random_ids,       # 10000
        ]

        for strategy in strategies:
            try:
                strategy()
            except Exception as e:
                print(f"Ошибка в стратегии: {e}")
                continue

        self.stats['end_time'] = datetime.now()
        self._print_stats()

    def import_ultra_fast(self):
        """Ультра-быстрый импорт всех аниме подряд"""
        print("=" * 80)
        print("🚀 ULTRA FAST MODE: ИМПОРТ ВСЕХ АНИМЕ С SHIKIMORI")
        print("=" * 80)

        self.stats['start_time'] = datetime.now()

        # Простая стратегия: все ID подряд от 1 до 500000
        total_ids = 500000
        batch_size = 1000  # Огромные батчи для скорости

        print(f"🎯 Цель: {total_ids} аниме")
        print(f"⚡ Режим: {self.max_workers} потоков, без задержек")

        imported = 0
        for start in range(1, total_ids + 1, batch_size):
            end = min(start + batch_size - 1, total_ids)
            ids = list(range(start, end + 1))

            batch_imported = self._import_batch_ultra(ids)
            imported += batch_imported

            print(f"📊 Прогресс: {start}-{end} → Импортировано: {batch_imported} (Всего: {imported})")

            if imported % 1000 == 0:
                print(f"🎉 Достигнуто: {imported} аниме!")

        self.stats['end_time'] = datetime.now()
        self._print_stats()
    
    def _strategy_popular_ids(self):
        """Стратегия 1: Популярные ID (40000)"""
        print("\n[СТРАТЕГИЯ 1] Популярные ID...")
        
        # Известные популярные диапазоны
        popular_ranges = [
            (1, 10000, 10000),      # Очень популярные
            (10001, 30000, 15000),  # Популярные
            (30001, 60000, 10000),  # Средние
            (60001, 100000, 5000),  # Менее популярные
        ]
        
        total_to_import = 40000
        imported = 0
        
        for start, end, target in popular_ranges:
            if imported >= total_to_import:
                break
            
            print(f"  Диапазон {start}-{end}...")
            
            # Генерируем ID из диапазона
            ids_needed = min(target, total_to_import - imported)
            ids = self.parser.get_random_ids_from_range(start, end, ids_needed)
            
            # Импортируем батчами
            batch_size = 500
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i+batch_size]
                batch_imported = self._import_batch(batch_ids)
                imported += batch_imported
                
                print(f"    Импортировано: {imported}/{total_to_import}")
                
                if imported >= total_to_import:
                    break
    
    def _strategy_year_ranges(self):
        """Стратегия 2: По годам (30000)"""
        print("\n[СТРАТЕГИЯ 2] Импорт по годам...")
        
        # Годы с наибольшим количеством аниме
        productive_years = [
            (2026, 1500), (2023, 1500), (2022, 1500), (2021, 1500),
            (2020, 1500), (2019, 1500), (2018, 1500), (2017, 1500),
            (2016, 1500), (2015, 1500), (2014, 1500), (2013, 1500),
            (2012, 1500), (2011, 1500), (2010, 1500),
            (2009, 1000), (2008, 1000), (2007, 1000), (2006, 1000),
            (2005, 1000), (2004, 1000), (2003, 1000), (2002, 1000),
            (2001, 500), (2000, 500), (1999, 500), (1998, 500),
            (1997, 500), (1996, 500), (1995, 500), (1990, 300),
            (1985, 200), (1980, 100), (1975, 50), (1970, 50),
        ]
        
        total_target = 30000
        imported = 0
        
        for year, target in productive_years:
            if imported >= total_target:
                break
            
            print(f"  Год {year} (цель: {target})...")
            
            # Пытаемся найти аниме этого года через поиск
            try:
                year_ids = self._find_anime_by_year(year, target)
                if year_ids:
                    batch_imported = self._import_batch(year_ids[:target])
                    imported += batch_imported
                    print(f"    Найдено: {len(year_ids)}, Импортировано: {batch_imported}")
            except Exception as e:
                print(f"    Ошибка года {year}: {e}")
                continue
    
    def _strategy_genre_based(self):
        """Стратегия 3: По жанрам (20000)"""
        print("\n[СТРАТЕГИЯ 3] Импорт по жанрам...")
        
        # Популярные жанры с их ID в Shikimori
        genres = [
            (1, 'Action', 3000),         # Экшен
            (2, 'Adventure', 2000),      # Приключения
            (4, 'Comedy', 2500),         # Комедия
            (7, 'Mystery', 1500),        # Мистика
            (10, 'Fantasy', 2000),       # Фэнтези
            (22, 'Romance', 1500),       # Романтика
            (27, 'Shounen', 2000),       # Сёнен
            (28, 'Shoujo', 1000),        # Сёдзё
            (24, 'Sci-Fi', 1500),        # Научная фантастика
            (36, 'Slice of Life', 1500), # Повседневность
            (31, 'Supernatural', 1500),  # Сверхъестественное
            (40, 'Psychological', 1000), # Психологическое
        ]
        
        total_target = 20000
        imported = 0
        
        for genre_id, genre_name, target in genres:
            if imported >= total_target:
                break
            
            print(f"  Жанр {genre_name} (цель: {target})...")
            
            try:
                # Получаем аниме по жанру
                url = "https://shikimori.one/api/animes"
                params = {
                    'genre': genre_id,
                    'limit': min(target, 100),
                    'order': 'popularity',
                    'page': 1
                }
                
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    anime_list = response.json()
                    ids = [item['id'] for item in anime_list]
                    
                    if ids:
                        batch_imported = self._import_batch(ids[:target])
                        imported += batch_imported
                        print(f"    Импортировано: {batch_imported}")
                        
                time.sleep(1)
                
            except Exception as e:
                print(f"    Ошибка жанра {genre_name}: {e}")
                continue
    
    def _strategy_random_ids(self):
        """Стратегия 4: Случайные ID (10000)"""
        print("\n[СТРАТЕГИЯ 4] Случайные ID...")
        
        total_target = 10000
        imported = 0
        attempts = 0
        max_attempts = total_target * 3
        
        while imported < total_target and attempts < max_attempts:
            batch_size = 100
            batch_ids = []
            
            # Генерируем случайные ID
            for _ in range(batch_size):
                # 80% в диапазоне 1-200000, 20% в 200001-500000
                if random.random() < 0.8:
                    anime_id = random.randint(1, 200000)
                else:
                    anime_id = random.randint(200001, 500000)
                batch_ids.append(anime_id)
            
            batch_imported = self._import_batch(batch_ids)
            imported += batch_imported
            attempts += batch_size
            
            print(f"  Попытка {attempts}: импортировано {imported}/{total_target}")
            
            # Прогресс каждые 1000
            if imported % 1000 == 0:
                print(f"  [ПРОГРЕСС] {imported}/{total_target}")
    
    def _import_batch(self, anime_ids: List[int]) -> int:
        """Импорт батча аниме"""
        imported = 0
        
        # Фильтруем уже существующие
        existing_ids = set(Anime.objects.filter(
            shikimori_id__in=anime_ids
        ).values_list('shikimori_id', flat=True))
        
        new_ids = [aid for aid in anime_ids if aid not in existing_ids]
        
        if not new_ids:
            return 0
        
        # Многопоточная загрузка
        with ThreadPoolExecutor(max_workers=self.parser.max_workers) as executor:
            future_to_id = {
                executor.submit(self._fetch_and_save, anime_id): anime_id
                for anime_id in new_ids[:200]  # Увеличенный батч
            }
            
            for future in as_completed(future_to_id):
                anime_id = future_to_id[future]
                try:
                    success = future.result(timeout=30)
                    if success:
                        imported += 1
                except Exception as e:
                    self.stats['errors'] += 1
                    if self.stats['errors'] % 100 == 0:
                        print(f"    [ОШИБКИ] {self.stats['errors']} ошибок")
        
        return imported

    def _import_batch_ultra(self, anime_ids: List[int]) -> int:
        """Ультра-быстрый импорт батча без задержек"""
        imported = 0

        # Фильтруем уже существующие
        existing_ids = set(Anime.objects.filter(
            shikimori_id__in=anime_ids
        ).values_list('shikimori_id', flat=True))

        new_ids = [aid for aid in anime_ids if aid not in existing_ids]

        if not new_ids:
            return 0

        # Многопоточная загрузка без лимитов
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_id = {
                executor.submit(self._fetch_and_save_ultra, anime_id): anime_id
                for anime_id in new_ids
            }

            for future in as_completed(future_to_id):
                anime_id = future_to_id[future]
                try:
                    success = future.result(timeout=5)  # Короткий таймаут
                    if success:
                        imported += 1
                except Exception as e:
                    pass  # Игнорируем ошибки в ultra mode

        return imported

    def _fetch_and_save_ultra(self, anime_id: int) -> bool:
        """Ультра-быстрая загрузка без retry и задержек"""
        try:
            url = f"https://shikimori.one/api/animes/{anime_id}"
            response = self.session.get(url, timeout=3)

            if response.status_code == 404:
                return False

            response.raise_for_status()
            data = response.json()

            # Быстрое сохранение без транзакций
            anime, created = Anime.objects.get_or_create(
                shikimori_id=anime_id,
                defaults={
                    'title_ru': data.get('russian') or data.get('name'),
                    'title_en': data.get('english') or data.get('name'),
                    'title_jp': data.get('japanese'),
                    'description': data.get('description', '')[:2000],
                    'year': data.get('aired_on', '').split('-')[0] if data.get('aired_on') else None,
                    'status': self._map_status(data.get('status')),
                    'episodes': data.get('episodes'),
                    'score': data.get('score'),
                    'poster_url': f"https://shikimori.one{data['image']['original']}" if data.get('image') else '',
                    'trailer_url': data.get('videos', [{}])[0].get('url', '') if data.get('videos') else '',
                    'data_source': 'shikimori'
                }
            )

            if created:
                # Жанры добавляем отдельно если нужно
                if data.get('genres'):
                    for genre_data in data['genres']:
                        genre_name = genre_data.get('russian') or genre_data.get('name')
                        if genre_name:
                            genre, _ = Genre.objects.get_or_create(
                                name=genre_name,
                                defaults={'slug': genre_name.lower().replace(' ', '-')}
                            )
                            anime.genres.add(genre)

                print(f"✅ {anime.title_ru or anime.title_en} (ID: {anime_id})")
                return True

            return False

        except Exception as e:
            return False

    def _fetch_and_save(self, anime_id: int) -> bool:
        """Получить и сохранить одно аниме"""
        try:
            url = f"https://shikimori.one/api/animes/{anime_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 404:
                return False
            
            response.raise_for_status()
            data = response.json()
            
            # Сохраняем в базу
            with transaction.atomic():
                anime, created = Anime.objects.get_or_create(
                    shikimori_id=anime_id,
                    defaults={
                        'title_ru': data.get('russian') or data.get('name'),
                        'title_en': data.get('english') or data.get('name'),
                        'title_jp': data.get('japanese'),
                        'description': data.get('description', '')[:2000],
                        'year': data.get('aired_on', '').split('-')[0] if data.get('aired_on') else None,
                        'status': self._map_status(data.get('status')),
                        'episodes': data.get('episodes'),
                        'score': data.get('score'),
                        'poster_url': f"https://shikimori.one{data['image']['original']}" if data.get('image') else '',
                        'trailer_url': data.get('videos', [{}])[0].get('url', '') if data.get('videos') else '',
                        'data_source': 'shikimori'
                    }
                )
                
                if created and data.get('genres'):
                    for genre_data in data['genres']:
                        genre_name = genre_data.get('russian') or genre_data.get('name')
                        if genre_name:
                            genre, _ = Genre.objects.get_or_create(
                                name=genre_name,
                                defaults={'slug': genre_name.lower().replace(' ', '-')}
                            )
                            anime.genres.add(genre)
            
            if created:
                print(f"✅ Imported: {anime.title_ru or anime.title_en} (ID: {anime_id})")

            time.sleep(0.002)  # Умеренная задержка
            return created

        except Exception as e:
            if "429" in str(e):  # Rate limit
                time.sleep(5)
            return False
    
    def _find_anime_by_year(self, year: int, limit: int = 100) -> List[int]:
        """Найти аниме по году"""
        try:
            url = "https://shikimori.one/api/animes"
            params = {
                'year': year,
                'limit': min(limit, 50),
                'order': 'id',
                'page': 1
            }
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                anime_list = response.json()
                return [item['id'] for item in anime_list]
        except:
            pass
        
        return []
    
    def _map_status(self, status: str) -> str:
        mapping = {'released': 'finished', 'ongoing': 'ongoing', 'anons': 'announced'}
        return mapping.get(status, 'finished')
    
    def _print_stats(self):
        """Печать статистики"""
        duration = self.stats['end_time'] - self.stats['start_time']
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        
        print("\n" + "=" * 80)
        print("СТАТИСТИКА ИМПОРТА")
        print("=" * 80)
        print(f"Всего попыток: {self.stats['total_attempted']}")
        print(f"Импортировано: {self.stats['total_imported']}")
        print(f"Ошибок: {self.stats['errors']}")
        print(f"Время выполнения: {hours}ч {minutes}м {seconds}с")
        print(f"Скорость: {self.stats['total_imported'] / max(duration.seconds, 1):.1f} аниме/сек")
        
        # Статистика базы
        print(f"\nВ базе всего: {Anime.objects.count()} аниме")
        print(f"Жанров: {Genre.objects.count()}")
        print(f"Студий: {Studio.objects.count()}")