<template>
  <div class="settings-section">
    <h2>Р—Р°Р±Р»РѕРєРёСЂРѕРІР°РЅРЅС‹Рµ РїРѕР»СЊР·РѕРІР°С‚РµР»Рё</h2>

    <div class="settings-group">
      <h3>рџ”Ќ РџРѕРёСЃРє РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ</h3>
      <div class="search-section">
        <div class="search-input">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Р’РІРµРґРёС‚Рµ РёРјСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РёР»Рё ID..."
            class="text-input"
            @keyup.enter="searchUser"
          />
          <button @click="searchUser" class="search-btn">рџ”Ќ</button>
        </div>
        <div v-if="searchResults.length > 0" class="search-results">
          <div v-for="user in searchResults" :key="user.id" class="search-result-item">
            <img v-if="user.avatar" :src="user.avatar" class="user-avatar" />
            <div v-else class="user-avatar placeholder">рџ‘¤</div>
            <div class="user-info">
              <div class="user-name">{{ user.display_name || user.username }}</div>
              <div class="user-username">@{{ user.username }}</div>
            </div>
            <button @click="blockUser(user)" class="block-btn">
              рџљ« Р—Р°Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ
            </button>
          </div>
        </div>
        <div v-if="searchError" class="search-error">{{ searchError }}</div>
      </div>
    </div>

    <div class="settings-group">
      <h3>рџљ« РЎРїРёСЃРѕРє Р·Р°Р±Р»РѕРєРёСЂРѕРІР°РЅРЅС‹С… ({{ blockedUsers.length }})</h3>
      
      <div v-if="blockedUsers.length === 0" class="empty-state">
        <div class="empty-icon">рџ”“</div>
        <p>РЈ РІР°СЃ РЅРµС‚ Р·Р°Р±Р»РѕРєРёСЂРѕРІР°РЅРЅС‹С… РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№</p>
      </div>

      <div v-else class="blocked-list">
        <div v-for="user in blockedUsers" :key="user.id" class="blocked-item">
          <img v-if="user.avatar" :src="user.avatar" class="user-avatar" />
          <div v-else class="user-avatar placeholder">рџ‘¤</div>
          <div class="user-info">
            <div class="user-name">{{ user.display_name || user.username }}</div>
            <div class="user-username">@{{ user.username }}</div>
            <div class="block-date">Р—Р°Р±Р»РѕРєРёСЂРѕРІР°РЅ: {{ formatDate(user.blocked_at) }}</div>
          </div>
          <button @click="unblockUser(user)" class="unblock-btn">
            рџ”“ Р Р°Р·Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ
          </button>
        </div>
      </div>

      <div v-if="blockedUsers.length > 0" class="bulk-actions">
        <button @click="showUnblockAllConfirm = true" class="unblock-all-btn">
          рџ”“ Р Р°Р·Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ РІСЃРµС…
        </button>
      </div>
    </div>

    <div class="settings-group info-group">
      <h3>в„№пёЏ Р§С‚Рѕ РїСЂРѕРёСЃС…РѕРґРёС‚ РїСЂРё Р±Р»РѕРєРёСЂРѕРІРєРµ?</h3>
      <div class="info-list">
        <div class="info-item">
          <span class="info-icon">рџ’¬</span>
          <span>РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РјРѕР¶РµС‚ РїРёСЃР°С‚СЊ РІР°Рј РІ Р»РёС‡РЅС‹Рµ СЃРѕРѕР±С‰РµРЅРёСЏ</span>
        </div>
        <div class="info-item">
          <span class="info-icon">рџ’­</span>
          <span>РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РјРѕР¶РµС‚ РєРѕРјРјРµРЅС‚РёСЂРѕРІР°С‚СЊ РІР°С€ РєРѕРЅС‚РµРЅС‚</span>
        </div>
        <div class="info-item">
          <span class="info-icon">рџ‘ЃпёЏ</span>
          <span>РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РІРёРґРёС‚ РІР°С€ РѕРЅР»Р°Р№РЅ-СЃС‚Р°С‚СѓСЃ</span>
        </div>
        <div class="info-item">
          <span class="info-icon">рџ“µ</span>
          <span>Р’С‹ РЅРµ РІРёРґРёС‚Рµ РїРѕСЃС‚С‹ Рё РєРѕРјРјРµРЅС‚Р°СЂРёРё Р·Р°Р±Р»РѕРєРёСЂРѕРІР°РЅРЅРѕРіРѕ</span>
        </div>
        <div class="info-item">
          <span class="info-icon">рџ”•</span>
          <span>Р’С‹ РЅРµ Р±СѓРґРµС‚Рµ РїРѕР»СѓС‡Р°С‚СЊ СѓРІРµРґРѕРјР»РµРЅРёСЏ Рѕ РµРіРѕ Р°РєС‚РёРІРЅРѕСЃС‚Рё</span>
        </div>
      </div>
    </div>

    <!-- Unblock All Confirmation Modal -->
    <div v-if="showUnblockAllConfirm" class="modal-overlay" @click="showUnblockAllConfirm = false">
      <div class="modal" @click.stop>
        <h3>рџ”“ Р Р°Р·Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ РІСЃРµС…?</h3>
        <p>Р’С‹ СѓРІРµСЂРµРЅС‹, С‡С‚Рѕ С…РѕС‚РёС‚Рµ СЂР°Р·Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ РІСЃРµС… РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ ({{ blockedUsers.length }})?</p>
        <p class="warning">Р­С‚Рѕ РґРµР№СЃС‚РІРёРµ РЅРµР»СЊР·СЏ РѕС‚РјРµРЅРёС‚СЊ.</p>
        
        <div class="modal-actions">
          <button @click="showUnblockAllConfirm = false" class="cancel-btn">РћС‚РјРµРЅР°</button>
          <button @click="unblockAllUsers" class="confirm-btn">Р Р°Р·Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ РІСЃРµС…</button>
        </div>
      </div>
    </div>

    <!-- Block Confirmation Modal -->
    <div v-if="showBlockConfirm" class="modal-overlay" @click="showBlockConfirm = false">
      <div class="modal" @click.stop>
        <h3>рџљ« Р—Р°Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ?</h3>
        <div v-if="userToBlock" class="user-preview">
          <img v-if="userToBlock.avatar" :src="userToBlock.avatar" class="preview-avatar" />
          <div v-else class="preview-avatar placeholder">рџ‘¤</div>
          <div class="preview-info">
            <div class="preview-name">{{ userToBlock.display_name || userToBlock.username }}</div>
            <div class="preview-username">@{{ userToBlock.username }}</div>
          </div>
        </div>
        <p class="warning">Р’С‹ Р±РѕР»СЊС€Рµ РЅРµ Р±СѓРґРµС‚Рµ РІРёРґРµС‚СЊ РєРѕРЅС‚РµРЅС‚ СЌС‚РѕРіРѕ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ.</p>
        
        <div class="modal-actions">
          <button @click="showBlockConfirm = false" class="cancel-btn">РћС‚РјРµРЅР°</button>
          <button @click="confirmBlock" class="danger-btn">Р—Р°Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '@/composables/useToast'
