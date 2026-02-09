<template>
  <div class="settings-view">
    <div class="settings-container">
      <!-- Header -->
      <div class="settings-header">
        <button @click="$router.go(-1)" class="back-button">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h1>Настройки</h1>
        <div class="header-spacer"></div>
      </div>

      <!-- Sidebar Navigation -->
      <div class="settings-layout">
        <div class="settings-sidebar">
          <div class="sidebar-section">
            <h2>Учетная запись</h2>
            <div class="sidebar-item" :class="{ active: activeTab === 'account' }" @click="activeTab = 'account'">
              <i class="fas fa-user"></i>
              <span>Редактировать профиль</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'password' }" @click="activeTab = 'password'">
              <i class="fas fa-key"></i>
              <span>Сменить пароль</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'contacts' }" @click="activeTab = 'contacts'">
              <i class="fas fa-address-book"></i>
              <span>Email и телефон</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === '2fa' }" @click="activeTab = '2fa'">
              <i class="fas fa-shield-alt"></i>
              <span>Двухфакторная аутентификация</span>
            </div>
          </div>

          <div class="sidebar-section">
            <h2>Конфиденциальность и безопасность</h2>
            <div class="sidebar-item" :class="{ active: activeTab === 'privacy' }" @click="activeTab = 'privacy'">
              <i class="fas fa-eye"></i>
              <span>Приватность</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'sessions' }" @click="activeTab = 'sessions'">
              <i class="fas fa-mobile-alt"></i>
              <span>Активные сессии</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'blocked' }" @click="activeTab = 'blocked'">
              <i class="fas fa-ban"></i>
              <span>Заблокированные пользователи</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'delete' }" @click="activeTab = 'delete'">
              <i class="fas fa-trash-alt"></i>
              <span>Удаление аккаунта</span>
            </div>
          </div>

          <div class="sidebar-section">
            <h2>Уведомления и звуки</h2>
            <div class="sidebar-item" :class="{ active: activeTab === 'notifications' }" @click="activeTab = 'notifications'">
              <i class="fas fa-bell"></i>
              <span>Уведомления</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'email-settings' }" @click="activeTab = 'email-settings'">
              <i class="fas fa-envelope"></i>
              <span>Email уведомления</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'sounds' }" @click="activeTab = 'sounds'">
              <i class="fas fa-volume-up"></i>
              <span>Звуки и вибрация</span>
            </div>
          </div>

          <div class="sidebar-section">
            <h2>Внешний вид</h2>
            <div class="sidebar-item" :class="{ active: activeTab === 'theme' }" @click="activeTab = 'theme'">
              <i class="fas fa-palette"></i>
              <span>Тема и оформление</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'chat-background' }" @click="activeTab = 'chat-background'">
              <i class="fas fa-image"></i>
              <span>Фон чатов</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'fonts' }" @click="activeTab = 'fonts'">
              <i class="fas fa-font"></i>
              <span>Шрифты и размер</span>
            </div>
          </div>

          <div class="sidebar-section">
            <h2>Данные и хранилище</h2>
            <div class="sidebar-item" :class="{ active: activeTab === 'storage' }" @click="activeTab = 'storage'">
              <i class="fas fa-hdd"></i>
              <span>Использование памяти</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'sync' }" @click="activeTab = 'sync'">
              <i class="fas fa-sync"></i>
              <span>Синхронизация</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'export' }" @click="activeTab = 'export'">
              <i class="fas fa-download"></i>
              <span>Экспорт данных</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'cache' }" @click="activeTab = 'cache'">
              <i class="fas fa-broom"></i>
              <span>Очистка кэша</span>
            </div>
          </div>

          <div class="sidebar-section">
            <h2>Дополнительно</h2>
            <div class="sidebar-item" :class="{ active: activeTab === 'language' }" @click="activeTab = 'language'">
              <i class="fas fa-globe"></i>
              <span>Язык и регион</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'advanced' }" @click="activeTab = 'advanced'">
              <i class="fas fa-cogs"></i>
              <span>Расширенные настройки</span>
            </div>
            <div class="sidebar-item" :class="{ active: activeTab === 'about' }" @click="activeTab = 'about'">
              <i class="fas fa-info-circle"></i>
              <span>О программе</span>
            </div>
          </div>
        </div>

        <!-- Main Content -->
        <div class="settings-content">
          <!-- Account Settings -->
          <div v-if="activeTab === 'account'" class="settings-section">
            <h2>Редактировать профиль</h2>
            <!-- Profile settings content will be added here -->
            <p>Настройки профиля в разработке...</p>
          </div>

          <!-- Password Change -->
          <div v-if="activeTab === 'password'" class="settings-section">
            <h2>Сменить пароль</h2>
            <!-- Password change content will be added here -->
            <p>Смена пароля в разработке...</p>
          </div>

          <!-- Contacts -->
          <div v-if="activeTab === 'contacts'" class="settings-section">
            <h2>Email и телефон</h2>
            <!-- Contacts content will be added here -->
            <p>Настройки контактов в разработке...</p>
          </div>

          <!-- Two-Factor Authentication -->
          <TwoFactorSettings v-if="activeTab === '2fa'" />

          <!-- Privacy Settings -->
          <PrivacySettings v-if="activeTab === 'privacy'" />

          <!-- Active Sessions -->
          <SessionsSettings v-if="activeTab === 'sessions'" />

          <!-- Blocked Users -->
          <div v-if="activeTab === 'blocked'" class="settings-section">
            <h2>Заблокированные пользователи</h2>
            <!-- Blocked users content will be added here -->
            <p>Список заблокированных пользователей в разработке...</p>
          </div>

          <!-- Delete Account -->
          <div v-if="activeTab === 'delete'" class="settings-section">
            <h2>Удаление аккаунта</h2>
            <!-- Delete account content will be added here -->
            <p>Удаление аккаунта в разработке...</p>
          </div>

          <!-- Notifications -->
          <NotificationsSettings v-if="activeTab === 'notifications'" />

          <!-- Email Settings -->
          <EmailSettings v-if="activeTab === 'email-settings'" />

          <!-- Sounds -->
          <div v-if="activeTab === 'sounds'" class="settings-section">
            <h2>Звуки и вибрация</h2>
            <!-- Sounds content will be added here -->
            <p>Настройки звуков в разработке...</p>
          </div>

          <!-- Theme -->
          <ThemeSettings v-if="activeTab === 'theme'" />

          <!-- Chat Background -->
          <div v-if="activeTab === 'chat-background'" class="settings-section">
            <h2>Фон чатов</h2>
            <!-- Chat background content will be added here -->
            <p>Настройки фона чатов в разработке...</p>
          </div>

          <!-- Fonts -->
          <div v-if="activeTab === 'fonts'" class="settings-section">
            <h2>Шрифты и размер</h2>
            <!-- Fonts content will be added here -->
            <p>Настройки шрифтов в разработке...</p>
          </div>

          <!-- Storage -->
          <StorageSettings v-if="activeTab === 'storage'" />

          <!-- Sync -->
          <div v-if="activeTab === 'sync'" class="settings-section">
            <h2>Синхронизация</h2>
            <!-- Sync content will be added here -->
            <p>Настройки синхронизации в разработке...</p>
          </div>

          <!-- Export -->
          <div v-if="activeTab === 'export'" class="settings-section">
            <h2>Экспорт данных</h2>
            <!-- Export content will be added here -->
            <p>Экспорт данных в разработке...</p>
          </div>

          <!-- Cache -->
          <div v-if="activeTab === 'cache'" class="settings-section">
            <h2>Очистка кэша</h2>
            <!-- Cache content will be added here -->
            <p>Очистка кэша в разработке...</p>
          </div>

          <!-- Language -->
          <LanguageSettings v-if="activeTab === 'language'" />

          <!-- Advanced -->
          <AdvancedSettings v-if="activeTab === 'advanced'" />

          <!-- About -->
          <div v-if="activeTab === 'about'" class="settings-section">
            <h2>О программе</h2>
            <!-- About content will be added here -->
            <p>Информация о программе в разработке...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import TwoFactorSettings from '@/components/settings/TwoFactorSettings.vue'
