/**
 * WebSocket 前端 composable — 连接后端实时推送
 */
export function useWebSocket() {
  const isConnected = ref(false)
  const messages = ref<any[]>([])
  const workflowProgress = ref<{ currentStage: string; percentage: number }>({ currentStage: '', percentage: 0 })
  const agentStatuses = ref<any[]>([])
  const liveLogs = ref<any[]>([])
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  const WS_URL = import.meta.dev
    ? 'ws://localhost:8000/ws'
    : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`

  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return

    ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      isConnected.value = true
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        messages.value.push(msg)

        switch (msg.type) {
          case 'workflow:progress':
            workflowProgress.value = msg.data
            break
          case 'agent:status':
            agentStatuses.value = [...agentStatuses.value.filter((a: any) => a.name !== msg.data.name), msg.data]
            break
          case 'log:new':
            liveLogs.value = [msg.data, ...liveLogs.value].slice(0, 100)
            break
        }
      } catch (e) {
        // ignore parse errors
      }
    }

    ws.onclose = () => {
      isConnected.value = false
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, 3000)
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws?.close()
    ws = null
    isConnected.value = false
  }

  function sendPing() {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }

  return {
    isConnected,
    messages,
    workflowProgress,
    agentStatuses,
    liveLogs,
    connect,
    disconnect,
    sendPing,
  }
}
