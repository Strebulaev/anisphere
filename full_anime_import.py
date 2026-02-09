#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import django
import json
import requests
import time
from urllib.parse import urlparse
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from anime.models import Anime

def download_image(url, filename):
    """Скачивает изображение и сохраняет его в файл"""
    if not url:
        return None
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        os.makedirs('backend/media/posters', exist_ok=True)
        filepath = f'backend/media/posters/{filename}'
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return filepath
    except Exception as e:
        print(f'Ошибка скачивания изображения {url}: {e}')
        return None

def clean_filename(title):
    """Очищает название для использования в имени файла"""
    import re
    filename = re.sub(r'[^\w\s-]', '', title).strip()
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename[:50]  # Ограничиваем длину имени файла

def import_from_kodik():
    """Импорт аниме из Kodik"""
    try:
        from anime_parsers_ru import KodikParser
        parser = KodikParser()
        print('Importing from Kodik...')
        
        # Получаем список аниме
        anime_list, next_page_id = parser.get_list(
            limit_per_page=50,
            pages_to_parse=10,  # Больше страниц для большего количества данных
            include_material_data=True,
            only_anime=True
        )
        
        return anime_list
    except Exception as e:
        print(f'❌ Ошибка импорта из Kodik: {e}')
        return []

def import_from_aniboom():
    """Импорт аниме из AniBoom"""
    try:
        from anime_parsers_ru import AniboomParser
        parser = AniboomParser()
        print('Импорт из AniBoom...')
        
        # Популярные аниме для поиска
        popular_anime = [
            "Наруто", "Блич", "Ванпанчмен", "Атака Титанов", "Моя геройская академия",
            "Драконий жнец", "Дракана", "Гинтама", "Хантер хантер", "ДжоДжо",
            "Клинок рассекающий демонов", "Черный клевер", "Фейт/Найт", "Эльфийская песня",
            "Восемьдесят шесть", "О моей наставнице", "Пламенная бригада пожарных",
            "Великий ученик Хикури", "Наруто: Ураганные хроники", "Гактаж",
            "Семья шпиона", "Тетрадь дружбы Нацумэ", "Пророк Амида", "Богиня благодати",
            "Кастлвания", "Барбоскины", "Котобой", "Кухня в Париже", "Человек-бензопила"
        ]
        
        all_anime = []
        for title in popular_anime:
            try:
                print(f'   Поиск: {title}')
                results = parser.search(title)
                for result in results:
                    # Получаем полную информацию об аниме
                    full_info = parser.anime_info(result['link'])
                    if full_info:
                        all_anime.append(full_info)
                    time.sleep(1)  # Задержка между запросами
            except Exception as e:
                print(f'   Ошибка поиска {title}: {e}')
                continue
        
        return all_anime
    except Exception as e:
        print(f'Ошибка импорта из AniBoom: {e}')
        return []

def import_from_shikimori():
    """Импорт аниме из Shikimori"""
    try:
        from anime_parsers_ru import ShikimoriParser
        parser = ShikimoriParser()
        print(' Импорт из Shikimori...')
        
        # Получаем популярные аниме
        anime_list = parser.get_anime_list(
            status=['released', 'ongoing'],
            anime_type=['tv', 'movie', 'ova'],
            page_limit=5,
            sort_by='popularity'
        )
        
        # Дополняем информацией
        enhanced_anime = []
        for anime in anime_list:
            try:
                print(f'   Получение информации: {anime["title"]}')
                info = parser.anime_info(anime['url'])
                additional_info = parser.additional_anime_info(anime['url'])
                
                if info:
                    enhanced_info = {**info, **additional_info}
                    enhanced_anime.append(enhanced_info)
                
                time.sleep(1)  # Задержка между запросами
            except Exception as e:
                print(f'   Ошибка получения информации для {anime["title"]}: {e}')
                enhanced_anime.append(anime)
        
        return enhanced_anime
    except Exception as e:
        print(f'Ошибка импорта из Shikimori: {e}')
        return []

