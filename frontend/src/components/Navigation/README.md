# Модуль навигационных элементов

Этот модуль предоставляет компоненты для навигации по приложению.

## Экспортируемые компоненты

### Breadcrumbs
Компонент хлебных крошек для отображения пути навигации.

**Props:**
- `items` (BreadcrumbItem[]) - массив элементов навигации
  - `label` (string) - текст элемента
  - `to` (string, опционально) - путь маршрута (если не указан, элемент считается текущим)

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { Breadcrumbs } from '@/components/Navigation'

const breadcrumbs = ref([
  { label: 'Аниме', to: '/anime' },
  { label: 'АCTION', to: '/anime/genre/action' },
  { label: 'Наруто' }
])
</script>

<template>
  <Breadcrumbs :items="breadcrumbs" />
</template>
```

### Pagination
Компонент пагинации для постраничной навигации.

**Props:**
- `currentPage` (number) - текущая страница
- `totalPages` (number) - общее количество страниц
- `totalItems` (number, опционально) - общее количество элементов
- `maxVisible` (number, опционально) - максимальное количество видимых страниц (по умолчанию 5)

**Events:**
- `update:currentPage` - изменение текущей страницы

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { Pagination } from '@/components/Navigation'

const currentPage = ref(1)
const totalPages = ref(25)
const totalItems = ref(247)

const handlePageChange = (page) => {
  currentPage.value = page
}
</script>

<template>
  <Pagination
    v-model:current-page="currentPage"
    :total-pages="totalPages"
    :total-items="totalItems"
  />
</template>
```

### LoadMoreButton
Кнопка "Загрузить ещё" для бесконечной загрузки.

**Props:**
- `shown` (number) - количество показанных элементов
- `total` (number) - общее количество элементов
- `isLoading` (boolean, опционально) - состояние загрузки

**Events:**
- `loadMore` - запрос на загрузку дополнительных элементов

**Пример использования:**
```vue
<script setup>
import { ref } from 'vue'
import { LoadMoreButton } from '@/components/Navigation'

const shownItems = ref(12)
const totalItems = ref(100)
const isLoading = ref(false)

const handleLoadMore = async () => {
  isLoading.value = true
  await fetchMoreItems()
  shownItems.value += 12
  isLoading.value = false
}
</script>

<template>
  <LoadMoreButton
    :shown="shownItems"
    :total="totalItems"
    :is-loading="isLoading"
    @load-more="handleLoadMore"
  />
</template>
```

## Особенности

Все компоненты модуля имеют:
- Единый дизайн и стили
- Адаптивный дизайн для мобильных устройств
- Поддержку темной/светлой темы через CSS-переменные
- Анимации при взаимодействии
