<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">实时监控</h1>
        <p class="text-sm text-slate-500 mt-0.5">工作流管道、Agent状态与系统指标实时展示</p>
      </div>
      <div class="flex items-center gap-3 text-xs">
        <button
          @click="store.triggerCollect()"
          :disabled="store.collecting"
          class="px-3.5 py-1.5 rounded-lg text-white text-xs font-medium flex items-center gap-1.5 transition-all hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed"
          style="background:oklch(0.52 0.18 230)">
          <RefreshCw class="w-3.5 h-3.5" :class="store.collecting ? 'animate-spin' : ''" />
          {{ store.collecting ? '采集中...' : '手动采集' }}
        </button>
        <span class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full" style="background:oklch(0.52 0.17 160)"></span>系统运行中
        </span>
        <span class="text-slate-300">|</span>
        <span class="text-slate-500">上次采集: {{ store.lastCollect }}</span>
        <span class="text-slate-300">|</span>
        <span class="text-slate-500">下次采集: {{ store.nextCollect }}</span>
      </div>
    </div>

    <!-- Pipeline -->
    <div class="card p-6 mb-4">
      <h2 class="text-sm font-semibold text-slate-800 mb-4">工作流管道视图</h2>
      <div class="flex items-center gap-2 justify-center flex-wrap">
        <template v-for="(step, idx) in store.pipelineSteps" :key="step.label">
          <!-- Step box -->
          <div class="text-center">
            <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-2" :class="[step.bgColor, step.borderColor]"
                 :style="step.status === 'running' ? { animation: 'pulse 2s infinite' } : {}">
              <component :is="getIcon(step.icon)" class="w-7 h-7" :class="[step.textColor, step.status === 'running' ? 'animate-spin' : '']" />
            </div>
            <p class="text-xs font-semibold text-slate-700">{{ step.label }}</p>
            <p class="text-[11px]" :class="step.textColor">{{ step.detail }}</p>
            <div v-if="step.label === '摘要'" class="w-12 h-1.5 rounded-full bg-slate-100 mx-auto mt-1 overflow-hidden">
              <div class="h-full rounded-full transition-all duration-700" :style="{ width: store.percentage + '%', background: 'linear-gradient(90deg,oklch(0.65 0.18 80),oklch(0.55 0.20 30))' }"></div>
            </div>
          </div>
          <!-- Arrow -->
          <component v-if="idx < store.pipelineSteps.length - 1" :is="ArrowRight" class="w-4 h-4"
                     :class="idx < 4 ? 'text-slate-300' : 'text-slate-300'" />
        </template>
      </div>
    </div>

    <!-- Agent Status + Logs -->
    <div class="grid grid-cols-2 gap-4">
      <div class="card p-5">
        <h2 class="text-sm font-semibold text-slate-800 mb-4">Agent 状态</h2>
        <div class="grid grid-cols-2 gap-3">
          <div v-for="agent in store.agents" :key="agent.name"
               class="p-3 rounded-lg border"
               :style="{ background: agent.color === 'green' ? 'oklch(0.52 0.17 160/0.03)' : 'oklch(0.65 0.18 80/0.03)', borderColor: agent.color === 'green' ? 'oklch(0.52 0.17 160/0.15)' : 'oklch(0.65 0.18 80/0.15)' }">
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-semibold text-slate-700">{{ agent.name }}</span>
              <span class="w-2 h-2 rounded-full" :class="agent.status === 'running' ? 'animate-pulse' : ''"
                    :style="{ background: agent.color === 'green' ? 'oklch(0.52 0.17 160)' : 'oklch(0.65 0.18 80)' }"></span>
            </div>
            <p class="text-[11px] text-slate-500">{{ agent.detail }}</p>
            <p class="text-xs font-medium" :style="{ color: agent.color === 'green' ? 'oklch(0.52 0.17 160)' : 'oklch(0.65 0.18 80)' }">{{ agent.statusText }}</p>
          </div>
        </div>
      </div>

      <div class="card p-5">
        <h2 class="text-sm font-semibold text-slate-800 mb-4">实时日志</h2>
        <div class="space-y-1.5 mb-3 text-xs font-mono p-3 rounded-lg bg-slate-50 max-h-[260px] overflow-y-auto">
          <div v-for="(log, idx) in store.logs" :key="idx" class="flex gap-2">
            <span class="text-slate-400 shrink-0">{{ log.time }}</span>
            <span class="shrink-0" :class="log.level === 'WARN' ? 'text-yellow-600' : log.level === 'ERROR' ? 'text-red-600' : 'text-blue-600'">[{{ log.level }}]</span>
            <span class="text-slate-600">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- System Metrics -->
    <div class="card p-5 mt-4">
      <h2 class="text-sm font-semibold text-slate-800 mb-4">系统指标</h2>
      <div class="grid grid-cols-4 gap-4">
        <div v-for="m in store.metrics" :key="m.label" class="text-center p-3 rounded-lg bg-slate-50">
          <p class="text-xs text-slate-500 mb-1">{{ m.label }}</p>
          <p class="text-xl font-extrabold" :style="{ color: metricColor(m.color) }">
            {{ m.value }}<span v-if="m.subValue" class="text-xs font-normal text-slate-400">{{ m.subValue }}</span>
          </p>
          <div class="w-full h-1.5 rounded-full bg-slate-200 mt-2 overflow-hidden">
            <div class="h-full rounded-full" :style="{ width: m.percentage + '%', background: metricColor(m.color) }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowRight, CheckCircle, Loader, Clock, RefreshCw } from 'lucide-vue-next'
import { useMonitorStore } from '~/stores/monitor'

const store = useMonitorStore()

onMounted(() => {
  store.fetchMonitor()
})

definePageMeta({ layout: 'default' })

function getIcon(name: string) {
  const map: Record<string, any> = { 'check-circle': CheckCircle, 'loader': Loader, 'clock': Clock }
  return map[name] || Clock
}

function metricColor(color: string): string {
  const map: Record<string, string> = {
    blue: 'oklch(0.52 0.18 230)',
    green: 'oklch(0.52 0.17 160)',
    orange: 'oklch(0.55 0.20 30)',
    amber: 'oklch(0.65 0.18 80)'
  }
  return map[color] || map.blue
}
</script>
