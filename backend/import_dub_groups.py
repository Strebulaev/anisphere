"""
Скрипт импорта групп озвучки из Kodik API в БД
Оптимизированная версия - сначала базовый импорт, потом детализация

Запуск:
1. Базовая загрузка (быстро): python manage.py shell < import_dub_groups.py
2. Детальная привязка к аниме: python manage.py shell < import_dub_groups_detail.py
"""
import os
import requests
import time

KODIK_TOKEN = os.environ.get('KODIK_API_TOKEN', '74ecb013335271e4344ebc994956dd75')
KODIK_URL = 'https://kodik-api.com'

def generate_slug(name, existing_slugs):
    """Генерация уникального slug"""
    base_slug = name.lower()
    for ch in ' .!?,()[]{}':
        base_slug = base_slug.replace(ch, '')
    base_slug = base_slug.replace('  ', ' ').strip()
    base_slug = base_slug.replace(' ', '-')
    
    if not base_slug:
        base_slug = 'dub-group'
    
    slug = base_slug
    counter = 1
    while slug in existing_slugs:
        slug = f'{base_slug}-{counter}'
        counter += 1
    
    existing_slugs.add(slug)
    return slug

def import_all_translations():
    """Быстрый импорт всех озвучек - только базовая информация"""
    from dubs.models import DubGroup
    
    print("📡 Загружаю все озвучки из Kodik...")
    
    params = {
        'token': KODIK_TOKEN,
        'limit': 1000,
    }
    
    all_translations = []
    offset = 0
    
    while True:
        params['offset'] = offset
        response = requests.get(f'{KODIK_URL}/translations/v2', params=params, timeout=30)
        data = response.json()
        
        results = data.get('results', [])
        if not results:
            break
            
        all_translations.extend(results)
        print(f"   Загружено: {len(all_translations)}...")
        
        if len(results) < 1000:
            break
        offset += 1000
        time.sleep(0.2)
    
    print(f"✅ Всего найдено озвучек: {len(all_translations)}")
    
    existing_slugs = set(DubGroup.objects.values_list('slug', flat=True))
    
    print(f"\n🎬 Начинаю импорт {len(all_translations)} групп...")
    
    created = 0
    skipped = 0
    
    for i, t in enumerate(all_translations):
        try:
            name = t.get('title', '').strip()
            count = t.get('count', 0)
            trans_type = t.get('type', 'voice')
            
            if not name:
                skipped += 1
                continue
            
            if DubGroup.objects.filter(name=name).exists():
                skipped += 1
                continue
            
            translation_type = 'subtitles' if trans_type == 'subtitles' else 'voice'
            
            slug = generate_slug(name, existing_slugs)
            
            group = DubGroup.objects.create(
                name=name,
                slug=slug,
                translation_type=translation_type,
                works_count=count,
                status='active',
                average_rating=0,
            )
            
            created += 1
            existing_slugs.add(slug)
            
            if (i + 1) % 100 == 0:
                print(f"   Прогресс: {i+1}/{len(all_translations)}...")
            
            time.sleep(0.03)
            
        except Exception as e:
            continue
    
    print(f"\n✅ Импорт завершён!")
    print(f"   Создано: {created}")
    print(f"   Пропущено: {skipped}")
    print(f"   Всего в базе: {DubGroup.objects.count()}")


if __name__ == '__main__':
    import django
    import sys
    sys.path.insert(0, '/var/www/www-root/data/www/anisphere.ru')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    import_all_translations()