const { show: showToast } = useToast()
import { ref, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'

interface BlockedUser {
  id: number
  username: string
  display_name?: string
  avatar?: string
  blocked_at: string
}

interface SearchResult {
  id: number
  username: string
  display_name?: string
  avatar?: string
}

const blockedUsers = ref<BlockedUser[]>([])
const searchQuery = ref('')
const searchResults = ref<SearchResult[]>([])
const searchError = ref('')

const showUnblockAllConfirm = ref(false)
const showBlockConfirm = ref(false)
const userToBlock = ref<SearchResult | null>(null)

const fetchBlockedUsers = async () => {
  try {
    const data = await settingsApi.getBlockedUsers()
    blockedUsers.value = data
  } catch (error) {
    console.error('Error fetching blocked users:', error)
  }
}

const searchUser = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    searchError.value = ''
    return
  }

  try {
    const response = await fetch(`/api/users/search/?q=${encodeURIComponent(searchQuery.value)}`)
    const data = await response.json()
    searchResults.value = data.results || data
    searchError.value = ''
  } catch (error) {
    console.error('Error searching users:', error)
    searchError.value = 'РћС€РёР±РєР° РїСЂРё РїРѕРёСЃРєРµ'
    searchResults.value = []
  }
}

const blockUser = (user: SearchResult) => {
  userToBlock.value = user
  showBlockConfirm.value = true
}

