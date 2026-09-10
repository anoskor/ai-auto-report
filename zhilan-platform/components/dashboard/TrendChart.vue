<template>
  <div class="card p-5">
    <h2 class="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
      <TrendingUp class="w-4 h-4" style="color:oklch(0.52 0.18 230)" />
      采集趋势 (近7日)
    </h2>
    <div ref="chartRef" style="width:100%;height:250px"></div>
  </div>
</template>

<script setup lang="ts">
import { TrendingUp } from 'lucide-vue-next'
import { useCharts } from '~/composables/useCharts'
import { useDashboardStore } from '~/stores/dashboard'

const chartRef = ref<HTMLElement | null>(null)
const { initTrendChart } = useCharts()
const store = useDashboardStore()
let chart: ReturnType<typeof initTrendChart> | null = null

function render() {
  if (!chartRef.value) return
  chart?.dispose()
  chart = initTrendChart(chartRef.value, store.trend)
}

onMounted(() => {
  nextTick(render)
})

watch(() => store.trend, () => nextTick(render), { deep: true })
</script>
