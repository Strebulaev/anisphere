/**
 * Sakura Icons - Документация по использованию
 * 
 * Этот компонент предоставляет 200+ SVG иконок в стиле аниме-тематики с розовой цветовой схемой сакуры.
 * 
 * ## Установка
 * 
 * Компонент уже зарегистрирован глобально. Просто используйте:
 * 
 * ```vue
 * <SakuraIcon name="heart" size="24" />
 * ```
 * 
 * ## Использование в шаблоне
 * 
 * ### Базовое использование
 * ```vue
 * <template>
 *   <SakuraIcon name="heart" />
 *   <SakuraIcon name="star" :size="32" />
 *   <SakuraIcon name="fire" size="20" class="custom-icon" />
 * </template>
 * ```
 * 
 * ### Доступные иконки
 * 
 * #### Навигация и UI
 * - `home` - Домой
 * - `user` - Пользователь
 * - `users` - Пользователи/Группа
 * - `settings` - Настройки
 * - `menu` - Меню
 * - `search` - Поиск
 * - `filter` - Фильтр
 * - `sort` - Сортировка
 * 
 * #### Действия
 * - `plus` - Плюс/Добавить
 * - `x` - Закрыть/Удалить
 * - `edit` - Редактировать
 * - `trash` - Удалить
 * - `copy` - Копировать
 * - `save` - Сохранить
 * - `export` - Экспорт
 * - `import` - Импорт
 * - `download` - Скачать
 * - `upload` - Загрузить
 * - `share` - Поделиться
 * - `link` - Ссылка
 * 
 * #### Статус и эмоции
 * - `heart` - Сердце/Лайк
 * - `star` - Звезда/Рейтинг
 * - `fire` - Огонь/Популярно
 * - `bell` - Уведомления
 * - `check` - Успешно
 * - `x-circle` - Ошибка
 * - `alert-circle` - Предупреждение
 * - `question` - Вопрос
 * 
 * #### Медиа
 * - `play` - Плей/Видео
 * - `video` - Видео
 * - `film` - Фильм
 * - `image` - Картинка
 * - `camera` - Камера
 * - `music` - Музыка
 * - `headphones` - Наушники
 * - `mic` - Микрофон
 * 
 * #### Время
 * - `calendar` - Календарь
 * - `clock` - Часы
 * - `timer` - Таймер
 * - `hourglass` - Песочные часы
 * 
 * #### Файлы
 * - `folder` - Папка
 * - `file-text` - Файл
 * - `book` - Книга
 * - `package` - Пакет
 * - `clipboard` - Буфер обмена
 * 
 * #### Устройства
 * - `phone` - Телефон
 * - `laptop` - Ноутбук
 * - `globe` - Глобус/Интернет
 * 
 * #### Безопасность
 * - `lock` - Замок
 * - `unlock` - Открытый замок
 * - `key` - Ключ
 * - `shield` - Щит
 * - `eye` - Глаз (показать)
 * - `eye-off` - Глаз (скрыть)
 * 
 * #### Социальные сети
 * - `message` - Чат
 * - `mail` - Почта
 * - `send` - Отправить (Telegram)
 * - `vk` - VK
 * - `message-circle` - WhatsApp
 * 
 * #### Разное
 * - `wheel` - Колесо фортуны
 * - `target` - Мишень
 * - `dice` - Кубики
 * - `sparkle` - Блеск
 * - `sparkles` - Блестки
 * - `palette` - Палитра
 * - `sun` - Солнце
 * - `moon` - Луна
 * - `rocket` - Ракета
 * - `trophy` - Кубок
 * - `crown` - Корона
 * - `gift` - Подарок
 * - `dollar` - Деньги
 * - `trending-up` - Тренд вверх
 * - `trending-down` - Тренд вниз
 * - `thumbs-up` - Лайк (палец вверх)
 * - `thumbs-down` - Дизлайк (палец вниз)
 * - `building` - Здание
 * - `map-pin` - Метка на карте
 * - `map` - Карта
 * - `cloud` - Облако
 * - `cloud-rain` - Дождь
 * - `snowflake` - Снежинка
 * - `wind` - Ветер
 * - `sakura` - Цветок сакуры (специальная иконка!)
 * 
 * ## Использование EmojiReplacer
 * 
 * Компонент для замены эмодзи в тексте:
 * 
 * ```vue
 * <template>
 *   <EmojiReplacer text="Привет! 🎉 Ура! 🔥" />
 *   <EmojiReplacer text="Статья про аниме ⭐" :inline="false" />
 * </template>
 * ```
 * 
 * ## Использование директивы v-sakura-emoji
 * 
 * Директива для автоматической замены эмодзи в любом элементе:
 * 
 * ```vue
 * <template>
 *   <span v-sakura-emoji="messageText"></span>
 *   <div v-sakura-emoji:inline="false">Текст с эмодзи</div>
 *   <p v-sakura-emoji:size="24">Большие иконки</p>
 * </template>
 * ```
 * 
 * ## Использование composable
 * 
 * ```vue
 * <script setup lang="ts">
 * import { ref } from 'vue'
 * import { useEmojiReplacer } from '@/composables/useEmojiReplacer'
 * 
 * const text = ref('Поздравляю! 🎊')
 * const { parts, hasEmoji } = useEmojiReplacer(text)
 * </script>
 * 
 * <template>
 *   <span v-for="part in parts" :key="part.key">
 *     <SakuraIcon v-if="part.type === 'emoji'" :name="part.iconName" />
 *     <span v-else>{{ part.content }}</span>
 *   </span>
 * </template>
 * ```
 * 
 * ## Кастомизация цветов
 * 
 * Цвета иконок настраиваются через CSS переменные:
 * 
 * ```css
 * .my-icon-container {
 *   --accent: #ff7eb3;      /* Основной цвет (розовый сакуры) */
 *   --accent-bright: #ffa8c9;  /* Яркий цвет при наведении */
 * }
 * ```
 * 
 * ## Добавление новых иконок
 * 
 * Добавьте новую иконку в компонент SakuraIcon.vue:
 * 
 * ```vue
 * <!-- Новая иконка -->
 * <template v-else-if="name === 'my-icon'">
 *   <path d="..." />
 * </template>
 * ```
 * 
 * Затем добавьте маппинг в emojiToIcon.ts:
 * 
 * ```ts
 * '🔤': 'my-icon',
 * ```
 */

export {}
