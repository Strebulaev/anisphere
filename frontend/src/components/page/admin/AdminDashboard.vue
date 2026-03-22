<template>
  <div class="admin-dashboard">
    <div class="admin-header">
      <h1>🛡️ Панель администратора</h1>
      <p class="admin-subtitle">Добро пожаловать, <strong>@{{ currentUser?.nickname || currentUser?.username }}</strong></p>
    </div>

    <!-- Табы -->
    <div class="admin-tabs">
      <button
        v-for="t in tabs" :key="t.id"
        :class="['tab-btn', { active: activeTab === t.id }]"
        @click="activeTab = t.id"
      >
        {{ t.icon }} {{ t.label }}
        <span v-if="t.id === 'complaints' && stats.pending_complaints" class="badge">
          {{ stats.pending_complaints }}
        </span>
      </button>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="loading-state">⏳ Загрузка...</div>

    <!-- Вкладка: Статистика -->
    <div v-else-if="activeTab === 'stats'" class="tab-content">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">👥</div>
          <div class="stat-value">{{ stats.total_users || 0 }}</div>
          <div class="stat-label">Всего пользователей</div>
        </div>
        <div class="stat-card green">
          <div class="stat-icon">🟢</div>
          <div class="stat-value">{{ stats.online_now || 0 }}</div>
          <div class="stat-label">Онлайн сейчас</div>
        </div>
        <div class="stat-card blue">
          <div class="stat-icon">📅</div>
          <div class="stat-value">{{ stats.registered_today || 0 }}</div>
          <div class="stat-label">Зарегистрировались сегодня</div>
        </div>
        <div class="stat-card purple">
          <div class="stat-icon">📊</div>
          <div class="stat-value">{{ stats.registered_this_week || 0 }}</div>
          <div class="stat-label">За последнюю неделю</div>
        </div>
        <div class="stat-card red">
          <div class="stat-icon">⚠️</div>
          <div class="stat-value">{{ stats.pending_complaints || 0 }}</div>
          <div class="stat-label">Необработанных жалоб</div>
        </div>
      </div>
    </div>

    <!-- Вкладка: Новые регистрации -->
    <div v-else-if="activeTab === 'registrations'" class="tab-content">
      <div class="section-title">Последние регистрации</div>
      <div class="users-table">
        <div class="table-header">
          <span>Пользователь</span>
          <span>Email</span>
          <span>Статус</span>
          <span>Дата</span>
        </div>
        <div v-for="u in recentRegistrations" :key="u.id" class="table-row">
          <div class="user-cell">
            <router-link :to="`/profile/@${u.nickname || u.username}`" class="user-link">
              @{{ u.nickname || u.username }}
            </router-link>
          </div>
          <div class="cell">{{ u.email || '—' }}</div>
          <div class="cell">
            <span :class="['status-dot', { online: u.is_online }]"></span>
            {{ u.is_online ? 'Онлайн' : 'Офлайн' }}
          </div>
          <div class="cell date">{{ formatDate(u.date_joined) }}</div>
        </div>
        <div v-if="!recentRegistrations.length" class="empty-state">Нет данных</div>
      </div>
    </div>

    <!-- Вкладка: Онлайн пользователи -->
    <div v-else-if="activeTab === 'online'" class="tab-content">
      <div class="section-title">Пользователи онлайн ({{ onlineUsers.length }})</div>
      <div class="users-table">
        <div class="table-header">
          <span>Пользователь</span>
          <span>Последний вход</span>
          <span>Действие</span>
        </div>
        <div v-for="u in onlineUsers" :key="u.id" class="table-row">
          <div class="user-cell">
            <span class="online-indicator">🟢</span>
            <router-link :to="`/profile/@${u.nickname || u.username}`" class="user-link">
              @{{ u.nickname || u.username }}
            </router-link>
          </div>
          <div class="cell date">{{ u.last_login ? formatDate(u.last_login) : '—' }}</div>
          <div class="cell">
            <router-link :to="`/profile/@${u.nickname || u.username}`" class="btn-view">
              Профиль →
            </router-link>
          </div>
        </div>
        <div v-if="!onlineUsers.length" class="empty-state">Никого нет онлайн</div>
      </div>
    </div>

    <!-- Вкладка: Жалобы -->
    <div v-else-if="activeTab === 'complaints'" class="tab-content">
      <div class="complaints-toolbar">
        <div class="section-title">Жалобы</div>
        <div class="filter-row">
          <button
            v-for="s in complaintStatuses" :key="s.value"
            :class="['filter-btn', { active: complaintFilter === s.value }]"
            @click="setComplaintFilter(s.value)"
          >
            {{ s.label }}
          </button>
        </div>
      </div>

      <div v-if="complaintsLoading" class="loading-state">⏳ Загрузка жалоб...</div>
      <div v-else class="complaints-list">
        <div v-for="c in complaints" :key="c.id" class="complaint-card" :class="c.status">
          <div class="complaint-header">
            <span class="complaint-type">{{ complaintTypeLabel(c.complaint_type) }}</span>
            <span :class="['complaint-status', c.status]">{{ complaintStatusLabel(c.status) }}</span>
            <span class="complaint-date">{{ formatDate(c.created_at) }}</span>
          </div>
          <div class="complaint-meta">
            От: <strong>@{{ c.complainant?.nickname || c.complainant?.username }}</strong>
            &nbsp;·&nbsp; Причина: <strong>{{ complaintReasonLabel(c.reason) }}</strong>
          </div>
          <div v-if="c.description" class="complaint-desc">{{ c.description }}</div>
          <div class="complaint-actions">
            <button
              v-if="c.status === 'pending'"
              @click="resolveComplaint(c.id, 'investigating')"
              class="btn-action blue"
            >🔍 Расследовать</button>
            <button
              v-if="c.status !== 'resolved'"
              @click="resolveComplaint(c.id, 'resolved')"
              class="btn-action green"
            >✅ Решена</button>
            <button
              v-if="c.status !== 'dismissed'"
              @click="resolveComplaint(c.id, 'dismissed')"
              class="btn-action gray"
            >❌ Отклонить</button>
          </div>
        </div>
        <div v-if="!complaints.length" class="empty-state">Жалоб нет 🎉</div>
      </div>
    </div>

    <!-- Refresh -->
    <div class="refresh-bar">
      <button @click="loadAll" class="btn-refresh" :disabled="loading">
        🔄 Обновить данные
      </button>
      <span class="refresh-time" v-if="lastRefresh">Обновлено: {{ lastRefresh }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const props = defineProps({
  tab: { type: String, default: 'stats' }
})

const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)

