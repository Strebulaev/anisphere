# Система настроек чатов AnimeCore

> Полная документация системы настроек личных и групповых чатов с ролевой моделью, модерацией и кастомизацией.

---

## Содержание

1. [Обзор архитектуры](#обзор-архитектуры)
2. [Личные чаты](#личные-чаты)
3. [Групповые чаты](#групповые-чаты)
4. [Ролевая система](#ролевая-система)
5. [Права и разрешения](#права-и-разрешения)
6. [Модерация](#модерация)
7. [Уведомления](#уведомления)
8. [Кастомизация](#кастомизация)
9. [Приглашения и ссылки](#приглашения-и-ссылки)
10. [Архивирование и организация](#архивирование-и-организация)
11. [Безопасность](#безопасность)
12. [WebSocket события](#websocket-события)
13. [API Endpoints](#api-endpoints)

---

## Обзор архитектуры

### Типы чатов

| Тип | Описание | Участники | Особенности |
|-----|----------|-----------|-------------|
| **Личный** | Диалог двух пользователей | 2 | Статусы онлайн, приватность |
| **Группа** | Многопользовательский чат | до 200,000 | Роли, модерация, ссылки-приглашения |
| **Обсуждение аниме** | Группа с привязкой к аниме | до 200,000 | Постер аниме, интеграция с контентом |
| **Канал** | Односторонняя коммуникация | безлимит | Только админы пишут |

### Иерархия настроек

```
Глобальные настройки пользователя
    ├── Настройки конкретного чата (персональные)
    │   ├── Уведомления
    │   ├── Папки
    │   └── Кастомизация
    └── Настройки группы (общие)
        ├── Роли и права
        ├── Модерация
        └── Внешний вид
```

---

## Личные чаты

### Персональные настройки пользователя

Каждый пользователь имеет независимые настройки для каждого личного чата.

#### Основные настройки

| Настройка | Тип | Описание |
|-----------|-----|----------|
| `custom_name` | string | Персональное название чата (только для себя) |
| `custom_avatar` | file | Персональная аватарка чата |
| `notifications` | boolean | Включить/выключить уведомления |
| `muted_until` | datetime | Заглушить до определённой даты |
| `archived` | boolean | Архивировать чат |
| `pinned` | boolean | Закрепить чат |
| `blocked` | boolean | Заблокировать пользователя |
| `hidden` | boolean | Скрыть чат из списка |

#### Настройки уведомлений

```
Уведомления
├── Включены
├── Заглушены
│   ├── На 1 час
│   ├── На 8 часов
│   ├── На 2 дня
│   ├── Навсегда (пока не включу)
│   └── До определённой даты
└── Персональные настройки
    ├── Звук: default/none/custom
    ├── Вибрация: default/none/short/long
    ├── Всплывающие: on/off
    └── Превью сообщения: on/off
```

#### Блокировка пользователя

При блокировке:
- Пользователь не может отправлять сообщения
- Не видит ваш статус "онлайн"
- Не видит "печатает..."
- Сообщения не доставляются (отправитель видит 1 галочку)
- Можно пожаловаться на пользователя при блокировке

#### Дополнительные опции

| Опция | Описание |
|-------|----------|
| `auto_delete` | Автоудаление сообщений через N времени |
| `report_spam` | Пожаловаться на спам |
| `clear_history` | Очистить историю (только для себя) |
| `delete_chat` | Удалить чат (только для себя) |

---

## Групповые чаты

### Общие настройки группы

Доступны для изменения администраторами с правом `can_change_chat_info`.

#### Основная информация

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `name` | string | 1-255 символов | Название группы |
| `description` | text | до 5000 символов | Описание |
| `avatar` | file | max 2MB, image/* | Аватар группы |
| `emoji_status` | string | emoji | Эмодзи-статус группы |

#### Настройки приватности

| Настройка | Описание |
|-----------|----------|
| `is_public` | Публичная группа (доступна в поиске) |
| `join_to_send` | Нужно вступить для отправки сообщений |
| `restrict_saving_content` | Запретить сохранение контента |
| `has_hidden_members` | Скрыть список участников |

#### Настройки сообщений

| Настройка | Описание |
|-----------|----------|
| `slow_mode_delay` | Задержка между сообщениями (0-3600 сек) |
| `allow_media` | Разрешить медиафайлы |
| `allow_stickers` | Разрешить стикеры |
| `allow_gifs` | Разрешить GIF |
| `allow_polls` | Разрешить опросы |
| `allow_links` | Разрешить ссылки |
| `allow_voice` | Разрешить голосовые сообщения |
| `allow_video_messages` | Разрешить видеосообщения |

#### Группы обсуждений аниме

Дополнительные поля для групп с привязкой к аниме:

| Поле | Описание |
|------|----------|
| `anime_id` | ID аниме на Shikimori |
| `anime_title` | Название аниме |
| `anime_poster` | Постер аниме (автозамена аватара) |
| `discussion_type` | Тип: discussion/reviews/news |

---

## Ролевая система

### Иерархия ролей

```
┌─────────────────────────────────────────────────────────────┐
│                    ВЛАДЕЛЕЦ (Owner)                         │
│  • Все права                                                │
│  • Не может быть понижен                                    │
│  • Передача владения                                        │
│  • Удаление группы                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 АДМИНИСТРАТОРЫ (Admins)                     │
│  • Управление участниками                                   │
│  • Модерация контента                                       │
│  • Настройки группы                                         │
│  • Создание приглашений                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   МОДЕРАТОРЫ (Moderators)                   │
│  • Удаление сообщений                                       │
│  • Ограничение участников                                   │
│  • Закрепление сообщений                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               СПЕЦИАЛЬНЫЕ РОЛИ (Custom Roles)               │
│  • Настраиваемые права                                      │
│  • Кастомные названия и цвета                               │
│  • Ограниченные права                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    УЧАСТНИКИ (Members)                      │
│  • Базовые права                                            │
│  • Отправка сообщений                                       │
│  • Реакции                                                  │
└─────────────────────────────────────────────────────────────┘
```

### Предустановленные роли

#### Владелец (Owner)
- **Уровень**: 5 (максимальный)
- **Цвет**: `#FFD700` (золотой)
- **Права**: Все права без исключений
- **Особенности**:
  - Единственный в группе
  - Не может быть удалён или понижен
  - Может передать владение другому участнику

#### Администратор (Administrator)
- **Уровень**: 4
- **Цвет**: `#E74C3C` (красный)
- **Права по умолчанию**:
  - `can_manage_chat` — управление настройками
  - `can_change_chat_info` — изменение информации
  - `can_delete_messages` — удаление сообщений
  - `can_ban_users` — блокировка пользователей
  - `can_invite_users` — приглашение участников
  - `can_pin_messages` — закрепление сообщений
  - `can_promote_members` — повышение до модератора
  - `can_manage_video_chats` — управление видеочатами

#### Модератор (Moderator)
- **Уровень**: 3
- **Цвет**: `#3498DB` (синий)
- **Права по умолчанию**:
  - `can_delete_messages` — удаление сообщений
  - `can_restrict_members` — ограничение участников
  - `can_pin_messages` — закрепление сообщений
  - `can_invite_users` — приглашение участников

### Кастомные роли

Администраторы с правом `can_add_new_admins` могут создавать кастомные роли.

#### Параметры кастомной роли

| Параметр | Тип | Описание |
|----------|-----|----------|
| `name` | string | Название роли (до 50 символов) |
| `color` | hex | Цвет роли (#RRGGBB) |
| `icon` | emoji | Иконка роли |
| `level` | int | Уровень (1-4) |
| `custom_title` | string | Кастомный титул для участников с этой ролью |

#### Настраиваемые права для кастомных ролей

```yaml
Права модерации:
  - can_delete_messages: Удаление сообщений
  - can_ban_users: Блокировка пользователей
  - can_restrict_members: Ограничение участников
  - can_pin_messages: Закрепление сообщений

Права управления:
  - can_manage_chat: Полное управление группой
  - can_change_chat_info: Изменение названия, описания, аватара
  - can_invite_users: Приглашение участников
  - can_add_new_admins: Назначение администраторов
  - can_promote_members: Повышение участников

Права контента:
  - can_post_messages: Публикация сообщений (для каналов)
  - can_edit_messages: Редактирование чужих сообщений
  - can_manage_video_chats: Управление видеочатами

Специальные права:
  - can_remain_anonymous: Скрытие роли
  - can_delete_chat: Удаление группы
```

### Правила передачи ролей

1. **Повышение**:
   - Владелец может повысить любого до любой роли
   - Админ может повышать только до уровня ниже своего
   - Модератор не может повышать участников

2. **Понижение**:
   - Нельзя понизить участника с уровнем выше или равным своему
   - Владелец не может быть понижен

3. **Передача владения**:
   - Только текущий владелец может передать владение
   - Новый владелец автоматически становится администратором
   - Старый владелец понижается до администратора

---

## Права и разрешения

### Матрица прав

| Право | Владелец | Админ | Модератор | Участник |
|-------|:--------:|:-----:|:---------:|:--------:|
| Отправка сообщений | ✅ | ✅ | ✅ | ✅ |
| Редактирование своих сообщений | ✅ | ✅ | ✅ | ✅ |
| Удаление своих сообщений | ✅ | ✅ | ✅ | ✅ |
| Удаление чужих сообщений | ✅ | ✅ | ✅ | ❌ |
| Закрепление сообщений | ✅ | ✅ | ✅ | ❌ |
| Редактирование чужих сообщений | ✅ | ✅ | ❌ | ❌ |
| Приглашение участников | ✅ | ✅ | ✅ | ⚠️ |
| Исключение участников | ✅ | ✅ | ❌ | ❌ |
| Ограничение участников | ✅ | ✅ | ✅ | ❌ |
| Блокировка участников | ✅ | ✅ | ❌ | ❌ |
| Изменение информации группы | ✅ | ✅ | ❌ | ❌ |
| Создание ролей | ✅ | ✅ | ❌ | ❌ |
| Назначение ролей | ✅ | ✅ | ❌ | ❌ |
| Создание ссылок-приглашений | ✅ | ✅ | ⚠️ | ❌ |
| Управление видеочатами | ✅ | ✅ | ✅ | ❌ |
| Удаление группы | ✅ | ❌ | ❌ | ❌ |
| Передача владения | ✅ | ❌ | ❌ | ❌ |

**Легенда**: ✅ — разрешено, ❌ — запрещено, ⚠️ — зависит от настроек группы

### Ограничения участников

Администраторы могут накладывать ограничения на участников:

| Ограничение | Параметры |
|-------------|-----------|
| Только чтение | Нельзя отправлять сообщения |
| Без медиа | Нельзя отправлять фото/видео |
| Без стикеров | Нельзя отправлять стикеры/GIF |
| Без ссылок | Нельзя отправлять ссылки |
| Без голосовых | Нельзя отправлять голосовые |
| Медленный режим | Персональная задержка между сообщениями |

Ограничения могут быть:
- Постоянными
- Временными (до определённой даты)
- С причиной (видна участнику)

---

## Модерация

### Инструменты модерации

#### Удаление сообщений
- Одно сообщение
- Диапазон сообщений (от A до B)
- Все сообщения пользователя за период
- Очистка чата (только владелец)

#### Ограничение участников

```
Ограничение
├── Тип ограничения
│   ├── Только чтение
│   ├── Без медиа
│   ├── Без стикеров
│   ├── Без ссылок
│   └── Кастомное
├── Длительность
│   ├── 1 час
│   ├── 1 день
│   ├── 1 неделя
│   ├── 1 месяц
│   └── Навсегда
└── Причина
    └── Обязательное поле (до 255 символов)
```

#### Блокировка (Ban)

При блокировке:
- Пользователь исключается из группы
- Не может вернуться по приглашению
- Не видит содержимое группы
- Может подать апелляцию

Параметры блокировки:
- `user_id` — ID пользователя
- `reason` — причина (обязательно)
- `until_date` — дата разблокировки (опционально)
- `delete_messages` — удалить все сообщения пользователя

#### Анти-спам фильтры

Автоматические правила:

| Правило | Параметры | Действие |
|---------|-----------|----------|
| Flood | >N сообщений за M секунд | Мут на X минут |
| Links | Ссылки в сообщениях | Удаление / Мут |
| Spam keywords | Стоп-слова | Удаление / Мут |
| New members | Ограничение новых участников | Только чтение N дней |
| Caps lock | >70% заглавных | Удаление |

### Журнал действий (Admin Logs)

Все действия администрации записываются:

| Событие | Поля |
|---------|------|
| Изменение названия | old_name, new_name |
| Изменение описания | old_description, new_description |
| Изменение аватара | old_avatar, new_avatar |
| Закрепление сообщения | message_id |
| Исключение участника | user_id, reason |
| Блокировка участника | user_id, reason, until_date |
| Изменение прав роли | role_id, old_permissions, new_permissions |
| Создание приглашения | invite_link_id |
| Изменение настроек | setting_name, old_value, new_value |

Журнал доступен:
- Владельцу — полностью
- Администраторам — за последние 30 дней
- Модераторам — только свои действия

---

## Уведомления

### Глобальные настройки уведомлений

```
Уведомления
├── Личные сообщения
│   ├── Все
│   ├── Только от контактов
│   └── Никто
├── Группы
│   ├── Все
│   ├── Только упоминания (@username)
│   └── Никто
├── Звуки
│   ├── Личные сообщения: [звук]
│   ├── Группы: [звук]
│   └── Каналы: [звук]
├── Вибрация
│   ├── По умолчанию
│   ├── Только звук
│   ├── Только вибрация
│   └── Тихий режим
└── Всплывающие уведомления
    ├── Показывать
    ├── Показывать только от контактов
    └── Не показывать
```

### Персональные настройки уведомлений чата

Для каждого чата можно переопределить:

| Настройка | Значения |
|-----------|----------|
| Уведомления | Включены / Заглушены / Только упоминания |
| Звук | По умолчанию / Без звука / Кастомный |
| Вибрация | По умолчанию / Без вибрации / Кастомная |
| Превью | Показывать текст / Скрыть |
| Всплывающие | Показывать / Не показывать |

### Заглушивание

```
Заглушить на:
├── 15 минут
├── 1 час
├── 8 часов
├── 2 дня
├── 1 неделю
├── Навсегда
└── До определённой даты 📅
```

### Исключения из заглушивания

Можно добавить пользователей, от которых уведомления будут приходить всегда:
- Контакты
- Избранные пользователи
- Конкретные пользователи (до 50 человек)

---

## Кастомизация

### Обои чатов

Каждый чат может иметь свои обои.

#### Параметры обоев

| Параметр | Описание |
|----------|----------|
| `wallpaper_type` | solid/gradient/pattern/image |
| `wallpaper_color` | Основной цвет (#RRGGBB) |
| `wallpaper_color2` | Второй цвет (для градиента) |
| `wallpaper_intensity` | Интенсивность (0-100%) |
| `wallpaper_blur` | Размытие (0-100%) |
| `wallpaper_motion` | Анимация (parallax/none) |
| `wallpaper_image` | Кастомное изображение |

#### Предустановленные обои

```yaml
Категории обоев:
  Сплошные цвета:
    - Белый
    - Чёрный
    - Тёмно-синий
    - Тёмно-серый
    - Индиго
    
  Градиенты:
    - Синий → Фиолетовый
    - Розовый → Оранжевый
    - Зелёный → Бирюзовый
    - Фиолетовый → Розовый
    
  Паттерны:
    - Точки
    - Сетка
    - Волны
    - Геометрия
    
  Тематические:
    - Аниме (постеры)
    - Космос
    - Природа
    - Минимализм
```

#### Кастомные обои

- Загрузка изображения (до 5MB)
- Форматы: JPG, PNG, WEBP
- Автоматическое размытие для читаемости
- Адаптация под тёмную/светлую тему

### Тема чата

| Настройка | Значения |
|-----------|----------|
| `theme` | default/dark/light/custom |
| `message_color` | Цвет своих сообщений |
| `message_color_other` | Цвет чужих сообщений |
| `bubble_style` | modern/classic/rounded |
| `font_size` | small/medium/large |
| `time_format` | 12h/24h |

### Размеры пузырей сообщений

```css
/* Современный стиль */
.message-bubble {
  border-radius: 18px;
  padding: 8px 12px;
}

/* Классический стиль */
.message-bubble.classic {
  border-radius: 4px;
  padding: 6px 10px;
}

/* Округлый стиль */
.message-bubble.rounded {
  border-radius: 24px;
  padding: 10px 14px;
}
```

### Анимации

| Анимация | Описание |
|----------|----------|
| `message_animation` | Появление сообщения (slide/fade/pop) |
| `reaction_animation` | Анимация реакций (bounce/scale/none) |
| `typing_animation` | Индикатор печати (dots/wave/pulse) |
| `scroll_animation` | Прокрутка (smooth/instant/auto) |

### Эмодзи и стикеры

#### Наборы эмодзи

| Набор | Описание |
|-------|----------|
| Default | Стандартные Apple emoji |
| Twitter | Twemoji |
| Google | Noto Color Emoji |
| Samsung | Samsung emoji |
| Аниме | Аниме-стилизованные эмодзи |

#### Размеры

| Элемент | Размеры |
|---------|---------|
| Эмодзи в тексте | small (16px) / medium (20px) / large (24px) |
| Отдельные эмодзи | small (48px) / medium (64px) / large (80px) |
| Стикеры | small (180px) / medium (256px) / large (320px) |

---

## Приглашения и ссылки

### Ссылки-приглашения

#### Параметры ссылки

| Параметр | Описание |
|----------|----------|
| `name` | Название ссылки (для управления) |
| `invite_link` | Уникальный код ссылки |
| `creator` | Создатель ссылки |
| `created_at` | Дата создания |
| `expires_at` | Дата истечения (опционально) |
| `usage_limit` | Лимит использований (опционально) |
| `usage_count` | Текущее количество использований |
| `is_revoked` | Отозвана ли ссылка |
| `is_primary` | Основная ссылка группы |

#### Типы ссылок

```
Основная ссылка
├── Генерируется автоматически
├── Не имеет ограничений
├── Не истекает
└── Только одна на группу

Временные ссылки
├── Срок действия: 1 час / 1 день / 1 неделя / Кастомный
├── Лимит использований: 1 / 5 / 10 / 50 / 100 / Кастомный
└── Может быть отозвана в любой момент

Персональные ссылки
├── Создаются для конкретного пользователя
├── Одноразовые
├── Отслеживание кто пришёл
└── Автоматическое назначение роли
```

#### Права на создание ссылок

| Роль | Основная | Временные | Персональные |
|------|:--------:|:---------:|:------------:|
| Владелец | ✅ | ✅ | ✅ |
| Администратор | ❌ | ✅ | ✅ |
| Модератор | ❌ | ⚠️ | ❌ |
| Участник | ❌ | ⚠️ | ❌ |

**⚠️** — зависит от настройки группы `members_can_invite`

### Запросы на вступление

Для приватных групп:

```
Настройки запросов:
├── Кто может отправлять запросы
│   ├── Все
│   ├── Только контакты участников
│   └── Никто (только по приглашению)
├── Одобрение
│   ├── Автоматическое
│   ├── Одобрение администратором
│   └── Голосование администрации
└── Анкета при вступении
    ├── Опциональные вопросы
    └── Обязательные вопросы
```

#### Процесс вступления

1. Пользователь переходит по ссылке
2. Видит информацию о группе (название, описание, участники)
3. Заполняет анкету (если включена)
4. Ожидает одобрения (если требуется)
5. Получает уведомление о решении

---

## Архивирование и организация

### Папки чатов

#### Системные папки

| Папка | ID | Описание |
|-------|----|---------|
| Все чаты | 0 | Все чаты без исключения |
| Личные | -1 | Только личные чаты |
| Группы | -2 | Только групповые чаты |
| Каналы | -3 | Только каналы |
| Обсуждения | -4 | Группы обсуждений аниме |

#### Пользовательские папки

| Параметр | Описание |
|----------|----------|
| `name` | Название папки |
| `icon` | Эмодзи-иконка |
| `color` | Цвет папки |
| `included_chats` | Включённые чаты (явно) |
| `excluded_chats` | Исключённые чаты |
| `rules` | Правила автоматического добавления |

#### Правила папок

```yaml
Правила автоматического добавления:
  По типу:
    - include_private: Включить личные чаты
    - include_groups: Включить группы
    - include_channels: Включить каналы
    
  По состоянию:
    - include_archived: Включить архивные
    - include_muted: Включить заглушенные
    - include_read: Включить прочитанные
    
  По контенту:
    - include_anime_discussions: Обсуждения аниме
    - include_specific_anime: [anime_ids] - Конкретные аниме
    
  Логика:
    - match_all: Все условия должны совпасть (AND)
    - match_any: Хотя бы одно условие (OR)
```

### Архивирование

Архивированные чаты:
- Скрыты из основного списка
- Не показывают уведомления (кроме упоминаний)
- Перемещаются в папку "Архив"
- Могут быть распакованы в любой момент

Автоматическое архивирование:
- Чаты без активности более N дней
- Настройка периода: 1 неделя / 1 месяц / 3 месяца / Никогда

### Закрепление

| Ограничение | Значение |
|-------------|----------|
| Максимум закреплённых чатов | 5 |
| Порядок | Ручная сортировка |

### Пометки и теги

```yaml
Теги для чатов:
  Цветовые метки:
    - 🔴 Красный (важное)
    - 🟠 Оранжевый (работа)
    - 🟡 Жёлтый (личное)
    - 🟢 Зелёный (друзья)
    - 🔵 Синий (учёба)
    - 🟣 Фиолетовый (развлечения)
    
  Кастомные теги:
    - Название тега
    - Цвет
    - Эмодзи
    - До 20 тегов на пользователя
```

---

## Безопасность

### Двухфакторная аутентификация

Для критических действий требуется 2FA:

- Передача владения группой
- Удаление группы
- Блокировка администраторов
- Изменение глобальных настроек

### Журнал безопасности

Записываются все критические действия:

| Событие | Данные |
|---------|--------|
| Вход в аккаунт | IP, устройство, местоположение |
| Изменение пароля | IP, дата |
- Новая авторизация | Устройство, браузер, ОС |
| Подозрительная активность | Тип активности, детали |

### Защита от спама

#### Ограничения для новых пользователей

| Ограничение | Длительность |
|-------------|--------------|
| Нельзя отправлять ссылки | Первые 24 часа |
| Медленный режим x2 | Первые 3 дня |
| Нельзя отправлять медиа | Первые 24 часа |
| Ограничение на создание групп | До 100 сообщений в личных чатах |

#### Защита от ботов

- hCaptcha при регистрации
- hCaptcha при вступлении в группу (опционально)
- Лимит приглашений в день (до 50)
- Проверка номеров телефонов (опционально)

### Шифрование

| Тип | Описание |
|-----|----------|
| Транспортное | TLS 1.3 для всех соединений |
| Хранение | Шифрование медиафайлов в S3 |
- Секретные чаты | E2E шифрование (планируется) |

---

## WebSocket события

### События чата

```yaml
Сообщения:
  new_message:
    - message: object
    - chat_id: number
    
  message_edited:
    - message_id: number
    - new_text: string
    
  message_deleted:
    - message_id: number
    - for_everyone: boolean
    
  messages_read:
    - message_ids: number[]
    - user_id: number
    
  reaction_added:
    - message_id: number
    - emoji: string
    - user_id: number
    
  reaction_removed:
    - message_id: number
    - emoji: string
    - user_id: number

Пользователи:
  user_typing:
    - user_id: number
    - is_typing: boolean
    
  user_online:
    - user_id: number
    - is_online: boolean
    
  user_joined:
    - user: object
    - chat_id: number
    
  user_left:
    - user_id: number
    - chat_id: number

Группа:
  chat_updated:
    - chat_id: number
    - changes: object
    
  role_changed:
    - user_id: number
    - new_role: object
    
  settings_changed:
    - setting: string
    - new_value: any
```

### Глобальные события

```yaml
Уведомления:
  notification:
    - type: string
    - title: string
    - body: string
    - data: object
    
  unread_count_updated:
    - chat_id: number
    - count: number
    
  mention:
    - message: object
    - chat_id: number

Синхронизация:
  chat_created:
    - chat: object
    
  chat_deleted:
    - chat_id: number
    
  contact_online:
    - user_id: number
    - is_online: boolean
```

---

## API Endpoints

### Личные чаты

```
GET    /api/social/private-chats/                           # Список чатов
POST   /api/social/private-chats/                           # Создать чат
GET    /api/social/private-chats/{id}/                      # Детали чата
DELETE /api/social/private-chats/{id}/                      # Удалить чат

GET    /api/social/private-chats/{id}/messages/             # Сообщения
POST   /api/social/private-chats/{id}/messages/             # Отправить сообщение

POST   /api/social/private-chats/{id}/update_settings/      # Обновить настройки
POST   /api/social/private-chats/{id}/mark_as_read/         # Пометить как прочитанное
POST   /api/social/private-chats/{id}/clear_history/        # Очистить историю
POST   /api/social/private-chats/{id}/block/                # Заблокировать
POST   /api/social/private-chats/{id}/unblock/              # Разблокировать

PUT    /api/social/private-chats/{id}/settings/             # Персональные настройки
```

### Групповые чаты

```
GET    /api/social/group-chats/                             # Список групп
POST   /api/social/group-chats/create/                      # Создать группу
GET    /api/social/group-chats/{id}/                        # Детали группы
PATCH  /api/social/group-chats/{id}/                        # Обновить группу
DELETE /api/social/group-chats/{id}/                        # Удалить группу

GET    /api/social/group-chats/{id}/members/                # Участники
POST   /api/social/group-chats/{id}/invite_user/            # Пригласить
POST   /api/social/group-chats/{id}/remove_member/          # Исключить
POST   /api/social/group-chats/{id}/ban_user/               # Забанить
POST   /api/social/group-chats/{id}/unban_user/             # Разбанить
POST   /api/social/group-chats/{id}/leave_chat/             # Покинуть группу

GET    /api/social/group-chats/{id}/roles/                  # Роли
POST   /api/social/group-chats/{id}/roles/                  # Создать роль
PATCH  /api/social/group-chats/{id}/roles/{role_id}/        # Обновить роль
DELETE /api/social/group-chats/{id}/roles/{role_id}/        # Удалить роль

POST   /api/social/group-chats/{id}/set_member_role/        # Назначить роль

GET    /api/social/group-chats/{id}/invite-links/           # Ссылки-приглашения
POST   /api/social/group-chats/{id}/invite-links/           # Создать ссылку
DELETE /api/social/group-chats/{id}/invite-links/{code}/    # Отозвать ссылку

GET    /api/social/group-chats/{id}/admin-logs/             # Журнал действий

PUT    /api/social/group-chats/{id}/settings/               # Настройки группы
PATCH  /api/social/group-chats/{id}/update_member_settings/ # Настройки участника

GET    /api/social/group-chats/{id}/banned-users/           # Забаненные
GET    /api/social/group-chats/{id}/restricted-users/       # Ограниченные
```

### Сообщения

```
GET    /api/social/messages/{id}/                           # Детали сообщения
POST   /api/social/messages/                                # Создать сообщение
PATCH  /api/social/messages/{id}/                           # Редактировать
DELETE /api/social/messages/{id}/                           # Удалить

POST   /api/social/messages/{id}/read/                      # Прочитано
POST   /api/social/messages/{id}/react/                     # Добавить реакцию
POST   /api/social/messages/{id}/pin/                       # Закрепить
POST   /api/social/messages/{id}/unpin/                     # Открепить
POST   /api/social/messages/{id}/forward/                   # Переслать
```

### Папки

```
GET    /api/social/chat-folders/                            # Список папок
POST   /api/social/chat-folders/                            # Создать папку
PATCH  /api/social/chat-folders/{id}/                       # Обновить папку
DELETE /api/social/chat-folders/{id}/                       # Удалить папку
POST   /api/social/chat-folders/reorder/                    # Изменить порядок
```

### Кастомизация

```
GET    /api/social/chat-settings/wallpapers/                # Доступные обои
POST   /api/social/chat-settings/wallpapers/                # Загрузить обои
PUT    /api/social/chat-settings/{chat_id}/wallpaper/       # Установить обои
DELETE /api/social/chat-settings/{chat_id}/wallpaper/       # Сбросить обои

GET    /api/social/chat-settings/themes/                    # Доступные темы
PUT    /api/social/chat-settings/{chat_id}/theme/           # Установить тему
```

---

## Заключение

Данная система настроек обеспечивает:

1. **Гибкость** — каждый пользователь может настроить чаты под себя
2. **Безопасность** — гранулярные права и модерация
3. **Масштабируемость** — поддержка до 200,000 участников в группе
4. **Кастомизация** — обои, темы, звуки, эмодзи
5. **Модерация** — полный набор инструментов для управления сообществом








База данных и хранение настроек
Модели данных
Личные чаты
python
class PrivateChat(models.Model):
    """Личный чат между двумя пользователями"""
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_initiated')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_received')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('user1', 'user2')
        indexes = [
            models.Index(fields=['user1', 'updated_at']),
            models.Index(fields=['user2', 'updated_at']),
        ]

class PrivateChatSettings(models.Model):
    """Персональные настройки пользователя для конкретного личного чата"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat = models.ForeignKey(PrivateChat, on_delete=models.CASCADE, related_name='user_settings')
    
    # Основные настройки
    custom_name = models.CharField(max_length=255, blank=True)
    custom_avatar = models.ImageField(upload_to='chat_avatars/', null=True, blank=True)
    
    # Уведомления
    notifications = models.BooleanField(default=True)
    muted_until = models.DateTimeField(null=True, blank=True)
    notification_sound = models.CharField(max_length=50, default='default')
    vibration = models.CharField(max_length=20, default='default')
    show_preview = models.BooleanField(default=True)
    popup_notifications = models.BooleanField(default=True)
    
    # Организация
    archived = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False)
    folder = models.ForeignKey('ChatFolder', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.JSONField(default=list)  # [{"name": "важное", "color": "#FF0000"}]
    
    # Блокировка
    is_blocked = models.BooleanField(default=False)
    blocked_at = models.DateTimeField(null=True, blank=True)
    block_reason = models.CharField(max_length=255, blank=True)
    
    # Кастомизация
    wallpaper = models.ForeignKey('ChatWallpaper', on_delete=models.SET_NULL, null=True, blank=True)
    theme = models.CharField(max_length=50, default='default')
    font_size = models.CharField(max_length=20, default='medium')
    bubble_style = models.CharField(max_length=20, default='modern')
    
    # Автоудаление
    auto_delete_messages = models.BooleanField(default=False)
    auto_delete_days = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'chat')
Групповые чаты
python
class GroupChat(models.Model):
    """Групповой чат"""
    CHAT_TYPES = [
        ('group', 'Группа'),
        ('anime_discussion', 'Обсуждение аниме'),
        ('channel', 'Канал'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, max_length=5000)
    avatar = models.ImageField(upload_to='group_avatars/', null=True, blank=True)
    emoji_status = models.CharField(max_length=10, blank=True)
    
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPES, default='group')
    anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True)
    
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name='owned_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Приватность
    is_public = models.BooleanField(default=False)
    join_to_send = models.BooleanField(default=True)
    restrict_saving_content = models.BooleanField(default=False)
    has_hidden_members = models.BooleanField(default=False)
    
    # Настройки сообщений
    slow_mode_delay = models.IntegerField(default=0)  # секунды между сообщениями
    allow_media = models.BooleanField(default=True)
    allow_stickers = models.BooleanField(default=True)
    allow_gifs = models.BooleanField(default=True)
    allow_polls = models.BooleanField(default=True)
    allow_links = models.BooleanField(default=True)
    allow_voice = models.BooleanField(default=True)
    allow_video_messages = models.BooleanField(default=True)
    
    # Модерация
    auto_spam_filter = models.BooleanField(default=False)
    flood_threshold = models.IntegerField(default=5)  # сообщений за...
    flood_timeframe = models.IntegerField(default=5)  # ...секунд
    flood_action = models.CharField(max_length=20, default='mute')
    flood_action_duration = models.IntegerField(default=300)  # секунд
    
    # Лимиты
    max_members = models.IntegerField(default=200000)
    
    # Статистика
    members_count = models.IntegerField(default=0)
    messages_count = models.BigIntegerField(default=0)
    
    # Приглашения
    primary_invite_link = models.CharField(max_length=100, unique=True)
    members_can_invite = models.BooleanField(default=False)
    
    # Глобальная ссылка-приглашение (автоматическая)
    invite_hash = models.CharField(max_length=16, unique=True)
    
    last_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['chat_type', '-created_at']),
        ]

class GroupChatSettings(models.Model):
    """Общие настройки группы (кэш)"""
    group = models.OneToOneField(GroupChat, on_delete=models.CASCADE, primary_key=True, related_name='settings')
    
    # Кэшированные настройки для быстрого доступа
    slow_mode_enabled = models.BooleanField(default=False)
    media_allowed = models.BooleanField(default=True)
    links_allowed = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
Роли и разрешения
python
class GroupRole(models.Model):
    """Роль в группе"""
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#808080')  # HEX цвет
    icon = models.CharField(max_length=10, blank=True)  # эмодзи
    level = models.IntegerField(default=1)  # 1-5, где 5 - самый высокий
    custom_title = models.CharField(max_length=100, blank=True)
    
    # Права (JSON для гибкости)
    permissions = models.JSONField(default=dict)
    
    is_default = models.BooleanField(default=False)  # роль по умолчанию для новых участников
    is_admin = models.BooleanField(default=False)  # административная роль
    is_moderator = models.BooleanField(default=False)  # модераторская роль
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('group', 'name')

class GroupMembership(models.Model):
    """Участие пользователя в группе"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='memberships')
    role = models.ForeignKey(GroupRole, on_delete=models.SET_NULL, null=True, blank=True)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    last_message_id = models.IntegerField(default=0)
    
    # Персональные настройки для этой группы
    notifications = models.BooleanField(default=True)
    muted_until = models.DateTimeField(null=True, blank=True)
    pinned = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    custom_wallpaper = models.ForeignKey('ChatWallpaper', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Статистика
    messages_count = models.IntegerField(default=0)
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'group')
        indexes = [
            models.Index(fields=['user', '-last_active']),
            models.Index(fields=['group', 'role']),
        ]
Ограничения и блокировки
python
class GroupRestriction(models.Model):
    """Ограничение на участника группы"""
    RESTRICTION_TYPES = [
        ('read_only', 'Только чтение'),
        ('no_media', 'Без медиа'),
        ('no_stickers', 'Без стикеров'),
        ('no_links', 'Без ссылок'),
        ('no_voice', 'Без голосовых'),
        ('custom', 'Кастомное'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE)
    restriction_type = models.CharField(max_length=20, choices=RESTRICTION_TYPES)
    
    reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # null = постоянно
    
    class Meta:
        unique_together = ('user', 'group', 'restriction_type')

class GroupBan(models.Model):
    """Блокировка пользователя в группе"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE)
    
    reason = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # При блокировке можно удалить сообщения пользователя
    delete_messages = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'group')
Приглашения
python
class InviteLink(models.Model):
    """Ссылка-приглашение в группу"""
    LINK_TYPES = [
        ('primary', 'Основная'),
        ('temporary', 'Временная'),
        ('personal', 'Персональная'),
    ]
    
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='invite_links')
    name = models.CharField(max_length=100, blank=True)
    code = models.CharField(max_length=16, unique=True)
    link_type = models.CharField(max_length=20, choices=LINK_TYPES, default='temporary')
    
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    expires_at = models.DateTimeField(null=True, blank=True)
    usage_limit = models.IntegerField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    is_revoked = models.BooleanField(default=False)
    
    # Для персональных ссылок
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    auto_role = models.ForeignKey(GroupRole, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['group', 'link_type']),
        ]
Папки и организация
python
class ChatFolder(models.Model):
    """Папка для организации чатов"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_folders')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, blank=True)
    color = models.CharField(max_length=7, default='#808080')
    
    # Порядок отображения
    order = models.IntegerField(default=0)
    
    # Правила автоматического добавления
    include_rules = models.JSONField(default=dict)  # {"types": ["private"], "archived": False}
    exclude_rules = models.JSONField(default=dict)
    match_logic = models.CharField(max_length=10, choices=[('all', 'AND'), ('any', 'OR')], default='any')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ('user', 'name')

class ChatFolderItem(models.Model):
    """Чат в папке (явное добавление)"""
    folder = models.ForeignKey(ChatFolder, on_delete=models.CASCADE, related_name='items')
    chat_type = models.CharField(max_length=20)  # 'private' или 'group'
    chat_id = models.IntegerField()
    
    class Meta:
        unique_together = ('folder', 'chat_type', 'chat_id')
Кастомизация
python
class ChatWallpaper(models.Model):
    """Обои для чатов"""
    WALLPAPER_TYPES = [
        ('solid', 'Сплошной цвет'),
        ('gradient', 'Градиент'),
        ('pattern', 'Паттерн'),
        ('image', 'Изображение'),
    ]
    
    name = models.CharField(max_length=100)
    wallpaper_type = models.CharField(max_length=20, choices=WALLPAPER_TYPES)
    
    # Для solid и gradient
    color1 = models.CharField(max_length=7, blank=True)
    color2 = models.CharField(max_length=7, blank=True)
    
    # Для image
    image = models.ImageField(upload_to='wallpapers/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='wallpapers/thumbnails/', null=True, blank=True)
    
    # Параметры отображения
    intensity = models.IntegerField(default=100)  # 0-100%
    blur = models.IntegerField(default=0)  # 0-100%
    motion = models.CharField(max_length=20, choices=[('none', 'Нет'), ('parallax', 'Параллакс')], default='none')
    
    # Метаданные
    is_official = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_official', 'name']

class ChatTheme(models.Model):
    """Тема оформления чата"""
    name = models.CharField(max_length=100)
    
    # Цвета
    primary_color = models.CharField(max_length=7)
    secondary_color = models.CharField(max_length=7)
    background_color = models.CharField(max_length=7)
    message_color_mine = models.CharField(max_length=7)
    message_color_other = models.CharField(max_length=7)
    
    # Стили
    bubble_style = models.CharField(max_length=20, default='modern')
    font_family = models.CharField(max_length=50, default='system')
    font_size = models.CharField(max_length=20, default='medium')
    
    # Анимации
    message_animation = models.CharField(max_length=20, default='slide')
    reaction_animation = models.CharField(max_length=20, default='bounce')
    typing_animation = models.CharField(max_length=20, default='dots')
    
    is_official = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
Журналы и аудит
python
class AdminLog(models.Model):
    """Журнал действий администраторов в группе"""
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='admin_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    action_type = models.CharField(max_length=50)
    details = models.JSONField(default=dict)
    
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['group', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

class SecurityLog(models.Model):
    """Журнал безопасности"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    
    additional_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
Фундаментальные фичи
1. Система кэширования настроек
Для оптимизации производительности все настройки кэшируются:

python
class SettingsCache:
    """Кэш настроек для быстрого доступа"""
    
    @staticmethod
    def get_chat_settings(user_id, chat_type, chat_id):
        cache_key = f"chat_settings:{user_id}:{chat_type}:{chat_id}"
        settings = cache.get(cache_key)
        
        if not settings:
            settings = self._load_from_db(user_id, chat_type, chat_id)
            cache.set(cache_key, settings, timeout=300)  # 5 минут
        
        return settings
    
    @staticmethod
    def invalidate(user_id, chat_type, chat_id):
        cache_key = f"chat_settings:{user_id}:{chat_type}:{chat_id}"
        cache.delete(cache_key)
2. Система прав (Permission System)
python
class PermissionChecker:
    """Проверка прав доступа"""
    
    def __init__(self, user, group):
        self.user = user
        self.group = group
        self.membership = GroupMembership.objects.filter(user=user, group=group).first()
    
    def has_permission(self, permission_name):
        if not self.membership:
            return False
        
        if self.membership.role:
            return self.membership.role.permissions.get(permission_name, False)
        
        # Проверка прав по умолчанию
        default_permissions = {
            'can_send_messages': True,
            'can_send_media': self.group.allow_media,
            'can_send_links': self.group.allow_links,
            # ...
        }
        
        return default_permissions.get(permission_name, False)
    
    def has_any_permission(self, permission_names):
        return any(self.has_permission(p) for p in permission_names)
    
    def has_all_permissions(self, permission_names):
        return all(self.has_permission(p) for p in permission_names)
3. Система уведомлений в реальном времени
python
class NotificationService:
    """Сервис отправки уведомлений"""
    
    @staticmethod
    def send_to_chat(chat, event_type, data, exclude_users=None):
        """Отправить уведомление всем участникам чата"""
        users = chat.get_all_users().exclude(id__in=exclude_users or [])
        
        for user in users:
            settings = SettingsCache.get_chat_settings(user.id, chat.type, chat.id)
            
            if settings.get('notifications', True):
                # Проверка на заглушенность
                if settings.get('muted_until') and settings['muted_until'] > timezone.now():
                    continue
                
                # Отправка через WebSocket
                channel_layer.group_send(
                    f"user_{user.id}",
                    {
                        'type': 'chat_notification',
                        'event': event_type,
                        'data': data,
                        'chat_id': chat.id
                    }
                )
    
    @staticmethod
    def send_to_user(user_id, event_type, data):
        """Отправить уведомление конкретному пользователю"""
        channel_layer.group_send(
            f"user_{user_id}",
            {
                'type': 'chat_notification',
                'event': event_type,
                'data': data
            }
        )
4. Система ограничений (Rate Limiting)
python
class RateLimiter:
    """Ограничение частоты действий"""
    
    def __init__(self, user_id, action_type):
        self.user_id = user_id
        self.action_type = action_type
        self.redis_key = f"rate_limit:{user_id}:{action_type}"
    
    def check(self, limit=10, period=60):
        """Проверка, не превышен ли лимит"""
        current = cache.get(self.redis_key, 0)
        
        if current >= limit:
            return False
        
        # Инкремент с истечением
        cache.incr(self.redis_key)
        cache.expire(self.redis_key, period)
        
        return True
    
    def get_remaining(self, limit=10):
        """Получить оставшееся количество"""
        current = cache.get(self.redis_key, 0)
        return max(0, limit - current)
5. Система анти-спам
python
class AntiSpamService:
    """Защита от спама"""
    
    SPAM_RULES = {
        'flood': {
            'threshold': 5,  # сообщений
            'timeframe': 5,   # секунд
            'action': 'mute',
            'duration': 300   # 5 минут
        },
        'links': {
            'threshold': 3,   # ссылок
            'timeframe': 60,  # секунд
            'action': 'restrict_links',
            'duration': 3600  # 1 час
        },
        'caps': {
            'threshold': 70,  # процент заглавных
            'min_length': 10, # минимальная длина
            'action': 'delete'
        }
    }
    
    @staticmethod
    def check_message(user, group, message_text):
        violations = []
        
        # Проверка на флуд
        recent_count = Message.objects.filter(
            sender=user,
            chat=group,
            created_at__gte=timezone.now() - timedelta(seconds=5)
        ).count()
        
        if recent_count >= 5:
            violations.append('flood')
        
        # Проверка на ссылки
        if 'http' in message_text:
            link_count = Message.objects.filter(
                sender=user,
                chat=group,
                text__contains='http',
                created_at__gte=timezone.now() - timedelta(seconds=60)
            ).count()
            
            if link_count >= 3:
                violations.append('links')
        
        # Проверка на капс
        if len(message_text) > 10:
            caps_ratio = sum(1 for c in message_text if c.isupper()) / len(message_text)
            if caps_ratio > 0.7:
                violations.append('caps')
        
        return violations
6. Система версионирования настроек
python
class SettingsVersioning:
    """Версионирование настроек для синхронизации"""
    
    @staticmethod
    def get_version(user_id):
        """Получить текущую версию настроек пользователя"""
        return cache.get(f"settings_version:{user_id}", 1)
    
    @staticmethod
    def increment_version(user_id):
        """Увеличить версию при изменении настроек"""
        cache.incr(f"settings_version:{user_id}")
    
    @staticmethod
    def sync_needed(user_id, client_version):
        """Проверить, нужна ли синхронизация"""
        server_version = SettingsVersioning.get_version(user_id)
        return server_version != client_version
7. Система очередей для массовых операций
python
class ChatTaskQueue:
    """Очередь для массовых операций с чатами"""
    
    @staticmethod
    def add_bulk_members(group_id, user_ids, role_id=None):
        """Добавление множества участников в фоне"""
        task = {
            'type': 'add_members',
            'group_id': group_id,
            'user_ids': user_ids,
            'role_id': role_id,
            'created_at': timezone.now().isoformat()
        }
        
        # Отправка в очередь Celery
        process_bulk_members.delay(task)
    
    @staticmethod
    def remove_old_messages(group_id, days=30):
        """Удаление старых сообщений"""
        task = {
            'type': 'cleanup_messages',
            'group_id': group_id,
            'days': days
        }
        
        cleanup_messages.delay(task)
Расширенные фичи
1. Умные уведомления
python
class SmartNotifications:
    """Интеллектуальные уведомления на основе активности"""
    
    @staticmethod
    def should_notify(user, chat, message):
        """Определить, нужно ли отправлять уведомление"""
        
        # Пользователь сейчас в чате
        if user in chat.active_users():
            return False
        
        # Сообщение от заглушенного пользователя
        if message.sender in user.muted_users.all():
            return False
        
        # Упоминание пользователя
        if f"@{user.username}" in message.text:
            return True
        
        # Время последнего посещения
        membership = GroupMembership.objects.get(user=user, group=chat)
        if message.created_at > membership.last_read_at:
            return True
        
        return False
2. Сборка мусора (Cleanup Service)
python
class ChatCleanupService:
    """Автоматическая очистка старых данных"""
    
    @staticmethod
    def cleanup_old_messages():
        """Удаление сообщений старше N дней"""
        days = settings.CHAT_MESSAGE_RETENTION_DAYS
        cutoff = timezone.now() - timedelta(days=days)
        
        # Удаление сообщений (с проверкой на закреплённые)
        Message.objects.filter(
            created_at__lt=cutoff,
            is_pinned=False
        ).delete()
    
    @staticmethod
    def cleanup_expired_bans():
        """Снятие истёкших блокировок"""
        GroupBan.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
    
    @staticmethod
    def cleanup_old_invites():
        """Удаление истёкших приглашений"""
        InviteLink.objects.filter(
            expires_at__lt=timezone.now()
        ).update(is_revoked=True)
3. Экспорт и импорт настроек
python
class SettingsExport:
    """Экспорт/импорт настроек чатов"""
    
    @staticmethod
    def export_user_settings(user):
        """Экспорт всех настроек пользователя"""
        data = {
            'global': {
                'notifications': user.notification_settings,
                'privacy': user.privacy_settings,
            },
            'folders': [],
            'chats': []
        }
        
        # Папки
        for folder in user.chat_folders.all():
            data['folders'].append({
                'name': folder.name,
                'icon': folder.icon,
                'color': folder.color,
                'rules': folder.include_rules
            })
        
        # Настройки чатов
        for settings in PrivateChatSettings.objects.filter(user=user):
            data['chats'].append({
                'type': 'private',
                'user_id': settings.chat.user2.id if settings.chat.user1 == user else settings.chat.user1.id,
                'settings': {
                    'custom_name': settings.custom_name,
                    'notifications': settings.notifications,
                    'archived': settings.archived,
                    'pinned': settings.pinned,
                    'wallpaper_id': settings.wallpaper_id
                }
            })
        
        return data
    
    @staticmethod
    def import_user_settings(user, data):
        """Импорт настроек пользователя"""
        # Применение настроек с проверкой прав
        pass
4. Аналитика чатов
python
class ChatAnalytics:
    """Сбор статистики по чатам"""
    
    @staticmethod
    def get_chat_stats(group):
        """Получить статистику группы"""
        return {
            'total_messages': group.messages_count,
            'active_users': group.memberships.filter(last_active__gte=timezone.now() - timedelta(days=7)).count(),
            'messages_per_day': Message.objects.filter(
                chat=group,
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count() / 30,
            'top_active_users': group.memberships.order_by('-messages_count')[:10].values('user__username', 'messages_count'),
            'peak_hours': Message.objects.filter(chat=group).extra(
                {'hour': 'extract(hour from created_at)'}
            ).values('hour').annotate(count=Count('id')).order_by('-count')[:5]
        }
5. Резервное копирование
python
class ChatBackup:
    """Система бэкапов чатов"""
    
    @staticmethod
    def create_backup(chat, user):
        """Создать резервную копию чата"""
        if not user.has_permission('can_backup_chat'):
            raise PermissionError
        
        backup = {
            'metadata': {
                'chat_id': chat.id,
                'chat_name': chat.name,
                'created_at': timezone.now().isoformat(),
                'message_count': chat.messages_count,
                'member_count': chat.members_count
            },
            'settings': {
                'name': chat.name,
                'description': chat.description,
                'is_public': chat.is_public,
                'slow_mode_delay': chat.slow_mode_delay,
                'allow_media': chat.allow_media
            },
            'messages': []
        }
        
        # Сообщения (последние 1000)
        for message in Message.objects.filter(chat=chat).order_by('-created_at')[:1000]:
            backup['messages'].append({
                'user': message.sender.username,
                'text': message.text,
                'created_at': message.created_at.isoformat(),
                'attachments': message.attachments
            })
        
        return backup






---

*Документация v1.0 | AnimeCore Chat System*