import PrivacySettings from '@/components/settings/PrivacySettings.vue'
import SessionsSettings from '@/components/settings/SessionsSettings.vue'
import NotificationsSettings from '@/components/settings/NotificationsSettings.vue'
import EmailSettings from '@/components/settings/EmailSettings.vue'
import ThemeSettings from '@/components/settings/ThemeSettings.vue'
import StorageSettings from '@/components/settings/StorageSettings.vue'
import LanguageSettings from '@/components/settings/LanguageSettings.vue'
import AdvancedSettings from '@/components/settings/AdvancedSettings.vue'

const activeTab = ref('account')

onMounted(() => {
  // Load initial settings
})
</script>

<style scoped>
.settings-view {
  min-height: 100vh;
  background: var(--color-background);
  color: var(--color-text-primary);
}

.settings-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-divider);
}

.back-button {
  background: none;
  border: none;
  color: var(--color-text-primary);
  font-size: 20px;
  cursor: pointer;
  padding: 10px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.back-button:hover {
  background: var(--color-background-surface);
}

.settings-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text);
}

.header-spacer {
  flex: 1;
}

.settings-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 40px;
}

.settings-sidebar {
  background: var(--color-background-surface);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--color-divider);
  height: fit-content;
}

.sidebar-section {
  margin-bottom: 30px;
}

.sidebar-section h2 {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 15px;
  margin-top: 0;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  color: var(--color-text-primary);
}

.sidebar-item:hover {
  background: var(--color-background-active);
}

.sidebar-item.active {
  background: var(--color-accent);
  color: white;
}

.sidebar-item i {
  width: 16px;
  text-align: center;
}

.settings-content {
  background: var(--color-background-surface);
  border-radius: 12px;
  padding: 30px;
  border: 1px solid var(--color-divider);
  min-height: 600px;
}

.settings-section h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
}

@media (max-width: 768px) {
  .settings-layout {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .settings-sidebar {
    order: 2;
  }

  .settings-content {
    order: 1;
    padding: 20px;
  }
}
</style>