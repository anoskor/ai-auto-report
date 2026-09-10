<template>
  <div v-if="item">
    <div class="flex items-center justify-between mb-6">
      <div>
        <BackButton label="返回列表" @back="router.back()" />
        <h1 class="text-2xl font-bold text-slate-800">{{ item.title }}</h1>
        <p class="text-sm text-slate-500 mt-0.5">生成时间: 2026-08-04 {{ item.time === '昨天 16:45' ? '2026-08-03' : '今天' }} · 信息来源: {{ item.articleCount }}篇文章</p>
      </div>
      <div class="flex items-center gap-2">
        <button @click="exportPdf" class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">
          <Download class="w-4 h-4" />导出PDF
        </button>
        <button class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">
          <Share2 class="w-4 h-4" />分享
        </button>
      </div>
    </div>

    <div class="space-y-4">
      <!-- 一、背景 -->
      <div class="card p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <span class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold"
                style="background:oklch(0.52 0.18 230)">一</span>事件背景
        </h2>
        <p class="text-sm text-slate-600 leading-relaxed mb-4">{{ item.background }}</p>
        <div class="flex flex-wrap items-center gap-2 text-xs">
          <span class="text-slate-400">引用来源:</span>
          <a v-for="(s, i) in item.sources" :key="i" :href="s.url" target="_blank" rel="noopener"
             class="px-2 py-0.5 rounded-full bg-slate-100 text-blue-600 hover:bg-blue-50 hover:underline transition-colors inline-flex items-center gap-1">
            [{{ i + 1 }}] {{ s.title || s.source }}
          </a>
        </div>
      </div>

      <!-- 二、现状 -->
      <div class="card p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <span class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold"
                style="background:oklch(0.52 0.17 160)">二</span>现状分析
        </h2>
        <p class="text-sm text-slate-600 leading-relaxed mb-4">{{ item.statusContent }}</p>
        <div class="p-4 rounded-xl border border-slate-200 bg-slate-50">
          <h4 class="text-xs font-semibold text-slate-500 mb-2">关键数据</h4>
          <div class="grid grid-cols-3 gap-4">
            <div v-for="d in item.keyData" :key="d.label">
              <p class="text-xs text-slate-400">{{ d.label }}</p>
              <p class="text-lg font-bold text-slate-800">
                {{ d.value }}
                <span class="text-xs ml-1" :class="d.change.startsWith('▲') ? 'text-green-600' : d.change.startsWith('▼') ? 'text-red-500' : 'text-slate-400'">
                  {{ d.change }}
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 三、趋势 -->
      <div class="card p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <span class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold"
                style="background:oklch(0.65 0.18 80)">三</span>趋势研判
        </h2>
        <p class="text-sm text-slate-600 leading-relaxed mb-3">
          <strong class="text-slate-700">短期（1-3个月）：</strong>{{ item.trendShort }}
        </p>
        <p class="text-sm text-slate-600 leading-relaxed">
          <strong class="text-slate-700">中长期（6-12个月）：</strong>{{ item.trendLong }}
        </p>
      </div>

      <!-- 四、风险 -->
      <div class="card p-6">
        <h2 class="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <span class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold"
                style="background:oklch(0.55 0.22 25)">四</span>风险提示
        </h2>
        <div class="space-y-3">
          <div class="flex items-start gap-3 p-3 rounded-lg bg-red-50 border border-red-100">
            <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" style="color:oklch(0.55 0.22 25)" />
            <div>
              <p class="text-sm font-medium text-slate-800">{{ item.risk1 }}</p>
              <p class="text-xs text-slate-500 mt-0.5">{{ item.risk1desc }}</p>
            </div>
          </div>
          <div class="flex items-start gap-3 p-3 rounded-lg bg-orange-50 border border-orange-100">
            <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" style="color:oklch(0.55 0.20 30)" />
            <div>
              <p class="text-sm font-medium text-slate-800">{{ item.risk2 }}</p>
              <p class="text-xs text-slate-500 mt-0.5">{{ item.risk2desc }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 信息来源 -->
      <div class="card p-6">
        <h2 class="text-sm font-semibold text-slate-800 mb-4">信息来源</h2>
        <div v-if="item.sources.length > 0" class="space-y-2">
          <div v-for="(s, i) in item.sources" :key="i" class="flex items-center justify-between text-sm p-2 rounded hover:bg-slate-50">
            <a :href="s.url" target="_blank" rel="noopener"
               class="text-blue-600 hover:underline inline-flex items-center gap-1.5 min-w-0">
              <span class="truncate">[{{ i + 1 }}] {{ s.title || s.source }}</span>
              <ExternalLink class="w-3.5 h-3.5 shrink-0 text-slate-400" />
            </a>
            <span class="text-xs text-slate-400 shrink-0 ml-3">{{ item.time === '昨天 16:45' ? '2026-08-03' : '2026-08-04' }}</span>
          </div>
        </div>
        <p v-else class="text-sm text-slate-400">暂无来源链接</p>
      </div>
    </div>
  </div>
  <div v-else class="card p-12 text-center text-slate-500">研报未找到</div>
</template>

<script setup lang="ts">
import { Download, Share2, AlertTriangle, ExternalLink } from 'lucide-vue-next'
import { useReportsStore } from '~/stores/reports'
import { BACKEND_ORIGIN } from '~/utils/api'
import BackButton from '~/components/common/BackButton.vue'

const route = useRoute()
const router = useRouter()
const store = useReportsStore()

const item = computed(() => store.currentReport)

function exportPdf() {
  const id = route.params.id
  window.open(`${BACKEND_ORIGIN}/api/v1/reports/${id}/export`, '_blank')
}

onMounted(() => {
  store.fetchReportById(Number(route.params.id))
})

definePageMeta({ layout: 'default' })
</script>
