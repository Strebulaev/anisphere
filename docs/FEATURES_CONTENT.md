# FEATURES_CONTENT — Playlists, Reactor (Shorts), Contests

## 1. Playlists (`/playlists`)

### Visibility Types
`public` — visible to all | `private` — owner only | `by-link` — anyone with the link (no auth required)

### Create / Edit Playlist
Fields:
- Name (required)
- Description (optional)
- Cover image (optional; defaults to first anime poster)
- Visibility

Anime management:
- Search with real-time autocomplete (debounced)
- Must have at least 1 anime before saving
- Per anime in list: choose dubbing, add note, remove, reorder (drag-and-drop)

### Playlist Detail Page
**Header:** cover, name, author (avatar + name → profile), description  
**Stats:** anime count, created date, view count  
**Buttons:** В избранное · Поделиться · Edit (own) · Delete (own) · Export (copy all links) · Report

**Anime list item:** poster · title · link status (working / unofficial / blocked / broken) · selected dubbing · note · "Смотреть" button

**Footer:** comments section + like/dislike counter

### Public Playlist Catalog (`/playlists/explore`)
- Search by name and description
- Filters: tags, popularity, date
- Sort: newest / most popular / alphabetical
- Playlist cards: cover, name, author, anime count

### Link Statuses
| Status | Meaning |
|---|---|
| `working` | Link confirmed active |
| `unofficial` | Works but unofficial source |
| `blocked` | Blocked by ISP/RKN |
| `broken` | Dead link |

Statuses update automatically or via user reports.

---

## 2. Reactor — Shorts (`/reactor`)

### Feed Layout
- Vertical infinite feed (TikTok-style)
- Swipe up/down → next/previous video
- Swipe left → author profile
- Swipe right → anime page
- Autoplay when in viewport
- Tap to pause

### Video Card Elements
Video · author name (clickable) · anime name (clickable) · description · tags  
Buttons: Like · Comment · Repost · Share · Report  
Counters: likes, comments, reposts  
Comments: slide-up panel, supports timestamps

### Upload Form
Fields:
- Video file (max 60 sec, max 50 MB)
- In-browser trim tool
- Cover image picker
- Description
- Tags
- Anime attachment **(required)**
- Dubbing attachment (optional)

After upload: goes to moderation queue before publish.

### Moderation Pipeline
Checks: content rules · 18+ detection · copyright  
Statuses: `на проверке` → `опубликовано` | `отклонено`

---

## 3. Contests (`/contests`)

### Contest Types
| Type | Cadence | Examples |
|---|---|---|
| Weekly | Every week | Memes, reactions, voice clip of the moment |
| Monthly | Every month | Fanart, playlists, full reviews |

### Contest Page Structure
- Title, organizer, timeline (submission open/close, voting, results)
- Stages overview
- Theme + description
- Rules & requirements (format, size, duration limits)
- Prizes: 1st/2nd/3rd place + special partner prizes
- Action buttons: Участвовать · Смотреть работы · Голосовать · Результаты
- Sponsors/partners, jury (if any)
- Participant count, countdown to next stage
- Discussion comments

### Submit Entry Form
Fields:
- Work type (photo / video / text)
- File upload with preview
- Work title
- Description
- Tags
- Anime attachment (if required by contest)
- Checkbox: "Это моя оригинальная работа"
- Checkbox: "Согласен с правилами конкурса"

Submissions editable until submission deadline.

### Voting
- **Open** — all users can vote
- **Closed** — jury only
- Anti-stuffing: time limits, account verification checks

### Results Page
- Winner announcement
- Full gallery of all submitted works
- Voting statistics
- Prize delivery screenshot (if applicable)

### Contest Archive (`/contests/archive`)
- All past contests
- Filters: year, type
- Per entry: title, dates, participant count, winners
