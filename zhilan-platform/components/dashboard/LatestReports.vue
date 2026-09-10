<template>
  <div class="card p-5">
    <h2 class="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
      <FileText class="w-4 h-4" style="color:oklch(0.52 0.18 230)" />
      最新研报
    </h2>
    <div class="space-y-2.5">
      <div
        v-for="item in items" :key="item.id"
        class="flex items-center justify-between p-2.5 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer"
        @click="$emit('select', item.id)">
        <div class="min-w-0">
          <p class="text-sm font-medium text-slate-800 truncate">{{ item.title }}</p>
          <p class="text-xs text-slate-400">背景 · 现状 · 趋势 · 风险</p>
        </div>
        <span class="text-xs text-slate-400 shrink-0 ml-3">{{ item.time }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FileText } from 'lucide-vue-next'
import type { ReportCard } from '~/types'

defineProps<{ items: ReportCard[] }>()
defineEmits<{ select: [id: number] }>()
</script>
