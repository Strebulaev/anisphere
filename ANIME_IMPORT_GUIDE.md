# Импорт аниме через Shikimori API

## Описание

Два скрипта для полноценного импорта аниме из Shikimori с реальными данными:
- Постеры (картинки)
- Описания
- Статусы (онгоинг, завершен, анонс)
- Жанры
- Студии
- Рейтинги
- Количество эпизодов
- Год выпуска

## Скрипты

### 1. import_shikimori_full.py - Базовый импорт

Импортирует аниме постранично с сортировкой по популярности.

**Запуск:**
```bash
python import_shikimori_full.py
```

**Опции:**
- `--max N` - максимальное количество аниме (по умолчанию: 10000)
- `--skip-images` - не скачивать постеры (быстрее)
- `--fast` - быстрый режим (минимальные задержки)

**Примеры:**
```bash
# Импорт 1000 аниме с картинками
python import_shikimori_full.py --max 1000

# Быстрый импорт без картинок
python import_shikimori_full.py --max 5000 --skip-images --fast
```

### 2. import_shikimori_extended.py - Расширенный импорт

Импортирует аниме с множественными фильтрами для максимального охвата:
- По статусам (released, ongoing, anons)
- По типам (TV, Movie, OVA, ONA)
- По рейтингам (G, PG, PG-13, R, R+)
- По жанрам (Action, Comedy, Drama и др.)
- По годам (2015-2024)

**Запуск:**
```bash
python import_shikimori_extended.py
```

**Опции:**
- `--max N` - максимальное количество аниме (по умолчанию: 20000)
- `--skip-images` - не скачивать постеры
- `--fast` - быстрый режим

**Примеры:**
```bash
# Максимальный импорт с картинками
python import_shikimori_extended.py --max 20000

# Быстрый импорт без картинок
python import_shikimori_extended.py --max 10000 --skip-images --fast
```

## Рекомендации по использованию

### Для быстрого теста:
```bash
python import_shikimori_full.py --max 100 --skip-images --fast
```

### Для полноценного наполнения базы:
```bash
# Сначала базовый импорт
python import_shikimori_full.py --max 10000

# Затем расширенный для охвата больше аниме
python import_shikimori_extended.py --max 20000
```

### Для обновления существующих данных:
```bash
# Скрипты автоматически обновляют существующие записи
# если у них нет описания, жанров, студий и т.д.
python import_shikimori_extended.py --max 5000 --fast
```

## Логи

- `shikimori_full_import.log` - логи базового импорта
- `shikimori_extended_import.log` - логи расширенного импорта

## Ограничения API

Shikimori API имеет ограничения по количеству запросов. Скрипты автоматически:
- Обрабатывают ошибки 429 (Too Many Requests)
- Делают паузы при превышении лимитов
- Повторяют неудачные запросы

## Где сохраняются постеры

Постеры сохраняются в: `backend/media/anime_posters/`

## Статистика после импорта

После завершения импорта скрипты показывают:
- Общее количество аниме в базе
- Количество новых записей
- Количество обновленных записей
- Количество ошибок
- Время выполнения
- Примеры последних добавленных аниме

## Проверка результата

После импорта можно проверить данные в Django shell:

```bash
python backend/manage.py shell
```

```python
from anime.models import Anime

# Общее количество
print(Anime.objects.count())

# С постерами
print(Anime.objects.exclude(poster__isnull=True).exclude(poster='').count())

# С описаниями
print(Anime.objects.exclude(description__isnull=True).exclude(description='').count())

# По статусам
print("Ongoing:", Anime.objects.filter(status='ongoing').count())
print("Finished:", Anime.objects.filter(status='finished').count())
print("Announced:", Anime.objects.filter(status='announced').count())

# По типам
print("TV:", Anime.objects.filter(kind='tv').count())
print("Movie:", Anime.objects.filter(kind='movie').count())
```

## Решение проблем

### Если импорт останавливается на середине:

Запустите снова с теми же параметрами - скрипты продолжат с того места, так как:
- Проверяют существующие записи по `shikimori_id`
- Не дублируют данные
- Обновляют только пустые поля

### Если не скачиваются картинки:

Убедитесь что директория существует:
```bash
mkdir -p backend/media/anime_posters
```

### Если слишком много ошибок 429:

Используйте флаг `--fast` для увеличения пауз между запросами, или уменьшите `--max` для тестового запуска.
