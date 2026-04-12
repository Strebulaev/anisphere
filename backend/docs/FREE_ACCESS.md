# Отключение системы подписок - Документация

## Обзор

**Дата изменения:** 2024

**Причина:** Решение сделать весь функционал сайта бесплатным для всех пользователей.

## Что изменилось

### Frontend

#### 1. `useAdBlocker.ts`
**Файл:** `frontend/src/composables/useAdBlocker.ts`

**Изменения:**
- Функция `isPremium()` теперь **всегда возвращает `true`**
- Проверка премиум статуса в `init()` закомментирована
- AdBlocker активируется для **всех пользователей**

**Код:**
```typescript
const isPremium = (): boolean => {
  // ... проверки (сохранены для истории)
  
  // ВСЕГДА ВОЗВРАЩАЕМ TRUE - весь функционал бесплатный
  return true
}
```

#### 2. `KodikPlayer.vue`
**Файл:** `frontend/src/components/Players/KodikPlayer.vue`

**Изменения:**
- Убрана загрузка `useSubscriptionStore`
- AdBlocker активируется сразу при монтировании
- Логика проверки подписки закомментирована

**Код:**
```typescript
onMounted(() => { 
  window.addEventListener('message', handlePlayerMessage)
  
  // AdBlocker активируется для всех пользователей
  console.log('[KodikPlayer] 🛡️ Activating AdBlocker (FREE FOR ALL USERS)')
  initAdBlocker()
})
```

#### 3. `SubscriptionView.vue`
**Файл:** `frontend/src/views/SubscriptionView.vue`

**Изменения:**
- Полностью переписан шаблон
- Убраны карточки с ценами
- Убрана форма промокода
- Убрана логика оплаты
- Добавлено уведомление о бесплатном доступе

**Новый вид:**
```
┌─────────────────────────────────────┐
│  👑 Премиум функции                 │
│  🎉 Все функции теперь бесплатны!   │
├─────────────────────────────────────┤
│  ✅ Все премиум функции доступны    │
│     бесплатно                       │
│                                     │
│  AdBlocker, скачивание опенингов/   │
│  эндингов, корона в профиле и       │
│  другие функции теперь доступны     │
│  всем без ограничений.              │
└─────────────────────────────────────┘
```

### Backend

#### 1. `views_subscription.py`
**Файл:** `backend/users/views_subscription.py`

**Изменения:**
- `SubscriptionView.get()` всегда возвращает `is_premium=True`
- `days_left` всегда возвращает `999` ("бесконечно")
- Все классы закомментированы:
  - `SubscriptionActivateView`
  - `SubscriptionDeactivateView`
  - `PromoCodeValidateView`
  - `PromoCodeApplyView`
  - `SubscriptionPriceView`

**Код:**
```python
def get(self, request):
    is_premium = True  # Было: sub.is_premium
    days_left = 999
    
    return Response({
        'is_active': is_premium,
        'is_premium': is_premium,
        'days_left': days_left,
        'note': 'Весь функционал бесплатный!',
    })
```

#### 2. Модели (`models.py`)
**Файл:** `backend/users/models.py`

**Изменения:**
- Модели **НЕ ИЗМЕНЕНЫ** (сохранены для истории)
- `Subscription` модель остаётся
- `PromoCode` модель остаётся
- `PromoCodeUsage` модель остаётся

### Payment System

#### CryptoCloud Integration
**Файлы:**
- `backend/core/cryptocloud.py` (сохранён)
- `backend/users/views_payment.py` (закомментирован)

**Статус:** Код оплаты сохранён но не используется

## Функции которые стали бесплатными

### 1. AdBlocker в плеере
- ✅ Блокировка рекламы в Kodik
- ✅ 8 методов блокировки
- ✅ Доступно всем пользователям

### 2. Скачивание опенингов/эндингов
- ✅ Скачать OP/ED в MP3
- ✅ Скачать OP/ED в видео
- ✅ Без ограничений

