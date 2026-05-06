<template>
  <div class="statistics">
    <el-row :gutter="20" class="filter-row">
      <el-col :span="24">
        <el-card class="filter-card">
          <el-form :inline="true" :model="filters">
            <el-form-item label="统计周期">
              <el-select v-model="filters.period" style="width: 120px">
                <el-option label="日" value="daily" />
                <el-option label="周" value="weekly" />
                <el-option label="月" value="monthly" />
                <el-option label="年" value="yearly" />
              </el-select>
            </el-form-item>
            <el-form-item label="最小震级">
              <el-input-number v-model="filters.min_magnitude" :min="0" :max="10" :step="0.5" style="width: 120px" />
            </el-form-item>
            <el-form-item label="区域">
              <el-input v-model="filters.region" placeholder="筛选区域" clearable style="width: 150px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="fetchStats">查询</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" class="stats-tabs">
      <el-tab-pane label="地震活动统计" name="earthquake">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>地震频次趋势</span>
              </template>
              <div ref="trendChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>震级分布</span>
              </template>
              <div ref="magnitudeChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>深度分布</span>
              </template>
              <div ref="depthChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>区域分布 Top 10</span>
              </template>
              <div ref="regionChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>
        <el-row style="margin-top: 20px">
          <el-col :span="24">
            <el-card class="summary-card">
              <template #header>
                <span>统计摘要</span>
              </template>
              <el-descriptions :column="4" border>
                <el-descriptions-item label="统计周期">{{ eqStats.period }}</el-descriptions-item>
                <el-descriptions-item label="地震总数">{{ eqStats.total_count }}</el-descriptions-item>
                <el-descriptions-item label="最大震级">M{{ eqStats.summary?.max_magnitude || 0 }}</el-descriptions-item>
                <el-descriptions-item label="平均震级">{{ eqStats.summary?.avg_magnitude?.toFixed(2) || 0 }}</el-descriptions-item>
                <el-descriptions-item label="最深深度">{{ eqStats.summary?.max_depth?.toFixed(1) || 0 }} km</el-descriptions-item>
                <el-descriptions-item label="平均深度">{{ eqStats.summary?.avg_depth?.toFixed(1) || 0 }} km</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="学术研究统计" name="academic">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card class="chart-card">
              <template #header>
                <span>论文发表趋势</span>
              </template>
              <div ref="paperTrendChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="chart-card">
              <template #header>
                <span>论文来源分布</span>
              </template>
              <div ref="paperSourceChartRef" class="chart-container"></div>
            </el-card>
          </el-col>
        </el-row>
        <el-row style="margin-top: 20px">
          <el-col :span="24">
            <el-card class="summary-card">
              <template #header>
                <span>学术统计摘要</span>
              </template>
              <el-descriptions :column="3" border>
                <el-descriptions-item label="论文总数">{{ acaStats.total_papers || 0 }}</el-descriptions-item>
                <el-descriptions-item label="时间范围">{{ acaStats.start_year }} - {{ acaStats.end_year }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="爬虫性能" name="crawl">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="mini-stat-card">
              <div class="stat-value">{{ crawlStats.total_runs || 0 }}</div>
              <div class="stat-label">总运行次数</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="mini-stat-card">
              <div class="stat-value success">{{ crawlStats.success_rate || 0 }}%</div>
              <div class="stat-label">成功率</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="mini-stat-card">
              <div class="stat-value">{{ crawlStats.total_articles || 0 }}</div>
              <div class="stat-label">采集文章数</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="mini-stat-card">
              <div class="stat-value">{{ Object.keys(crawlStats.by_source || {}).length }}</div>
              <div class="stat-label">活跃数据源</div>
            </el-card>
          </el-col>
        </el-row>
        <el-row style="margin-top: 20px">
          <el-col :span="24">
            <el-card>
              <template #header>
                <span>各数据源表现</span>
              </template>
              <el-table :data="crawlSourceData" stripe>
                <el-table-column prop="name" label="数据源" />
                <el-table-column prop="runs" label="运行次数" width="100" />
                <el-table-column prop="success" label="成功次数" width="100" />
                <el-table-column prop="articles" label="采集数量" width="100" />
                <el-table-column label="成功率" width="120">
                  <template #default="{ row }">
                    {{ row.runs > 0 ? ((row.success / row.runs) * 100).toFixed(1) : 0 }}%
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { statisticsApi } from '@/api'
import * as echarts from 'echarts'

const activeTab = ref('earthquake')
const filters = ref({
  period: 'monthly',
  min_magnitude: 4.0,
  region: ''
})

const eqStats = ref({})
const acaStats = ref({})
const crawlStats = ref({})

const trendChartRef = ref(null)
const magnitudeChartRef = ref(null)
const depthChartRef = ref(null)
const regionChartRef = ref(null)
const paperTrendChartRef = ref(null)
const paperSourceChartRef = ref(null)

let trendChart = null
let magnitudeChart = null
let depthChart = null
let regionChart = null
let paperTrendChart = null
let paperSourceChart = null

const crawlSourceData = computed(() => {
  const data = crawlStats.value.by_source || {}
  return Object.entries(data).map(([name, stats]) => ({ name, ...stats }))
})

const fetchEarthquakeStats = async () => {
  try {
    eqStats.value = await statisticsApi.getEarthquakeStats({
      period: filters.value.period,
      min_magnitude: filters.value.min_magnitude,
      region: filters.value.region || undefined
    })
    updateEarthquakeCharts()
  } catch (error) {
    console.error('Failed to fetch earthquake stats:', error)
  }
}

const fetchAcademicStats = async () => {
  try {
    acaStats.value = await statisticsApi.getAcademicStats()
    updateAcademicCharts()
  } catch (error) {
    console.error('Failed to fetch academic stats:', error)
  }
}

const fetchCrawlStats = async () => {
  try {
    crawlStats.value = await statisticsApi.getCrawlStats({ days: 30 })
  } catch (error) {
    console.error('Failed to fetch crawl stats:', error)
  }
}

const updateEarthquakeCharts = () => {
  nextTick(() => {
    if (!trendChartRef.value || !magnitudeChartRef.value || !depthChartRef.value || !regionChartRef.value) return

    if (!trendChart) trendChart = echarts.init(trendChartRef.value)
    if (!magnitudeChart) magnitudeChart = echarts.init(magnitudeChartRef.value)
    if (!depthChart) depthChart = echarts.init(depthChartRef.value)
    if (!regionChart) regionChart = echarts.init(regionChartRef.value)

    if (eqStats.value.trend && eqStats.value.trend.length > 0) {
      trendChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: eqStats.value.trend.map(t => t.period) },
        yAxis: [
          { type: 'value', name: '次数', position: 'left' },
          { type: 'value', name: '震级', position: 'right', max: 10 }
        ],
        series: [
          { name: '地震次数', type: 'bar', data: eqStats.value.trend.map(t => t.count), itemStyle: { color: '#5470c6' }, yAxisIndex: 0 },
          { name: '最大震级', type: 'line', data: eqStats.value.trend.map(t => t.max_magnitude), itemStyle: { color: '#ee6666' }, yAxisIndex: 1 }
        ]
      })
    }

    if (eqStats.value.by_magnitude) {
      const data = Object.entries(eqStats.value.by_magnitude)
        .filter(([, value]) => value > 0)
        .map(([name, value]) => ({ name, value }))
      magnitudeChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { bottom: 0 },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          label: { show: true, formatter: '{b}\n{c}', fontSize: 11, lineHeight: 14 },
          labelLine: { show: true, lineStyle: { color: '#999' } },
          data,
          color: ['#67c23a', '#e6a23c', '#f56c6c', '#909399', '#c71585']
        }]
      })
    }

    if (eqStats.value.by_depth) {
      const data = Object.entries(eqStats.value.by_depth)
        .filter(([, value]) => value > 0)
        .map(([name, value]) => ({ name, value }))
      depthChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { bottom: 0 },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          label: { show: true, formatter: '{b}\n{c}', fontSize: 11, lineHeight: 14 },
          labelLine: { show: true, lineStyle: { color: '#999' } },
          data,
          color: ['#4facfe', '#00f2fe', '#667eea']
        }]
      })
    }

    if (eqStats.value.by_region && eqStats.value.by_region.length > 0) {
      const data = eqStats.value.by_region.slice(0, 10)
      regionChart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        xAxis: { type: 'category', data: data.map(d => d.region) },
        yAxis: { type: 'value', name: '次数' },
        series: [{
          type: 'bar',
          data: data.map(d => d.count),
          itemStyle: { color: '#5470c6' }
        }]
      })
    }
  })
}

