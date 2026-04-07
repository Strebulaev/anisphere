<template>
  <div class="notif-settings">

    <transition name="toast">
      <div v-if="toast.visible" :class="['toast', toast.type]">{{ toast.message }}</div>
    </transition>

    <div class="sg">
      <h3><SakuraIcon name="bell" /> Push-уведомления</h3>

      <div class="row toggle-row">
        <span>Push-уведомления</span>
        <label class="switch">
          <input type="checkbox" v-model="form.push_enabled" @change="autoSave" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="row">
        <label>Звук</label>
        <select v-model="form.notification_sound" class="sel" @change="autoSave">
          <option value="default">По умолчанию</option>
          <option value="gentle">Мягкий</option>
          <option value="urgent">Срочный</option>
          <option value="silent">Без звука</option>
        </select>
      </div>

      <div class="row toggle-row">
        <span>Вибрация</span>
        <label class="switch">
          <input type="checkbox" v-model="form.push_vibration" @change="autoSave" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="row toggle-row">
        <span>Показывать текст сообщения</span>
        <label class="switch">
          <input type="checkbox" v-model="form.push_preview" @change="autoSave" />
          <span class="slider"></span>
        </label>
      </div>
    </div>

    <div class="sg">
      <h3><SakuraIcon name="phone" /> Типы уведомлений</h3>

      <div class="row">
        <label>Личные сообщения</label>
        <select v-model="form.message_mode" class="sel" @change="autoSave">
          <option value="all">Все</option>
          <option value="important">Только важные</option>
          <option value="none">Выключено</option>
        </select>
      </div>

      <div class="row">
        <label>Групповые чаты</label>
        <select v-model="form.group_mode" class="sel" @change="autoSave">
          <option value="all">Все</option>
          <option value="mentions">Только упоминания</option>
          <option value="none">Выключено</option>
        </select>
      </div>

      <div class="row">
        <label>Звонки</label>
        <select v-model="form.call_mode" class="sel" @change="autoSave">
          <option value="all">Все</option>
          <option value="none">Выключено</option>
        </select>
      </div>

      <div class="row toggle-row">
        <span>Реакции на сообщения</span>
        <label class="switch">
          <input type="checkbox" v-model="form.reaction_notifications" @change="autoSave" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="row toggle-row">
        <span>Email-уведомления</span>
        <label class="switch">
          <input type="checkbox" v-model="form.email_enabled" @change="autoSave" />
          <span class="slider"></span>
        </label>
      </div>

      <div v-if="form.email_enabled" class="row">
        <label>Частота email</label>
        <select v-model="form.email_frequency" class="sel" @change="autoSave">
          <option value="immediately">Сразу</option>
          <option value="hourly">Раз в час</option>
          <option value="daily">Раз в день</option>
          <option value="weekly">Раз в неделю</option>
        </select>
      </div>
    </div>

    <div class="sg">
      <h3><SakuraIcon name="clock" /> Не беспокоить</h3>

      <div class="row toggle-row">
        <span>Режим «Не беспокоить»</span>
        <label class="switch">
          <input type="checkbox" v-model="form.dnd_enabled" @change="autoSave" />
          <span class="slider"></span>
        </label>
      </div>

      <div v-if="form.dnd_enabled" class="dnd-times">
        <div class="row">
          <label>С</label>
          <input type="time" v-model="form.dnd_start" class="time-in" @change="autoSave" />
        </div>
        <div class="row">
          <label>До</label>
          <input type="time" v-model="form.dnd_end" class="time-in" @change="autoSave" />
        </div>
      </div>
    </div>

    <div class="actions">
      <button class="btn-save" @click="save" :disabled="saving || !dirty">
        {{ saving ? '<SakuraIcon name="hourglass" /> Сохранение...' : '<SakuraIcon name="save" /> Сохранить' }}
      </button>
      <button class="btn-reset" @click="reset" :disabled="!dirty">↺ Отменить</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

interface NotifForm {
  push_enabled: boolean
  notification_sound: string
  push_vibration: boolean
  push_preview: boolean
  message_mode: string
  group_mode: string
  call_mode: string
  reaction_notifications: boolean
  email_enabled: boolean
  email_frequency: string
  dnd_enabled: boolean
  dnd_start: string
  dnd_end: string
}

const defaultForm = (): NotifForm => ({
  push_enabled: true,
  notification_sound: 'default',
  push_vibration: true,
  push_preview: true,
  message_mode: 'all',
  group_mode: 'mentions',
  call_mode: 'all',
  reaction_notifications: false,
  email_enabled: false,
  email_frequency: 'daily',
  dnd_enabled: false,
  dnd_start: '22:00',
  dnd_end: '08:00',
})

const form     = ref<NotifForm>(defaultForm())
const original = ref('')
const saving   = ref(false)
const dirty    = ref(false)
const toast    = ref({ visible: false, message: '', type: 'success' })
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null
let toastTimer:    ReturnType<typeof setTimeout> | null = null

