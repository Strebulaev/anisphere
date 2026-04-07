<template>
  <div class="account-settings">

    <!-- Уведомления -->
    <transition name="toast">
      <div v-if="toast.visible" :class="['toast', toast.type]">
        {{ toast.message }}
      </div>
    </transition>

    <!-- Аватар -->
    <div class="settings-group">
      <h3><SakuraIcon name="camera" /> Аватар</h3>
      <div class="avatar-row">
        <div class="avatar-preview">
          <img v-if="form.avatar_url" :src="form.avatar_url" alt="Аватар" />
          <div v-else class="avatar-placeholder">{{ userInitials }}</div>
        </div>
        <div class="avatar-actions">
          <input ref="avatarInput" type="file" accept="image/jpeg,image/png,image/webp"
                 class="hidden-input" @change="handleAvatarUpload" />
          <button class="btn-primary" @click="avatarInput?.click()" :disabled="saving.avatar">
            {{ saving.avatar ? 'Загрузка...' : '<SakuraIcon name="folder" /> Загрузить фото' }}
          </button>
          <button v-if="form.avatar_url" class="btn-danger" @click="removeAvatar" :disabled="saving.avatar">
            <SakuraIcon name="trash" /> Удалить
          </button>
        </div>
        <p class="hint">JPEG / PNG / WebP, до 5 МБ</p>
      </div>
    </div>

    <!-- Имя -->
    <div class="settings-group">
      <h3><SakuraIcon name="user" /> Имя</h3>
      <div class="field">
        <label>Отображаемое имя</label>
        <input v-model="form.display_name" type="text" placeholder="Твоё имя"
               class="input" :class="{ error: errors.display_name }"
               maxlength="50" @input="clearError('display_name')" />
        <span v-if="errors.display_name" class="error-msg">{{ errors.display_name }}</span>
      </div>
    </div>

    <!-- О себе -->
    <div class="settings-group">
      <h3><SakuraIcon name="file-text" /> О себе</h3>
      <textarea v-model="form.bio" class="textarea" rows="4" maxlength="500"
                placeholder="Расскажи о себе..."></textarea>
      <div class="char-count">{{ form.bio?.length || 0 }} / 500</div>
    </div>

    <!-- Социальные сети -->
    <div class="settings-group">
      <h3><SakuraIcon name="circle" /> Социальные сети</h3>
      <div class="social-list">
        <div v-for="(link, idx) in form.social_links" :key="idx" class="social-item">
          <select v-model="link.platform" class="select">
            <option value="telegram">Telegram</option>
            <option value="vk">VK</option>
            <option value="youtube">YouTube</option>
            <option value="twitter">X (Twitter)</option>
            <option value="instagram">Instagram</option>
            <option value="discord">Discord</option>
            <option value="other">Другое</option>
          </select>
          <input v-model="link.url" type="url" placeholder="https://..." class="input" />
          <button class="btn-icon-danger" @click="removeSocialLink(idx)" title="Удалить">✕</button>
        </div>
        <button class="btn-dashed" @click="addSocialLink"><SakuraIcon name="plus" /> Добавить ссылку</button>
      </div>
    </div>

    <!-- Дата рождения и Статус - ЗАКОММЕНТИРОВАНЫ
    <div class="settings-group locked">
      <h3>
        <span class="lock-icon"><i class="fas fa-lock"></i></span>
        🎂 Дата рождения
      </h3>
      <input v-model="form.birth_date" type="date" class="input date-input" disabled />
      <span class="hint">Используется для возрастных ограничений контента</span>
    </div>

    <div class="settings-group locked">
      <h3>
        <span class="lock-icon"><i class="fas fa-lock"></i></span>
        <SakuraIcon name="circle" /> Статус
      </h3>
      <div class="status-row">
        <label v-for="opt in statusOptions" :key="opt.value"
               :class="['status-chip', { active: form.status === opt.value }]">
          <input type="radio" v-model="form.status" :value="opt.value" hidden disabled />
          <span :class="['dot', opt.value]"></span>
          {{ opt.label }}
        </label>
      </div>
    </div> -->

    <!-- Кнопки сохранения -->
    <div class="actions">
      <button class="btn-save" @click="saveProfile"
              :disabled="!hasChanges || saving.profile || !isValid">
        <span v-if="saving.profile"><SakuraIcon name="hourglass" /> Сохранение...</span>
        <span v-else><SakuraIcon name="save" /> Сохранить изменения</span>
      </button>
      <button class="btn-reset" @click="resetForm" :disabled="!hasChanges">
        ↺ Отменить
      </button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import apiClient from '@/api/client'
