# FEATURES_SOCIAL — Chats, Groups, Profiles, Search, Notifications

## 1. Chats (`/messages`)

### Chat Types
- **Personal** — auto-created on first message
- **Group** — 3+ participants, admin-managed
- **Community chat** — extended for large groups
- **Franchise Discussion** — one group-chat per franchise (not per individual title); contains topics (threads) for each franchise entry plus a general topic

### Group Chat Creation
Fields: name (required), avatar, description, participants search, access type (public/private/by-link), anime attachment (optional)

### Franchise Discussion Chats

For every franchise (a set of related anime titles grouped under one parent) the platform auto-creates **one** discussion group. Individual franchise entries do **not** get their own standalone discussion groups.

**Structure:**
- Each franchise discussion contains **topics** (similar to Telegram forum topics / supergroup topics).
- One topic per franchise entry (e.g. for the Frieren franchise: "Провожающая в последний путь Фрирен: Магия ●●", "Фрирен [ТВ-1]", "Фрирен [ТВ-2]").
- A mandatory **«Общее»** topic is always present for franchise-wide discussion.
- Topics are ordered: «Общее» first, then entries in release order.

**Navigation:**
- The "Обсуждение" button on a **franchise page** → opens the franchise discussion group (lands on «Общее» topic).
- The "Обсуждение" button on an **individual anime entry page** → redirects into the franchise discussion group and automatically opens the topic corresponding to that entry.
- If an anime does not belong to any franchise, its "Обсуждение" button creates/opens a standalone discussion group for that single title (legacy behaviour).

**Chat list placement:**
- Franchise discussion groups appear under the **«Обсуждения»** folder, **not** under «Группы».

**Topic model fields (ChatTopic):**
| Field | Type | Notes |
|---|---|---|
| `id` | UUID | PK |
| `chat` | FK → Chat | parent franchise discussion |
| `anime` | FK → Anime \| null | null for the «Общее» topic |
| `title` | CharField | display name |
| `order` | IntegerField | sort order |
| `created_at` | DateTimeField | auto |

**API endpoints:**
```
GET  /api/social/franchise-discussions/{franchise_id}/          # Get or auto-create
GET  /api/social/franchise-discussions/{franchise_id}/topics/   # List topics
GET  /api/social/franchise-discussions/{franchise_id}/topics/{topic_id}/messages/
POST /api/social/franchise-discussions/{franchise_id}/topics/{topic_id}/messages/
```

### Chat UI Elements

**Header:** avatar(s), name, online status / member count, search in chat, settings, leave

**Franchise discussion header extras:** topic selector bar (horizontal pill tabs or dropdown list of topics); active topic name shown in sub-header.

**Message Input supports:** text · images · video · documents · voice messages · geolocation · post · anime card · emoji

### Message Types
| Type | Display |
|---|---|
| Text | Plain text with @mentions and links |
| Image | Thumbnail → full view on click |
| Video | Inline player |
| Voice | Player + waveform |
| Document | Icon + name + size + download |
| Geolocation | Map thumbnail |
| Anime card | Rich card |
| Post card | Rich card |
| System | "User joined", "User left", "Message pinned" |

### Message Actions
- Send, reply, forward, edit (5 min window → "отредактировано" label)
- Delete (own: delete; moderators: delete for all → "[сообщение удалено]")
- Pin (admins only)
- @mention with autocomplete
- Delivery statuses: sent → delivered → read
- Typing indicator

### Roles
`Owner` → `Admin` → `Moderator` → `Member`

| Role | Can |
|---|---|
| Owner | All + transfer ownership |
| Admin | Manage members, moderate, edit settings |
| Moderator | Delete messages, issue warnings |
| Member | Read, send |

### Chat Settings

**Personal:** notifications, sound, theme color, chat background, block user, clear history, delete chat

**Group:** name/avatar/description, member management (add/remove/assign roles), permissions (who can write/add), invite link (generate/reset), notifications, delete group

