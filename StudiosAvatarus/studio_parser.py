#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pywikibot Studio Logo Collector - Исправленная версия
"""

import os
import re
import time
import json
from pathlib import Path
import sys

import pywikibot
from pywikibot.data import api

class StudioLogoCollector:
    """
    Сборщик логотипов с использованием Pywikibot
    """
    
    def __init__(self, output_folder="studio_logos"):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        
        # Подключаемся к русской Википедии
        self.site = pywikibot.Site('ru', 'wikipedia')
        
        # Логинимся
        try:
            self.site.login()
            print(f"✅ Успешный вход как: {self.site.user()}")
        except Exception as e:
            print(f"❌ Ошибка входа: {e}")
            print("Проверьте логин/пароль в конфиге")
            sys.exit(1)
        
        # Файл для сохранения прогресса
        self.progress_file = Path("pywikibot_progress.json")
        self.load_progress()
        
        print("=" * 60)
        print("🤖 Pywikibot Studio Logo Collector")
        print(f"👤 Пользователь: {self.site.user()}")
        print(f"📁 Папка: {output_folder}")
        print(f"📊 Уже собрано: {len(self.completed)}")
        print(f"🌐 Сайт: {self.site}")
        print("=" * 60)
        
    def load_progress(self):
        """Загрузка прогресса"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.completed = data.get('completed', [])
                self.failed = data.get('failed', [])
        else:
            self.completed = []
            self.failed = []
            
    def save_progress(self):
        """Сохранение прогресса"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                'completed': self.completed,
                'failed': self.failed
            }, f, ensure_ascii=False, indent=2)
            
    def get_page_image_url(self, page_title):
        """
        Получение URL логотипа через API запрос (правильный способ)
        """
        try:
            # Используем прямой API запрос для получения изображений
            params = {
                'action': 'query',
                'titles': page_title,
                'prop': 'images',
                'imlimit': 50,
                'format': 'json'
            }
            
            request = api.Request(site=self.site, parameters=params)
            data = request.submit()
            
            # Парсим результат
            pages = data.get('query', {}).get('pages', {})
            
            for page_id, page_data in pages.items():
                if page_id == '-1':  # Страница не существует
                    print(f"  Страница {page_title} не существует")
                    return None
                    
                if 'images' not in page_data:
                    print(f"  На странице нет изображений")
                    return None
                    
                images = page_data['images']
                
                # Сначала ищем логотип
                logo_image = None
                for img in images:
                    img_title = img['title'].lower()
                    if any(keyword in img_title for keyword in 
                           ['logo', 'лог', 'log', 'логотип', 'эмблема', 'emblem']):
                        logo_image = img
                        break
                        
                # Если не нашли логотип, берем первое изображение
                if not logo_image and images:
                    logo_image = images[0]
                    print(f"  Логотип не найден, беру первое изображение")
                else:
                    print(f"  Найден логотип")
                    
                if not logo_image:
                    return None
                    
                # Получаем URL изображения
                img_title = logo_image['title']
                
                # Второй запрос для получения URL
                img_params = {
                    'action': 'query',
                    'titles': img_title,
                    'prop': 'imageinfo',
                    'iiprop': 'url|mime',
                    'format': 'json'
                }
                
                img_request = api.Request(site=self.site, parameters=img_params)
                img_data = img_request.submit()
                
                img_pages = img_data.get('query', {}).get('pages', {})
                for img_page_id, img_page_data in img_pages.items():
                    if 'imageinfo' in img_page_data:
                        return img_page_data['imageinfo'][0]['url']
                        
            return None
            
        except Exception as e:
            print(f"  Ошибка API: {e}")
            return None
            
    def download_logo(self, studio_name):
        """
        Скачивание логотипа для студии
        """
        if studio_name in self.completed:
            print(f"⏭ {studio_name} уже скачан")
            return True
            
        print(f"\n🔍 Обработка: {studio_name}")
        
        # Получаем URL изображения
        img_url = self.get_page_image_url(studio_name)
        
        if not img_url:
            print(f"❌ Изображение не найдено")
            self.failed.append({
                'name': studio_name,
                'reason': 'no_image_found'
            })
            self.save_progress()
            return False
            
        print(f"  URL: {img_url[:100]}...")  # показываем начало URL
            
        # Скачиваем изображение
        try:
            # Создаем безопасное имя файла
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', studio_name)
            
            # Определяем расширение
            url_path = img_url.split('?')[0]
            ext = os.path.splitext(url_path)[1].lower()
            
            # Валидные расширения
            valid_exts = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']
            
            if not ext or ext not in valid_exts:
                # Пробуем определить по заголовкам
                import requests
                try:
                    head = requests.head(img_url, timeout=10, allow_redirects=True)
                    content_type = head.headers.get('content-type', '').lower()
                    
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'svg' in content_type:
                        ext = '.svg'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    elif 'webp' in content_type:
                        ext = '.webp'
                    else:
                        ext = '.png'
                except:
                    ext = '.png'
                    
            filename = self.output_folder / f"{safe_name}{ext}"
            
            # Скачиваем файл
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(img_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Проверяем, что это изображение
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                print(f"  Предупреждение: получен {content_type}")
                
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"✅ Сохранено: {filename.name}")
            
            self.completed.append(studio_name)
            self.save_progress()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка скачивания: {e}")
            self.failed.append({
                'name': studio_name,
                'reason': str(e)
            })
            self.save_progress()
            return False
            
    def collect_all(self, studios):
        """
        Сбор всех студий
        """
        # Фильтруем уже обработанные
        to_process = [s for s in studios if s not in self.completed]
        
        print(f"\n🎯 Осталось обработать: {len(to_process)} студий")
        
        for i, studio in enumerate(to_process, 1):
            print(f"\n[{i}/{len(to_process)}] ", end="")
            
            success = self.download_logo(studio)
            
            # Пауза между запросами
            if i < len(to_process):
                delay = 3
                print(f"  ⏸ Пауза {delay}с...")
                time.sleep(delay)
                
            # После каждых 5 студий - длинная пауза
            if i % 5 == 0 and i < len(to_process):
                pause = 30
                print(f"\n⏸ ДЛИННАЯ ПАУЗА {pause}с (обработано {i})")
                time.sleep(pause)
                
        # Итог
        print("\n" + "=" * 60)
        print("📊 ИТОГИ:")
        print(f"✅ Успешно: {len(self.completed)}")
        print(f"❌ Ошибок: {len(self.failed)}")
        print("=" * 60)

# ============================================================================
# ЗАПУСК
# ============================================================================

if __name__ == "__main__":
    
    # Список студий
    STUDIOS = [
        "Kyoto Animation",
        "Lay-duce", "Lerche", "Liden Films",
        "Madhouse", "Magic Bus (студия)", "MAPPA", "Mushi Production",
        "NAZ (студия)", "Nexus (анимационная студия)", "Nippon Animation", "NUT",
        "OLM, Inc.", "Ordet",
        "P.A. Works", "Passione", "Pony Canyon", "Production I.G", "Project No.9",
        "Robot Communications",
        "Sanzigen", "Satelight", "Science Saru", "Seven (анимационная студия)",
        "Seven Arcs", "Shaft (компания)", "Shin-Ei Animation", "Shuka", "Silver Link",
        "Studio 4°C", "Studio A-Cat", "Studio Bind", "Studio Comet", "Studio Deen",
        "Studio Ghibli", "Studio Gokumi", "Studio Hibari", "Studio Khara", "Studio Pierrot",
        "Studio Ponoc", "Studio VOLN",
        "Tatsunoko Production", "Tear Studio", "Tezuka Productions", "TMS Entertainment",
        "TNK", "Toei Animation", "Toho", "Trigger (компания)", "TROYCA",
        "Tsuchida Production", "TYO Animations", "Type-Moon", "Typhoon Graphics",
        "Ufotable", "Ultra Super Pictures",
        "VAP", "Victor Entertainment",
        "White Fox", "Wit Studio",
        "Zero-G", "Zexcs"
    ]
    
    # Создаем и запускаем коллектор
    collector = StudioLogoCollector()
    collector.collect_all(STUDIOS)