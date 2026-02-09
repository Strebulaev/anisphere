import asyncio
import logging
from typing import Dict, List, Optional, Any
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from anime.models import Anime, Genre, Studio
from users.models import User

logger = logging.getLogger(__name__)

class AnimeParsersCollector:
    """Коллектор аниме из различных источников через AnimeParsers"""
    
    def __init__(self):
        self.imported_count = 0
        self.updated_count = 0
        self.errors = []
    
    def import_from_kodik(self, limit_per_page: int = 50, pages_to_parse: int = 1) -> Dict[str, int]:
        """Импорт аниме из Kodik через AnimeParsers"""
        try:
            from anime_parsers_ru import KodikParser
            
            parser = KodikParser()
            
            # Получаем список аниме
            try:
                anime_list, next_page_id = parser.get_list(
                    limit_per_page=limit_per_page,
                    pages_to_parse=pages_to_parse,
                    include_material_data=True,
                    anime_status=None,  # Все статусы
                    only_anime=True    # Только аниме
                )
                
                # Проверяем результат
                if not anime_list:
                    self.errors.append("Kodik вернул пустой список")
                    return {'imported': 0, 'updated': 0, 'errors': 1}
                    
                if not isinstance(anime_list, list):
                    self.errors.append(f"Некорректный формат данных от Kodik: ожидался список")
                    return {'imported': 0, 'updated': 0, 'errors': 1}
                
                return self._process_anime_list(anime_list, 'kodik')
                
            except Exception as e:
                # Обрабатываем специфичные ошибки Kodik
                if "TokenError" in str(e):
                    self.errors.append("Kodik: Ошибка токена. Возможно, API ключ недействителен.")
                elif "ServiceError" in str(e):
                    self.errors.append("Kodik: Ошибка сервиса. Попробуйте позже.")
                elif "timeout" in str(e).lower():
                    self.errors.append("Kodik: Таймаут соединения. Попробуйте позже.")
                else:
                    self.errors.append(f"Ошибка при импорте из Kodik: {str(e)}")
                return {'imported': 0, 'updated': 0, 'errors': 1}
            
        except ImportError:
            self.errors.append("AnimeParsers не установлен. Установите: pip install anime-parsers-ru")
            return {'imported': 0, 'updated': 0, 'errors': 1}
        except Exception as e:
            self.errors.append(f"Общая ошибка при импорте из Kodik: {str(e)}")
            return {'imported': 0, 'updated': 0, 'errors': 1}
    
    def import_from_shikimori(self, status: List[str] = None, page_limit: int = 3) -> Dict[str, int]:
        """Импорт аниме из Shikimori через AnimeParsers"""
        try:
            from anime_parsers_ru import ShikimoriParser
            import time
            
            parser = ShikimoriParser()
            
            # Получаем список аниме с фильтрами
            try:
                anime_list = parser.get_anime_list(
                    status=status or ['ongoing', 'released'],
                    anime_type=['tv', 'movie', 'ova', 'ona'],
                    page_limit=min(page_limit, 2),  # Ограничиваем для надежности
                    sort_by='popularity'
                )
                
                # Проверяем, что получили результат
                if not anime_list:
                    self.errors.append("Shikimori вернул пустой список")
                    return {'imported': 0, 'updated': 0, 'errors': 1}
                    
                return self._process_anime_list(anime_list, 'shikimori')
                
            except Exception as e:
                # Обрабатываем специфичные ошибки Shikimori
                if "timeout" in str(e).lower() or "read timed out" in str(e).lower():
                    self.errors.append("Shikimori недоступен (таймаут). Попробуйте позже.")
                elif "520" in str(e):
                    self.errors.append("Shikimori перегружен. Попробуйте позже.")
                elif "429" in str(e):
                    self.errors.append("Превышен лимит запросов к Shikimori. Попробуйте позже.")
                else:
                    self.errors.append(f"Ошибка при импорте из Shikimori: {str(e)}")
                return {'imported': 0, 'updated': 0, 'errors': 1}
            
        except ImportError:
            self.errors.append("AnimeParsers не установлен")
            return {'imported': 0, 'updated': 0, 'errors': 1}
        except Exception as e:
            self.errors.append(f"Общая ошибка при импорте из Shikimori: {str(e)}")
            return {'imported': 0, 'updated': 0, 'errors': 1}
    
    def import_from_aniboom(self, search_query: str = None) -> Dict[str, int]:
        """Импорт аниме из AniBoom через AnimeParsers"""
        try:
            from anime_parsers_ru import AniboomParser
            
            parser = AniboomParser()
            
            if search_query:
                # Поиск конкретного аниме
                try:
                    print(f"Поиск '{search_query}' в AniBoom...")
                    anime_list = parser.search(search_query)
                    print(f"Найдено результатов: {len(anime_list) if anime_list else 0}")
                    return self._process_anime_list(anime_list, 'aniboom')
                except Exception as e:
                    error_msg = f"Ошибка поиска '{search_query}': {str(e)}"
                    print(f"❌ {error_msg}")
                    self.errors.append(error_msg)
                    return {'imported': 0, 'updated': 0, 'errors': 1}
            else:
                # Получаем популярное аниме (используем поиск по популярным запросам)
                popular_searches = ['Наруто', 'Блич', 'Ванпанчмен', 'Атака титонов', 'Драконий караван', 
                                  'Моя геройская академия', 'Человек-бензопила', 'Джujutsu Kaisen']
                anime_list = []
                errors_count = 0
                
                print(f"🔍 Поиск в AniBoom по {len(popular_searches)} популярным запросам...")
                
                for i, query in enumerate(popular_searches, 1):
                    try:
                        print(f"  [{i}/{len(popular_searches)}] Поиск '{query}'...")
                        
                        # Пробуем сначала быстрый поиск
                        try:
                            results = parser.fast_search(query)
                            if results and isinstance(results, list):
                                anime_list.extend(results[:3])  # Берем первые 3 результата
                                print(f"    ✅ Быстрый поиск: найдено {len(results)} результатов")
                            else:
                                print(f"    ⚠️ Быстрый поиск: результатов нет")
                        except Exception as e:
                            print(f"    ❌ Быстрый поиск ошибка: {e}")
                            errors_count += 1
                            
                        # Если быстрый поиск не дал результатов, пробуем обычный
                        if not anime_list or len([r for r in anime_list if r.get('title', '').lower().find(query.lower()) != -1]) == 0:
                            try:
                                results = parser.search(query)
                                if results and isinstance(results, list):
                                    anime_list.extend(results[:2])  # Берем первые 2 результата
                                    print(f"    ✅ Обычный поиск: найдено {len(results)} результатов")
                                else:
                                    print(f"    ⚠️ Обычный поиск: результатов нет")
                            except Exception as e:
                                print(f"    ❌ Обычный поиск ошибка: {e}")
                                errors_count += 1
                            
                        # Небольшая пауза между запросами
                        import time
                        time.sleep(1)
                            
                    except Exception as e:
                        error_msg = f"Общая ошибка поиска '{query}': {str(e)}"
                        print(f"❌ {error_msg}")
                        self.errors.append(error_msg)
                        errors_count += 1
                        continue
            
                print(f"📊 Итого найдено аниме: {len(anime_list)}")
                
                if not anime_list:
                    error_msg = f"AniBoom: не найдено ни одного аниме (попыток: {len(popular_searches)}, ошибок: {errors_count})"
                    print(f"❌ {error_msg}")
                    self.errors.append(error_msg)
                    return {'imported': 0, 'updated': 0, 'errors': errors_count}
                
                return self._process_anime_list(anime_list, 'aniboom')
            
        except ImportError:
            error_msg = "AnimeParsers не установлен"
            print(f"❌ {error_msg}")
            self.errors.append(error_msg)
            return {'imported': 0, 'updated': 0, 'errors': 1}
        except Exception as e:
            error_msg = f"Общая ошибка при импорте из AniBoom: {str(e)}"
            print(f"❌ {error_msg}")
            self.errors.append(error_msg)
            return {'imported': 0, 'updated': 0, 'errors': 1}
    
    def _process_anime_list(self, anime_list: List[Dict], source: str) -> Dict[str, int]:
        """Обработка списка аниме и сохранение в БД"""
        if not anime_list:
            self.errors.append(f"Получен пустой список от {source}")
            return {'imported': 0, 'updated': 0, 'errors': 1}
            
        if not isinstance(anime_list, list):
            self.errors.append(f"Некорректный формат данных от {source}: ожидался список")
            return {'imported': 0, 'updated': 0, 'errors': 1}
            
        imported = 0
        updated = 0
        
        for i, anime_data in enumerate(anime_list):
            try:
                # Проверяем, что данные аниме корректны
                if not isinstance(anime_data, dict):
                    self.errors.append(f"Элемент {i} от {source} не является словарем")
                    continue
                    
                if not anime_data.get('title'):
                    self.errors.append(f"Элемент {i} от {source} не содержит title")
                    continue
                    
                result = self._save_anime_data(anime_data, source)
                if result == 'created':
                    imported += 1
                elif result == 'updated':
                    updated += 1
                    
            except Exception as e:
                anime_title = anime_data.get('title', f'Элемент {i}') if isinstance(anime_data, dict) else f'Элемент {i}'
                self.errors.append(f"Ошибка обработки {anime_title}: {str(e)}")
                logger.error(f"Ошибка обработки аниме: {e}")
        
        return {
            'imported': imported,
            'updated': updated,
            'errors': len([e for e in self.errors if source in e])
        }
    
    def _save_anime_data(self, anime_data: Dict, source: str) -> str:
        """Сохранение данных аниме в БД"""
        with transaction.atomic():
            try:
                if source == 'kodik':
                    return self._save_kodik_data(anime_data)
                elif source == 'shikimori':
                    return self._save_shikimori_data(anime_data)
                elif source == 'aniboom':
                    return self._save_aniboom_data(anime_data)
                else:
                    raise ValueError(f"Неизвестный источник: {source}")
            except Exception as e:
                self.errors.append(f"Ошибка сохранения аниме {anime_data.get('title', 'Unknown')}: {str(e)}")
                raise
    
    def _save_kodik_data(self, data: Dict) -> str:
        """Сохранение данных из Kodik"""
        title_ru = data.get('title', '')
        title_en = data.get('additional_data', {}).get('title_en', '') or ''
        shikimori_id = data.get('shikimori_id')
        
        # Проверяем существующее аниме
        anime = None
        if shikimori_id:
            try:
                anime = Anime.objects.get(shikimori_id=shikimori_id)
            except Anime.DoesNotExist:
                pass
        
        if not anime:
            # Создаем новое
            anime = Anime(
                title_ru=title_ru,
                title_en=title_en,
                shikimori_id=shikimori_id,
                data_source='shikimori'  # Kodik использует shikimori_id
            )
            created = True
        else:
            # Обновляем существующее
            anime.title_ru = title_ru
            anime.title_en = title_en
            created = False
        
        # Заполняем остальные поля
        anime.description = data.get('material_data', {}).get('description', '') or ''
        anime.year = data.get('year')
        anime.poster_url = data.get('screenshots', [''])[0] if data.get('screenshots') else None
        anime.screenshots = [{'url': url} for url in data.get('screenshots', [])]
        
        # Статус
        material_data = data.get('material_data', {})
        if material_data.get('status') == 'released':
            anime.status = 'finished'
        elif material_data.get('status') == 'ongoing':
            anime.status = 'ongoing'
        else:
            anime.status = 'finished'  # По умолчанию
        
        # Рейтинг
        if material_data.get('score'):
            anime.score = float(material_data['score'])
        
        # Эпизоды
        series_count = data.get('series_count')
        if series_count:
            anime.episodes = series_count
        
        # Сначала сохраняем объект, потом устанавливаем жанры
        anime.save()
        
        # Обрабатываем жанры после сохранения
        genres = material_data.get('genres', [])
        if genres:
            self._update_anime_genres(anime, genres)
        
        return 'created' if created else 'updated'
    
    def _save_shikimori_data(self, data: Dict) -> str:
        """Сохранение данных из Shikimori"""
        shikimori_id = data.get('shikimori_id')
        title_ru = data.get('title', '')
        title_en = data.get('original_title', '') or ''
        
        # Проверяем существующее аниме
        anime = None
        if shikimori_id:
            try:
                anime = Anime.objects.get(shikimori_id=shikimori_id)
            except Anime.DoesNotExist:
                pass
        
        if not anime:
            # Создаем новое
            anime = Anime(
                title_ru=title_ru,
                title_en=title_en,
                shikimori_id=shikimori_id,
                data_source='shikimori'
            )
            created = True
        else:
            # Обновляем существующее
            anime.title_ru = title_ru
            anime.title_en = title_en
            created = False
        
        # Заполняем остальные поля
        anime.year = data.get('year')
        anime.poster_url = data.get('poster')
        
        # Статус
        status = data.get('status', '').lower()
        if status == 'ongoing':
            anime.status = 'ongoing'
        elif status == 'released':
            anime.status = 'finished'
        elif status == 'anons':
            anime.status = 'announced'
        else:
            anime.status = 'finished'
        
        # Тип аниме (для определения количества эпизодов)
        anime_type = data.get('type', '')
        if 'movie' in anime_type.lower():
            anime.episodes = 1
        elif 'tv' in anime_type.lower():
            # Для TV сериалов количество эпизодов неизвестно
            anime.episodes = None
        
        # Сначала сохраняем объект, потом устанавливаем жанры
        anime.save()
        
        # Обрабатываем жанры после сохранения
        genres = data.get('genres', [])
        if genres:
            self._update_anime_genres(anime, genres)
        
        return 'created' if created else 'updated'
    
    def _save_aniboom_data(self, data: Dict) -> str:
        """Сохранение данных из AniBoom"""
        title_ru = data.get('title', '')
        title_en = ', '.join(data.get('other_titles', [])) if data.get('other_titles') else ''
        animego_id = data.get('animego_id')
        
        # Проверяем существующее аниме по заголовку
        anime = None
        try:
            anime = Anime.objects.get(title_ru=title_ru)
        except Anime.DoesNotExist:
            pass
        
        if not anime:
            # Создаем новое
            anime = Anime(
                title_ru=title_ru,
                title_en=title_en,
                data_source='demo'
            )
            created = True
        else:
            # Обновляем существующее
            anime.title_en = title_en
            created = False
        
        # Заполняем остальные поля
        anime.description = data.get('description', '')
        anime.poster_url = data.get('poster_url')
        anime.screenshots = [{'url': url} for url in data.get('screenshots', [])]
        
        # Год
        if data.get('year'):
            anime.year = int(data.get('year'))
        
        # Статус
        status = data.get('status', '').lower()
        if 'онгоинг' in status:
            anime.status = 'ongoing'
        elif 'вышел' in status:
            anime.status = 'finished'
        elif 'анонс' in status:
            anime.status = 'announced'
        else:
            anime.status = 'finished'
        
        # Эпизоды
        episodes_info = data.get('episodes_info', [])
        if episodes_info:
            anime.episodes = len(episodes_info)
        
        # Сначала сохраняем объект, потом устанавливаем жанры
        anime.save()
        
        # Обрабатываем жанры после сохранения
        genres = data.get('genres', [])
        if genres:
            self._update_anime_genres(anime, genres)
        
        return 'created' if created else 'updated'
    
    def _update_anime_genres(self, anime: Anime, genres: List[str]):
        """Обновление жанров аниме"""
        if not genres or not isinstance(genres, list):
            return
            
        genre_objects = []
        for genre_name in genres:
            if not genre_name or not isinstance(genre_name, str):
                continue
                
            genre_name = genre_name.strip()
            if not genre_name:
                continue
                
            try:
                genre, created = Genre.objects.get_or_create(
                    name=genre_name,
                    defaults={'slug': slugify(genre_name)}
                )
                genre_objects.append(genre)
            except Exception as e:
                logger.warning(f"Не удалось создать/найти жанр '{genre_name}': {e}")
                continue
        
        if genre_objects:
            try:
                anime.genres.set(genre_objects)
            except Exception as e:
                logger.error(f"Не удалось установить жанры для аниме {anime.title_ru}: {e}")
    
