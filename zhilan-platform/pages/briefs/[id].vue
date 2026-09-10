<template>
  <div v-if="item">
    <div class="flex items-center justify-between mb-6">
      <div>
        <BackButton label="返回简报" sub-label="2026-08-04" @back="router.back()" />
        <h1 class="text-2xl font-bold text-slate-800">{{ item.title }}</h1>
        <p class="text-sm text-slate-500 mt-0.5">
          发布时间: 2026-08-04 {{ item.time }} · 来源: {{ item.articleCount }}篇相关报道 · 聚类主题: {{ item.category }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">
          <Share2 class="w-4 h-4" />分享
        </button>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-4 mb-4">
      <div class="card p-4 text-center">
        <p class="text-xs text-slate-500 mb-1">重要性</p>
        <div class="flex justify-center gap-0.5">
          <span v-for="i in 5" :key="i" class="text-sm" :class="i <= item.rating ? 'text-yellow-400' : 'text-slate-300'">
            {{ i <= item.rating ? '⭐' : '☆' }}
          </span>
        </div>
      </div>
      <div class="card p-4 text-center">
        <p class="text-xs text-slate-500 mb-1">关联文章</p>
        <p class="text-xl font-bold text-slate-800">{{ item.relatedArticleCount }}<span class="text-xs font-normal text-slate-400">篇</span></p>
      </div>
      <div class="card p-4 text-center">
        <p class="text-xs text-slate-500 mb-1">相关研报</p>
        <p class="text-xl font-bold text-slate-800">{{ item.relatedReportCount }}<span class="text-xs font-normal text-slate-400">篇</span></p>
      </div>
    </div>

    <div class="card p-6 mb-4">
      <h2 class="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <FileText class="w-4 h-4" style="color:oklch(0.52 0.18 230)" />新闻正文
      </h2>
      <div class="text-sm text-slate-600 leading-relaxed space-y-3" v-html="sanitizedContent"></div>
    </div>

    <div v-if="item.relatedReports.length > 0" class="card p-5">
      <h2 class="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <FileCheck class="w-4 h-4" style="color:oklch(0.55 0.20 30)" />关联研报
      </h2>
      <div class="space-y-2">
        <NuxtLink v-for="r in item.relatedReports" :key="r.id" :to="`/reports/${r.id}`"
          class="p-3 rounded-lg border border-slate-200 cursor-pointer hover:border-slate-300 transition-colors block no-underline">
          <p class="text-sm font-medium text-slate-800">{{ r.title }}</p>
          <p class="text-xs text-slate-400 mt-0.5">四段式结构化研报</p>
        </NuxtLink>
      </div>
    </div>
  </div>
  <div v-else class="card p-12 text-center text-slate-500">简报未找到</div>
</template>

<script setup lang="ts">
import { FileText, FileCheck, Share2 } from 'lucide-vue-next'
import { useBriefsStore } from '~/stores/briefs'
import BackButton from '~/components/common/BackButton.vue'

const route = useRoute()
const router = useRouter()
const store = useBriefsStore()

const item = computed(() => store.currentBrief)

const sanitizedContent = computed(() => {
  if (!item.value) return ''
  return item.value.content
})

onMounted(() => {
  store.fetchBriefById(Number(route.params.id))
})

definePageMeta({ layout: 'default' })
</script>
