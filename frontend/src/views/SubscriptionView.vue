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
      <h1><SakuraIcon name="crown" /> Премиум функции</h1>
      <p class="subtitle">🎉 Все функции теперь бесплатны!</p>
    </div>

    <!-- Информация о бесплатном доступе -->
    <div class="free-access-notice">
      <div class="subscription-status active">
        <PremiumCrown :size="24" />
        <span>✅ Все премиум функции доступны бесплатно</span>
      </div>
      <p class="notice-text">
        AdBlocker, скачивание опенингов/эндингов, корона в профиле и другие 
        эксклюзивные функции теперь доступны всем пользователям без ограничений.
      </p>
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
// import { 
//   getSubscription, 
//   deactivateSubscription as deactivateApi,
//   validatePromoCode,
//   getSubscriptionPrice,
//   createPayment,
//   type SubscriptionInfo,
//   type SubscriptionPrice
// } from '@/api/settings'
import PremiumCrown from '@/components/icons/PremiumCrown.vue'

const route = useRoute()
const toast = useToast()

// Закомментированные переменные (сохранены для будущего)
// const subscription = ref<SubscriptionInfo | null>(null)
// const priceInfo = ref<SubscriptionPrice | null>(null)
// const loading = ref(false)
// const processingPayment = ref(false)
// const promoCode = ref('')
// const promoError = ref('')
// const promoValid = ref(false)
// const promoDiscount = ref(0)

// const basePrice = computed(() => priceInfo.value?.base_price || 399)
// const discount = computed(() => priceInfo.value?.discount || 0)
// const finalPrice = computed(() => priceInfo.value?.final_price || 399)

// const loadSubscription = async () => { ... }
// const loadPrice = async () => { ... }
// const validatePromo = async () => { ... }
// const handlePayment = async () => { ... }
// const deactivateSubscription = async () => { ... }

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ru-RU', { 
    day: 'numeric', 
    month: 'long', 
    year: 'numeric' 
  })
}

onMounted(async () => {
  // Логика загрузки подписки отключена - всё бесплатно
  console.log('[SubscriptionView] Premium features are now FREE for all users!')
  
  // const success = route.query.success
  // const failed = route.query.failed
  // if (success === '1') { ... }
  
  // await loadSubscription()
  // await loadPrice()
})
</script>

<style scoped>
.subscription-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

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
</style>
