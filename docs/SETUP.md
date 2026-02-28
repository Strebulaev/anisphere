# SETUP — Installation, Commands, Deployment

## Quick Start (Docker)

```bash
git clone https://github.com/yourusername/animecore.git
cd animecore
docker-compose up -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:80 |
| Backend API | http://localhost:8000/api/ |
| Django Admin | http://localhost:8000/admin/ |

---

## Manual Setup

### Requirements
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15 (or use Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then fill in values
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

### Backend (`backend/.env`)

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/animecore
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1

# OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
VK_CLIENT_ID=
VK_CLIENT_SECRET=

# Email
EMAIL_HOST=smtp.yandex.ru
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=app-password

# Kodik
KODIK_API_TOKEN=your-kodik-token

# MinIO / S3
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=animecore
AWS_S3_ENDPOINT_URL=http://minio:9000
```

---

## Common Commands

### Django (Backend)

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py shell
python manage.py loaddata fixtures.json
```

### Vue.js (Frontend)

```bash
npm run dev           # Dev server
npm run build         # Production build
npm run preview       # Preview build
npm run type-check    # TypeScript check
npm run lint          # ESLint + Prettier
npm run test:unit     # Vitest
```

### Docker

```bash
docker-compose up -d              # Start all services
docker-compose down               # Stop
docker-compose logs -f backend    # View logs
docker-compose build --no-cache   # Rebuild
docker-compose exec backend python manage.py migrate
```

---

## Anime Data Import Scripts

Located in project root. Use when populating initial database.

| Script | Purpose |
|---|---|
| `import_anime_universal.py` | Universal import (recommended) |
| `import_shikimori_full.py` | Full import from Shikimori |
| `import_jikan_full.py` | Import from Jikan API |
| `full_import_with_images.py` | Import + download poster images |
| `auto_shikimori_import.py` | Auto-scheduled Shikimori import |

```bash
cd backend
python import_shikimori_full.py
```

---

## Adding New Endpoints (Checklist)

1. `models.py` — add/update model
2. `python manage.py makemigrations && migrate`
3. `serializers.py` — create serializer
4. `views.py` — create ViewSet or APIView
5. `urls.py` — register URL
6. Update `docs/API.md`

## Adding New Frontend Page (Checklist)

1. Create `src/views/YourPage.vue`
2. Add route in `src/router/index.ts`
3. Add API client in `src/api/your-resource.ts`
4. Add Pinia store in `src/stores/your-store.ts` if needed
5. Add nav link if needed