import { useAuthStore } from '@/stores/auth'

interface SocialLink { platform: string; url: string }

interface ProfileForm {
  avatar_url: string
  display_name: string
  nickname: string
  bio: string
  birth_date: string
  social_links: SocialLink[]
  status: string
}

const authStore  = useAuthStore()
const avatarInput = ref<HTMLInputElement | null>(null)

const form = ref<ProfileForm>({
  avatar_url:   '',
  display_name: '',
  nickname:     '',
  bio:          '',
  birth_date:   '',
  social_links: [],
  status:       'online',
})

const original     = ref<string>('')   // JSON-снапшот для сравнения
const errors       = ref<Record<string, string>>({})
const saving       = ref({ profile: false, avatar: false })
const nicknameAvailable = ref<boolean | null>(null)
let   nickCheckTimer: ReturnType<typeof setTimeout> | null = null

const toast = ref({ visible: false, message: '', type: 'success' })

const statusOptions = [
  { value: 'online',    label: 'Онлайн'    },
  { value: 'away',      label: 'Отошёл'    },
  { value: 'invisible', label: 'Невидимка' },
]

// ── Вычисляемые ─────────────────────────────────────────────────
const hasChanges = computed(() => JSON.stringify(form.value) !== original.value)

const isValid = computed(() => Object.keys(errors.value).length === 0)

const userInitials = computed(() => {
  const name = form.value.display_name || form.value.nickname || ''
  return name.slice(0, 2).toUpperCase() || '?'
})

// ── Загрузка данных ──────────────────────────────────────────────
const loadProfile = async () => {
  try {
    const { data } = await apiClient.get('/users/me/')
    applyToForm(data)
  } catch {
    showToast('Не удалось загрузить профиль', 'error')
  }
}

const applyToForm = (data: any) => {
  form.value = {
    avatar_url:   data.avatar_url || data.avatar || '',
    display_name: data.display_name || '',
    nickname:     data.nickname     || '',
    bio:          data.bio          || '',
    birth_date:   data.birth_date   || '',
    social_links: Array.isArray(data.social_links) ? data.social_links : [],
    status:       data.status       || 'online',
  }
  original.value = JSON.stringify(form.value)
}

// ── Валидация никнейма ───────────────────────────────────────────
const onNicknameInput = () => {
  clearError('nickname')
  nicknameAvailable.value = null

  const nick = form.value.nickname
  if (!nick) return

  if (!/^[a-zA-Z0-9_-]+$/.test(nick)) {
    errors.value.nickname = 'Только латиница, цифры, _ и -'
    return
  }
  if (nick.length < 3) {
    errors.value.nickname = 'Минимум 3 символа'
    return
  }

  if (nickCheckTimer) clearTimeout(nickCheckTimer)
  nickCheckTimer = setTimeout(async () => {
    try {
      const { data } = await apiClient.get('/users/nickname/check/', { params: { nickname: nick } })
      nicknameAvailable.value = data.available !== false
      if (!nicknameAvailable.value) errors.value.nickname = 'Этот nickname уже занят'
    } catch {
      // молча игнорируем
    }
  }, 500)
}

const clearError = (field: string) => { delete errors.value[field] }

