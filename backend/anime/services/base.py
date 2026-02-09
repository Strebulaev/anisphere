import abc
import requests
from typing import Dict, List, Optional

class BaseAnimeParser(abc.ABC):
    """Базовый класс для парсеров аниме"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AnimeCore Parser/1.0 (+https://animecore.app)'
        })
    
    @abc.abstractmethod
    def search_anime(self, query: str, limit: int = 20) -> List[Dict]:
        """Поиск аниме по названию"""
        pass
    
    @abc.abstractmethod
    def get_anime_by_id(self, external_id: int) -> Optional[Dict]:
        """Получение аниме по внешнему ID"""
        pass
    
    @abc.abstractmethod
    def get_popular_anime(self, page: int = 1, limit: int = 50) -> List[Dict]:
        """Получение популярных аниме"""
        pass
    
    def normalize_anime_data(self, raw_data: Dict) -> Dict:
        """Нормализация данных в единый формат"""
        # Базовый метод, может быть переопределен
        return {
            'id': raw_data.get('id'),
            'title_ru': raw_data.get('russian') or raw_data.get('name'),
            'title_en': raw_data.get('english') or raw_data.get('name'),
            'description': raw_data.get('description', ''),
            'year': None,
            'status': 'finished',
            'episodes': raw_data.get('episodes'),
            'score': raw_data.get('score'),
            'genres': [],
            'studios': [],
            'raw': raw_data
        }