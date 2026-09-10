import * as echarts from 'echarts'
import type { TrendDataPoint, ClusterNode, ClusterLink } from '~/types'
import type { SentimentTrendData } from '~/utils/api'

export function useCharts() {
  const initTrendChart = (dom: HTMLElement | null, data?: TrendDataPoint[]) => {
    if (!dom) return
    const chart = echarts.init(dom)
    const points = data || []
    chart.setOption({
      grid: { left: 5, right: 15, top: 10, bottom: 5, containLabel: true },
      xAxis: { type: 'category', data: points.map(p => p.date), axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#94a3b8', fontSize: 11 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f1f5f9' } }, axisLabel: { color: '#94a3b8', fontSize: 11 } },
      series: [{ data: points.map(p => p.count), type: 'line', smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { color: 'oklch(0.52 0.18 230)', width: 2.5 }, itemStyle: { color: 'oklch(0.52 0.18 230)' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'oklch(0.52 0.18 230 / 0.2)' }, { offset: 1, color: 'oklch(0.52 0.18 230 / 0.02)' }]) } }]
    })
    return chart
  }

  const initSentimentChart = (dom: HTMLElement | null, data?: SentimentTrendData) => {
    if (!dom) return
    const chart = echarts.init(dom)
    const labels = data?.labels || []
    const sentiment = data?.sentiment || []
    const heat = data?.heat || []
    const volatility = data?.volatility || []
    chart.setOption({
      grid: { left: 0, right: 5, top: 5, bottom: 0, containLabel: true },
      xAxis: { type: 'category', data: labels, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#94a3b8', fontSize: 10 } },
      yAxis: { type: 'value', min: 30, max: 100, splitLine: { lineStyle: { color: '#f1f5f9' } }, axisLabel: { color: '#94a3b8', fontSize: 10 } },
      series: [
        { name: '情绪', data: sentiment, type: 'line', smooth: true, lineStyle: { color: 'oklch(0.52 0.17 160)', width: 2 }, itemStyle: { color: 'oklch(0.52 0.17 160)' }, symbol: 'none' },
        { name: '热度', data: heat, type: 'line', smooth: true, lineStyle: { color: 'oklch(0.55 0.20 30)', width: 2 }, itemStyle: { color: 'oklch(0.55 0.20 30)' }, symbol: 'none' },
        { name: '波动', data: volatility, type: 'line', smooth: true, lineStyle: { color: 'oklch(0.52 0.18 230)', width: 2, type: 'dashed' }, itemStyle: { color: 'oklch(0.52 0.18 230)' }, symbol: 'none' }
      ]
    })
    return chart
  }

  const initClusterGraph = (dom: HTMLElement | null, graph?: { nodes: ClusterNode[]; links: ClusterLink[] }) => {
    if (!dom) return
    const chart = echarts.init(dom)
    const nodes: ClusterNode[] = graph?.nodes || []
    const links: ClusterLink[] = graph?.links || []
    chart.setOption({
      tooltip: {},
      series: [{
        type: 'graph', layout: 'force', roam: true, draggable: true,
        force: { repulsion: 280, gravity: 0.12, edgeLength: [100, 220] },
        label: {
          show: true, fontSize: 11, color: '#334155', fontWeight: 500,
          formatter: (params: any) => {
            const d = params?.data || {}
            if ((d.symbolSize || 0) < 30) return ''
            const name = d.name || ''
            return name.length > 14 ? name.slice(0, 14) + '…' : name
          }
        },
        edgeSymbol: ['none', 'none'],
        lineStyle: { color: '#cbd5e1', width: 1.5, curveness: 0.2, opacity: 0.7 },
        data: nodes, links,
        categories: [
          { name: '科技', itemStyle: { color: 'oklch(0.52 0.18 230)' } },
          { name: '政策', itemStyle: { color: 'oklch(0.52 0.17 160)' } },
          { name: '其他', itemStyle: { color: 'oklch(0.55 0.20 30)' } }
        ]
      }]
    })
    return chart
  }

  return { initTrendChart, initSentimentChart, initClusterGraph }
}
