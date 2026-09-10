<template>
  <div>
    <PageHeader title="每日简报" description="结构化日报，涵盖要闻、研报、行业动态与数据看板" />

    <!-- TOP5 -->
    <div class="card p-5 mb-4">
      <h2 class="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <Flame class="w-4 h-4" style="color:oklch(0.55 0.22 25)" />
        今日要闻 TOP5
      </h2>
      <div class="space-y-2">
        <div v-for="(item, idx) in store.briefs" :key="item.id"
          class="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer border border-slate-100"
          @click="navigateTo(`/briefs/${item.id}`)">
          <div class="flex items-center gap-3 min-w-0">
            <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
                  :style="{ background: rankColors[idx % 5] }">{{ idx + 1 }}</span>
            <div class="min-w-0">
              <span class="text-sm font-medium text-slate-800">{{ item.title }}</span>
              <span class="text-xs text-slate-400 ml-2">{{ item.summary }}</span>
            </div>
          </div>
          <NuxtLink :to="`/briefs/${item.id}`" @click.stop
            class="text-xs font-medium shrink-0 ml-3 px-2 py-1 rounded hover:bg-slate-100 transition-colors no-underline"
            style="color:oklch(0.52 0.18 230)">
            展开详情
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Report Cards -->
    <div class="card p-5 mb-4">
      <h2 class="text-sm font-semibold text-slate-800 mb-4">深度研报</h2>
      <div class="grid grid-cols-2 gap-4">
        <div v-for="item in store.reportCards" :key="item.id"
          class="border border-slate-200 rounded-xl p-4 hover:border-slate-300 hover:shadow-sm transition-all cursor-pointer"
          @click="navigateTo(`/reports/${item.id}`)">
          <h3 class="font-semibold text-slate-800 mb-2">{{ item.title }}</h3>
          <div class="flex gap-2 mb-3">
            <span class="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-100">背景</span>
            <span class="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-600 border border-green-100">现状</span>
            <span class="text-xs px-2 py-0.5 rounded-full bg-orange-50 text-orange-600 border border-orange-100">趋势</span>
            <span class="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-500 border border-red-100">风险</span>
          </div>
          <p class="text-xs text-slate-500 mb-3 line-clamp-2">{{ item.summary }}</p>
          <div class="flex items-center justify-between">
            <span class="text-xs text-slate-400">来源: {{ item.source }} · {{ item.time }}</span>
            <NuxtLink :to="`/reports/${item.id}`" @click.stop
              class="text-xs font-medium px-3 py-1 rounded-lg text-white transition-colors no-underline inline-block"
              style="background:oklch(0.52 0.18 230)">
              阅读全文
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>

    <!-- Industry Snapshot + Data Dashboard -->
    <div class="grid grid-cols-2 gap-4">
      <div class="card p-5">
        <h2 class="text-sm font-semibold text-slate-800 mb-4">行业动态速览</h2>
        <div class="space-y-3">
          <div v-for="ind in store.industries" :key="ind.name" class="p-3 rounded-lg bg-slate-50">
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full mr-2"
                  :class="industryTagClass(ind.name)">{{ ind.name }}</span>
            <span v-for="tag in ind.tags" :key="tag"
              class="text-xs text-slate-600 cursor-pointer hover:text-blue-600 mr-2">{{ tag }}</span>
          </div>
        </div>
      </div>
      <div class="card p-5">
        <h2 class="text-sm font-semibold text-slate-800 mb-4">数据看板</h2>
        <div class="grid grid-cols-3 gap-3">
          <div class="p-4 rounded-xl text-center border" style="background:oklch(0.52 0.17 160/0.04);border-color:oklch(0.52 0.17 160/0.15)">
            <p class="text-xs text-slate-500 mb-1">情绪指数</p>
            <p class="text-3xl font-extrabold" style="color:oklch(0.52 0.17 160)">{{ store.sentiment.sentiment }}</p>
            <p class="text-xs text-slate-400">/100</p>
            <span class="inline-block text-xs font-medium px-2 py-0.5 rounded-full mt-2"
                  style="background:oklch(0.52 0.17 160/0.1);color:oklch(0.52 0.17 160)">▲ 偏乐观</span>
          </div>
          <div class="p-4 rounded-xl text-center border" style="background:oklch(0.55 0.20 30/0.04);border-color:oklch(0.55 0.20 30/0.15)">
            <p class="text-xs text-slate-500 mb-1">热度指数</p>
            <p class="text-3xl font-extrabold" style="color:oklch(0.55 0.20 30)">{{ store.sentiment.heat }}</p>
            <p class="text-xs text-slate-400">/100</p>
            <span class="inline-block text-xs font-medium px-2 py-0.5 rounded-full mt-2"
                  style="background:oklch(0.55 0.20 30/0.1);color:oklch(0.55 0.20 30)">▲ 高</span>
          </div>
          <div class="p-4 rounded-xl text-center border" style="background:oklch(0.52 0.18 230/0.04);border-color:oklch(0.52 0.18 230/0.15)">
            <p class="text-xs text-slate-500 mb-1">波动指数</p>
            <p class="text-3xl font-extrabold" style="color:oklch(0.52 0.18 230)">{{ store.sentiment.volatility }}</p>
            <p class="text-xs text-slate-400">/100</p>
            <span class="inline-block text-xs font-medium px-2 py-0.5 rounded-full mt-2"
                  style="background:oklch(0.52 0.18 230/0.1);color:oklch(0.52 0.18 230)">▼ 低</span>
          </div>
        </div>
        <div ref="sentimentChartRef" style="width:100%;height:180px;margin-top:1rem"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Flame } from 'lucide-vue-next'
import { useBriefsStore } from '~/stores/briefs'
import { useCharts } from '~/composables/useCharts'
import PageHeader from '~/components/common/PageHeader.vue'

const store = useBriefsStore()
const { initSentimentChart } = useCharts()
const sentimentChartRef = ref<HTMLElement | null>(null)
let sentimentChart: ReturnType<typeof initSentimentChart> | null = null

definePageMeta({ layout: 'default' })

const rankColors = [
  'oklch(0.55 0.22 25)', 'oklch(0.55 0.20 30)',
  'oklch(0.65 0.18 80)', 'oklch(0.52 0.18 230)', 'oklch(0.52 0.17 160)'
]

function industryTagClass(name: string): string {
  const map: Record<string, string> = {
    '金融': 'bg-blue-50 text-blue-600',
    '科技': 'bg-green-50 text-green-600',
    '能源': 'bg-orange-50 text-orange-600',
    '医药': 'bg-purple-50 text-purple-600'
  }
  return map[name] || 'bg-slate-50 text-slate-600'
}

function renderSentiment() {
  if (!sentimentChartRef.value) return
  sentimentChart?.dispose()
  sentimentChart = initSentimentChart(sentimentChartRef.value, store.trendData)
}

onMounted(() => {
  store.fetchBriefs()
  nextTick(renderSentiment)
})

watch(() => store.trendData, () => nextTick(renderSentiment), { deep: true })
</script>
