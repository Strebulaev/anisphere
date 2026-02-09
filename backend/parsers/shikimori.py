import time
import requests
import re
from typing import Dict, List, Optional
from .base import BaseAnimeParser
from .anilist import AnilistParser

class ShikimoriParser(BaseAnimeParser):
    """Улучшенный парсер Shikimori с лучшей обработкой ошибок"""
    
    BASE_URL = "https://shikimori.one/api"
    ANILIST_URL = "https://graphql.anilist.co"
    
    def __init__(self):
        super().__init__()
        # Увеличиваем таймаут и добавляем retry
        self.session.timeout = 30
        self.session.max_retries = 3
        
        # Настройка для больших запросов
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_all_anime_bulk(self, limit: int = 50000) -> List[Dict]:
        """Массовая загрузка всех аниме"""
        print(f"Загрузка {limit} аниме...")
        all_anime = []
        page = 1
        per_page = 50
        
        while len(all_anime) < limit:
            try:
                print(f"Загрузка страницы {page}...")
                url = f"{self.BASE_URL}/animes"
                params = {
                    'page': page,
                    'limit': per_page,
                    'order': 'id'
                }
                
                response = self.session.get(url, params=params, timeout=60)
                response.raise_for_status()
                
                page_data = response.json()
                if not page_data:
                    print("Нет больше данных")
                    break
                
                all_anime.extend(page_data)
                print(f"Загружено: {len(all_anime)}/{limit}")
                
                page += 1
                if page % 10 == 0:
                    time.sleep(2)  # Пауза каждые 10 страниц
                else:
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"Ошибка на странице {page}: {e}")
                if "404" in str(e) or "429" in str(e):
                    print("Превышен лимит запросов, пауза...")
                    time.sleep(30)
                else:
                    time.sleep(5)
                continue
        
        return all_anime[:limit]
    
    def get_anime_by_id_range(self, start_id: int = 1, end_id: int = 100000, limit: int = None) -> List[Dict]:
        """Получение аниме по диапазону ID"""
        results = []
        total_range = end_id - start_id + 1
        if limit:
            total_range = min(total_range, limit)
        
        print(f"Загрузка аниме с ID {start_id} по {start_id + total_range - 1}...")
        
        for current_id in range(start_id, start_id + total_range):
            try:
                anime_data = self.get_anime_by_id(current_id)
                if anime_data:
                    results.append(anime_data)
                
                if len(results) % 50 == 0:
                    print(f"Обработано: {len(results)}/{total_range}")
                
                # Увеличиваем задержку для больших диапазонов
                if current_id % 100 == 0:
                    time.sleep(2)
                elif current_id % 10 == 0:
                    time.sleep(0.5)
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                if "404" not in str(e):
                    print(f"Ошибка ID {current_id}: {e}")
                continue
        
        return results
    
    def search_anime(self, query: str, limit: int = 20) -> List[Dict]:
        """Поиск аниме по названию"""
        try:
            url = f"{self.BASE_URL}/animes"
            params = {'search': query, 'limit': limit}
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            return []
    
    def get_anime_by_id(self, shikimori_id: int) -> Optional[Dict]:
        """Получение аниме по ID"""
        try:
            url = f"{self.BASE_URL}/animes/{shikimori_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return None
    
    def get_popular_anime(self, page: int = 1, limit: int = 50) -> List[Dict]:
        """Получение популярных аниме с пагинацией"""
        try:
            url = f"{self.BASE_URL}/animes"
            params = {
                'page': page,
                'limit': limit,
                'order': 'popularity',
                'status': 'released,ongoing,anons',
                'score': '7'
            }
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения популярных: {e}")
            return []
    
    def get_anime_by_genre(self, genre_id: int, page: int = 1, limit: int = 50) -> List[Dict]:
        """Получение аниме по жанру"""
        try:
            url = f"{self.BASE_URL}/animes"
            params = {
                'page': page,
                'limit': limit,
                'genre': genre_id,
                'order': 'popularity'
            }
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения по жанру {genre_id}: {e}")
            return []
    
    def get_anime_by_year(self, year: int, page: int = 1, limit: int = 50) -> List[Dict]:
        """Получение аниме по году"""
        try:
            url = f"{self.BASE_URL}/animes"
            params = {
                'page': page,
                'limit': limit,
                'season': 'summer,winter,spring,fall',
                'year': year,
                'order': 'popularity'
            }
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения по году {year}: {e}")
            return []
    
    def get_all_genres(self) -> List[Dict]:
        """Получение всех жанров"""
        try:
            url = f"{self.BASE_URL}/genres"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения жанров: {e}")
            return []
    
    def get_anime_by_ids_range(self, start_id: int = 1, end_id: int = 100, limit: int = 50) -> List[Dict]:
        """Получение аниме по диапазону ID (fallback метод)"""
        results = []
        
        for anime_id in range(start_id, min(end_id + 1, start_id + limit)):
            try:
                anime_data = self.get_anime_by_id(anime_id)
                if anime_data:
                    results.append(anime_data)
                time.sleep(0.5)  # Задержка между запросами
            except Exception as e:
                print(f"Ошибка получения ID {anime_id}: {e}")
                continue
                
        return results
    
    def get_random_anime_ids(self, count: int = 50) -> List[int]:
        """Получение случайных ID аниме"""
        # Популярные ID аниме для начала
        popular_ids = [
            1, 20, 1535, 164, 813, 6702, 11061, 9253, 6547, 20507,
            21881, 22319, 23273, 24701, 28223, 30276, 31964, 32935,
            33352, 34321, 34933, 37491, 38000, 39486, 40456, 40748,
            41587, 42938, 44135, 48561, 48607, 48926, 49129, 49596,
            5114, 5081, 47257, 48583, 47917, 49762, 50602, 50631,
            51179, 52034, 16498, 1482, 1735, 263, 19, 21, 32, 48,
            57, 82, 100, 117, 134, 148, 164, 178, 190, 199, 232,
            288, 310, 322, 377, 423, 457, 477, 486, 506, 511, 513,
            533, 578, 590, 618, 654, 693, 707, 759, 810, 820, 851
        ]
        
        # Добавляем случайные ID в диапазоне
        import random
        random_ids = random.sample(range(1000, 30000), count - len(popular_ids))
        
        return popular_ids + random_ids[:count - len(popular_ids)]
    
    def normalize_anime_data(self, raw_data: Dict) -> Dict:
        """Нормализация данных Shikimori"""
        # Обработка постера с fallback
        poster_url = ''
        if raw_data.get('image'):
            if (raw_data['image'].get('original') and
                raw_data['image']['original'] != '/assets/globals/missing_original.jpg'):
                poster_url = f"https://shikimori.one{raw_data['image']['original']}"
            elif raw_data['image'].get('x96'):
                poster_url = f"https://shikimori.one{raw_data['image']['x96']}"
            else:
                # Попробовать получить с Anilist
                title = raw_data.get('russian') or raw_data.get('name') or raw_data.get('english')
                if title:
                    try:
                        anilist_parser = AnilistParser()
                        alt_poster = anilist_parser.get_poster_url(title)
                        if alt_poster:
                            poster_url = alt_poster
                        else:
                            poster_url = '/missing_original.jpg'
                    except:
                        poster_url = '/missing_original.jpg'
                else:
                    poster_url = '/missing_original.jpg'

        normalized = {
            'id': raw_data.get('id'),
            'title_ru': raw_data.get('russian') or raw_data.get('name'),
            'title_en': raw_data.get('english') or raw_data.get('name'),
            'title_jp': raw_data.get('japanese'),
            'description': self._clean_description(raw_data.get('description', '')),
            'poster_url': poster_url,
            'year': raw_data.get('aired_on', '').split('-')[0] if raw_data.get('aired_on') else None,
            'status': self._map_status(raw_data.get('status')),
            'episodes': raw_data.get('episodes'),
            'score': raw_data.get('score'),
            'genres': [{'name': g['russian'] or g['name']} for g in raw_data.get('genres', [])],
            'studios': [s['name'] for s in raw_data.get('studios', [])],
            'screenshots': [{'url': s['original']} for s in raw_data.get('screenshots', [])],
            'raw': raw_data
        }
        
        # Добавляем aired_from если есть
        if raw_data.get('aired_on'):
            normalized['aired_from'] = raw_data['aired_on']
        
        return normalized
    
    def _clean_description(self, description: str) -> str:
        """Очистка описания от BBCode тегов Shikimori"""
        if not description:
            return description

        # Удалить [tag=...] и [/tag]
        # Примеры: [person=62325 dustcell], [character=186854], [/character]
        description = re.sub(r'\[/?\w+(=\w+)?[^\]]*\]', '', description)

        # Удалить лишние пробелы
        description = re.sub(r'\s+', ' ', description).strip()

        return description

    def _map_status(self, status: str) -> str:
        mapping = {'released': 'finished', 'ongoing': 'ongoing', 'anons': 'announced'}
        return mapping.get(status, 'finished')