const activeTab = ref(props.tab || 'stats')
const loading = ref(false)
const complaintsLoading = ref(false)
const lastRefresh = ref('')

const stats = ref<any>({})
const recentRegistrations = ref<any[]>([])
const onlineUsers = ref<any[]>([])
const complaints = ref<any[]>([])
const complaintFilter = ref('pending')

const tabs = [
  { id: 'stats',         icon: '📊', label: 'Статистика' },
  { id: 'registrations', icon: '👤', label: 'Регистрации' },
  { id: 'online',        icon: '🟢', label: 'Онлайн' },
  { id: 'complaints',    icon: '⚠️', label: 'Жалобы' },
]

const complaintStatuses = [
  { value: 'pending',      label: '⏳ На рассмотрении' },
  { value: 'investigating',label: '🔍 Расследуется' },
  { value: 'resolved',     label: '✅ Решённые' },
  { value: 'dismissed',    label: '❌ Отклонённые' },
  { value: 'all',          label: '📋 Все' },
]

const loadDashboard = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/users/admin/dashboard/')
    stats.value = data.stats || {}
    recentRegistrations.value = data.recent_registrations || []
    onlineUsers.value = data.online_users || []
    lastRefresh.value = new Date().toLocaleTimeString('ru-RU')
  } catch (e) {
    console.error('Admin dashboard error:', e)
  } finally {
    loading.value = false
  }
}

