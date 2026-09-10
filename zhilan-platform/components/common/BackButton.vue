<template>
  <div class="flex items-center gap-3 mb-1">
    <button class="back-btn" @click="$emit('back')">
      <ArrowLeft class="w-4 h-4" />
      {{ label }}
    </button>
    <span class="text-xs text-slate-300">|</span>
    <span class="text-xs text-slate-500">{{ subLabel }}</span>
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft } from 'lucide-vue-next'

defineProps<{
  label: string
  subLabel?: string
}>()

defineEmits<{ back: [] }>()
</script>

<style scoped>
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: oklch(0.38 0.015 260);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 150ms;
  border: none;
  background: none;
  padding: 0;
}
.back-btn:hover {
  color: oklch(0.52 0.18 230);
}
</style>
