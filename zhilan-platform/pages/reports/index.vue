<template>
  <div>
    <PageHeader title="研报中心" description="AI生成的深度结构化研报，涵盖背景、现状、趋势与风险分析" />

    <div class="flex items-center gap-3 mb-4">
      <div class="relative flex-1 max-w-sm">
        <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input v-model="store.searchQuery" type="text" placeholder="搜索研报标题或关键词..."
          class="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-100">
      </div>
      <select v-model="store.timeFilter" class="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-100">
        <option>全部时间</option><option>今天</option><option>近7天</option><option>近30天</option>
      </select>
      <select v-model="store.topicFilter" class="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-100">
        <option>全部主题</option><option>宏观经济</option><option>科技</option><option>能源</option><option>金融</option>
      </select>
    </div>

    <div class="space-y-3">
      <NuxtLink v-for="item in store.filteredReports" :key="item.id" :to="`/reports/${item.id}`"
        class="card p-5 cursor-pointer hover:shadow-md block no-underline">
        <div class="flex items-start justify-between mb-2">
          <h2 class="font-semibold text-slate-800">{{ item.title }}</h2>
          <span class="text-xs text-slate-400 shrink-0 ml-3">{{ item.time }}</span>
        </div>
        <div class="flex gap-2 mb-2">
          <span class="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-100">背景</span>
          <span class="text-xs px-2 py-0.5 rounded-full bg-green-50 text-green-600 border border-green-100">现状</span>
          <span class="text-xs px-2 py-0.5 rounded-full bg-orange-50 text-orange-600 border border-orange-100">趋势</span>
          <span class="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-500 border border-red-100">风险</span>
        </div>
        <p class="text-xs text-slate-500 line-clamp-2 mb-2">{{ item.summary }}</p>
        <div class="flex items-center gap-4 text-xs text-slate-400">
          <span>来源: {{ item.articleCount }}篇文章</span>
          <span>通过率: {{ item.passRate }}</span>
          <span style="color:oklch(0.52 0.18 230)">阅读全文 →</span>
        </div>
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search } from 'lucide-vue-next'
import { useReportsStore } from '~/stores/reports'
import PageHeader from '~/components/common/PageHeader.vue'

const store = useReportsStore()

onMounted(() => {
  store.fetchReports()
})

definePageMeta({ layout: 'default' })
</script>
