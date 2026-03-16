<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ isEditing ? 'Редактировать правило' : 'Новое правило анти-спама' }}</h3>
        <button @click="$emit('close')" class="close-btn">
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>

      <form @submit.prevent="saveRule" class="modal-body">
        <!-- Тип правила -->
        <div class="form-group">
          <label>Тип правила</label>
          <select v-model="form.rule_type" :disabled="isEditing" class="input">
            <option v-for="type in ruleTypes" :key="type.value" :value="type.value">
              {{ type.label }}
            </option>
          </select>
          <p class="help-text">{{ getRuleTypeDescription(form.rule_type) }}</p>
        </div>

        <!-- Порог срабатывания -->
        <div v-if="needsThreshold" class="form-group">
          <label>Порог срабатывания</label>
          <input
            v-model.number="form.threshold"
            type="number"
            min="1"
            max="100"
            class="input"
          />
          <p class="help-text">Количество нарушений для срабатывания</p>
        </div>

        <!-- Временное окно -->
        <div v-if="needsTimeWindow" class="form-group">
          <label>Временное окно (секунды)</label>
          <input
            v-model.number="form.time_window"
            type="number"
            min="5"
            max="3600"
            class="input"
          />
          <p class="help-text">Время в секундах для подсчёта нарушений</p>
        </div>

        <!-- Ключевые слова -->
        <div v-if="form.rule_type === 'spam_keywords'" class="form-group">
          <label>Стоп-слова</label>
          <div class="keywords-input">
            <input
              v-model="newKeyword"
              type="text"
              placeholder="Введите слово и нажмите Enter"
              class="input"
              @keydown.enter.prevent="addKeyword"
            />
            <button type="button" @click="addKeyword" class="add-keyword-btn">
              Добавить
            </button>
          </div>
          <div class="keywords-list">
            <span
              v-for="(keyword, index) in form.keywords"
              :key="index"
              class="keyword-chip"
            >
              {{ keyword }}
              <button type="button" @click="removeKeyword(index)" class="remove-keyword">
                <XMarkIcon class="w-3 h-3" />
              </button>
            </span>
          </div>
        </div>

        <!-- Действие -->
        <div class="form-group">
          <label>Действие при нарушении</label>
          <select v-model="form.action" class="input">
            <option v-for="action in actionTypes" :key="action.value" :value="action.value">
              {{ action.label }}
            </option>
          </select>
        </div>

        <!-- Длительность действия -->
        <div v-if="needsDuration" class="form-group">
          <label>Длительность (минуты)</label>
          <input
            v-model.number="form.action_duration"
            type="number"
            min="1"
            max="10080"
            class="input"
            placeholder="Оставьте пустым для постоянного действия"
          />
          <p class="help-text">
            0 = навсегда, 60 = 1 час, 1440 = 1 день, 10080 = 1 неделя
          </p>
        </div>

        <!-- Включено -->
        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input v-model="form.enabled" type="checkbox" />
            <span>Правило активно</span>
          </label>
        </div>
      </form>

      <div class="modal-footer">
        <button type="button" @click="$emit('close')" class="btn btn-secondary">
          Отмена
        </button>
        <button @click="saveRule" class="btn btn-primary" :disabled="saving">
          {{ saving ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'
import chatsApi from '@/api/chats'
import type { AntiSpamRule } from '@/api/chats'

interface Props {
  chatId: number
  rule?: AntiSpamRule | null
}

const props = withDefaults(defineProps<Props>(), {
  rule: null
})

const emit = defineEmits(['close', 'save'])

// State
const saving = ref(false)
const newKeyword = ref('')

const form = ref({
  rule_type: 'flood',
  threshold: 5,
  time_window: 60,
  keywords: [] as string[],
  action: 'delete',
  action_duration: undefined as number | undefined,
  enabled: true
})

// Computed
const isEditing = computed(() => !!props.rule)

const needsThreshold = computed(() => {
  return ['flood', 'media_flood', 'new_members'].includes(form.value.rule_type)
})

const needsTimeWindow = computed(() => {
  return ['flood', 'media_flood'].includes(form.value.rule_type)
})

const needsDuration = computed(() => {
  return ['mute', 'ban'].includes(form.value.action)
})

// Options
const ruleTypes = [
  { value: 'flood', label: 'Флуд (много сообщений)' },
  { value: 'links', label: 'Ссылки в сообщениях' },
  { value: 'spam_keywords', label: 'Стоп-слова' },
  { value: 'caps_lock', label: 'CAPS LOCK' },
  { value: 'new_members', label: 'Ограничение новых участников' },
  { value: 'media_flood', label: 'Медиа-флуд' }
]

const actionTypes = [
  { value: 'delete', label: 'Удалить сообщение' },
  { value: 'warn', label: 'Предупреждение' },
  { value: 'mute', label: 'Заглушить' },
  { value: 'ban', label: 'Забанить' }
]

// Methods
const getRuleTypeDescription = (type: string): string => {
  const descriptions: Record<string, string> = {
    flood: 'Блокирует пользователей, отправляющих слишком много сообщений за короткое время',
    links: 'Автоматически удаляет сообщения с ссылками',
    spam_keywords: 'Блокирует сообщения, содержащие стоп-слова',
    caps_lock: 'Блокирует сообщения, написанные в CAPS LOCK',
    new_members: 'Ограничивает новых участников чата',
    media_flood: 'Блокирует отправку большого количества медиа-файлов'
  }
  return descriptions[type] || ''
}

const addKeyword = () => {
  const keyword = newKeyword.value.trim().toLowerCase()
  if (keyword && !form.value.keywords.includes(keyword)) {
    form.value.keywords.push(keyword)
    newKeyword.value = ''
  }
}

const removeKeyword = (index: number) => {
  form.value.keywords.splice(index, 1)
}

const saveRule = async () => {
  if (saving.value) return

  saving.value = true
  try {
    let response
    if (isEditing.value && props.rule) {
      response = await chatsApi.antiSpam.update(props.rule.id, form.value)
    } else {
      response = await chatsApi.antiSpam.create({
        chat: props.chatId,
        ...form.value
      })
    }

    emit('save', response.data)
  } catch (error) {
    console.error('Error saving anti-spam rule:', error)
  } finally {
    saving.value = false
  }
}

// Initialize
onMounted(() => {
  if (props.rule) {
    form.value = {
      rule_type: props.rule.rule_type,
      threshold: props.rule.threshold,
      time_window: props.rule.time_window,
      keywords: props.rule.keywords || [],
      action: props.rule.action,
      action_duration: props.rule.action_duration ?? undefined,
      enabled: props.rule.enabled
    }
  }
})
</script>

<style scoped>
.modal-overlay {
  @apply fixed inset-0 bg-black/60 flex items-center justify-center z-50;
}

.modal-content {
  @apply bg-gray-800 rounded-xl w-full max-w-lg mx-4 overflow-hidden;
}

.modal-header {
  @apply flex items-center justify-between p-4 border-b border-gray-700;
}

.modal-header h3 {
  @apply text-lg font-semibold text-white;
}

.close-btn {
  @apply p-1 rounded hover:bg-gray-700 transition-colors text-gray-400;
}

.modal-body {
  @apply p-4 space-y-4 max-h-[60vh] overflow-y-auto;
}

.form-group {
  @apply space-y-2;
}

.form-group label {
  @apply block text-sm font-medium text-gray-300;
}

.input {
  @apply w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white;
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500;
}

.input:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.help-text {
  @apply text-xs text-gray-400;
}

.keywords-input {
  @apply flex gap-2;
}

.keywords-input .input {
  @apply flex-1;
}

.add-keyword-btn {
  @apply px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white transition-colors;
  @apply hover:bg-gray-600;
}

.keywords-list {
  @apply flex flex-wrap gap-2 mt-2;
}

.keyword-chip {
  @apply inline-flex items-center gap-1 px-2 py-1 bg-gray-700 rounded text-sm;
}

.remove-keyword {
  @apply p-0.5 rounded hover:bg-gray-600;
}

.checkbox-group {
  @apply py-2;
}

.checkbox-label {
  @apply flex items-center gap-3 cursor-pointer;
}

.checkbox-label input[type="checkbox"] {
  @apply w-5 h-5 rounded;
}

.modal-footer {
  @apply flex justify-end gap-3 p-4 border-t border-gray-700;
}

.btn {
  @apply px-4 py-2 rounded-lg font-medium transition-colors;
}

.btn-secondary {
  @apply bg-gray-700 text-white hover:bg-gray-600;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700;
}

.btn-primary:disabled {
  @apply opacity-50 cursor-not-allowed;
}
</style>
