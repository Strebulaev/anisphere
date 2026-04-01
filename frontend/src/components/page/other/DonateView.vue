

<script setup lang="ts">
import { ref } from 'vue'

const copied = ref<string | null>(null)

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = text
    setTimeout(() => {
      copied.value = null
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

const copyCryptoAddress = (address: string) => {
  copyToClipboard(address)
}
</script>

<template>
  <div class="donate-page">
    <header class="page-header">
      <h1>💝 Поддержать проект</h1>
      <p class="subtitle">Помогите нам развиваться и радовать вас новым контентом!</p>
    </header>

    <div class="donate-content">
      <!-- Причина доната -->
      <section class="donate-reason">
        <h2>Почему это важно?</h2>
        <p>
          Animesphere — это бесплатная платформа для любителей аниме. 
          Мы не показываем рекламу и не требуем подписки. 
          Однако для поддержания серверов, покупки доменов, хранения баз данных и развития проекта нужны средства.
        </p>
        <p>
          Каждый ваш донат помогает нам:
        </p>
        <ul class="reason-list">
          <li>🚀 Оплачивать серверы и хостинг</li>
          <li>💾 Обеспечивать резервное копирование данных</li>
          <li>✨ Добавлять новые функции</li>
          <li>🐛 Улучшать производительность</li>
        </ul>
      </section>

      <!-- Способы доната -->
      <section class="donate-methods">
        <h2>Способы доната</h2>
        
        <div class="methods-grid">
          <!-- Donation Alerts -->
          <div class="donate-card main">
            <div class="card-icon">🎁</div>
            <h3>Donation Alerts</h3>
            <p>Официальная платформа для приёма донатов с поддержкой автоматических пожертвований и отображения ваших имён в донатерском списке.</p>
            <a 
              href="https://www.donationalerts.com/r/anisphere" 
              target="_blank" 
              rel="noopener noreferrer"
              class="donate-btn primary"
            >
              Перейти на Donation Alerts
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
            </a>
            <div class="donation-link">
              <span class="link-label">Ссылка для доната:</span>
              <code class="link-value">https://www.donationalerts.com/r/anisphere</code>
            </div>
          </div>

          <!-- Qiwi -->
          <!-- <div class="donate-card">
            <div class="card-icon">💚</div>
            <h3>Qiwi Кошелёк</h3>
            <p>Быстрый и удобный способ перевести деньги через Qiwi или любой банк.</p>
            <div class="wallet-info">
              <span class="wallet-label">Номер кошелька:</span>
              <div class="wallet-number">
                <code>89042882020</code>
                <button @click="copyToClipboard('89042882020')" class="copy-btn" title="Скопировать">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                  </svg>
                </button>
              </div>
            </div>
          </div> -->

          <!-- ЮMoney -->
          <!-- <div class="donate-card">
            <div class="card-icon">🟡</div>
            <h3>ЮMoney</h3>
            <p>Перевод через ЮMoney (бывшие Яндекс.Деньги). Привяжите карту и переводите моментально.</p>
            <a 
              href="https://yoomoney.ru/fundraise/89659.4e9276d8b1c0" 
              target="_blank" 
              rel="noopener noreferrer"
              class="donate-btn secondary"
            >
              Перейти к сбору
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
            </a>
          </div> -->

          <!-- Криптовалюта -->
          <!-- <div class="donate-card">
            <div class="card-icon">₿</div>
            <h3>Криптовалюта</h3>
            <p>Принимаем различные криптовалюты. Переведите любую удобную вам монету.</p>
            <div class="crypto-info">
              <div class="crypto-item">
                <span class="crypto-name">USDT (TRC-20):</span>
                <code class="crypto-address">TXk8Ypz8r2KZ3Y1WaiqTxoS9G6wXqZ7YqJ</code>
              </div>
              <div class="crypto-item">
                <span class="crypto-name">BTC:</span>
                <code class="crypto-address">bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh</code>
              </div>
              <div class="crypto-item">
                <span class="crypto-name">ETH:</span>
                <code class="crypto-address">0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0</code>
              </div>
            </div>
            <button @click="copyCryptoAddress('TXk8Ypz8r2KZ3Y1WaiqTxoS9G6wXqZ7YqJ')" class="copy-btn-full">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              Скопировать USDT (TRC-20)
            </button>
          </div> -->
        </div>
      </section>
      <!-- 
      <section class="donate-faq">
        <h2>Частые вопросы</h2>
        
        <div class="faq-item">
          <h3>Буду ли я получать что-то за донат?</h3>
          <p>
            Мы не продаём подписки и привилегии — проект остаётся полностью бесплатным для всех. 
          </p>
        </div>
        <div class="faq-item">
          <h3>Могу ли я указать своё имя/никнейм?</h3>
          <p>
            Да! При донате через Donation Alerts вы можете указать ваш никнейм, и он будет отображаться в виджете донатов на сайте.
          </p>
        </div>

        <div class="faq-item">
          <h3>Как узнать, что мой донат получен?</h3>
          <p>
            После успешного перевода вы получите уведомление на экране, а ваш никнейм появится в ленте донатов на сайте.
          </p>
        </div>

        <div class="faq-item">
          <h3>Можно ли сделать разовый донат?</h3>
          <p>
            Конечно! Мы принимаем любые суммы — от 10 рублей и выше. Любая помощь для нас бесценна.
          </p>
        </div>
      </section>

      <section class="donate-thanks">
        <h2>Спасибо за поддержку! 🎉</h2>
        <p>
          Каждый ваш вклад помогает нам продолжать работу над проектом. 
          Мы обещаем использовать средства исключительно на развитие и поддержание сервиса.
        </p>
      </section> -->
    </div>
  </div>
</template>

<style scoped>
.donate-page {
  padding: 2rem 1rem;
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
}

.page-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 0.75rem 0;
}

.subtitle {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Причина */
.donate-reason {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 2rem;
}

.donate-reason h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 1rem 0;
}

.donate-reason p {
  font-size: 1rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0 0 1rem 0;
}

.reason-list {
  list-style: none;
  padding: 0;
  margin: 1rem 0 0 0;
}

.reason-list li {
  font-size: 1rem;
  color: var(--color-text-primary);
  padding: 0.5rem 0;
  padding-left: 1.5rem;
  position: relative;
}

.reason-list li::before {
  content: "✓";
  position: absolute;
  left: 0;
  color: var(--color-accent);
  font-weight: 600;
}

/* Методы доната */
.donate-methods {
  margin-bottom: 3rem;
}

.donate-methods h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 1.5rem 0;
  text-align: center;
}

