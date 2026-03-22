<template>
  <div class="cp-wrap">

    <transition name="toast">
      <div v-if="toast.visible" :class="['toast', toast.type]">{{ toast.message }}</div>
    </transition>

    <!-- Успех -->
    <div v-if="done" class="success-card">
      <div class="success-icon">✅</div>
      <h3>Пароль изменён!</h3>
      <p>Все остальные сессии завершены. На других устройствах нужно войти заново.</p>
      <button class="btn-primary" @click="resetForm">Понятно</button>
    </div>

    <template v-else>
      <div class="sg">
        <h3>🔑 Текущий пароль</h3>
        <div class="pw-field">
          <input
            v-model="form.old_password"
            :type="show.old ? 'text' : 'password'"
            placeholder="Введите текущий пароль"
            class="input"
            :class="{ error: errors.old_password }"
            @input="clearError('old_password')"
          />
          <button class="eye-btn" @click="show.old = !show.old" type="button">
            {{ show.old ? '🙈' : '👁' }}
          </button>
        </div>
        <span v-if="errors.old_password" class="err">{{ errors.old_password }}</span>
      </div>

      <div class="sg">
        <h3>🔒 Новый пароль</h3>

        <div class="pw-field">
          <input
            v-model="form.new_password"
            :type="show.new ? 'text' : 'password'"
            placeholder="Новый пароль (мин. 8 символов)"
            class="input"
            :class="{ error: errors.new_password }"
            @input="clearError('new_password')"
          />
          <button class="eye-btn" @click="show.new = !show.new" type="button">
            {{ show.new ? '🙈' : '👁' }}
          </button>
        </div>
        <span v-if="errors.new_password" class="err">{{ errors.new_password }}</span>

        <!-- Индикатор надёжности -->
        <div class="strength-bar-wrap" v-if="form.new_password">
          <div class="strength-bar">
            <div class="strength-fill" :class="strengthClass" :style="{ width: strengthPct + '%' }"></div>
          </div>
          <span class="strength-label" :class="strengthClass">{{ strengthLabel }}</span>
        </div>

        <!-- Чеклист требований -->
        <ul class="checklist" v-if="form.new_password">
          <li :class="{ ok: r.hasMinLength }">Минимум 8 символов</li>
          <li :class="{ ok: r.hasLetter }">Буква</li>
          <li :class="{ ok: r.hasDigit }">Цифра</li>
        </ul>
      </div>

      <div class="sg">
        <h3>🔁 Подтверждение</h3>
        <div class="pw-field">
          <input
            v-model="form.confirm_password"
            :type="show.confirm ? 'text' : 'password'"
            placeholder="Повторите новый пароль"
            class="input"
            :class="{ error: errors.confirm_password || (form.confirm_password && !passwordsMatch) }"
            @input="clearError('confirm_password')"
          />
          <button class="eye-btn" @click="show.confirm = !show.confirm" type="button">
            {{ show.confirm ? '🙈' : '👁' }}
          </button>
        </div>
        <span v-if="form.confirm_password && !passwordsMatch" class="err">Пароли не совпадают</span>
        <span v-else-if="errors.confirm_password" class="err">{{ errors.confirm_password }}</span>
      </div>

      <div class="actions">
        <button class="btn-save" @click="submit" :disabled="!canSubmit || saving">
          {{ saving ? '⏳ Сохранение...' : '💾 Изменить пароль' }}
        </button>
        <button class="btn-reset" @click="resetForm" :disabled="saving">↺ Очистить</button>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

const form = ref({ old_password: '', new_password: '', confirm_password: '' })
const show = ref({ old: false, new: false, confirm: false })
const errors = ref<Record<string, string>>({})
const saving = ref(false)
const done   = ref(false)

const toast = ref({ visible: false, message: '', type: 'success' })
let toastTimer: ReturnType<typeof setTimeout> | null = null
const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { visible: true, message: msg, type }
  toastTimer  = setTimeout(() => (toast.value.visible = false), 4000)
}

// ── Валидация нового пароля ──────────────────────────────────────
const r = computed(() => ({
  hasMinLength: form.value.new_password.length >= 8,
  hasLetter:    /[a-zA-Zа-яА-Я]/.test(form.value.new_password),
  hasDigit:     /\d/.test(form.value.new_password),
}))

const strengthScore = computed(() => Object.values(r.value).filter(Boolean).length)
const strengthPct   = computed(() => (strengthScore.value / 3) * 100)
const strengthClass = computed(() => ['weak', 'medium', 'strong'][strengthScore.value - 1] || 'weak')
const strengthLabel = computed(() => ['Слабый', 'Средний', 'Надёжный'][strengthScore.value - 1] || '')

