/**
 * Server-Sent Events (SSE) composable with authentication support
 *
 * Native EventSource doesn't support custom headers, so we use fetch API
 * to implement SSE with proper authentication.
 */
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

export function useSSE() {
  const router = useRouter()
  const isConnected = ref(false)
  const retryCount = ref(0)
  const maxRetries = 5
  let abortController = null
  let eventHandlers = {}
  let reconnectTimer = null
  let isReconnecting = false

  /**
   * Parse SSE data from a line
   */
  function parseSSELine(line) {
    if (line.startsWith('event:')) {
      return { type: 'event', value: line.slice(6).trim() }
    } else if (line.startsWith('data:')) {
      return { type: 'data', value: line.slice(5).trim() }
    } else if (line.startsWith(':')) {
      return { type: 'comment' }
    }
    return null
  }

  /**
   * Connect to SSE endpoint with authentication
   */
  async function connect(url, options = {}) {
    const {
      onOpen = null,
      onError = null,
      onMessage = null,
      reconnectInterval = 3000
    } = options

    disconnect()

    const token = localStorage.getItem('hotspotai_token')
    const headers = {
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache'
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    abortController = new AbortController()

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
        signal: abortController.signal
      })

      // Handle 401 Unauthorized
      if (response.status === 401) {
        handleError('认证失败，请重新登录', true)
        return
      }

      // Handle other errors
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      isConnected.value = true
      retryCount.value = 0
      if (onOpen) onOpen()

      // Read the stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = 'message'
      let currentData = []

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          break
        }

        // Decode and process the chunk
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // Keep the last incomplete line in buffer

        for (const line of lines) {
          const parsed = parseSSELine(line)

          if (!parsed) continue

          if (parsed.type === 'event') {
            currentEvent = parsed.value
          } else if (parsed.type === 'data') {
            if (parsed.value === '') {
              // Empty data line marks the end of an event
              if (currentData.length > 0) {
                const eventData = currentData.join('\n')
                handleEvent(currentEvent, eventData, onMessage)
                currentData = []
                currentEvent = 'message'
              }
            } else {
              currentData.push(parsed.value)
            }
          }
        }
      }

    } catch (error) {
      if (error.name === 'AbortError') {
        // Connection was intentionally closed
        return
      }

      isConnected.value = false

      if (onError) {
        onError(error)
      }

      // Attempt to reconnect
      if (retryCount.value < maxRetries) {
        scheduleReconnect(url, options, reconnectInterval)
      }
    }
  }

  /**
   * Handle SSE event
   */
  function handleEvent(eventType, data, onMessage) {
    try {
      const parsedData = data === '' ? null : JSON.parse(data)

      // Call event-specific handler
      if (eventHandlers[eventType]) {
        eventHandlers[eventType](parsedData)
      }

      // Call general message handler
      if (onMessage) {
        onMessage(eventType, parsedData)
      }
    } catch (e) {
      console.error(`Failed to parse SSE event [${eventType}]:`, e)
    }
  }

  /**
   * Handle error (401, network error, etc.)
   */
  function handleError(message, shouldLogout = false) {
    console.error('SSE error:', message)

    if (shouldLogout) {
      // Clear auth state
      localStorage.removeItem('hotspotai_token')
      localStorage.removeItem('hotspotai_user')

      ElMessage.warning('登录已过期，请重新登录')

      // Redirect to login
      setTimeout(() => {
        if (window.location.pathname !== '/login') {
          router.push('/login')
        }
      }, 500)
    }

    isConnected.value = false
  }

  /**
   * Schedule reconnection attempt
   */
  function scheduleReconnect(url, options, interval) {
    if (isReconnecting) return

    isReconnecting = true
    retryCount.value++

    console.log(`SSE: Scheduling reconnect ${retryCount.value}/${maxRetries} in ${interval}ms`)

    reconnectTimer = setTimeout(() => {
      isReconnecting = false
      connect(url, options)
    }, interval)
  }

  /**
   * Register event handler
   */
  function on(event, handler) {
    eventHandlers[event] = handler
  }

  /**
   * Remove event handler
   */
  function off(event) {
    delete eventHandlers[event]
  }

  /**
   * Disconnect SSE connection
   */
  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }

    if (abortController) {
      abortController.abort()
      abortController = null
    }

    isReconnecting = false
    isConnected.value = false
  }

  // Auto disconnect on component unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    retryCount,
    connect,
    disconnect,
    on,
    off
  }
}
