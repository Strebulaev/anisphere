<template>
  <!-- 
    ============================================================================
    КОММЕНТАРИЙ: ПОДПИСКА ОТКЛЮЧЕНА - ВЕСЬ ФУНКЦИОНАЛ БЕСПЛАТНЫЙ
    ============================================================================
    Эта страница сохранена для возможного будущего использования.
    Сейчас все функции доступны бесплатно.
    ============================================================================
  -->
  <div class="subscription-page">
    <div class="page-header">
      <h1><SakuraIcon name="crown" /> Премиум подписка</h1>
    </div>

    <div class="content">
      <!-- Форма активации по промокоду -->
      <div class="promo-form">
        <div class="form-header">
          <h2>Активация премиума</h2>
          <p>Введите промокод для получения подписки</p>
        </div>
        <div class="form-group">
          <label for="promo-code">Промокод</label>
          <input
            id="promo-code"
            v-model="promoCode"
            type="text"
            placeholder="ANI100"
            :disabled="activating"
            class="promo-input"
            @keyup.enter="activatePromo"
          />
        </div>
        <button
          @click="activatePromo"
          :disabled="!promoCode.trim() || activating"
          class="activate-btn"
        >
          <SakuraIcon v-if="activating" name="hourglass" :size="16" />
          {{ activating ? 'Активация...' : 'Активировать премиум' }}
        </button>
        <div v-if="promoError" class="message error-text">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {{ promoError }}
        </div>
        <div v-if="promoSuccess" class="message success-text">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {{ promoSuccess }}
        </div>
        <div v-if="promoRemaining !== null" class="promo-info">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
          Осталось использований промокода: {{ promoRemaining }}
        </div>
      </div>

      <!-- Информация о подписке -->
      <div v-if="subscription" class="subscription-info">
        <div class="info-header">
          <PremiumCrown :size="24" />
          <span>Статус подписки</span>
        </div>
        <div class="subscription-status" :class="{ active: subscription.is_premium, inactive: !subscription.is_premium }">
          <span>{{ subscription.is_premium ? '✅ Премиум активен' : '❌ Премиум не активен' }}</span>
        </div>
        <div v-if="subscription.days_left" class="days-left">
          Осталось дней: {{ subscription.days_left }}
        </div>
        <div class="features-list">
          <h3>Что входит в премиум:</h3>
          <ul>
            <li>Скачивание опенингов</li>
            <li>Скачивание эндингов</li>
            <li>Скачивание фрагментов аниме</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Карточки (закомментированы - не используются) -->
    <!--
    <div class="plans-grid">
      <div class="plan-card free">
        <div class="plan-header">
          <h2>Бесплатный</h2>
          <div class="plan-price">0 ₽</div>
        </div>
        <ul class="plan-features">
          <li><SakuraIcon name="check" /> Базовые функции</li>
          <li><SakuraIcon name="check" /> Просмотр аниме</li>
        </ul>
      </div>

      <div class="plan-card premium">
        <div class="plan-header">
          <h2>Премиум</h2>
          <div class="plan-price">
            <span class="price-amount">0 ₽</span>
            <span class="price-period">/месяц</span>
          </div>
        </div>
        <ul class="plan-features">
          <li><SakuraIcon name="check" /> Все функции бесплатны</li>
          <li><SakuraIcon name="check" /> AdBlocker</li>
          <li><SakuraIcon name="check" /> Скачивание тем</li>
          <li><SakuraIcon name="check" /> Корона в профиле</li>
        </ul>
      </div>
    </div>
    -->
  </div>
</template>

<script setup lang="ts">
/**
 * ============================================================================
 * КОММЕНТАРИЙ: ЛОГИКА ПОДПИСКИ ОТКЛЮЧЕНА
 * ============================================================================
 * Код сохранён для возможного будущего использования.
 * Сейчас все функции доступны бесплатно.
 * ============================================================================
 */

import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '@/composables/useToast'
import apiClient from '@/api/client'
import PremiumCrown from '@/components/icons/PremiumCrown.vue'

const route = useRoute()
const toast = useToast()

const subscription = ref<any>(null)
const loading = ref(false)
const promoCode = ref('')
const promoError = ref('')
const promoSuccess = ref('')
const activating = ref(false)
const promoRemaining = ref<number | null>(null)
// const finalPrice = computed(() => priceInfo.value?.final_price || 399)

const loadSubscription = async () => {
  try {
    loading.value = true
    const response = await apiClient.get('/users/subscription/')
    subscription.value = response.data
  } catch (error) {
    console.error('Error loading subscription:', error)
  } finally {
    loading.value = false
  }
}

const loadPromoInfo = async () => {
  try {
    const response = await apiClient.get('/users/subscription/promo/validate/?code=ANI100')
    if (response.data.valid) {
      promoRemaining.value = response.data.remaining_uses
    }
  } catch {
    promoRemaining.value = null
  }
}

const activatePromo = async () => {
  if (!promoCode.value.trim()) return

  try {
    activating.value = true
    promoError.value = ''
    promoSuccess.value = ''

    const response = await apiClient.post('/users/subscription/activate/', {
      promo_code: promoCode.value.trim().toUpperCase()
    })

    promoSuccess.value = response.data.message || 'Подписка активирована! Теперь доступно скачивание опенингов/эндингов/фрагментов.'
    promoCode.value = ''
    await loadSubscription()
    await loadPromoInfo()
  } catch (error: any) {
    promoError.value = error.response?.data?.error || 'Ошибка активации'
  } finally {
    activating.value = false
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })
}