### Chat List Context Menu Actions

Right-clicking (or long-pressing on mobile) any chat row in `/messages` shows a context menu. All actions below must work correctly:

| Action | Behaviour |
|---|---|
| **Закрепить / Открепить** | Toggles `pinned` flag in user's chat settings; pinned chats float to top of list (max 5); UI updates instantly via optimistic update |
| **Архивировать / Разархивировать** | Moves chat to/from the «Архив» folder; archived chats are hidden from main list; badge still shown if unread |
| **Заглушить уведомления** | Opens mute duration picker (15 мин / 1 час / 8 часов / 2 дня / 1 неделю / Навсегда / До даты…); stores `muted_until` in user's chat settings |
| **Отметить как прочитанное** | Sets `last_read_message_id` to the latest message id in that chat; clears unread counter; persisted to backend |
| **Удалить чат** | Confirmation dialog; for personal chats deletes only for the current user; for group chats performs "leave group" |

All five actions send the corresponding API calls and update the local Pinia store optimistically.

### Global Chat Style Settings (gear icon above chat list)

The ⚙️ gear icon above the chat search bar opens **Global Chat Style Settings** — a modal/panel with style-only options that apply as defaults across all chats. These settings are overridden on a per-chat basis by individual chat settings.

**Scope:** style/visual only — no notification or permission settings here.

**Available global style options:**
| Option | Values |
|---|---|
| Default wallpaper | solid / gradient / pattern / image (same picker as per-chat) |
| Default message bubble style | modern / classic / rounded |
| Default accent color | color palette picker |
| Default font size | small / medium / large |
| Message animation | slide / fade / pop / none |
| Emoji set | default / twitter / google / samsung / аниме |
| Time format | 12h / 24h |

**Priority rule:** per-chat settings always override global settings. If a chat has no explicit setting for a given option, the global default is used.

**Storage:** saved in `UserGlobalChatStyle` model (one row per user). Applied client-side: when rendering a chat, merge global defaults → per-chat overrides.

**UserGlobalChatStyle model fields:**
| Field | Type | Default |
|---|---|---|
| `user` | OneToOne FK → User | — |
| `wallpaper` | FK → ChatWallpaper \| null | null |
| `bubble_style` | CharField | `modern` |
| `accent_color` | CharField (hex) | `#6C5CE7` |
| `font_size` | CharField | `medium` |
| `message_animation` | CharField | `slide` |
| `emoji_set` | CharField | `default` |
| `time_format` | CharField | `24h` |

**API:**
```
GET  /api/social/chat-settings/global/    # Fetch current global style
PUT  /api/social/chat-settings/global/    # Save global style
```

### Media Tab
Tabs: images · video · documents · voice · anime  
Features: grid/list view, search, download

---

## 2. Communities & Groups (`/groups`)

### Group Types
By anime (fan clubs) · By genre · By dubbing studio · Local (city/school) · Thematic

### Create Group
Fields: name (required), description, avatar, banner (optional), type (public/private/closed), anime attachment (optional), tags/categories, rules

### Group Page Structure

**Header:** banner, avatar, name, type, member count  
**Buttons:** Join / Member / Request sent  
**Content:** description, rules (collapsible)

**Tabs:**
- **Лента** — member posts
- **Обсуждения** — forum threads
- **Плейлисты** — shared playlists
- **Shorts** — member videos on group topic
- **Участники** — list with roles
- **Медиа** — shared photos/videos
- **События** — planned events

**Admin controls:** edit, delete, manage members

### Group Roles
Same structure as chat: Owner → Admin → Moderator → Member

### Invitations
Generate invite link with optional: time limit, use limit

---

## 3. User Profile (`/u/:username`)

### Profile Header
Avatar (click → full size), display name, @username, online status, stats: followers / following / playlists / achievements  
Buttons: Subscribe/Unsubscribe · Message · Share · Menu (report, block)