const updateAcademicCharts = () => {
  nextTick(() => {
    if (!paperTrendChartRef.value || !paperSourceChartRef.value) return

    if (!paperTrendChart) paperTrendChart = echarts.init(paperTrendChartRef.value)
    if (!paperSourceChart) paperSourceChart = echarts.init(paperSourceChartRef.value)

    if (acaStats.value.monthly_trend && acaStats.value.monthly_trend.length > 0) {
      paperTrendChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: acaStats.value.monthly_trend.map(t => t.period) },
        yAxis: { type: 'value', name: '论文数' },
        series: [{
          type: 'line',
          data: acaStats.value.monthly_trend.map(t => t.count),
          itemStyle: { color: '#f093fb' },
          areaStyle: { color: 'rgba(240,147,251,0.2)' }
        }]
      })
    }

    if (acaStats.value.by_source) {
      const data = Object.entries(acaStats.value.by_source)
        .filter(([, value]) => value > 0)
        .map(([name, value]) => ({ name, value }))
      paperSourceChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { bottom: 0 },
        series: [{
          type: 'pie',
          radius: '60%',
          label: { show: true, formatter: '{b}\n{c}', fontSize: 11, lineHeight: 14 },
          labelLine: { show: true, lineStyle: { color: '#999' } },
          data,
          color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
        }]
      })
    }
  })
}