// ── Аватар ───────────────────────────────────────────────────────
const handleAvatarUpload = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return

  if (file.size > 5 * 1024 * 1024) { showToast('Файл больше 5 МБ', 'error'); return }
  if (!file.type.match(/image\/(jpeg|png|webp)/)) { showToast('Только JPEG, PNG или WebP', 'error'); return }

  saving.value.avatar = true
  try {
    const fd = new FormData()
    fd.append('avatar', file)
    const { data } = await apiClient.post('/users/avatar/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    form.value.avatar_url = data.avatar_url || data.avatar || ''
    original.value = JSON.stringify(form.value)   // аватар сохранён — сбрасываем dirty
    await authStore.fetchUser()
    showToast('Аватар обновлён ✓')
  } catch {
    showToast('Ошибка загрузки аватара', 'error')
  } finally {
    saving.value.avatar = false
    if (avatarInput.value) avatarInput.value.value = ''
  }
}

const removeAvatar = async () => {
  saving.value.avatar = true
  try {
    await apiClient.delete('/users/avatar/')
    form.value.avatar_url = ''
    original.value = JSON.stringify(form.value)
    await authStore.fetchUser()
    showToast('Аватар удалён')
  } catch {
    showToast('Ошибка удаления аватара', 'error')
  } finally {
    saving.value.avatar = false
  }
}

// ── Соцсети ──────────────────────────────────────────────────────
const addSocialLink    = () => form.value.social_links.push({ platform: 'telegram', url: '' })
const removeSocialLink = (idx: number) => form.value.social_links.splice(idx, 1)

// ── Сохранение профиля ────────────────────────────────────────────
const saveProfile = async () => {
  if (!hasChanges.value || saving.value.profile) return

  // Финальная валидация
  errors.value = {}
  const nick = form.value.nickname
  if (nick && nick.length < 3) { errors.value.nickname = 'Минимум 3 символа'; return }
  if (nick && !/^[a-zA-Z0-9_-]+$/.test(nick)) { errors.value.nickname = 'Только латиница, цифры, _ и -'; return }
  const name = form.value.display_name
  if (name && name.length > 50) { errors.value.display_name = 'Максимум 50 символов'; return }

  saving.value.profile = true
  try {
    const payload = {
      display_name: form.value.display_name,
      nickname:     form.value.nickname,
      bio:          form.value.bio,
      birth_date:   form.value.birth_date   || null,
      social_links: form.value.social_links,
      status:       form.value.status,
    }
    const { data } = await apiClient.put('/users/me/', payload)
    applyToForm(data)
    await authStore.fetchUser()
    showToast('Профиль сохранён ✓')
  } catch (err: any) {
    const detail = err?.response?.data
    if (detail && typeof detail === 'object') {
      // Серверные ошибки валидации
      for (const [k, v] of Object.entries(detail)) {
        errors.value[k] = Array.isArray(v) ? v[0] : String(v)
      }
      showToast('Проверьте поля формы', 'error')
    } else {
      showToast('Ошибка сохранения профиля', 'error')
    }
  } finally {
    saving.value.profile = false
  }
}

const resetForm = () => {
  form.value   = JSON.parse(original.value)
  errors.value = {}
  nicknameAvailable.value = null
}

// ── Toast ────────────────────────────────────────────────────────
let toastTimer: ReturnType<typeof setTimeout> | null = null
const showToast = (message: string, type: 'success' | 'error' = 'success') => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { visible: true, message, type }
  toastTimer  = setTimeout(() => (toast.value.visible = false), 3000)
}

onMounted(loadProfile)
</script>

<style scoped>
.account-settings { display: flex; flex-direction: column; gap: 0; }

