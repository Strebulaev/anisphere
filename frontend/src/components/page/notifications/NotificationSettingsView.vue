<template>
  <div class="nsettings-page">
    <div class="nsettings-container">

      <div class="page-header">
        <router-link to="/notifications" class="back-btn">← Уведомления</router-link>
        <h1>⚙️ Настройки уведомлений</h1>
      </div>

      <div v-if="loading" class="state-loading">
        <div class="spinner" />
        <p>Загрузка настроек...</p>
      </div>

      <template v-else>

        <!-- Каналы -->
        <div class="section-card">
          <h2 class="section-title">📡 Каналы</h2>
          <div class="toggle-list">
            <label class="toggle-row">
              <span>Push-уведомления</span>
              <input type="checkbox" v-model="form.push_enabled" class="toggle-input" />
              <span class="toggle-switch"></span>
            </label>
            <label class="toggle-row">
              <span>Email-уведомления</span>
              <input type="checkbox" v-model="form.email_enabled" class="toggle-input" />
              <span class="toggle-switch"></span>
            </label>
            <label class="toggle-row">
              <span>Звук</span>
              <input type="checkbox" v-model="form.sound_enabled" class="toggle-input" />
              <span class="toggle-switch"></span>
            </label>
          </div>
        </div>

        <!-- По типам -->
        <div class="section-card">
          <h2 class="section-title">🔔 По типам</h2>
          <div class="toggle-list">
            <label v-for="t in notifTypes" :key="t.key" class="toggle-row">
              <span>{{ t.icon }} {{ t.label }}</span>
              <input
                type="checkbox"
                :checked="getTypeEnabled(t.key)"
                @change="setTypeEnabled(t.key, ($event.target as HTMLInputElement).checked)"
                class="toggle-input"
                :disabled="t.locked"
              />
              <span class="toggle-switch" :class="{ locked: t.locked }"></span>
            </label>
          </div>
          <p class="hint">🔒 Победа в конкурсе и уведомления безопасности всегда включены</p>
        </div>

        <!-- Режим "Не беспокоить" -->
        <div class="section-card">
          <h2 class="section-title">🔕 Режим "Не беспокоить"</h2>
          <label class="toggle-row">
            <span>Включить по расписанию</span>
            <input type="checkbox" v-model="form.dnd_enabled" class="toggle-input" />
            <span class="toggle-switch"></span>
          </label>
          <div v-if="form.dnd_enabled" class="dnd-times">
            <label class="time-field">
              <span>С</span>
              <input type="time" v-model="form.dnd_start" class="time-input" />
            </label>
            <label class="time-field">
              <span>До</span>
              <input type="time" v-model="form.dnd_end" class="time-input" />
            </label>
          </div>
        </div>

        <!-- Автоочистка -->
        <div class="section-card">
          <h2 class="section-title">🧹 Автоматическая очистка</h2>
          <div class="cleanup-row">
            <span>Удалять прочитанные старше</span>
            <select v-model="form.auto_clean_read_days" class="select-input">
              <option :value="7">7 дней</option>
              <option :value="14">14 дней</option>
              <option :value="30">30 дней</option>
              <option :value="60">60 дней</option>
              <option :value="90">90 дней</option>
            </select>
          </div>
          <div class="cleanup-row">
            <span>Удалять непрочитанные старше</span>
            <select v-model="form.auto_clean_unread_days" class="select-input">
              <option :value="30">30 дней</option>
              <option :value="60">60 дней</option>
              <option :value="90">90 дней</option>
              <option :value="180">180 дней</option>
            </select>
          </div>
          <p class="hint">⭐ Важные уведомления не удаляются автоматически</p>
        </div>

        <!-- Кнопки -->
        <div class="actions-row">
          <button class="btn-save" :disabled="saving" @click="saveAll">
            {{ saving ? 'Сохранение...' : '💾 Сохранить' }}
          </button>
          <button class="btn-reset" @click="resetForm">Сбросить</button>
        </div>

        <div v-if="saved" class="save-toast">✅ Настройки сохранены</div>

      </template>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useNotificationStore } from '@/stores/notifications'

