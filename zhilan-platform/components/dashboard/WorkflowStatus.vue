<template>
  <div class="card p-5">
    <h2 class="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
      <Workflow class="w-4 h-4" style="color:oklch(0.52 0.17 160)" />
      工作流状态
    </h2>
    <!-- Group 1: done steps -->
    <div class="flex items-center gap-3 p-2.5 rounded-lg mb-2" style="background:oklch(0.52 0.17 160/0.04)">
      <template v-for="(step, idx) in stepGroup1" :key="step.label">
        <div class="flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold"
             style="background:oklch(0.52 0.17 160);color:#fff">✓</div>
        <span class="text-sm font-medium text-slate-700">{{ step.label }}</span>
        <span v-if="idx < stepGroup1.length - 1" class="text-sm text-slate-500">→</span>
      </template>
    </div>
    <!-- Group 2: in-progress / pending steps -->
    <div class="flex items-center gap-3 p-2.5 rounded-lg" style="background:oklch(0.65 0.18 80/0.04)">
      <template v-for="(step, idx) in stepGroup2" :key="step.label">
        <div v-if="step.status === 'running'"
             class="flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold"
             style="background:oklch(0.65 0.18 80);color:#fff">⟳</div>
        <div v-else
             class="flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold border-2 border-dashed"
             style="border-color:oklch(0.82 0.01 260);color:oklch(0.55 0.01 260)">⏳</div>
        <span class="text-sm font-medium" :class="step.status === 'running' ? 'text-slate-700' : 'text-slate-500'">
          {{ step.label }}
        </span>
        <span v-if="idx < stepGroup2.length - 1" class="text-sm text-slate-500">→</span>
      </template>
    </div>
    <!-- Progress Bar -->
    <div class="mt-4 p-3 rounded-lg" style="background:oklch(0.52 0.18 230/0.04)">
      <div class="flex justify-between text-xs mb-1">
        <span class="font-medium text-slate-700">当前{{ progress.currentStage }}进度</span>
        <span class="text-slate-500">{{ progress.percentage }}%</span>
      </div>
      <div class="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
        <div class="h-full rounded-full transition-all duration-700"
             :style="{ width: progress.percentage + '%', background: 'linear-gradient(90deg,oklch(0.52 0.18 230),oklch(0.55 0.16 200))' }"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Workflow } from 'lucide-vue-next'
import type { WorkflowStep, WorkflowProgress } from '~/types'

defineProps<{
  stepGroup1: WorkflowStep[]
  stepGroup2: WorkflowStep[]
  progress: WorkflowProgress
}>()
</script>