/* Toast */
.toast {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  padding: 12px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 20px rgba(0,0,0,.3);
  pointer-events: none;
}
.toast.success { background: #22c55e; color: #fff; }
.toast.error   { background: #ef4444; color: #fff; }
.toast-enter-active, .toast-leave-active { transition: all .25s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(-12px); }

/* Groups */
.settings-group {
  padding: 22px 24px;
  border-bottom: 1px solid var(--border-color);
}
.settings-group:last-of-type { border-bottom: none; }
.settings-group h3 { margin: 0 0 16px; font-size: 15px; font-weight: 600; }

.settings-group.locked {
  opacity: 0.5;
  pointer-events: none;
}

.settings-group.locked .lock-icon {
  margin-right: 8px;
  color: var(--secondary-text);
}

.settings-group.locked .input,
.settings-group.locked .select,
.settings-group.locked .textarea {
  background: var(--hover-bg);
  cursor: not-allowed;
}

.settings-group.locked .btn-dashed,
.settings-group.locked .btn-icon-danger {
  opacity: 0.5;
  cursor: not-allowed;
}

.settings-group.locked .status-chip {
  cursor: not-allowed;
  opacity: 0.6;
}

/* Avatar */
.avatar-row { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.avatar-preview {
  width: 88px; height: 88px; border-radius: 50%;
  overflow: hidden; background: var(--card-bg);
  border: 2px solid var(--border-color); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.avatar-preview img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { font-size: 28px; font-weight: 700; color: var(--secondary-text); }
.avatar-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.hidden-input { display: none; }

/* Fields */
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 600px) { .field-row { grid-template-columns: 1fr; } }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 13px; font-weight: 500; color: var(--secondary-text); }

.input {
  padding: 9px 13px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 14px;
  transition: border-color .15s;
}
.input:focus { outline: none; border-color: var(--primary-color); }
.input.error { border-color: #ef4444; }

.input-with-icon { position: relative; }
.prefix {
  position: absolute; left: 10px; top: 50%;
  transform: translateY(-50%);
  color: var(--secondary-text); font-size: 14px; pointer-events: none;
}
.with-prefix { padding-left: 24px; }

.textarea {
  padding: 9px 13px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 14px;
  resize: vertical; min-height: 90px;
  width: 100%; box-sizing: border-box;
}
.textarea:focus { outline: none; border-color: var(--primary-color); }

.date-input { max-width: 200px; }

.char-count { text-align: right; font-size: 12px; color: var(--secondary-text); margin-top: 4px; }
.error-msg { font-size: 12px; color: #ef4444; }
.ok-msg    { font-size: 12px; color: #22c55e; }
.hint      { font-size: 12px; color: var(--secondary-text); margin-top: 2px; }

/* Social links */
.social-list { display: flex; flex-direction: column; gap: 8px; }
.social-item { display: flex; gap: 8px; align-items: center; }
.select {
  padding: 8px 10px; border: 1px solid var(--border-color);
  border-radius: 8px; background: var(--card-bg); color: var(--text-color);
  font-size: 14px; min-width: 130px;
}
.social-item .input { flex: 1; }

/* Status */
.status-row { display: flex; gap: 10px; flex-wrap: wrap; }
.status-chip {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; border: 1px solid var(--border-color);
  border-radius: 20px; cursor: pointer;
  font-size: 14px; transition: all .15s;
  user-select: none;
}
.status-chip:hover { background: var(--hover-bg); }
.status-chip.active { border-color: var(--primary-color); background: rgba(0,132,255,.1); }
.dot { width: 9px; height: 9px; border-radius: 50%; }
.dot.online    { background: #22c55e; }
.dot.away      { background: #f59e0b; }
.dot.invisible { background: #6b7280; }

/* Buttons */
.btn-primary, .btn-danger, .btn-save, .btn-reset, .btn-dashed, .btn-icon-danger {
  padding: 8px 16px; border-radius: 8px; cursor: pointer;
  font-size: 14px; font-weight: 500; transition: all .15s;
  border: none;
}
.btn-primary { background: var(--primary-color); color: #fff; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-danger  { background: rgba(239,68,68,.1); color: #ef4444; border: 1px solid #ef4444; }
.btn-icon-danger { background: none; color: #ef4444; padding: 6px 10px; font-size: 16px; }
.btn-dashed  {
  background: none; border: 1px dashed var(--border-color);
  color: var(--text-color); width: 100%; padding: 9px;
}
.btn-dashed:hover { border-color: var(--primary-color); color: var(--primary-color); }

.actions { padding: 20px 24px; display: flex; gap: 12px; border-top: 1px solid var(--border-color); }
.btn-save {
  background: var(--primary-color); color: #fff;
  padding: 10px 24px; font-size: 15px;
}
.btn-save:disabled { opacity: .4; cursor: not-allowed; }
.btn-reset {
  background: var(--hover-bg); color: var(--text-color);
  border: 1px solid var(--border-color);
}
.btn-reset:disabled { opacity: .4; cursor: not-allowed; }
</style>
