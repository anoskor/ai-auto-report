import { defineStore } from 'pinia'
import type { ClusterItem, ClusterNode, ClusterLink } from '~/types'
import { clustersApi } from '~/utils/api'

function parseDays(span: string): number {
  const m = (span || '').match(/(\d+)/)
  return m ? Number(m[1]) : 0
}

export const useClustersStore = defineStore('clusters', () => {
  const clusters = ref<ClusterItem[]>([])
  const graphNodes = ref<ClusterNode[]>([])
  const graphLinks = ref<ClusterLink[]>([])
  const topicFilter = ref('全部主题')
  const timeFilter = ref('今日')
  const sortBy = ref('按重要性排序')
  const loading = ref(false)
  const currentCluster = ref<ClusterItem | null>(null)

  // 分类下拉选项：动态来自真实聚类的主题（去重）
  const topicOptions = computed(() => {
    const opts = ['全部主题']
    const seen = new Set<string>()
    for (const c of clusters.value) {
      if (c.title && !seen.has(c.title)) {
        seen.add(c.title)
        opts.push(c.title)
      }
    }
    return opts
  })

  // 按分类/时间筛选 + 排序后的列表
  const filteredClusters = computed(() => {
    const filtered = clusters.value.filter(c => {
      if (topicFilter.value !== '全部主题' && c.title !== topicFilter.value) return false
      const days = parseDays(c.timeSpan)
      if (timeFilter.value === '今日' && days > 1) return false
      if (timeFilter.value === '近3天' && days > 3) return false
      if (timeFilter.value === '近7天' && days > 7) return false
      return true
    })
    const arr = [...filtered]
    if (sortBy.value === '按文章数排序') {
      arr.sort((a, b) => b.articleCount - a.articleCount)
    } else if (sortBy.value === '按时间排序') {
      arr.sort((a, b) => parseDays(b.timeSpan) - parseDays(a.timeSpan))
    } else {
      arr.sort((a, b) => (b.importanceScore ?? b.rating) - (a.importanceScore ?? a.rating))
    }
    return arr
  })

  // 关系图数据由后端按 topic 过滤返回（默认 top 60，选主题时为单主题子图）
  const filteredGraph = computed(() => ({ nodes: graphNodes.value, links: graphLinks.value }))

  async function fetchClusters() {
    loading.value = true
    try {
      const [list, graph] = await Promise.all([clustersApi.list(), clustersApi.graph()])
      clusters.value = list.items || []
      graphNodes.value = graph.nodes || []
      graphLinks.value = graph.links || []
    } catch (e) {
      console.error('[clusters] fetch failed:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchGraphByTopic(topic: string) {
    try {
      const graph = await clustersApi.graph(topic)
      graphNodes.value = graph.nodes || []
      graphLinks.value = graph.links || []
    } catch (e) {
      console.error('[clusters] fetch graph by topic failed:', e)
    }
  }

  async function fetchClusterById(id: number) {
    const found = clusters.value.find(c => c.id === id)
    if (found) {
      currentCluster.value = found
      return
    }
    try {
      currentCluster.value = await clustersApi.detail(id)
    } catch (e) {
      console.error('[clusters] fetch detail failed:', e)
      currentCluster.value = null
    }
  }

  const getClusterById = (id: number): ClusterItem | undefined => {
    return clusters.value.find(c => c.id === id)
  }

  return { clusters, graphNodes, graphLinks, topicFilter, timeFilter, sortBy, topicOptions, filteredClusters, filteredGraph, loading, currentCluster, fetchClusters, fetchGraphByTopic, fetchClusterById, getClusterById }
})
