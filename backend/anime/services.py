import time
import random
from datetime import datetime
from django.db import transaction
from parsers.shikimori import ShikimoriParser
from .models import Anime, Genre, Studio
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

class AnimeImportService:
    """Мощный сервис импорта для больших объемов данных"""
    
    def __init__(self):
        self.parser = ShikimoriParser()
    
    def import_all_shikimori(self, target: int = 50000, method: str = 'mixed', workers: int = 4) -> list:
        """Полная загрузка аниме с Shikimori"""
        print(f"Загрузка {target} аниме методом {method}...")
        imported = []
        
        if method == 'bulk':
            imported = self._bulk_import(target)
        elif method == 'id_range':
            imported = self._id_range_import(target, workers)
        elif method == 'mixed':
            imported = self._mixed_import(target, workers)
        elif method == 'complete':
            imported = self._complete_import(target, workers)
        
        return imported
    
    def _bulk_import(self, target: int) -> list:
        """Массовая загрузка через API"""
        print("Загрузка через bulk API...")
        all_anime = self.parser.get_all_anime_bulk(target)
        
        imported = []
        for anime_data in all_anime:
            try:
                normalized = self.parser.normalize_anime_data(anime_data)
                anime = self._save_anime_to_db(normalized)
                if anime:
                    imported.append(anime)
                    
                if len(imported) % 50 == 0:
                    print(f"Загружено: {len(imported)}/{target}")
                    
            except Exception as e:
                print(f"Ошибка: {e}")
                continue
        
        return imported
    
    def _id_range_import(self, target: int, workers: int = 4) -> list:
        """Импорт по диапазону ID с параллельной обработкой"""
        print(f"Импорт по ID диапазонам, потоков: {workers}")
        
        # Разбиваем на диапазоны
        max_id = 200000  # Предполагаемый максимум
        chunk_size = math.ceil(max_id / workers)
        
        futures = []
        imported = []
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for i in range(workers):
                start_id = i * chunk_size + 1
                end_id = min((i + 1) * chunk_size, max_id)
                
                future = executor.submit(
                    self._process_id_range, 
                    start_id, end_id, target // workers
                )
                futures.append(future)
            
            # Собираем результаты
            for future in as_completed(futures):
                try:
                    chunk_imported = future.result()
                    imported.extend(chunk_imported)
                    print(f"Поток завершен, добавлено: {len(chunk_imported)}")
                except Exception as e:
                    print(f"Ошибка потока: {e}")
        
        return imported[:target]
    
    def _mixed_import(self, target: int, workers: int = 4) -> list:
        """Смешанный метод"""
        print("Смешанный импорт...")
        imported = []
        
        # 30% через bulk API
        bulk_target = target // 3
        if bulk_target > 0:
            print(f"Загрузка {bulk_target} через bulk API...")
            bulk_imported = self._bulk_import(bulk_target)
            imported.extend(bulk_imported)
        
        # 70% через ID диапазоны
        remaining = target - len(imported)
        if remaining > 0:
            print(f"Загрузка {remaining} через ID диапазоны...")
            id_imported = self._id_range_import(remaining, workers)
            imported.extend(id_imported[:remaining])
        
        return imported
    
    def _complete_import(self, target: int, workers: int = 4) -> list:
        """Полная загрузка всех доступных аниме"""
        print("Полная загрузка всех аниме...")
        
        imported = []
        current_id = 1
        batch_size = 1000
        max_id = 300000  # Более широкий диапазон
        
        while len(imported) < target and current_id < max_id:
            end_id = min(current_id + batch_size - 1, max_id)
            print(f"Обработка диапазона {current_id}-{end_id}")
            
            # Параллельная обработка батча
            with ThreadPoolExecutor(max_workers=workers) as executor:
                chunk_size = batch_size // workers
                futures = []
                
                for i in range(workers):
                    chunk_start = current_id + i * chunk_size
                    chunk_end = min(chunk_start + chunk_size - 1, end_id)
                    
                    if chunk_start <= end_id:
                        future = executor.submit(
                            self._process_id_range,
                            chunk_start, chunk_end,
                            batch_size // workers
                        )
                        futures.append(future)
                
                # Собираем результаты
                for future in as_completed(futures):
                    try:
                        chunk_imported = future.result()
                        imported.extend(chunk_imported)
                    except Exception as e:
                        print(f"Ошибка в батче: {e}")
            
            current_id = end_id + 1
            time.sleep(1)  # Пауза между батчами
            
            if len(imported) >= target:
                break
        
        return imported[:target]
    
    def _process_id_range(self, start_id: int, end_id: int, limit: int) -> list:
        """Обработка диапазона ID"""
        imported = []
        
        for anime_id in range(start_id, end_id + 1):
            if len(imported) >= limit:
                break
                
            try:
                anime_data = self.parser.get_anime_by_id(anime_id)
                if anime_data:
                    normalized = self.parser.normalize_anime_data(anime_data)
                    anime = self._save_anime_to_db(normalized)
                    if anime:
                        imported.append(anime)
                        
                if len(imported) % 25 == 0:
                    print(f"Диапазон {start_id}-{end_id}: {len(imported)}")
                    
            except Exception as e:
                if "404" not in str(e):
                    print(f"Ошибка ID {anime_id}: {e}")
                continue
        
        return imported
    
    def _save_anime_to_db(self, anime_data: dict) -> Anime:
        """Сохранение аниме в БД"""
        try:
            with transaction.atomic():
                # Создаем или обновляем аниме
                anime, created = Anime.objects.update_or_create(
                    shikimori_id=anime_data['id'],
                    defaults={
                        'title_ru': anime_data['title_ru'],
                        'title_en': anime_data['title_en'],
                        'title_jp': anime_data['title_jp'],
                        'description': anime_data['description'],
                        'year': anime_data['year'],
                        'status': anime_data['status'],
                        'episodes': anime_data['episodes'],
                        'score': anime_data['score'],
                        'poster_url': anime_data['poster_url'],
                        'screenshots': anime_data.get('screenshots'),
                        'data_source': 'shikimori'
                    }
                )
                
                # Добавляем жанры
                if anime_data['genres']:
                    for genre_data in anime_data['genres']:
                        genre_name = genre_data['name']
                        if genre_name:
                            genre, _ = Genre.objects.get_or_create(
                                name=genre_name,
                                defaults={'slug': genre_name.lower().replace(' ', '-')}
                            )
                            anime.genres.add(genre)
                
                # Добавляем студии
                if 'studios' in anime_data and anime_data['studios']:
                    for studio_name in anime_data['studios']:
                        if studio_name:
                            studio, _ = Studio.objects.get_or_create(
                                name=studio_name,
                                defaults={'slug': studio_name.lower().replace(' ', '-')}
                            )
                            anime.studios.add(studio)
                
                action = "Создано" if created else "Обновлено"
                print(f"  OK {action}: {anime.title_ru}")
                
                return anime
                
        except Exception as e:
            print(f"  X Ошибка сохранения: {e}")
            return None
    
    def import_single_anime(self, shikimori_id: int) -> Anime:
        """Импорт одного аниме"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ID: {shikimori_id}")
        
        try:
            # Получаем данные
            raw_data = self.parser.get_anime_by_id(shikimori_id)
            if not raw_data:
                print(f"  X Не найдено")
                return None
            
            # Нормализуем
            data = self.parser.normalize_anime_data(raw_data)
            
            # Сохраняем
            anime = self._save_anime_to_db(data)
            return anime
                
        except Exception as e:
            print(f"  X Ошибка: {e}")
            return None
    
    def import_by_known_ids(self, anime_ids: list) -> list:
        """Импорт по списку известных ID"""
        imported = []
        
        for idx, anime_id in enumerate(anime_ids):
            if Anime.objects.filter(shikimori_id=anime_id).exists():
                print(f"[{idx+1}/{len(anime_ids)}] Уже есть ID {anime_id}")
                continue
            
            try:
                anime = self.import_single_anime(anime_id)
                if anime:
                    imported.append(anime)
                    print(f"[{idx+1}/{len(anime_ids)}]")
                time.sleep(0.5)
            except Exception as e:
                print(f"[{idx+1}/{len(anime_ids)}] X Ошибка ID {anime_id}: {e}")
                time.sleep(1)
        
        return imported