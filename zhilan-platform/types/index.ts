// ===== Dashboard Types =====
export interface StatItem {
  label: string
  value: string | number
  changeLabel: string
  changeType: 'up' | 'down' | 'neutral'
  icon: string
  color: string
}

export interface TopNewsItem {
  id: number
  title: string
  time: string
  category: string
}

export interface TrendDataPoint {
  date: string
  count: number
}

export interface WorkflowStep {
  label: string
  status: 'done' | 'running' | 'pending'
  detail: string
}

export interface WorkflowProgress {
  currentStage: string
  percentage: number
}

// ===== Briefs Types =====
export interface BriefItem {
  id: number
  title: string
  summary: string
  time: string
  category: string
  rating: number
  articleCount: number
  content: string
  relatedArticleCount: number
  relatedReportCount: number
  relatedReports: { id: number; title: string }[]
}

export interface ReportCard {
  id: number
  title: string
  sections: string[]
  summary: string
  source: string
  time: string
  passRate: string
}

export interface IndustryItem {
  name: string
  tags: string[]
}

export interface SentimentData {
  sentiment: number
  heat: number
  volatility: number
}

// ===== Reports Types =====
export interface ReportItem {
  id: number
  title: string
  time: string
  sections: string[]
  summary: string
  articleCount: number
  passRate: string
  background: string
  statusContent: string
  trendShort: string
  trendLong: string
  risk1: string
  risk1desc: string
  risk2: string
  risk2desc: string
  sources: { title: string; url: string; source?: string }[]
  keyData: { label: string; value: string; change: string }[]
}

// ===== Clusters Types =====
export interface ClusterNode {
  id: string
  name: string
  symbolSize: number
  category: number
  itemStyle?: { color: string }
}

export interface ClusterLink {
  source: string
  target: string
}

export interface ClusterItem {
  id: number
  title: string
  articleCount: number
  timeSpan: string
  rating: number
  importanceScore?: number
  keywords: string[]
  timeline: TimelineEvent[]
  articles: ArticleItem[]
}

export interface TimelineEvent {
  time: string
  title: string
  description: string
}

export interface ArticleItem {
  title: string
  source: string
  date: string
}

// ===== Monitor Types =====
export interface AgentStatus {
  name: string
  icon: string
  status: 'running' | 'done' | 'idle'
  detail: string
  statusText: string
  color: string
}

export interface LogEntry {
  time: string
  level: 'INFO' | 'WARN' | 'ERROR'
  message: string
}

export interface SystemMetric {
  label: string
  value: string
  subValue?: string
  percentage: number
  color: string
}

// ===== Settings Types =====
export interface Topic {
  id: number
  name: string
  color: string
  active: boolean
}

export interface DataSource {
  id: number
  name: string
  description: string
  enabled: boolean
}

export interface CronConfig {
  collection: string
  reportGeneration: string
}

export interface PushChannel {
  id: number
  name: string
  description: string
  enabled: boolean
  webhookUrl?: string
}