const confirmBlock = async () => {
  if (!userToBlock.value) return

  try {
    await settingsApi.blockUser(userToBlock.value.id)
    blockedUsers.value.push({
      id: userToBlock.value.id,
      username: userToBlock.value.username,
      display_name: userToBlock.value.display_name,
      avatar: userToBlock.value.avatar,
      blocked_at: new Date().toISOString()
    })
    searchResults.value = searchResults.value.filter(u => u.id !== userToBlock.value?.id)
    searchQuery.value = ''
    showBlockConfirm.value = false
    userToBlock.value = null
  } catch (error) {
    console.error('Error blocking user:', error)
    showToast('РћС€РёР±РєР° РїСЂРё Р±Р»РѕРєРёСЂРѕРІРєРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ')
  }
}

const unblockUser = async (user: BlockedUser) => {
  try {
    await settingsApi.unblockUser(user.id)
    blockedUsers.value = blockedUsers.value.filter(u => u.id !== user.id)
  } catch (error) {
    console.error('Error unblocking user:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЂР°Р·Р±Р»РѕРєРёСЂРѕРІРєРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ')
  }
}

const unblockAllUsers = async () => {
  try {
    // Р Р°Р·Р±Р»РѕРєРёСЂСѓРµРј РІСЃРµС… РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№
    for (const user of blockedUsers.value) {
      await settingsApi.unblockUser(user.id)
    }
    blockedUsers.value = []
    showUnblockAllConfirm.value = false
  } catch (error) {
    console.error('Error unblocking all users:', error)
    showToast('РћС€РёР±РєР° РїСЂРё СЂР°Р·Р±Р»РѕРєРёСЂРѕРІРєРµ РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№')
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

onMounted(() => {
  fetchBlockedUsers()
})
</script>

<style scoped>
.settings-group {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--hover-bg);
  border-radius: 8px;
}

.settings-group h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
}

.search-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.search-input {
  display: flex;
  gap: 10px;
}

.text-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 14px;
}

.search-btn {
  padding: 10px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
}

.search-results {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--card-bg);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.user-avatar.placeholder {
  background: var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.user-username {
  font-size: 13px;
  color: var(--secondary-text);
}

.block-btn {
  padding: 8px 12px;
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
  border: 1px solid #f44336;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.search-error {
  color: #f44336;
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 60px;
  margin-bottom: 15px;
}

.empty-state p {
  color: var(--secondary-text);
  margin: 0;
}

.blocked-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.blocked-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--card-bg);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.block-date {
  font-size: 12px;
  color: var(--secondary-text);
  margin-top: 2px;
}

.unblock-btn {
  padding: 8px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.bulk-actions {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.unblock-all-btn {
  width: 100%;
  padding: 10px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
}

.info-group {
  background: rgba(0, 132, 255, 0.05);
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}

.info-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--card-bg);
  padding: 30px;
  border-radius: 12px;
  max-width: 400px;
  width: 90%;
  border: 1px solid var(--border-color);
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.user-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: var(--hover-bg);
  border-radius: 6px;
  margin-bottom: 15px;
}

.preview-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
}

.preview-avatar.placeholder {
  background: var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.preview-name {
  font-weight: 500;
}

.preview-username {
  font-size: 13px;
  color: var(--secondary-text);
}

.warning {
  color: #f44336;
  font-size: 14px;
  margin: 10px 0;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.cancel-btn {
  flex: 1;
  padding: 10px 16px;
  background: var(--hover-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
}

.confirm-btn {
  flex: 1;
  padding: 10px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.danger-btn {
  flex: 1;
  padding: 10px 16px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
</style>
