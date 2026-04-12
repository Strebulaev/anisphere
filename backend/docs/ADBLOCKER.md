# AdBlocker для Anisphere - Документация

## Обзор

AdBlocker — это система блокировки рекламы в плеере Kodik для премиум-пользователей Anisphere.

## Возможности

### Методы блокировки рекламы:

1. **CSS Injection** — внедрение стилей для скрытия рекламных элементов
2. **DOM Observer** — наблюдение за DOM и удаление рекламных элементов
3. **Fetch Interception** — блокировка рекламных network запросов
4. **XHR Interception** — блокировка XMLHttpRequest
5. **postMessage Blocking** — перехват рекламных сообщений от iframe
6. **Player Methods Patching** — переопределение методов показа рекламы
7. **Video Ad Skipping** — автоматический пропуск рекламных видео
8. **Iframe Injection** — попытка инъекции в iframe плеера

## Архитектура

### Frontend Компоненты:

#### 1. `useAdBlocker.ts` (Composable)
Основной модуль блокировки рекламы.

**Местоположение:** `frontend/src/composables/useAdBlocker.ts`

**Функции:**
- `init()` — активация блокировщика
- `deactivate()` — деактивация
- `isPremium()` — проверка премиум статуса
- `isAdUrl(url)` — проверка URL на рекламный
- `isAdMessage(data)` — проверка сообщения на рекламное

**Пример использования:**
```typescript
import { useAdBlocker } from '@/composables/useAdBlocker'

const { init, deactivate, isPremium } = useAdBlocker()

// Активировать если премиум
if (isPremium()) {
  init()
}
```

#### 2. `KodikPlayer.vue` (Компонент плеера)
Интегрирует AdBlocker в плеер.

**Местоположение:** `frontend/src/components/Players/KodikPlayer.vue`

**Логика работы:**
1. При монтировании загружает информацию о подписке
2. Проверяет премиум статус
3. Активирует/деактивирует AdBlocker
4. При размонтировании деактивирует AdBlocker

#### 3. `useSubscriptionStore.ts` (Pinia Store)
Управление подпиской и премиум статусом.

**Местоположение:** `frontend/src/stores/subscription.ts`

**State:**
- `subscription` — информация о подписке
- `loading` — статус загрузки
- `error` — ошибка

**Getters:**
- `isActive` — активна ли подписка
- `isPremium` — премиум ли пользователь
- `daysLeft` — дней до окончания
- `expiresAt` — дата окончания

**Actions:**
- `fetchSubscription()` — загрузка данных
- `activateWithPromo(code)` — активация промокодом
- `deactivateSubscription()` — деактивация
- `checkPremiumSync()` — быстрая проверка (без API)
- `refreshPremiumStatus()` — обновление статуса

### Backend API

#### 1. Subscription API

**Endpoint:** `GET /api/users/subscription/`

**Ответ:**
```json
{
  "is_active": true,
  "is_premium": true,
  "started_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-02-01T00:00:00Z",
  "auto_renew": true,
  "payment_method": "cryptocloud",
  "days_left": 30
}
```

**Местоположение:** `backend/users/views_subscription.py`

#### 2. Payment API (CryptoCloud)

**Создание платежа:**
- `POST /api/users/payment/create/`

**Проверка статуса:**
- `POST /api/users/payment/check/`

**Webhook:**
- `POST /api/payment/webhook/`

**Местоположение:** `backend/users/views_payment.py`

#### 3. CryptoCloud Service

**Местоположение:** `backend/core/cryptocloud.py`

**Методы:**
- `create_invoice(amount, order_id, description)` — создание счёта
- `check_payment(invoice_uuid)` — проверка статуса
- `verify_webhook_token(token)` — проверка JWT токена

## Настройка

### 1. Backend (.env)

```bash
# CryptoCloud Payment
CRYPTOCLOUD_API_KEY=your_api_key
CRYPTOCLOUD_SHOP_ID=your_shop_id
CRYPTOCLOUD_SECRET_KEY=your_secret_key
```

### 2. Frontend

Ничего дополнительно настраивать не нужно. AdBlocker автоматически:
- Проверяет премиум статус при загрузке плеера
- Активируется для премиум пользователей
- Деактивируется для обычных пользователей

## Как это работает

### Для премиум пользователей:

1. **При загрузке страницы с аниме:**
   - `KodikPlayer.vue` монтируется
   - `useSubscriptionStore.fetchSubscription()` загружает данные
   - Проверяется `isPremium`
   - Вызывается `useAdBlocker.init()`

2. **AdBlocker выполняет:**
   - Внедряет CSS стили для скрытия рекламы
   - Запускает наблюдатель за DOM
   - Перехватывает fetch/XHR запросы
   - Блокирует рекламные postMessage
   - Переопределяет методы плеера
   - Пропускает рекламные видео

