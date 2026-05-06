<template>
  <div class="articles">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索标题或内容" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="filters.source" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="s in sources" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="articles" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" min-width="300" show-overflow-tooltip />
        <el-table-column prop="source" label="来源" width="120" />
        <el-table-column prop="author" label="作者" width="150" show-overflow-tooltip />
        <el-table-column prop="published_at" label="发布时间" width="120">
          <template #default="{ row }">
            {{ formatDate(row.published_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewArticle(row)">查看</el-button>
            <el-button type="danger" link @click="deleteArticle(row)">删除</el-button>
          </template>
        </el-table-column>
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

    <el-dialog v-model="dialogVisible" title="论文详情" width="70%" top="5vh">
      <div v-if="currentArticle" class="article-detail">
        <h2>{{ currentArticle.title }}</h2>
        <div class="meta">
          <el-tag>{{ currentArticle.source }}</el-tag>
          <span class="author">{{ currentArticle.author }}</span>
          <span class="date">{{ formatDate(currentArticle.published_at) }}</span>
        </div>
        <div class="content">
          <p v-if="currentArticle.summary"><strong>摘要：</strong>{{ currentArticle.summary }}</p>
          <p v-if="currentArticle.content"><strong>内容：</strong>{{ currentArticle.content }}</p>
        </div>
        <div v-if="currentArticle.url" class="actions">
          <el-button type="primary" @click="openUrl(currentArticle.url)">
            <el-icon><Link /></el-icon>
            访问原文
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { articleApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Link } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const articles = ref([])
const sources = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const currentArticle = ref(null)

const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0
})

const filters = ref({
  keyword: '',
  source: ''
})

const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD')
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.page_size
    }
    if (filters.value.keyword) params.keyword = filters.value.keyword
    if (filters.value.source) params.source = filters.value.source

    const res = await articleApi.getList(params)
    articles.value = res.items
    pagination.value.total = res.total
  } catch (error) {
    console.error('Failed to fetch articles:', error)
  } finally {
    loading.value = false
  }
}

const fetchSources = async () => {
  try {
    const res = await articleApi.getSources()
    sources.value = res.sources || []
  } catch (error) {
    console.error('Failed to fetch sources:', error)
  }
}

const resetFilters = () => {
  filters.value = { keyword: '', source: '' }
  pagination.value.page = 1
  fetchData()
}

const viewArticle = (article) => {
  currentArticle.value = article
  dialogVisible.value = true
}

const deleteArticle = async (article) => {
  try {
    await ElMessageBox.confirm('确定要删除这篇论文吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await articleApi.delete(article.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const openUrl = (url) => {
  if (url) {
    window.open(url, '_blank')
  }
}

onMounted(() => {
  fetchData()
  fetchSources()
})
</script>

<style scoped>
.articles {
  width: 100%;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.table-card {
  border-radius: 12px;
}

.article-detail h2 {
  margin-bottom: 16px;
  color: #333;
}

.meta {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.meta .author,
.meta .date {
  color: #666;
  font-size: 14px;
}

.content {
  line-height: 1.8;
  color: #444;
  max-height: 60vh;
  overflow-y: auto;
}

.content p {
  margin-bottom: 16px;
}

.actions {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}
</style>
