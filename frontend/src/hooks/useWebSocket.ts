import { useEffect, useRef, useState, useCallback } from 'react'
import type { RealtimeEvent } from '@/types/api'

interface UseWebSocketOptions {
  onMessage?: (event: RealtimeEvent) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  eventTypes?: string[]
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function useWebSocket(endpoint: string, options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    eventTypes,
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const [isConnected, setIsConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null)

  const connect = useCallback(() => {
    // Build URL with event type filter if specified
    let url = `${WS_URL}${endpoint}`
    if (eventTypes && eventTypes.length > 0) {
      url += `?event_types=${eventTypes.join(',')}`
    }

    const ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('WebSocket connected:', endpoint)
      setIsConnected(true)
      onConnect?.()

      // Clear reconnect timeout if exists
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as RealtimeEvent
        setLastEvent(data)
        onMessage?.(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      onError?.(error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected:', endpoint)
      setIsConnected(false)
      onDisconnect?.()

      // Attempt to reconnect
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('Attempting to reconnect...')
        connect()
      }, reconnectInterval)
    }

    wsRef.current = ws
  }, [endpoint, eventTypes, onMessage, onConnect, onDisconnect, onError, reconnectInterval])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(message)
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    lastEvent,
    sendMessage,
    reconnect: connect,
    disconnect,
  }
}
