#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import django
import requests
import time
import re
import argparse
import json
import concurrent.futures
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import random
import logging

# Исправляем кодировку для Windows
if sys.platform == "win32":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройка логирования без emoji для Windows
class NoEmojiFormatter(logging.Formatter):
    def format(self, record):
        # Убираем emoji для совместимости с Windows
        emoji_map = {
            '🚀': '[ROCKET]',
            '📦': '[BOX]',
            '🔍': '[MAG]',
            '🔧': '[WRENCH]',
            '💾': '[DISK]',
            '✅': '[OK]',
            '❌': '[ERR]',
            '⚠️': '[WARN]',
            '⏭️': '[SKIP]',
            '🔄': '[UPDATE]',
            '📊': '[CHART]',
            '📝': '[NOTE]',
            '🎉': '[PARTY]',
            '⏹️': '[STOP]',
            '📂': '[FOLDER]',
            '📄': '[PAGE]',
            '📭': '[MAILBOX]',
            '⏳': '[CLOCK]',
            '🔌': '[PLUG]',
            '⏱️': '[TIMER]',
            '🔥': '[FIRE]',
            '⭐': '[STAR]'
        }
        
        message = record.getMessage()
        for emoji, replacement in emoji_map.items():
            message = message.replace(emoji, replacement)
        
        record.msg = message
        return super().format(record)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shikimori_parser.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Применяем кастомный форматтер
