/**
 * 统一 API 客户端 — 通过 Nuxt Server 代理转发到 FastAPI 后端
 * 所有请求走 /api/v1/...，由 server/api/v1/[...].ts 代理到 http://localhost:8000/api/v1
 */
import type {
  StatItem, TopNewsItem, TrendDataPoint, WorkflowProgress, WorkflowStep,
  BriefItem, ReportCard, IndustryItem, SentimentData,
  ReportItem, ClusterItem, ClusterNode, ClusterLink,
  AgentStatus, LogEntry, SystemMetric,
  Topic, DataSource, CronConfig, PushChannel
} from '~/types'

const BASE = '/api/v1'

// 后端直连地址（文件下载等需直接访问后端的场景，开发环境默认 8000）
export const BACKEND_ORIGIN = 'http://localhost:8000'

async function get<T>(path: string): Promise<T> {
  return await $fetch<T>(`${BASE}${path}`)
}

async function post<T>(path: string, body?: any): Promise<T> {
  return await $fetch<T>(`${BASE}${path}`, { method: 'POST', body })
}

async function put<T>(path: string, body?: any): Promise<T> {
  return await $fetch<T>(`${BASE}${path}`, { method: 'PUT', body })
}

async function del<T>(path: string): Promise<T> {
  return await $fetch<T>(`${BASE}${path}`, { method: 'DELETE' })
}

// ===== Dashboard =====
export interface WorkflowStatusResponse extends WorkflowProgress {
  stepGroup1: WorkflowStep[]
  stepGroup2: WorkflowStep[]
}

export const dashboardApi = {
  stats: () => get<StatItem[]>('/dashboard/stats'),
  topNews: () => get<TopNewsItem[]>('/dashboard/top-news'),
  trend: () => get<TrendDataPoint[]>('/dashboard/trend'),
  latestReports: () => get<ReportCard[]>('/dashboard/latest-reports'),
  workflowStatus: () => get<WorkflowStatusResponse>('/dashboard/workflow-status'),
}

// ===== Briefs =====
export interface SentimentTrendData {
  labels: string[]
  sentiment: number[]
  heat: number[]
  volatility: number[]
}

export interface BriefsResponse {
  briefs: BriefItem[]
  reportCards: ReportCard[]
  industries: IndustryItem[]
  sentiment: SentimentData
  trendData: SentimentTrendData
}

export const briefsApi = {
  list: () => get<BriefsResponse>('/briefs'),
  detail: (id: number) => get<BriefItem>(`/briefs/${id}`),
}

// ===== Reports =====
export interface ReportsResponse {
  items: ReportItem[]
  total: number
}

export const reportsApi = {
  list: (q?: string) => get<ReportsResponse>(`/reports${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  detail: (id: number) => get<ReportItem>(`/reports/${id}`),
}

// ===== Clusters =====
export interface ClustersResponse {
  items: ClusterItem[]
  total: number
}

export interface ClusterGraph {
  nodes: ClusterNode[]
  links: ClusterLink[]
}

export const clustersApi = {
  list: () => get<ClustersResponse>('/clusters'),
  graph: (topic?: string) => get<ClusterGraph>(topic ? `/clusters/graph?topic=${encodeURIComponent(topic)}` : '/clusters/graph'),
  detail: (id: number) => get<ClusterItem>(`/clusters/${id}`),
}

// ===== Monitor =====
export interface PipelineStep {
  label: string
  status: string
  icon: string
  detail: string
  bgColor: string
  borderColor: string
  textColor: string
}

export interface MonitorStatus {
  isRunning: boolean
  lastCollect: string
  nextCollect: string
  percentage: number
  pipelineSteps: PipelineStep[]
  agents: AgentStatus[]
  logs: LogEntry[]
  metrics: SystemMetric[]
}

export interface LogsResponse {
  items: LogEntry[]
  total: number
  page: number
  size: number
}

export const monitorApi = {
  status: () => get<MonitorStatus>('/monitor/status'),
  agents: () => get<AgentStatus[]>('/monitor/agents'),
  logs: (page = 1, size = 50) => get<LogsResponse>(`/monitor/logs?page=${page}&size=${size}`),
  metrics: () => get<SystemMetric[]>('/monitor/metrics'),
}

// ===== Settings =====
export interface MessageResponse {
  message: string
  success?: boolean
}

export const settingsApi = {
  topics: () => get<Topic[]>('/topics'),
  createTopic: (name: string) => post<Topic>('/topics', { name }),
  deleteTopic: (id: number) => del<MessageResponse>(`/topics/${id}`),
  toggleTopic: (id: number) => put<Topic>(`/topics/${id}/toggle`),
  sources: () => get<DataSource[]>('/sources'),
  toggleSource: (id: number) => put<DataSource>(`/sources/${id}`),
  cron: () => get<CronConfig>('/config/cron'),
  updateCron: (data: Partial<CronConfig>) => put<CronConfig>('/config/cron', data),
  pushChannels: () => get<PushChannel[]>('/config/push'),
  toggleChannel: (id: number) => put<PushChannel>(`/config/push/${id}`),
  collect: () => post<MessageResponse>('/collect'),
}
