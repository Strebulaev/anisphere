<template>
  <div class="settings-section">
    <h2>Экспорт данных</h2>

    <div class="settings-group info-group">
      <h3>📤 Экспорт всех данных</h3>
      
      <div class="info-content">
        <p>
          Вы можете экспортировать все свои данные в машиночитаемом формате. 
          Это позволяет создать резервную копию или перенести данные в другой сервис.
        </p>
        
        <div class="info-points">
          <div class="info-point">
            <span class="point-icon">⏱️</span>
            <span>Процесс может занять до 24 часов</span>
          </div>
          <div class="info-point">
            <span class="point-icon">📧</span>
            <span>Ссылка будет отправлена на ваш email</span>
          </div>
          <div class="info-point">
            <span class="point-icon">🔗</span>
            <span>Ссылка действительна 7 дней</span>
          </div>
          <div class="info-point">
            <span class="point-icon">📦</span>
            <span>Данные будут упакованы в архив</span>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>☑️ Выберите, что экспортировать</h3>
      
      <div class="export-items">
        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.profile" />
          <span class="export-icon">👤</span>
          <span class="export-info">
            <span class="export-name">Профиль</span>
            <span class="export-desc">Ник, био, аватар</span>
          </span>
        </label>

        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.playlists" />
          <span class="export-icon">📋</span>
          <span class="export-info">
            <span class="export-name">Плейлисты</span>
            <span class="export-desc">Все плейлисты и их содержимое</span>
          </span>
        </label>

        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.shorts" />
          <span class="export-icon">🎬</span>
          <span class="export-info">
            <span class="export-name">Shorts</span>
            <span class="export-desc">Ссылки на ваши видео</span>
          </span>
        </label>

        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.comments" />
          <span class="export-icon">💬</span>
          <span class="export-info">
            <span class="export-name">Комментарии</span>
            <span class="export-desc">Все ваши комментарии</span>
          </span>
        </label>

        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.reviews" />
          <span class="export-icon">⭐</span>
          <span class="export-info">
            <span class="export-name">Отзывы</span>
            <span class="export-desc">Отзывы на аниме</span>
          </span>
        </label>

        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.messages" />
          <span class="export-icon">📩</span>
          <span class="export-info">
            <span class="export-name">Сообщения</span>
            <span class="export-desc">Личные и групповые чаты</span>
          </span>
        </label>

        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.history" />
          <span class="export-icon">📺</span>
          <span class="export-info">
            <span class="export-name">История просмотров</span>
            <span class="export-desc">Что вы смотрели</span>
          </span>
        </label>

        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.favorites" />
          <span class="export-icon">❤️</span>
          <span class="export-info">
            <span class="export-name">Избранное</span>
            <span class="export-desc">Любимые аниме и моменты</span>
          </span>
        </label>

        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.settings" />
          <span class="export-icon">⚙️</span>
          <span class="export-info">
            <span class="export-name">Настройки</span>
            <span class="export-desc">Все ваши настройки</span>
          </span>
        </label>

        <label class="export-item">
          <input type="checkbox" v-model="exportOptions.activity" />
          <span class="export-icon">📊</span>
          <span class="export-info">
            <span class="export-name">Статистика активности</span>
            <span class="export-desc">Лайки, просмотры, подписчики</span>
          </span>
        </label>
      </div>

      <div class="select-all-section">
        <label class="select-all-label">
          <input type="checkbox" v-model="selectAll" @change="toggleSelectAll" />
          <span>Выбрать всё</span>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>📁 Формат экспорта</h3>
      
      <div class="format-options">
        <label class="format-option" :class="{ active: exportFormat === 'json' }">
          <input type="radio" v-model="exportFormat" value="json" />
          <div class="format-info">
            <span class="format-name">JSON</span>
            <span class="format-desc">Машиночитаемый формат</span>
            <span class="format-badge">Рекомендуется</span>
          </div>
        </label>

        <label class="format-option" :class="{ active: exportFormat === 'csv' }">
          <input type="radio" v-model="exportFormat" value="csv" />
          <div class="format-info">
            <span class="format-name">CSV</span>
            <span class="format-desc">Для Excel и таблиц</span>
          </div>
        </label>

        <label class="format-option" :class="{ active: exportFormat === 'html' }">
          <input type="radio" v-model="exportFormat" value="html" />
          <div class="format-info">
            <span class="format-name">HTML</span>
            <span class="format-desc">Для просмотра в браузере</span>
          </div>
        </label>
      </div>
    </div>

    <div class="settings-group">
      <h3>📊 Оценка размера</h3>
      
      <div class="size-estimate">
        <div class="estimate-chart">
          <div class="chart-bar">
            <div
              class="chart-fill"
              :style="{ width: estimatePercent + '%' }"
            ></div>
          </div>
        </div>
        
        <div class="estimate-details">
          <div class="estimate-total">
            <span class="estimate-label">Предполагаемый размер:</span>
            <span class="estimate-value">{{ estimatedSize }}</span>
          </div>
          
          <div class="estimate-breakdown">
            <div class="breakdown-item">
              <span class="breakdown-label">Текстовые данные:</span>
              <span class="breakdown-value">~{{ textSize }}</span>
            </div>
            <div class="breakdown-item">
              <span class="breakdown-label">Медиа файлы:</span>
              <span class="breakdown-value">~{{ mediaSize }}</span>
            </div>
            <div class="breakdown-item">
              <span class="breakdown-label">Архивирование:</span>
              <span class="breakdown-value">-{{ compressionSize }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>📋 Предыдущие экспорты</h3>
      
      <div v-if="previousExports.length > 0" class="exports-list">
        <div v-for="exp in previousExports" :key="exp.id" class="export-item">
          <div class="export-info">
            <span class="export-date">{{ formatDate(exp.created_at) }}</span>
            <span class="export-format">{{ exp.format.toUpperCase() }}</span>
            <span class="export-size">{{ exp.size }}</span>
          </div>
          <div class="export-status">
            <span v-if="exp.status === 'ready'" class="status-ready">
              <button @click="downloadExport(exp)" class="download-btn">📥 Скачать</button>
              <span class="expiry">Истекает через {{ getExpiryDays(exp.created_at) }} дней</span>
            </span>
            <span v-else-if="exp.status === 'processing'" class="status-processing">
              🔄 Обработка...
            </span>
            <span v-else class="status-expired">
              ⏰ Истёк
            </span>
          </div>
        </div>
      </div>

      <div v-else class="no-exports">
        <div class="no-exports-icon">📭</div>
        <p>У вас пока нет запросов на экспорт</p>
      </div>
    </div>

    <div class="settings-actions">
      <button
        @click="requestExport"
        :disabled="!canRequestExport || isRequesting"
        class="export-btn"
      >
        {{ isRequesting ? '⏳ Обработка...' : '📨 Запросить экспорт' }}
      </button>
    </div>

    <!-- Export Confirmation Modal -->
    <div v-if="showConfirmModal" class="modal-overlay" @click="showConfirmModal = false">
      <div class="modal" @click.stop>
        <h3>Подтвердить экспорт данных?</h3>
        
        <div class="modal-content">
          <p>Вы собираетесь экспортировать следующие данные:</p>
          
          <div class="modal-export-list">
            <div v-for="(item, key) in exportOptions" :key="key">
              <span v-if="item" class="modal-export-item">✓ {{ getExportItemName(key) }}</span>
            </div>
          </div>

          <div class="modal-format">
            <strong>Формат:</strong> {{ exportFormat.toUpperCase() }}
          </div>

          <div class="modal-warning">
            <strong>⚠️ Важно:</strong>
            <ul>
              <li>Экспортированные данные содержат персональную информацию</li>
              <li>Храните архив в безопасном месте</li>
              <li>Не передавайте его третьим лицам</li>
            </ul>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="showConfirmModal = false" class="cancel-btn">Отмена</button>
          <button @click="confirmExport" class="confirm-btn">Подтвердить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as settingsApi from '@/api/settings'

interface PreviousExport {
  id: number
  created_at: string
  format: string
  size: string
  status: 'ready' | 'processing' | 'expired'
  expires_at: string | null
  download_url: string | null
}

const exportOptions = ref({
  profile: true,
  playlists: true,
  shorts: true,
  comments: true,
  reviews: true,
  messages: false,
  history: true,
  favorites: true,
  settings: true,
  activity: true
})

const exportFormat = ref('json')
const showConfirmModal = ref(false)
const isRequesting = ref(false)

const previousExports = ref<PreviousExport[]>([])

const selectAll = computed(() => {
  return Object.values(exportOptions.value).every(v => v)
})

const canRequestExport = computed(() => {
  return Object.values(exportOptions.value).some(v => v)
})

const estimatedSize = ref('42.5 MB')
const textSize = ref('15.3 MB')
const mediaSize = ref('30.2 MB')
const compressionSize = ref('3.0 MB')
const estimatePercent = ref(85)

const toggleSelectAll = () => {
  const newValue = !selectAll.value
  Object.keys(exportOptions.value).forEach(key => {
    exportOptions.value[key as keyof typeof exportOptions.value] = newValue
  })
}

const getExportItemName = (key: string) => {
  const names: Record<string, string> = {
    profile: 'Профиль',
    playlists: 'Плейлисты',
    shorts: 'Shorts',
    comments: 'Комментарии',
    reviews: 'Отзывы',
    messages: 'Сообщения',
    history: 'История просмотров',
    favorites: 'Избранное',
    settings: 'Настройки',
    activity: 'Статистика активности'
  }
  return names[key] || key
}

const requestExport = () => {
  showConfirmModal.value = true
}

const confirmExport = async () => {
  isRequesting.value = true
  showConfirmModal.value = false

  try {
    const selectedItems = Object.entries(exportOptions.value)
      .filter(([_, value]) => value)
      .map(([key, _]) => key)

    await settingsApi.requestExportData({
      items: selectedItems,
      format: exportFormat.value
    })

    alert('Запрос на экспорт отправлен! Ссылка будет отправлена на ваш email.')
    await fetchExports()
  } catch (error) {
    console.error('Error requesting export:', error)
    alert('Ошибка при запросе экспорта')
  } finally {
    isRequesting.value = false
  }
}

const downloadExport = async (exp: PreviousExport) => {
  try {
    const blob = await settingsApi.downloadExportData(exp.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `anisphere-export-${exp.id}.${exp.format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error('Error downloading export:', error)
    alert('Ошибка при скачивании')
  }
}

const fetchExports = async () => {
  try {
    const data = await settingsApi.getDataExports()
    previousExports.value = data.exports || []
  } catch (error) {
    console.error('Error fetching exports:', error)
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getExpiryDays = (dateString: string) => {
  if (!dateString) return 0
  const created = new Date(dateString)
  const expiry = new Date(created.getTime() + 7 * 24 * 60 * 60 * 1000)
  const now = new Date()
  const diffDays = Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  return Math.max(0, diffDays)
}

onMounted(() => {
  fetchExports()
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

.info-group {
  background: rgba(0, 132, 255, 0.05);
}

.info-content {
  line-height: 1.6;
}

.info-content p {
  margin-bottom: 20px;
}

.info-points {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-point {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.point-icon {
  font-size: 18px;
}

.export-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
}

.export-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.export-item:hover {
  background: var(--hover-bg);
}

.export-item input[type="checkbox"] {
  margin: 0;
}

.export-icon {
  font-size: 24px;
  width: 40px;
  text-align: center;
}

.export-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.export-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.export-desc {
  font-size: 13px;
  color: var(--secondary-text);
}

.select-all-section {
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

.select-all-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
  cursor: pointer;
}

.select-all-label input[type="checkbox"] {
  margin: 0;
}

.format-options {
  display: flex;
  gap: 15px;
}

.format-option {
  flex: 1;
  display: block;
  padding: 20px;
  border: 2px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.format-option:hover {
  background: var(--card-bg);
}

.format-option.active {
  border-color: var(--primary-color);
  background: rgba(0, 132, 255, 0.1);
}

.format-option input[type="radio"] {
  display: none;
}

.format-info {
  text-align: center;
}

.format-name {
  display: block;
  font-weight: 600;
  font-size: 18px;
  margin-bottom: 5px;
}

.format-desc {
  display: block;
  font-size: 13px;
  color: var(--secondary-text);
}

.format-badge {
  display: inline-block;
  margin-top: 8px;
  padding: 2px 8px;
  background: #4CAF50;
  color: white;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.size-estimate {
  padding: 20px;
  background: var(--card-bg);
  border-radius: 6px;
}

.estimate-chart {
  margin-bottom: 20px;
}

.chart-bar {
  height: 20px;
  background: var(--border-color);
  border-radius: 10px;
  overflow: hidden;
}

.chart-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), #4CAF50);
  border-radius: 10px;
  transition: width 0.5s;
}

.estimate-details {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.estimate-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: rgba(0, 132, 255, 0.1);
  border-radius: 6px;
}

.estimate-label {
  font-size: 14px;
  color: var(--secondary-text);
}

.estimate-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-color);
}

.estimate-breakdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.breakdown-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.breakdown-label {
  color: var(--secondary-text);
}

.breakdown-value {
  font-weight: 500;
}

.exports-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.export-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  background: var(--card-bg);
  border-radius: 6px;
}

.export-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.export-date {
  font-weight: 500;
}

.export-format {
  padding: 4px 8px;
  background: var(--hover-bg);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.export-size {
  color: var(--secondary-text);
  font-size: 14px;
}

.export-status {
  text-align: right;
}

.status-ready {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}

.download-btn {
  padding: 6px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.expiry {
  font-size: 12px;
  color: var(--secondary-text);
}

.status-processing {
  color: var(--primary-color);
}

.status-expired {
  color: var(--secondary-text);
}

.no-exports {
  text-align: center;
  padding: 40px 20px;
}

.no-exports-icon {
  font-size: 60px;
  margin-bottom: 15px;
}

.no-exports p {
  color: var(--secondary-text);
  margin: 0;
}

.settings-actions {
  margin-top: 30px;
  text-align: center;
}

.export-btn {
  padding: 14px 28px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 16px;
}

.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  max-width: 500px;
  width: 90%;
  border: 1px solid var(--border-color);
  max-height: 80vh;
  overflow-y: auto;
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 20px;
}

.modal-content {
  margin-bottom: 20px;
}

.modal-content p {
  margin-bottom: 15px;
}

.modal-export-list {
  padding: 15px;
  background: var(--hover-bg);
  border-radius: 6px;
  margin-bottom: 15px;
}

.modal-export-item {
  display: block;
  margin-bottom: 5px;
}

.modal-format {
  padding: 10px 15px;
  background: rgba(0, 132, 255, 0.1);
  border-radius: 6px;
  margin-bottom: 15px;
}

.modal-warning {
  padding: 15px;
  background: rgba(255, 193, 7, 0.1);
  border-left: 4px solid #FFC107;
  border-radius: 4px;
}

.modal-warning ul {
  margin: 10px 0 0 20px;
  padding: 0;
}

.modal-warning li {
  margin-bottom: 5px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 10px;
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
</style>
