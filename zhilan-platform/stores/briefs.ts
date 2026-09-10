import { defineStore } from 'pinia'
import type { BriefItem, ReportCard, IndustryItem, SentimentData } from '~/types'
import { briefsApi, type SentimentTrendData } from '~/utils/api'

export const useBriefsStore = defineStore('briefs', () => {
  const briefs = ref<BriefItem[]>([])
  const reportCards = ref<ReportCard[]>([])
  const industries = ref<IndustryItem[]>([])
  const sentiment = ref<SentimentData>({ sentiment: 0, heat: 0, volatility: 0 })
  const trendData = ref<SentimentTrendData>({ labels: [], sentiment: [], heat: [], volatility: [] })
  const loading = ref(false)
  const currentBrief = ref<BriefItem | null>(null)

  async function fetchBriefs() {
    loading.value = true
    try {
      const data = await briefsApi.list()
      briefs.value = data.briefs || []
      reportCards.value = data.reportCards || []
      industries.value = data.industries || []
      if (data.sentiment) sentiment.value = data.sentiment
      if (data.trendData) trendData.value = data.trendData
    } catch (e) {
      console.error('[briefs] fetch failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchBriefById(id: number) {
    const found = briefs.value.find(b => b.id === id)
    if (found) {
      currentBrief.value = found
      return
    }
    try {
      currentBrief.value = await briefsApi.detail(id)
    } catch (e) {
      console.error('[briefs] fetch detail failed:', e)
      currentBrief.value = null
    }
  }

  const getBriefById = (id: number): BriefItem | undefined => {
    return briefs.value.find(b => b.id === id)
  }

  return { briefs, reportCards, industries, sentiment, trendData, loading, currentBrief, fetchBriefs, fetchBriefById, getBriefById }
})