const loadComplaints = async () => {
  complaintsLoading.value = true
  try {
    const { data } = await api.get(`/users/admin/complaints/?status=${complaintFilter.value}`)
    complaints.value = data.results || []
  } catch (e) {
    console.error('Complaints error:', e)
  } finally {
    complaintsLoading.value = false
  }
}

const setComplaintFilter = (val: string) => {
  complaintFilter.value = val
  loadComplaints()
}

const resolveComplaint = async (id: number, newStatus: string) => {
  try {
    await api.patch(`/users/admin/complaints/${id}/`, { status: newStatus })
    await loadComplaints()
    await loadDashboard()
  } catch (e) {
    console.error('Resolve complaint error:', e)
  }
}

const loadAll = () => {
  loadDashboard()
  if (activeTab.value === 'complaints') loadComplaints()
}

watch(activeTab, (val) => {
  if (val === 'complaints') loadComplaints()
})

const formatDate = (d: string) => {
  if (!d) return '—'
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

const complaintTypeLabel = (t: string) => ({
  playlist: 'Плейлист', comment: 'Комментарий', reactor_post: 'Пост',
  user: 'Пользователь', dub: 'Озвучка', group: 'Группа', playlist_item: 'Эл. плейлиста'
}[t] || t)

const complaintReasonLabel = (r: string) => ({
  spam: 'Спам', harassment: 'Харассмент', inappropriate: 'Неподходящий контент',
  copyright: 'Авторские права', misleading: 'Вводящая в заблуждение',
  broken_link: 'Битая ссылка', duplicate: 'Дубликат', other: 'Другое'
}[r] || r)

const complaintStatusLabel = (s: string) => ({
  pending: '⏳ На рассмотрении', investigating: '🔍 Расследуется',
  resolved: '✅ Решена', dismissed: '❌ Отклонена'
}[s] || s)

onMounted(() => {
  loadDashboard()
  if (props.tab === 'complaints') {
    activeTab.value = 'complaints'
    loadComplaints()
  }
})
</script>

<style scoped>
.admin-dashboard {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
  min-height: 100vh;
}

.admin-header {
  margin-bottom: 24px;
}

.admin-header h1 {
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 4px;
}

.admin-subtitle {
  color: var(--text-secondary, #aaa);
  font-size: 14px;
  margin: 0;
}

/* Tabs */
.admin-tabs {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--border-color, #333);
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 10px 18px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary, #aaa);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.tab-btn:hover { color: var(--text-color, #fff); }
.tab-btn.active {
  color: var(--primary-color, #6c63ff);
  border-bottom-color: var(--primary-color, #6c63ff);
}

.badge {
  background: #ef4444;
  color: #fff;
  border-radius: 99px;
  padding: 1px 7px;
  font-size: 11px;
  font-weight: 700;
  min-width: 18px;
  text-align: center;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--card-bg, #1e1e1e);
  border: 1px solid var(--border-color, #333);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  transition: transform 0.15s;
}

.stat-card:hover { transform: translateY(-2px); }
.stat-card.green { border-color: #22c55e33; background: #22c55e0a; }
.stat-card.blue  { border-color: #3b82f633; background: #3b82f60a; }
.stat-card.purple{ border-color: #8b5cf633; background: #8b5cf60a; }
.stat-card.red   { border-color: #ef444433; background: #ef44440a; }

.stat-icon { font-size: 28px; margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; margin-bottom: 4px; }
.stat-label { font-size: 13px; color: var(--secondary-text, #aaa); }

/* Tables */
.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.users-table {
  background: var(--card-bg, #1e1e1e);
  border: 1px solid var(--border-color, #333);
  border-radius: 12px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 2fr 1fr 1.5fr;
  padding: 12px 16px;
  background: var(--hover-bg, #2a2a2a);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--secondary-text, #aaa);
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 2fr 1fr 1.5fr;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color, #333);
  align-items: center;
  transition: background 0.1s;
}

.table-row:hover { background: var(--hover-bg, #2a2a2a); }

.user-cell { display: flex; align-items: center; gap: 8px; }
.user-link { color: var(--primary-color, #6c63ff); text-decoration: none; font-weight: 500; }
.user-link:hover { text-decoration: underline; }

.cell { font-size: 14px; color: var(--secondary-text, #aaa); }
.cell.date { font-size: 12px; }

.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #6b7280; display: inline-block; margin-right: 6px;
}
.status-dot.online { background: #22c55e; }
.online-indicator { font-size: 10px; }

.btn-view {
  color: var(--primary-color, #6c63ff);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
}
.btn-view:hover { text-decoration: underline; }

.empty-state {
  padding: 32px;
  text-align: center;
  color: var(--secondary-text, #aaa);
  font-size: 15px;
}

/* Complaints */
.complaints-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-row { display: flex; gap: 8px; flex-wrap: wrap; }
.filter-btn {
  padding: 6px 14px;
  background: var(--card-bg, #1e1e1e);
  border: 1px solid var(--border-color, #333);
  border-radius: 20px;
  color: var(--secondary-text, #aaa);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.filter-btn:hover { border-color: var(--primary-color, #6c63ff); }
.filter-btn.active {
  background: var(--primary-color, #6c63ff);
  color: #fff;
  border-color: var(--primary-color, #6c63ff);
}

.complaints-list { display: flex; flex-direction: column; gap: 12px; }

.complaint-card {
  background: var(--card-bg, #1e1e1e);
  border: 1px solid var(--border-color, #333);
  border-radius: 12px;
  padding: 16px;
}
.complaint-card.resolved { border-color: #22c55e33; opacity: 0.75; }
.complaint-card.dismissed { opacity: 0.5; }

.complaint-header {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.complaint-type {
  font-weight: 600;
  font-size: 14px;
}

.complaint-status {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 99px;
}
.complaint-status.pending     { background: #f59e0b22; color: #f59e0b; }
.complaint-status.investigating{ background: #3b82f622; color: #3b82f6; }
.complaint-status.resolved    { background: #22c55e22; color: #22c55e; }
.complaint-status.dismissed   { background: #6b728022; color: #6b7280; }

.complaint-date { font-size: 12px; color: var(--secondary-text, #aaa); margin-left: auto; }
.complaint-meta { font-size: 13px; color: var(--secondary-text, #aaa); margin-bottom: 6px; }
.complaint-meta strong { color: var(--text-color, #fff); }
.complaint-desc {
  font-size: 13px;
  color: var(--text-color, #eee);
  background: var(--hover-bg, #2a2a2a);
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 10px;
}

.complaint-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-action {
  padding: 6px 14px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-action:hover { opacity: 0.8; }
.btn-action.blue  { background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f633; }
.btn-action.green { background: #22c55e22; color: #22c55e; border: 1px solid #22c55e33; }
.btn-action.gray  { background: #6b728022; color: #9ca3af; border: 1px solid #6b728033; }

/* Refresh bar */
.refresh-bar {
  margin-top: 32px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-refresh {
  padding: 8px 18px;
  background: var(--card-bg, #1e1e1e);
  border: 1px solid var(--border-color, #333);
  border-radius: 8px;
  color: var(--text-color, #fff);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-refresh:hover { background: var(--hover-bg, #2a2a2a); }
.btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }

.refresh-time { font-size: 13px; color: var(--secondary-text, #aaa); }

.loading-state {
  padding: 48px;
  text-align: center;
  font-size: 16px;
  color: var(--secondary-text, #aaa);
}
</style>
