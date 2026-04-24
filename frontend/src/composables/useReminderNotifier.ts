/**
 * useReminderNotifier — следит за активными напоминаниями и показывает тосты.
 * Подключается один раз в App.vue или MainLayout.vue.
 */
import { watch, onUnmounted } from 'vue'
import { useNotificationStore } from '@/stores/notifications'
import { useToast } from '@/composables/useToast'
import { useRouter } from 'vue-router'
import type { Reminder } from '@/stores/notifications'

const FIRED_KEY = 'fired_reminders'

// Звук уведомления (base64 короткий beep)
const NOTIFICATION_SOUND = new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU')

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

// Запрос права на пуш-уведомления
async function requestPushPermission(): Promise<boolean> {
  if (!('Notification' in window)) return false
  if (Notification.permission === 'granted') return true
  
  const result = await Notification.requestPermission()
  return result === 'granted'
}

// Отправить пуш-уведомление
async function sendPushNotification(title: string, body: string, clickAction?: string) {
  if (!('Notification' in window)) return
  
  const granted = await requestPushPermission()
  if (!granted) return
  
  new Notification(title, {
    body,
    icon: '/logo.png',
    badge: '/badge.png',
    tag: clickAction || 'reminder',
    requireInteraction: true
  } as NotificationOptions)
}

// Воспроизвести звук
function playNotificationSound() {
  try {
    // Создаем AudioContext для воспроизведения звука
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
    const oscillator = ctx.createOscillator()
    const gainNode = ctx.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(ctx.destination)
    
    oscillator.type = 'sine'
    oscillator.frequency.setValueAtTime(880, ctx.currentTime)
    oscillator.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3)
    
    gainNode.gain.setValueAtTime(0.3, ctx.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3)
    
    oscillator.start(ctx.currentTime)
    oscillator.stop(ctx.currentTime + 0.3)
  } catch (e) {
    console.warn('Failed to play notification sound:', e)
  }
}

export function useReminderNotifier() {
  const store  = useNotificationStore()
  const toast  = useToast()
  const router = useRouter()

  let interval: ReturnType<typeof setInterval> | null = null

  const check = () => {
    const fired = getFired()
    const now   = Date.now()

    for (const r of store.reminders as Reminder[]) {
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
        const comment    = r.comment || ''

        // Получаем настройки уведомлений из напоминания
        const enableSound = r.enable_sound !== false  // По умолчанию true
        const enablePush  = r.enable_push !== false   // По умолчанию true

        // Воспроизводим звук если включен
        if (enableSound) {
          playNotificationSound()
        }

        // Отправляем пуш-уведомление если включен
        if (enablePush && animeTitle) {
          sendPushNotification(
            '⏰ Напоминание о просмотре',
            `Пора смотреть ${animeTitle}${comment ? ` — ${comment}` : ''}`,
            `reminder-${animeId}`
          )
        }

        toast.info(`⏰ Пора смотреть ${animeTitle}${comment ? ` — ${comment}` : ''}`, {
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
