import { defineStore } from 'pinia'
import type { StatItem, TopNewsItem, TrendDataPoint, ReportCard, WorkflowProgress, WorkflowStep } from '~/types'
import { dashboardApi } from '~/utils/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<StatItem[]>([])
  const news = ref<TopNewsItem[]>([])
  const trend = ref<TrendDataPoint[]>([])
  const latestReports = ref<ReportCard[]>([])
  const progress = ref<WorkflowProgress>({ currentStage: '加载中', percentage: 0 })
  const stepGroup1 = ref<WorkflowStep[]>([])
  const stepGroup2 = ref<WorkflowStep[]>([])
  const loading = ref(false)

  async function fetchDashboard() {
    loading.value = true
    try {
      const [s, n, t, r, p] = await Promise.all([
        dashboardApi.stats(),
        dashboardApi.topNews(),
        dashboardApi.trend(),
        dashboardApi.latestReports(),
        dashboardApi.workflowStatus(),
      ])
      stats.value = s || []
      news.value = n || []
      trend.value = t || []
      latestReports.value = r || []
      if (p) {
        progress.value = { currentStage: p.currentStage, percentage: p.percentage }
        stepGroup1.value = p.stepGroup1 || []
        stepGroup2.value = p.stepGroup2 || []
      }
    } catch (e) {
      console.error('[dashboard] fetch failed:', e)
    } finally {
      loading.value = false
    }
  }

  return { stats, news, trend, latestReports, progress, stepGroup1, stepGroup2, loading, fetchDashboard }
})
