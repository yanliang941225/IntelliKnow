<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon earthquake-icon">
              <el-icon :size="32"><Odometer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.earthquake_count || 0 }}</div>
              <div class="stat-label">地震事件总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon article-icon">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.article_count || 0 }}</div>
              <div class="stat-label">学术论文总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon source-icon">
              <el-icon :size="32"><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.source_count || 0 }}</div>
              <div class="stat-label">数据来源数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon time-icon">
              <el-icon :size="32"><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ currentTime }}</div>
              <div class="stat-label">当前时间</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>地震事件分布</span>
              <el-radio-group v-model="mapPeriod" size="small">
                <el-radio-button value="week">最近一周</el-radio-button>
                <el-radio-button value="month">最近一月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="mapChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>震级分布</span>
          </template>
          <div ref="pieChartRef" class="chart-container-small"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>最近地震事件</span>
          </template>
          <el-table :data="overview.recent_events?.slice(0, 10)" stripe style="width: 100%">
            <el-table-column prop="magnitude" label="震级" width="80">
              <template #default="{ row }">
                <el-tag :type="getMagnitudeType(row.magnitude)" size="small">
                  M{{ row.magnitude }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="location" label="位置" />
            <el-table-column prop="time" label="时间" width="160">
              <template #default="{ row }">
                {{ formatTime(row.time) }}
              </template>
            </el-table-column>
            <el-table-column prop="source" label="来源" width="120" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>最近论文</span>
          </template>
          <el-table :data="overview.recent_articles" stripe style="width: 100%">
            <el-table-column prop="title" label="标题" show-overflow-tooltip />
            <el-table-column prop="source" label="来源" width="120" />
            <el-table-column prop="published_at" label="发布时间" width="120">
              <template #default="{ row }">
                {{ formatDate(row.published_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { statisticsApi } from '@/api'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { Odometer, Document, Connection, Clock } from '@element-plus/icons-vue'

const overview = ref({})
const currentTime = ref('')
const mapPeriod = ref('week')
const mapChartRef = ref(null)
const pieChartRef = ref(null)
let mapChart = null
let pieChart = null
let timeInterval = null
let mapDataLoaded = false

const formatTime = (time) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD')
}

const getMagnitudeType = (mag) => {
  if (mag >= 7) return 'danger'
  if (mag >= 5) return 'warning'
  return 'success'
}

const updateTime = () => {
  currentTime.value = dayjs().format('HH:mm:ss')
}

const fetchOverview = async () => {
  try {
    overview.value = await statisticsApi.getOverview()
    updateCharts()
  } catch (error) {
    console.error('Failed to fetch overview:', error)
  }
}

const fetchEarthquakeStats = async () => {
  try {
    const period = mapPeriod.value === 'week' ? 'daily' : 'monthly'
    const stats = await statisticsApi.getEarthquakeStats({ period })
    updatePieChart(stats.by_magnitude)
  } catch (error) {
    console.error('Failed to fetch earthquake stats:', error)
  }
}

const updateCharts = () => {
  if (!mapChart) return

  const mapData = overview.value.recent_events?.map(e => ({
    name: e.location,
    value: [e.longitude, e.latitude, e.magnitude],
    magnitude: e.magnitude,
    source: e.source,
    depth: e.depth,
    time: e.time
  })) || []

  mapChart.setOption({
    title: { text: '地震分布示意 (仅展示近期数据)' },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const d = params.data
        return `<strong>${d.name}</strong><br/>
                震级: <strong>M${d.magnitude}</strong><br/>
                深度: ${d.depth} km<br/>
                来源: ${d.source}<br/>
                时间: ${d.time ? new Date(d.time).toLocaleString('zh-CN') : 'N/A'}`
      }
    },
    visualMap: { min: 0, max: 10, text: ['高', '低'], calculable: true, left: 'right' },
    geo: {
      map: 'world',
      roam: true,
      emphasis: { label: { show: true } },
      itemStyle: { areaColor: '#e7ebf0', borderColor: '#ccc' }
    },
    series: [{
      type: 'effectScatter',
      coordinateSystem: 'geo',
      data: mapData,
      symbolSize: (val) => Math.max(val[2] * 3, 8),
      showEffectOn: 'render',
      rippleEffect: { brushType: 'stroke', scale: 3 },
      label: {
        show: false,
        formatter: '{b}',
        position: 'right'
      },
      emphasis: {
        label: { show: true }
      }
    }]
  })
}

const loadWorldMap = () => {
  return new Promise((resolve) => {
    if (mapDataLoaded) {
      resolve()
      return
    }
    // Use jsDelivr CDN for better China accessibility
    fetch('https://cdn.jsdelivr.net/npm/echarts@4.9.0/map/json/world.json')
      .then(async response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const contentType = response.headers.get('content-type')
        if (!contentType || !contentType.includes('application/json')) {
          throw new Error('Invalid content type')
        }
        const geoJson = await response.json()
        echarts.registerMap('world', geoJson)
        mapDataLoaded = true
        updateCharts()
        resolve()
      })
      .catch(err => {
        console.error('Failed to load world map, using fallback:', err)
        // Use world map from another CDN as fallback
        fetch('https://unpkg.com/echarts@4.9.0/map/json/world.json')
          .then(r => r.json())
          .then(geoJson => {
            echarts.registerMap('world', geoJson)
            mapDataLoaded = true
            updateCharts()
          })
          .catch(() => {
            // Try one more CDN
            fetch('https://geo.datav.aliyun.com/areas_v3/world.json')
              .then(r => r.json())
              .then(geoJson => {
                echarts.registerMap('world', geoJson)
                mapDataLoaded = true
                updateCharts()
              })
              .catch(e => console.error('All map sources failed:', e))
          })
        resolve()
      })
  })
}

const updatePieChart = (data) => {
  if (!pieChart || !data) return

  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }))

  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {c}' },
      data: chartData,
      color: ['#67c23a', '#e6a23c', '#f56c6c', '#909399', '#c71585']
    }]
  })
}

const initCharts = () => {
  if (mapChartRef.value) {
    mapChart = echarts.init(mapChartRef.value)
  }
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
  }
}

watch(mapPeriod, () => {
  fetchEarthquakeStats()
})

onMounted(async () => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)

  initCharts()
  await loadWorldMap()
  await fetchOverview()
  await fetchEarthquakeStats()

  window.addEventListener('resize', () => {
    mapChart?.resize()
    pieChart?.resize()
  })
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
  mapChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.earthquake-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.article-icon { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.source-icon { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.time-icon { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 400px;
}

.chart-container-small {
  height: 400px;
}
</style>
