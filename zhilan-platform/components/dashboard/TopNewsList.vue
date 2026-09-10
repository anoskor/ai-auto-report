<template>
  <div class="card p-5">
    <h2 class="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
      <Star class="w-4 h-4" style="color:oklch(0.65 0.18 80)" />
      今日要闻 TOP5
    </h2>
    <div class="space-y-3">
      <div
        v-for="(item, idx) in items" :key="item.id"
        class="flex items-start gap-3 p-2.5 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer"
        @click="$emit('select', item.id)">
        <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 text-white"
              :style="{ background: rankColors[idx] }">
          {{ idx + 1 }}
        </span>
        <div class="min-w-0">
          <p class="text-sm font-medium text-slate-800 truncate">{{ item.title }}</p>
          <p class="text-xs text-slate-400 mt-0.5">{{ item.time }} · {{ item.category }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Star } from 'lucide-vue-next'
import type { TopNewsItem } from '~/types'

defineProps<{ items: TopNewsItem[] }>()
defineEmits<{ select: [id: number] }>()

const rankColors = [
  'oklch(0.55 0.22 25)',
  'oklch(0.55 0.20 30)',
  'oklch(0.65 0.18 80)',
  'oklch(0.52 0.18 230)',
  'oklch(0.52 0.17 160)'
]
</script>