### 3. Профиль пользователя
- ✅ Корона в профиле
- ✅ Шапка профиля
- ✅ Соцсети в профиле
- ✅ Эксклюзивные значки

### 4. Другие функции
- ✅ Моя коллекция
- ✅ Плейлисты
- ✅ Reactor (Shorts)
- ✅ Чат
- ✅ Конкурсы

## Сохранённый код (для истории)

### Frontend
- `frontend/src/stores/subscription.ts` - Pinia store
- `frontend/src/composables/useAdBlocker.ts` - проверки премиум
- `frontend/src/api/settings.ts` - API функции подписки

### Backend
- `backend/users/models.py` - модели Subscription, PromoCode
- `backend/users/views_subscription.py` - все views закомментированы
- `backend/users/views_payment.py` - оплата через CryptoCloud
- `backend/core/cryptocloud.py` - сервис CryptoCloud

## API Endpoints

### Активные (возвращают бесплатный статус)
```
GET  /api/users/subscription/
     → {'is_premium': True, 'days_left': 999}
```

### Неактивные (закомментированы в URLConf)
```
POST /api/users/subscription/activate/    # Закомментировано
POST /api/users/subscription/deactivate/  # Закомментировано
GET  /api/users/subscription/promo/validate/  # Закомментировано
POST /api/users/subscription/promo/apply/    # Закомментировано
GET  /api/users/subscription/price/      # Закомментировано
POST /api/users/payment/create/          # Закомментировано
POST /api/users/payment/check/           # Закомментировано
POST /api/payment/webhook/               # Закомментировано
```

## Как вернуть подписку (если понадобится)

### 1. Frontend
Раскомментировать в `useAdBlocker.ts`:
```typescript
const isPremium = (): boolean => {
  // Вернуть оригинальную логику
  if (authStore.user?.is_premium === true) return true
  // ...
  return false
}
```

Раскомментировать в `KodikPlayer.vue`:
```typescript
const subscriptionStore = useSubscriptionStore()
subscriptionStore.fetchSubscription().then(() => {
  updateAdBlockerStatus()
})
```

### 2. Backend
Раскомментировать классы в `views_subscription.py`:
```python
class SubscriptionActivateView(APIView):
    # ... раскомментировать код
```

Добавить URL в `urls.py`:
```python
path('subscription/activate/', SubscriptionActivateView.as_view()),
```

### 3. Payment
Раскомментировать CryptoCloud views в `urls.py`:
```python
path('payment/create/', CreatePaymentView.as_view()),
path('payment/webhook/', PaymentWebhookView.as_view()),
```

## Тестирование

### Проверка что AdBlocker работает для всех:
1. Открыть любое аниме
2. Открыть консоль браузера
3. Должно быть: `[AdBlock] 🛡️ === ACTIVATING AD BLOCKER (FREE FOR ALL) ===`
4. Реклама должна быть заблокирована

### Проверка API:
```bash
curl https://anisphere.ru/api/users/subscription/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Ответ:
```json
{
  "is_active": true,
  "is_premium": true,
  "days_left": 999,
  "note": "Весь функционал бесплатный!"
}
```

## Миграции базы данных

**Не требуются** - модели не изменены, данные сохранены.

## Влияние на пользователей

### До изменения:
- ❌ Реклама для бесплатных
- ❌ Платные функции
- ❌ Промокоды

### После изменения:
- ✅ AdBlocker для всех
- ✅ Все функции бесплатны
- ✅ Нет ограничений

## Будущее использование

Код подписки может быть использован для:
1. **VIP уровней** - дополнительные функции за плату
2. **Донаты** - поддержка проекта
3. **Ранний доступ** - новые функции сначала для платных
4. **Косметика** - платные темы, значки, аватарки

## Примечания

- Весь код подписки **сохранён** и может быть активирован
- Модели базы данных **не изменены**
- Миграции **не требуются**
- Данные о старых подписках **сохранены**

## Контакты

По вопросам восстановления системы подписок:
- Email: contact@anisphere.app
- Telegram: @anisphere_support
