# FEATURES_CATALOG — Home, Feed, Anime Catalog & Anime Page

## 1. Home Page (`/`)

Персонализированная стартовая точка для авторизованного пользователя.

### Header
- User greeting + current date
- Quick search button, create post button, notification badge

### Section: "Продолжить просмотр"
- Anime with status "В процессе", sorted by last watched (most recent first), up to 10
- Card: poster, title, current episode ("5 из 24 эп."), progress bar, "Продолжить" → last episode, quick "Отметить просмотренным"
- Empty state: "Вы ещё ничего не начали смотреть" + "Перейти в каталог"

### Section: "Пересмотреть"
- Completed anime: score ≥ 8, or in "Любимое", or classic titles watched long ago — random selection, up to 6
- Card: poster, title, user score, "Смотреть заново" → ep 1, "В избранное"
- Empty state: "Здесь появятся аниме, которые вы захотели пересмотреть" + "Посмотреть любимое"

### Section: "Рекомендации для вас"
- Based on: watch history + ratings + similar users + season releases matching taste, up to 12 (3-4 per row)
- Card: poster, title, year, first 2-3 genres, "Вам понравится на X%", "В коллекцию", "Смотреть сейчас"
- Empty state: "Оцените больше аниме" + "Перейти в каталог"

### Optional Sections
- **"Популярное сейчас"** — daily trending
- **"Новинки сезона"** — high-rated current-season anime
- **"Смотрят друзья"** — friends currently watching
- **"Обсуждаемое в сообществах"** — posts from user's groups

---

## 2. Activity Feed (`/feed`)

### Post Types
`text` | `images (≤10)` | `video (≤5min, 100MB)` | `playlist card` | `anime card` | `shorts` | `repost` | `system`

### Post Elements
- Author avatar + name (→ profile), group name (if from group), timestamp
- Post menu: edit, delete, pin, report, save, hide, "not interested", share, copy link
- Title (optional), text (truncated to 500 chars + "Показать полностью")
- Media, attached content (anime/playlist card)
- Spoiler block (blurred + "Показать спойлер")
- Counters + buttons: like, dislike, comment, repost, bookmark

### Post Interactions
| Action | Behavior |
|---|---|
| Like | Toggle; notify author on first like only |
| Dislike | Toggle; no notification |
| Comment | Create, reply, edit (10 min window), delete |
| Repost | Choose destination (feed / group / DM) + optional comment |
| Bookmark | Saved to "Сохранённое" |
| Report | Reason picker → sent to moderators |
| Edit | Author only, 5 min window; adds "отредактировано" label |
| Delete | Author + moderators; replaces text with "[сообщение удалено]" |
| Pin | Author only, on own profile |

### Feed Algorithm
- Subscriptions 70% / user's groups 15% / recommended 10% / promoted 5%
- Sorted by publish time with weight
- Infinite scroll, real-time via WebSocket, new post counter

---

## 3. Anime Catalog (`/anime`)

### Tabs
`Все` | `Анонсы` | `Онгоинги` | `Рекомендации` | `Топ` | `Сезонные`

### Filters

**Basic:**
- Title search (ru/en/jp) — autocomplete at 3+ chars
- Genres — multi-select with AND/OR logic
- Year range
- Status: ongoing / finished / announced
- Type: TV / film / OVA / ONA / special
- Score range 0–10

**Advanced:**
- Studio, original author, director, composer — text/multi-select
- Episode count range
- Episode duration range (minutes)
- Season + year picker
- Has dubbing: yes/no
- Age rating: G / PG / PG-13 / R / R+
- Country: Japan / China / Korea
- Date added range
- In my collection: yes/no
- Has my rating: yes/no
- Not in my collection: yes/no

### Sort Options
Popularity · Score · Release date · Title A-Z · Rating count · Date added (each: asc/desc)

### Display
- Modes: grid (default) / list / compact
- Page size: 20 / 50 / 100 / 200
- Pagination or infinite load
- Filter state persisted in URL

### Anime Card (in catalog)
- Poster, title (ru → en fallback), year, type, episode count, score
- Hover overlay: "В избранное", "В плейлист", "Напомнить"
- Collection status icon, watch progress bar (if in-progress)
- First 2-3 genres

---

## 4. Anime Detail Page (`/anime/:id`)

### Header
- Large poster, all title variants (ru/en/jp)
- Rating + vote count
- Action buttons: В избранное · В плейлист · В коллекцию · Напомнить · Поделиться

### Info Block
Year · Status · Type · Episodes · Episode duration · Studio · Genres (clickable) · Age rating · Original author · Director · Composer

### Media
- Embedded trailer player
- Screenshot gallery (click to enlarge)

### Tabs

**Описание** — full synopsis, spoiler toggle, related works (manga/LN)

**Где смотреть**
- Add link form
- Legal sources list
- User links: source name, available episodes, status (working / unofficial / blocked / broken), visit button, report button, bookmark

**Озвучки**
- "Добавить озвучку" button
- Per studio: name, voice actors with roles, dubbed episodes, contacts (Telegram/VK/site), "Смотреть эту озвучку", "Подписаться на студию"

**Отзывы**
- "Написать отзыв" button
- Sort: by usefulness / newest / by score
- Review card: author avatar+name+date, score, text, spoiler label, like/dislike counters, reply + menu

**Персонажи**
- Character grid: image, name, role, description
- JP and RU voice actors per character
- Role filter

**Связанное**
Prequels · Sequels · Spin-offs · Alternative versions · Summaries

**Статистика**
- Score distribution histogram
- Popularity over time chart
- Friends who watched

---

## 5. My Collection (`/collection`)

### Statuses
`В процессе` | `Просмотрено` | `Запланировано` | `Отложено` | `Брошено` | `Любимое`

### Per-Anime Display
Status · Progress (for in-progress) · Score (for completed) · Date added · Note (if any)  
Actions: change status / rate / delete

### Add to Collection Modal
Fields: status picker, current episode (for in-progress), score (for completed), note, "Add to favorites" checkbox

### Auto-Update Logic
- Clicking a watch link adds anime to "В процессе" if not already tracked
- Episode watch updates progress count
- Reaching final episode moves to "Просмотрено"
