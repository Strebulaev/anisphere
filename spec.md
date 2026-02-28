# ANISPHERE — Project Specification Index

**AniSphere** — русскоязычная социальная сеть для анимешников: каталог аниме, коллекции, озвучки, чаты, Shorts (Reactor), конкурсы.

## Quick Reference

| What you need | Go to |
|---|---|
| Project overview, tech stack, architecture | [docs/OVERVIEW.md](docs/OVERVIEW.md) |
| Development rules, code standards, patterns | [docs/DEV_RULES.md](docs/DEV_RULES.md) |
| UI features: home, feed, catalog, anime page | [docs/FEATURES_CATALOG.md](docs/FEATURES_CATALOG.md) |
| UI features: social — chats, groups, profiles | [docs/FEATURES_SOCIAL.md](docs/FEATURES_SOCIAL.md) |
| UI features: content — playlists, Reactor, contests | [docs/FEATURES_CONTENT.md](docs/FEATURES_CONTENT.md) |
| User systems: achievements, reputation, moderation | [docs/SYSTEMS.md](docs/SYSTEMS.md) |
| API endpoints reference | [docs/API.md](docs/API.md) |
| Database models reference | [docs/MODELS.md](docs/MODELS.md) |
| Setup, deployment, Docker | [docs/SETUP.md](docs/SETUP.md) |

## Memory Bank Usage Guide

Load **only what you need** for the current task:

- **Building a new feature** → OVERVIEW + DEV_RULES + relevant FEATURES_* file
- **API work** → DEV_RULES + API + MODELS
- **Frontend component** → DEV_RULES + relevant FEATURES_* file
- **New model / migration** → DEV_RULES + MODELS
- **DevOps / deploy** → OVERVIEW + SETUP
- **Full system understanding** → All files (use sparingly)
