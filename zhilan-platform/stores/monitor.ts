import { defineStore } from 'pinia'
import type { AgentStatus, LogEntry, SystemMetric } from '~/types'
import { monitorApi, settingsApi, type PipelineStep } from '~/utils/api'

export const useMonitorStore = defineStore('monitor', () => {
  const agents = ref<AgentStatus[]>([])
  const logs = ref<LogEntry[]>([])
  const metrics = ref<SystemMetric[]>([])
  const isRunning = ref(false)
  const lastCollect = ref('')
  const nextCollect = ref('')
  const percentage = ref(0)
  const pipelineSteps = ref<PipelineStep[]>([])
  const loading = ref(false)
  const collecting = ref(false)

  async function fetchMonitor() {
    loading.value = true
    try {
      const [status, logData] = await Promise.all([
        monitorApi.status(),
        monitorApi.logs(1, 50),
      ])
      isRunning.value = status.isRunning
      lastCollect.value = status.lastCollect || ''
      nextCollect.value = status.nextCollect || ''
      percentage.value = status.percentage || 0
      pipelineSteps.value = status.pipelineSteps || []
      agents.value = status.agents || []
      metrics.value = status.metrics || []
      logs.value = logData.items || []
    } catch (e) {
      console.error('[monitor] fetch failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function triggerCollect() {
    if (collecting.value) return
    collecting.value = true
    try {
      await settingsApi.collect()
      // 轮询刷新监控状态，直到流水线从 running 回到 idle（或超时）
      const maxWait = 180000 // 最多等待 3 分钟
      const start = Date.now()
      let sawRunning = false
      while (Date.now() - start < maxWait) {
        await new Promise((r) => setTimeout(r, 2000))
        await fetchMonitor()
        if (isRunning.value) {
          sawRunning = true
        } else if (sawRunning) {
          break // 流水线已完成
        } else if (Date.now() - start > 30000) {
          break // 30 秒内未观察到运行状态，视为已快速完成
        }
      }
      await fetchMonitor() // 最终刷新一次
    } catch (e) {
      console.error('[monitor] trigger collect failed:', e)
    } finally {
      collecting.value = false
    }
  }

  return { agents, logs, metrics, isRunning, lastCollect, nextCollect, percentage, pipelineSteps, loading, collecting, fetchMonitor, triggerCollect }
})
