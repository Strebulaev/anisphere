# DEV_RULES — Development Standards

## Non-Negotiable Rules

- **No stubs.** Every function must be fully implemented.
- **No TODO comments** in production code.
- **No console.log / print / alert** in production code.
- **No mock data** — every endpoint returns real DB data.
- **Every button does a real action** — no alert() placeholders.

---

## Error Handling

**Frontend:** Show user-friendly error messages for every API call.  
**Backend:** Return correct HTTP status codes + informative messages.  
**Logging:** Log errors to Sentry or equivalent.

---

## Validation

- All input validated on backend (SQL injection, XSS prevention at all layers).
- Frontend does basic validation before sending (UX, not security).

---

## Backend Rules

### Code Structure
- Each Django app: `models.py`, `serializers.py`, `views.py`, `urls.py`
- Business logic in `services.py` or `utils.py` — never in views
- Shared utilities in separate modules

### Models
```python
# Every model must have:
class Meta:
    ordering = ['-created_at']
    indexes = [models.Index(fields=['field_name'])]

id = models.UUIDField(primary_key=True, default=uuid.uuid4)  # UUID, not auto-int
created_at = models.DateTimeField(auto_now_add=True)
updated_at = models.DateTimeField(auto_now=True)

# ForeignKey always has related_name
user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')

# Choices via Enum classes
class Status(models.TextChoices):
    ONGOING = 'ongoing', 'Онгоинг'
```

### API
- Document all endpoints (drf-yasg or similar)
- Use ViewSets for standard CRUD
- Use `@action` decorator for custom actions
- Pagination on all list endpoints
- Filters support: multiple select, ranges, search (use django-filter)

### Database
- Use `select_related` / `prefetch_related` — no N+1 queries
- Index fields used for search and sorting
- Use Django Filters for complex filtering

### Auth & Permissions
- JWT for API authentication
- Check permissions on every endpoint
- Separate permission levels: user / moderator / admin

---

## Frontend Rules

### Components
- Reusable where possible; accept typed props (TypeScript)
- Logic in composables, not in component body
- Styles: scoped or CSS modules
- Naming: `PascalCase` (e.g., `AnimeCard.vue`)

### Pinia Stores
- Split by domain: `auth`, `anime`, `playlist`, etc. (snake_case filenames)
- Include loading state and error handling in every store
- Use getters for computed values
- Don't store data that can always be fetched fresh

### Axios
- Single axios instance with interceptors
- Interceptors auto-attach auth token
- Interceptors handle: `401` → redirect to login, `500` → show error message
- One file per endpoint group in `src/api/`

### Routing
- All routes typed
- Protected routes check auth before loading
- Lazy-load pages with dynamic imports
- Handle 404 for unknown routes

### UI/UX Standards
- All interactive elements have loading / disabled / active states
- Forms show validation errors inline, under each field
- Use skeleton loaders (not spinners) where appropriate
- Empty states offer a clear action (e.g., "Создать первый плейлист")
- Destructive actions require confirmation dialog

---

## Feature-Specific Rules

### Playlists
- Require at least 1 anime before saving
- Anime search uses debounce for real-time results
- Link statuses auto-update or update via reports
- Public-link playlists viewable without auth

### User Collection
- Anime status auto-updates on watch
- Watch progress syncs across devices
- Status changes update profile counters

### Reactor (Shorts)
- Upload shows progress bar
- Videos go through moderation before publish
- Feed uses infinite scroll
- Anime attachment is required for every video

### Chat
- Real-time delivery via WebSocket
- Message history loads on scroll (pagination)
- Unread count shown in chat list
- File attachments have preview

### Contests
- Submission validates format and size
- Voting protected from stuffing
- Results auto-announce at deadline
- Prize delivery marked with confirmation

---

## Testing

- **Backend:** Django TestCase
- **Frontend:** Vitest + Vue Test Utils — `npm run test:unit`

## Linting

- **Backend:** flake8, isort
- **Frontend:** ESLint + Prettier — `npm run lint`
