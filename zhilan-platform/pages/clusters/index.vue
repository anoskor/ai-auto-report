<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">聚类分析</h1>
        <p class="text-sm text-slate-500 mt-0.5">新闻主题簇可视化与语义关系分析</p>
      </div>
      <div class="flex items-center gap-3">
        <select v-model="store.topicFilter" class="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-100">
          <option v-for="opt in store.topicOptions" :key="opt" :value="opt">{{ opt }}</option>
        </select>
        <select v-model="store.timeFilter" class="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-100">
          <option>今日</option><option>近3天</option><option>近7天</option>
        </select>
        <select v-model="store.sortBy" class="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-100">
          <option>按重要性排序</option><option>按时间排序</option><option>按文章数排序</option>
        </select>
      </div>
    </div>

    <!-- Cluster Graph -->
    <div class="card p-5 mb-4">
      <h2 class="text-sm font-semibold text-slate-800 mb-1">聚类关系图</h2>
      <p class="text-xs text-slate-400 mb-4">力导向图展示主题簇之间的语义关联</p>
      <div ref="graphRef" style="width:100%;height:350px"></div>
    </div>

    <!-- Cluster List -->
    <div class="card p-5">
      <h2 class="text-sm font-semibold text-slate-800 mb-4">主题簇列表</h2>
      <div class="space-y-3">
        <NuxtLink v-for="item in store.filteredClusters" :key="item.id" :to="`/clusters/${item.id}`"
          class="border border-slate-200 rounded-xl p-4 hover:border-slate-300 hover:shadow-sm transition-all cursor-pointer block no-underline">
          <div class="flex items-start justify-between mb-2">
            <div class="flex items-center gap-3">
              <span class="text-lg">📌</span>
              <div>
                <h3 class="font-semibold text-slate-800">{{ item.title }}</h3>
                <p class="text-xs text-slate-400">相关文章: {{ item.articleCount }}篇 · 时间跨度: {{ item.timeSpan }}</p>
              </div>
            </div>
            <div class="flex items-center gap-1">
              <span v-for="i in 5" :key="i" class="text-sm" :class="i <= item.rating ? 'text-yellow-400' : 'text-slate-300'">
                {{ i <= item.rating ? '⭐' : '☆' }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 mb-3">
            <template v-for="(kw, i) in item.keywords" :key="kw">
              <span class="text-xs px-2 py-0.5 rounded-full border"
                    :class="keywordClass(i)">{{ kw }}</span>
              <span v-if="i < item.keywords.length - 1" class="text-xs text-slate-300">→</span>
            </template>
          </div>
          <span class="text-xs font-medium px-3 py-1 rounded-lg text-white" style="background:oklch(0.52 0.18 230)">查看详情</span>
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useClustersStore } from '~/stores/clusters'
import { useCharts } from '~/composables/useCharts'

const store = useClustersStore()
const { initClusterGraph } = useCharts()
const graphRef = ref<HTMLElement | null>(null)
let graphChart: ReturnType<typeof initClusterGraph> | null = null

definePageMeta({ layout: 'default' })

const keywordColors = ['blue', 'green', 'orange', 'purple', 'red']

function keywordClass(idx: number): string {
  const color = keywordColors[idx % keywordColors.length]
  const map: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    green: 'bg-green-50 text-green-600 border-green-100',
    orange: 'bg-orange-50 text-orange-600 border-orange-100',
    purple: 'bg-purple-50 text-purple-600 border-purple-100',
    red: 'bg-red-50 text-red-500 border-red-100'
  }
  return map[color] || map.blue
}

function renderGraph() {
  if (!graphRef.value) return
  graphChart?.dispose()
  graphChart = initClusterGraph(graphRef.value, { nodes: store.filteredGraph.nodes, links: store.filteredGraph.links })
}

onMounted(() => {
  store.fetchClusters()
  nextTick(renderGraph)
})

watch(() => store.filteredGraph, () => nextTick(renderGraph), { deep: true })

// 分类筛选驱动关系图：选主题时动态请求该主题子图，回「全部主题」时恢复 top 图
watch(() => store.topicFilter, (topic) => {
  store.fetchGraphByTopic(topic === '全部主题' ? '' : topic)
})
</script>
