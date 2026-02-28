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
          <AccountSettings v-if="activeTab === 'account'" />

          <!-- Password Change -->
          <ChangePassword v-if="activeTab === 'password'" />

          <!-- Contacts -->
          <EmailPhoneSettings v-if="activeTab === 'contacts'" />

          <!-- Two-Factor Authentication -->
          <TwoFactorSettings v-if="activeTab === '2fa'" />

          <!-- Privacy Settings -->
          <PrivacySettings v-if="activeTab === 'privacy'" />

          <!-- Active Sessions -->
          <SessionsSettings v-if="activeTab === 'sessions'" />

          <!-- Blocked Users -->
          <BlockedUsersSettings v-if="activeTab === 'blocked'" />

          <!-- Delete Account -->
          <DeleteAccountSettings v-if="activeTab === 'delete'" />

          <!-- Notifications -->
          <NotificationsSettings v-if="activeTab === 'notifications'" />

          <!-- Email Settings -->
          <EmailSettings v-if="activeTab === 'email-settings'" />

          <!-- Sounds -->
          <SoundsSettings v-if="activeTab === 'sounds'" />

          <!-- Theme -->
          <ThemeSettings v-if="activeTab === 'theme'" />

          <!-- Chat Background -->
          <ChatBackgroundSettings v-if="activeTab === 'chat-background'" />

          <!-- Fonts -->
          <FontsSettings v-if="activeTab === 'fonts'" />

          <!-- Storage -->
          <StorageSettings v-if="activeTab === 'storage'" />

          <!-- Sync -->
          <SyncSettings v-if="activeTab === 'sync'" />

          <!-- Export -->
          <ExportDataSettings v-if="activeTab === 'export'" />

          <!-- Cache -->
          <ClearCacheSettings v-if="activeTab === 'cache'" />

          <!-- Language -->
          <LanguageSettings v-if="activeTab === 'language'" />

          <!-- Advanced -->
          <AdvancedSettings v-if="activeTab === 'advanced'" />

          <!-- About -->
          <AboutSettings v-if="activeTab === 'about'" />
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
import AccountSettings from '@/components/settings/AccountSettings.vue'
import ChangePassword from '@/components/settings/ChangePassword.vue'
import EmailPhoneSettings from '@/components/settings/EmailPhoneSettings.vue'
import BlockedUsersSettings from '@/components/settings/BlockedUsersSettings.vue'
import DeleteAccountSettings from '@/components/settings/DeleteAccountSettings.vue'
import SoundsSettings from '@/components/settings/SoundsSettings.vue'
import ChatBackgroundSettings from '@/components/settings/ChatBackgroundSettings.vue'
import FontsSettings from '@/components/settings/FontsSettings.vue'
import SyncSettings from '@/components/settings/SyncSettings.vue'
import ExportDataSettings from '@/components/settings/ExportDataSettings.vue'
import ClearCacheSettings from '@/components/settings/ClearCacheSettings.vue'
import AboutSettings from '@/components/settings/AboutSettings.vue'

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