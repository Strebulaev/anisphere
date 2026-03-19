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
| Repost | See **Repost Flow** below |
| Bookmark | Saved to "Избранное" tab |
| Report | Reason picker → sent to moderators |
| Edit | Author only, 5 min window; adds "отредактировано" label |
| Delete | Author + moderators; replaces text with "[сообщение удалено]" |
| Pin | Author only, on own profile |
| Not interested | Hides post; added to "Не интересно" tab |

### Repost Flow

Clicking the repost button opens a **Repost Modal** with three destination options and an optional comment field.

| Destination | Behaviour |
|---|---|
| **Моя лента** | Creates a new `kind=repost` post for the current user; appears in followers' feeds |
| **Группа** | Group picker (groups where user is member); posts as repost in group feed |
| **Сообщение** | Chat/user search; sends the post as a **Post card** message into a personal or group chat |

Repost post structure: `kind=repost`, `original_post` FK, `content` = optional comment. Rendered as reposter comment + embedded original post card.
`repost_count` on the original post increments for all destinations.

**API:**
```
POST /api/social/posts/{id}/repost/
  body: { destination: 'feed' | 'group' | 'chat', target_id?: uuid, comment?: string }
```

### Feed Tabs

The `/feed` page has a tab bar:

| Tab | Content |
|---|---|
| Для вас | Default algorithmic feed |
| Подписки | Posts only from followed users and groups |
| Избранное | Bookmarked posts, sorted by bookmark date newest-first; keyword search bar; empty state: "Вы ещё не сохранили ни одного поста" |
| Закреплённые посты | Posts pinned by the current user on their profile; sorted by pin order; each post can be unpinned from here; empty state: "У вас нет закреплённых постов" |
| Не интересно | Posts hidden from feed; sorted by hide date newest-first; each entry has "Восстановить" button to undo; empty state: "Здесь появятся посты, которые вы отметили неинтересными" |

**Supporting models:**
- `PostBookmark`: `user` FK, `post` FK, `created_at`
- `PostPin`: `user` FK, `post` FK, `order` IntegerField
- `PostHide`: `user` FK, `post` FK, `created_at`

**API:**
```
GET  /api/social/feed/?tab=bookmarks
GET  /api/social/feed/?tab=pinned
GET  /api/social/feed/?tab=hidden
POST /api/social/posts/{id}/bookmark/     # Toggle
POST /api/social/posts/{id}/pin/          # Toggle
POST /api/social/posts/{id}/hide/         # Mark not interested
DELETE /api/social/posts/{id}/hide/       # Undo
```

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

### Statistics Panel

The `/collection` page includes a **Statistics** section with the following data, all computed from the user's `UserCollection` and `WatchProgress` records.

#### Watch Time

| Metric | Calculation |
|---|---|
| Всего просмотрено часов | Sum of `(episodes_watched × avg_episode_duration)` across all anime with status `completed` or `in_progress` |
| Осталось досмотреть (часов) | Sum of `(remaining_episodes × avg_episode_duration)` for anime with status `in_progress` |
| Среднее в день (за последние 30 дней) | Hours watched in last 30 days ÷ 30 |

`avg_episode_duration` is taken from the `Anime` model field `episode_duration` (minutes); falls back to 24 min if null.

**Display format:** "X ч Y мин" (e.g. "142 ч 35 мин"); for large values also show days ("5 д 22 ч").

#### Episodes

| Metric | Value |
|---|---|
| Серий просмотрено | Sum of `progress` (episodes watched) across all statuses |
| Серий осталось | Sum of `(episodes_total − progress)` for `in_progress` anime |
| Серий запланировано | Sum of `episodes_total` for `planned` anime |

Episode counts must use the anime's actual `episodes` field (total planned) and `episodes_aired` for ongoing titles, never show 0/0 or null — display "?" when unknown.

#### Collection Breakdown

Counts per status with percentage of total:

| Status | Count | % of total |
|---|---|---|
| В процессе | N | X% |
| Просмотрено | N | X% |
| Запланировано | N | X% |
| Отложено | N | X% |
| Брошено | N | X% |
| Любимое | N | X% |
| **Всего** | **N** | 100% |

Displayed as a horizontal segmented bar chart + table below it.

#### Drop Rate
`(Брошено ÷ (Просмотрено + Брошено)) × 100%` — shown as "X% аниме заброшено".

#### Score Distribution
Histogram of user scores (1–10) across rated anime; shows count per score value.

#### Average Score
Mean of all non-zero scores the user has given, rounded to one decimal.

#### Genre Coverage
Top-5 genres by anime count in collection + "other" bucket.

#### API
```
GET /api/users/me/collection/stats/
```
Returns: `{ watch_hours, remaining_hours, episodes_watched, episodes_remaining, by_status: {...}, avg_score, score_histogram, top_genres, drop_rate }`