const store = useNotificationStore()
const loading = ref(true)
const saving  = ref(false)
const saved   = ref(false)

const form = reactive({
  push_enabled: true,
  email_enabled: true,
  sound_enabled: true,
  dnd_enabled: false,
  dnd_start: '23:00',
  dnd_end: '08:00',
  auto_clean_read_days: 30,
  auto_clean_unread_days: 90,
  type_settings: {} as Record<string, { enabled: boolean }>,
})

const notifTypes = [
  { key: 'like',           icon: '❤️',  label: 'Лайки' },
  { key: 'dislike',        icon: '👎',  label: 'Дизлайки' },
  { key: 'comment',        icon: '💬',  label: 'Комментарии' },
  { key: 'reply',          icon: '↩️',  label: 'Ответы на комментарии' },
  { key: 'mention',        icon: '@',   label: 'Упоминания' },
  { key: 'follow',         icon: '👥',  label: 'Подписки' },
  { key: 'repost',         icon: '🔁',  label: 'Репосты' },
  { key: 'message',        icon: '✉️',  label: 'Личные сообщения' },
  { key: 'group_message',  icon: '👥',  label: 'Сообщения в группах' },
  { key: 'achievement',    icon: '🏆',  label: 'Достижения' },
  { key: 'contest',        icon: '🏅',  label: 'Новые конкурсы' },
  { key: 'contest_vote',   icon: '🗳️', label: 'Начало голосования' },
  { key: 'contest_results',icon: '📊',  label: 'Результаты конкурсов' },
  { key: 'contest_win',    icon: '👑',  label: 'Победа в конкурсе', locked: true },
  { key: 'reminder_episode',icon: '⏰', label: 'Новые серии (напоминание)' },
  { key: 'system',         icon: '⚙️',  label: 'Системные обновления' },
  { key: 'warning',        icon: '⚠️',  label: 'Предупреждения модератора' },
  { key: 'security',       icon: '🔒',  label: 'Безопасность', locked: true },
]

const getTypeEnabled = (key: string) => {
  if (key === 'contest_win' || key === 'security') return true
  return form.type_settings[key]?.enabled ?? true
}

const setTypeEnabled = (key: string, value: boolean) => {
  if (!form.type_settings[key]) form.type_settings[key] = { enabled: true }
  form.type_settings[key].enabled = value
}

const applySettings = () => {
  const s = store.settings
  if (!s) return
  form.push_enabled            = s.push_enabled
  form.email_enabled           = s.email_enabled
  form.sound_enabled           = s.sound_enabled
  form.dnd_enabled             = s.dnd_enabled
  form.dnd_start               = s.dnd_start ?? '23:00'
  form.dnd_end                 = s.dnd_end ?? '08:00'
  form.auto_clean_read_days    = s.auto_clean_read_days
  form.auto_clean_unread_days  = s.auto_clean_unread_days
  form.type_settings           = { ...s.type_settings }
}

const resetForm = () => applySettings()

const saveAll = async () => {
  saving.value = true
  try {
    await store.saveSettings({
      push_enabled:           form.push_enabled,
      email_enabled:          form.email_enabled,
      sound_enabled:          form.sound_enabled,
      dnd_enabled:            form.dnd_enabled,
      dnd_start:              form.dnd_enabled ? form.dnd_start : null,
      dnd_end:                form.dnd_enabled ? form.dnd_end : null,
      auto_clean_read_days:   form.auto_clean_read_days,
      auto_clean_unread_days: form.auto_clean_unread_days,
      type_settings:          form.type_settings,
    })
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await store.fetchSettings()
  applySettings()
  loading.value = false
})
</script>

