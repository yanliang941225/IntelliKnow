<template>
  <div class="datasources">
    <el-card class="toolbar-card">
      <div class="toolbar">
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加数据源
        </el-button>
        <div class="filter">
          <el-select v-model="filterType" placeholder="筛选类型" clearable style="width: 150px">
            <el-option label="学术" value="academic" />
            <el-option label="新闻" value="news" />
            <el-option label="监测" value="monitoring" />
            <el-option label="政府" value="government" />
          </el-select>
        </div>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-table :data="filteredDatasources" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" min-width="150">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.source_type)" size="small">
              {{ row.source_type }}
            </el-tag>
            {{ row.name }}
          </template>
        </el-table-column>
        <el-table-column prop="spider_class" label="爬虫类" width="180" />
        <el-table-column prop="update_interval" label="更新间隔" width="100">
          <template #default="{ row }">
            {{ formatInterval(row.update_interval) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_crawl_at" label="最后爬取" width="160">
          <template #default="{ row }">
            {{ formatTime(row.last_crawl_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="editDatasource(row)">编辑</el-button>
            <el-button type="success" link @click="triggerCrawl(row)" :loading="row.crawling">
              立即爬取
            </el-button>
            <el-button type="warning" link @click="toggleStatus(row)">
              {{ row.enabled ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" link @click="deleteDatasource(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="数据源名称" />
        </el-form-item>
        <el-form-item label="类型" prop="source_type">
          <el-select v-model="form.source_type" placeholder="选择类型">
            <el-option label="学术" value="academic" />
            <el-option label="新闻" value="news" />
            <el-option label="监测" value="monitoring" />
            <el-option label="政府" value="government" />
          </el-select>
        </el-form-item>
        <el-form-item label="爬虫类" prop="spider_class">
          <el-select v-model="form.spider_class" placeholder="选择爬虫">
            <el-option label="USGS Spider" value="USGSSpider" />
            <el-option label="中国地震台网" value="ChinaEarthquakeSpider" />
            <el-option label="EMSC Spider" value="EMSCSpider" />
            <el-option label="arXiv" value="ArxivSeismologySpider" />
            <el-option label="Semantic Scholar" value="SemanticScholarSpider" />
            <el-option label="OpenAlex" value="OpenAlexSpider" />
            <el-option label="应急管理新闻" value="EmergencyNewsSpider" />
          </el-select>
        </el-form-item>
        <el-form-item label="API地址" prop="base_url">
          <el-input v-model="form.base_url" placeholder="API基础地址" />
        </el-form-item>
        <el-form-item label="更新间隔" prop="update_interval">
          <el-input-number v-model="form.update_interval" :min="60" :step="60" />
          <span style="margin-left: 8px; color: #666">秒</span>
        </el-form-item>
        <el-form-item label="速率限制" prop="rate_limit">
          <el-input-number v-model="form.rate_limit" :min="1" :max="60" />
          <span style="margin-left: 8px; color: #666">秒</span>
        </el-form-item>
        <el-form-item label="关键词">
          <el-select v-model="form.keywords" multiple filterable allow-create default-first-option placeholder="输入关键词">
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { datasourceApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const datasources = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('添加数据源')
const filterType = ref('')
const formRef = ref(null)
const editingId = ref(null)

const form = ref({
  name: '',
  source_type: 'academic',
  spider_class: '',
  base_url: '',
  update_interval: 3600,
  rate_limit: 10,
  keywords: [],
  enabled: true
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  source_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  spider_class: [{ required: true, message: '请选择爬虫类', trigger: 'change' }],
  base_url: [{ required: true, message: '请输入API地址', trigger: 'blur' }]
}

const filteredDatasources = computed(() => {
  if (!filterType.value) return datasources.value
  return datasources.value.filter(ds => ds.source_type === filterType.value)
})

const getTypeColor = (type) => {
  const colors = { academic: 'primary', news: 'warning', monitoring: 'success', government: 'info' }
  return colors[type] || 'info'
}

const formatInterval = (seconds) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时`
}

const formatTime = (time) => {
  if (!time) return '从未'
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

const fetchData = async () => {
  loading.value = true
  try {
    datasources.value = await datasourceApi.getList()
  } catch (error) {
    console.error('Failed to fetch datasources:', error)
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  dialogTitle.value = '添加数据源'
  editingId.value = null
  form.value = {
    name: '',
    source_type: 'academic',
    spider_class: '',
    base_url: '',
    update_interval: 3600,
    rate_limit: 10,
    keywords: [],
    enabled: true
  }
  dialogVisible.value = true
}

const editDatasource = (row) => {
  dialogTitle.value = '编辑数据源'
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

const submitForm = async () => {
  try {
    await formRef.value.validate()

    if (editingId.value) {
      await datasourceApi.update(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await datasourceApi.create(form.value)
      ElMessage.success('添加成功')
    }

    dialogVisible.value = false
    fetchData()
  } catch (error) {
    if (error !== false) {
      ElMessage.error('操作失败')
    }
  }
}

const triggerCrawl = async (row) => {
  try {
    await datasourceApi.triggerCrawl(row.id)
    ElMessage.success('爬取任务已触发')
  } catch (error) {
    ElMessage.error('触发失败')
  }
}

const toggleStatus = async (row) => {
  try {
    await datasourceApi.toggle(row.id)
    ElMessage.success(`已${row.enabled ? '禁用' : '启用'}`)
    fetchData()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteDatasource = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个数据源吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await datasourceApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.datasources {
  width: 100%;
}

.toolbar-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-card {
  border-radius: 12px;
}
</style>
