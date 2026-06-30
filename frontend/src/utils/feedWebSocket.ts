/**
 * WebSocket service for real-time feed updates.
 * Connects to the global events channel and dispatches custom events.
 */

type EventHandler = (data: unknown) => void

interface FeedWsEvent {
  type: string
  data: unknown
}

class FeedWebSocketService {
  private ws: WebSocket | null = null
  private handlers: Map<string, EventHandler[]> = new Map()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectDelay = 2000
  private maxReconnectDelay = 30000
  private shouldReconnect = true

  connect(token: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) return

    const wsBase = import.meta.env.VITE_WS_URL || 
      (window.location.protocol === 'https:' ? 'wss' : 'ws') + `:

    const url = `${wsBase}/global/?token=${token}`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.reconnectDelay = 2000
    }

    this.ws.onmessage = (event) => {
      try {
        const msg: FeedWsEvent = JSON.parse(event.data)
        this.dispatch(msg.type, msg.data)
      } catch {
        
      }
    }

    this.ws.onclose = () => {
      if (this.shouldReconnect) {
        this.scheduleReconnect(token)
      }
    }

    this.ws.onerror = () => {
      this.ws?.close()
    }
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
  }

  on(eventType: string, handler: EventHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, [])
    }
    this.handlers.get(eventType)!.push(handler)
  }

  off(eventType: string, handler: EventHandler) {
    const list = this.handlers.get(eventType)
    if (list) {
      this.handlers.set(eventType, list.filter(h => h !== handler))
    }
  }

  private dispatch(type: string, data: unknown) {
    const list = this.handlers.get(type) || []
    list.forEach(h => h(data))

    
    const wildcards = this.handlers.get('*') || []
    wildcards.forEach(h => h({ type, data }))
  }

  private scheduleReconnect(token: string) {
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay)
      this.connect(token)
    }, this.reconnectDelay)
  }
}

export const feedWs = new FeedWebSocketService()
