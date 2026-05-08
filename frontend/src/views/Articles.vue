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
          <el-button type="primary" @click="fetchData">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table :data="articles" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" min-width="300" show-overflow-tooltip />
        <el-table-column prop="source" label="来源" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.source }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" width="150" show-overflow-tooltip />
        <el-table-column prop="published_at" label="发布时间" width="120">
          <template #default="{ row }">
            <span class="date-cell">{{ formatDate(row.published_at) }}</span>
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

    <el-dialog
      v-model="dialogVisible"
      :title="currentArticle?.title_zh || currentArticle?.title || '论文详情'"
      width="75%"
      top="3vh"
      class="article-dialog"
      destroy-on-close
    >
      <div v-if="currentArticle" class="article-detail">
        <!-- Title Section -->
        <div class="title-section">
          <h2 class="article-title">{{ currentArticle.title }}</h2>
          <h2 v-if="currentArticle.title_zh" class="article-title-zh">{{ currentArticle.title_zh }}</h2>
        </div>

        <!-- Meta Info -->
        <div class="meta-bar">
          <div class="meta-left">
            <el-tag type="primary" effect="light">{{ currentArticle.source }}</el-tag>
            <span class="meta-item">
              <el-icon><User /></el-icon>
              {{ currentArticle.author || '未知作者' }}
            </span>
            <span class="meta-item">
              <el-icon><Calendar /></el-icon>
              {{ formatDate(currentArticle.published_at) }}
            </span>
          </div>
          <div class="meta-right">
            <el-button
              v-if="currentArticle.url"
              type="primary"
              size="small"
              @click="openUrl(currentArticle.url)"
            >
              <el-icon><Link /></el-icon>
              访问原文
            </el-button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="translating" class="loading-state">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>翻译加载中...</span>
        </div>

        <!-- Content Tabs - Load translations on tab switch -->
        <el-tabs v-if="currentArticle" class="content-tabs" v-model="activeTab" @tab-change="handleTabChange">
          <el-tab-pane label="原文" name="original">
            <div class="content-body">
              <!-- Only show summary if content is same as summary or content doesn't exist -->
              <div class="section-block" v-if="currentArticle.summary && (!currentArticle.content || currentArticle.content === currentArticle.summary)">
                <h4><el-icon><Document /></el-icon> 摘要</h4>
                <p class="text-content">{{ currentArticle.summary }}</p>
              </div>
              <!-- Show summary separately if content is different -->
              <div class="section-block" v-if="currentArticle.summary && currentArticle.content && currentArticle.content !== currentArticle.summary">
                <h4><el-icon><Document /></el-icon> 摘要</h4>
                <p class="text-content">{{ currentArticle.summary }}</p>
              </div>
              <!-- Show full content only if it's different from summary -->
              <div class="section-block" v-if="currentArticle.content && currentArticle.content !== currentArticle.summary">
                <h4><el-icon><Reading /></el-icon> 全文</h4>
                <p class="text-content">{{ currentArticle.content }}</p>
              </div>
              <!-- Show message if no content -->
              <div v-if="!currentArticle.summary && !currentArticle.content" class="empty-content">
                暂无内容
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane
            v-if="currentArticle.summary_zh || currentArticle.content_zh"
            label="中文翻译"
            name="chinese"
          >
            <div class="content-body translation-body">
              <div class="section-block" v-if="currentArticle.summary_zh && (!currentArticle.content_zh || currentArticle.content_zh === currentArticle.summary_zh)">
                <h4>
                  <el-icon><Document /></el-icon> 摘要
                  <el-tag size="small" type="success" class="translated-tag">翻译</el-tag>
                </h4>
                <p class="text-content">{{ currentArticle.summary_zh }}</p>
              </div>
              <div class="section-block" v-if="currentArticle.summary_zh && currentArticle.content_zh && currentArticle.content_zh !== currentArticle.summary_zh">
                <h4>
                  <el-icon><Document /></el-icon> 摘要
                  <el-tag size="small" type="success" class="translated-tag">翻译</el-tag>
                </h4>
                <p class="text-content">{{ currentArticle.summary_zh }}</p>
              </div>
              <div class="section-block full-content" v-if="currentArticle.content_zh && currentArticle.content_zh !== currentArticle.summary_zh">
                <h4>
                  <el-icon><Reading /></el-icon> 全文
                  <el-tag size="small" type="success" class="translated-tag">翻译</el-tag>
                </h4>
                <p class="text-content">{{ currentArticle.content_zh }}</p>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane
            v-if="!currentArticle.summary_zh && !currentArticle.content_zh"
            label="中文翻译"
            name="chinese"
            disabled
          >
            <template #label>
              <span>中文翻译 <el-tag size="small" type="info">无需翻译</el-tag></span>
            </template>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { articleApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Link, User, Calendar, Document, Reading, Loading } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const articles = ref([])
