<template>
  <div class="reports-tab">
    <!-- Filters Bar -->
    <div class="reports-filters">
      <select v-model="filterStatus" @change="loadReports(true)" class="filter-select">
        <option value="">Все статусы</option>
        <option value="pending">На рассмотрении</option>
        <option value="resolved">Рассмотрено</option>
        <option value="rejected">Отклонено</option>
      </select>
      <select v-model="filterType" @change="loadReports(true)" class="filter-select">
        <option value="">Все типы</option>
        <option value="post">Посты</option>
        <option value="comment">Комментарии</option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
    </div>

    <!-- Empty -->
    <div v-else-if="reports.length === 0" class="empty-state">
      <span class="empty-icon"> <SakuraIcon name="check" /> </span>
      <p>Жалоб нет</p>
    </div>

    <!-- List -->
    <div v-else class="reports-list">
      <div
        v-for="report in reports"
        :key="report.id"
        class="report-card"
        :class="report.status"
      >
        <div class="report-header">
          <span class="report-type-badge">
            {{ report.content_type === 'post' ? '<SakuraIcon name="file-text" /> Пост' : '<SakuraIcon name="message" /> Комментарий' }} #{{ report.content_id }}
          </span>
          <span class="status-badge" :class="report.status">
            {{ statusLabels[report.status] }}
          </span>
        </div>

        <div class="report-body">
          <div class="report-info-row">
            <span class="label">Причина:</span>
            <span class="value reason">{{ reasonLabels[report.reason] || report.reason }}</span>
          </div>
          <div class="report-info-row" v-if="(report as any).content?.author">
            <span class="label">Автор контента:</span>
            <span class="value">@{{ (report as any).content.author }}</span>
          </div>
          <div class="report-info-row">
            <span class="label">Жалобщик:</span>
            <span class="value">@{{ (report as any).reporter?.username || report.reporter_username }}</span>
          </div>
          <div class="report-info-row" v-if="report.comment">
            <span class="label">Комментарий:</span>
            <span class="value comment">{{ report.comment }}</span>
          </div>
          <div class="report-info-row">
            <span class="label">Дата:</span>
            <span class="value">{{ formatDate(report.created_at) }}</span>
          </div>
          <div class="report-info-row" v-if="(report as any).content?.text || report.content_preview">
            <span class="label">Контент:</span>
            <span class="value preview">{{ (report as any).content?.text || report.content_preview }}</span>
          </div>
        </div>

        <!-- Actions (only for pending) -->
        <div v-if="report.status === 'pending'" class="report-actions">
          <div class="action-input-wrapper">
            <input
              v-model="actionComments[report.id]"
              placeholder="Комментарий модератора (опционально)"
              class="mod-comment"
            />
          </div>
          <div class="action-buttons">
            <button
              class="btn-action delete"
              @click="resolveReport(report, 'delete_content')"
              :disabled="processingId === report.id"
            >
              <SakuraIcon name="trash" /> Удалить контент
            </button>
            <button
              class="btn-action warn"
              @click="resolveReport(report, 'warn')"
              :disabled="processingId === report.id"
            >
              <SakuraIcon name="warning" />️ Предупреждение
            </button>
            <button
              class="btn-action reject"
              @click="rejectReport(report)"
              :disabled="processingId === report.id"
            >
              ✕ Отклонить
            </button>
          </div>
        </div>

        <!-- Already resolved -->
        <div v-else class="resolved-info">
          <span class="resolved-label">
            {{ report.status === 'resolved' ? '<SakuraIcon name="check" /> Рассмотрено' : '<SakuraIcon name="x" /> Отклонено' }}
            <span v-if="report.moderation_comment"> — {{ report.moderation_comment }}</span>
          </span>
        </div>
      </div>

      <!-- Load More -->
      <button v-if="hasMore" class="btn-load-more" @click="loadReports()" :disabled="loading">
        Загрузить ещё
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { ReportItem } from '@/api/feed'
import { subscriptionsApi } from '@/api/feed'

const reports = ref<ReportItem[]>([])
const loading = ref(false)
const filterStatus = ref('')
const filterType = ref('')
const page = ref(1)
const hasMore = ref(false)
const processingId = ref<number | null>(null)
const actionComments = ref<Record<number, string>>({})

