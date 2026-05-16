<template>
  <div class="novel-list-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-container">
        <div class="header-content">
          <h1 class="page-title">我的小说</h1>
          <p class="page-subtitle">管理您创作的所有小说</p>
        </div>
        <a-button type="primary" size="large" @click="goToCreate" class="create-btn">
          <template #icon><PlusOutlined /></template>
          创建新小说
        </a-button>
      </div>
    </div>

    <div class="container">
      <!-- 搜索筛选栏 -->
      <div class="filter-bar">
        <div class="filter-left">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索小说标题..."
            style="width: 280px"
            @search="handleSearch"
            allow-clear
            class="search-input"
          >
            <template #prefix><SearchOutlined class="search-icon" /></template>
          </a-input-search>

          <a-select
            v-model:value="statusFilter"
            placeholder="全部状态"
            style="width: 120px"
            allow-clear
            @change="loadData"
            class="status-select"
          >
            <a-select-option v-for="opt in NOVEL_STATUS_OPTIONS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </a-select-option>
          </a-select>
        </div>
        <div class="filter-right">
          <span class="total-count">共 {{ pagination.total }} 部小说</span>
        </div>
      </div>

      <!-- 表格 -->
      <a-card :bordered="false" class="table-card">
        <a-table
          :columns="columns"
          :data-source="dataSource"
          :loading="loading"
          :pagination="pagination"
          @change="handleTableChange"
          row-key="id"
          class="novel-table"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'title'">
              <div class="title-cell" @click="viewNovel(record)">
                <div class="main-title">{{ record.title || '-' }}</div>
              </div>
            </template>

            <template v-else-if="column.key === 'genre'">
              <a-tag :color="GENRE_COLOR_MAP[record.genre] || 'default'">
                {{ getGenreLabel(record.genre) }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'progress'">
              <span class="progress-text">
                {{ record.currentChapterNumber || 0 }} 章 / {{ formatWordCount(record.totalWordCount || 0) }}
              </span>
            </template>

            <template v-else-if="column.key === 'status'">
              <span :class="['status-badge', `status-${record.status}`]">
                <span class="status-dot"></span>
                {{ NOVEL_STATUS_TEXT_MAP[record.status] || record.status }}
              </span>
            </template>

            <template v-else-if="column.key === 'createTime'">
              <span class="time-text">{{ formatDate(record.createTime) }}</span>
            </template>

            <template v-else-if="column.key === 'action'">
              <div class="action-group">
                <a-button type="link" size="small" @click="viewNovel(record)" class="action-btn">
                  <EyeOutlined />
                  详情
                </a-button>
                <a-button type="link" size="small" @click="writeNovel(record)" class="action-btn">
                  <EditOutlined />
                  写作
                </a-button>
                <a-popconfirm
                  title="确定要删除这部小说吗?"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleDelete(record)"
                >
                  <a-button type="link" size="small" danger class="action-btn">
                    <DeleteOutlined />
                    删除
                  </a-button>
                </a-popconfirm>
              </div>
            </template>
          </template>

          <template #emptyText>
            <div class="empty-state">
              <BookOutlined class="empty-icon" />
              <p class="empty-title">暂无小说</p>
              <p class="empty-desc">创建您的第一部小说吧</p>
              <a-button type="primary" @click="goToCreate">
                <PlusOutlined />
                创建新小说
              </a-button>
            </div>
          </template>
        </a-table>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  BookOutlined,
} from '@ant-design/icons-vue'
import { listNovel, deleteNovel } from '@/api/novelController'
import { NOVEL_STATUS_TEXT_MAP, NOVEL_STATUS_OPTIONS, GENRE_OPTIONS, GENRE_COLOR_MAP } from '@/constants/novel'
import { formatWordCount } from '@/utils/novel'
import dayjs from 'dayjs'

const router = useRouter()

const searchKeyword = ref('')
const statusFilter = ref('')
const loading = ref(false)
const dataSource = ref<API.NovelVO[]>([])
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

const columns = [
  { title: '书名', key: 'title', dataIndex: 'title', width: 220, ellipsis: true },
  { title: '题材', key: 'genre', width: 100 },
  { title: '进度', key: 'progress', width: 160 },
  { title: '状态', key: 'status', width: 100 },
  { title: '创建时间', key: 'createTime', width: 160 },
  { title: '操作', key: 'action', width: 200 },
]

const getGenreLabel = (genre: string) => {
  return GENRE_OPTIONS.find((g) => g.value === genre)?.label || genre
}

const formatDate = (date: string) => {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await listNovel({
      page: pagination.value.current,
      pageSize: pagination.value.pageSize,
    })
    if (res.data.code === 0 && res.data.data) {
      const data = res.data.data as any
      dataSource.value = data.records || []
      pagination.value.total = data.total || 0
    }
  } catch (e) {
    console.error('加载小说列表失败:', e)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.current = 1
  loadData()
}

const handleTableChange = (pag: any) => {
  pagination.value.current = pag.current
  pagination.value.pageSize = pag.pageSize
  loadData()
}

const goToCreate = () => router.push('/novel/create')
const viewNovel = (record: API.NovelVO) => router.push(`/novel/${record.id}`)
const writeNovel = (record: API.NovelVO) => router.push(`/novel/${record.id}/write`)

const handleDelete = async (record: API.NovelVO) => {
  try {
    const res = await deleteNovel(record.id!)
    if (res.data.code === 0) {
      message.success('删除成功')
      loadData()
    } else {
      message.error(res.data.message || '删除失败')
    }
  } catch (e) {
    message.error('删除失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.novel-list-page {
  min-height: calc(100vh - 64px);
  background: var(--bg-secondary);
}

.page-header {
  background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
  padding: 40px 0 32px;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-family: 'Outfit', sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px;
}

.page-subtitle {
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  font-size: 14px;
}

.create-btn {
  height: 40px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(8px);
  font-weight: 600;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-left {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.total-count {
  color: #6B7280;
  font-size: 14px;
}

.table-card {
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.title-cell {
  cursor: pointer;
}

.title-cell:hover .main-title {
  color: #22C55E;
}

.main-title {
  font-weight: 600;
  color: #0F172A;
  transition: color 0.2s;
}

.progress-text {
  color: #374151;
  font-size: 13px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.status-ongoing .status-dot { background: #3B82F6; }
.status-completed .status-dot { background: #22C55E; }
.status-paused .status-dot { background: #F59E0B; }

.action-group {
  display: flex;
  gap: 4px;
}

.empty-state {
  padding: 48px 0;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: #D1D5DB;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.empty-desc {
  color: #9CA3AF;
  margin-bottom: 16px;
}

.time-text {
  color: #6B7280;
  font-size: 13px;
}
</style>
