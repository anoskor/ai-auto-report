<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-800 mb-1">系统配置</h1>
    <p class="text-sm text-slate-500 mb-6">管理监控主题、数据源、采集频率与推送渠道</p>

    <div class="grid grid-cols-2 gap-4">
      <!-- Topics -->
      <div class="card p-5">
        <h2 class="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Tags class="w-4 h-4" style="color:oklch(0.52 0.18 230)" />监控主题管理
        </h2>
        <div class="space-y-2 mb-4">
          <div v-for="t in store.topicList" :key="t.id"
               class="flex items-center justify-between p-3 rounded-lg bg-slate-50">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full" :style="{ background: topicColor(t.color) }"></span>
              <span class="text-sm font-medium text-slate-700">{{ t.name }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[10px] px-2 py-0.5 rounded-full"
                    :class="t.active ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-500'">
                {{ t.active ? '活跃' : '暂停' }}
              </span>
              <button class="text-slate-400 hover:text-red-500 transition-colors" @click="store.removeTopic(t.id)">
                <X class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        <div class="flex gap-2">
          <input v-model="store.newTopicName" type="text" placeholder="输入新主题名称..."
                 class="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-300"
                 @keyup.enter="store.addTopic()">
          <button @click="store.addTopic"
                  class="px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors hover:opacity-90"
                  style="background:oklch(0.52 0.18 230)">添加</button>
        </div>
      </div>

      <!-- Data Sources -->
      <div class="card p-5">
        <h2 class="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Database class="w-4 h-4" style="color:oklch(0.52 0.17 160)" />数据源配置
        </h2>
        <div class="space-y-3">
          <div v-for="src in store.sourceList" :key="src.id"
               class="flex items-center justify-between p-3 rounded-lg border border-slate-200">
            <div class="flex items-center gap-3">
              <span class="text-lg">{{ src.id === 1 ? '📰' : src.id === 2 ? '🕷️' : src.id === 3 ? '📡' : '📄' }}</span>
              <div>
                <p class="text-sm font-medium text-slate-700">{{ src.name }}</p>
                <p class="text-[11px] text-slate-400">{{ src.description }}</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" :checked="src.enabled" @change="store.toggleSource(src.id)" class="sr-only peer">
              <div class="w-9 h-5 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"
                   :style="{ background: src.enabled ? 'oklch(0.52 0.18 230)' : '#e2e8f0' }"></div>
            </label>
          </div>
        </div>
      </div>

      <!-- Collection Frequency -->
      <div class="card p-5">
        <h2 class="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Clock class="w-4 h-4" style="color:oklch(0.65 0.18 80)" />采集频率设置
        </h2>
        <div class="space-y-4">
          <div>
            <label class="text-xs font-medium text-slate-600 mb-1.5 block">采集间隔 (Cron表达式)</label>
            <input v-model="store.cron.collection" type="text"
                   class="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-100">
            <p class="text-[11px] text-slate-400 mt-1">当前设置: 每2小时执行一次</p>
          </div>
          <div>
            <label class="text-xs font-medium text-slate-600 mb-1.5 block">日报生成时间</label>
            <input v-model="store.cron.reportGeneration" type="text"
                   class="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-100">
            <p class="text-[11px] text-slate-400 mt-1">当前设置: 每天早7点生成</p>
          </div>
          <button @click="store.saveCron" class="px-4 py-2 rounded-lg text-white text-sm font-medium transition-colors hover:opacity-90"
                  style="background:oklch(0.52 0.18 230)">保存配置</button>
        </div>
      </div>

      <!-- Push Channels -->
      <div class="card p-5">
        <h2 class="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Send class="w-4 h-4" style="color:oklch(0.55 0.20 30)" />推送渠道配置
        </h2>
        <div class="space-y-3">
          <div v-for="ch in store.channelList" :key="ch.id"
               class="flex items-center justify-between p-3 rounded-lg border border-slate-200">
            <div class="flex items-center gap-3">
              <span class="text-lg">{{ ch.id === 1 ? '🔌' : '📥' }}</span>
              <div>
                <p class="text-sm font-medium text-slate-700">{{ ch.name }}</p>
                <p class="text-[11px] text-slate-400">{{ ch.description }}</p>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" :checked="ch.enabled" @change="store.toggleChannel(ch.id)" class="sr-only peer">
              <div class="w-9 h-5 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"
                   :style="{ background: ch.enabled ? 'oklch(0.52 0.18 230)' : '#e2e8f0' }"></div>
            </label>
          </div>
        </div>
        <div class="mt-4 p-3 rounded-lg bg-slate-50">
          <p class="text-xs text-slate-500 mb-1">Webhook URL</p>
          <input v-model="store.webhookUrl" type="text" placeholder="https://example.com/webhook"
                 class="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-100">
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Tags, Database, Clock, Send, X } from 'lucide-vue-next'
import { useSettingsStore } from '~/stores/settings'

const store = useSettingsStore()

onMounted(() => {
  store.fetchSettings()
})

definePageMeta({ layout: 'default' })

function topicColor(color: string): string {
  const map: Record<string, string> = {
    blue: 'oklch(0.52 0.18 230)',
    green: 'oklch(0.52 0.17 160)',
    amber: 'oklch(0.65 0.18 80)',
    orange: 'oklch(0.55 0.20 30)'
  }
  return map[color] || map.blue
}
</script>
