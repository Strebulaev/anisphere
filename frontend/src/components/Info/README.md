# Модуль информационных блоков

Этот модуль предоставляет компоненты для отображения различной информации о состоянии контента.

## Экспортируемые компоненты

### PageTitle
Заголовок страницы с опциональным количеством результатов и описанием.

**Props:**
- `title` (string) - заголовок страницы
- `count` (number, опционально) - количество результатов
- `description` (string, опционально) - описание раздела

**Пример использования:**
```vue
<script setup>
import { PageTitle } from '@/components/Info'
</script>

<template>
  <PageTitle
    title="Результаты поиска"
    :count="42"
    description="Найдено аниме по вашему запросу"
  />
</template>
```

### LoadingState
Компонент для отображения состояния загрузки.

**Props:**
- `type` ('spinner' | 'skeleton', опционально) - тип индикатора загрузки
- `message` (string, опционально) - текст сообщения
- `count` (number, опционально) - количество скелетонов (для type='skeleton')

**Пример использования:**
```vue
<script setup>
import { LoadingState } from '@/components/Info'
</script>

<template>
  <LoadingState type="spinner" message="Загрузка данных..." />
  <LoadingState type="skeleton" :count="8" />
</template>
```

### ErrorState
Компонент для отображения состояния ошибки.

**Props:**
- `title` (string, опционально) - заголовок ошибки
- `message` (string, опционально) - сообщение об ошибке
- `showRetry` (boolean, опционально) - показывать кнопку повтора

**Events:**
- `retry` - нажатие на кнопку "Повторить"

**Пример использования:**
```vue
<script setup>
import { ErrorState } from '@/components/Info'

const handleRetry = () => {
  window.location.reload()
}
</script>

<template>
  <ErrorState
    title="Не удалось загрузить данные"
    message="Произошла ошибка при загрузке. Попробуйте позже."
    @retry="handleRetry"
  />
</template>
```

### EmptyState
Компонент для отображения пустого состояния.

**Props:**
- `title` (string, опционально) - заголовок
- `message` (string, опционально) - сообщение
- `icon` ('search' | 'folder' | 'heart' | 'default', опционально) - тип иконки
- `suggestions` (string[], опционально) - список предложений
- `actionLabel` (string, опционально) - текст кнопки действия

**Events:**
- `action` - нажатие на кнопку действия

**Пример использования:**
```vue
<script setup>
import { EmptyState } from '@/components/Info'

const handleResetFilters = () => {
  resetFilters()
}
</script>

<template>
  <EmptyState
    title="Ничего не найдено"
    message="Попробуйте изменить параметры поиска"
    icon="search"
    :suggestions="['Сбросить фильтры', 'Изменить запрос поиска']"
    action-label="Сбросить фильтры"
    @action="handleResetFilters"
  />
</template>
```

### RecommendationBanner
Баннер с рекомендациями аниме в виде горизонтальной карусели.

**Props:**
- `title` (string, опционально) - заголовок баннера
- `animeList` (Anime[], опционально) - список аниме для рекомендаций
- `loading` (boolean, опционально) - состояние загрузки

**Events:**
- `refresh` - нажатие на кнопку "Обновить"
- `click` - клик по карточке аниме

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { RecommendationBanner } from '@/components/Info'
import type { Anime } from '@/types'

const recommendations = ref<Anime[]>([])
const isLoading = ref(false)

const handleRefresh = async () => {
  isLoading.value = true
  await fetchRecommendations()
  isLoading.value = false
}

const handleAnimeClick = (anime) => {
  navigateToAnime(anime.id)
}
</script>

<template>
  <RecommendationBanner
    title="Вам может понравиться"
    :anime-list="recommendations"
    :loading="isLoading"
    @refresh="handleRefresh"
    @click="handleAnimeClick"
  />
</template>
```

## Особенности

Все компоненты модуля имеют:
- Единый дизайн и стили
- Адаптивный дизайн для мобильных устройств
- Поддержку темной/светлой темы через CSS-переменные
- Анимации и плавные переходы
