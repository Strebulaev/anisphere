# План адаптивных стилей для AnimeCore

## Обзор

Этот документ описывает полный план адаптивных стилей для всех устройств. Мы расширим стандартные Tailwind breakpoints для более точного контроля над макетами на разных устройствах.

---

## 1. Breakpoints

### 1.1 Мобильные устройства

| Breakpoint | Ширина | Устройства | Класс |
|------------|--------|------------|-------|
| xs | 320px | iPhone SE, маленькие Android | `xs:` |
| sm | 375px | iPhone 12/13/14, стандартные Android | `sm:` |
| md | 414px | iPhone Plus, большие Android | `md:` |
| lg | 428px | iPhone Pro Max, iPhone 15 Pro Max | `lg:` |
| xl | 480px | Маленькие планшеты в портретном режиме | `xl:` |

### 1.2 Планшеты

| Breakpoint | Ширина | Устройства | Класс |
|------------|--------|------------|-------|
| tablet-sm | 600px | iPad Mini | `tablet-sm:` |
| tablet | 768px | iPad, iPad Air | `tablet:` |
| tablet-lg | 834px | iPad Pro 11" | `tablet-lg:` |
| tablet-xl | 1024px | iPad Pro 12.9" в портрете | `tablet-xl:` |

### 1.3 Ноутбуки