class Command(BaseCommand):
    help = 'Импорт аниме через AnimeParsers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['kodik', 'shikimori', 'aniboom', 'all'],
            default='all',
            help='Источник для импорта'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Количество элементов на страницу (для Kodik)'
        )
        parser.add_argument(
            '--pages',
            type=int,
            default=1,
            help='Количество страниц для обработки (для Kodik)'
        )
        parser.add_argument(
            '--search',
            type=str,
            help='Поисковый запрос (для AniBoom)'
        )

    def handle(self, *args, **options):
        collector = AnimeParsersCollector()
        source = options['source']
        
        if source in ['kodik', 'all']:
            self.stdout.write(self.style.SUCCESS('🔄 Импорт из Kodik...'))
            result = collector.import_from_kodik(
                limit_per_page=options['limit'],
                pages_to_parse=options['pages']
            )
            self._print_result('Kodik', result)
        
        if source in ['shikimori', 'all']:
            self.stdout.write(self.style.SUCCESS('🔄 Импорт из Shikimori...'))
            result = collector.import_from_shikimori(page_limit=3)
            self._print_result('Shikimori', result)
        
        if source in ['aniboom', 'all']:
            self.stdout.write(self.style.SUCCESS('🔄 Импорт из AniBoom...'))
            result = collector.import_from_aniboom(search_query=options['search'])
            self._print_result('AniBoom', result)
        
        # Выводим ошибки если есть
        if collector.errors:
            self.stdout.write(self.style.ERROR('❌ Ошибки:'))
            for error in collector.errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
    
    def _print_result(self, source: str, result: Dict):
        """Вывод результата импорта"""
        if result['imported'] > 0:
            self.stdout.write(self.style.SUCCESS(f'✅ {source}: Создано {result["imported"]} аниме'))
        if result['updated'] > 0:
            self.stdout.write(self.style.WARNING(f'🔄 {source}: Обновлено {result["updated"]} аниме'))
        if result['errors'] > 0:
            self.stdout.write(self.style.ERROR(f'❌ {source}: {result["errors"]} ошибок'))