for handler in logger.handlers:
    handler.setFormatter(NoEmojiFormatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime

class ShikimoriParser:
    def __init__(self, max_anime=None, skip_images=False, fast_mode=False, max_workers=5):
        self.base_url = "https://shikimori.one"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.max_anime = max_anime
        self.skip_images = skip_images
        self.fast_mode = fast_mode
        self.max_workers = max_workers
        self.total_saved = 0
        self.processed_count = 0
        self.failed_urls = []
        
        # Создаем директории для сохранения изображений
        os.makedirs('backend/media/posters', exist_ok=True)
        os.makedirs('backend/media/screenshots', exist_ok=True)
        
        logger.info(f"Initialized Shikimori Parser with {max_workers} workers")
    
    def download_image(self, url, filename, folder='posters'):
        """Скачивает изображение и сохраняет его в файл"""
        if self.skip_images or not url:
            return None
        
        try:
            if not url.startswith('http'):
                url = urljoin(self.base_url, url)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            filepath = f'backend/media/{folder}/{filename}'
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f'{folder}/{filename}'
        except Exception as e:
            logger.warning(f'Error downloading image {url}: {str(e)[:100]}')
            return None
    
    def get_soup(self, url, params=None):
        """Получает HTML страницу и возвращает BeautifulSoup объект"""
        try:
            if params:
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.get(url, timeout=30)
            
            response.raise_for_status()
            
            # Проверяем кодировку
            if response.encoding is None:
                response.encoding = 'utf-8'
            
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f'Error fetching {url}: {str(e)[:100]}')
            return None
    
    def get_all_anime_urls(self):
        """Получает ВСЕ ссылки на аниме с Shikimori"""
        logger.info("[ROCKET] Starting to collect ALL anime URLs from Shikimori...")
        
        all_urls = set()
        base_list_url = f"{self.base_url}/animes"
        
        # Парсим по различным фильтрам чтобы получить максимум аниме
        filters_combinations = [
            # По статусам
            {'status': 'released', 'order': 'popularity'},
            {'status': 'ongoing', 'order': 'popularity'},
            {'status': 'anons', 'order': 'popularity'},
            # По типам
            {'kind': 'tv', 'order': 'popularity'},
            {'kind': 'movie', 'order': 'popularity'},
            {'kind': 'ova', 'order': 'popularity'},
            {'kind': 'ona', 'order': 'popularity'},
            {'kind': 'special', 'order': 'popularity'},
            # По рейтингу
            {'rating': 'g', 'order': 'popularity'},
            {'rating': 'pg', 'order': 'popularity'},
            {'rating': 'pg_13', 'order': 'popularity'},
            {'rating': 'r', 'order': 'popularity'},
            {'rating': 'r_plus', 'order': 'popularity'},
            # По жанрам (популярные жанры)
            {'genre': '1', 'order': 'popularity'},  # Action
            {'genre': '2', 'order': 'popularity'},  # Adventure
            {'genre': '4', 'order': 'popularity'},  # Comedy
            {'genre': '8', 'order': 'popularity'},  # Drama
            {'genre': '10', 'order': 'popularity'},  # Fantasy
            {'genre': '22', 'order': 'popularity'},  # Romance
            {'genre': '24', 'order': 'popularity'},  # Sci-Fi
            {'genre': '27', 'order': 'popularity'},  # Shounen
            {'genre': '28', 'order': 'popularity'},  # Shoujo
            {'genre': '42', 'order': 'popularity'},  # Seinen
            {'genre': '43', 'order': 'popularity'},  # Josei
            # По годам (последние 20 лет для теста)
            {'season': '2024_2023', 'order': 'popularity'},
            {'season': '2022_2021', 'order': 'popularity'},
            {'season': '2020_2019', 'order': 'popularity'},
            {'season': '2018_2017', 'order': 'popularity'},
            {'season': '2016_2015', 'order': 'popularity'},
            {'season': '2014_2013', 'order': 'popularity'},
            {'season': '2012_2011', 'order': 'popularity'},
            {'season': '2010_2009', 'order': 'popularity'},
            {'season': '2008_2007', 'order': 'popularity'},
        ]
        
        for filters in filters_combinations:
            if self.max_anime and len(all_urls) >= self.max_anime:
                logger.info(f"[OK] Reached max limit: {self.max_anime}")
                break
            
            logger.info(f"[FOLDER] Parsing with filters: {filters}")
            
            page = 1
            max_pages = 3  # Ограничиваем страницы для теста
            
            while page <= max_pages:
                if self.max_anime and len(all_urls) >= self.max_anime:
                    break
                
                logger.info(f"  [PAGE] Page {page}...")
                
                params = dict(filters)
                params['page'] = page
                
                soup = self.get_soup(base_list_url, params)
                if not soup:
                    logger.warning(f"    Failed to get page {page}")
                    break
                
                # Находим все ссылки на аниме
                anime_links = []
                # Попробуем разные селекторы
                selectors = [
                    'a.cover',
                    'a.catalog-tooltip',
                    'a.title',
                    '.c-anime',
                    '.b-catalog_entry',
                    '.b-ajax',
                    'article a'
                ]
                
                for selector in selectors:
                    links = soup.select(selector)
                    anime_links.extend(links)
                
                new_urls = 0
                for link in anime_links:
                    href = link.get('href', '')
                    if href and '/animes/' in href and 'z' not in href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in all_urls:
                            all_urls.add(full_url)
                            new_urls += 1
                
                logger.info(f"    Found {new_urls} new anime (total: {len(all_urls)})")
                
                # Проверяем есть ли следующая страница
                next_page = soup.select_one('a.next_page, a.page-link[rel="next"], .next, .b-link[rel="next"]')
                if not next_page or new_urls == 0:
                    logger.info(f"    No more pages for this filter")
                    break
                
                page += 1
                
                # Задержка между страницами
                if not self.fast_mode:
                    time.sleep(random.uniform(2, 4))
                else:
                    time.sleep(random.uniform(0.5, 1))
        
        # Если собрали мало URL, пробуем альтернативный метод
        if len(all_urls) < 100:
            logger.info("[MAG] Searching additional anime through alternative methods...")
            
            # Метод: Парсим первые N страниц общего каталога
            for page in range(1, 6):
                if self.max_anime and len(all_urls) >= self.max_anime:
                    break
                
                logger.info(f"  [PAGE] General catalog page {page}")
                soup = self.get_soup(f"{base_list_url}?page={page}")
                
                if soup:
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        if '/animes/' in href and href.count('/') == 3 and 'z' not in href:
                            full_url = urljoin(self.base_url, href)
                            all_urls.add(full_url)
                
                time.sleep(1)
        
        logger.info(f"[OK] Total unique anime URLs collected: {len(all_urls)}")
        return list(all_urls)
    
    def parse_anime_page(self, url):
        """Парсит страницу одного аниме"""
        try:
            logger.info(f"Parsing: {url}")
            
            soup = self.get_soup(url)
            if not soup:
                self.failed_urls.append(url)
                return None
            
            anime_data = {}
            
            # Извлекаем ID из URL
            mal_id_match = re.search(r'/animes/(\d+)', url)
            mal_id = mal_id_match.group(1) if mal_id_match else None
            
            # Основное название (русское)
            title_ru = ''
            
            # Попробуем разные селекторы для заголовка
            title_selectors = [
                'h1',
                'header h1',
                '.catalog-head h1',
                '.b-anime_status_tag + h1',
                '.headline h1',
                '.b-entry > h1',
                '[itemprop="name"]',
                '.name-ru',
                '.names .name'
            ]
            
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    title_ru = elem.get_text(strip=True)
                    break
            
            # Если не нашли русское название, берем из URL или мета-тегов
            if not title_ru:
                # Пробуем получить из meta тега
                meta_title = soup.select_one('meta[property="og:title"], meta[name="twitter:title"]')
                if meta_title:
                    title_ru = meta_title.get('content', '').split(' / ')[0].strip()
            
            # Оригинальное название
            title_en = title_ru  # по умолчанию
            
            # Пробуем найти английское название
            en_selectors = [
                '.b-anime_status_tag + .line-container .line',
                '.line-container .line',
                '.name-en',
                '.names .name:last-child',
                '[itemprop="alternativeHeadline"]',
                '.b-entry-info .line:contains("англ")'
            ]
            
            for selector in en_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    title_en = elem.get_text(strip=True)
                    break
            
            # Год
            year = None
            year_pattern = re.compile(r'\b(19\d{2}|20\d{2})\b')
            
            # Ищем год в разных местах
            year_sources = [
                soup.get_text(),
                soup.select_one('.b-anime_status_tag + .line-container').get_text() if soup.select_one('.b-anime_status_tag + .line-container') else '',
                soup.select_one('.year').get_text() if soup.select_one('.year') else '',
                soup.select_one('.b-anime_info').get_text() if soup.select_one('.b-anime_info') else ''
            ]
            
            for source in year_sources:
                match = year_pattern.search(source)
                if match:
                    year = int(match.group(1))
                    break
            
            # Описание
            description = ''
            desc_selectors = [
                '.b-text_with_paragraphs',
                '.description',
                '.b-entry-info p',
                '[itemprop="description"]',
                '.text'
            ]
            
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    description = elem.get_text(strip=True)
                    break
            
            # Рейтинг (score)
            score = None
            score_selectors = [
                '.score-value',
                '.b-score__value',
                '[itemprop="ratingValue"]',
                '.score',
                '.rating-value'
            ]
            
            for selector in score_selectors:
                elem = soup.select_one(selector)
                if elem and elem.get_text(strip=True):
                    try:
                        score_text = elem.get_text(strip=True).replace(',', '.')
                        score = float(score_text)
                        break
                    except:
                        pass
            
            # Количество эпизодов
            episodes = None
            ep_selectors = [
                '.episodes',
                '.b-anime_info .key:contains("Эпизодов") + .value',
                '[itemprop="numberOfEpisodes"]',
                '.episode-count'
            ]
            
            for selector in ep_selectors:
                elem = soup.select_one(selector)
                if elem:
                    ep_text = elem.get_text(strip=True)
                    if ep_text.isdigit():
                        episodes = int(ep_text)
                        break
                    # Пробуем извлечь число из текста
                    ep_match = re.search(r'(\d+)', ep_text)
                    if ep_match:
                        episodes = int(ep_match.group(1))
                        break
            
            # Тип (TV, Movie, OVA и т.д.)
            kind = 'tv'  # по умолчанию
            
            # Ищем информацию о типе в разных местах
            kind_text = ''
            kind_selectors = [
                '.kind',
                '.b-anime_info .key:contains("Тип") + .value',
                '[itemprop="genre"]',
                '.type'
            ]
            
            for selector in kind_selectors:
                elem = soup.select_one(selector)
                if elem:
                    kind_text = elem.get_text(strip=True).lower()
                    break
            
            kind_map = {
                'tv': 'tv',
                'тв': 'tv',
                'сериал': 'tv',
                'movie': 'movie',
                'фильм': 'movie',
                'ova': 'ova',
                'она': 'ona',
                'special': 'special',
                'спешл': 'special'
            }
            
            for key, value in kind_map.items():
                if key in kind_text:
                    kind = value
                    break
            
            # Статус
            status = 'finished'  # по умолчанию
            status_text = ''
            status_selectors = [
                '.status',
                '.b-anime_info .key:contains("Статус") + .value',
                '.anime-status'
            ]
            
            for selector in status_selectors:
                elem = soup.select_one(selector)
                if elem:
                    status_text = elem.get_text(strip=True).lower()
                    break
            
            status_map = {
                'вышел': 'finished',
                'завершен': 'finished',
                'онгоинг': 'ongoing',
                'выходит': 'ongoing',
                'анонс': 'announced',
                'анонсировано': 'announced'
            }
            
            for key, value in status_map.items():
                if key in status_text:
                    status = value
                    break
            
            # Жанры
            genres = []
            genre_selectors = [
                '.genre',
                '.b-anime_info .key:contains("Жанр") + .value a',
                '.tags a',
                '[itemprop="genre"] a',
                '.genre-list a'
            ]
            
            for selector in genre_selectors:
                elems = soup.select(selector)
                for elem in elems:
                    genre = elem.get_text(strip=True)
                    if genre and genre not in genres:
                        genres.append(genre)
            
            # Студии
            studios = []
            studio_selectors = [
                '.studio',
                '.b-anime_info .key:contains("Студия") + .value a',
                '[itemprop="productionCompany"]',
                '.studios a'
            ]
            
            for selector in studio_selectors:
                elems = soup.select(selector)
                for elem in elems:
                    studio = elem.get_text(strip=True)
                    if studio and studio not in studios:
                        studios.append(studio)
            
            # Постер
            poster_url = None
            poster_selectors = [
                '.c-poster img',
                '.poster img',
                '[itemprop="image"]',
                '.cover img',
                'img.poster'
            ]
            
            for selector in poster_selectors:
                elem = soup.select_one(selector)
                if elem:
                    poster_url = elem.get('src') or elem.get('data-src')
                    if poster_url:
                        if poster_url.startswith('//'):
                            poster_url = 'https:' + poster_url
                        break
            
            # Скриншоты (ограничим 3)
            screenshots = []
            screenshot_selectors = [
                '.screenshots img',
                '.b-screenshots img',
                '[itemprop="screenshot"]',
                '.screenshot'
            ]
            
            for selector in screenshot_selectors:
                elems = soup.select(selector)
                for elem in elems[:3]:  # только первые 3
                    screenshot_url = elem.get('src') or elem.get('data-src')
                    if screenshot_url:
                        if screenshot_url.startswith('//'):
                            screenshot_url = 'https:' + screenshot_url
                        screenshots.append(screenshot_url)
            
            # Создаем имя файла для постера
            poster_filename = None
            if poster_url:
                # Создаем безопасное имя файла
                filename_base = re.sub(r'[^\w\s-]', '', title_ru or title_en or 'unknown').strip()
                filename_base = re.sub(r'[-\s]+', '_', filename_base)
                filename_base = filename_base[:50]  # ограничиваем длину
                poster_filename = f"{filename_base}_{mal_id or 'unknown'}.jpg"
            
            # Скачиваем постер
            poster_file = None
            if not self.skip_images and poster_url and poster_filename:
                poster_file = self.download_image(poster_url, poster_filename, 'posters')
            
            # Скачиваем скриншоты
            screenshot_files = []
            if not self.skip_images and screenshots:
                for i, screenshot_url in enumerate(screenshots[:2]):  # первые 2 скриншота
                    screenshot_filename = f"{filename_base}_{mal_id or 'unknown'}_ss{i+1}.jpg"
                    screenshot_file = self.download_image(screenshot_url, screenshot_filename, 'screenshots')
                    if screenshot_file:
                        screenshot_files.append(screenshot_file)
            
            self.processed_count += 1
            
            return {
                'title_ru': title_ru[:200] or f"Anime {mal_id or 'unknown'}",
                'title_en': title_en[:200] or title_ru[:200],
                'description': description[:2000],
                'year': year,
                'episodes': episodes,
                'score': score,
                'poster_url': poster_url,
                'poster_file': poster_file,
                'screenshot_files': screenshot_files,
                'genres': genres[:10],
                'studios': studios[:5],
                'kind': kind,
                'status': status,
                'source': 'shikimori',
                'mal_id': mal_id,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error parsing {url}: {str(e)[:100]}")
            self.failed_urls.append(url)
            return None
    
    def save_anime(self, anime_data):
        """Сохраняет аниме в базу данных"""
        if not anime_data:
            return False
        
        try:
            title_ru = anime_data['title_ru']
            if not title_ru:
                logger.warning(f"No title for anime: {anime_data.get('url', 'Unknown')}")
                return False
            
            # Проверяем существует ли уже такое аниме по названию
            existing = Anime.objects.filter(title_ru=title_ru).first()
            if existing:
                # Обновляем существующую запись если нужно
                needs_update = False
                
                if not existing.description and anime_data['description']:
                    existing.description = anime_data['description']
                    needs_update = True
                
                if not existing.year and anime_data['year']:
                    existing.year = anime_data['year']
                    needs_update = True
                
                if not existing.episodes and anime_data['episodes']:
                    existing.episodes = anime_data['episodes']
                    needs_update = True
                
                if not existing.score and anime_data['score']:
                    existing.score = anime_data['score']
                    needs_update = True
                
                if not existing.genres and anime_data['genres']:
                    existing.genres = anime_data['genres']
                    needs_update = True
                
                if not existing.studios and anime_data['studios']:
                    existing.studios = anime_data['studios']
                    needs_update = True
                
                if anime_data['poster_file'] and not existing.poster:
                    existing.poster = anime_data['poster_file']
                    needs_update = True
                
                if needs_update:
                    existing.save()
                    self.total_saved += 1
                    logger.info(f"[UPDATE] Updated: {title_ru[:50]}")
                    return True
                else:
                    logger.debug(f"[SKIP] Already exists: {title_ru[:50]}")
                    return False
            
            # Создаем новую запись
            anime = Anime(
                title_ru=title_ru,
                title_en=anime_data['title_en'],
                description=anime_data['description'],
                year=anime_data['year'],
                status=anime_data['status'],
                kind=anime_data['kind'],
                episodes=anime_data['episodes'],
                score=anime_data['score'],
                poster_url=anime_data['poster_url'],
                poster=anime_data['poster_file'],
                genres=anime_data['genres'],
                studios=anime_data['studios'],
                data_source=anime_data['source']
            )
            
            anime.save()
            self.total_saved += 1
            logger.info(f"[DISK] Saved: {title_ru[:50]}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving anime {anime_data.get('title_ru', 'Unknown')}: {str(e)[:100]}")
            return False
    
    def parse_anime_batch(self, urls_batch):
        """Парсит батч аниме"""
        results = []
        for url in urls_batch:
            anime_data = self.parse_anime_page(url)
            if anime_data:
                results.append(anime_data)
            
            # Задержка между запросами
            if not self.fast_mode:
                time.sleep(random.uniform(2, 4))
            else:
                time.sleep(random.uniform(1, 2))
        
        return results
    
    def run_massive_parse(self):
        """Запускает массовый парсинг всех аниме с Shikimori"""
        print("=" * 80)
        print("MASSIVE SHIKIMORI PARSER - ALL ANIME")
        print("=" * 80)
        print(f"Settings: max_anime={self.max_anime or 'unlimited'}, "
              f"skip_images={self.skip_images}, fast_mode={self.fast_mode}")
        print("=" * 80)
        
        start_time = time.time()
        
        # Этап 1: Сбор всех URL аниме
        logger.info("\n[BOX] PHASE 1: Collecting ALL anime URLs")
        logger.info("   (This may take some time to collect URLs)")
        
        all_urls = self.get_all_anime_urls()
        
        if not all_urls:
            logger.error("[ERR] No anime URLs collected!")
            return
        
        logger.info(f"[OK] Collected {len(all_urls)} anime URLs")
        
        # Ограничиваем количество если нужно
        if self.max_anime and len(all_urls) > self.max_anime:
            all_urls = all_urls[:self.max_anime]
            logger.info(f"[WARN] Limited to {self.max_anime} anime")
        
        # Этап 2: Парсинг аниме
        logger.info(f"\n[WRENCH] PHASE 2: Parsing {len(all_urls)} anime pages")
        logger.info(f"   Using {self.max_workers} workers")
        
        batch_size = 20  # Уменьшил для теста
        total_batches = (len(all_urls) + batch_size - 1) // batch_size
        
        all_anime_data = []
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = start_idx + batch_size
            batch_urls = all_urls[start_idx:end_idx]
            
            logger.info(f"\n  Processing batch {batch_num + 1}/{total_batches} "
                       f"({len(batch_urls)} anime)...")
            
            if self.max_workers > 1:
                # Многопоточный парсинг
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, 5)) as executor:
                    future_to_url = {executor.submit(self.parse_anime_page, url): url for url in batch_urls}
                    
                    for future in concurrent.futures.as_completed(future_to_url):
                        url = future_to_url[future]
                        try:
                            anime_data = future.result()
                            if anime_data:
                                all_anime_data.append(anime_data)
                                # Показываем прогресс
                                logger.info(f"    Parsed: {anime_data['title_ru'][:40]}")
                        except Exception as e:
                            logger.error(f"Exception parsing {url}: {str(e)[:100]}")
            else:
                # Однопоточный парсинг
                batch_results = self.parse_anime_batch(batch_urls)
                all_anime_data.extend(batch_results)
                for anime_data in batch_results:
                    if anime_data:
                        logger.info(f"    Parsed: {anime_data['title_ru'][:40]}")
            
            logger.info(f"  [OK] Processed: {len(all_anime_data)}/{len(all_urls)} anime")
            
            # Сохраняем прогресс
            if all_anime_data:
                saved_count = 0
                for anime_data in all_anime_data[-len(batch_urls):]:  # только последний батч
                    if self.save_anime(anime_data):
                        saved_count += 1
                logger.info(f"  [DISK] Saved {saved_count} anime from this batch")
            
            # Задержка между батчами
            if not self.fast_mode and batch_num + 1 < total_batches:
                wait_time = random.uniform(5, 10)
                logger.info(f"  [CLOCK] Waiting {wait_time:.1f} seconds before next batch...")
                time.sleep(wait_time)
        
        # Финальное сохранение
        logger.info(f"\n[DISK] Final save to database...")
        
        final_saved = 0
        for anime_data in all_anime_data:
            if self.save_anime(anime_data):
                final_saved += 1
        
        # Статистика
        elapsed_time = time.time() - start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        print("\n" + "=" * 80)
        print("PARSING COMPLETED!")
        print("=" * 80)
        
        total_in_db = Anime.objects.count()
        
        print(f"\nSTATISTICS:")
        print(f"   Total anime in database: {total_in_db:,}")
        print(f"   Newly saved/updated: {self.total_saved:,}")
        print(f"   Total processed: {self.processed_count:,}")
        print(f"   Failed URLs: {len(self.failed_urls):,}")
        print(f"   Time taken: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Показываем последние добавленные
        print(f"\nRECENTLY ADDED:")
        recent = Anime.objects.order_by('-id')[:10]
        for anime in recent:
            year_display = f"({anime.year})" if anime.year else ""
            genres_count = len(anime.genres) if anime.genres else 0
            title_display = anime.title_ru[:50] if anime.title_ru else "No title"
            print(f"   - {title_display:50} {year_display:8} Genres: {genres_count}")
        
        print("\nMASSIVE PARSING FINISHED!")

def main():
    """Точка входа с аргументами командной строки"""
    parser = argparse.ArgumentParser(description='Massive Shikimori parser for ALL anime')
    parser.add_argument('--max', type=int, default=None, 
                       help='Maximum number of anime to parse (default: unlimited)')
    parser.add_argument('--skip-images', action='store_true',
                       help='Skip downloading images (much faster)')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode (minimum delays, may be blocked)')
    parser.add_argument('--workers', type=int, default=3,
                       help='Number of worker threads (1-10 recommended)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("MASSIVE SHIKIMORI PARSER")
    print("Target: ALL anime (thousands)")
    print("Source: shikimori.one (direct parsing)")
    print("=" * 80)
    
    try:
        parser = ShikimoriParser(
            max_anime=args.max,
            skip_images=args.skip_images,
            fast_mode=args.fast,
            max_workers=args.workers
        )
        parser.run_massive_parse()
    except KeyboardInterrupt:
        print('\n\n[STOP] Parsing interrupted by user.')
        total = Anime.objects.count()
        print(f'   Parsed {total:,} anime before interruption.')
    except Exception as e:
        print(f'\n[ERR] Fatal error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()