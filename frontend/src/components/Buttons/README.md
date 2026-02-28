# Модуль кнопок действий

Этот модуль предоставляет готовые к использованию кнопки для различных действий с аниме и контентом.

## Экспортируемые компоненты

### AddToFavoriteButton
Кнопка для добавления/удаления аниме в избранное.

**Props:**
- `animeId` (number) - ID аниме
- `animeTitle` (string) - название аниме
- `animePoster` (string, опционально) - URL постера

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { AddToFavoriteButton } from '@/components/Buttons'

const anime = ref({
  id: 123,
  title_ru: 'Наруто',
  poster_url: '/poster.jpg'
})
</script>

<template>
  <AddToFavoriteButton
    :anime-id="anime.id"
    :anime-title="anime.title_ru"
    :anime-poster="anime.poster_url || undefined"
  />
</template>
```

### CollectionButton
Кнопка для добавления аниме в коллекцию с указанием статуса просмотра.

**Props:**
- `status` (null | 'watching' | 'completed' | 'planned', опционально) - статус просмотра
- `showLabel` (boolean, опционально) - показывать текст кнопки

**Events:**
- `click` - нажатие на кнопку

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { CollectionButton } from '@/components/Buttons'

const status = ref('watching')

const handleCollectionClick = () => {
  openCollectionModal()
}
</script>

<template>
  <CollectionButton
    :status="status"
    @click="handleCollectionClick"
  />
</template>
```

### ShareButton
Кнопка для шаринга ссылки на страницу.

**Props:**
- `url` (string, опционально) - URL для шаринга (по умолчанию текущий URL)
- `showLabel` (boolean, опционально) - показывать текст кнопки

**Events:**
- `share` - успешное копирование ссылки или использование нативного шэринга

**Пример использования:**
```vue
<script setup>
import { ShareButton } from '@/components/Buttons'

const handleShare = (url) => {
  console.log('Поделиться:', url)
}
</script>

<template>
  <ShareButton @share="handleShare" />
</template>
```

### ReportButton
Кнопка для отправки жалобы на контент.

**Props:**
- `showLabel` (boolean, опционально) - показывать текст кнопки

**Events:**
- `click` - нажатие на кнопку (обычно открывает модалку жалобы)

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { ReportButton } from '@/components/Buttons'
import { ReportModal } from '@/components/Modals'

const showReportModal = ref(false)

const handleReportClick = () => {
  showReportModal.value = true
}
</script>

<template>
  <ReportButton @click="handleReportClick" />

  <ReportModal
    :show="showReportModal"
    target-id="123"
    target-type="anime"
    target-name="Наруто"
    @close="showReportModal = false"
    @submit="handleSubmitReport"
  />
</template>
```

### BackButton
Кнопка для возврата на предыдущую страницу.

**Props:**
- `to` (string | (() => void), опционально) - путь маршрута или функция для перехода
- `label` (string, опционально) - текст кнопки
- `showLabel` (boolean, опционально) - показывать текст кнопки

**Пример использования:**
```vue
<script setup>
import { BackButton } from '@/components/Buttons'
</script>

<template>
  <BackButton label="Назад к списку" />
  <BackButton :to="'/anime'" />
  <BackButton :to="() => router.back()" />
</template>
```

## Особенности

Все кнопки модуля имеют:
- Единый дизайн и стили
- Адаптивный дизайн для мобильных устройств
- Поддержку темной/светлой темы через CSS-переменные
- Анимации при наведении и клике
- Опциональное отображение текста для мобильной версии
- Поддержку иконок для визуального обозначения действия
