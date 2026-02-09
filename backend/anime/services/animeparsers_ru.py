"""Интеграция с anime-parsers-ru для получения данных об аниме"""
import time
import logging
from typing import Dict, List, Optional, Tuple
from .base import BaseAnimeParser

try:
    from anime_parsers_ru import (
        KodikParser, ShikimoriParser, AniboomParser, JutsuParser
    )
    from anime_parsers_ru.errors import (
        TokenError, ServiceError, NoResults, QualityNotFound,
        ContentBlocked, TooManyRequests, ServiceIsOverloaded
    )
    ANIME_PARSERS_AVAILABLE = True
except ImportError as e:
    ANIME_PARSERS_AVAILABLE = False
    logging.warning(f"anime-parsers-ru не установлен: {e}")

logger = logging.getLogger(__name__)


class AnimeParsersRuParser(BaseAnimeParser):
    """Парсер на основе anime-parsers-ru с поддержкой мультиисточниковости"""
    
    def __init__(self):
        super().__init__()
        try:
            from anime_parsers_ru import ShikimoriParser, KodikParser, AniboomParser
            self.shikimori_parser = ShikimoriParser()
            self.kodik_parser = KodikParser(validate_token=False)
            self.aniboom_parser = AniboomParser()
            logger.info("Парсеры успешно инициализированы")
        except ImportError as e:
            logger.error(f"Ошибка импорта парсеров: {e}")
            self.shikimori_parser = None
            self.kodik_parser = None
            self.aniboom_parser = None
        except Exception as e:
            logger.error(f"Ошибка инициализации парсеров: {e}")
            self.shikimori_parser = None
            self.kodik_parser = None
            self.aniboom_parser = None
    
    def search_anime(self, query: str, limit: int = 20) -> List[Dict]:
        """Поиск аниме по названию"""
        all_results = []
        
        try:
            # Пробуем поиск в разных источниках
            if self.shikimori_parser:
                try:
                    results = self.shikimori_parser.search(query)
                    for result in results[:limit]:
                        normalized = self._normalize_shikimori_data(result)
                        normalized['source'] = 'shikimori'
                        all_results.append(normalized)
                except Exception as e:
                    logger.warning(f"Ошибка поиска в Shikimori: {e}")
            
            if self.kodik_parser and len(all_results) < limit:
                try:
                    results = self.kodik_parser.search(
                        title=query,
                        limit=limit - len(all_results),
                        include_material_data=True,
                        only_anime=True
                    )
                    for result in results:
                        normalized = self._normalize_kodik_data(result)
                        normalized['source'] = 'kodik'
                        all_results.append(normalized)
                except Exception as e:
                    logger.warning(f"Ошибка поиска в Kodik: {e}")
            
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка поиска аниме: {e}")
            return []
        
    def get_anime_by_id(self, external_id: int) -> Optional[Dict]:
        """Получение аниме по внешнему ID"""
        try:
            # Пробуем получить из Shikimori
            if self.shikimori_parser:
                try:
                    anime_data = self.shikimori_parser.get_anime_by_id(external_id)
                    if anime_data:
                        normalized = self._normalize_shikimori_data(anime_data)
                        normalized['source'] = 'shikimori'
                        return normalized
                except Exception as e:
                    logger.warning(f"Ошибка получения аниме из Shikimori: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения аниме по ID: {e}")
            return None
    
    def get_popular_anime(self, page: int = 1, limit: int = 50) -> List[Dict]:
        """Получение популярных аниме"""
        try:
            # Используем прямой API запрос к Shikimori
            import requests
            
            url = "https://shikimori.one/api/animes"
            params = {
                'page': page,
                'limit': min(50, limit),
                'order': 'popularity'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            results = response.json()
            popular_anime = []
            
            for anime_data in results:
                normalized = self._normalize_shikimori_data(anime_data)
                normalized['source'] = 'shikimori'
                popular_anime.append(normalized)
            
            return popular_anime
            
        except Exception as e:
            logger.error(f"Ошибка получения популярных аниме: {e}")
            return []
    
    def get_all_anime(self, source: str = 'all', page: int = 1, limit: int = 50) -> List[Dict]:
        """Получение всех аниме из всех доступных источников"""
        all_anime = []
        
        try:
            sources = ['shikimori', 'kodik', 'aniboom'] if source == 'all' else [source]
            
            for src in sources:
                logger.info(f"Получаем аниме из источника: {src}")
                
                if src == 'shikimori' and self.shikimori_parser:
                    anime_list = self._get_all_anime_from_shikimori(page, limit)
                elif src == 'kodik' and self.kodik_parser:
                    anime_list = self._get_all_anime_from_kodik(limit)
                elif src == 'aniboom' and self.aniboom_parser:
                    anime_list = self._get_all_anime_from_aniboom(limit)
                else:
                    logger.warning(f"Парсер {src} недоступен")
                    continue
                
                all_anime.extend(anime_list)
                
                # Пауза между источниками
                time.sleep(1)
            
            # Объединяем связанные аниме
            merged_anime = self._merge_related_anime(all_anime)
            
            logger.info(f"Всего получено аниме: {len(merged_anime)}")
            return merged_anime[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка получения всех аниме: {e}")
            return []
    
    def _get_all_anime_from_shikimori(self, page: int, limit: int) -> List[Dict]:
        """Получение всех аниме из Shikimori API"""
        all_anime = []
        
        try:
            import requests
            
            # Увеличиваем timeout и используем более простой подход
            timeout = 30
            
            # Базовый URL для Shikimori API
            base_url = "https://shikimori.one/api/animes"
            
            # Простые параметры
            params = {
                'page': page,
                'limit': min(20, limit),  # уменьшаем до 20 за запрос
            }
            
            current_page = page
            
            while len(all_anime) < limit:
                try:
                    params['page'] = current_page
                    
                    logger.info(f"Запрашиваем страницу {current_page} из Shikimori API...")
                    
                    response = requests.get(base_url, params=params, timeout=timeout)
                    response.raise_for_status()
                    
                    results = response.json()
                    
                    if not results:
                        logger.info(f"Страница {current_page} пуста, завершаем")
                        break
                    
                    logger.info(f"Получено {len(results)} аниме со страницы {current_page}")
                    
                    for anime_data in results:
                        try:
                            # Нормализуем данные напрямую, без дополнительных запросов
                            normalized = self._normalize_shikimori_data(anime_data)
                            normalized['source'] = 'shikimori'
                            all_anime.append(normalized)
                            
                            if len(all_anime) >= limit:
                                break
                        except Exception as e:
                            logger.warning(f"Ошибка обработки аниме: {e}")
                            continue
                    
                    # Если получено меньше чем запрашивали, значит это последняя страница
                    if len(results) < params['limit']:
                        logger.info("Получена последняя страница")
                        break
                    
                    current_page += 1
                    
                    # Пауза между запросами
                    time.sleep(1)
                    
                except requests.RequestException as e:
                    logger.error(f"Ошибка HTTP запроса на страницу {current_page}: {e}")
                    # Пробуем следующую страницу
                    current_page += 1
                    continue
                except Exception as e:
                    logger.error(f"Общая ошибка на странице {current_page}: {e}")
                    break
            
            logger.info(f"Всего получено аниме: {len(all_anime)}")
            return all_anime
            
        except Exception as e:
            logger.error(f"Критическая ошибка получения аниме из Shikimori: {e}")
            return []
    
    def _get_all_anime_from_kodik(self, limit: int) -> List[Dict]:
        """Получение аниме из Kodik"""
        anime_list = []
        
        try:
            # Используем популярные поисковые запросы для получения максимального количества аниме
            popular_searches = [
                'naruto', 'one piece', 'dragon ball', 'attack on titan', 'demon slayer',
                'my hero academia', 'death note', 'fullmetal alchemist', 'bleach', 'fairy tail',
                'sword art online', 'tokyo ghoul', 'one punch man', 'mob psycho', 'violet evergarden',
                'your name', 'spirited away', 'neon genesis evangelion', 'cowboy bebop', 'akira',
                'ghost in the shell', 'princess mononoke', 'nausicaa', 'porco rosso', 'kiki delivery service',
                'hunter x hunter', 'jojo bizarre adventure', 'fate stay night', 'steins gate',
                'madoka magica', 'rezero', 'kono suba', 'overlord', 'sao', 're zero',
                'chainsaw man', 'jujutsu kaisen', 'spy family', 'mob', 'haikyuu', 'kuroko',
                'assassination classroom', 'oregairu', 'monster', 'berserk', 'vagabond',
                'saint seiya', 'yu-gi-oh', 'pokemon', 'digimon', 'cardcaptor', 'sailor moon'
            ]
            
            seen_ids = set()
            
            for search_term in popular_searches:
                try:
                    results = self.kodik_parser.search(
                        title=search_term,
                        limit=15,
                        include_material_data=True,
                        only_anime=True
                    )
                    
                    for anime in results:
                        anime_id = anime.get('shikimori_id') or anime.get('id')
                        if anime_id and anime_id not in seen_ids:
                            seen_ids.add(anime_id)
                            normalized = self._normalize_kodik_data(anime)
                            normalized['source'] = 'kodik'
                            anime_list.append(normalized)
                            
                            if len(anime_list) >= limit:
                                break
                                
                except Exception as e:
                    logger.warning(f"Ошибка поиска '{search_term}' в Kodik: {e}")
                    continue
                    
                if len(anime_list) >= limit:
                    break
                    
        except Exception as e:
            logger.error(f"Ошибка получения аниме из Kodik: {e}")
        
        return anime_list[:limit]
    
    def _get_all_anime_from_aniboom(self, limit: int) -> List[Dict]:
        """Получение аниме из Aniboom"""
        anime_list = []
        
        try:
            # Используем популярные поисковые запросы
            popular_searches = [
                'naruto', 'one piece', 'dragon ball', 'attack on titan', 'demon slayer',
                'my hero academia', 'death note', 'fullmetal alchemist', 'bleach', 'fairy tail'
            ]
            
            seen_ids = set()
            
            for search_term in popular_searches:
                try:
                    results = self.aniboom_parser.search(search_term, limit=10)
                    
                    for anime in results:
                        anime_id = anime.get('id')
                        if anime_id and anime_id not in seen_ids:
                            seen_ids.add(anime_id)
                            normalized = self._normalize_aniboom_data(anime)
                            normalized['source'] = 'aniboom'
                            anime_list.append(normalized)
                            
                            if len(anime_list) >= limit:
                                break
                                
                except Exception as e:
                    logger.warning(f"Ошибка поиска '{search_term}' в Aniboom: {e}")
                    continue
                    
                if len(anime_list) >= limit:
                    break
                    
        except Exception as e:
            logger.error(f"Ошибка получения аниме из Aniboom: {e}")
        
        return anime_list[:limit]
    
    def _normalize_aniboom_data(self, data: Dict) -> Dict:
        """Нормализация данных от Aniboom в единый формат"""
        try:
            return {
                'id': data.get('id'),
                'shikimori_id': data.get('shikimori_id'),
                'title_ru': data.get('russian', '') or data.get('title', '') or 'Без названия',
                'title_en': data.get('english', '') or data.get('title', ''),
                'title_jp': data.get('japanese', '') or '',
                'description': data.get('description', ''),
                'year': data.get('year'),
                'status': data.get('status', 'finished'),
                'kind': self._normalize_kind(data.get('type', 'tv')),
                'episodes': data.get('episodes'),
                'score': data.get('score'),
                'poster_url': data.get('poster', '') or data.get('image', ''),
                'genres': self._safe_get_list(data.get('genres', [])),
                'studios': self._safe_get_list(data.get('studios', [])),
                'raw': data
            }
        except Exception as e:
            logger.warning(f"Ошибка нормализации данных Aniboom: {e}")
            return {
                'id': data.get('id'),
                'title_ru': 'Без названия',
                'title_en': '',
                'title_jp': '',
                'description': '',
                'year': None,
                'status': 'finished',
                'kind': 'tv',
                'episodes': None,
                'score': None,
                'poster_url': '',
                'genres': [],
                'studios': [],
                'raw': data
            }
    
    def _normalize_kodik_data(self, data: Dict) -> Dict:
        """Нормализация данных от Kodik в единый формат"""
        try:
            # Безопасное получение названий с обработкой ошибок кодировки
            def safe_get_text(text, default=''):
                if text is None:
                    return default
                try:
                    if isinstance(text, str):
                        # Убираем проблемные Unicode символы
                        cleaned_text = text.encode('utf-8', errors='ignore').decode('utf-8')
                        # Убираем специальные символы, которые могут вызвать проблемы с кодировкой
                        import unicodedata
                        cleaned_text = unicodedata.normalize('NFKC', cleaned_text)
                        return cleaned_text
                    return str(text)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    return default

            # Безопасное получение года
            def safe_get_year(year_data, default=None):
                if year_data is None:
                    return default
                try:
                    if isinstance(year_data, (str, int)):
                        year = int(year_data)
                        return year if 1900 <= year <= 2030 else default
                    return default
                except (ValueError, TypeError):
                    return default

            return {
                'id': data.get('id') or data.get('shikimori_id'),
                'shikimori_id': data.get('shikimori_id'),
                'title_ru': safe_get_text(data.get('russian') or data.get('title') or data.get('name')),
                'title_en': safe_get_text(data.get('english') or data.get('title') or data.get('name')),
                'title_jp': safe_get_text(data.get('japanese') or data.get('original_title')),
                'description': safe_get_text(data.get('description', '')),
                'year': safe_get_year(data.get('year')),
                'status': safe_get_text(data.get('status', 'finished')),
                'kind': self._normalize_kind(data.get('type', 'tv')),
                'episodes': data.get('episodes') or data.get('series_count'),
                'score': data.get('score') or data.get('kinopoisk_rating'),
                'poster_url': data.get('poster') or data.get('image') or '',
                'genres': self._safe_get_list(data.get('genres', [])),
                'studios': self._safe_get_list(data.get('studios', [])),
                'raw': data
            }
        except Exception as e:
            logger.warning(f"Ошибка нормализации данных Kodik: {e}")
            return {
                'id': data.get('id'),
                'title_ru': 'Без названия',
                'title_en': '',
                'title_jp': '',
                'description': '',
                'year': None,
                'status': 'finished',
                'kind': 'tv',
                'episodes': None,
                'score': None,
                'poster_url': '',
                'genres': [],
                'studios': [],
                'raw': data
            }
    
    def _normalize_kind(self, kind: str) -> str:
        """Нормализация типа аниме"""
        kind_mapping = {
            'tv': 'tv',
            'movie': 'movie',
            'ova': 'ova',
            'ona': 'ona',
            'special': 'special',
            'music': 'music'
        }
        return kind_mapping.get(kind, 'tv')
    
    def _safe_get_list(self, data_list):
        """Безопасное получение списка данных"""
        if not data_list:
            return []
        
        result = []
        for item in data_list:
            if isinstance(item, dict):
                result.append(item.get('name') or item.get('title') or str(item))
            elif isinstance(item, str):
                result.append(item)
            else:
                result.append(str(item))
        return result
    
    def _merge_related_anime(self, anime_list: List[Dict]) -> List[Dict]:
        """Объединение связанных аниме (сериалы, фильмы, OVA) в одну карточку"""
        try:
            # Группируем аниме по базовому названию
            franchise_groups = {}
            
            for anime in anime_list:
                # Извлекаем базовое название (убираем номера сезонов, "фильм", "OVA" и т.д.)
                base_title = self._extract_base_title(anime.get('title_ru', '') or anime.get('title_en', ''))
                
                if base_title not in franchise_groups:
                    franchise_groups[base_title] = []
                
                franchise_groups[base_title].append(anime)
            
            merged_anime = []
            
            for base_title, franchise_anime in franchise_groups.items():
                if len(franchise_anime) == 1:
                    # Одно аниме в группе
                    merged_anime.append(franchise_anime[0])
                else:
                    # Несколько аниме - объединяем в одну карточку
                    merged = self._merge_franchise_anime(franchise_anime)
                    merged_anime.append(merged)
            
            return merged_anime
            
        except Exception as e:
            logger.error(f"Ошибка объединения аниме: {e}")
            return anime_list
    
    def _extract_base_title(self, title: str) -> str:
        """Извлекает базовое название аниме, убирая номера сезонов, "фильм", OVA и т.д."""
        if not title:
            return ''
        
        import re
        
        # Убираем номера сезонов (ТВ-1, [ТВ-1], сезон 1, и т.д.)
        title = re.sub(r'\s*[\[\(]?ТВ[-\s]*\d+[\)\]]?', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*сезон\s*\d+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*season\s*\d+', '', title, flags=re.IGNORECASE)
        
        # Убираем "фильм", "movie", "film"
        title = re.sub(r'\s*[\[\(]?фильм\s*\d*[\)\]]?', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*movie\s*\d*', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*film\s*\d*', '', title, flags=re.IGNORECASE)
        
        # Убираем "OVA", "OVA-\d+"
        title = re.sub(r'\s*OVA[-\s]*\d*', '', title, flags=re.IGNORECASE)
        
        # Убираем специальные эпизоды
        title = re.sub(r'\s*спецвыпуск', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*special', '', title, flags=re.IGNORECASE)
        
        # Убираем номера в конце
        title = re.sub(r'\s*\d+$', '', title).strip()
        
        return title.strip()
    
    def _merge_franchise_anime(self, franchise_anime: List[Dict]) -> Dict:
        """Объединяет несколько аниме франшизы в одну карточку"""
        try:
            # Берем основное аниме (обычно TV сериал)
            main_anime = None
            movies = []
            ovas = []
            
            for anime in franchise_anime:
                kind = anime.get('kind', '').lower()
                title = anime.get('title_ru', '') or anime.get('title_en', '')
                
                if 'tv' in kind or 'сериал' in title.lower():
                    anime_episodes = anime.get('episodes') if anime.get('episodes') is not None else 0
                    main_episodes = main_anime.get('episodes') if main_anime and main_anime.get('episodes') is not None else 0
                    if not main_anime or anime_episodes > main_episodes:
                        main_anime = anime
                elif 'movie' in kind or 'фильм' in title.lower():
                    movies.append(anime)
                elif 'ova' in kind or 'ova' in title.lower():
                    ovas.append(anime)
                else:
                    # Если не определили тип, считаем дополнительным
                    if not main_anime:
                        main_anime = anime
            
            if not main_anime:
                main_anime = franchise_anime[0]
            
            # Объединяем информацию
            merged = main_anime.copy()
            
            # Добавляем информацию о фильмах и OVA
            if movies:
                movie_titles = [m.get('title_ru', '') or m.get('title_en', '') for m in movies]
                merged['movies'] = movie_titles
                merged['movie_count'] = len(movies)
            
            if ovas:
                ova_titles = [o.get('title_ru', '') or o.get('title_en', '') for o in ovas]
                merged['ovas'] = ova_titles
                merged['ova_count'] = len(ovas)
            
            # Объединяем постеры (берем лучший)
            posters = [a.get('poster_url') for a in franchise_anime if a.get('poster_url')]
            if posters:
                merged['poster_url'] = posters[0]  # Берем первый доступный
            
            # Объединяем описания
            descriptions = [a.get('description', '') for a in franchise_anime if a.get('description')]
            if descriptions:
                merged['description'] = max(descriptions, key=len)  # Берем самое подробное
            
            # Обновляем тип
            merged['kind'] = 'franchise'
            merged['total_items'] = len(franchise_anime)
            
            return merged
            
        except Exception as e:
            logger.error(f"Ошибка объединения франшизы: {e}")
            return franchise_anime[0] if franchise_anime else {}