def save_anime_to_db(anime_data, source):
    """Сохраняет аниме в базу данных"""
    try:
        # Извлекаем данные в зависимости от источника
        if source == 'kodik':
            title_ru = anime_data.get('title', '')
            title_en = anime_data.get('material_data', {}).get('english', '') or title_ru
            description = anime_data.get('material_data', {}).get('description', '')
            year = anime_data.get('year')
            if year:
                try:
                    year = int(year)
                except:
                    year = None
            
            episodes = anime_data.get('material_data', {}).get('episodes') or anime_data.get('episodes')
            score = anime_data.get('material_data', {}).get('shikimori_score')
            poster_url = anime_data.get('screenshots', [''])[0] if anime_data.get('screenshots') else None
            genres = anime_data.get('material_data', {}).get('genres', [])
            studios = [anime_data.get('material_data', {}).get('studio')] if anime_data.get('material_data', {}).get('studio') else []
            
            # Определяем тип
            anime_type = anime_data.get('type', '')
            if 'serial' in anime_type.lower():
                kind = 'tv'
            elif 'movie' in anime_type.lower():
                kind = 'movie'
            elif 'ova' in anime_type.lower():
                kind = 'ova'
            else:
                kind = 'tv'
            
            status = 'released'
            
        elif source == 'aniboom':
            title_ru = anime_data.get('title', '')
            title_en = anime_data.get('other_titles', [''])[0] if anime_data.get('other_titles') else title_ru
            description = anime_data.get('description', '')
            year = None
            if anime_data.get('other_info', {}).get('Выпуск'):
                try:
                    year = int(anime_data['other_info']['Выпуск'].split()[-1])
                except:
                    pass
            
            episodes = anime_data.get('episodes')
            if episodes and '/' in episodes:
                episodes = int(episodes.split('/')[1]) if episodes.split('/')[1].isdigit() else None
            elif episodes and episodes.isdigit():
                episodes = int(episodes)
            else:
                episodes = None
            
            score = None
            poster_url = anime_data.get('poster_url')
            genres = anime_data.get('genres', [])
            studios = [info.get('Студия') for info in [anime_data.get('other_info', {})] if info.get('Студия')]
            
            status_map = {
                'вышел': 'released',
                'онгоинг': 'ongoing',
                'анонс': 'anons'
            }
            status = status_map.get(anime_data.get('status', '').lower(), 'released')
            
            anime_type = anime_data.get('type', '')
            if 'фильм' in anime_type.lower():
                kind = 'movie'
            elif 'ova' in anime_type.lower():
                kind = 'ova'
            else:
                kind = 'tv'
                
        elif source == 'shikimori':
            title_ru = anime_data.get('title', '')
            title_en = anime_data.get('original_title', '') or title_ru
            description = anime_data.get('description', '')
            year = anime_data.get('dates', '').split('-')[0] if anime_data.get('dates') else None
            if year:
                try:
                    year = int(year)
                except:
                    year = None
            
            episodes_str = anime_data.get('episodes', '')
            if episodes_str and '/' in episodes_str:
                episodes = int(episodes_str.split('/')[1]) if episodes_str.split('/')[1].isdigit() else None
            elif episodes_str and episodes_str.isdigit():
                episodes = int(episodes_str)
            else:
                episodes = None
            
            score = anime_data.get('score')
            if score:
                try:
                    score = float(score)
                except:
                    score = None
            
            poster_url = anime_data.get('picture')
            genres = anime_data.get('genres', [])
            studios = [anime_data.get('studio')] if anime_data.get('studio') else []
            
            status_map = {
                'вышло': 'released',
                'онгоинг': 'ongoing',
                'анонс': 'anons'
            }
            status = status_map.get(anime_data.get('status', '').lower(), 'released')
            
            anime_type = anime_data.get('type', '')
            if 'фильм' in anime_type.lower():
                kind = 'movie'
            elif 'ova' in anime_type.lower():
                kind = 'ova'
            else:
                kind = 'tv'
        else:
            return None
        
        # Скачиваем постер
        poster_file = None
        if poster_url:
            filename = clean_filename(title_ru) + '.jpg'
            poster_file = download_image(poster_url, filename)
        
        # Создаем или обновляем запись в БД
        anime_obj, created = Anime.objects.get_or_create(
            title_ru=title_ru,
            defaults={
                'title_en': title_en,
                'description': description,
                'year': year,
                'status': status,
                'kind': kind,
                'episodes': episodes,
                'score': score,
                'poster_url': poster_url,
                'poster': poster_file,
                'genres': genres,
                'studios': studios,
                'data_source': source
            }
        )
        
        if not created:
            # Обновляем существующую запись
            anime_obj.title_en = title_en
            anime_obj.description = description
            anime_obj.year = year
            anime_obj.status = status
            anime_obj.kind = kind
            anime_obj.episodes = episodes
            anime_obj.score = score
            anime_obj.poster_url = poster_url
            if poster_file:
                anime_obj.poster = poster_file
            anime_obj.genres = genres
            anime_obj.studios = studios
            anime_obj.data_source = source
            anime_obj.save()
        
        return anime_obj
        
    except Exception as e:
        print(f'Ошибка сохранения аниме {anime_data.get("title", "Unknown")}: {e}')
        return None

def main():
    """Основная функция импорта"""
    print('Starting full anime import from all sources...')
    
    # Удаляем старые данные
    print('Clearing database...')
    Anime.objects.all().delete()
    
    total_imported = 0
    
    # Импортируем из всех источников
    sources = [
        ('kodik', import_from_kodik),
        ('aniboom', import_from_aniboom),
        ('shikimori', import_from_shikimori)
    ]
    
    for source_name, import_func in sources:
        print(f'\nImporting from {source_name.upper()}...')
        try:
            anime_list = import_func()
            if anime_list:
                for anime_data in anime_list:
                    if save_anime_to_db(anime_data, source_name):
                        total_imported += 1
                        print(f'   Saved: {anime_data.get("title", "Unknown")}')
                    time.sleep(0.5)  # Небольшая задержка
            else:
                print(f'   No data to import from {source_name}')
        except Exception as e:
            print(f'   Critical error importing from {source_name}: {e}')
    
    print(f'\nImport completed! Total saved anime: {total_imported}')
    
    # Выводим статистику
    print('\nDatabase statistics:')
    print(f'Total anime: {Anime.objects.count()}')
    print(f'With posters: {Anime.objects.exclude(poster__isnull=True).count()}')
    print(f'With descriptions: {Anime.objects.exclude(description__isnull=True).exclude(description='').count()}')
    print(f'With genres: {Anime.objects.exclude(genres__len__gt=0).count()}')

if __name__ == '__main__':
    main()