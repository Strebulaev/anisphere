<template>
  <div class="settings-view">
    <div class="settings-container">
      <!-- Header -->
      <div class="settings-header">
        <button @click="$router.go(-1)" class="back-button">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
        <h1>Настройки</h1>
        <div class="header-spacer"></div>
      </div>

      <!-- Tabs -->
      <div class="settings-tabs">
        <button 
          :class="['tab', { active: activeTab === 'account' }]" 
          @click="activeTab = 'account'"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
          Редактировать профиль
        </button>
        <!-- <button 
          :class="['tab', { active: activeTab === 'delete' }]" 
          @click="activeTab = 'delete'"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
          Удаление аккаунта
        </button> -->
      </div>

      <!-- Content -->
      <div class="settings-content">
        <AccountSettings v-if="activeTab === 'account'" />
        <DeleteAccountSettings v-if="activeTab === 'delete'" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AccountSettings from '@/components/settings/AccountSettings.vue'
import DeleteAccountSettings from '@/components/settings/DeleteAccountSettings.vue'

const activeTab = ref('account')
</script>

<style scoped>
.settings-view {
  min-height: 100vh;
  background: var(--surface-2);
  color: var(--text-primary);
}

.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.back-button {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  width: 40px;
  height: 40px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.back-button:hover {
  background: var(--surface-4);
  border-color: var(--border-default);
}

.settings-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}

.header-spacer {
  flex: 1;
}

/* Tabs */
.settings-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  background: var(--surface-3);
  padding: 6px;
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
}

.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.tab.active {
  background: var(--accent);
  color: white;
}

/* Content */
.settings-content {
  background: var(--surface-3);
  border-radius: 16px;
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

@media (max-width: 600px) {
  .settings-tabs {
    flex-direction: column;
  }
  
  .tab {
    padding: 14px;
  }
}
</style>
