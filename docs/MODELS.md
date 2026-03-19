# MODELS — Database Models Reference

All models use:
- `id`: UUID primary key
- `created_at`: auto timestamp
- `updated_at`: auto timestamp
- `Meta.ordering` and `Meta.indexes` defined

---

## anime app

### Franchise
`name` · `slug` · `description` · `cover` ImageField

A franchise groups related anime titles (sequels, prequels, spin-offs) under one parent entity.

### AnimeFranchise (M2M through table)
`franchise` FK · `anime` FK · `order` IntegerField (release order within franchise)

### Anime
| Field | Type | Notes |
|---|---|---|
| title_ru | CharField | Russian title |
| title_en | CharField | English title |
| title_jp | CharField | Japanese title |
| shikimori_id | IntegerField | unique, nullable |
| status | CharField | `ongoing/finished/announced/canceled` |
| kind | CharField | `tv/movie/ova/special/ona/music` |
| episodes | IntegerField | total episodes |
| episodes_aired | IntegerField | aired so far |
| score | FloatField | 0.0–10.0 |
| poster_url | URLField | external URL |
| poster | ImageField | local storage |
| description | TextField | |
| genres | JSONField | list of genre names |
| studios | JSONField | list of studio names |
| year | IntegerField | |
| season | CharField | |
| age_rating | CharField | `g/pg/pg13/r/r_plus` |
| kodik_link | URLField | nullable |
| kodik_id | CharField | nullable |

### Genre
`name` · `slug`

### Studio
`name` · `slug`

### AnimeGenre / AnimeStudio
M2M through tables with `anime` + `genre/studio`

---

## users app

### User (extends AbstractUser)
| Field | Notes |
|---|---|
| username | @handle |
| display_name | shown name |
| avatar | ImageField |
| bio | TextField ≤500 chars |
| birth_date | DateField |
| country / city | CharField |
| gender | CharField |
| social_links | JSONField |
| xp | IntegerField |
| level | IntegerField |
| is_online | BooleanField |
| last_seen | DateTimeField |

### UserCollection
`user` FK · `anime` FK · `status` (in_progress/completed/planned/on_hold/dropped/favorite) · `progress` (episode number) · `score` (0–10) · `note` · unique_together(user, anime)

### UserFollow
`follower` FK · `following` FK · unique_together

### UserBlock
`blocker` FK · `blocked` FK

---

## playlists app

### Playlist
`owner` FK · `title` · `description` · `cover` ImageField · `visibility` (public/private/link) · `view_count`

### PlaylistItem
`playlist` FK · `anime` FK · `order` IntegerField · `dub_studio` FK nullable · `note` · unique_together(playlist, anime)

---

## dubs app

### DubStudio
`name` · `slug` · `description` · `contacts` JSONField (telegram/vk/website) · `verified` BooleanField

### VoiceActor
`name` · `studio` FK · `photo` ImageField

### Dub
`anime` FK · `studio` FK · `voice_actors` M2M · `episodes_dubbed` CharField · `is_complete` BooleanField

---

## social app

### Post
`author` FK · `group` FK nullable · `kind` (text/images/video/playlist/anime/shorts/repost/system) · `title` · `content` · `is_spoiler` · `original_post` FK nullable (for reposts) · `like_count` · `dislike_count` · `comment_count` · `repost_count`

### PostBookmark
`user` FK · `post` FK · `created_at` auto · unique_together(user, post)

### PostPin
`user` FK · `post` FK · `order` IntegerField · unique_together(user, post)

### PostHide
`user` FK · `post` FK · `created_at` auto · unique_together(user, post)  — “Не интересно”

### PostMedia
`post` FK · `file` FileField · `media_type` (image/video) · `order`

### Comment
`post` FK · `author` FK · `parent` FK nullable (for replies) · `content` · `like_count` · `dislike_count` · `is_edited`

### Group
`owner` FK · `name` · `slug` · `description` · `rules` · `avatar` · `banner` · `kind` (anime/genre/dub/local/thematic) · `access` (public/private/closed) · `linked_anime` FK nullable · `member_count`

### GroupMember
`group` FK · `user` FK · `role` (owner/admin/moderator/member) · `joined_at`

---

## reactor app

### ReactorPost (Short video)
`author` FK · `video` FileField · `cover` ImageField · `description` · `tags` JSONField · `anime` FK (required) · `dub` FK nullable · `duration` FloatField · `status` (pending/published/rejected) · `like_count` · `comment_count`

---

## notifications app

### Notification
`recipient` FK · `kind` (social/content/group/contest/system) · `text` · `url` · `is_read` · `is_flagged`

### Complaint
`reporter` FK · `content_type` FK (generic FK) · `object_id` · `reason` (spam/copyright/abuse/adult/other) · `description` · `status` (pending/accepted/rejected/needs_info) · `resolved_by` FK nullable

---

## VideoSource (anime app)
`anime` FK · `url` URLField · `source_name` · `episodes_available` · `status` (working/unofficial/blocked/broken) · `added_by` FK · `is_legal` BooleanField

---

## WatchProgress (users app)
`user` FK · `anime` FK · `episode` IntegerField · `position_seconds` IntegerField · `updated_at`

---

## Chat / Message (social app)

### Chat
`kind` (personal/group/community/franchise_discussion) · `name` · `avatar` · `description` · `access` (public/private/link) · `linked_anime` FK nullable · `linked_franchise` FK → Franchise nullable · `invite_link` · `message_count` · `folder_type` CharField default `groups` — for franchise discussions set to `discussions`

### ChatTopic
`chat` FK → Chat · `anime` FK → Anime nullable (null = «Общее» topic) · `title` CharField · `order` IntegerField · `created_at` auto

### UserGlobalChatStyle
`user` OneToOne FK → User · `wallpaper` FK → ChatWallpaper nullable · `bubble_style` CharField default `modern` · `accent_color` CharField(hex) default `#6C5CE7` · `font_size` CharField default `medium` · `message_animation` CharField default `slide` · `emoji_set` CharField default `default` · `time_format` CharField default `24h`

### ChatMember
`chat` FK · `user` FK · `role` (owner/admin/moderator/member) · `joined_at` · `notifications_enabled`

### Message
`chat` FK · `author` FK · `kind` (text/image/video/voice/document/location/anime_card/post_card/system) · `content` · `reply_to` FK nullable · `is_edited` · `is_deleted` · `delivered_at` · `read_by` M2M

### MessageAttachment
`message` FK · `file` FileField · `file_type` · `file_size`

---

## Achievements & XP (users app)

### Achievement
`slug` · `name` · `description` · `category` (basic/social/collection/contest/special) · `tier` (common/advanced/elite/legendary) · `icon` ImageField · `is_animated` BooleanField · `xp_reward`

### UserAchievement
`user` FK · `achievement` FK · `earned_at` · unique_together