| Breakpoint | Ширина | Устройства | Класс |
|------------|--------|------------|-------|
| laptop-sm | 1152px | Маленькие ноутбуки | `laptop-sm:` |
| laptop | 1280px | Стандартные ноутбуки (13-14") | `laptop:` |
| laptop-lg | 1366px | Ноутбуки 15" | `laptop-lg:` |
| laptop-xl | 1440px | Ноутбуки 15-16" | `laptop-xl:` |

### 1.4 Десктопы

| Breakpoint | Ширина | Устройства | Класс |
|------------|--------|------------|-------|
| desktop-sm | 1536px | Маленькие десктопы | `desktop-sm:` |
| desktop | 1600px | Стандартные десктопы | `desktop:` |
| desktop-lg | 1680px | Десктопы 23-24" | `desktop-lg:` |
| desktop-xl | 1920px | Full HD мониторы | `desktop-xl:` |
| desktop-2xl | 2560px | 2K мониторы | `desktop-2xl:` |
| desktop-3xl | 3840px | 4K мониторы | `desktop-3xl:` |

---

## 2. Конфигурация Tailwind

Добавьте кастомные breakpoints в `tailwind.config.js`:

```javascript
// tailwind.config.js - дополнение к theme.extend
theme: {
  extend: {
    screens: {
      // Мобильные устройства
      'xs': { 'raw': '(min-width: 320px)' },
      'sm': { 'raw': '(min-width: 375px)' },
      'md': { 'raw': '(min-width: 414px)' },
      'lg': { 'raw': '(min-width: 428px)' },
      'xl': { 'raw': '(min-width: 480px)' },
      
      // Планшеты
      'tablet-sm': { 'raw': '(min-width: 600px)' },
      'tablet': { 'raw': '(min-width: 768px)' },
      'tablet-lg': { 'raw': '(min-width: 834px)' },
      'tablet-xl': { 'raw': '(min-width: 1024px)' },
      
      // Ноутбуки
      'laptop-sm': { 'raw': '(min-width: 1152px)' },
      'laptop': { 'raw': '(min-width: 1280px)' },
      'laptop-lg': { 'raw': '(min-width: 1366px)' },
      'laptop-xl': { 'raw': '(min-width: 1440px)' },
      
      // Десктопы
      'desktop-sm': { 'raw': '(min-width: 1536px)' },
      'desktop': { 'raw': '(min-width: 1600px)' },
      'desktop-lg': { 'raw': '(min-width: 1680px)' },
      'desktop-xl': { 'raw': '(min-width: 1920px)' },
      'desktop-2xl': { 'raw': '(min-width: 2560px)' },
      'desktop-3xl': { 'raw': '(min-width: 3840px)' },
    },
  },
},
```

### 2.1 Дополнительные модификаторы высоты

```javascript
theme: {
  extend: {
    height: {
      'screen-xs': '480px',   // Маленькие телефоны
      'screen-sm': '600px',   // Стандартные телефоны
      'screen-md': '700px',   // Большие телефоны
      'screen-lg': '800px',   // Планшеты
    },
    minHeight: {
      'screen-xs': '480px',
      'screen-sm': '600px',
      'screen-md': '700px',
      'screen-lg': '800px',
    },
  },
},
```

---

## 3. Общие паттерны адаптивного дизайна

### 3.1 Контейнеры

```css
/* Основной контейнер */
.container {
  @apply w-full mx-auto px-3;
  
  /* xs (320px) */
  @apply xs:px-3;
  
  /* sm (375px) */
  @apply sm:px-4;
  
  /* md (414px) */
  @apply md:px-4;
  
  /* lg (428px) */
  @apply lg:px-5;
  
  /* xl (480px) */
  @apply xl:px-6;
  
  /* tablet (768px) */
  @apply tablet:px-6;
  
  /* tablet-lg (834px) */
  @apply tablet-lg:px-8;
  
  /* laptop (1280px) */
  @apply laptop:max-w-6xl;
  
  /* desktop (1600px) */
  @apply desktop:max-w-7xl;
  
  /* desktop-xl (1920px) */
  @apply desktop-xl:max-w-8xl;
}
```

### 3.2 Сетка аниме-карточек

```css
/* Количество колонок на разных экранах */
.anime-grid {
  @apply grid grid-cols-2 gap-2;
  
  /* xs (320px) - 2 колонки, маленькие карточки */
  @apply xs:grid-cols-2 xs:gap-2;
  
  /* sm (375px) */
  @apply sm:grid-cols-2 sm:gap-3;
  
  /* md (414px) */
  @apply md:grid-cols-3 md:gap-3;
  
  /* lg (428px) */
  @apply lg:grid-cols-3 lg:gap-4;
  
  /* xl (480px) */
  @apply xl:grid-cols-4 xl:gap-4;
  
  /* tablet-sm (600px) */
  @apply tablet-sm:grid-cols-4 tablet-sm:gap-4;
  
  /* tablet (768px) */
  @apply tablet:grid-cols-4 tablet:gap-4;
  
  /* tablet-lg (834px) */
  @apply tablet-lg:grid-cols-5 tablet-lg:gap-5;
  
  /* tablet-xl (1024px) */
  @apply tablet-xl:grid-cols-5 tablet-xl:gap-5;
  
  /* laptop-sm (1152px) */
  @apply laptop-sm:grid-cols-5 laptop-sm:gap-5;
  
  /* laptop (1280px) */
  @apply laptop:grid-cols-6 laptop:gap-5;
  
  /* laptop-lg (1366px) */
  @apply laptop-lg:grid-cols-6 laptop-lg:gap-6;
  
  /* desktop-sm (1536px) */
  @apply desktop-sm:grid-cols-7 desktop-sm:gap-6;
  
  /* desktop-xl (1920px) */
  @apply desktop-xl:grid-cols-8 desktop-xl:gap-6;
  
  /* desktop-2xl (2560px) */
  @apply desktop-2xl:grid-cols-9 desktop-2xl:gap-7;
}
```

### 3.3 Типографика

```css
/* Заголовки */
h1 {
  @apply text-2xl font-bold;
  
  /* xs */
  @apply xs:text-2xl;
  
  /* sm */
  @apply sm:text-3xl;
  
  /* tablet */
  @apply tablet:text-4xl;
  
  /* laptop */
  @apply laptop:text-5xl;
  
  /* desktop-xl */
  @apply desktop-xl:text-6xl;
}

h2 {
  @apply text-xl font-semibold;
  @apply xs:text-xl sm:text-2xl tablet:text-3xl laptop:text-4xl;
}

h3 {
  @apply text-lg font-semibold;
  @apply xs:text-lg sm:text-xl tablet:text-2xl laptop:text-2xl;
}

/* Основной текст */
body-text {
  @apply text-sm;
  @apply xs:text-sm sm:text-base tablet:text-base laptop:text-lg;
}

/* Вторичный текст */
secondary-text {
  @apply text-xs;
  @apply xs:text-xs sm:text-sm tablet:text-sm laptop:text-base;
}
```

---

## 4. План стилей по страницам

### 4.1 Главная страница (HomeView)

#### 4.1.1 Hero-секция

| Элемент | xs (320px) | sm (375px) | md (414px) | lg (428px) | tablet (768px) | laptop (1280px) | desktop (1600px) | desktop-xl (1920px) |
|---------|------------|------------|------------|------------|----------------|-----------------|------------------|---------------------|
| Высота hero | 300px | 350px | 400px | 420px | 450px | 500px | 550px | 600px |
| Размер заголовка | 24px | 28px | 32px | 36px | 42px | 48px | 56px | 64px |
| Padding | 12px | 16px | 20px | 24px | 32px | 40px | 48px | 64px |
| Отступ между элементами | 8px | 12px | 16px | 16px | 20px | 24px | 32px | 40px |

```css
.hero-section {
  @apply relative h-[300px] flex flex-col justify-center items-center text-center px-3;
  
  @apply xs:h-[300px] xs:px-3;
  @apply sm:h-[350px] sm:px-4;
  @apply md:h-[400px] md:px-5;
  @apply lg:h-[420px] lg:px-6;
  @apply xl:h-[450px] xl:px-6;
  @apply tablet:h-[450px] tablet:px-8;
  @apply tablet-lg:h-[480px];
  @apply laptop:h-[500px] laptop:px-12;
  @apply laptop-lg:h-[550px];
  @apply desktop:h-[580px];
  @apply desktop-xl:h-[600px] desktop-xl:px-16;
}
```

#### 4.1.2 Секция "Топ аниме"

| Элемент | xs | sm | md | lg | tablet | laptop | desktop |
|---------|----|----|----|----|--------|--------|---------|
| Заголовок секции | 18px | 20px | 22px | 24px | 26px | 28px | 32px |
| Количество карточек в ряду | 2 | 2 | 3 | 3 | 4 | 5 | 6 |
| Размер карточки аниме | 120x170px | 130x185px | 140x200px | 150x215px | 160x230px | 180x260px | 200x290px |
| Gap между карточками | 8px | 10px | 12px | 14px | 16px | 18px | 20px |

#### 4.1.3 Секция "Недавно обновлено"

| Элемент | xs | sm | md | lg | tablet | laptop | desktop |
|---------|----|----|----|----|--------|--------|---------|
| Заголовок секции | 16px | 18px | 20px | 22px | 24px | 26px | 28px |
| Количество карточек | 2 | 2 | 3 | 3 | 4 | 5 | 6 |
| Тип отображения | горизонт. | горизонт. | горизонт. | горизонт. | сетка | сетка | сетка |

#### 4.1.4 Навигация в hero

```css
.hero-nav {
  @apply flex flex-col gap-2 w-full;
  
  /* xs-sm */
  @apply xs:flex-row xs:flex-wrap xs:justify-center xs:gap-2;
  
  /* tablet+ */
  @apply tablet:gap-3;
  
  /* laptop+ */
  @apply laptop:gap-4;
}
```

### 4.2 Каталог аниме (AnimeCatalogView)

#### 4.2.1 Боковая панель фильтров

| Элемент | xs | sm | md | lg | tablet | laptop | desktop |
|---------|----|----|----|----|--------|--------|---------|
| Видимость | скрыта | скрыта | скрыта | скрыта | скрыта | visible | visible |
| Ширина | 0 | 0 | 0 | 0 | 0 | 280px | 300px |
| Позиция | fixed | fixed | fixed | fixed | fixed | sticky | sticky |
| Отступ сверху | - | - | - | - | - | 80px | 80px |

```css
.filter-sidebar {
  @apply hidden;
  
  /* laptop - показываем сайдбар */
  @apply laptop:block laptop:sticky laptop:top-20 laptop:w-[280px] laptop:max-h-[calc(100vh-100px)] laptop:overflow-y-auto;
  
  @apply desktop:w-[300px];
}

/* Мобильный фильтр - модальное окно */
.mobile-filter {
  @apply fixed inset-0 z-50 bg-black/80;
  @apply xs:block sm:block md:block lg:block xl:block tablet-sm:block tablet:block;
  @apply laptop:hidden;
}
```

#### 4.2.2 Панель поиска

```css
.search-bar {
  @apply w-full h-10 px-3 rounded-lg;
  
  @apply xs:h-10 xs:text-sm;
  @apply sm:h-11 sm:text-base;
  @apply md:h-12;
  @apply lg:h-12 lg:text-lg;
  @apply tablet:h-12 tablet:w-96;
  @apply laptop:h-14 laptop:w-[480px];
  @apply desktop:h-14 desktop:w-[560px];
}
```

#### 4.2.3 Сортировка и вид

| Элемент | xs | sm | md | lg | tablet | laptop | desktop |
|---------|----|----|----|----|--------|--------|---------|
| Выпадающий список | полная ширина | полная ширина | 200px | 220px | 240px | 260px | 280px |
| Кнопки вида (сетка/список) | скрыты | скрыты | видимы | видимы | видимы | видимы | видимы |

### 4.3 Карточка аниме (AnimeCard)

#### 4.3.1 Размеры карточки

| Breakpoint | Ширина | Высота | Соотношение |
|------------|--------|--------|-------------|
| xs | 140px | 200px | 0.7 |
| sm | 150px | 215px | 0.7 |
| md | 160px | 230px | 0.7 |
| lg | 170px | 245px | 0.7 |
| xl | 180px | 260px | 0.69 |
| tablet | 190px | 275px | 0.69 |
| tablet-lg | 200px | 290px | 0.69 |
| laptop | 210px | 305px | 0.69 |
| desktop | 220px | 320px | 0.69 |
| desktop-xl | 240px | 350px | 0.69 |

```css
.anime-card {
  @apply relative w-[140px] h-[200px] rounded-lg overflow-hidden cursor-pointer transition-transform;
  
  @apply xs:w-[140px] xs:h-[200px];
  @apply sm:w-[150px] sm:h-[215px];
  @apply md:w-[160px] md:h-[230px];
  @apply lg:w-[170px] lg:h-[245px];
  @apply xl:w-[180px] xl:h-[260px];
  @apply tablet:w-[190px] tablet:h-[275px];
  @apply tablet-lg:w-[200px] tablet-lg:h-[290px];
  @apply laptop:w-[210px] laptop:h-[305px];
  @apply laptop-lg:w-[220px] laptop-lg:h-[320px];
  @apply desktop:w-[230px] desktop:h-[335px];
  @apply desktop-xl:w-[240px] desktop-xl:h-[350px];
}
```

#### 4.3.2 Элементы карточки

**Обложка (poster)**

```css
.anime-card-poster {
  @apply w-full h-full object-cover;
  
  /* xs-sm: только обложка, без доп. информации */
  @apply xs:object-cover;
  
  /* md+: показываем градиент с рейтингом */
  @apply md:object-cover md:after:content-[''] md:after:absolute md:after:inset-0 md:after:bg-gradient-to-t md:after:from-black/80 md:after:to-transparent;
}
```

**Рейтинг**

```css
.anime-card-rating {
  @apply absolute top-2 right-2 bg-accent text-white text-xs font-bold px-2 py-0.5 rounded;
  
  @apply xs:text-[10px] xs:px-1.5 xs:py-0.5;
  @apply sm:text-xs;
  @apply md:text-sm md:px-2 md:py-1;
  @apply tablet:text-sm;
  @apply laptop:text-base;
}
```

**Информация о сериях**

```css
.anime-card-episodes {
  @apply absolute bottom-2 left-2 text-white text-xs;
  
  @apply xs:text-[10px];
  @apply sm:text-xs;
  @apply md:text-sm;
  @apply tablet:text-sm;
}
```

**Статус ( ongoing, finished )**

```css
.anime-card-status {
  @apply absolute top-2 left-2 text-[10px] font-medium px-1.5 py-0.5 rounded;
  
  @apply xs:text-[8px] xs:px-1 xs:py-0.5;
  @apply sm:text-[10px];
  @apply md:text-xs md:px-2 md:py-1;
}
```

### 4.4 Страница детального просмотра аниме (AnimeDetailView)

#### 4.4.1 Баннер

```css
.anime-banner {
  @apply relative h-[250px] w-full bg-cover bg-center;
  
  @apply xs:h-[200px];
  @apply sm:h-[250px];
  @apply md:h-[300px];
  @apply lg:h-[350px];
  @apply xl:h-[380px];
  @apply tablet:h-[400px];
  @apply tablet-lg:h-[450px];
  @apply laptop:h-[500px];
  @apply desktop:h-[550px];
  @apply desktop-xl:h-[600px];
}
```

#### 4.4.2 Постер аниме

```css
.anime-poster {
  @apply absolute -bottom-16 left-4 w-28 h-40 rounded-lg shadow-lg border-2 border-background;
  
  @apply xs:w-24 xs:h-36 xs:-bottom-12;
  @apply sm:w-28 sm:h-40 sm:-bottom-14;
  @apply md:w-32 md:h-48 md:-bottom-16;
  @apply lg:w-36 lg:h-52 lg:-bottom-18;
  @apply xl:w-40 lg:h-56 xl:-bottom-20;
  @apply tablet:w-44 tablet:h-64 tablet:-bottom-20;
  @apply laptop:w-48 laptop:h-72 laptop:-bottom-24;
  @apply desktop:w-52 desktop:h-76 desktop-xl:w-56 desktop-xl:h-80;
}
```

#### 4.4.3 Информация об аниме

```css
.anime-info {
  @apply ml-4 mt-16;
  
  @apply xs:mt-12 xs:ml-32 xs:pr-4;
  @apply sm:mt-14 sm:ml-36;
  @apply md:mt-16 md:ml-40;
  @apply lg:mt-18 lg:ml-44;
  @apply xl:mt-20 xl:ml-48;
  @apply tablet:mt-20 tablet:ml-52 tablet:pr-8;
  @apply laptop:mt-24 laptop:ml-56 laptop:pr-12;
  @apply desktop:mt-24 desktop:ml-60 desktop:pr-16;
  @apply desktop-xl:ml-64 desktop-xl:pr-20;
}
```

**Название**

```css
.anime-title {
  @apply text-xl font-bold text-text-primary leading-tight;
  
  @apply xs:text-lg xs:leading-tight;
  @apply sm:text-xl;
  @apply md:text-2xl;
  @apply lg:text-3xl;
  @apply tablet:text-3xl;
  @apply laptop:text-4xl;
}
```

**Оригинальное название**

```css
.anime-title-original {
  @apply text-sm text-text-secondary mt-1;
  
  @apply xs:text-xs;
  @apply sm:text-sm;
  @apply md:text-base;
  @apply tablet:text-base;
  @apply laptop:text-lg;
}
```

#### 4.4.4 Кнопки действий

```css
.anime-actions {
  @apply flex flex-wrap gap-2 mt-4;
  
  @apply xs:gap-2;
  @apply sm:gap-3;
  @apply md:gap-4;
  @apply lg:gap-4;
  @apply tablet:gap-5;
  @apply laptop:gap-6;
}
```

**Кнопка "Смотреть"**

```css
.watch-button {
  @apply bg-accent hover:bg-accent-hover text-white font-medium px-4 py-2 rounded-lg transition-colors;
  
  @apply xs:px-3 xs:py-1.5 xs:text-sm xs:w-full;
  @apply sm:px-4 sm:py-2 sm:text-base sm:w-auto;
  @apply md:px-5 md:py-2.5;
  @apply tablet:px-6 tablet:py-3 tablet:text-lg;
  @apply laptop:px-8 laptop:py-3;
}
```

#### 4.4.5 Табы (Описание, Серии, Озвучки, Отзывы)

```css
.anime-tabs {
  @apply flex overflow-x-auto gap-2 border-b border-divider px-4 mt-6;
  
  @apply xs:gap-1 xs:px-2;
  @apply sm:gap-2 sm:px-3;
  @apply md:gap-3 md:px-4;
  @apply lg:gap-4 lg:px-6;
  @apply tablet:px-8;
}

.tab-item {
  @apply whitespace-nowrap px-3 py-2 text-sm font-medium text-text-secondary border-b-2 border-transparent transition-colors;
  
  @apply xs:px-2 xs:py-2 xs:text-xs;
  @apply sm:px-3 sm:text-sm;
  @apply md:px-4 md:text-base;
  @apply tablet:px-5;
  
  &.active {
    @apply text-accent border-accent;
  }
}
```

#### 4.4.6 Список серий

```css
.episode-list {
  @apply grid grid-cols-4 gap-2 mt-4;
  
  @apply xs:grid-cols-3 xs:gap-1;
  @apply sm:grid-cols-4 sm:gap-2;
  @apply md:grid-cols-5;
  @apply lg:grid-cols-6;
  @apply xl:grid-cols-7;
  @apply tablet:grid-cols-8;
  @apply tablet-lg:grid-cols-9;
  @apply laptop:grid-cols-10;
}

.episode-item {
  @apply bg-background-surface hover:bg-background-active rounded px-2 py-2 text-center text-sm cursor-pointer transition-colors;
  
  @apply xs:px-1 xs:py-1.5 xs:text-xs;
  @apply sm:px-2 sm:py-2 sm:text-sm;
  @apply md:px-3 md:py-2.5;
}
```

#### 4.4.7 Список озвучек

```css
.dub-list {
  @apply space-y-3 mt-4;
  
  @apply xs:space-y-2;
  @apply sm:space-y-3;
  @apply md:space-y-4;
}

.dub-item {
  @apply flex items-center gap-3 p-3 bg-background-surface rounded-lg;
  
  @apply xs:p-2 xs:gap-2;
  @apply sm:p-3 sm:gap-3;
  @apply md:p-4 md:gap-4;
}
```

### 4.5 Профиль пользователя (ProfileView)

#### 4.5.1 Обложка профиля

```css
.profile-cover {
  @apply h-32 w-full bg-cover bg-center;
  
  @apply xs:h-24;
  @apply sm:h-28;
  @apply md:h-36;
  @apply lg:h-40;
  @apply tablet:h-48;
  @apply laptop:h-56;
  @apply desktop:h-64;
}
```

#### 4.5.2 Аватар

```css
.profile-avatar {
  @apply absolute -bottom-8 left-4 w-20 h-20 rounded-full border-4 border-background;
  
  @apply xs:w-16 xs:h-16 xs:-bottom-6;
  @apply sm:w-20 sm:h-20 sm:-bottom-8;
  @apply md:w-24 md:h-24 md:-bottom-10;
  @apply lg:w-28 lg:h-28 lg:-bottom-12;
  @apply tablet:w-32 tablet:h-32 tablet:-bottom-14;
  @apply laptop:w-36 laptop:h-36;
}
```

#### 4.5.3 Информация о пользователе

```css
.profile-info {
  @apply mt-12 px-4;
  
  @apply xs:mt-10 xs:px-3;
  @apply sm:mt-12 sm:px-4;
  @apply md:mt-14 md:px-6;
  @apply lg:mt-16 lg:px-8;
  @apply tablet:mt-16 tablet:px-8;
  @apply laptop:mt-20 laptop:px-12;
}

.profile-name {
  @apply text-xl font-bold;
  
  @apply xs:text-lg;
  @apply sm:text-xl;
  @apply md:text-2xl;
  @apply lg:text-3xl;
  @apply tablet:text-3xl;
  @apply laptop:text-4xl;
}

.profile-stats {
  @apply flex gap-4 mt-2 text-sm text-text-secondary;
  
  @apply xs:gap-2 xs:text-xs;
  @apply sm:gap-3 sm:text-sm;
  @apply md:gap-4;
  @apply lg:gap-6;
}
```

#### 4.5.4 Навигация профиля

```css
.profile-nav {
  @apply flex gap-2 mt-4 overflow-x-auto;
  
  @apply xs:gap-1;
  @apply sm:gap-2;
  @apply md:gap-3;
  @apply lg:gap-4;
}
```

### 4.6 Коллекция аниме (MyCollectionView)

#### 4.6.1 Статусы (Смотрю, Завершено, В планах, Бросил, На паузе)

```css
.collection-tabs {
  @apply flex overflow-x-auto gap-2 py-3 px-4 sticky top-14 bg-background z-10;
  
  @apply xs:gap-1 xs:px-2 xs:top-12;
  @apply sm:gap-2 sm:px-3;
  @apply md:gap-3 md:px-4;
  @apply tablet:gap-4;
  @apply laptop:justify-center;
}

.collection-tab {
  @apply px-3 py-1.5 text-sm whitespace-nowrap rounded-full bg-background-surface text-text-secondary transition-colors;
  
  @apply xs:px-2 xs:py-1 xs:text-xs;
  @apply sm:px-3 sm:py-1.5 sm:text-sm;
  @apply md:px-4 md:py-2;
  
  &.active {
    @apply bg-accent text-white;
  }
}
```

#### 4.6.2 Прогресс просмотра

```css
.progress-bar {
  @apply h-1.5 bg-divider rounded-full overflow-hidden;
  
  @apply xs:h-1;
  @apply sm:h-1.5;
  @apply md:h-2;
}

.progress-fill {
  @apply h-full bg-status-watching rounded-full;
}
```

### 4.7 Плейлисты (PlaylistsView, PlaylistDetailView)

#### 4.7.1 Карточка плейлиста

```css
.playlist-card {
  @apply bg-background-surface rounded-lg p-4 flex gap-4;
  
  @apply xs:p-3 xs:gap-3 xs:flex-col;
  @apply sm:p-4 sm:gap-4 sm:flex-row;
  @apply md:p-5;
  @apply lg:p-6;
}

.playlist-cover {
  @apply w-24 h-24 rounded-lg bg-background-active flex-shrink-0;
  
  @apply xs:w-full xs:h-40;
  @apply sm:w-24 sm:h-24;
  @apply md:w-28 md:h-28;
  @apply lg:w-32 lg:h-32;
  @apply laptop:w-36 laptop:h-36;
}

.playlist-info {
  @apply flex-1 min-w-0;
  
  @apply xs:text-center xs:items-center;
  @apply sm:text-left sm:items-start;
}
```

#### 4.7.2 Список аниме в плейлисте

```css
.playlist-items {
  @apply space-y-3;
  
  @apply xs:space-y-2;
  @apply sm:space-y-3;
  @apply md:space-y-4;
}

.playlist-item {
  @apply flex gap-3 p-3 bg-background-surface rounded-lg;
  
  @apply xs:gap-2 xs:p-2;
  @apply sm:gap-3 sm:p-3;
  @apply md:p-4;
}
```

### 4.8 Поиск (SearchView)

#### 4.8.1 Поисковая строка

```css
.search-input {
  @apply w-full h-12 px-4 bg-background-surface rounded-lg text-text-primary placeholder:text-text-tertiary;
  
  @apply xs:h-10 xs:px-3 xs:text-sm;
  @apply sm:h-11;
  @apply md:h-12 md:text-base;
  @apply lg:h-14 lg:px-6;
  @apply tablet:h-14 tablet:w-[500px];
  @apply laptop:h-16 laptop:w-[600px] laptop:text-lg;
}
```

#### 4.8.2 Результаты поиска

```css
.search-results {
  @apply grid grid-cols-2 gap-3 mt-4;
  
  @apply xs:grid-cols-2 xs:gap-2;
  @apply sm:gap-3;
  @apply md:grid-cols-3;
  @apply lg:grid-cols-4;
  @apply xl:grid-cols-5;
  @apply tablet:grid-cols-4 tablet-lg:grid-cols-5;
  @apply laptop:grid-cols-6;
}
```

### 4.9 Настройки (SettingsView)

#### 4.9.1 Боковое меню настроек

```css
.settings-sidebar {
  @apply w-full bg-background-surface rounded-lg p-4;
  
  @apply xs:p-2 xs:text-sm;
  @apply sm:p-3;
  @apply md:p-4 md:w-64 md:sticky md:top-20;
  @apply lg:w-72;
  @apply laptop:w-80;
}

.settings-nav-item {
  @apply block w-full text-left px-4 py-3 rounded-lg text-text-secondary hover:bg-background-active transition-colors;
  
  @apply xs:px-3 xs:py-2 xs:text-sm;
  @apply sm:px-4 sm:py-3;
}
```

#### 4.9.2 Контент настроек

```css
.settings-content {
  @apply flex-1 bg-background-surface rounded-lg p-4;
  
  @apply xs:p-3;
  @apply sm:p-4;
  @apply md:p-6;
  @apply lg:p-8;
}

.settings-section {
  @apply mb-6;
  
  @apply xs:mb-4;
  @apply sm:mb-6;
  @apply md:mb-8;
}
```

### 4.10 Чаты (ChatsView, ChatDetailView)

#### 4.10.1 Список чатов

```css
.chat-list {
  @apply w-full;
  
  @apply xs:w-full;
  @apply md:w-80 md:border-r md:border-divider;
  @apply lg:w-96;
  @apply laptop:w-[400px];
  @apply desktop:w-[450px];
}

.chat-item {
  @apply flex gap-3 p-3 hover:bg-background-surface cursor-pointer transition-colors;
  
  @apply xs:p-2 xs:gap-2;
  @apply sm:p-3 sm:gap-3;
}

.chat-avatar {
  @apply w-12 h-12 rounded-full flex-shrink-0;
  
  @apply xs:w-10 xs:h-10;
  @apply sm:w-12 sm:h-12;
  @apply md:w-14 md:h-14;
}
```

#### 4.10.2 Окно чата

```css
.chat-window {
  @apply flex-1 flex flex-col h-full;
  
  @apply xs:h-[calc(100vh-120px)];
  @apply sm:h-[calc(100vh-140px)];
  @apply md:h-[calc(100vh-80px)];
}

.chat-messages {
  @apply flex-1 overflow-y-auto p-4 space-y-3;
  
  @apply xs:p-2 xs:space-y-2;
  @apply sm:p-3 sm:space-y-3;
  @apply md:p-4;
}

.message {
  @apply max-w-[80%] p-3 rounded-lg;
  
  @apply xs:max-w-[90%] xs:p-2 xs:text-sm;
  @apply sm:max-w-[85%] sm:p-3;
  @apply md:max-w-[80%] md:p-4 md:text-base;
  
  &.own {
    @apply bg-accent text-white ml-auto;
  }
  
  &.other {
    @apply bg-background-surface;
  }
}
```

#### 4.10.3 Поле ввода сообщения

```css
.message-input {
  @apply flex gap-3 p-4 border-t border-divider;
  
  @apply xs:p-2 xs:gap-2;
  @apply sm:p-3 sm:gap-3;
  @apply md:p-4;
}

.message-input-field {
  @apply flex-1 bg-background-surface rounded-lg px-4 py-3 text-text-primary placeholder:text-text-tertiary;
  
  @apply xs:px-3 xs:py-2 xs:text-sm;
  @apply sm:px-4 sm:py-3;
  @apply md:px-5 md:py-3 md:text-base;
}
```

### 4.11 Лента (FeedView)

#### 4.11.1 Посты в ленте

```css
.feed-post {
  @apply bg-background-surface rounded-lg p-4 mb-4;
  
  @apply xs:p-3 xs:mb-3;
  @apply sm:p-4;
  @apply md:p-5;
  @apply lg:p-6;
}

.post-header {
  @apply flex items-center gap-3 mb-3;
  
  @apply xs:gap-2 xs:mb-2;
  @apply sm:gap-3 sm:mb-3;
}

.post-avatar {
  @apply w-10 h-10 rounded-full;
  
  @apply xs:w-8 xs:h-8;
  @apply sm:w-10 sm:h-10;
  @apply md:w-12 md:h-12;
}

.post-content {
  @apply text-base;
  
  @apply xs:text-sm;
  @apply sm:text-base;
  @apply md:text-lg;
}
```

### 4.12 Reactor (Shorts видео)

#### 4.12.1 Сетка видео

```css
.reactor-grid {
  @apply grid grid-cols-1 gap-4;
  
  @apply xs:grid-cols-1;
  @apply sm:grid-cols-2;
  @apply md:grid-cols-2;
  @apply lg:grid-cols-3;
  @apply xl:grid-cols-4;
  @apply tablet:grid-cols-2 tablet-lg:grid-cols-3;
  @apply laptop:grid-cols-4;
}

.reactor-video {
  @apply aspect-[9/16] rounded-lg bg-background-surface overflow-hidden;
  
  @apply xs:aspect-[3/4];
  @apply sm:aspect-[9/16];
  @apply md:aspect-[3/4];
  @apply lg:aspect-[9/16];
}
```

### 4.13 Уведомления (NotificationsView)

#### 4.13.1 Список уведомлений

```css
.notification-list {
  @apply space-y-2;
  
  @apply xs:space-y-1;
  @apply sm:space-y-2;
  @apply md:space-y-3;
}

.notification-item {
  @apply flex gap-3 p-4 bg-background-surface rounded-lg cursor-pointer hover:bg-background-active transition-colors;
  
  @apply xs:p-3 xs:gap-2;
  @apply sm:p-4 sm:gap-3;
}

.notification-icon {
  @apply w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0;
  
  @apply xs:w-8 xs:h-8;
  @apply sm:w-10 sm:h-10;
  @apply md:w-12 md:h-12;
}
```

### 4.14 Студии озвучки (StudiosView, DubStudioView)

#### 4.14.1 Карточка студии

```css
.studio-card {
  @apply bg-background-surface rounded-lg p-4 flex items-center gap-4;
  
  @apply xs:p-3 xs:gap-3 xs:flex-col xs:text-center;
  @apply sm:p-4 sm:gap-4 sm:flex-row sm:text-left;
  @apply md:p-5;
}

.studio-logo {
  @apply w-16 h-16 rounded-lg bg-background-active;
  
  @apply xs:w-12 xs:h-12;
  @apply sm:w-16 sm:h-16;
  @apply md:w-20 md:h-20;
  @apply lg:w-24 lg:h-24;
}
```

---

## 5. Адаптивные компоненты

### 5.1 Модальные окна

```css
.modal-base {
  @apply fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80;
  
  @apply xs:p-2;
  @apply sm:p-4;
  @apply md:p-6;
}

.modal-content {
  @apply bg-background-surface rounded-modal w-full max-w-lg max-h-[90vh] overflow-y-auto;
  
  @apply xs:max-w-full xs:rounded-lg;
  @apply sm:max-w-md;
  @apply md:max-w-lg;
  @apply lg:max-w-xl;
  @apply laptop:max-w-2xl;
}

.modal-header {
  @apply flex items-center justify-between p-4 border-b border-divider;
  
  @apply xs:p-3;
  @apply sm:p-4;
}

.modal-body {
  @apply p-4;
  
  @apply xs:p-3;
  @apply sm:p-4;
  @apply md:p-6;
}

.modal-footer {
  @apply flex justify-end gap-3 p-4 border-t border-divider;
  
  @apply xs:p-3 xs:gap-2;
  @apply sm:p-4 sm:gap-3;
}
```

### 5.2 Выпадающие списки (Dropdown)

```css
.dropdown-menu {
  @apply absolute top-full left-0 mt-2 bg-background-surface rounded-lg shadow-card py-2 min-w-[180px] z-50;
  
  @apply xs:min-w-[160px] xs:mt-1;
  @apply sm:min-w-[180px] sm:mt-2;
  @apply md:min-w-[200px];
  @apply lg:min-w-[220px];
}

.dropdown-item {
  @apply block w-full text-left px-4 py-2 text-text-secondary hover:bg-background-active hover:text-text-primary transition-colors;
  
  @apply xs:px-3 xs:py-2 xs:text-sm;
  @apply sm:px-4 sm:py-2;
}
```

### 5.3 Кнопки

```css
.btn {
  @apply inline-flex items-center justify-center font-medium rounded-button transition-colors disabled:opacity-50 disabled:cursor-not-allowed;
  
  /* Размеры */
  @apply px-4 py-2 text-base;
  @apply xs:px-3 xs:py-1.5 xs:text-sm;
  @apply sm:px-4 sm:py-2;
  @apply md:px-5 md:py-2.5 md:text-base;
  @apply lg:px-6 lg:py-3 lg:text-lg;
  @apply tablet:px-8 tablet:py-3;
  
  /* Варианты */
  &.btn-primary {
    @apply bg-accent text-white hover:bg-accent-hover;
  }
  
  &.btn-secondary {
    @apply bg-background-surface text-text-primary hover:bg-background-active;
  }
  
  &.btn-ghost {
    @apply bg-transparent text-text-secondary hover:bg-background-surface;
  }
  
  &.btn-danger {
    @apply bg-status-dropped text-white hover:opacity-90;
  }
}
```

### 5.4 Формы

```css
.form-group {
  @apply mb-4;
  
  @apply xs:mb-3;
  @apply sm:mb-4;
  @apply md:mb-6;
}

.form-label {
  @apply block text-sm font-medium text-text-secondary mb-2;
  
  @apply xs:text-xs xs:mb-1;
  @apply sm:text-sm sm:mb-2;
}

.form-input {
  @apply w-full bg-background-surface border border-divider rounded-lg px-4 py-3 text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent transition-colors;
  
  @apply xs:px-3 xs:py-2 xs:text-sm;
  @apply sm:px-4 sm:py-3;
  @apply md:px-5 md:py-3 md:text-base;
}

.form-select {
  @apply w-full bg-background-surface border border-divider rounded-lg px-4 py-3 text-text-primary focus:outline-none focus:border-accent transition-colors cursor-pointer appearance-none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23888888'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 20px;
  
  @apply xs:px-3 xs:py-2 xs:text-sm xs:bg-size-16;
  @apply sm:px-4 sm:py-3;
  @apply md:px-5;
}
```

### 5.5 Скелетоны загрузки

```css
.skeleton {
  @apply bg-background-surface animate-pulse rounded;
  
  /* Аниме карточка */
  &.skeleton-card {
    @apply xs:w-[140px] xs:h-[200px];
    @apply sm:w-[150px] sm:h-[215px];
    @apply md:w-[160px] md:h-[230px];
    @apply lg:w-[180px] lg:h-[260px];
    @apply laptop:w-[200px] laptop:h-[290px];
  }
  
  /* Текст */
  &.skeleton-text {
    @apply h-4 w-full;
    
    @apply xs:h-3;
    @apply sm:h-4;
    @apply md:h-5;
  }
  
  /* Аватар */
  &.skeleton-avatar {
    @apply w-10 h-10 rounded-full;
    
    @apply xs:w-8 xs:h-8;
    @apply sm:w-10 sm:h-10;
    @apply md:w-12 md:h-12;
  }
}
```

---

## 6. Навигация (Header/Sidebar)

### 6.1 Мобильная навигация (Bottom Navigation)

```css
.bottom-nav {
  @apply fixed bottom-0 left-0 right-0 bg-background-surface border-t border-divider z-40;
  
  @apply xs:h-14 xs:flex xs:justify-around xs:items-center;
  @apply sm:h-16;
  @apply md:hidden; /* На планшетах и выше - боковая навигация */
}

.bottom-nav-item {
  @apply flex flex-col items-center justify-center flex-1 py-2 text-text-tertiary transition-colors;
  
  @apply xs:py-1.5 xs:text-[10px];
  @apply sm:py-2 sm:text-xs;
  
  &.active {
    @apply text-accent;
  }
}

.bottom-nav-icon {
  @apply w-6 h-6;
  
  @apply xs:w-5 xs:h-5;
  @apply sm:w-6 sm:h-6;
}
```

### 6.2 Десктопная навигация (Sidebar)

```css
.sidebar {
  @apply hidden md:flex md:flex-col md:w-16 md:h-screen md:fixed md:left-0 md:top-0 md:bg-background-surface md:border-r md:border-divider md:z-40;
  
  @apply lg:w-20;
  @apply laptop:w-64; /* Расширенная версия */
}

.sidebar-item {
  @apply flex items-center gap-3 px-4 py-3 text-text-secondary hover:bg-background-active transition-colors;
  
  @apply md:justify-center md:px-2;
  @apply lg:px-4;
  @apply laptop:justify-start;
  
  &.active {
    @apply text-accent bg-background-active;
  }
}

.sidebar-icon {
  @apply w-6 h-6 flex-shrink-0;
  
  @apply md:w-5 md:h-5;
  @apply lg:w-6 lg:h-6;
}

.sidebar-text {
  @apply hidden whitespace-nowrap;
  
  @apply laptop:block;
}
```

### 6.3 Header

```css
.header {
  @apply fixed top-0 left-0 right-0 h-14 bg-background/80 backdrop-blur-nav z-30 border-b border-divider;
  
  @apply xs:h-12;
  @apply sm:h-14;
  @apply md:h-16;
  @apply md:left-16; /* Отступ для сайдбара */
  @apply lg:left-20;
  @apply laptop:left-64;
}

.header-content {
  @apply flex items-center justify-between h-full px-4;
  
  @apply xs:px-3;
  @apply sm:px-4;
  @apply md:px-6;
  @apply lg:px-8;
}
```

---

## 7. Адаптивные утилитарные классы

### 7.1 Отступы (Padding/Margin)

```css
/* Отступы для мобильных */
.p-mobile {
  @apply p-3;
  @apply xs:p-2 sm:p-3 md:p-4 lg:p-5 tablet:p-6;
}

.px-mobile {
  @apply px-3;
  @apply xs:px-2 sm:px-3 md:px-4 lg:px-5 tablet:px-6;
}

.py-mobile {
  @apply py-3;
  @apply xs:py-2 sm:py-3 md:py-4 lg:py-5 tablet:py-6;
}

/* Отступы для десктопа */
.p-desktop {
  @apply tablet:p-4 laptop:p-6 desktop:p-8;
}
```

### 7.2 Ширина

```css
/* Ограничение ширины контента */
.content-max-width {
  @apply max-w-screen-xs;
  @apply sm:max-w-screen-sm;
  @apply md:max-w-screen-md;
  @apply lg:max-w-screen-lg;
  @apply xl:max-w-screen-xl;
  @apply tablet:max-w-screen-tablet;
  @apply laptop:max-w-screen-laptop;
  @apply desktop:max-w-screen-desktop;
}
```

### 7.3 Видимость

```css
/* Скрытие на мобильных */
.hide-mobile {
  @apply xs:hidden sm:hidden md:hidden lg:hidden xl:hidden;
}

/* Скрытие на десктопе */
.hide-desktop {
  @apply md:hidden lg:hidden xl:hidden tablet:hidden;
  @apply laptop:hidden desktop:hidden;
}

/* Показ только на мобильных */
.show-mobile-only {
  @apply xs:block sm:block md:hidden;
}

/* Показ только на планшетах */
.show-tablet-only {
  @apply xs:hidden sm:hidden md:block lg:hidden;
}

/* Показ только на десктопе */
.show-desktop-only {
  @apply xs:hidden sm:hidden md:hidden;
  @apply lg:block;
}
```

---

## 8. Адаптивные медиа-запросы для фоновых изображений

```css
/* Фоновые изображения для разных разрешений */
.hero-background {
  background-image: url('/images/hero-xs.jpg');
  
  @apply sm:bg-[url('/images/hero-sm.jpg')];
  @apply md:bg-[url('/images/hero-md.jpg')];
  @apply lg:bg-[url('/images/hero-lg.jpg')];
  @apply xl:bg-[url('/images/hero-xl.jpg')];
  @apply tablet:bg-[url('/images/hero-tablet.jpg')];
  @apply laptop:bg-[url('/images/hero-laptop.jpg')];
  @apply desktop:bg-[url('/images/hero-desktop.jpg')];
  @apply desktop-xl:bg-[url('/images/hero-desktop-xl.jpg')];
}

/* Постеры аниме */
.anime-poster-image {
  @apply xs:content-[url('/images/posters/poster-xs.jpg')];
  @apply sm:content-[url('/images/posters/poster-sm.jpg')];
  @apply md:content-[url('/images/posters/poster-md.jpg')];
  @apply lg:content-[url('/images/posters/poster-lg.jpg')];
  @apply tablet:content-[url('/images/posters/poster-tablet.jpg')];
  @apply laptop:content-[url('/images/posters/poster-laptop.jpg')];
}
```

---

## 9. Адаптивные состояния

### 9.1 Touch-устройства

```css
/* Стили для touch-устройств */
@supports (hover: none) {
  .hover-only {
    @apply xs:pointer-events-none;
  }
  
  .touch-friendly {
    @apply xs:min-h-[44px] xs:min-w-[44px];
  }
}
```

### 9.2 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 9.3 Dark/Light Mode (дополнительно)

```css
@media (prefers-color-scheme: light) {
  :root {
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --text-primary: #1a1a1a;
    --text-secondary: #666666;
  }
}
```

---

## 10. Приоритеты реализации

### Phase 1: Мобильные устройства (xs - xl)
- [ ] Базовая сетка аниме-карточек
- [ ] Навигация (bottom nav)
- [ ] Главная страница
- [ ] Каталог аниме
- [ ] Карточка аниме
- [ ] Детальная страница аниме
- [ ] Поиск

### Phase 2: Планшеты (tablet-sm - tablet-xl)
- [ ] Адаптация сетки
- [ ] Сайдбар (частично)
- [ ] Фильтры

### Phase 3: Ноутбуки (laptop-sm - laptop-xl)
- [ ] Полный сайдбар
- [ ] Расширенная навигация
- [ ] Оптимизация под широкие экраны

### Phase 4: Десктопы (desktop-sm - desktop-3xl)
- [ ] Оптимизация под большие мониторы
- [ ] 2K/4K мониторы
- [ ] Дополнительные колонки

---

## 11. Тестирование

### 11.1 Тестовые устройства

| Категория | Устройство | Разрешение | Viewport |
|-----------|------------|------------|----------|
| Mobile XS | iPhone SE | 320x568 | 320x568 |
| Mobile SM | iPhone 12/13 | 375x812 | 375x812 |
| Mobile MD | iPhone Plus | 414x896 | 414x896 |
| Mobile LG | iPhone Pro Max | 428x926 | 428x926 |
| Tablet SM | iPad Mini | 768x1024 | 768x1024 |
| Tablet | iPad Air | 820x1180 | 768x1024 |
| Tablet LG | iPad Pro 11" | 834x1194 | 834x1194 |
| Laptop SM | - | 1152x864 | 1152x864 |
| Laptop | MacBook Air 13" | 1280x800 | 1280x800 |
| Laptop LG | MacBook Pro 15" | 1440x900 | 1440x900 |
| Desktop SM | - | 1536x864 | 1536x864 |
| Desktop | - | 1600x900 | 1600x900 |
| Desktop LG | Full HD 23" | 1920x1080 | 1920x1080 |
| Desktop XL | - | 2560x1440 | 1920x1080* |
| Desktop 3XL | 4K | 3840x2160 | 1920x1080* |

*Примечание: для тестирования использовать browser zoom для имитации

### 11.2 Инструменты тестирования

```bash
# Chrome DevTools Device Mode
# 1. Открыть DevTools (F12)
# 2. Нажать Ctrl+Shift+M
# 3. Выбрать устройство из списка или добавить кастомное

# Добавление кастомных устройств:
# Settings > Devices > Add custom device
```

---

## 12. Примеры использования в компонентах

### 12.1 Пример карточки аниме

```vue
<template>
  <div class="anime-card group cursor-pointer">
    <!-- Постер -->
    <img 
      :src="poster" 
      :alt="title"
      class="anime-card-poster"
      loading="lazy"
    />
    
    <!-- Рейтинг -->
    <div class="anime-card-rating">
      {{ rating }}
    </div>
    
    <!-- Статус -->
    <div v-if="status" class="anime-card-status" :class="statusClass">
      {{ statusText }}
    </div>
    
    <!-- Информация при наведении (десктоп) -->
    <div class="anime-card-overlay hidden laptop:block">
      <h3 class="anime-card-title">{{ title }}</h3>
      <p class="anime-card-year">{{ year }}</p>
    </div>
  </div>
</template>

<style scoped>
.anime-card {
  @apply relative w-[140px] h-[200px] rounded-lg overflow-hidden cursor-pointer transition-transform duration-300;
  
  @apply xs:w-[140px] xs:h-[200px] xs:scale-95;
  @apply sm:w-[150px] sm:h-[215px] sm:scale-100;
  @apply md:w-[160px] md:h-[230px];
  @apply lg:w-[170px] lg:h-[245px];
  @apply xl:w-[180px] xl:h-[260px];
  @apply tablet:w-[190px] tablet:h-[275px];
  @apply tablet-lg:w-[200px] tablet-lg:h-[290px];
  @apply laptop:w-[210px] laptop:h-[305px];
  @apply laptop-lg:w-[220px] laptop-lg:h-[320px];
  @apply desktop:w-[230px] desktop:h-[335px];
  @apply desktop-xl:w-[240px] desktop-xl:h-[350px];
}

.anime-card:hover {
  @apply xs:scale-105 sm:scale-110;
}

.anime-card-poster {
  @apply w-full h-full object-cover transition-transform duration-300;
}

.anime-card:hover .anime-card-poster {
  @apply xs:scale-110;
}

.anime-card-rating {
  @apply absolute top-2 right-2 bg-accent text-white text-xs font-bold px-2 py-0.5 rounded;
  
  @apply xs:text-[10px] xs:px-1.5 xs:py-0.5;
  @apply sm:text-xs;
  @apply md:text-sm md:px-2 md:py-1;
  @apply tablet:text-sm;
  @apply laptop:text-base;
}

.anime-card-status {
  @apply absolute top-2 left-2 text-[10px] font-medium px-1.5 py-0.5 rounded;
  
  @apply xs:text-[8px] xs:px-1 xs:py-0.5;
  @apply sm:text-[10px];
  @apply md:text-xs md:px-2 md:py-1;
  
  &.status-watching {
    @apply bg-status-watching text-white;
  }
  
  &.status-completed {
    @apply bg-status-completed text-white;
  }
  
  &.status-planned {
    @apply bg-status-planned text-black;
  }
}

.anime-card-overlay {
  @apply absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent flex flex-col justify-end p-3;
}

.anime-card-title {
  @apply text-white text-sm font-medium truncate;
  
  @apply xs:text-xs;
  @apply sm:text-sm;
  @apply md:text-sm;
}

.anime-card-year {
  @apply text-white/70 text-xs mt-1;
  
  @apply xs:text-[10px];
}
</style>
```

### 12.2 Пример сетки каталога

```vue
<template>
  <div class="catalog-container">
    <!-- Фильтры -->
    <div class="catalog-filters mb-4">
      <!-- Мобильный фильтр - кнопка -->
      <button 
        class="filter-button laptop:hidden"
        @click="showFilters = true"
      >
        <FilterIcon class="w-5 h-5" />
        Фильтры
      </button>
      
      <!-- Десктопный фильтр - сайдбар -->
      <aside class="filter-sidebar hidden laptop:block">
        <FilterPanel />
      </aside>
    </div>
    
    <!-- Сетка аниме -->
    <div class="anime-grid">
      <AnimeCard 
        v-for="anime in animeList" 
        :key="anime.id"
        :anime="anime"
      />
    </div>
  </div>
</template>

<style scoped>
.catalog-container {
  @apply container mx-auto px-3 py-4;
  
  @apply xs:px-2 xs:py-3;
  @apply sm:px-3 sm:py-4;
  @apply md:px-4;
  @apply lg:px-5;
  @apply xl:px-6;
  @apply tablet:px-6;
  @apply laptop:px-8;
  @apply desktop:px-12;
}

.filter-button {
  @apply flex items-center gap-2 w-full bg-background-surface px-4 py-3 rounded-lg text-text-primary;
  
  @apply xs:px-3 xs:py-2;
  @apply sm:px-4 sm:py-3;
}

.filter-sidebar {
  @apply fixed left-0 top-14 bottom-0 w-64 bg-background-surface border-r border-divider p-4 overflow-y-auto;
  @apply laptop:sticky laptop:top-20 laptop:w-[280px] laptop:h-[calc(100vh-120px)] laptop:border-r-0;
  
  @apply desktop:w-[300px];
}

.anime-grid {
  @apply grid grid-cols-2 gap-2;
  
  @apply xs:grid-cols-2 xs:gap-2;
  @apply sm:grid-cols-2 sm:gap-3;
  @apply md:grid-cols-3 md:gap-3;
  @apply lg:grid-cols-3 lg:gap-4;
  @apply xl:grid-cols-4 xl:gap-4;
  @apply tablet-sm:grid-cols-4 tablet-sm:gap-4;
  @apply tablet:grid-cols-4 tablet:gap-4;
  @apply tablet-lg:grid-cols-5 tablet-lg:gap-5;
  @apply tablet-xl:grid-cols-5 tablet-xl:gap-5;
  @apply laptop-sm:grid-cols-5 laptop-sm:gap-5;
  @apply laptop:grid-cols-6 laptop:gap-5;
  @apply laptop-lg:grid-cols-6 laptop-lg:gap-6;
  @apply desktop-sm:grid-cols-7 desktop-sm:gap-6;
  @apply desktop-xl:grid-cols-8 desktop-xl:gap-6;
  @apply desktop-2xl:grid-cols-9 desktop-2xl:gap-7;
}
</style>
```

---

## 13. Заключение

Этот план охватывает все основные сценарии адаптивного дизайна для проекта AnimeCore. Ключевые принципы:

1. **Mobile-first**: начинаем с минимальных экранов и расширяем для больших
2. **Progressive enhancement**: добавляем функциональность для больших экранов
3. **Touch-friendly**: все интерактивные элементы имеют достаточный размер для касаний (min 44px)
4. **Performance**: используем responsive images и lazy loading
5. **Consistency**: единая система отступов, размеров и типографики на всех устройствах

При реализации рекомендуется использовать CSS-переменные для часто изменяемых значений и создавать миксины/компоненты для повторяющихся паттернов.
