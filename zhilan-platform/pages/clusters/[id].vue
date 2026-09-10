<template>
  <div v-if="item">
    <div class="flex items-center justify-between mb-6">
      <div>
        <BackButton label="返回聚类分析" @back="router.back()" />
        <h1 class="text-2xl font-bold text-slate-800">{{ item.title }}</h1>
        <p class="text-sm text-slate-500 mt-0.5">
          主题标签: 科技政策 · 相关文章: {{ item.articleCount }}篇 · 时间跨度: {{ item.timeSpan }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span v-for="i in 5" :key="i" class="text-sm" :class="i <= item.rating ? 'text-yellow-400' : 'text-slate-300'">
          {{ i <= item.rating ? '⭐' : '☆' }}
        </span>
        <span class="text-xs text-slate-400 ml-1">重要性 {{ item.rating }}/5</span>
      </div>
    </div>

    <!-- Timeline -->
    <div class="card p-5 mb-4">
      <h2 class="text-sm font-semibold text-slate-800 mb-4">事件时间线</h2>
      <div class="relative pl-6 border-l-2 border-blue-100 space-y-5">
        <div v-for="(evt, i) in item.timeline" :key="i" class="relative">
          <div class="absolute -left-[31px] w-4 h-4 rounded-full bg-white border-2 top-0.5"
               :class="i < item.timeline.length - 1 ? 'border-blue-300' : 'border-slate-200'"></div>
          <p class="text-xs text-slate-400 mb-1">{{ evt.time }}</p>
          <p class="text-sm font-medium text-slate-700">{{ evt.title }}</p>
          <p class="text-xs text-slate-500 mt-0.5">{{ evt.description }}</p>
        </div>
      </div>
    </div>

    <!-- Articles -->
    <div class="card p-5">
      <h2 class="text-sm font-semibold text-slate-800 mb-4">文章列表 ({{ item.articles.length }}篇)</h2>
      <div class="space-y-2">
        <div v-for="art in item.articles" :key="art.title"
          class="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 border border-slate-100">
          <div class="min-w-0">
            <p class="text-sm font-medium text-slate-800 truncate">{{ art.title }}</p>
            <p class="text-xs text-slate-400">{{ art.source }} · {{ art.date }}</p>
          </div>
          <ExternalLink class="w-4 h-4 text-slate-400 shrink-0 ml-3" />
        </div>
      </div>
    </div>
  </div>
  <div v-else class="card p-12 text-center text-slate-500">聚类未找到</div>
</template>

<script setup lang="ts">
import { ExternalLink } from 'lucide-vue-next'
import { useClustersStore } from '~/stores/clusters'
import BackButton from '~/components/common/BackButton.vue'

const route = useRoute()
const router = useRouter()
const store = useClustersStore()

const item = computed(() => store.currentCluster)

onMounted(() => {
  store.fetchClusterById(Number(route.params.id))
})

definePageMeta({ layout: 'default' })
</script>
