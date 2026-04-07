<script setup lang="ts">
defineProps<{
  name: string
  size?: number
}>()
</script>

<template>
  <svg 
    :width="size || 20" 
    :height="size || 20" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    stroke-width="2" 
    stroke-linecap="round" 
    stroke-linejoin="round"
    class="sakura-icon"
    style="display: inline-block; vertical-align: middle; flex-shrink: 0;"
  >
    <!-- Колесо фортуны / Рулетка -->
    <template v-if="name === 'wheel'">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
    </template>

    <!-- Статистика / График -->
    <template v-else-if="name === 'chart'">
      <path d="M3 3v18h18" />
      <path d="M7 14l4-4 4 4 5-5" />
    </template>

    <!-- Настройки -->
    <template v-else-if="name === 'settings'">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
    </template>

    <!-- Корзина -->
    <template v-else-if="name === 'trash'">
      <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6" />
    </template>

    <!-- Кино / Плей -->
    <template v-else-if="name === 'play'">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="M10 9l5 3-5 3V9z" fill="currentColor" />
    </template>

    <!-- Плюс -->
    <template v-else-if="name === 'plus'">
      <path d="M12 5v14M5 12h14" />
    </template>

    <!-- Крест -->
    <template v-else-if="name === 'x'">
      <path d="M18 6L6 18M6 6l12 12" />
    </template>

    <!-- Карандаш -->
    <template v-else-if="name === 'edit'">
      <path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
    </template>

    <!-- История / Свиток -->
    <template v-else-if="name === 'history'">
      <path d="M3 12a9 9 0 109-9 9.75 9.75 0 00-6.74 2.74L3 8" />
      <path d="M3 3v5h5" />
    </template>

    <!-- Палитра -->
    <template v-else-if="name === 'palette'">
      <circle cx="13.5" cy="6.5" r="2.5" />
      <circle cx="17.5" cy="10.5" r="2.5" />
      <circle cx="8.5" cy="7.5" r="2.5" />
      <circle cx="6.5" cy="12.5" r="2.5" />
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 011.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.555C21.965 6.012 17.461 2 12 2z" />
    </template>

    <!-- Солнце -->
    <template v-else-if="name === 'sun'">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
    </template>

    <!-- Луна -->
    <template v-else-if="name === 'moon'">
      <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
    </template>

    <!-- Картинка -->
    <template v-else-if="name === 'image'">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="9" cy="9" r="2" />
      <path d="M21 15l-3.086-3.086a2 2 0 00-2.828 0L6 21" />
    </template>

    <!-- Заметка -->
    <template v-else-if="name === 'file-text'">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
    </template>

    <!-- Радуга -->
    <template v-else-if="name === 'rainbow'">
      <path d="M2 16c2-4 4-6 8-6s6 4 8 6M2 12c2-4 4-6 8-6s6 4 8 6M2 8c2-4 4-6 8-6s6 4 8 6M2 20c2-4 4-6 8-6s6 4 8 6" />
    </template>

    <!-- Мерцание / Sparkle -->
    <template v-else-if="name === 'sparkle'">
      <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" fill="currentColor" />
    </template>

    <!-- Молния -->
    <template v-else-if="name === 'zap'">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="currentColor" />
    </template>

    <!-- Звук вкл -->
    <template v-else-if="name === 'volume'">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="currentColor" />
      <path d="M15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14" />
    </template>

    <!-- Звук выкл -->
    <template v-else-if="name === 'volume-x'">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="currentColor" />
      <path d="M23 9l-6 6M17 9l6 6" />
    </template>

    <!-- Весы -->
    <template v-else-if="name === 'scale'">
      <path d="M16 16l-2 2a2 2 0 01-2-2 2 2 0 012-2l2-2M8 16l2-2a2 2 0 012 2 2 2 0 01-2 2l-2-2M12 4v6M4 12h16" />
    </template>

    <!-- Календарь -->
    <template v-else-if="name === 'calendar'">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01" />
    </template>

    <!-- Обновление -->
    <template v-else-if="name === 'refresh'">
      <path d="M23 4v6h-6M1 20v-6h6" />
      <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
    </template>

    <!-- Книги -->
    <template v-else-if="name === 'book'">
      <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
    </template>

    <!-- Папка -->
    <template v-else-if="name === 'folder'">
      <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
    </template>

    <!-- Сохранить -->
    <template v-else-if="name === 'save'">
      <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
      <path d="M17 21v-8H7v8M7 3v5h8" />
    </template>

    <!-- Экспорт -->
    <template v-else-if="name === 'export'">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
    </template>

    <!-- Импорт -->
    <template v-else-if="name === 'import'">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
    </template>

    <!-- Корона -->
    <template v-else-if="name === 'crown'">
      <path d="M2 17l3-7 5 4 2-6 2 6 5-4 3 7h-16z" fill="currentColor" />
    </template>

    <!-- Бег -->
    <template v-else-if="name === 'run'">
      <circle cx="5" cy="6" r="3" />
      <path d="M9 8l4 2-3 2 2 4-4-1M15 17l-2-5" />
    </template>

    <!-- Копировать -->
    <template v-else-if="name === 'copy'">
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
    </template>

    <!-- Человек / Пользователь -->
    <template v-else-if="name === 'user'">
      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </template>

    <!-- Люди -->
    <template v-else-if="name === 'users'">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
    </template>

    <!-- Группа -->
    <template v-else-if="name === 'group'">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
    </template>

    <!-- Чат -->
    <template v-else-if="name === 'message'">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </template>

    <!-- Чат пузырь -->
    <template v-else-if="name === 'chat'">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </template>

    <!-- Сердце -->
    <template v-else-if="name === 'heart'">
      <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" fill="currentColor" />
    </template>

    <!-- Огонь -->
    <template v-else-if="name === 'fire'">
      <path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z" fill="currentColor" />
    </template>

    <!-- Лампочка -->
    <template v-else-if="name === 'lightbulb'">
      <path d="M9 18h6M10 22h4M12 2a7 7 0 00-4 13.26V17a1 1 0 001 1h6a1 1 0 001-1v-1.74A7 7 0 0012 2z" />
    </template>

    <!-- Булавка -->
    <template v-else-if="name === 'pin'">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
      <circle cx="12" cy="10" r="3" />
    </template>

    <!-- Ракета -->
    <template v-else-if="name === 'rocket'">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 00-2.91-.09z" />
      <path d="M12 19l3-3m0 0l-3-3m3 3v-3M3 13l3 3m0 0l-3-3m3 3v-3" />
    </template>

    <!-- Портфель -->
    <template v-else-if="name === 'briefcase'">
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
    </template>

    <!-- Джойстик -->
    <template v-else-if="name === 'gamepad'">
      <line x1="6" y1="12" x2="10" y2="12" />
      <line x1="8" y1="10" x2="8" y2="14" />
      <rect x="14" y="6" width="4" height="10" rx="1" />
      <path d="M15 8h.01M18 8h.01" />
    </template>

    <!-- Нота -->
    <template v-else-if="name === 'music'">
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    </template>

    <!-- Камера -->
    <template v-else-if="name === 'camera'">
      <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
      <circle cx="12" cy="13" r="4" />
    </template>

    <!-- Кубок -->
    <template v-else-if="name === 'trophy'">
      <path d="M6 9H4.5a2.5 2.5 0 010-5H6M18 9h1.5a2.5 2.5 0 000-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22M18 2H6v7a6 6 0 1012 0V2z" />
    </template>

    <!-- Звезда -->
    <template v-else-if="name === 'star'">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" fill="currentColor" />
    </template>

    <!-- Звёзды блест -->
    <template v-else-if="name === 'sparkles'">
      <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z" />
      <path d="M5 19l.5 1.5L7 21l-1.5.5L5 23l-.5-1.5L3 21l1.5-.5L5 19z" />
    </template>

    <!-- Колокольчик -->
    <template v-else-if="name === 'bell'">
      <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0" />
    </template>

    <!-- Мешок денег -->
    <template v-else-if="name === 'dollar'">
      <line x1="12" y1="1" x2="12" y2="23" />
      <path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
    </template>

    <!-- Подарок -->
    <template v-else-if="name === 'gift'">
      <polyline points="20 12 20 22 4 22 4 12" />
      <rect x="2" y="7" width="20" height="5" />
      <line x1="12" y1="22" x2="12" y2="7" />
      <path d="M12 7H7.5a2.5 2.5 0 010-5C11 2 12 7 12 7zM12 7h4.5a2.5 2.5 0 000-5C13 2 12 7 12 7z" />
    </template>

    <!-- Глобус -->
    <template v-else-if="name === 'globe'">
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
    </template>

    <!-- Дом -->
    <template v-else-if="name === 'home'">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </template>

    <!-- Здание -->
    <template v-else-if="name === 'building'">
      <rect x="4" y="2" width="16" height="20" rx="2" />
      <path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01" />
    </template>

    <!-- Телефон -->
    <template v-else-if="name === 'phone'">
      <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z" />
    </template>

    <!-- Ноутбук -->
    <template v-else-if="name === 'laptop'">
      <rect x="2" y="3" width="20" height="14" rx="2" />
      <line x1="2" y1="20" x2="22" y2="20" />
    </template>

    <!-- Замок -->
    <template v-else-if="name === 'lock'">
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 0110 0v4" />
    </template>

    <!-- Открытый замок -->
    <template v-else-if="name === 'unlock'">
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 019.9-1" />
    </template>

    <!-- Ключ -->
    <template v-else-if="name === 'key'">
      <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 017.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />
    </template>

    <!-- Глаз -->
    <template v-else-if="name === 'eye'">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </template>

    <!-- Щит -->
    <template v-else-if="name === 'shield'">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </template>

    <!-- QR код -->
    <template v-else-if="name === 'qr-code'">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
      <rect x="14" y="14" width="3" height="3" />
      <rect x="18" y="14" width="3" height="3" />
      <rect x="14" y="18" width="3" height="3" />
      <rect x="18" y="18" width="3" height="3" />
    </template>

    <!-- Цифры -->
    <template v-else-if="name === 'hash'">
      <line x1="4" y1="9" x2="20" y2="9" />
      <line x1="4" y1="15" x2="20" y2="15" />
      <line x1="10" y1="3" x2="8" y2="21" />
      <line x1="16" y1="3" x2="14" y2="21" />
    </template>

    <!-- Запрет -->
    <template v-else-if="name === 'ban'">
      <circle cx="12" cy="12" r="10" />
      <path d="M4.93 4.93l14.14 14.14" />
    </template>

    <!-- Свиток -->
    <template v-else-if="name === 'scroll'">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </template>

    <!-- Часы -->
    <template v-else-if="name === 'clock'">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </template>

    <!-- Язык -->
    <template v-else-if="name === 'languages'">
      <path d="M5 8l6 6M4 14l6-6 2-3M2 5h12M7 2h1M22 22l-5-10-5 10M14 18h6" />
    </template>

    <!-- Линейка -->
    <template v-else-if="name === 'ruler'">
      <path d="M21.21 15.89A10 10 0 118 2.83M22 12A10 10 0 0012 2v10z" />
    </template>

    <!-- Температура -->
    <template v-else-if="name === 'thermometer'">
      <path d="M14 14.76V3.5a2.5 2.5 0 00-5 0v11.26a4.5 4.5 0 105 0z" />
    </template>

    <!-- Основатели -->
    <template v-else-if="name === 'landmark'">
      <path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6M9 9h.01M15 9h.01M9 13h.01M15 13h.01" />
    </template>

    <!-- Галстук -->
    <template v-else-if="name === 'suitcase'">
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
    </template>

    <!-- Микрофон -->
    <template v-else-if="name === 'mic'">
      <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
      <path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8" />
    </template>

    <!-- Маски / Театр -->
    <template v-else-if="name === 'theater'">
      <path d="M2 10s3-3 10-3 10 3 10 3M2 14s3 3 10 3 10-3 10-3" />
      <circle cx="8" cy="10" r="2" />
      <circle cx="16" cy="10" r="2" />
    </template>

    <!-- Мегафон -->
    <template v-else-if="name === 'announcement'">
      <path d="M22 8a2 2 0 01-2 2c-2 0-4-1-5.6-2.6L12 2 9.6 3.4C8 4.9 6 6 4 6a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V8z" />
      <path d="M12 11v4M12 17h.01" />
    </template>

    <!-- Мысли -->
    <template v-else-if="name === 'thought'">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 15v3M8 21h8M9 18h.01" />
    </template>

    <!-- Лайк -->
    <template v-else-if="name === 'thumbs-up'">
      <path d="M14 9V5a3 3 0 00-3-3l-4 9v11h11.28a2 2 0 002-1.7l1.38-9a2 2 0 00-2-2.3zM7 22H4a2 2 0 01-2-2v-7a2 2 0 012-2h3" />
    </template>

    <!-- Дизлайк -->
    <template v-else-if="name === 'thumbs-down'">
      <path d="M10 15v4a3 3 0 003 3l4-9V2H5.72a2 2 0 00-2 1.7l-1.38 9a2 2 0 002 2.3zm7-13h2.67A2.31 2.31 0 0122 4v7a2.31 2.31 0 01-2.33 2H17" />
    </template>

    <!-- Газета -->
    <template v-else-if="name === 'newspaper'">
      <path d="M20 21V5a2 2 0 00-2-2H6a2 2 0 00-2 2v16M4 7h16M4 11h16M4 15h16M8 19h8" />
    </template>

    <!-- Обезьяна -->
    <template v-else-if="name === 'eye-off'">
      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24M1 1l22 22" />
    </template>

    <!-- Дверь -->
    <template v-else-if="name === 'door'">
      <path d="M13 4h3a2 2 0 012 2v14M2 20h3M17 20h3M6 9v11" />
    </template>

    <!-- Сеть -->
    <template v-else-if="name === 'network'">
      <rect x="16" y="16" width="6" height="6" rx="1" />
      <rect x="2" y="16" width="6" height="6" rx="1" />
      <rect x="9" y="2" width="6" height="6" rx="1" />
      <path d="M5 16v-3a1 1 0 011-1h12a1 1 0 011 1v3M12 12V8" />
    </template>

    <!-- Тренд вверх -->
    <template v-else-if="name === 'trending-up'">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
      <polyline points="17 6 23 6 23 12" />
    </template>

    <!-- Тренд вниз -->
    <template v-else-if="name === 'trending-down'">
      <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
      <polyline points="17 18 23 18 23 12" />
    </template>

    <!-- Популярное -->
    <template v-else-if="name === 'hot'">
      <path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z" fill="currentColor" />
    </template>

    <!-- Подписки -->
    <template v-else-if="name === 'subscriptions'">
      <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="8.5" cy="7" r="4" />
      <line x1="23" y1="11" x2="17" y2="11" />
    </template>

    <!-- Проверено -->
    <template v-else-if="name === 'check'">
      <polyline points="20 6 9 17 4 12" />
    </template>

    <!-- Крест маленький -->
    <template v-else-if="name === 'x-small'">
      <path d="M18 6L6 18M6 6l12 12" />
    </template>

    <!-- Ссылка -->
    <template v-else-if="name === 'link'">
      <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
    </template>

    <!-- WhatsApp -->
    <template v-else-if="name === 'message-circle'">
      <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
    </template>

    <!-- VK -->
    <template v-else-if="name === 'vk'">
      <path d="M18.5 2h-13C4.12 2 3 3.12 3 4.5v15C3 20.88 4.12 22 5.5 22h13c1.38 0 2.5-1.12 2.5-2.5v-15C21 3.12 19.88 2 18.5 2z" />
      <path d="M14.5 7.5h-2c-.83 0-1.5.67-1.5 1.5v2c0 .83.67 1.5 1.5 1.5h2c.83 0 1.5-.67 1.5-1.5v-2c0-.83-.67-1.5-1.5-1.5zM10 13.5c0 .83.67 1.5 1.5 1.5h1c.83 0 1.5-.67 1.5-1.5v-1c0-.83-.67-1.5-1.5-1.5h-1c-.83 0-1.5.67-1.5 1.5v1z" />
    </template>

    <!-- Telegram -->
    <template v-else-if="name === 'send'">
      <path d="M22 2L11 13" />
      <path d="M22 2L15 22L11 13L2 9L22 2Z" />
    </template>

    <!-- Назад -->
    <template v-else-if="name === 'arrow-left'">
      <path d="M19 12H5M12 19l-7-7 7-7" />
    </template>

    <!-- Вперёд -->
    <template v-else-if="name === 'arrow-right'">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </template>

    <!-- Стрелка вверх -->
    <template v-else-if="name === 'arrow-up'">
      <path d="M12 19V5M5 12l7-7 7 7" />
    </template>

    <!-- Стрелка вниз -->
    <template v-else-if="name === 'arrow-down'">
      <path d="M12 5v14M19 12l-7 7-7-7" />
    </template>

    <!-- Поиск -->
    <template v-else-if="name === 'search'">
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" />
    </template>

    <!-- Меню -->
    <template v-else-if="name === 'menu'">
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </template>

    <!-- Закрыть -->
    <template v-else-if="name === 'close'">
      <path d="M18 6L6 18M6 6l12 12" />
    </template>

    <!-- Сортировка -->
    <template v-else-if="name === 'sort'">
      <path d="M3 6h18M6 12h12M9 18h6" />
    </template>

    <!-- Фильтр -->
    <template v-else-if="name === 'filter'">
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </template>

    <!-- Загрузка -->
    <template v-else-if="name === 'download'">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
    </template>

    <!-- Загрузка (альтернатива) -->
    <template v-else-if="name === 'download-alt'">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
    </template>

    <!-- Dice (игральные кости) -->
    <template v-else-if="name === 'dice'">
      <rect x="2" y="2" width="20" height="20" rx="3" />
      <circle cx="8" cy="8" r="1.5" fill="currentColor" />
      <circle cx="16" cy="8" r="1.5" fill="currentColor" />
      <circle cx="8" cy="16" r="1.5" fill="currentColor" />
      <circle cx="16" cy="16" r="1.5" fill="currentColor" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" />
    </template>

    <!-- Target (мишень) -->
    <template v-else-if="name === 'target'">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" fill="currentColor" />
    </template>

    <!-- Video -->
    <template v-else-if="name === 'video'">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="M10 9l5 3-5 3V9z" fill="currentColor" />
    </template>

    <!-- Film -->
    <template v-else-if="name === 'film'">
      <rect x="2" y="2" width="20" height="20" rx="2" />
      <line x1="7" y1="2" x2="7" y2="22" />
      <line x1="17" y1="2" x2="17" y2="22" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <line x1="2" y1="7" x2="7" y2="7" />
      <line x1="2" y1="17" x2="7" y2="17" />
      <line x1="17" y1="17" x2="22" y2="17" />
      <line x1="17" y1="7" x2="22" y2="7" />
    </template>

    <!-- Package -->
    <template v-else-if="name === 'package'">
      <path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
      <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
      <line x1="12" y1="22.08" x2="12" y2="12" />
    </template>

    <!-- Folder Open -->
    <template v-else-if="name === 'folder-open'">
      <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2v11z" />
      <path d="M2 10h20" />
    </template>

    <!-- Timer -->
    <template v-else-if="name === 'timer'">
      <circle cx="12" cy="13" r="8" />
      <path d="M12 9v4l2 2M5 3L2 6M22 6l-3-3M6 19l-2 2M18 19l2 2" />
    </template>

    <!-- Hourglass -->
    <template v-else-if="name === 'hourglass'">
      <path d="M5 22h14M5 2h14M17 22v-4l-5-9V2H8l-5 9v4" />
    </template>

    <!-- Smile -->
    <template v-else-if="name === 'smile'">
      <circle cx="12" cy="12" r="10" />
      <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01" />
    </template>

    <!-- Heart Broken -->
    <template v-else-if="name === 'heart-broken'">
      <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" />
      <path d="M2 2l20 20" stroke-width="3" />
    </template>

    <!-- Brain -->
    <template v-else-if="name === 'brain'">
      <path d="M9.5 2A2.5 2.5 0 017 4.5v15a2.5 2.5 0 005 0v-6a2.5 2.5 0 015 0v6a2.5 2.5 0 01-2.5 2.5H12" />
      <path d="M14.5 2A2.5 2.5 0 0012 4.5v15a2.5 2.5 0 005 0v-6a2.5 2.5 0 015 0v6a2.5 2.5 0 01-2.5 2.5H17" />
    </template>

    <!-- Hard Hat -->
    <template v-else-if="name === 'hard-hat'">
      <path d="M2 18a1 1 0 000 2h20a1 1 0 000-2H2zM5 18v-5a4 4 0 018 0v5" />
      <path d="M12 2v4M8 6h8" />
    </template>

    <!-- Mail -->
    <template v-else-if="name === 'mail'">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <polyline points="22,6 12,13 2,6" />
    </template>

    <!-- Inbox -->
    <template v-else-if="name === 'inbox'">
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z" />
    </template>

    <!-- Castle -->
    <template v-else-if="name === 'castle'">
      <path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6" />
    </template>

    <!-- Factory -->
    <template v-else-if="name === 'factory'">
      <path d="M2 20a2 2 0 002 2h16a2 2 0 002-2V8l-7 5V8l-7 5V4a2 2 0 00-2-2H4a2 2 0 00-2 2z" />
      <path d="M10 11v6M14 11v6" />
    </template>

    <!-- Map Pin -->
    <template v-else-if="name === 'map-pin'">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
      <circle cx="12" cy="10" r="3" />
    </template>

    <!-- Map -->
    <template v-else-if="name === 'map'">
      <path d="M1 6v16l7-4 8 4 7-4V2l-7 4-8-4-7 4z" />
      <path d="M8 2v16M16 6v16" />
    </template>

    <!-- Plane -->
    <template v-else-if="name === 'plane'">
      <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
    </template>

    <!-- Car -->
    <template v-else-if="name === 'car'">
      <path d="M14 16H9m10 0h3v-3.15a1 1 0 00-.84-.99L16 11l-2.7-3.6a1 1 0 00-.8-.4H5.24a2 2 0 00-1.8 1.1l-.8 1.63A6 6 0 002 18.42V20h6" />
      <circle cx="7.5" cy="16.5" r="2.5" />
      <circle cx="16.5" cy="16.5" r="2.5" />
    </template>

    <!-- Train -->
    <template v-else-if="name === 'train'">
      <rect x="4" y="3" width="16" height="16" rx="2" />
      <path d="M4 11V7a2 2 0 012-2h12a2 2 0 012 2v4M8 15v5M16 15v5M8 19h8" />
      <circle cx="12" cy="15" r="2" />
    </template>

    <!-- Clipboard -->
    <template v-else-if="name === 'clipboard'">
      <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" />
    </template>

    <!-- Headphones -->
    <template v-else-if="name === 'headphones'">
      <path d="M3 18v-6a9 9 0 0118 0v6" />
      <path d="M21 19a2 2 0 01-2 2h-1a2 2 0 01-2-2v-3a2 2 0 012-2h3zM3 19a2 2 0 002 2h1a2 2 0 002-2v-3a2 2 0 00-2-2H3z" />
    </template>

    <!-- Piano -->
    <template v-else-if="name === 'piano'">
      <rect x="2" y="3" width="20" height="18" rx="2" />
      <line x1="6" y1="3" x2="6" y2="11" />
      <line x1="10" y1="3" x2="10" y2="11" />
      <line x1="14" y1="3" x2="14" y2="11" />
      <line x1="18" y1="3" x2="18" y2="11" />
      <line x1="6" y1="15" x2="6" y2="21" />
      <line x1="10" y1="15" x2="10" y2="21" />
      <line x1="14" y1="15" x2="14" y2="21" />
      <line x1="18" y1="15" x2="18" y2="21" />
    </template>

    <!-- Credit Card -->
    <template v-else-if="name === 'credit-card'">
      <rect x="1" y="4" width="22" height="16" rx="2" />
      <line x1="1" y1="10" x2="23" y2="10" />
    </template>

    <!-- Flower -->
    <template v-else-if="name === 'flower'">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v4M12 18v4M2 12h4M18 12h4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
    </template>

    <!-- Leaf -->
    <template v-else-if="name === 'leaf'">
      <path d="M11 20A7 7 0 019.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10zM2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
    </template>

    <!-- Cloud -->
    <template v-else-if="name === 'cloud'">
      <path d="M18 10h-1.26A8 8 0 109 20h9a5 5 0 000-10z" />
    </template>

    <!-- Cloud Rain -->
    <template v-else-if="name === 'cloud-rain'">
      <path d="M16 13v8M8 13v8M12 15v8M20 16.58A5 5 0 0018 9h-1.26A8 8 0 104 16.25" />
    </template>

    <!-- Snowflake -->
    <template v-else-if="name === 'snowflake'">
      <path d="M2 12h20M12 2v20M4.93 4.93l14.14 14.14M19.07 4.93L4.93 19.07" />
      <path d="M6.34 6.34l2.83 2.83M14.83 6.34l2.83-2.83M6.34 17.66l2.83-2.83M14.83 17.66l2.83 2.83" />
    </template>

    <!-- Wind -->
    <template v-else-if="name === 'wind'">
      <path d="M9.59 4.59A2 2 0 1111 8H2m10.59 11.41A2 2 0 1014 16H2m15.73-8.27A2.5 2.5 0 1119.5 12H2" />
    </template>

    <!-- Cat -->
    <template v-else-if="name === 'cat'">
      <path d="M12 5c.67 0 1.35.09 2 .26 1.78-2 5.03-2.84 6.42-2.26 1.4.58-.42 7-.42 7 .57 1.07 1 2.24 1 3.44C21 17.9 16.97 21 12 21s-9-3.1-9-7.56c0-1.25.5-2.4 1-3.44 0 0-1.89-6.42-.5-7 1.39-.58 4.72.23 6.5 2.23A9.04 9.04 0 0112 5z" />
      <path d="M10 9a1 1 0 011-1h2a1 1 0 011 1v1a1 1 0 01-1 1h-1" />
      <path d="M14 9a1 1 0 001-1v-1a1 1 0 00-1-1h-1" />
    </template>

    <!-- Dog -->
    <template v-else-if="name === 'dog'">
      <path d="M10 5.172C10 3.782 8.423 2.679 6.5 3c-2.823.47-4.113 6.006-4 7 .08.703 1.725 1.722 3.656 1 1.261-.472 1.96-1.45 2.344-2.5M14.267 5.172c0-1.39 1.577-2.493 3.5-2.172 2.823.47 4.113 6.006 4 7-.08.703-1.725 1.722-3.656 1-1.261-.472-1.855-1.45-2.239-2.5M8 14v.5M16 14v.5M11.25 16.25h1.5L12 17l-.75-.75zM4.42 11.247A13.152 13.152 0 004 14.556C4 18.728 7.582 21 12 21s8-2.272 8-6.444c0-1.061-.162-2.2-.493-3.309m-9.243-6.082A8.801 8.801 0 0112 5c.78 0 1.53.104 2.25.308" />
    </template>

    <!-- Rabbit -->
    <template v-else-if="name === 'rabbit'">
      <path d="M15.5 2.5c1.5 1.5 2 4 1.5 6-.5 2-2.5 3-4.5 3.5-2.5.5-5-1-6-3.5-1-3 1-6 3.5-7.5 1.5-.9 3.5-1 5.5.5z" />
      <path d="M8.5 2.5c-1.5 1.5-2 4-1.5 6 .5 2 2.5 3 4.5 3.5 2.5.5 5-1 6-3.5 1-3-1-6-3.5-7.5-1.5-.9-3.5-1-5.5.5z" />
      <path d="M12 12v3M10 15h4" />
    </template>

    <!-- Skull -->
    <template v-else-if="name === 'skull'">
      <circle cx="12" cy="8" r="5" />
      <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01" />
      <path d="M10 14a2 2 0 104 0" />
      <path d="M14 14a2 2 0 104 0" />
    </template>

    <!-- Ghost -->
    <template v-else-if="name === 'ghost'">
      <path d="M9 10h.01M15 10h.01M12 2a8 8 0 00-8 8v12l3-3 2.5 2.5L12 19l2.5 2.5L17 17l3 3V10a8 8 0 00-8-8z" />
      <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01" />
    </template>

    <!-- Robot -->
    <template v-else-if="name === 'robot'">
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="3" />
      <path d="M12 8v3M8 14h8M7 17h.01M17 17h.01" />
    </template>

    <!-- Alien -->
    <template v-else-if="name === 'alien'">
      <path d="M12 2a8 8 0 00-8 8c0 5.4 3.134 9.903 7 11.2 3.866-1.297 7-6.8 7-11.2a8 8 0 00-8-8z" />
      <ellipse cx="9" cy="8" rx="1.5" ry="2" fill="currentColor" />
      <ellipse cx="15" cy="8" rx="1.5" ry="2" fill="currentColor" />
      <path d="M9 12a1 1 0 101 0 1 1 0 00-1 0zM15 12a1 1 0 101 0 1 1 0 00-1 0z" />
    </template>

    <!-- Rainbow Flag -->
    <template v-else-if="name === 'rainbow-flag'">
      <path d="M4 4h16v4H4zM4 10h16v4H4zM4 16h16v4H4z" />
      <path d="M4 4h16M4 10h16M4 16h16" stroke="none" />
    </template>

    <!-- Flag White -->
    <template v-else-if="name === 'flag-white'">
      <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
      <line x1="4" y1="22" x2="4" y2="15" />
    </template>

    <!-- Flag Black -->
    <template v-else-if="name === 'flag-black'">
      <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" />
      <line x1="4" y1="22" x2="4" y2="15" />
    </template>

    <!-- Rocket (alternative) -->
    <template v-else-if="name === 'rocket-alt'">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 00-2.91-.09z" />
      <path d="M12 19l3-3m0 0l-3-3m3 3v-3M3 13l3 3m0 0l-3-3m3 3v-3" />
    </template>

    <!-- Sakura Flower (цветок сакуры) -->
    <template v-else-if="name === 'sakura'">
      <circle cx="12" cy="12" r="3" fill="currentColor" />
      <path d="M12 2c-2 4-6 6-6 10 0 4 4 6 6 6s6-2 6-6c0-4-4-6-6-10z" />
      <path d="M12 2c2 4 6 6 6 10 0 4-4 6-6 6s-6-2-6-6c0-4 4-6 6-10z" transform="rotate(72 12 12)" />
      <path d="M12 2c2 4 6 6 6 10 0 4-4 6-6 6s-6-2-6-6c0-4 4-6 6-10z" transform="rotate(144 12 12)" />
      <path d="M12 2c2 4 6 6 6 10 0 4-4 6-6 6s-6-2-6-6c0-4 4-6 6-10z" transform="rotate(216 12 12)" />
      <path d="M12 2c2 4 6 6 6 10 0 4-4 6-6 6s-6-2-6-6c0-4 4-6 6-10z" transform="rotate(288 12 12)" />
    </template>

    <!-- Подписки (alternative) -->
    <template v-else-if="name === 'subscriptions'">
      <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="8.5" cy="7" r="4" />
      <line x1="23" y1="11" x2="17" y2="11" />
    </template>

    <!-- Загрузка / Upload -->
    <template v-else-if="name === 'upload'">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
    </template>

    <!-- Вопросительный знак -->
    <template v-else-if="name === 'question'">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01" />
    </template>

    <!-- Warning -->
    <template v-else-if="name === 'warning'">
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01" />
    </template>

    <!-- Info -->
    <template v-else-if="name === 'info'">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </template>

    <!-- Success / Check Circle -->
    <template v-else-if="name === 'check-circle'">
      <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </template>

    <!-- Error / X Circle -->
    <template v-else-if="name === 'x-circle'">
      <circle cx="12" cy="12" r="10" />
      <line x1="15" y1="9" x2="9" y2="15" />
      <line x1="9" y1="9" x2="15" y2="15" />
    </template>

    <!-- Alert Circle -->
    <template v-else-if="name === 'alert-circle'">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </template>

    <!-- Eye Off -->
    <template v-else-if="name === 'eye-off'">
      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24M1 1l22 22" />
    </template>

    <!-- Eye -->
    <template v-else-if="name === 'eye'">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </template>

    <!-- User Plus -->
    <template v-else-if="name === 'user-plus'">
      <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="8.5" cy="7" r="4" />
      <line x1="20" y1="8" x2="20" y2="14" />
      <line x1="23" y1="11" x2="17" y2="11" />
    </template>

    <!-- User Minus -->
    <template v-else-if="name === 'user-minus'">
      <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="8.5" cy="7" r="4" />
      <line x1="23" y1="11" x2="17" y2="11" />
    </template>

    <!-- User Check -->
    <template v-else-if="name === 'user-check'">
      <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="8.5" cy="7" r="4" />
      <polyline points="17 11 19 13 23 9" />
    </template>

    <!-- User X -->
    <template v-else-if="name === 'user-x'">
      <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="8.5" cy="7" r="4" />
      <line x1="18" y1="8" x2="23" y2="13" />
      <line x1="23" y1="8" x2="18" y2="13" />
    </template>

    <!-- Log Out -->
    <template v-else-if="name === 'log-out'">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
    </template>

    <!-- Log In -->
    <template v-else-if="name === 'log-in'">
      <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4M10 17l5-5-5-5M15 12H3" />
    </template>

    <!-- Bookmark -->
    <template v-else-if="name === 'bookmark'">
      <path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z" />
    </template>

    <!-- Bookmark Alt -->
    <template v-else-if="name === 'bookmark-alt'">
      <path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z" />
    </template>

    <!-- Star Half -->
    <template v-else-if="name === 'star-half'">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" fill="currentColor" />
      <path d="M12 2v15.77L5.82 21.02l1.18-6.88L2 9.27l6.82-.58L12 2z" />
    </template>

    <!-- Heart Plus -->
    <template v-else-if="name === 'heart-plus'">
      <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" />
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </template>

    <!-- Share -->
    <template v-else-if="name === 'share'">
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
      <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
    </template>

    <!-- Share 2 -->
    <template v-else-if="name === 'share-2'">
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <path d="M8.59 13.51l6.83 3.98M15.41 6.51l-6.82 3.98" />
    </template>

    <!-- More Horizontal -->
    <template v-else-if="name === 'more-horizontal'">
      <circle cx="12" cy="12" r="1" />
      <circle cx="19" cy="12" r="1" />
      <circle cx="5" cy="12" r="1" />
    </template>

    <!-- More Vertical -->
    <template v-else-if="name === 'more-vertical'">
      <circle cx="12" cy="12" r="1" />
      <circle cx="12" cy="5" r="1" />
      <circle cx="12" cy="19" r="1" />
    </template>

    <!-- Dots -->
    <template v-else-if="name === 'more-dots'">
      <circle cx="12" cy="12" r="2" />
      <circle cx="19" cy="12" r="2" />
      <circle cx="5" cy="12" r="2" />
    </template>

    <!-- Ellipsis -->
    <template v-else-if="name === 'ellipsis'">
      <circle cx="12" cy="12" r="2" />
      <circle cx="19" cy="12" r="2" />
      <circle cx="5" cy="12" r="2" />
    </template>

    <!-- List -->
    <template v-else-if="name === 'list'">
      <line x1="8" y1="6" x2="21" y2="6" />
      <line x1="8" y1="12" x2="21" y2="12" />
      <line x1="8" y1="18" x2="21" y2="18" />
      <line x1="3" y1="6" x2="3.01" y2="6" />
      <line x1="3" y1="12" x2="3.01" y2="12" />
      <line x1="3" y1="18" x2="3.01" y2="18" />
    </template>

    <!-- Align Left -->
    <template v-else-if="name === 'align-left'">
      <line x1="17" y1="10" x2="3" y2="10" />
      <line x1="21" y1="6" x2="3" y2="6" />
      <line x1="21" y1="14" x2="3" y2="14" />
      <line x1="17" y1="18" x2="3" y2="18" />
    </template>

    <!-- Align Center -->
    <template v-else-if="name === 'align-center'">
      <line x1="18" y1="10" x2="6" y2="10" />
      <line x1="21" y1="6" x2="3" y2="6" />
      <line x1="21" y1="14" x2="3" y2="14" />
      <line x1="18" y1="18" x2="6" y2="18" />
    </template>

    <!-- Align Right -->
    <template v-else-if="name === 'align-right'">
      <line x1="21" y1="10" x2="7" y2="10" />
      <line x1="21" y1="6" x2="3" y2="6" />
      <line x1="21" y1="14" x2="3" y2="14" />
      <line x1="21" y1="18" x2="7" y2="18" />
    </template>

    <!-- Bold -->
    <template v-else-if="name === 'bold'">
      <path d="M6 4h8a4 4 0 014 4 4 4 0 01-4 4H6z" />
      <path d="M6 12h9a4 4 0 014 4 4 4 0 01-4 4H6z" />
    </template>

    <!-- Italic -->
    <template v-else-if="name === 'italic'">
      <line x1="19" y1="4" x2="10" y2="4" />
      <line x1="14" y1="20" x2="5" y2="20" />
      <line x1="15" y1="4" x2="9" y2="20" />
    </template>

    <!-- Underline -->
    <template v-else-if="name === 'underline'">
      <path d="M6 3v7a6 6 0 006 6 6 6 0 006-6V3" />
      <line x1="4" y1="21" x2="20" y2="21" />
    </template>

    <!-- Strikethrough -->
    <template v-else-if="name === 'strikethrough'">
      <line x1="4" y1="12" x2="20" y2="12" />
      <path d="M17.5 7.5c-.7-1.5-2.5-3-5.5-3-3.5 0-5.5 2-5.5 4.5 0 2 1.5 3 3.5 3.5" />
      <path d="M8.5 14c.5 1 2 2 4 2 2.5 0 4-1 4-3 0-1-.5-1.5-1.5-2" />
    </template>

    <!-- Highlighter -->
    <template v-else-if="name === 'highlighter'">
      <path d="M9 11l-6 6v3h9l3-3" />
      <path d="M22 12l-4.6 4.6a2 2 0 01-2.8 0l-5.2-5.2a2 2 0 010-2.8L14 4" />
    </template>

    <!-- Type -->
    <template v-else-if="name === 'type'">
      <polyline points="4 7 4 4 20 4 20 7" />
      <line x1="9" y1="20" x2="15" y2="20" />
      <line x1="12" y1="4" x2="12" y2="20" />
    </template>

    <!-- Code -->
    <template v-else-if="name === 'code'">
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </template>

    <!-- Terminal -->
    <template v-else-if="name === 'terminal'">
      <polyline points="4 17 10 11 4 5" />
      <line x1="12" y1="19" x2="20" y2="19" />
    </template>

    <!-- Binary -->
    <template v-else-if="name === 'binary'">
      <path d="M10 20v-6h4v6h5v-8h-3l-4-4-4 4h-3v8z" />
    </template>

    <!-- Database -->
    <template v-else-if="name === 'database'">
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </template>

    <!-- Server -->
    <template v-else-if="name === 'server'">
      <rect x="2" y="2" width="20" height="8" rx="2" />
      <rect x="2" y="14" width="20" height="8" rx="2" />
      <line x1="6" y1="6" x2="6.01" y2="6" />
      <line x1="6" y1="18" x2="6.01" y2="18" />
    </template>

    <!-- Hard Drive -->
    <template v-else-if="name === 'hard-drive'">
      <line x1="22" y1="12" x2="2" y2="12" />
      <path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z" />
      <line x1="6" y1="16" x2="6.01" y2="16" />
      <line x1="10" y1="16" x2="10.01" y2="16" />
    </template>

    <!-- Wifi -->
    <template v-else-if="name === 'wifi'">
      <path d="M5 12.55a11 11 0 0114.08 0M1.42 9a16 16 0 0121.16 0M8.53 16.11a6 6 0 016.95 0M12 20h.01" />
    </template>

    <!-- Wifi Off -->
    <template v-else-if="name === 'wifi-off'">
      <line x1="1" y1="1" x2="23" y2="23" />
      <path d="M16.72 11.06A10.94 10.94 0 0119 12.55M5 12.55a10.94 10.94 0 015.17-2.39M10.71 5.05A16 16 0 0122.58 9M1.42 9a15.91 15.91 0 014.7-2.88M8.53 16.11a6 6 0 016.95 0M12 20h.01" />
    </template>

    <!-- Bluetooth -->
    <template v-else-if="name === 'bluetooth'">
      <path d="M6.5 6.5l11 11L12 23V1l5.5 5.5-11 11" />
    </template>

    <!-- RSS -->
    <template v-else-if="name === 'rss'">
      <path d="M4 11a9 9 0 019 9M4 4a16 16 0 0116 16M5 19h.01" />
    </template>

    <!-- Wifi -->
    <template v-else-if="name === 'wifi'">
      <path d="M5 12.55a11 11 0 0114.08 0M1.42 9a16 16 0 0121.16 0M8.53 16.11a6 6 0 016.95 0M12 20h.01" />
    </template>

    <!-- Wifi Off -->
    <template v-else-if="name === 'wifi-off'">
      <line x1="1" y1="1" x2="23" y2="23" />
      <path d="M16.72 11.06A10.94 10.94 0 0119 12.55M5 12.55a10.94 10.94 0 015.17-2.39M10.71 5.05A16 16 0 0122.58 9M1.42 9a15.91 15.91 0 014.7-2.88M8.53 16.11a6 6 0 016.95 0M12 20h.01" />
    </template>

    <!-- Bluetooth -->
    <template v-else-if="name === 'bluetooth'">
      <path d="M6.5 6.5l11 11L12 23V1l5.5 5.5-11 11" />
    </template>

    <!-- RSS -->
    <template v-else-if="name === 'rss'">
      <path d="M4 11a9 9 0 019 9M4 4a16 16 0 0116 16M5 19h.01" />
    </template>

    <!-- Cloud Off -->
    <template v-else-if="name === 'cloud-off'">
      <path d="M22.61 16.95A8 8 0 018 4H4a8 8 0 00-4 12.74c0 3.5 2.2 6.5 5.26 7.66" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </template>

    <!-- Cloud Lightning -->
    <template v-else-if="name === 'cloud-lightning'">
      <path d="M19 16.9A5 5 0 0018 7h-1.26a8 8 0 10-11.62 9" />
      <polyline points="13 11 9 17 15 17 11 23" />
    </template>

    <!-- Cloud Snow -->
    <template v-else-if="name === 'cloud-snow'">
      <path d="M19 16.9A5 5 0 0018 7h-1.26a8 8 0 10-11.62 9" />
      <line x1="8" y1="19" x2="8" y2="21" />
      <line x1="8" y1="13" x2="8" y2="15" />
      <line x1="16" y1="19" x2="16" y2="21" />
      <line x1="16" y1="13" x2="16" y2="15" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="12" y1="15" x2="12" y2="17" />
    </template>

    <!-- Cloud Sun -->
    <template v-else-if="name === 'cloud-sun'">
      <path d="M12 2v2M4.93 4.93l1.41 1.41M20 12h2M17.66 17.66l1.41 1.41M2 12h2M6.34 17.66l-1.41 1.41M17.07 4.93l-1.41 1.41" />
      <path d="M17.66 7.76A7 7 0 0012 4c-3.5 0-6.5 2.55-7 6a7 7 0 007 7c3.14 0 5.73-2.13 6.66-5.24z" />
    </template>

    <!-- Moon -->
    <template v-else-if="name === 'moon'">
      <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
    </template>

    <!-- Sunset -->
    <template v-else-if="name === 'sunset'">
      <path d="M17 18a5 5 0 00-10 0M12 9V2M4.22 10.22l1.42 1.42M1 18h2M21 18h2M18.36 11.64l1.42-1.42M23 22H1M16 5l-4 4-4-4" />
    </template>

    <!-- Sunrise -->
    <template v-else-if="name === 'sunrise'">
      <path d="M17 18a5 5 0 00-10 0M12 9V2M7 4l-4 4 4 4M18.36 11.64l-1.42-1.42M1 18h2M23 22h-2M16 5l4 4-4 4" />
    </template>

    <!-- Sunset Alternative -->
    <template v-else-if="name === 'sunset-alt'">
      <path d="M17 18a5 5 0 00-10 0M12 9V2M4.22 10.22l1.42 1.42M1 18h2M21 18h2M18.36 11.64l1.42-1.42M23 22H1" />
      <path d="M17 18a5 5 0 00-10 0" />
    </template>

    <!-- Star rating -->
    <template v-else-if="name === 'star-rating'">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" fill="currentColor" />
    </template>

    <!-- Star Half Alt -->
    <template v-else-if="name === 'star-half-alt'">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" fill="currentColor" />
    </template>

    <!-- Итого: Default - вопросительный знак -->
    <template v-else>
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01" />
    </template>
  </svg>
</template>

<style scoped>
.sakura-icon {
  display: inline-block;
  vertical-align: middle;
  color: var(--accent, #ff7eb3);
  transition: color 0.2s ease, transform 0.2s ease;
}

.sakura-icon[fill="currentColor"] {
  color: var(--accent, #ff7eb3);
}

.sakura-icon:hover {
  color: var(--accent-bright, #ffa8c9);
}

.sakura-icon:active {
  transform: scale(0.95);
}
</style>
