import requests
import pandas as pd
import json
import time
import os
import math
import random
from urllib.parse import urlencode

# URL API Shikimori для пакетного получения данных
BASE_URL = "https://shikimori.one/api"

# Улучшенные заголовки для имитации браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

class ShikimoriCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.max_retries = 3
        self.base_delay = 2
        
    def replace_nan(self, value):
        """Замена NaN значений на None"""
        if isinstance(value, float) and math.isnan(value):
            return None
        return value
    
    def get_anime_page(self, page: int, limit: int = 50) -> list:
        """Получение одной страницы аниме"""
        url = f"{BASE_URL}/animes"
        params = {
            "order": "popularity",
            "page": page,
            "limit": limit
        }
        
        for attempt in range(self.max_retries):
            try:
                print(f"Запрос страницы {page} (попытка {attempt + 1})...")
                
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=30,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    anime_list = response.json()
                    print(f"✓ Страница {page}: получено {len(anime_list)} аниме")
                    return anime_list
                    
                elif response.status_code == 429:
                    # Превышен лимит запросов
                    wait_time = 60 * (attempt + 1)
                    print(f"⚠ Превышен лимит запросов. Ожидание {wait_time} секунд...")
                    time.sleep(wait_time)
                    continue
                    
                elif response.status_code == 404:
                    print(f"⚠ Страница {page} не найдена (404)")
                    return []
                    
                else:
                    print(f"⚠ Неожиданный статус {response.status_code} на странице {page}")
                    
            except requests.exceptions.Timeout:
                print(f"⚠ Таймаут на странице {page} (попытка {attempt + 1})")
                
            except requests.exceptions.ConnectionError:
                print(f"⚠ Ошибка соединения на странице {page} (попытка {attempt + 1})")
                
            except Exception as e:
                print(f"⚠ Ошибка на странице {page}: {e}")
            
            # Задержка перед повторной попыткой
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt) + random.uniform(0, 2)
                print(f"Ожидание {delay:.1f} секунд перед повтором...")
                time.sleep(delay)
        
        print(f"✗ Не удалось получить страницу {page} после {self.max_retries} попыток")
        return []
    
    def collect_anime_data(self, total_pages: int = 100):
        """Сбор данных о аниме"""
        # Проверка существующих данных
        if os.path.exists('anime_data.csv') and os.path.getsize('anime_data.csv') > 0:
            try:
                existing_data = pd.read_csv('anime_data.csv')
                anime_data = existing_data.to_dict('records')
                last_page = (len(existing_data) // 50) + 1
                print(f"📂 Найдены существующие данные: {len(anime_data)} записей")
                print(f"📍 Продолжаем с страницы {last_page}")
            except Exception as e:
                print(f"⚠ Ошибка чтения файла: {e}")
                anime_data = []
                last_page = 1
        else:
            anime_data = []
            last_page = 1
        
        print(f"🎯 Цель: собрать данные с {last_page} по {total_pages} страницу")
        print("=" * 60)
        
        # Сбор данных
        for page in range(last_page, total_pages + 1):
            anime_list = self.get_anime_page(page)
            
            if anime_list:
                for anime_info in anime_list:
                    anime_data.append({
                        'id': self.replace_nan(anime_info.get('id')),
                        'name': self.replace_nan(anime_info.get('name')),
                        'russian': self.replace_nan(anime_info.get('russian', '')),
                        'url': self.replace_nan(anime_info.get('url')),
                        'kind': self.replace_nan(anime_info.get('kind')),
                        'score': self.replace_nan(anime_info.get('score')),
                        'status': self.replace_nan(anime_info.get('status')),
                        'episodes': self.replace_nan(anime_info.get('episodes')),
                        'episodes_aired': self.replace_nan(anime_info.get('episodes_aired', 0)),
                        'aired_on': self.replace_nan(anime_info.get('aired_on')),
                        'released_on': self.replace_nan(anime_info.get('released_on'))
                    })
                
                # Промежуточное сохранение каждые 10 страниц
                if page % 10 == 0:
                    self.save_data(anime_data)
                    print(f"💾 Промежуточное сохранение: {len(anime_data)} записей")
            
            # Задержка между страницами (случайная для имитации человеческого поведения)
            if page < total_pages:
                delay = self.base_delay + random.uniform(0, 2)
                print(f"⏳ Ожидание {delay:.1f} секунд до следующей страницы...")
                time.sleep(delay)
        
        # Финальное сохранение
        self.save_data(anime_data)
        print("=" * 60)
        print(f"✅ Сбор завершен! Всего собрано: {len(anime_data)} аниме")
        return anime_data
    
    def save_data(self, anime_data: list):
        """Сохранение данных в файлы"""
        if len(anime_data) == 0:
            return
        
        try:
            # Сохранение в CSV
            df = pd.DataFrame(anime_data)
            df.to_csv('anime_data.csv', index=False, encoding='utf-8')
            
            # Сохранение в JSON
            with open('anime_data.json', 'w', encoding='utf-8') as json_file:
                json.dump(anime_data, json_file, ensure_ascii=False, indent=2)
                
            print(f"💾 Данные сохранены в anime_data.csv и anime_data.json")
            
        except Exception as e:
            print(f"⚠ Ошибка сохранения: {e}")

def main():
    print("🎌 Shikimori Anime Data Collector")
    print("=" * 60)
    
    collector = ShikimoriCollector()
    
    # Ввод количества страниц
    try:
        total_pages = int(input("Введите количество страниц для сбора (рекомендуется 100-200): ") or "100")
        if total_pages <= 0:
            print("❌ Количество страниц должно быть положительным числом")
            return
    except ValueError:
        print("❌ Неверный ввод. Используется значение по умолчанию: 100 страниц")
        total_pages = 100
    
    start_time = time.time()
    
    try:
        anime_data = collector.collect_anime_data(total_pages)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Время выполнения: {duration:.1f} секунд")
        print(f"📊 Средняя скорость: {len(anime_data) / (duration / 60):.1f} аниме/минуту")
        
    except KeyboardInterrupt:
        print("\n⚠️ Сбор прерван пользователем")
        collector.save_data(collector.anime_data if hasattr(collector, 'anime_data') else [])
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        collector.save_data([])

if __name__ == "__main__":
    main()