### Info Block
Bio, registration date, country/city, social links, favorite genres

### Profile Tabs

**Лента** — user activity in chronological order:
- Added anime to collection, created playlists, wrote reviews, uploaded Shorts, earned achievements, new follows

**Аниме** — user collection filtered by status; poster grid; in-progress shows progress bar; completed shows user score

**Плейлисты** — public playlists; playlist cards (cover, name, anime count); "Save" button on others' playlists

**Shorts** — video grid; each shows: duration, views, likes

**Достижения** — categorized (основные/социальные/коллекционные/конкурсные/специальные); badge + name + description + date earned; progress on incomplete; counter "Получено X из Y"

**О себе** — extended info, favorite anime (from favorites), group activity

### Followers / Following
User list with avatars, names, statuses; search; subscribe/unsubscribe buttons

### Favorites
Tabs: аниме · плейлисты · посты · авторы · группы  
Features: search, sort by date added

---

## 4. Search (`/search`)

### Global Search (header bar)
- Autocomplete at 3+ chars
- Results grouped: аниме · пользователи · плейлисты · группы · Shorts (5 per group)
- "See all" → full search page

### Full Search Page
- Results per category with expand option
- Filter by content type
- Sort results
- Highlight matched text

### Section-Specific Search
| Context | Extra filter |
|---|---|
| Users | Online status |
| Playlists | Tags |
| Groups | Theme/category |
| Reactor | Anime attachment |

---

## 5. Online Users (`/online`)

**Header:** "Сейчас на сайте"  
**Tabs:** online · offline · all  
**Sort:** last seen · name · popularity  
**Search:** by username

**User card:** avatar, name + @username, status ("онлайн" or "был(а) X мин назад"), follower count, Subscribe / Message buttons  
**For online users:** current activity ("Смотрит аниме", "В чате")

---

## 6. Notifications (`/notifications`)

### Notification Types
| Category | Events |
|---|---|
| Social | likes, comments, comment replies, @mentions, new followers |
| Content | new playlists, new Shorts, anime reviews |
| Group | group messages, new members, group events |
| Contest | new contest, voting starts, results, win |
| System | platform updates, announcements, security |

### Display
- Badge on header icon (unread count)
- Dropdown with recent notifications
- Full page with filters: by type / by period / by status (all/unread/flagged)

### Notification Item
Type icon · text (clickable → content) · timestamp  
Actions: mark read, delete

### Actions
- Click → navigate to content
- Mark all read
- Delete all
- Per-type notification settings (which types to receive)

---

## 7. Settings (`/settings`)

Two-column layout: left nav menu + right content (independent scroll).

### Account
- **Edit profile:** avatar (upload/crop/delete), display name, username (limited changes), bio (≤500 chars), birth date, country/city, gender, social links
- **Change password:** current → new (strength indicator) → confirm + email code
- **Email & phone:** view/verify current, add/change phone
- **2FA:** method (app/SMS/backup codes/security key), QR setup, backup codes (show/download/print)
- **Privacy & security:** who sees profile/playlists/activity (all/followers/only me); who can DM/add to groups/mention; show online status; search indexing; block 18+ content; hide spoilers
- **Active sessions:** list with OS/browser/IP/location/time; current session marked; terminate buttons
- **Blocked users:** list with avatar/name/block date; search; unblock
- **Delete account:** warning, list of what gets deleted, reason survey, password confirm, 7-day cool-down

### Notifications & Sounds
Per-category toggles (social/content/group/contest/system) · Email notifications (digest, instant, frequency) · Push (on/off, sound, vibration) · Do Not Disturb (schedule, exceptions)

### Appearance
Theme: light / dark / system · Accent color (palette) · Chat backgrounds · Fonts (size, family, density) · Animations (all / important only / none)

### Data & Storage
Cache stats (images, video, documents) · Clear cache buttons · Cross-device sync · Data export (select data, format, request)
