# OVERVIEW — AniSphere Project

## What It Is

AniSphere — социальная сеть для русскоязычных анимешников. Объединяет:
- Каталог аниме с поиском и фильтрами
- Личные коллекции и плейлисты
- Базу озвучек
- Ленту активности, посты, комментарии
- Чаты и сообщества
- Shorts-видео (Reactor)
- Конкурсы и достижения

**Brand name:** AniSphere  
**Codebase name:** animecore  
**Target audience:** Русскоязычные анимешники

---

## Tech Stack

### Backend
| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | Django 4.2.10 + DRF |
| Database | PostgreSQL 15 |
| Cache / Sessions | Redis 7 |
| Task Queue | Celery + RabbitMQ |
| Media Storage | MinIO (S3-compatible) |
| WebSockets | Django Channels |
| Search | Elasticsearch |
| Web Server | Gunicorn + Nginx |
| Auth | JWT |

### Frontend
| Component | Technology |
|---|---|
| Framework | Vue.js 3 (Composition API) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State | Pinia |
| Routing | Vue Router 4 |
| HTTP | Axios |
| Video | HLS.js / Video.js |

### Infrastructure
| Component | Technology |
|---|---|
| Containers | Docker + Docker Compose |
| Frontend Deploy | Vercel |
| Backend Hosting | VPS (Hetzner/Timeweb) |

---

## Project Structure

```
animecore/
├── backend/
│   ├── anime/           # Anime catalog, models, views, serializers
│   ├── users/           # User accounts, profiles, auth
│   ├── social/          # Feed, posts, comments, groups
│   ├── playlists/       # Playlists
│   ├── dubs/            # Dubbing studios and voice actors
│   ├── reactor/         # Shorts videos
│   ├── notifications/   # Notifications + complaints
│   ├── parsers/         # Anime data importers
│   └── config/          # Django settings
│
├── frontend/
│   └── src/
│       ├── api/         # Axios API clients (one file per endpoint group)
│       ├── components/  # Reusable Vue components (PascalCase)
│       ├── views/       # Page-level components
│       ├── stores/      # Pinia stores (snake_case filenames)
│       ├── router/      # Vue Router config
│       └── types/       # TypeScript type definitions
│
├── docs/                # This documentation
├── docker-compose.yml
└── spec.md              # Documentation index (this system)
```

---

## External Integrations

| Service | Purpose |
|---|---|
| Shikimori API | Primary anime data import |
| Jikan API | Fallback anime data import |
| Kodik API | Embedded video player |
| Google OAuth | Social login |
| VK OAuth | Social login |
| Telegram OAuth | Social login |

---

## Legal & Security

- **Legal position:** Information intermediary (ст. 1253.1 ГК РФ) — no content initiation, no modification, takedown on first rightsholder notice
- **Data storage:** Russia (152-ФЗ compliance), encrypted PII
- **User controls:** Account deletion (7-day cool-down), data export
- **Safety:** Warning system → temp ban → permanent ban; appeals committee

---

## User Journey (Summary)

1. **Registration** — email/phone or OAuth (Google, VK, Telegram)
2. **Onboarding** — profile setup, browse recommendations
3. **Core loop** — watch anime, manage collection, create playlists
4. **Social** — follow users, post, chat, join communities
5. **Long-term** — earn achievements, level up reputation, enter contests