const passwordsMatch = computed(() =>
  form.value.new_password === form.value.confirm_password && form.value.confirm_password.length > 0
)

const canSubmit = computed(() =>
  form.value.old_password.length > 0 &&
  r.value.hasMinLength &&
  r.value.hasLetter &&
  r.value.hasDigit &&
  passwordsMatch.value
)

const clearError = (field: string) => { delete errors.value[field] }

const submit = async () => {
  if (!canSubmit.value || saving.value) return
  errors.value = {}
  saving.value = true
  try {
    await apiClient.post('/users/change-password/', {
      old_password:     form.value.old_password,
      new_password:     form.value.new_password,
      confirm_password: form.value.confirm_password,
    })
    done.value = true
    showToast('Пароль успешно изменён ✓')
  } catch (err: any) {
    const detail = err?.response?.data
    if (detail && typeof detail === 'object') {
      for (const [k, v] of Object.entries(detail)) {
        errors.value[k] = Array.isArray(v) ? v[0] : String(v)
      }
      // Обобщённые ключи
      if (detail.old_password) errors.value.old_password = Array.isArray(detail.old_password) ? detail.old_password[0] : String(detail.old_password)
      if (detail.non_field_errors) showToast(Array.isArray(detail.non_field_errors) ? detail.non_field_errors[0] : String(detail.non_field_errors), 'error')
      else showToast('Проверьте введённые данные', 'error')
    } else {
      showToast('Ошибка при смене пароля', 'error')
    }
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  form.value   = { old_password: '', new_password: '', confirm_password: '' }
  errors.value = {}
  done.value   = false
}
</script>

<style scoped>
.cp-wrap { display: flex; flex-direction: column; gap: 0; }

.toast {
  position: fixed; top: 24px; right: 24px; z-index: 9999;
  padding: 11px 18px; border-radius: 10px; font-size: 14px; font-weight: 500;
  box-shadow: 0 4px 20px rgba(0,0,0,.3); pointer-events: none;
}
.toast.success { background: #22c55e; color: #fff; }
.toast.error   { background: #ef4444; color: #fff; }
.toast-enter-active, .toast-leave-active { transition: all .25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(-10px); }

.success-card {
  text-align: center; padding: 48px 24px;
}
.success-icon { font-size: 56px; margin-bottom: 16px; }
.success-card h3 { margin: 0 0 10px; font-size: 20px; }
.success-card p { color: var(--secondary-text); margin: 0 0 24px; line-height: 1.5; }

.sg {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}
.sg h3 { margin: 0 0 14px; font-size: 15px; font-weight: 600; }

.pw-field { position: relative; }
.input {
  width: 100%; box-sizing: border-box;
  padding: 10px 44px 10px 13px;
  border: 1px solid var(--border-color); border-radius: 8px;
  background: var(--card-bg); color: var(--text-color); font-size: 14px;
  transition: border-color .15s;
}
.input:focus { outline: none; border-color: var(--primary-color); }
.input.error  { border-color: #ef4444; }

.eye-btn {
  position: absolute; right: 10px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none; cursor: pointer;
  font-size: 17px; padding: 2px;
}

.err { font-size: 12px; color: #ef4444; display: block; margin-top: 5px; }

/* Strength */
.strength-bar-wrap { display: flex; align-items: center; gap: 10px; margin: 10px 0 6px; }
.strength-bar { flex: 1; height: 4px; background: var(--border-color); border-radius: 2px; overflow: hidden; }
.strength-fill { height: 100%; border-radius: 2px; transition: width .3s, background .3s; }
.strength-fill.weak   { background: #ef4444; }
.strength-fill.medium { background: #f59e0b; }
.strength-fill.strong { background: #22c55e; }
.strength-label { font-size: 12px; font-weight: 600; white-space: nowrap; }
.strength-label.weak   { color: #ef4444; }
.strength-label.medium { color: #f59e0b; }
.strength-label.strong { color: #22c55e; }

/* Checklist */
.checklist { margin: 8px 0 0 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 4px; }
.checklist li { font-size: 13px; color: var(--secondary-text); padding-left: 18px; position: relative; }
.checklist li::before { content: '✗'; position: absolute; left: 0; color: #ef4444; }
.checklist li.ok { color: #22c55e; }
.checklist li.ok::before { content: '✓'; color: #22c55e; }

/* Buttons */
.actions {
  padding: 20px 24px; display: flex; gap: 12px;
  border-top: 1px solid var(--border-color);
}
.btn-primary, .btn-save {
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
