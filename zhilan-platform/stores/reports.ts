import { defineStore } from 'pinia'
import type { ReportItem } from '~/types'
import { reportsApi } from '~/utils/api'

export const useReportsStore = defineStore('reports', () => {
  const reports = ref<ReportItem[]>([])
  const searchQuery = ref('')
  const timeFilter = ref('全部时间')
  const topicFilter = ref('全部主题')
  const loading = ref(false)
  const currentReport = ref<ReportItem | null>(null)

  const filteredReports = computed(() => {
    let result = reports.value
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      result = result.filter(r => r.title.toLowerCase().includes(q) || r.summary.toLowerCase().includes(q))
    }
    return result
  })

  async function fetchReports() {
    loading.value = true
    try {
      const data = await reportsApi.list()
      reports.value = data.items || []
    } catch (e) {
      console.error('[reports] fetch failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchReportById(id: number) {
    const found = reports.value.find(r => r.id === id)
    if (found) {
      currentReport.value = found
      return
    }
    try {
      currentReport.value = await reportsApi.detail(id)
    } catch (e) {
      console.error('[reports] fetch detail failed:', e)
      currentReport.value = null
    }
  }

  const getReportById = (id: number): ReportItem | undefined => {
    return reports.value.find(r => r.id === id)
  }

  return { reports, searchQuery, timeFilter, topicFilter, filteredReports, loading, currentReport, fetchReports, fetchReportById, getReportById }
})
