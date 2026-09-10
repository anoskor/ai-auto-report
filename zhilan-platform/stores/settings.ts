import { defineStore } from 'pinia'
import type { Topic, DataSource, CronConfig, PushChannel } from '~/types'
import { settingsApi } from '~/utils/api'

export const useSettingsStore = defineStore('settings', () => {
  const topicList = ref<Topic[]>([])
  const sourceList = ref<DataSource[]>([])
  const cron = ref<CronConfig>({ collection: '', reportGeneration: '' })
  const channelList = ref<PushChannel[]>([])
  const newTopicName = ref('')
  const webhookUrl = ref('')
  const loading = ref(false)

  async function fetchSettings() {
    loading.value = true
    try {
      const [t, s, c, p] = await Promise.all([
        settingsApi.topics(),
        settingsApi.sources(),
        settingsApi.cron(),
        settingsApi.pushChannels(),
      ])
      topicList.value = t || []
      sourceList.value = s || []
      if (c) cron.value = c
      channelList.value = p || []
    } catch (e) {
      console.error('[settings] fetch failed:', e)
    } finally {
      loading.value = false
    }
  }

  const addTopic = async () => {
    if (!newTopicName.value.trim()) return
    try {
      const topic = await settingsApi.createTopic(newTopicName.value.trim())
      topicList.value.push(topic)
    } catch (e) {
      console.error('[settings] addTopic failed:', e)
      const colors = ['blue', 'green', 'amber', 'orange', 'purple']
      topicList.value.push({
        id: topicList.value.length + 1,
        name: newTopicName.value.trim(),
        color: colors[topicList.value.length % colors.length],
        active: true
      })
    }
    newTopicName.value = ''
  }

  const removeTopic = async (id: number) => {
    try {
      await settingsApi.deleteTopic(id)
    } catch (e) {
      console.error('[settings] removeTopic failed:', e)
    }
    topicList.value = topicList.value.filter(t => t.id !== id)
  }

  const toggleTopic = async (id: number) => {
    try {
      const updated = await settingsApi.toggleTopic(id)
      const idx = topicList.value.findIndex(t => t.id === id)
      if (idx >= 0) topicList.value[idx] = updated
    } catch (e) {
      const topic = topicList.value.find(t => t.id === id)
      if (topic) topic.active = !topic.active
    }
  }

  const toggleSource = async (id: number) => {
    try {
      const updated = await settingsApi.toggleSource(id)
      const idx = sourceList.value.findIndex(s => s.id === id)
      if (idx >= 0) sourceList.value[idx] = updated
    } catch (e) {
      const source = sourceList.value.find(s => s.id === id)
      if (source) source.enabled = !source.enabled
    }
  }

  const toggleChannel = async (id: number) => {
    try {
      const updated = await settingsApi.toggleChannel(id)
      const idx = channelList.value.findIndex(c => c.id === id)
      if (idx >= 0) channelList.value[idx] = updated
    } catch (e) {
      const channel = channelList.value.find(c => c.id === id)
      if (channel) channel.enabled = !channel.enabled
    }
  }

  const saveCron = async () => {
    try {
      cron.value = await settingsApi.updateCron(cron.value)
    } catch (e) {
      console.error('[settings] saveCron failed:', e)
    }
  }

  return {
    topicList, sourceList, cron, channelList, newTopicName, webhookUrl, loading,
    fetchSettings, addTopic, removeTopic, toggleTopic, toggleSource, toggleChannel, saveCron
  }
})
