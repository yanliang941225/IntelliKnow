<template>
  <div class="earthquakes">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="最小震级">
          <el-input-number v-model="filters.min_magnitude" :min="0" :max="10" :step="0.1" />
        </el-form-item>
        <el-form-item label="区域">
          <el-input v-model="filters.region" placeholder="如: Japan, China" clearable />
        </el-form-item>
        <el-form-item label="数据来源">
          <el-select v-model="filters.source" placeholder="全部" clearable>
            <el-option label="USGS" value="USGS" />
            <el-option label="中国地震台网" value="中国地震台网" />
            <el-option label="EMSC" value="EMSC" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="earthquakes" v-loading="loading" stripe>
        <el-table-column prop="event_id" label="事件ID" width="120" />
        <el-table-column prop="magnitude" label="震级" width="100">
          <template #default="{ row }">
            <el-tag :type="getMagnitudeType(row.magnitude)" size="large">
              M{{ row.magnitude }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" min-width="200" />
        <el-table-column prop="region" label="区域" width="120" />
        <el-table-column prop="depth" label="深度(km)" width="100">
          <template #default="{ row }">
            {{ row.depth?.toFixed(1) || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="latitude" label="纬度" width="100">
          <template #default="{ row }">
            {{ row.latitude?.toFixed(4) || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="longitude" label="经度" width="100">
          <template #default="{ row }">
            {{ row.longitude?.toFixed(4) || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="time" label="发震时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.time) }}
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="120" />
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
        style="margin-top: 20px; justify-content: center"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { earthquakeApi } from '@/api'
import dayjs from 'dayjs'

const earthquakes = ref([])
const loading = ref(false)
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})
const filters = ref({
  min_magnitude: 3.0,
  region: '',
  source: ''
})

const formatTime = (time) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

const getMagnitudeType = (mag) => {
  if (mag >= 7) return 'danger'
  if (mag >= 5) return 'warning'
  return 'success'
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      min_magnitude: filters.value.min_magnitude
    }
    if (filters.value.region) params.region = filters.value.region
    if (filters.value.source) params.source = filters.value.source

    const res = await earthquakeApi.getList(params)
    earthquakes.value = res.items
    pagination.value.total = res.total
  } catch (error) {
    console.error('Failed to fetch earthquakes:', error)
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.value = {
    min_magnitude: 3.0,
    region: '',
    source: ''
  }
  pagination.value.page = 1
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.earthquakes {
  width: 100%;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.table-card {
  border-radius: 12px;
}
</style>
