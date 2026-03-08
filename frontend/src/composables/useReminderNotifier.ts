/**
 * useReminderNotifier — следит за активными напоминаниями и показывает тосты.
 * Подключается один раз в App.vue или MainLayout.vue.
 */
import { watch, onUnmounted } from 'vue'
import { useNotificationStore } from '@/stores/notifications'
import { useToast } from '@/composables/useToast'
import { useRouter } from 'vue-router'

const FIRED_KEY = 'fired_reminders'

function getFired(): Set<number> {
  try {
    const raw = sessionStorage.getItem(FIRED_KEY)
    return raw ? new Set(JSON.parse(raw)) : new Set()
  } catch {
    return new Set()
  }
}

function saveFired(set: Set<number>) {
  sessionStorage.setItem(FIRED_KEY, JSON.stringify([...set]))
}

export function useReminderNotifier() {
  const store  = useNotificationStore()
  const toast  = useToast()
  const router = useRouter()

  let interval: ReturnType<typeof setInterval> | null = null

  const check = () => {
    const fired = getFired()
    const now   = Date.now()

    for (const r of store.reminders) {
      if (!r.is_active || fired.has(r.id)) continue

      const rTime = new Date(
        r.reminder_time.includes('Z') || r.reminder_time.includes('+')
          ? r.reminder_time
          : r.reminder_time.replace(' ', 'T') + 'Z'
      ).getTime()

      // Срабатывает в диапазоне [-30 сек, +5 мин]
      if (rTime >= now - 30_000 && rTime <= now + 300_000) {
        const animeTitle = r.anime_detail?.title_ru || 'Аниме'
        const animeId    = r.anime_detail?.id

        toast.info(`⏰ Пора смотреть ${animeTitle}${r.comment ? ` — ${r.comment}` : ''}`, {
          duration: 8000,
          title: 'Напоминание',
          action: animeId
            ? { label: '▶ Смотреть', handler: () => router.push(`/anime/${animeId}`) }
            : undefined,
        })

        fired.add(r.id)
        saveFired(fired)

        // Деактивируем одноразовые напоминания после срабатывания
        if (!r.repeat_weekly) {
          store.deactivateReminder(r.id).catch(() => {})
        }
      }
    }
  }

  // Проверяем каждые 30 секунд
  interval = setInterval(check, 30_000)
  // И сразу при инициализации
  check()

  onUnmounted(() => {
    if (interval) clearInterval(interval)
  })

  return { check }
}