const statusLabels: Record<string, string> = {
  pending: 'На рассмотрении',
  resolved: 'Рассмотрено',
  rejected: 'Отклонено',
}

const reasonLabels: Record<string, string> = {
  spam: 'Спам',
  copyright: 'Авторские права',
  harassment: 'Оскорбления / травля',
  inappropriate: 'Неприемлемый контент',
  other: 'Другое',
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('ru-RU', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
  })
}

const loadReports = async (reset = false) => {
  if (reset) {
    page.value = 1
    reports.value = []
  }
  loading.value = true
  try {
    const { data } = await subscriptionsApi.getReports({
      status: filterStatus.value || undefined,
      content_type: filterType.value || undefined,
      page: page.value,
    })
    if (reset) {
      reports.value = data.results
    } else {
      reports.value.push(...data.results)
    }
    hasMore.value = !!data.next
    page.value++
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const resolveReport = async (report: ReportItem, action: string) => {
  processingId.value = report.id
  try {
    const comment = actionComments.value[report.id]
    const { data } = await subscriptionsApi.resolveReport(report.id, action, comment)
    const idx = reports.value.findIndex(r => r.id === report.id)
    if (idx !== -1) reports.value[idx] = data
  } catch (e) {
    console.error(e)
  } finally {
    processingId.value = null
  }
}

const rejectReport = async (report: ReportItem) => {
  processingId.value = report.id
  try {
    const comment = actionComments.value[report.id]
    const { data } = await subscriptionsApi.rejectReport(report.id, comment)
    const idx = reports.value.findIndex(r => r.id === report.id)
    if (idx !== -1) reports.value[idx] = data
  } catch (e) {
    console.error(e)
  } finally {
    processingId.value = null
  }
}

onMounted(() => loadReports(true))
</script>

<style scoped>
.reports-tab {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.reports-filters {
  display: flex;
  gap: 0.5rem;
}

.filter-select {
  background: #111;
  border: 1px solid #2a2a2a;
  color: #aaa;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.875rem;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #667eea;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 2rem;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 2px solid #333;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 3rem;
  color: #555;
}

.empty-icon {
  font-size: 2.5rem;
}

.reports-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.report-card {
  background: #111;
  border-radius: 12px;
  padding: 1rem;
  border-left: 3px solid #2a2a2a;
}

.report-card.pending {
  border-left-color: #f59e0b;
}

.report-card.resolved {
  border-left-color: #22c55e;
  opacity: 0.8;
}

.report-card.rejected {
  border-left-color: #555;
  opacity: 0.7;
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.report-type-badge {
  color: #aaa;
  font-size: 0.85rem;
}

.status-badge {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.status-badge.resolved {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.status-badge.rejected {
  background: rgba(100, 100, 100, 0.15);
  color: #888;
}

.report-body {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}

.report-info-row {
  display: flex;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.label {
  color: #555;
  flex-shrink: 0;
  min-width: 110px;
}

.value {
  color: #ccc;
}

.value.reason {
  color: #f59e0b;
}

.value.comment {
  color: #999;
  font-style: italic;
}

.value.preview {
  color: #888;
  font-size: 0.8rem;
  max-height: 60px;
  overflow: hidden;
}

.report-actions {
  border-top: 1px solid #1a1a1a;
  padding-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.action-input-wrapper {
  width: 100%;
}

.mod-comment {
  width: 100%;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  color: #aaa;
  font-size: 0.8rem;
  box-sizing: border-box;
}

.mod-comment::placeholder {
  color: #444;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-action {
  padding: 0.5rem 0.875rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  transition: opacity 0.2s;
}

.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-action.delete {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.btn-action.delete:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.25);
}

.btn-action.warn {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.btn-action.warn:hover:not(:disabled) {
  background: rgba(245, 158, 11, 0.25);
}

.btn-action.reject {
  background: rgba(100, 100, 100, 0.15);
  color: #888;
}

.btn-action.reject:hover:not(:disabled) {
  background: rgba(100, 100, 100, 0.25);
}

.resolved-info {
  border-top: 1px solid #1a1a1a;
  padding-top: 0.5rem;
}

.resolved-label {
  color: #555;
  font-size: 0.8rem;
}

.btn-load-more {
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  color: #888;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.btn-load-more:hover:not(:disabled) {
  background: #222;
  color: #aaa;
}
</style>