.methods-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.donate-card {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 1rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}

.donate-card.main {
  grid-column: span 2;
  background: linear-gradient(135deg, rgba(58, 134, 255, 0.1) 0%, rgba(255, 107, 107, 0.1) 100%);
  border-color: var(--color-accent);
}

.card-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

.donate-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.75rem 0;
}

.donate-card p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0 0 1.25rem 0;
  flex: 1;
}

.donate-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
  border: none;
}

.donate-btn.primary {
  background: var(--color-accent);
  color: white;
}

.donate-btn.primary:hover {
  background: var(--color-accent-hover);
  transform: translateY(-1px);
}

.donate-btn.secondary {
  background: var(--color-background-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-divider-light);
}

.donate-btn.secondary:hover {
  background: var(--color-background-hover);
}

.donation-link {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-divider-light);
}

.link-label {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  display: block;
  margin-bottom: 0.25rem;
}

.link-value {
  font-family: monospace;
  font-size: 0.9375rem;
  color: var(--color-accent);
  background: var(--color-background);
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
}

.wallet-info {
  margin-top: auto;
}

.wallet-label {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  display: block;
  margin-bottom: 0.5rem;
}

.wallet-number {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.wallet-number code {
  font-family: monospace;
  font-size: 1.125rem;
  color: var(--color-text-primary);
  background: var(--color-background);
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
}

.copy-btn {
  padding: 0.5rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.375rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: var(--color-background-hover);
  color: var(--color-text-primary);
}

.crypto-info {
  margin-bottom: 1rem;
}

.crypto-item {
  margin-bottom: 0.75rem;
}

.crypto-name {
  font-size: 0.8125rem;
  color: var(--color-text-tertiary);
  display: block;
  margin-bottom: 0.25rem;
}

.crypto-address {
  font-family: monospace;
  font-size: 0.75rem;
  color: var(--color-text-primary);
  background: var(--color-background);
  padding: 0.375rem 0.5rem;
  border-radius: 0.25rem;
  word-break: break-all;
  display: block;
}

.copy-btn-full {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--color-background);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.5rem;
  color: var(--color-text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: auto;
}

.copy-btn-full:hover {
  background: var(--color-background-hover);
}

/* FAQ */
.donate-faq {
  margin-bottom: 3rem;
}

.donate-faq h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 1.5rem 0;
  text-align: center;
}

.faq-item {
  background: var(--color-background-surface);
  border: 1px solid var(--color-divider-light);
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin-bottom: 1rem;
}

.faq-item h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.5rem 0;
}

.faq-item p {
  font-size: 0.9375rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* Благодарность */
.donate-thanks {
  text-align: center;
  padding: 2rem;
  background: linear-gradient(135deg, rgba(58, 134, 255, 0.08) 0%, rgba(255, 107, 107, 0.08) 100%);
  border-radius: 1rem;
  border: 1px solid var(--color-divider-light);
}

.donate-thanks h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 0.75rem 0;
}

.donate-thanks p {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Адаптивность */
@media (max-width: 768px) {
  .methods-grid {
    grid-template-columns: 1fr;
  }

  .donate-card.main {
    grid-column: span 1;
  }

  .page-header h1 {
    font-size: 1.75rem;
  }

  .donate-reason,
  .donate-card,
  .faq-item {
    padding: 1.25rem;
  }
}
</style>