<style scoped>
.nsettings-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
  color: #fff;
  padding: 2rem 1.5rem;
}
.nsettings-container {
  max-width: 640px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.page-header { display: flex; flex-direction: column; gap: .4rem; }
.back-btn { color: #3b82f6; text-decoration: none; font-size: .875rem; }
.back-btn:hover { text-decoration: underline; }
.page-header h1 { margin: 0; font-size: 1.6rem; font-weight: 800; }

/* State */
.state-loading {
  display: flex; flex-direction: column; align-items: center; gap: .75rem;
  padding: 4rem 2rem; color: #6b7280; text-align: center;
}
.spinner {
  width: 32px; height: 32px;
  border: 3px solid rgba(255,255,255,0.08);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Section card */
.section-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: .7rem;
}
.section-title {
  margin: 0 0 .25rem;
  font-size: 1rem;
  font-weight: 700;
  color: #e2e8f0;
}
.hint {
  margin: 0;
  font-size: .75rem;
  color: #4b5563;
}

/* Toggle */
.toggle-list { display: flex; flex-direction: column; gap: .55rem; }
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  cursor: pointer;
  font-size: .9rem;
  color: #d1d5db;
  user-select: none;
}
.toggle-input { display: none; }
.toggle-switch {
  width: 44px; height: 24px;
  border-radius: 12px;
  background: rgba(255,255,255,0.1);
  position: relative;
  flex-shrink: 0;
  transition: background .2s;
}
.toggle-switch::after {
  content: '';
  position: absolute;
  top: 3px; left: 3px;
  width: 18px; height: 18px;
  background: #9ca3af;
  border-radius: 50%;
  transition: all .2s;
}
.toggle-input:checked + .toggle-switch {
  background: rgba(59,130,246,0.6);
}
.toggle-input:checked + .toggle-switch::after {
  left: 23px;
  background: #3b82f6;
}
.toggle-switch.locked {
  opacity: .5;
  cursor: not-allowed;
}

/* DND */
.dnd-times {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-top: .25rem;
}
.time-field {
  display: flex;
  align-items: center;
  gap: .5rem;
  font-size: .875rem;
  color: #9ca3af;
}
.time-input {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: .875rem;
  padding: .4rem .75rem;
  outline: none;
}
.time-input:focus { border-color: rgba(59,130,246,0.5); }

/* Cleanup */
.cleanup-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  font-size: .9rem;
  color: #d1d5db;
}
.select-input {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: .875rem;
  padding: .4rem .75rem;
  outline: none;
  cursor: pointer;
}
.select-input:focus { border-color: rgba(59,130,246,0.5); }
.select-input option { background: #1e1e30; }

/* Actions */
.actions-row {
  display: flex;
  gap: .75rem;
  align-items: center;
}
.btn-save {
  padding: .6rem 2rem;
  border-radius: 10px;
  border: 1px solid rgba(59,130,246,0.4);
  background: rgba(59,130,246,0.2);
  color: #3b82f6;
  font-size: .9rem;
  font-weight: 700;
  cursor: pointer;
  transition: all .2s;
}
.btn-save:hover:not(:disabled) { background: rgba(59,130,246,0.35); }
.btn-save:disabled { opacity: .5; cursor: not-allowed; }
.btn-reset {
  padding: .6rem 1.25rem;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.12);
  background: transparent;
  color: #6b7280;
  font-size: .9rem;
  cursor: pointer;
  transition: all .2s;
}
.btn-reset:hover { color: #d1d5db; }

.save-toast {
  text-align: center;
  color: #22c55e;
  font-size: .875rem;
  font-weight: 600;
  animation: fadeIn .3s;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

@media (max-width: 640px) {
  .nsettings-page { padding: 1rem; }
  .page-header h1 { font-size: 1.35rem; }
  .section-card { padding: 1rem; }
  .cleanup-row { flex-direction: column; align-items: flex-start; }
}
</style>