const fetchStats = () => {
  fetchEarthquakeStats()
}

watch(activeTab, (tab) => {
  nextTick(() => {
    if (tab === 'earthquake') {
      if (!trendChart) trendChart = echarts.init(trendChartRef.value)
      if (!magnitudeChart) magnitudeChart = echarts.init(magnitudeChartRef.value)
      if (!depthChart) depthChart = echarts.init(depthChartRef.value)
      if (!regionChart) regionChart = echarts.init(regionChartRef.value)
      fetchEarthquakeStats()
    } else if (tab === 'academic') {
      if (!paperTrendChart) paperTrendChart = echarts.init(paperTrendChartRef.value)
      if (!paperSourceChart) paperSourceChart = echarts.init(paperSourceChartRef.value)
      paperTrendChart?.resize()
      paperSourceChart?.resize()
      fetchAcademicStats()
    } else if (tab === 'crawl') {
      fetchCrawlStats()
    }
  })
})

watch(filters, () => {
  if (activeTab.value === 'earthquake') {
    nextTick(() => {
      fetchEarthquakeStats()
    })
  }
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    fetchEarthquakeStats()
  })

  window.addEventListener('resize', () => {
    trendChart?.resize()
    magnitudeChart?.resize()
    depthChart?.resize()
    regionChart?.resize()
    paperTrendChart?.resize()
    paperSourceChart?.resize()
  })
})
</script>

<style scoped>
.statistics {
  width: 100%;
}

.filter-row {
  margin-bottom: 20px;
}

.filter-card {
  border-radius: 12px;
}

.chart-card {
  border-radius: 12px;
}

.chart-container {
  height: 300px;
}

.summary-card {
  border-radius: 12px;
}

.mini-stat-card {
  border-radius: 12px;
  text-align: center;
  padding: 20px 0;
}

.mini-stat-card .stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.mini-stat-card .stat-value.success {
  color: #67c23a;
}

.mini-stat-card .stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
}

.stats-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 12px;
}
</style>
