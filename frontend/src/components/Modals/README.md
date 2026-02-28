# Модуль модальных окон

Этот модуль предоставляет готовые к использованию компоненты модальных окон для работы с аниме.

## Экспортируемые компоненты

### PlaylistSelectModal
Модальное окно выбора плейлиста для добавления аниме.

**Props:**
- `show` (boolean) - отображение модального окна
- `anime` (Anime) - объект аниме для добавления

**Events:**
- `close` - закрытие модального окна
- `save` - сохранение изменений (добавление в плейлист)
- `create-playlist` - открытие модалки создания плейлиста

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { PlaylistSelectModal } from '@/components/Modals'

const showPlaylistModal = ref(false)
const anime = ref(null)

const handleSave = (data) => {
  console.log('Добавлено в плейлисты:', data)
}
</script>

<template>
  <PlaylistSelectModal
    :show="showPlaylistModal"
    :anime="anime"
    @close="showPlaylistModal = false"
    @save="handleSave"
    @create-playlist="showPlaylistModal = false"
  />
</template>
```

### PlaylistCreateModal
Модальное окно создания нового плейлиста.

**Props:**
- `show` (boolean) - отображение модального окна

**Events:**
- `close` - закрытие модального окна
- `create` - создание плейлиста (передает данные: `{ title, description, privacy, animeIds }`)

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { PlaylistCreateModal } from '@/components/Modals'

const showCreateModal = ref(false)

const handleCreate = (data) => {
  console.log('Создание плейлиста:', data)
}
</script>

<template>
  <PlaylistCreateModal
    :show="showCreateModal"
    @close="showCreateModal = false"
    @create="handleCreate"
  />
</template>
```

### ReminderModal
Модальное окно установки напоминания о просмотре.

**Props:**
- `show` (boolean) - отображение модального окна
- `anime` (Anime) - объект аниме для напоминания

**Events:**
- `close` - закрытие модального окна
- `save` - сохранение напоминания (передает данные: `{ animeId, reminderTime, comment, repeatWeekly }`)

**Особенности:**
- Чекбокс "Повторять каждую неделю" отображается только для сериалов (episodes > 1)

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { ReminderModal } from '@/components/Modals'

const showReminderModal = ref(false)
const anime = ref(null)

const handleSaveReminder = (data) => {
  console.log('Напоминание установлено:', data)
}
</script>

<template>
  <ReminderModal
    :show="showReminderModal"
    :anime="anime"
    @close="showReminderModal = false"
    @save="handleSaveReminder"
  />
</template>
```

### QuickViewModal
Модальное окно быстрого просмотра аниме.

**Props:**
- `show` (boolean) - отображение модального окна
- `anime` (Anime) - объект аниме для просмотра
- `isFavorite` (boolean) - находится ли аниме в избранном

**Events:**
- `close` - закрытие модального окна
- `add-to-library` - добавление аниме в коллекцию
- `toggle-favorite` - переключение статуса избранного
- `view-details` - переход к детальной странице аниме

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { QuickViewModal } from '@/components/Modals'

const showQuickViewModal = ref(false)
const anime = ref(null)
const isFavorite = ref(false)

const handleAddToLibrary = () => {
  console.log('Добавлено в коллекцию')
}

const handleToggleFavorite = () => {
  isFavorite.value = !isFavorite.value
}
</script>

<template>
  <QuickViewModal
    :show="showQuickViewModal"
    :anime="anime"
    :is-favorite="isFavorite"
    @close="showQuickViewModal = false"
    @add-to-library="handleAddToLibrary"
    @toggle-favorite="handleToggleFavorite"
    @view-details="handleViewDetails"
  />
</template>
```

## Общие принципы

Все модальные окна имеют:
- Единый дизайн и стили
- Поддержку анимаций открытия/закрытия
- Закрытие по клику на оверлей
- Кнопку закрытия (крестик)
- Адаптивный дизайн для мобильных устройств

## TypeScript типы

Модуль использует следующие типы из `@/types`:
- `Anime` - объект аниме
- `Playlist` - объект плейлиста

Для получения дополнительной информации о типах смотрите `@/types/index.ts`.