onMounted(async () => {
  await loadSubscription()
  await loadPromoInfo()
})
</script>

<style scoped>
.subscription-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.subtitle {
  color: var(--text-secondary);
  font-size: 18px;
  margin: 0;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.promo-form {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.form-header {
  text-align: center;
  margin-bottom: 24px;
}

.form-header h2 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.form-header p {
  color: var(--text-secondary);
  margin: 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-primary);
  font-weight: 500;
  font-size: 16px;
}

.promo-input {
  width: 100%;
  padding: 16px;
  border: 2px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--surface-1);
  color: var(--text-primary);
  font-size: 16px;
  transition: border-color var(--duration-base);
}

.promo-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb, 59, 130, 246), 0.1);
}

.activate-btn {
  width: 100%;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  padding: 16px;
  border-radius: var(--radius-lg);
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  transition: all var(--duration-base);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.activate-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--accent-rgb, 59, 130, 246), 0.3);
}

.activate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.message {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-text {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: var(--danger, #ef4444);
}

.success-text {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: var(--success, #10b981);
}

.promo-info {
  background: var(--surface-3);
  padding: 16px;
  border-radius: var(--radius-md);
  margin-top: 16px;
  color: var(--text-secondary);
  font-size: 14px;
  text-align: center;
}

.subscription-info {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.info-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.subscription-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 18px;
}

.subscription-status.active {
  color: var(--success, #10b981);
}

.subscription-status.inactive {
  color: var(--text-secondary);
}

.days-left {
  color: var(--text-secondary);
  margin-top: 8px;
  font-size: 14px;
}

.features-list {
  margin-top: 16px;
}

.features-list h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.features-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  color: var(--text-secondary);
}

.features-list li::before {
  content: '✓';
  color: var(--success, #10b981);
  font-weight: bold;
}

/* Responsive */
@media (max-width: 768px) {
  .subscription-page {
    padding: 16px;
  }

  .page-header h1 {
    font-size: 28px;
    flex-direction: column;
    gap: 8px;
  }

  .subtitle {
    font-size: 16px;
  }

  .promo-form {
    padding: 24px;
  }

  .subscription-info {
    padding: 24px;
  }

  .activate-btn {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 24px;
  }

  .promo-form,
  .subscription-info {
    padding: 20px;
  }

  .promo-input {
    padding: 14px;
    font-size: 16px; /* Prevent zoom on iOS */
  }

  .activate-btn {
    padding: 14px;
  }
}
</style>

.free-access-notice {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 165, 0, 0.1));
  border: 2px solid #FFD700;
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
  text-align: center;
}

.free-access-notice .subscription-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 700;
  color: #FFD700;
  margin-bottom: 16px;
}

.free-access-notice .subscription-status.active {
  color: #FFD700;
}

.notice-text {
  color: var(--text-color, #333);
  font-size: 16px;
  line-height: 1.6;
  margin: 0;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 28px;
  margin-bottom: 8px;
}

.subtitle {
  color: var(--text-secondary, #666);
  font-size: 16px;
}

.current-subscription {
  background: var(--card-bg, #f5f5f5);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.subscription-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.subscription-status.active {
  color: #FFD700;
}

.subscription-expires {
  color: var(--text-secondary, #666);
  font-size: 14px;
}

.plans-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.plan-card {
  background: var(--card-bg, #fff);
  border: 2px solid var(--border-color, #eee);
  border-radius: 16px;
  padding: 24px;
  position: relative;
}

.plan-card.premium {
  border-color: #FFD700;
  box-shadow: 0 4px 20px rgba(255, 215, 0, 0.2);
}

.plan-card.current {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 165, 0, 0.1));
}

.plan-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: #FFD700;
  color: #000;
  padding: 4px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.plan-header {
  text-align: center;
  margin-bottom: 20px;
}

.plan-header h2 {
  font-size: 20px;
  margin-bottom: 8px;
}

.plan-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
}

.price-amount {
  font-size: 36px;
  font-weight: 700;
  color: #FFD700;
}

.price-period {
  color: var(--text-secondary, #666);
}

.discount-badge {
  display: inline-block;
  background: #4CAF50;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  margin-top: 8px;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 24px 0;
}

.plan-features li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color, #eee);
}

.plan-features li:last-child {
  border-bottom: none;
}

.plan-features li :deep(.disabled) {
  color: var(--text-secondary, #999);
}

.plan-actions {
  display: flex;
  justify-content: center;
}

.btn-plan {
  width: 100%;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-plan.btn-primary {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: #000;
}

.btn-plan.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 215, 0, 0.4);
}

.btn-plan.btn-secondary {
  background: var(--border-color, #eee);
  color: var(--text-color, #333);
}

.btn-plan:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.promo-section {
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #eee);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.promo-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.promo-form {
  display: flex;
  gap: 12px;
}

.promo-input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid var(--border-color, #eee);
  border-radius: 8px;
  font-size: 16px;
}

.promo-input:focus {
  outline: none;
  border-color: #FFD700;
}

.btn-promo {
  padding: 12px 24px;
  background: #FFD700;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.btn-promo:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.promo-error {
  color: #f44336;
  margin-top: 12px;
}

.promo-success {
  color: #4CAF50;
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.payment-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--info-bg, #e3f2fd);
  border-radius: 8px;
  color: var(--text-secondary, #666);
}

.payment-info p {
  margin: 0;
  font-size: 14px;
}

@media (max-width: 600px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }
}
<\style>