const sources = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const currentArticle = ref(null)
const translating = ref(false)
const activeTab = ref('original')

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
  currentArticle.value = { ...article, summary_zh: null, content_zh: null }
  dialogVisible.value = true
  activeTab.value = 'original'
}

const loadTranslations = async () => {
  if (currentArticle.value.summary_zh || currentArticle.value.content_zh) return

  translating.value = true
  try {
    const res = await articleApi.translateContent(currentArticle.value.id)
    if (res.summary_zh) currentArticle.value.summary_zh = res.summary_zh
    if (res.content_zh) currentArticle.value.content_zh = res.content_zh
  } catch (error) {
    console.error('Failed to fetch translation:', error)
  } finally {
    translating.value = false
  }
}

const handleTabChange = (tabName) => {
  if (tabName === 'chinese') {
    loadTranslations()
  }
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
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.table-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.date-cell {
  color: #909399;
  font-size: 13px;
}

/* Dialog Styles */
.article-detail {
  max-height: 75vh;
  overflow-y: auto;
}

.title-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f2f5;
}

.article-title {
  font-size: 22px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.article-title-zh {
  font-size: 18px;
  font-weight: 500;
  color: #409eff;
  margin: 0;
  line-height: 1.4;
}

.meta-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #f0f2f5 100%);
  border-radius: 10px;
  margin-bottom: 20px;
}

.meta-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
  font-size: 14px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: #909399;
  font-size: 15px;
}

.loading-state .el-icon {
  font-size: 20px;
  color: #409eff;
}

.content-tabs {
  margin-top: 16px;
}

.content-body {
  padding: 8px 4px;
}

.translation-body :deep(.el-tabs__item) {
  color: #67c23a;
}

.section-block {
  margin-bottom: 24px;
  padding: 20px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.section-block:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.section-block h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 1px dashed #e4e7ed;
  color: #303133;
  font-size: 15px;
  font-weight: 600;
}

.section-block h4 .el-icon {
  color: #409eff;
}

.translated-tag {
  margin-left: 8px;
}

.text-content {
  color: #606266;
  font-size: 14px;
  line-height: 1.9;
  text-align: justify;
  word-break: break-word;
  max-height: none;
  overflow: visible;
  margin: 0;
}

.empty-content {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
  font-size: 14px;
}

/* Translation section styling */
.translation-body .section-block {
  background: linear-gradient(135deg, #f0f9eb 0%, #e8f5e1 100%);
  border-color: #c2e7b0;
}

.translation-body .section-block h4 {
  color: #2d5016;
}

.translation-body .section-block h4 .el-icon {
  color: #67c23a;
}

.translation-body .text-content {
  color: #3a5a1c;
}

/* Dialog global styles */
:deep(.article-dialog .el-dialog__header) {
  padding: 16px 20px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  margin-right: 0;
}

:deep(.article-dialog .el-dialog__title) {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

:deep(.article-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: #fff;
}

:deep(.article-dialog .el-dialog__body) {
  padding: 20px 24px;
}

/* Scrollbar styling */
.article-detail::-webkit-scrollbar {
  width: 6px;
}

.article-detail::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.article-detail::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.article-detail::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
