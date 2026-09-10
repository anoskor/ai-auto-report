<template>
  <div class="card p-5 cursor-pointer" @click="$emit('click')">
    <div class="flex items-center gap-3 mb-3">
      <div class="w-10 h-10 rounded-lg flex items-center justify-center" :style="{ background: bgColor }">
        <component :is="icon" class="w-5 h-5" :style="{ color: iconColor }" />
      </div>
      <div>
        <p class="text-xs text-slate-500">{{ label }}</p>
        <p class="text-2xl font-bold text-slate-800">{{ value }}</p>
      </div>
    </div>
    <div class="flex items-center gap-1 text-xs font-medium" :class="changeClass">
      <component :is="changeIcon" class="w-3 h-3" />
      {{ changeLabel }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Rss, Filter, FileCheck, Send, TrendingUp, ArrowDown, CheckCircle, Clock } from 'lucide-vue-next'

const props = defineProps<{
  label: string
  value: string | number
  changeLabel: string
  changeType: 'up' | 'down' | 'neutral'
  icon: string
  color: string
}>()

defineEmits<{ click: [] }>()

const iconMap: Record<string, any> = { rss: Rss, filter: Filter, 'file-check': FileCheck, send: Send }

const icon = computed(() => iconMap[props.icon] || Rss)

const bgColor = computed(() => {
  const map: Record<string, string> = {
    blue: 'oklch(0.52 0.18 230/0.1)',
    orange: 'oklch(0.55 0.20 30/0.1)',
    green: 'oklch(0.52 0.17 160/0.1)',
    amber: 'oklch(0.65 0.18 80/0.1)'
  }
  return map[props.color] || map.blue
})

const iconColor = computed(() => {
  const map: Record<string, string> = {
    blue: 'oklch(0.52 0.18 230)',
    orange: 'oklch(0.55 0.20 30)',
    green: 'oklch(0.52 0.17 160)',
    amber: 'oklch(0.65 0.18 80)'
  }
  return map[props.color] || map.blue
})

const changeClass = computed(() => {
  if (props.changeType === 'up') return 'text-green-600'
  if (props.changeType === 'down') return 'text-red-500'
  return 'text-slate-400'
})

const changeIcon = computed(() => {
  if (props.changeType === 'up') return TrendingUp
  if (props.changeType === 'down') return ArrowDown
  return Clock
})
</script>
