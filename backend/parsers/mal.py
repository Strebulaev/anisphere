import requests
import time
import pandas as pd
import json
import os
from typing import Dict, List, Optional
from .base import BaseAnimeParser

class MalParser(BaseAnimeParser):
    """Парсер MyAnimeList с поддержкой PKCE"""
    
    BASE_URL = "https://api.myanimelist.net/v2"
    
    def __init__(self, access_token: str = None):
        super().__init__()
        self.access_token = access_token
        if access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
    
    def set_access_token(self, access_token: str):
        """Установка нового токена доступа"""
        self.access_token = access_token
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}"
        })
    
    def get_all_anime_mal(self, target: int = 100000) -> List[Dict]:
        """Получение всех аниме с MyAnimeList с автоматической остановкой"""
        if not self.access_token:
            raise ValueError("Требуется access_token для работы с MyAnimeList API")
        
        print(f"Загрузка {target} аниме с MyAnimeList...")
        
        # Проверяем существующие данные
        offset = self._get_last_offset()
        anime_data = []
        error_count = 0
        max_errors = 15
        
        while len(anime_data) < target and error_count < max_errors:
            url = f"{self.BASE_URL}/anime?offset={offset}&limit=50&fields=id,title,main_picture,alternative_titles,start_date,end_date,mean,rank,popularity,num_list_users,num_scoring_users,status,genres,num_episodes,start_season,broadcast,source,average_episode_duration,rating"
            
            try:
                print(f"Загрузка с offset {offset}...")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    anime_list = data.get('data', [])
                    
                    if not anime_list:
                        print("Данные закончились.")
                        break
                    
                    for anime_info in anime_list:
                        if len(anime_data) >= target:
                            break
                            
                        node = anime_info.get('node', {})
                        anime_item = self._normalize_mal_data(node)
                        if anime_item:
                            anime_data.append(anime_item)
                    
                    error_count = 0  # Сброс счетчика ошибок
                    print(f"Загружено: {len(anime_data)}/{target}")
                    
                elif response.status_code == 401:
                    print("Токен истек. Остановите процесс и обновите токен.")
                    break
                elif response.status_code == 404:
                    error_count += 1
                    print(f"Ошибка 404 на offset {offset}. Ошибок: {error_count}")
                    
                else:
                    print(f"Ошибка {response.status_code} на offset {offset}")
                    time.sleep(2)
                
            except Exception as e:
                print(f"Ошибка при обработке offset {offset}: {e}")
                error_count += 1
                time.sleep(3)
            
            # Сохраняем промежуточные результаты
            if len(anime_data) % 500 == 0:
                self._save_intermediate_data(anime_data)
            
            time.sleep(1)  # Задержка между запросами
            offset += 50
            
            if error_count >= max_errors:
                print(f"Превышено максимальное количество ошибок. Завершаем.")
                break
        
        # Финальное сохранение
        self._save_final_data(anime_data)
        return anime_data
    
    def _get_last_offset(self) -> int:
        """Получение последнего offset из сохраненных данных"""
        csv_file = 'anime_data_mal.csv'
        json_file = 'anime_data_mal.json'
        
        if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
            try:
                existing_data = pd.read_csv(csv_file)
                last_offset = len(existing_data)
                print(f"Продолжаем с позиции {last_offset}")
                return last_offset
            except:
                return 0
        elif os.path.exists(json_file) and os.path.getsize(json_file) > 0:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                last_offset = len(existing_data)
                print(f"Продолжаем с позиции {last_offset}")
                return last_offset
            except:
                return 0
        
        return 0
    
    def _normalize_mal_data(self, node: Dict) -> Optional[Dict]:
        """Нормализация данных MyAnimeList"""
        try:
            # Основная информация
            title_ru = ''
            title_en = ''
            title_jp = ''
            
            # Обработка названий
            alternative_titles = node.get('alternative_titles', {})
            
            # Русское название (если есть)
            if 'ru' in alternative_titles:
                title_ru = alternative_titles['ru']
            elif 'ja' in alternative_titles:
                title_ru = alternative_titles['ja']
            
            # Английское название
            if 'en' in alternative_titles:
                title_en = alternative_titles['en']
            
            # Японское название
            if 'ja' in alternative_titles:
                title_jp = alternative_titles['ja']
            
            # Основное название
            main_title = node.get('title', '')
            if not title_ru:
                title_ru = main_title
            if not title_en:
                title_en = main_title
            
            # Постер
            poster_url = ''
            main_picture = node.get('main_picture', {})
            if main_picture.get('large'):
                poster_url = main_picture['large']
            elif main_picture.get('medium'):
                poster_url = main_picture['medium']
            
            # Год
            year = None
            start_date = node.get('start_date', '')
            if start_date:
                try:
                    year = int(start_date.split('-')[0])
                except:
                    pass
            
            # Статус
            status_map = {
                'finished_airing': 'finished',
                'currently_airing': 'ongoing',
                'not_yet_aired': 'announced'
            }
            status = status_map.get(node.get('status'), 'finished')
            
            # Жанры
            genres = []
            for genre in node.get('genres', []):
                if genre.get('name'):
                    genres.append({'name': genre['name']})
            
            return {
                'id': node.get('id'),
                'title_ru': title_ru,
                'title_en': title_en,
                'title_jp': title_jp,
                'description': '',  # MAL API не возвращает описание в этом запросе
                'poster_url': poster_url,
                'year': year,
                'status': status,
                'episodes': node.get('num_episodes'),
                'score': node.get('mean'),
                'rank': node.get('rank'),
                'popularity': node.get('popularity'),
                'genres': genres,
                'studios': [],  # Нужно отдельный запрос
                'screenshots': [],
                'source': 'mal',
                'raw': node
            }
            
        except Exception as e:
            print(f"Ошибка нормализации данных: {e}")
            return None
    
    def _save_intermediate_data(self, anime_data: List[Dict]):
        """Сохранение промежуточных данных"""
        try:
            # CSV
            df = pd.DataFrame(anime_data)
            df.to_csv('anime_data_mal.csv', index=False, encoding='utf-8')
            
            # JSON
            with open('anime_data_mal.json', 'w', encoding='utf-8') as f:
                json.dump(anime_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Ошибка сохранения промежуточных данных: {e}")
    
    def _save_final_data(self, anime_data: List[Dict]):
        """Финальное сохранение данных"""
        try:
            print(f"Сохранение {len(anime_data)} записей...")
            
            # CSV
            df = pd.DataFrame(anime_data)
            df.to_csv('anime_data_mal.csv', index=False, encoding='utf-8')
            
            # JSON
            with open('anime_data_mal.json', 'w', encoding='utf-8') as f:
                json.dump(anime_data, f, ensure_ascii=False, indent=2)
            
            print("Данные сохранены в 'anime_data_mal.csv' и 'anime_data_mal.json'")
            
        except Exception as e:
            print(f"Ошибка финального сохранения: {e}")
    
    def search_anime_mal(self, query: str, limit: int = 50) -> List[Dict]:
        """Поиск аниме в MyAnimeList"""
        if not self.access_token:
            raise ValueError("Требуется access_token для работы с MyAnimeList API")
        
        url = f"{self.BASE_URL}/anime?q={query}&limit={limit}&fields=id,title,main_picture,alternative_titles,start_date,end_date,mean,genres,status,num_episodes"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            anime_list = []
            
            for anime_info in data.get('data', []):
                node = anime_info.get('node', {})
                normalized = self._normalize_mal_data(node)
                if normalized:
                    anime_list.append(normalized)
            
            return anime_list
            
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            return []
    
    def get_anime_by_id_mal(self, mal_id: int) -> Optional[Dict]:
        """Получение аниме по ID MyAnimeList"""
        if not self.access_token:
            raise ValueError("Требуется access_token для работы с MyAnimeList API")
        
        url = f"{self.BASE_URL}/anime/{mal_id}?fields=id,title,main_picture,alternative_titles,start_date,end_date,mean,rank,popularity,num_list_users,num_scoring_users,status,genres,num_episodes,start_season,broadcast,source,average_episode_duration,rating,synopsis"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            node = response.json()
            return self._normalize_mal_data_with_synopsis(node)
            
        except Exception as e:
            print(f"Ошибка получения аниме {mal_id}: {e}")
            return None
    
    def _normalize_mal_data_with_synopsis(self, node: Dict) -> Optional[Dict]:
        """Нормализация данных с описанием"""
        normalized = self._normalize_mal_data(node)
        if normalized and node.get('synopsis'):
            normalized['description'] = node['synopsis']
        return normalized