3. **Во время просмотра:**
   - Все рекламные элементы скрываются
   - Рекламные запросы блокируются
   - События о рекламе не обрабатываются

### Для обычных пользователей:

- AdBlocker не активируется
- Реклама показывается в обычном режиме

## Паттерны блокировки

### Рекламные домены (AD_PATTERNS):
- doubleclick, googleadservices, moatads
- adfox, yandex.ru/ads, mytarget.ru
- /ad/, /ads/, /banner/, /sponsor/
- kodik_advert, kodik_ad, kodik_banner

### CSS Селекторы (AD_ELEMENT_SELECTORS):
- `.advert`, `.ad-banner`, `.ad-container`
- `.kodik-ad`, `.player-ad`, `.video-ad`
- `[class*="ad-"]`, `[id*="ad-"]`

### Сообщения (AD_MESSAGE_KEYS):
- `kodik_player_advert_started`
- `kodik_player_advert_ended`
- `ad_start`, `ad_end`, `banner_show`

## Отладка

### Включение логов:

AdBlocker выводит логи в консоль:
```
[AdBlock] 🛡️ === ACTIVATING AD BLOCKER FOR PREMIUM USER ===
[AdBlock] ✅ CSS injection complete
[AdBlock] ✅ DOM observer started
[AdBlock] 🚫 Blocked fetch request: https://...
[AdBlock] 🚫 Hidden 3 ad element(s)
```

### Проверка статуса:

В консоли браузера:
```javascript
// Проверка активности AdBlocker
window.KODIK_AD_BLOCKER_ACTIVE  // true/false

// Проверка премиум статуса
const { useSubscriptionStore } = await import('@/stores/subscription')
const store = useSubscriptionStore()
store.isPremium  // true/false
```

## Тестирование

### 1. Активировать премиум:

```bash
# Backend shell
python manage.py shell

# В shell
from users.models import User, Subscription
from datetime import timedelta
from django.utils import timezone

user = User.objects.get(username='testuser')
sub, _ = Subscription.objects.get_or_create(user=user)
sub.activate(days=30, payment_method='test')

# Обновить профиль
profile = user.profile_settings
profile.is_premium = True
profile.save()
```

### 2. Проверить в браузере:

1. Войти под тестовым пользователем
2. Открыть любое аниме
3. Открыть консоль разработчика
4. Убедиться что видно `[AdBlock] 🛡️ === ACTIVATING AD BLOCKER`
5. Реклама должна быть заблокирована

## Ограничения

### CORS:
- Инъекция в iframe работает только если iframe на том же домене
- Kodik iframe обычно на другом домене, поэтому injection ограничен

### Обход блокировки:
- Kodik может обновить методы показа рекламы
- Некоторые виды рекламы могут обходить блокировку
- Рекомендуется регулярно обновлять паттерны

### Производительность:
- DOM Observer может влиять на производительность
- Мутации отслеживаются только в `document.body`
- Интервал проверки: 2 секунды для видео

## Обновление паттернов

Для добавления новых рекламных паттернов:

```typescript
// frontend/src/composables/useAdBlocker.ts

// Добавить домен
const AD_PATTERNS = [
  // ... существующие
  'new-ad-domain.com',
]

// Добавить CSS селектор
const AD_ELEMENT_SELECTORS = [
  // ... существующие
  '.new-ad-class',
]

// Добавить сообщение
const AD_MESSAGE_KEYS = [
  // ... существующие
  'new_ad_event',
]
```

## Альтернативные платёжные системы

### CryptoCloud (текущий)
- ✅ Принимает рубли (конвертирует в крипту)
- ✅ Не проверяет контент
- ✅ Автоматический webhook
- ❌ Минимальная сумма ~2000₽

### Bitbanker
- ✅ Выставление счёта в рублях
- ✅ Оплата криптовалютой
- ❌ Минимальная сумма 2000₽

### Ручной перевод (рекомендуется для малых сумм)
- ✅ Нет минимальной суммы
- ✅ Полный контроль
- ❌ Ручная активация подписки

## Будущие улучшения

1. **White-list доменов** — разрешить только необходимые запросы
2. **Machine Learning** — автоматическое определение рекламы
3. **Shadow DOM** — блокировка на более низком уровне
4. **Service Worker** — перехват на уровне network
5. **WebAssembly модуль** — для лучшей производительности

## Поддержка

При проблемах с блокировкой рекламы:

1. Проверьте логи в консоли
2. Убедитесь что премиум активен
3. Проверьте что AdBlocker инициализирован
4. Обновите паттерны если реклама новая
5. Создайте issue с примером рекламы

## Лицензия

Внутренняя разработка Anisphere. Не для коммерческого использования.
