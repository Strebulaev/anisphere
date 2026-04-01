# План адаптивных стилей для AnimeCore

## Содержание
1. [Обзор стратегии](#1-обзор-стратегии)
2. [Breakpoints для мобильных устройств](#2-breakpoints-для-мобильных-устройств)
3. [Breakpoints для компьютеров](#3-breakpoints-для-компьютеров)
4. [Детальный план по страницам и компонентам](#4-детальный-план-по-страницам-и-компонентам)
5. [Конфигурация Tailwind](#5-конфигурация-tailwind)
6. [Рекомендации по реализации](#6-рекомендации-по-реализации)

---

## 1. Обзор стратегии

### 1.1 Принципы адаптивного дизайна
- **Mobile First**: разработка начинается с мобильной версии, затем расширяется
- **Desktop Only**: изменения под компьютеры не затрагиваются (как указано в ТЗ)
- **Fluid Typography**: плавная адаптация шрифтов между breakpoints
- **Component-Level Responsive**: каждый компонент имеет собственный набор адаптивных стилей

### 1.2 Целевые устройства

#### Мобильные устройства (6 категорий)
| Категория | Диапазон ширины | Устройства |
|-----------|-----------------|------------|
| xs-min | 280px - 319px | Старые Android, iPhone SE |
| xs | 320px - 374px | iPhone 12/13/14 Mini, маленькие Android |
| sm | 375px - 413px | iPhone 12/13/14, Pixel 5 |
| md | 414px - 479px | iPhone 12/13/14 Plus, большие Android |
| lg | 480px - 599px | Маленькие планшеты (7") |
| xl | 600px - 767px | Планшеты (8-10") |

#### Компьютеры (7 категорий)
| Категория | Диапазон ширины | Устройства |
|-----------|-----------------|------------|
| 2xl | 768px - 1023px | Маленькие ноутбуки, iPad Mini горизонтально |
| 3xl | 1024px - 1279px | Стандартные ноутбуки (13-14") |
| 4xl | 1280px - 1365px | Ноутбуки 13" Retina, старые мониторы |
| 5xl | 1366px - 1535px | Стандартные мониторы (15-19") |
| 6xl | 1536px - 1919px | Большие мониторы (22-24") |
| 7xl | 1920px - 2559px | QHD мониторы, MacBook Pro 16" |
| 8xl | 2560px+ | 4K мониторы, ультра-широкие |

---

## 2. Breakpoints для мобильных устройств

### 2.1 Расширенная конфигурация Tailwind

```javascript
// tailwind.config.js - добавить в theme.extend.screens
screens: {
  // Мобильные устройства
  'xs-min': '280px',    // Старые маленькие телефоны
  'xs': '320px',        // Маленькие iPhone
  'sm': '375px',        // Стандартные iPhone
  'md': '414px',        // Большие iPhone, Android
  'lg': '480px',        // Маленькие планшеты
  'xl': '600px',        // Планшеты
  
  // Компьютеры (расширенные)
  '2xl': '768px',       // Маленькие ноутбуки
  '3xl': '1024px',      // Стандартные ноутбуки
  '4xl': '1280px',      // Ноутбуки с высоким разрешением
  '5xl': '1366px',      // Стандартные мониторы
  '6xl': '1536px',      // Большие мониторы
  '7xl': '1920px',      // QHD мониторы
  '8xl': '2560px',      // 4K и ультра-широкие
  
  // Ориентация
  'portrait': { 'orientation': 'portrait' },
  'landscape': { 'orientation': 'landscape' },
  
  // Соотношение сторон
  'aspect-video': '(aspect-ratio: 16/9)',
  'aspect-square': '(aspect-ratio: 1/1)',
  'aspect-portrait': '(aspect-ratio: 3/4)',
  
  // Высота
  'h-sm': '640px',
  'h-md': '768px', 
  'h-lg': '1024px',
  'h-xl': '1280px',
}
```

### 2.2 Стили по категориям мобильных устройств

#### xs-min (280px - 319px)
```css
/* Особенности: Очень маленькие экраны, ограниченное пространство */

/* Отступы */
.p-mobile-xs { padding: 8px; }
.m-mobile-xs { margin: 8px; }

/* Размеры текста */
.text-xs-min { font-size: 12px; }
.title-xs-min { font-size: 16px; }

/* Сетка */
.grid-cols-xs-min-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-xs-min-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }

/* Компоненты */
.card-xs-min { width: 100%; max-width: 260px; }
.btn-xs-min { padding: 6px 12px; font-size: 12px; }
.input-xs-min { font-size: 14px; padding: 8px; }
.avatar-xs-min { width: 32px; height: 32px; }

/* Навигация */
.nav-xs-min { 
  padding: 8px; 
  font-size: 12px;
}
.sidebar-xs-min { 
  width: 100%; 
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  top: auto;
}
```

#### xs (320px - 374px)
```css
/* Особенности: Стандартные маленькие iPhone, Android */

/* Отступы */
.p-mobile-sm { padding: 12px; }
.m-mobile-sm { margin: 12px; }

/* Размеры текста */
.text-xs { font-size: 13px; }
.title-xs { font-size: 18px; }

/* Сетка */
.grid-cols-xs-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-xs-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }

/* Компоненты */
.card-xs { width: 100%; max-width: 300px; }
.btn-xs { padding: 8px 16px; font-size: 13px; }
.input-xs { font-size: 15px; padding: 10px; }
.avatar-xs { width: 36px; height: 36px; }

/* Карточки аниме */
.anime-card-xs { 
  width: 140px; 
  height: 200px;
}
.anime-card-xs .poster { 
  height: 180px; 
}
```

#### sm (375px - 413px)
```css
/* Особенности: iPhone 12/13/14 стандартные */

/* Отступы */
.p-mobile-md { padding: 16px; }
.m-mobile-md { margin: 16px; }

/* Размеры текста */
.text-sm { font-size: 14px; }
.title-sm { font-size: 20px; }

/* Сетка */
.grid-cols-sm-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-sm-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-sm-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }

/* Компоненты */
.card-sm { width: 100%; max-width: 350px; }
.btn-sm { padding: 10px 20px; font-size: 14px; }
.input-sm { font-size: 16px; padding: 12px; }
.avatar-sm { width: 40px; height: 40px; }

/* Карточки аниме */
.anime-card-sm { 
  width: 160px; 
  height: 230px;
}
.anime-card-sm .poster { 
  height: 210px; 
}
```

#### md (414px - 479px)
```css
/* Особенности: iPhone Plus, большие Android */

/* Отступы */
.p-mobile-lg { padding: 20px; }
.m-mobile-lg { margin: 20px; }

/* Размеры текста */
.text-md { font-size: 15px; }
.title-md { font-size: 22px; }

/* Сетка */
.grid-cols-md-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-md-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-md-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-md-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }

/* Компоненты */
.card-md { width: 100%; max-width: 390px; }
.btn-md { padding: 12px 24px; font-size: 15px; }
.input-md { font-size: 16px; padding: 14px; }
.avatar-md { width: 44px; height: 44px; }

/* Карточки аниме */
.anime-card-md { 
  width: 180px; 
  height: 260px;
}
.anime-card-md .poster { 
  height: 240px; 
}
```

#### lg (480px - 599px)
```css
/* Особенности: Маленькие планшеты (7") */

/* Отступы */
.p-mobile-xl { padding: 24px; }
.m-mobile-xl { margin: 24px; }

/* Размеры текста */
.text-lg { font-size: 16px; }
.title-lg { font-size: 24px; }

/* Сетка */
.grid-cols-lg-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-lg-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-lg-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-lg-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid-cols-lg-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }

/* Компоненты */
.card-lg { width: 100%; max-width: 450px; }
.btn-lg { padding: 14px 28px; font-size: 16px; }
.input-lg { font-size: 16px; padding: 14px; }
.avatar-lg { width: 48px; height: 48px; }

/* Карточки аниме */
.anime-card-lg { 
  width: 200px; 
  height: 290px;
}
.anime-card-lg .poster { 
  height: 270px; 
}

/* Превью контента - 2 колонки */
.preview-grid-lg { 
  grid-template-columns: repeat(2, 1fr); 
  gap: 12px;
}
```

#### xl (600px - 767px)
```css
/* Особенности: Планшеты 8-10 дюймов */

/* Отступы */
.p-tablet { padding: 28px; }
.m-tablet { margin: 28px; }

/* Размеры текста */
.text-xl { font-size: 16px; }
.title-xl { font-size: 26px; }
.heading-xl { font-size: 32px; }

/* Сетка */
.grid-cols-xl-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-xl-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-xl-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-xl-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid-cols-xl-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.grid-cols-xl-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }

/* Компоненты */
.card-xl { width: 100%; max-width: 560px; }
.btn-xl { padding: 14px 28px; font-size: 16px; }
.input-xl { font-size: 16px; padding: 14px; }
.avatar-xl { width: 52px; height: 52px; }

/* Карточки аниме */
.anime-card-xl { 
  width: 220px; 
  height: 320px;
}
.anime-card-xl .poster { 
  height: 300px; 
}

/* Превью контента - 3 колонки */
.preview-grid-xl { 
  grid-template-columns: repeat(3, 1fr); 
  gap: 16px;
}

/* Боковая панель может быть видимой */
.sidebar-tablet { 
  width: 280px; 
  position: sticky;
  top: 0;
}
```

---

## 3. Breakpoints для компьютеров

### 3.1 Детальная адаптация по размерам экрана

#### 2xl (768px - 1023px) - Маленькие ноутбуки, iPad горизонтально
```css
/* Особенности: Экран как у планшета, но горизонтально */

/* Сетка */
.grid-cols-2xl-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-2xl-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-2xl-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }

/* Компоненты */
.card-2xl { max-width: 700px; }
.btn-2xl { padding: 14px 28px; }

/* Карточки аниме - 3-4 в ряд */
.anime-grid-2xl { 
  grid-template-columns: repeat(3, 1fr); 
  gap: 16px;
}

/* Навигация */
.nav-2xl { 
  padding: 12px 24px;
  font-size: 14px;
}

/* Видео плеер */
.player-2xl {
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
}
```

#### 3xl (1024px - 1279px) - Стандартные ноутбуки 13-14"
```css
/* Особенности: Стандартный ноутбук, достаточно места для контента */

/* Сетка */
.grid-cols-3xl-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-3xl-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid-cols-3xl-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }

/* Компоненты */
.card-3xl { max-width: 900px; }
.btn-3xl { padding: 14px 28px; }

/* Карточки аниме - 4 в ряд */
.anime-grid-3xl { 
  grid-template-columns: repeat(4, 1fr); 
  gap: 20px;
}

/* Навигация */
.nav-3xl { 
  padding: 16px 32px;
  font-size: 15px;
}

/* Профиль пользователя - 2 колонки */
.profile-layout-3xl {
  grid-template-columns: 250px 1fr;
  gap: 24px;
}

/* Видео плеер */
.player-3xl {
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
}
```

#### 4xl (1280px - 1365px) - Ноутбуки с высоким разрешением, Retina
```css
/* Особенности: Высокое разрешение, хорошая детализация */

/* Сетка */
.grid-cols-4xl-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid-cols-4xl-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.grid-cols-4xl-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }

/* Компоненты */
.card-4xl { max-width: 1100px; }

/* Карточки аниме - 5 в ряд */
.anime-grid-4xl { 
  grid-template-columns: repeat(5, 1fr); 
  gap: 20px;
}

/* Профиль пользователя */
.profile-layout-4xl {
  grid-template-columns: 280px 1fr;
  gap: 32px;
}

/* Видео плеер */
.player-4xl {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

/* Сайдбар */
.sidebar-4xl {
  width: 260px;
}
```

#### 5xl (1366px - 1535px) - Стандартные мониторы 15-19"
```css
/* Особенности: Стандартный десктоп, много места */

/* Сетка */
.grid-cols-5xl-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid-cols-5xl-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.grid-cols-5xl-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.grid-cols-5xl-7 { grid-template-columns: repeat(7, minmax(0, 1fr)); }

/* Компоненты */
.card-5xl { max-width: 1300px; }

/* Карточки аниме - 5-6 в ряд */
.anime-grid-5xl { 
  grid-template-columns: repeat(5, 1fr); 
  gap: 24px;
}

/* Профиль пользователя */
.profile-layout-5xl {
  grid-template-columns: 300px 1fr 300px;
  gap: 32px;
}

/* Видео плеер */
.player-5xl {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
}

/* Чат */
.chat-layout-5xl {
  grid-template-columns: 280px 1fr 300px;
}
```

#### 6xl (1536px - 1919px) - Большие мониторы 22-24"
```css
/* Особенности: Большой экран, можно показывать больше контента */

/* Сетка */
.grid-cols-6xl-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.grid-cols-6xl-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.grid-cols-6xl-7 { grid-template-columns: repeat(7, minmax(0, 1fr)); }
.grid-cols-6xl-8 { grid-template-columns: repeat(8, minmax(0, 1fr)); }

/* Компоненты */
.card-6xl { max-width: 1600px; }

/* Карточки аниме - 6 в ряд */
.anime-grid-6xl { 
  grid-template-columns: repeat(6, 1fr); 
  gap: 24px;
}

/* Профиль пользователя */
.profile-layout-6xl {
  grid-template-columns: 320px 1fr 320px;
  max-width: 1800px;
  margin: 0 auto;
}

/* Видео плеер */
.player-6xl {
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
}

/* Чат */
.chat-layout-6xl {
  grid-template-columns: 320px 1fr 350px;
}

/* Детали аниме */
.anime-detail-6xl {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 40px;
}
```

#### 7xl (1920px - 2559px) - QHD мониторы, MacBook Pro 16"
```css
/* Особенности: QHD разрешение, очень много места */

/* Сетка */
.grid-cols-7xl-6 { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.grid-cols-7xl-7 { grid-template-columns: repeat(7, minmax(0, 1fr)); }
.grid-cols-7xl-8 { grid-template-columns: repeat(8, minmax(0, 1fr)); }
.grid-cols-7xl-9 { grid-template-columns: repeat(9, minmax(0, 1fr)); }

/* Компоненты */
.card-7xl { max-width: 2000px; }

/* Карточки аниме - 7 в ряд */
.anime-grid-7xl { 
  grid-template-columns: repeat(7, 1fr); 
  gap: 28px;
}

/* Профиль пользователя */
.profile-layout-7xl {
  grid-template-columns: 350px 1fr 350px;
  max-width: 2200px;
  margin: 0 auto;
}

/* Видео плеер */
.player-7xl {
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
}

/* Чат */
.chat-layout-7xl {
  grid-template-columns: 350px 1fr 400px;
}

/* Детали аниме */
.anime-detail-7xl {
  display: grid;
  grid-template-columns: 450px 1fr 300px;
  gap: 48px;
}

/* Каталог с фильтрами */
.catalog-layout-7xl {
  display: grid;
  grid-template-columns: 280px 1fr 300px;
  gap: 32px;
}
```

#### 8xl (2560px+) - 4K мониторы, ультра-широкие
```css
/* Особенности: Огромный экран, максимум контента */

/* Сетка */
.grid-cols-8xl-7 { grid-template-columns: repeat(7, minmax(0, 1fr)); }
.grid-cols-8xl-8 { grid-template-columns: repeat(8, minmax(0, 1fr)); }
.grid-cols-8xl-9 { grid-template-columns: repeat(9, minmax(0, 1fr)); }
.grid-cols-8xl-10 { grid-template-columns: repeat(10, minmax(0, 1fr)); }
.grid-cols-8xl-12 { grid-template-columns: repeat(12, minmax(0, 1fr)); }

/* Компоненты */
.card-8xl { max-width: 2400px; }

/* Карточки аниме - 8-10 в ряд */
.anime-grid-8xl { 
  grid-template-columns: repeat(8, 1fr); 
  gap: 32px;
  max-width: 2400px;
  margin: 0 auto;
}

/* Профиль пользователя */
.profile-layout-8xl {
  grid-template-columns: 400px 1fr 400px;
  max-width: 2800px;
  margin: 0 auto;
}

/* Видео плеер */
.player-8xl {
  width: 100%;
  max-width: 2200px;
  margin: 0 auto;
}

/* Чат */
.chat-layout-8xl {
  grid-template-columns: 400px 1fr 450px;
}

/* Детали аниме */
.anime-detail-8xl {
  display: grid;
  grid-template-columns: 500px 1fr 400px;
  gap: 56px;
  max-width: 2600px;
  margin: 0 auto;
}

/* Каталог с фильтрами */
.catalog-layout-8xl {
  display: grid;
  grid-template-columns: 320px 1fr 400px;
  gap: 40px;
  max-width: 2800px;
  margin: 0 auto;
}

/* Центрирование контента для больших экранов */
.content-center-8xl {
  max-width: 2400px;
  margin: 0 auto;
  padding: 0 48px;
}
```

---

## 4. Детальный план по страницам и компонентам

### 4.1 Главная страница (HomeView)

#### Мобильная адаптация (xs-min - xl)

**Структура:**
```
┌─────────────────────────┐
│      Header (sticky)    │  - Лого + поиск + профиль
├─────────────────────────┤
│    Hero Banner          │  - Баннер (1 колонка)
├─────────────────────────┤
│   Продолжить просмотр   │  - Горизонтальный скролл
├─────────────────────────┤
│   Рекомендации          │  - 2-3 колонки
├─────────────────────────┤
│   Популярное            │  - 2-3 колонки
├─────────────────────────┤
│   Новинки               │  - 2-3 колонки
├─────────────────────────┤
│      Bottom Nav         │  - 5 иконок (мобильная навигация)
└─────────────────────────┘
```

**Стили по breakpoints:**

| Элемент | xs-min (280-319) | xs (320-374) | sm (375-413) | md (414-479) | lg (480-599) | xl (600-767) |
|---------|-----------------|--------------|--------------|--------------|--------------|--------------|
| Header height | 48px | 52px | 56px | 60px | 64px | 68px |
| Banner height | 180px | 200px | 220px | 250px | 280px | 320px |
| Banner font | 16px | 18px | 20px | 22px | 24px | 28px |
| Section title | 14px | 16px | 18px | 20px | 22px | 24px |
| Card width | 120px | 140px | 160px | 180px | 200px | 220px |
| Card height | 170px | 200px | 230px | 260px | 290px | 320px |
| Scroll items | 2 | 2-3 | 3 | 3-4 | 4 | 5 |
| Grid columns | 2 | 2 | 2 | 2-3 | 3 | 3-4 |
| Bottom nav icons | 24px | 26px | 28px | 30px | 32px | 34px |
| Gap between sections | 16px | 20px | 24px | 28px | 32px | 36px |

**Особенности:**
- xs-min: Только 2 колонки, упрощенный баннер
- xs: Добавляется hover эффект на карточки
- sm: Появляется категория "Продолжить просмотр"
- md: 3 колонки в сетке, больше информации на карточке
- lg: Промежуточный размер, 3-4 колонки
- xl: Планшетный вид, 4 колонки, боковая панель может появляться

#### Компьютерная адаптация (2xl - 8xl)

| Элемент | 2xl (768-1023) | 3xl (1024-1279) | 4xl (1280-1365) | 5xl (1366-1535) | 6xl (1536-1919) | 7xl (1920-2559) | 8xl (2560+) |
|---------|---------------|-----------------|-----------------|-----------------|-----------------|-----------------|-------------|
| Header height | 72px | 80px | 84px | 88px | 92px | 96px | 100px |
| Banner height | 360px | 400px | 440px | 480px | 520px | 560px | 600px |
| Banner font | 32px | 36px | 40px | 44px | 48px | 52px | 56px |
| Section title | 26px | 28px | 30px | 32px | 34px | 36px | 38px |
| Card width | 200px | 220px | 240px | 260px | 280px | 300px | 320px |
| Card height | 290px | 320px | 350px | 380px | 410px | 440px | 470px |
| Scroll items | 4-5 | 5-6 | 6 | 6-7 | 7-8 | 8-9 | 10 |
| Grid columns | 3-4 | 4 | 4-5 | 5 | 5-6 | 6-7 | 8 |
| Sidebar width | - | - | 260px | 280px | 320px | 350px | 400px |
| Max content width | 700px | 900px | 1100px | 1300px | 1600px | 2000px | 2400px |

### 4.2 Каталог аниме (AnimeCatalogView)

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│      Header             │
├─────────────────────────┤
│  Search + Filters       │  - Выпадающие фильтры
├─────────────────────────┤
│  Active Filters         │  - Теги выбранных фильтров
├─────────────────────────┤
│  Sort Dropdown          │  - Сортировка
├─────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐│
│ │Card │ │Card │ │Card ││  - Сетка карточек
│ │     │ │     │ │     ││
│ └─────┘ └─────┘ └─────┘│
│ ┌─────┐ ┌─────┐ ┌─────┐│
│ │Card │ │Card │ │Card ││
│ └─────┘ └─────┘ └─────┘│
├─────────────────────────┤
│      Pagination         │  - Номера страниц
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

**Фильтры (мобильные):**
- xs-min/xs: Фильтры в модальном окне (кнопка "Фильтры")
- sm/md: Фильтры в выпадающей панели сверху
- lg/xl: Фильтры слева в боковой панели (аккордеон)

**Сетка (мобильные):**

| Breakpoint | Колонок | Card Width | Gap |
|------------|---------|------------|-----|
| xs-min | 2 | 130px | 8px |
| xs | 2 | 150px | 10px |
| sm | 2 | 170px | 12px |
| md | 2-3 | 190px | 14px |
| lg | 3 | 210px | 16px |
| xl | 3-4 | 230px | 18px |

**Дополнительная информация на карточке:**
- xs-min: Только постер + название
- xs: + год выхода
- sm: + тип (TV/Movie) + рейтинг
- md: + жанры (2-3)
- lg: + полное описание
- xl: + студия, эпизоды

#### Компьютерная адаптация

**Структура:**
```
┌─────────────────────────────────────────────────────────┐
│                        Header                           │
├────────────┬────────────────────────────────────────────┤
│  Sidebar   │  Search + Sort                             │
│            ├────────────────────────────────────────────┤
│  Filters:  │  Active Filters                            │
│  - Genre   ├────────────────────────────────────────────┤
│  - Year    │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│  - Type    │  │Card│ │Card│ │Card│ │Card│ │Card│       │
│  - Status  │  └────┘ └────┘ └────┘ └────┘ └────┘       │
│  - Studio  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐       │
│  - Rating  │  │Card│ │Card│ │Card│ │Card│ │Card│       │
│            │  └────┘ └────┘ └────┘ └────┘ └────┘       │
│            ├────────────────────────────────────────────┤
│            │              Pagination                    │
└────────────┴────────────────────────────────────────────┘
```

**Боковая панель (компьютеры):**

| Breakpoint | Sidebar Width | Collapsible |
|------------|---------------|-------------|
| 2xl | 240px (overlay) | Да |
| 3xl | 260px | Да |
| 4xl | 280px | Нет |
| 5xl | 300px | Нет |
| 6xl | 340px | Нет |
| 7xl | 380px | Нет |
| 8xl | 420px | Нет |

**Сетка (компьютеры):**

| Breakpoint | Колонок | Card Width | Gap |
|------------|---------|------------|-----|
| 2xl | 3 | 200px | 16px |
| 3xl | 4 | 220px | 18px |
| 4xl | 4-5 | 240px | 20px |
| 5xl | 5 | 260px | 22px |
| 6xl | 5-6 | 280px | 24px |
| 7xl | 6-7 | 300px | 26px |
| 8xl | 8 | 320px | 28px |

### 4.3 Детали аниме (AnimeDetailView)

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│   ◄ Back    Share btn   │  - Header с кнопкой назад
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │                     │ │
│ │      Poster         │ │  - Постер (фулл ширина)
│ │                     │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│     Title (RU/EN/JP)    │  - Название
├─────────────────────────┤
│ ★ 8.5  •  TV  •  12 эп. │  - Meta информация
├─────────────────────────┤
│ [Смотреть] [В список]   │  - Кнопки действий
├─────────────────────────┤
│ Описание...             │  - Описание (спойлер)
├─────────────────────────┤
│ Жанры:                  │  - Теги жанров
│ ┌────┐ ┌────┐ ┌────┐   │
│ └────┘ └────┘ └────┘   │
├─────────────────────────┤
│ Сезон: 2024, Осень      │
│ Студия: Studio X        │
│ Режиссёр: Name          │
├─────────────────────────┤
│ ▶ Сезон 1  (12 эп.)    │  - Список эпизодов
│ ▶ Сезон 2  (24 эп.)    │
│ ▶ Сезон 3  (12 эп.)    │
├─────────────────────────┤
│ ┌────┐ ┌────┐ ┌────┐   │
│ │Эп 1│ │Эп 2│ │Эп 3│   │  - Эпизоды
│ └────┘ └────┘ └────┘   │
├─────────────────────────┤
│ Переводы:               │  - Выбор озвучки
│ ○ AniMedia              │
│ ○ AniLibria             │
│ ○ SHIZA                 │
├─────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐│
│ │Player│ │Info │ │Sim  ││  - Табы
├─────────────────────────┤
│      Comments           │  - Комментарии
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

**Размеры элементов:**

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Poster width | 100% | 100% | 100% | 100% | 100% | 100% |
| Poster max-width | 260px | 300px | 340px | 380px | 420px | 460px |
| Title font | 18px | 20px | 22px | 24px | 26px | 28px |
| Button height | 40px | 44px | 48px | 50px | 52px | 56px |
| Episode card | 60x34px | 70x40px | 80x45px | 90x50px | 100x56px | 110x60px |
| Genre tag | 24px h | 26px h | 28px h | 30px h | 32px h | 34px h |

#### Компьютерная адаптация

**Структура:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                              Header                                 │
├──────────────────────┬──────────────────────────────────────────────┤
│                      │                                              │
│    ┌──────────┐      │            Title (RU/EN/JP)                 │
│    │          │      │      ★ 8.5  •  TV  •  12 эп.                │
│    │  Poster  │      │                                              │
│    │          │      │   [Смотреть] [В список] [На заметку]        │
│    │          │      │                                              │
│    └──────────┘      │   Описание (полное)...                      │
│                      │                                              │
├──────────────────────┤   Жанры: [Action] [Sci-Fi] [Adventure]      │
│   Информация:        ├──────────────────────────────────────────────┤
│   • Сезон: 2024      │                                              │
│   • Студия: X        │   ┌─────────────────────────────────────┐   │
│   • Режиссёр: Y      │   │           Плеер / Эпизоды           │   │
│   • Тип: TV          │   │                                     │   │
│   • Статус: Ongoing  │   │   [Эп 1] [Эп 2] [Эп 3] ...          │   │
│                      │   │                                     │   │
├──────────────────────┤   └─────────────────────────────────────┘   │
│   Похожее:           │                                              │
│   ┌──┐ ┌──┐ ┌──┐    │   Переводы: [AniMedia] [AniLibria] [SHIZA]   │
│   └──┘ └──┘ └──┘    ├──────────────────────────────────────────────┤
│                      │                                              │
│   Рекомендации:      │            Комментарии                      │
│   ┌──┐ ┌──┐ ┌──┐    │                                              │
│   └──┘ └──┘ └──┘    │                                              │
└──────────────────────┴──────────────────────────────────────────────┘
```

**Размеры элементов:**

| Элемент | 2xl | 3xl | 4xl | 5xl | 6xl | 7xl | 8xl |
|---------|-----|-----|-----|-----|-----|-----|-----|
| Poster width | 300px | 340px | 380px | 420px | 480px | 540px | 600px |
| Main column | 1fr | 1fr | 1fr | 1fr | 600px | 700px | 800px |
| Sidebar | 260px | 280px | 300px | 340px | 380px | 420px | 480px |
| Title font | 28px | 32px | 36px | 40px | 44px | 48px | 52px |
| Button height | 48px | 52px | 56px | 60px | 64px | 68px | 72px |
| Episode card | 80x45px | 90x50px | 100x56px | 110x60px | 120x68px | 130x74px | 140x80px |

### 4.4 Профиль пользователя (ProfileView)

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│   ◄ Back    Edit        │  - Header
├─────────────────────────┤
│      ┌──────┐           │
│      │Avatar│  User     │  - Аватар + имя
│      └──────┘  @username│
│      ★ 150 аниме        │
│      ✐ 50 отзывов       │
├─────────────────────────┤
│ [Коллекция] [Избранное] │  - Табы
│ [Плейлисты] [Шортс]    │
├─────────────────────────┤
│                         │
│   ┌──┐ ┌──┐ ┌──┐       │  - Контент (сетка)
│   └──┘ └──┘ └──┘       │
│   ┌──┐ ┌──┐ ┌──┐       │
│   └──┘ └──┘ └──┘       │
│                         │
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

**Размеры:**

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Avatar | 64px | 72px | 80px | 88px | 96px | 104px |
| Avatar font | 24px | 28px | 32px | 36px | 40px | 44px |
| Username | 16px | 18px | 20px | 22px | 24px | 26px |
| Stats | 12px | 13px | 14px | 15px | 16px | 16px |
| Tab height | 36px | 40px | 44px | 48px | 52px | 56px |
| Grid columns | 2 | 2 | 2-3 | 3 | 3-4 | 4 |

#### Компьютерная адаптация

**Структура:**
```
┌─────────────────────────────────────────────────────────┐
│                         Header                          │
├─────────────┬───────────────────────────────────────────┤
│             │                                           │
│  ┌───────┐  │           User Info                       │
│  │Avatar │  │     Username, @handle                     │
│  │ 120px │  │     ★ 150 anime  ✐ 50 reviews            │
│  └───────┘  │                                           │
│             │     [Edit Profile] [Share] [Settings]    │
│  Stats:     ├───────────────────────────────────────────┤
│  • 150 anime│  [Коллекция] [Избранное] [Плейлисты] [Шортс]│
│  • 50 reviews├───────────────────────────────────────────┤
│  • 10 lists │                                           │
│  • Joined   │   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐      │
│             │   │Card│ │Card│ │Card│ │Card│ │Card│      │
│  Badges:    │   └────┘ └────┘ └────┘ └────┘ └────┘      │
│  🏆🏅       │   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐      │
│             │   │Card│ │Card│ │Card│ │Card│ │Card│      │
│             │   └────┘ └────┘ └────┘ └────┘ └────┘      │
└─────────────┴───────────────────────────────────────────┘
```

### 4.5 Плейлисты (PlaylistsView)

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│   ◄ Back  + Create      │  - Header
├─────────────────────────┤
│    [Все] [Мои] [Популяр]│  - Категории
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │ ┌─────┐  Playlist 1 │ │  - Карточка плейлиста
│ │ │Cover│  12 аниме   │ │
│ │ └─────┘  ★ 4.5      │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │ ┌─────┐  Playlist 2 │ │
│ │ │Cover│  8 аниме    │ │
│ │ └─────┘  ★ 4.2      │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

**Размеры:**

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Cover size | 80px | 90px | 100px | 110px | 120px | 130px |
| Card height | 100px | 110px | 120px | 130px | 140px | 150px |
| Title | 14px | 15px | 16px | 17px | 18px | 20px |
| Grid columns | 1 | 1 | 1 | 1-2 | 2 | 2 |

#### Компьютерная адаптация

| Элемент | 2xl | 3xl | 4xl | 5xl | 6xl | 7xl | 8xl |
|---------|-----|-----|-----|-----|-----|-----|-----|
| Cover size | 140px | 160px | 180px | 200px | 220px | 240px | 260px |
| Card height | 160px | 180px | 200px | 220px | 240px | 260px | 280px |
| Grid columns | 2 | 2-3 | 3 | 3-4 | 4 | 4-5 | 5-6 |

### 4.6 Чат (ChatsView)

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│   ◄ Chats      + New    │  - Header
├─────────────────────────┤
│  🔍 Search...           │  - Поиск
├─────────────────────────┤
│ [All] [Groups] [Private]│  - Фильтры
├─────────────────────────┤
│ ┌──┐ User 1    12:30    │  - Список чатов
│ │A │ Last message...    │
│ └──┘ ●●●                │
│ ┌──┐ User 2    11:45    │
│ │B │ Last message...    │
│ └──┘                  │
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

**Детали чата:**
```
┌─────────────────────────┐
│ ◄ User Name      ⋮      │  - Header чата
├─────────────────────────┤
│ ┌──┐                   │
│ │A │ Message 1         │
│ │12:30│               │
│ └──────────────────────┘
│        Message 2 ┌──┐   │
│              12:31│B │   │
│                   └──┘  │
│ ┌──────────────────────┐│
│ │ Message 3            ││
│ │ 12:35               ││
│ └──┘                   │
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │ Type message...   📎│ │  - Input
│ └─────────────────────┘ │
└─────────────────────────┘
```

**Размеры:**

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Avatar | 40px | 44px | 48px | 52px | 56px | 60px |
| Message max-width | 75% | 75% | 80% | 80% | 85% | 85% |
| Input height | 44px | 48px | 52px | 56px | 60px | 64px |
| Chat list item | 60px | 64px | 68px | 72px | 76px | 80px |

#### Компьютерная адаптация

**Структура:**
```
┌────────────────┬───────────────────────────────┐
│   Chats List   │        Chat Window            │
│                ├───────────────────────────────┤
│  🔍 Search     │  User Name          ⋮        │
│                ├───────────────────────────────┤
│  [All][Groups] │                               │
│                │  ┌──┐ Message 1               │
│  ┌──┐ User 1   │  │A │ 12:30                   │
│  │A │ msg...   │  └─────────────────────────┘ │
│  └──┘ ●●●      │                               │
│                │        Message 2    ┌──┐     │
│  ┌──┐ User 2   │                    │B │     │
│  │B │ msg...   │                    └──┘ 12:31│
│  └──┘          │                               │
│                │  ┌─────────────────────────┐  │
│                │  │ Message 3               │  │
│                │  └──┘ 12:35                │  │
│                ├───────────────────────────────┤
│                │  ┌─────────────────────┐ 📎  │
│                │  │ Type message...     │    │
│                │  └─────────────────────┘     │
└────────────────┴───────────────────────────────┘
```

| Элемент | 2xl | 3xl | 4xl | 5xl | 6xl | 7xl | 8xl |
|---------|-----|-----|-----|-----|-----|-----|-----|
| Sidebar width | 280px | 300px | 320px | 340px | 380px | 420px | 480px |
| Chat window | 1fr | 1fr | 1fr | 1fr | 600px | 700px | 800px |
| Avatar | 48px | 52px | 56px | 60px | 64px | 68px | 72px |
| Message max-width | 65% | 70% | 70% | 65% | 60% | 55% | 50% |

### 4.7 Навигация

#### Мобильная навигация (Bottom Nav)

**Структура:**
```
┌─────────────────────────┐
│        Контент          │
│          ...            │
├─────────────────────────┤
│ 🏠  🎬  📋  🔔  👤     │  - 5 иконок
│ГлавнаяКаталогПлейлистыУведомлПрофиль
└─────────────────────────┘
```

**Размеры:**

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Nav height | 50px | 54px | 58px | 62px | 66px | 70px |
| Icon size | 22px | 24px | 26px | 28px | 30px | 32px |
| Label font | 9px | 10px | 11px | 12px | 12px | 13px |
| Icon spacing | 8px | 10px | 12px | 14px | 16px | 18px |

**Поведение:**
- xs-min: Только иконки, без подписей
- xs: Иконки + короткие подписи (2-3 буквы)
- sm+: Полные подписи
- lg+: Возможно появление боковой навигации

#### Компьютерная навигация (Sidebar)

**Структура:**
```
┌────────────────────────┐
│     Logo               │
├────────────────────────┤
│ 🏠 Главная             │
│ 🎬 Каталог             │
│ 📋 Плейлисты           │
│ 💬 Чаты                │
│ 🔔 Уведомления         │
│ ⚙️ Настройки           │
├────────────────────────┤
│ User Profile           │
└────────────────────────┘
```

| Элемент | 2xl | 3xl | 4xl | 5xl | 6xl | 7xl | 8xl |
|---------|-----|-----|-----|-----|-----|-----|-----|
| Sidebar width | 200px | 220px | 240px | 260px | 280px | 300px | 320px |
| Nav item height | 44px | 48px | 52px | 56px | 60px | 64px | 68px |
| Icon size | 20px | 22px | 24px | 26px | 28px | 30px | 32px |
| Font size | 14px | 15px | 16px | 16px | 17px | 18px | 18px |
| Logo height | 36px | 40px | 44px | 48px | 52px | 56px | 60px |

### 4.8 Видеоплеер

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│ ┌─────────────────────┐ │
│ │                     │ │
│ │      Video          │ │  - 16:9 или адаптивно
│ │                     │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│ ◄  Эпизод 5  ►   ⚙️    │  - Controls
├─────────────────────────┤
│ [1][2][3][4][5][6]...  │  - Эпизоды
├─────────────────────────┤
│ Перевод: AniMedia  ▼   │  - Выбор озвучки
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

**Floating Player (мобильный):**
```
┌──────────┐
│ ▌▌ ┐ X   │  - Мини плеер справа внизу
│ └───┘    │
└──────────┘
→ При нажатии разворачивается
```

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Player aspect | 16:9 | 16:9 | 16:9 | 16:9 | 16:9 | 16:9 |
| Control height | 36px | 40px | 44px | 48px | 52px | 56px |
| Episode button | 36px | 40px | 44px | 48px | 52px | 56px |
| Floating size | 120x68px | 140x79px | 160x90px | 180x101px | 200x112px | 220x124px |

#### Компьютерная адаптация

| Элемент | 2xl | 3xl | 4xl | 5xl | 6xl | 7xl | 8xl |
|---------|-----|-----|-----|-----|-----|-----|-----|
| Player max-width | 720px | 960px | 1120px | 1280px | 1440px | 1680px | 1920px |
| Control height | 48px | 52px | 56px | 60px | 64px | 68px | 72px |
| Episode button | 48px | 52px | 56px | 60px | 64px | 68px | 72px |
| Floating size | 200x112px | 240x135px | 280x158px | 320x180px | 360x202px | 400x225px | 440x248px |

### 4.9 Поиск (SearchView)

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│ [◄] [Search input    ] X│  - Search bar
├─────────────────────────┤
│ [История]              │  - Недавние поиски
│ ┌─────┐ ┌─────┐ ┌─────┐│
│ │Item │ │Item │ │Item ││
│ └─────┘ └─────┘ └─────┘│
├─────────────────────────┤
│ [Популярное]           │  - Популярные запросы
│ ┌─────┐ ┌─────┐ ┌─────┐│
│ │Item │ │Item │ │Item ││
│ └─────┘ └─────┘ └─────┘│
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

**Результаты:**
```
┌─────────────────────────┐
│ [◄] Results: 42    [Filter]│
├─────────────────────────┤
│ ┌─────┐ Title           │
│ │Poster│ Year • Type    │
│ │     │ ★ 8.5           │
│ └─────┘                 │
│ ┌─────┐ Title           │
│ │Poster│ Year • Type    │
│ └─────┘                 │
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Search height | 40px | 44px | 48px | 52px | 56px | 60px |
| Suggestion item | 36px | 40px | 44px | 48px | 52px | 56px |
| Result card | 100% | 100% | 100% | 100% | 100% | 100% |
| Result poster | 60px | 70px | 80px | 90px | 100px | 110px |

#### Компьютерная адаптация

| Элемент | 2xl | 3xl | 4xl | 5xl | 6xl | 7xl | 8xl |
|---------|-----|-----|-----|-----|-----|-----|-----|
| Search width | 500px | 600px | 700px | 800px | 900px | 1000px | 1100px |
| Search height | 52px | 56px | 60px | 64px | 68px | 72px | 76px |
| Suggestion dropdown | 500px | 600px | 700px | 800px | 900px | 1000px | 1100px |
| Result card | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| Result poster | 100px | 120px | 140px | 160px | 180px | 200px | 220px |
| Grid columns | 1 | 1 | 1-2 | 2 | 2 | 2-3 | 3 |

### 4.10 Уведомления (NotificationsView)

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│   ◄ Back    [Read All]  │
├─────────────────────────┤
│ [Все] [Новые] [Коммент] │  - Фильтры
├─────────────────────────┤
│ ┌──┐ User liked your    │
│ │A │ review             │
│ └──┘ 2 hours ago        │
├─────────────────────────┤
│ ┌──┐ New episode: X     │
│ │B │                    │
│ └──┘ 5 hours ago        │
├─────────────────────────┤
│ ┌──┐ @user mentioned    │
│ │C │ you in comments    │
│ └──┘ 1 day ago          │
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Item height | 56px | 60px | 64px | 68px | 72px | 76px |
| Avatar | 36px | 40px | 44px | 48px | 52px | 56px |
| Icon size | 16px | 18px | 20px | 22px | 24px | 26px |

#### Компьютерная адаптация

| Элемент | 2xl | 3xl | 4xl | 5xl | 6xl | 7xl | 8xl |
|---------|-----|-----|-----|-----|-----|-----|-----|
| Item height | 72px | 80px | 88px | 96px | 104px | 112px | 120px |
| Avatar | 52px | 56px | 60px | 64px | 68px | 72px | 76px |
| Max width | 700px | 800px | 900px | 1000px | 1100px | 1200px | 1400px |

### 4.11 Настройки (SettingsView)

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│   ◄ Back    Save        │
├─────────────────────────┤
│  Профиль                │
│  ├─ Аватар             │
│  ├─ Имя                │
│  ├─ Email              │
│  └─ Пароль             │
├─────────────────────────┤
│  Уведомления            │
│  ├─ Email уведомления  │
│  ├─ Push уведомления   │
│  └─ Звук               │
├─────────────────────────┤
│  Внешний вид            │
│  ├─ Тема               │
│  ├─ Язык               │
│  └─ Шрифт              │
├─────────────────────────┤
│  Конфиденциальность     │
│  ├─ Приватный профиль   │
│  └─ Показывать онлайн  │
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Section padding | 12px | 16px | 20px | 24px | 28px | 32px |
| Item height | 44px | 48px | 52px | 56px | 60px | 64px |
| Label font | 13px | 14px | 15px | 16px | 16px | 17px |
| Input height | 36px | 40px | 44px | 48px | 52px | 56px |

#### Компьютерная адаптация

**Структура:**
```
┌─────────────────────────────────────────────────────────┐
│   ◄ Back                            [Save Changes]      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌────────────────────────────────┐  │
│  │              │  │                                │  │
│  │  Navigation  │  │       Content Area             │  │
│  │              │  │                                │  │
│  │ • Профиль    │  │   [Form Fields]                │  │
│  │ • Уведомлен. │  │                                │  │
│  │ • Внешний вид│  │                                │  │
│  │ • Приватность│  │                                │  │
│  │              │  │                                │  │
│  └──────────────┘  └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

| Элемент | 2xl | 3xl | 4xl | 5xl | 6xl | 7xl | 8xl |
|---------|-----|-----|-----|-----|-----|-----|-----|
| Sidebar width | 220px | 240px | 260px | 280px | 300px | 320px | 340px |
| Content max-width | 600px | 700px | 800px | 900px | 1000px | 1100px | 1200px |
| Form field height | 48px | 52px | 56px | 60px | 64px | 68px | 72px |

### 4.12 Reactor / Shorts (ReactorView)

#### Мобильная адаптация

**Структура:**
```
┌─────────────────────────┐
│   [Reactor]             │  - Tabs: Подписки / Для вас
├─────────────────────────┤
│ ┌─────────────────────┐ │
│ │                     │ │
│ │     Video 16:9      │ │  - Полноэкранное видео
│ │                     │ │
│ │  ┌─────────────┐    │ │
│ │  │ @username   │    │ │
│ │  │ Description │    │ │
│ │  └─────────────┘    │ │
│ │                     │ │
│ │  [♥] [💬] [↗️]     │ │  - Actions
│ └─────────────────────┘ │
│    ← Prev  |  Next →   │  - Навигация
├─────────────────────────┤
│      Bottom Nav         │
└─────────────────────────┘
```

**Swipe навигация:**
- Свайп вверх/вниз для переключения между видео
- Свайп влево/вправо для переключения эпизодов

| Элемент | xs-min | xs | sm | md | lg | xl |
|---------|--------|-----|-----|-----|-----|-----|
| Video height | 70vh | 72vh | 75vh | 78vh | 80vh | 82vh |
| Action button | 32px | 36px | 40px | 44px | 48px | 52px |
| Username font | 14px | 15px | 16px | 17px | 18px | 20px |

#### Компьютерная адаптация

| Элемент | 2xl | 3xl | 4xl | 5xl | 6xl | 7xl | 8xl |
|---------|-----|-----|-----|-----|-----|-----|-----|
| Video max-width | 500px | 600px | 700px | 800px | 900px | 1000px | 1100px |
| Video max-height | 80vh | 80vh | 80vh | 85vh | 85vh | 85vh | 85vh |
| Action button | 48px | 52px | 56px | 60px | 64px | 68px | 72px |
| Sidebar visible | Нет | Нет | Нет | Да | Да | Да | Да |

---

## 5. Конфигурация Tailwind

### 5.1 Расширенная конфигурация breakpoints

```javascript
// tailwind.config.js
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      screens: {
        // Мобильные устройства
        'xs-min': '280px',
        'xs': '320px',
        'sm': '375px',
        'md': '414px',
        'lg': '480px',
        'xl': '600px',
        
        // Компьютеры
        '2xl': '768px',
        '3xl': '1024px',
        '4xl': '1280px',
        '5xl': '1366px',
        '6xl': '1536px