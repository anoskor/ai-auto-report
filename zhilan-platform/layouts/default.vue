<template>
  <div class="min-h-screen">
    <!-- ===== HEADER ===== -->
    <header class="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-xl border-b border-slate-200/80 shadow-sm">
      <div class="max-w-screen-2xl mx-auto px-6 h-16 flex items-center gap-6">
        <!-- Logo -->
        <NuxtLink to="/" class="flex items-center gap-3 shrink-0 no-underline">
          <div class="w-9 h-9 rounded-lg flex items-center justify-center text-white font-extrabold text-base"
               style="background:linear-gradient(135deg,oklch(0.52 0.18 230),oklch(0.55 0.16 200))">智</div>
          <span class="font-bold text-lg tracking-tight text-slate-800">智览</span>
          <span class="text-xs font-semibold px-2 py-0.5 rounded-full border border-slate-200 text-slate-500">v1.0</span>
        </NuxtLink>

        <!-- Navigation -->
        <nav class="flex items-center gap-1 h-full">
          <NuxtLink v-for="item in navItems" :key="item.path" :to="item.path"
            class="tab-btn h-full flex items-center gap-2 px-4 text-sm font-medium transition-colors"
            :class="isActive(item.path) ? 'text-slate-700 active' : 'text-slate-500 hover:text-slate-700'"
            :style="isActive(item.path) ? '' : ''">
            <component :is="item.icon" class="w-4 h-4" />
            {{ item.label }}
          </NuxtLink>
        </nav>

        <div class="flex-1"></div>

        <!-- Status + Notifications + User -->
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
               style="background:oklch(0.52 0.17 160 / 0.08);color:oklch(0.52 0.17 160)">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style="background:oklch(0.52 0.17 160)"></span>
              <span class="relative inline-flex rounded-full h-2 w-2" style="background:oklch(0.52 0.17 160)"></span>
            </span>
            系统运行中
          </div>
          <div class="relative cursor-pointer">
            <Bell class="w-5 h-5 text-slate-400 hover:text-slate-600 transition-colors" />
            <span class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center">3</span>
          </div>
          <div class="w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold text-sm cursor-pointer"
               style="background:linear-gradient(135deg,oklch(0.52 0.18 230),oklch(0.55 0.17 180))">李</div>
        </div>
      </div>
    </header>

    <!-- ===== MAIN CONTENT ===== -->
    <main class="pt-16">
      <div class="max-w-screen-2xl mx-auto px-6 py-6">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { LayoutDashboard, Newspaper, FileText, GitBranch, Activity, Settings, Bell } from 'lucide-vue-next'

const route = useRoute()

const navItems = [
  { path: '/', label: '工作台', icon: LayoutDashboard },
  { path: '/briefs', label: '每日简报', icon: Newspaper },
  { path: '/reports', label: '研报中心', icon: FileText },
  { path: '/clusters', label: '聚类分析', icon: GitBranch },
  { path: '/monitor', label: '实时监控', icon: Activity },
  { path: '/settings', label: '系统配置', icon: Settings },
]

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<style scoped>
.tab-btn {
  position: relative;
}
.tab-btn::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: oklch(0.52 0.18 230);
  border-radius: 1px 1px 0 0;
  transform: scaleX(0);
  transition: transform 200ms ease;
}
.tab-btn.active::after,
.tab-btn:hover::after {
  transform: scaleX(1);
}
</style>
