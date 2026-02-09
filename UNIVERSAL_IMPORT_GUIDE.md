# Универсальный импортёр аниме

## Обзор

Универсальный импортёр использует несколько источников данных для максимальной надёжности и охвата:

### Источники данных

1. **Jikan API (MyAnimeList)** - работает в РФ без VPN
   - Топ аниме
   - Сезонные аниме
   - Поиск по названию

2. **AniList GraphQL API** - работает в РФ без VPN
   - Трендовые аниме
   - Популярные аниме

### Особенности

- ✅ Работает без VPN в РФ
- ✅ Несколько источников данных
- ✅ Автоматическое обновление существующих записей
- ✅ Скачивание постеров (картинок)
- ✅ Полные данные: названия, описания, жанры, студии, статусы
- ✅ Обработка ошибок и повторные попытки
- ✅ Подробные логи

## Установка

Нет дополнительных зависимостей - использует стандартные библиотеки Django.

## Использование

### Базовый запуск (тестовый)

```bash
python import_anime_universal.py --max 50 --skip-images --fast
```

Это импортирует 50 аниме без картинок в быстром режиме для проверки.

### Полноценный импорт

```bash
# Импорт с картинками (рекомендуется для начала)
python import_anime_universal.py --max 1000

# Полный импорт с картинками
python import_anime_universal.py --max 10000

# Быстрый импорт без картинок
python import_anime_universal.py --max 5000 --skip-images --fast
```

### Параметры командной строки

- `--max N` - максимальное количество аниме для импорта (по умолчанию: 10000)
- `--skip-images` - не скачивать постеры (ускоряет процесс)
- `--fast` - быстрый режим (минимальные задержки между запросами)
- `--workers N` - количество рабочих потоков (по умолчанию: 5)

## Примеры использования

### Тестовый запуск (без картинок)

```bash
python import_anime_universal.py --max 100 --skip-images --fast
```

### Небольшой импорт с картинками

```bash
python import_anime_universal.py --max 500
```

### Средний импорт

```bash
python import_anime_universal.py --max 2000
```

### Максимальный импорт

```bash
python import_anime_universal.py --max 10000
```

### Обновление существующих данных

```bash
# Скрипт автоматически обновляет существующие записи
# если у них нет описания, жанров, студий и т.д.
python import_anime_universal.py --max 5000 --fast
```

## Логи

Логи сохраняются в файл `universal_anime_import.log` и выводятся в консоль.

## Как работает импорт

### Этап 1: Jikan Top Anime
Импортирует топ-500 аниме с MyAnimeList по рейтингу.

### Этап 2: AniList Trending
Импортирует трендовые аниме с AniList.

### Этап 3: Jikan Seasonal
Импортирует сезонные аниме за последние 3 года (2024-2026).

### Этап 4: AniList Popular
Импортирует популярные аниме с AniList.

### Этап 5: Поиск по популярным названиям
Импортирует аниме по списку популярных названий.

## Обновление данных

Скрипт автоматически:
- Не создаёт дубликаты (проверяет по названию)
- Обновляет существующие записи если у них нет:
  - Описания
  - Жанров
  - Студий
  - Рейтинга
  - Количество эпизодов
  - Постера

## Проверка результата

### Через Django shell

```bash
python backend/manage.py shell
```

```python
from anime.models import Anime

# Общее количество
print(f"Total: {Anime.objects.count()}")

# С постерами
print(f"With posters: {Anime.objects.exclude(poster__isnull=True).exclude(poster='').count()}")

# С описаниями
print(f"With descriptions: {Anime.objects.exclude(description__isnull=True).exclude(description='').count()}")

# По статусам
print(f"Ongoing: {Anime.objects.filter(status='ongoing').count()}")
print(f"Finished: {Anime.objects.filter(status='finished').count()}")
print(f"Announced: {Anime.objects.filter(status='announced').count()}")

# По типам
print(f"TV: {Anime.objects.filter(kind='tv').count()}")
print(f"Movie: {Anime.objects.filter(kind='movie').count()}")
print(f"OVA: {Anime.objects.filter(kind='ova').count()}")

# По источникам
print(f"From Jikan: {Anime.objects.filter(data_source='jikan').count()}")
print(f"From AniList: {Anime.objects.filter(data_source='anilist').count()}")

# Примеры аниме
print("\nRecent anime:")
for anime in Anime.objects.order_by('-id')[:10]:
    poster = "✓" if anime.poster else "✗"
    print(f"  [{poster}] {anime.title_ru[:50]} ({anime.year or 'N/A'})")
```

### Через админку Django

1. Перейдите в админку: `http://localhost:8000/admin/`
2. Перейдите в раздел Anime
3. Просмотрите список аниме

## Решение проблем

### Проблема: "Rate limited"

Если вы видите сообщение "Rate limited", скрипт автоматически подождёт и продолжит. Для уменьшения вероятности этой ошибки используйте параметр `--fast`.

### Проблема: Медленная загрузка

Используйте `--skip-images` для пропуска загрузки картинок:
```bash
python import_anime_universal.py --max 5000 --skip-images
```

### Проблема: Скрипт остановился

Просто запустите его снова с теми же параметрами. Скрипт продолжит с того места, так как:
- Не создаёт дубликаты
- Обновляет только пустые поля

### Проблема: Нет картинок

Убедитесь что директория существует:
```bash
mkdir -p backend/media/anime_posters
```

### Проблема: Слишком много ошибок

Используйте быстрый режим с меньшим количеством аниме для теста:
```bash
python import_anime_universal.py --max 100 --skip-images --fast
```

## Статистика после импорта

После завершения скрипт покажет:
- Общее количество аниме в базе
- Количество новых записей
- Количество обновленных записей
- Количество ошибок
- Время выполнения
- Статистику по статусам (ongoing, finished, announced)
- Статистику по типам (tv, movie, ova, ona)
- Статистику по источникам данных (jikan, anilist)
- Примеры последних добавленных аниме

## Рекомендации

1. **Начните с тестового запуска:**
   ```bash
   python import_anime_universal.py --max 50 --skip-images --fast
   ```

2. **Затем импортируйте с картинками:**
   ```bash
   python import_anime_universal.py --max 500
   ```

3. **После успешного теста запустите полный импорт:**
   ```bash
   python import_anime_universal.py --max 10000
   ```

4. **Для обновления данных запускайте периодически:**
   ```bash
   python import_anime_universal.py --max 2000 --fast
   ```

## Ограничения

- Jikan API имеет ограничения по количеству запросов (обрабатывается автоматически)
- AniList GraphQL API имеет ограничения (обрабатывается автоматически)
- Время импорта зависит от количества аниме и скорости интернета
- Загрузка картинок занимает дополнительное время

## Сравнение с другими скриптами

| Скрипт | Источники | Работает в РФ | Картинки | Описания |
|--------|-----------|---------------|----------|----------|
| `import_shikimori_full.py` | Shikimori | ❌ (заблокирован) | ✅ | ✅ |
| `import_jikan_full.py` | Jikan | ✅ | ✅ | ✅ |
| `import_anime_universal.py` | Jikan + AniList | ✅ | ✅ | ✅ |

**Рекомендация:** Используйте `import_anime_universal.py` - он наиболее надёжный и универсальный.