const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { visible: true, message: msg, type }
  toastTimer  = setTimeout(() => (toast.value.visible = false), 3000)
}

const load = async () => {
  try {
    const { data } = await apiClient.get('/users/notification-settings/')
    form.value = {
      push_enabled: data.push_enabled ?? true,
      notification_sound: data.notification_sound ?? 'default',
      push_vibration: data.push_vibration ?? true,
      push_preview: data.push_preview ?? true,
      message_mode: data.message_notifications ? 'all' : 'none',
      group_mode:   data.mention_notifications ? 'mentions' : (data.group_notifications ? 'all' : 'none'),
      call_mode:    data.call_notifications ? 'all' : 'none',
      reaction_notifications: data.reaction_notifications ?? false,
      email_enabled: data.email_enabled ?? false,
      email_frequency: data.email_frequency ?? 'daily',
      dnd_enabled: !!(data.do_not_disturb_start && data.do_not_disturb_end),
      dnd_start: data.do_not_disturb_start ?? '22:00',
      dnd_end:   data.do_not_disturb_end   ?? '08:00',
    }
    original.value = JSON.stringify(form.value)
    dirty.value    = false
  } catch {
    showToast('Не удалось загрузить настройки', 'error')
  }
}

const toPayload = () => ({
  push_enabled:           form.value.push_enabled,
  push_vibration:         form.value.push_vibration,
  push_preview:           form.value.push_preview,
  message_notifications:  form.value.message_mode !== 'none',
  group_notifications:    form.value.group_mode !== 'none',
  mention_notifications:  form.value.group_mode === 'mentions',
  call_notifications:     form.value.call_mode === 'all',
  reaction_notifications: form.value.reaction_notifications,
  email_enabled:          form.value.email_enabled,
  email_frequency:        form.value.email_frequency,
  do_not_disturb_start:   form.value.dnd_enabled ? form.value.dnd_start : null,
  do_not_disturb_end:     form.value.dnd_enabled ? form.value.dnd_end   : null,
})

const save = async () => {
  if (saving.value) return
  saving.value = true
  try {
    await apiClient.put('/users/notification-settings/', toPayload())
    original.value = JSON.stringify(form.value)
    dirty.value    = false
    showToast('Уведомления сохранены ✓')
  } catch {
    showToast('Ошибка сохранения', 'error')
  } finally {
    saving.value = false
  }
}

const autoSave = () => {
  dirty.value = JSON.stringify(form.value) !== original.value
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(save, 1500)
}

const reset = () => {
  form.value = JSON.parse(original.value)
  dirty.value = false
}

onMounted(load)
</script>

<style scoped>
.notif-settings { display: flex; flex-direction: column; gap: 0; }

.toast {
  position: fixed; top: 24px; right: 24px; z-index: 9999;
  padding: 11px 18px; border-radius: 10px; font-size: 14px; font-weight: 500;
  box-shadow: 0 4px 20px rgba(0,0,0,.3); pointer-events: none;
}
.toast.success { background: #22c55e; color: #fff; }
.toast.error   { background: #ef4444; color: #fff; }
.toast-enter-active, .toast-leave-active { transition: all .25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(-10px); }

.sg {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}
.sg h3 { margin: 0 0 16px; font-size: 15px; font-weight: 600; }

.row {
  display: flex; align-items: center;
  justify-content: space-between;
  gap: 12px; padding: 10px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--border-color) 50%, transparent);
}
.row:last-child { border-bottom: none; }
.toggle-row span { font-size: 14px; }

.sel, .time-in {
  padding: 7px 10px; border: 1px solid var(--border-color);
  border-radius: 8px; background: var(--card-bg); color: var(--text-color);
  font-size: 14px; min-width: 140px;
}

/* Toggle switch */
.switch { position: relative; display: inline-block; width: 42px; height: 24px; flex-shrink: 0; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute; cursor: pointer; inset: 0;
  background: var(--border-color); border-radius: 24px; transition: .2s;
}
.slider::before {
  content: ''; position: absolute;
  width: 18px; height: 18px; left: 3px; bottom: 3px;
  background: #fff; border-radius: 50%; transition: .2s;
}
.switch input:checked + .slider { background: var(--primary-color); }
.switch input:checked + .slider::before { transform: translateX(18px); }

.dnd-times { padding-left: 8px; }

.actions {
  padding: 20px 24px;
  display: flex; gap: 12px;
  border-top: 1px solid var(--border-color);
}
.btn-save {
  background: var(--primary-color); color: #fff;
  border: none; padding: 10px 22px; border-radius: 8px;
  font-size: 14px; font-weight: 500; cursor: pointer;
}
.btn-save:disabled { opacity: .4; cursor: not-allowed; }
.btn-reset {
  background: var(--hover-bg); color: var(--text-color);
  border: 1px solid var(--border-color);
  padding: 10px 22px; border-radius: 8px; font-size: 14px; cursor: pointer;
}
.btn-reset:disabled { opacity: .4; cursor: not-allowed; }
</style>
