<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ECharts } from 'echarts/core'
import { api, type DashboardOverview } from '../api'

echarts.use([BarChart, PieChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

const loading = ref(true)
const data = ref<DashboardOverview | null>(null)
const categoryChartEl = ref<HTMLDivElement | null>(null)
const statusChartEl = ref<HTMLDivElement | null>(null)
const charts: ECharts[] = []

function renderCharts() {
  if (!data.value || !categoryChartEl.value || !statusChartEl.value) return
  const categoryChart = echarts.init(categoryChartEl.value)
  categoryChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 24, right: 18, top: 18, bottom: 24, containLabel: true },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#edf1ee' } } },
    yAxis: { type: 'category', data: data.value.category_distribution.map(item => item.name), axisTick: { show: false }, axisLine: { show: false } },
    series: [{ type: 'bar', data: data.value.category_distribution.map(item => item.value), barWidth: 18, itemStyle: { color: '#3aa878', borderRadius: [0, 6, 6, 0] } }],
  })
  const statusChart = echarts.init(statusChartEl.value)
  statusChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 4 },
    series: [{ type: 'pie', radius: ['48%', '70%'], center: ['50%', '44%'], data: data.value.status_distribution, color: ['#efb84c', '#49b982'], label: { formatter: '{b}\n{c}' } }],
  })
  charts.push(categoryChart, statusChart)
}

function resizeCharts() { charts.forEach(chart => chart.resize()) }
function hoursLabel(value: number | null) { return value === null ? '—' : `${value}h` }

onMounted(async () => {
  try { data.value = await api.getDashboard(); await nextTick(); renderCharts(); window.addEventListener('resize', resizeCharts) }
  finally { loading.value = false }
})
onBeforeUnmount(() => { window.removeEventListener('resize', resizeCharts); charts.forEach(chart => chart.dispose()) })
</script>

<template>
  <div v-loading="loading">
    <div class="page-heading"><div><div class="eyebrow dark">OVERVIEW</div><h1>数据看板</h1><p>了解反馈规模、处理进度与需要优先关注的问题。</p></div></div>
    <template v-if="data">
      <div class="metric-grid">
        <div class="metric-card"><span>反馈总数</span><strong>{{ data.feedback_total }}</strong><small>{{ data.feedback_pending_analysis }} 条待分析</small></div>
        <div class="metric-card warning"><span>待处理问题</span><strong>{{ data.issue_pending }}</strong><small>{{ data.high_severity_pending }} 个高严重度</small></div>
        <div class="metric-card success"><span>已处理问题</span><strong>{{ data.issue_processed }}</strong><small>持续沉淀解决方案</small></div>
        <div class="metric-card"><span>平均解决时间</span><strong>{{ hoursLabel(data.average_resolution_hours) }}</strong><small>从创建至完成处理</small></div>
      </div>
      <div class="chart-grid"><section class="content-card chart-card"><h2>反馈分类分布</h2><div ref="categoryChartEl" class="chart"></div></section><section class="content-card chart-card"><h2>问题处理状态</h2><div ref="statusChartEl" class="chart"></div></section></div>
      <section class="content-card top-issues"><div class="settings-title"><h2>高频问题</h2><span>按关联反馈数量排序</span></div><el-table :data="data.top_issues" empty-text="暂无问题"><el-table-column label="编号" width="90"><template #default="scope">IS-{{ String(scope.row.id).padStart(4, '0') }}</template></el-table-column><el-table-column prop="title" label="问题标题" min-width="300" /><el-table-column prop="category" label="分类" width="140" /><el-table-column prop="priority" label="优先级" width="90" /><el-table-column prop="feedback_count" label="反馈数" width="90" /><el-table-column label="状态" width="100"><template #default="scope"><el-tag :type="scope.row.status === 'processed' ? 'success' : 'warning'">{{ scope.row.status === 'processed' ? '已处理' : '待处理' }}</el-tag></template></el-table-column></el-table></section>
    </template>
  </div>
</template>
