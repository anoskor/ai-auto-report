<template>
  <div class="mb-6">
    <h1 class="text-2xl font-bold text-slate-800">{{ title }}</h1>
    <p v-if="description" class="text-sm text-slate-500 mt-0.5">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>
