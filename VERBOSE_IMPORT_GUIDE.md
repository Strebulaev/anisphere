# Подробный импортёр аниме с путями к постерам

## Что нового

Скрипт `import_anime_verbose.py` теперь показывает **путь к постеру** для каждого аниме:

### При импорте каждого аниме:
```
🆕 [NEW] ID: 123 | Source: JIKAN
  📺 Title (RU): Fullmetal Alchemist: Brotherhood
  📺 Title (EN): Fullmetal Alchemist: Brotherhood
  📅 Year: 2009 | 📊 Status: finished | 🎬 Type: tv
  📼 Episodes: 64 | ⭐ Score: 9.1
  🖼️  Poster: ✅ anime_posters/Fullmetal_Alchemist_Brotherhood_5114.jpg
  🎭 Genres: Action, Adventure, Drama, Fantasy
  🏢 Studios: Bones
```

### В консолидированной сводке:
- **Топ-20 по рейтингу** - с путями к постерам
- **Последние 20 добавленных** - с путями к постерам
- **Все ongoing аниме** - с путями к постерам
- **Полный список обработанных** - с путями к постерам
- **Примеры путей к постерам** - отдельная секция

## Статусы постеров

- ✅ `anime_posters/Name_ID.jpg` - постер скачан и сохранён локально
- ⏳ `https://...` - только URL постера (не скачан)
- ❌ `No poster` - нет постера

## Использование

### Тестовый запуск (без картинок - быстрые URL):
```bash
python import_anime_verbose.py --max 50 --skip-images --fast
```
Результат: покажет URL постеров, но не будет скачивать

### Скачивание постеров:
```bash
python import_anime_verbose.py --max 100
```
Результат: скачает постеры в `backend/media/anime_posters/`

### Полный импорт:
```bash
python import_anime_verbose.py --max 1000
```

## Параметры

- `--max N` - максимальное количество аниме
- `--skip-images` - НЕ скачивать постеры (только URL)
- `--fast` - быстрый режим
- `--workers N` - количество потоков

## Где хранятся постеры

Постеры сохраняются в: `backend/media/anime_posters/`

Пример пути: `anime_posters/Fullmetal_Alchemist_Brotherhood_5114.jpg`

## Пример вывода

### При импорте:
```
🆕 [NEW] ID: 1 | Source: JIKAN
  📺 Title (RU): Fullmetal Alchemist: Brotherhood
  📅 Year: 2009 | 📊 Status: finished | 🎬 Type: tv
  📼 Episodes: 64 | ⭐ Score: 9.1
  🖼️  Poster: ✅ anime_posters/Fullmetal_Alchemist_Brotherhood_5114.jpg
  🎭 Genres: Action, Adventure, Drama, Fantasy
  🏢 Studios: Bones
```

### В сводке:
```
⭐ TOP 20 BY SCORE:
   1. Fullmetal Alchemist: Brotherhood     | ⭐ 9.10 | 🖼️  anime_posters/Fullmetal_Alchemist_Brotherhood_5114.jpg
   2. Attack on Titan Final Season         | ⭐ 9.05 | 🖼️  anime_posters/Attack_on_Titan_16498.jpg
   ...
```

```
🖼️  POSTER PATHS EXAMPLES:
  1. Fullmetal Alchemist: Brotherhood
     Path: anime_posters/Fullmetal_Alchemist_Brotherhood_5114.jpg
     URL:  https://cdn.myanimelist.net/images/anime/1223/96541.jpg...
  2. Attack on Titan
     Path: anime_posters/Attack_on_Titan_16498.jpg
     URL:  https://cdn.myanimelist.net/images/anime/10/47347.jpg...
```

## Проверка постеров в базе данных

```python
from anime.models import Anime

# Все аниме с постерами
anime_with_posters = Anime.objects.exclude(poster__isnull=True).exclude(poster='')
print(f"Anime with posters: {anime_with_posters.count()}")

# Примеры путей
for anime in anime_with_posters[:5]:
    print(f"{anime.title_ru}: {anime.poster.name}")

# Аниме без постеров
anime_without_posters = Anime.objects.filter(poster__isnull=True) | Anime.objects.filter(poster='')
print(f"Anime without posters: {anime_without_posters.count()}")
```

## Рекомендации

1. **Сначала тест без картинок:**
   ```bash
   python import_anime_verbose.py --max 50 --skip-images --fast
   ```

2. **Затем с картинками:**
   ```bash
   python import_anime_verbose.py --max 100
   ```

3. **Полный импорт:**
   ```bash
   python import_anime_verbose.py --max 1000
   ```

4. **Для обновления:**
   ```bash
   python import_anime_verbose.py --max 500 --fast
   ```

## Отличия от обычного импортёра

| Функция | `import_anime_universal.py` | `import_anime_verbose.py` |
|---------|----------------------------|---------------------------|
| Вывод каждого аниме | ✅ Краткий | ✅ **Подробный** |
| Путь к постеру | ❌ | ✅ **Да** |
| Консолидированная сводка | ✅ | ✅ **Расширенная** |
| Примеры путей к постерам | ❌ | ✅ **Да** |
| Все обработанные в этом запуске | ❌ | ✅ **Да** |

Используйте `import_anime_verbose.py` для полного контроля над импортом и путями к постерам!
