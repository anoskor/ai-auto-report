<template>
  <div>
    <PageHeader title="工作台概览" description="今日数据处理状态与关键指标一览" />

    <!-- Stat Cards -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <StatCard v-for="s in store.stats" :key="s.label" v-bind="s" />
    </div>

    <!-- Mid Section -->
    <div class="grid grid-cols-2 gap-4 mb-6">
      <TopNewsList :items="store.news" @select="goToBrief" />
      <TrendChart />
    </div>

    <!-- Bottom Section -->
    <div class="grid grid-cols-2 gap-4">
      <LatestReports :items="store.latestReports" @select="goToReport" />
      <WorkflowStatus
        :step-group1="store.stepGroup1"
        :step-group2="store.stepGroup2"
        :progress="store.progress" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDashboardStore } from '~/stores/dashboard'
import PageHeader from '~/components/common/PageHeader.vue'
import StatCard from '~/components/common/StatCard.vue'
import TopNewsList from '~/components/dashboard/TopNewsList.vue'
import TrendChart from '~/components/dashboard/TrendChart.vue'
import LatestReports from '~/components/dashboard/LatestReports.vue'
import WorkflowStatus from '~/components/dashboard/WorkflowStatus.vue'

const store = useDashboardStore()
const router = useRouter()

onMounted(() => {
  store.fetchDashboard()
})

function goToBrief(id: number) {
  router.push(`/briefs/${id}`)
}

function goToReport(id: number) {
  router.push(`/reports/${id}`)
}

definePageMeta({ layout: 'default' })
</script>
