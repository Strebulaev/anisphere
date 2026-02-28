# API — Endpoints Reference

Base URL: `/api/`  
Auth: JWT (`Authorization: Bearer <token>`)

---

## Authentication

```
POST /auth/login/        Login
POST /auth/register/     Register
POST /auth/refresh/      Refresh JWT token
GET  /auth/user/         Get current user
```

---

## Anime

```
GET  /anime/                              List (with filters)
GET  /anime/{id}/                         Detail
GET  /anime/{id}/episodes/                Episodes list
GET  /anime/{id}/translations/            Available translations
GET  /anime/{id}/kodik_player/            Kodik embed URL

GET  /anime/search/?q=                    Search
GET  /anime/updates/                      Recent updates
```

**Filter params (GET /anime/):**  
`q` · `genre` · `year_from/year_to` · `status` · `kind` · `score_min/score_max` · `studio` · `episodes_min/episodes_max` · `season` · `age_rating` · `country` · `has_dub` · `ordering`

---

## Playlists

```
GET    /playlists/              List (public + own)
POST   /playlists/              Create
GET    /playlists/{id}/         Detail
PUT    /playlists/{id}/         Update
DELETE /playlists/{id}/         Delete
POST   /playlists/{id}/add_item/      Add anime
DELETE /playlists/{id}/remove_item/   Remove anime
POST   /playlists/{id}/reorder/       Reorder items
```

---

## User Collection

```
GET    /collection/             User's collection (all statuses)
POST   /collection/             Add anime
PUT    /collection/{id}/        Update status/progress/score
DELETE /collection/{id}/        Remove
```

---

## Dubbing Studios

```
GET /dubs/            List studios
GET /dubs/{id}/       Studio detail (with voice actors, dubbed anime)
POST /dubs/           Create studio entry
POST /dubs/{id}/subscribe/   Subscribe to studio
```

---

## Social: Feed & Posts

```
GET  /social/feed/              Personalized feed
GET  /social/posts/             All posts (filterable)
POST /social/posts/             Create post
GET  /social/posts/{id}/        Post detail
PUT  /social/posts/{id}/        Edit post (5 min window)
DELETE /social/posts/{id}/      Delete post
POST /social/posts/{id}/like/   Like/unlike
POST /social/posts/{id}/dislike/
POST /social/posts/{id}/repost/
POST /social/posts/{id}/bookmark/
```

## Social: Comments

```
GET  /social/comments/?post={id}   Comments for post
POST /social/comments/             Create comment
PUT  /social/comments/{id}/        Edit (10 min window)
DELETE /social/comments/{id}/      Delete
POST /social/comments/{id}/like/
```

## Social: Groups

```
GET  /social/groups/           List groups
POST /social/groups/           Create group
GET  /social/groups/{id}/      Group detail
PUT  /social/groups/{id}/      Update group
POST /social/groups/{id}/join/
POST /social/groups/{id}/leave/
GET  /social/groups/{id}/members/
POST /social/groups/{id}/invite/   Generate invite link
```

---

## Reactor (Shorts)

```
GET  /reactor/posts/           Feed (paginated)
POST /reactor/posts/           Upload video
GET  /reactor/posts/{id}/      Video detail
DELETE /reactor/posts/{id}/    Delete
POST /reactor/posts/{id}/like/
POST /reactor/posts/{id}/report/
```

---

## Chats

```
GET  /chats/                   List user's chats
POST /chats/                   Create group chat
GET  /chats/{id}/              Chat detail
GET  /chats/{id}/messages/     Message history (paginated)
POST /chats/{id}/messages/     Send message
PUT  /chats/{id}/messages/{msg_id}/    Edit (5 min)
DELETE /chats/{id}/messages/{msg_id}/ Delete
POST /chats/{id}/members/      Add member
DELETE /chats/{id}/members/{user_id}/ Remove member
```

WebSocket endpoint: `ws://.../ws/chat/{room_id}/`

---

## Notifications

```
GET  /notifications/                    List notifications
POST /notifications/read_all/           Mark all read
DELETE /notifications/{id}/             Delete
GET  /notifications/complaints/         List complaints
POST /notifications/complaints/         Create complaint
PATCH /notifications/complaints/{id}/  Update status (moderators)
```

---

## Users

```
GET  /users/{username}/          Profile
GET  /users/{username}/followers/
GET  /users/{username}/following/
POST /users/{username}/follow/
POST /users/{username}/unfollow/
POST /users/{username}/block/
GET  /users/online/              Online users list
```

---

## Contests

```
GET  /contests/              List contests
GET  /contests/{id}/         Contest detail
POST /contests/{id}/submit/  Submit entry
GET  /contests/{id}/entries/ Browse entries
POST /contests/{id}/vote/    Cast vote
GET  /contests/archive/      Past contests
```

---

## Response Conventions

- All list endpoints are paginated: `{ count, next, previous, results }`
- Errors: `{ error: string, detail: string }` with appropriate HTTP status
- Auth errors: 401 Unauthorized
- Permission errors: 403 Forbidden
- Not found: 404 Not Found
- Validation errors: 400 Bad Request with field-level messages
