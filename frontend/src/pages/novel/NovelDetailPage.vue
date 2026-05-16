<template>
  <div class="novel-detail-page">
    <!-- 头部 -->
    <div class="page-header">
      <div class="header-container">
        <div class="header-left">
          <a-button type="text" @click="router.push('/novel/list')" class="back-btn">
            <template #icon><ArrowLeftOutlined /></template>
          </a-button>
          <div>
            <h1 class="page-title">{{ novel?.title || '加载中...' }}</h1>
            <div class="page-meta">
              <a-tag v-if="novel?.genre" :color="GENRE_COLOR_MAP[novel.genre]">
                {{ getGenreLabel(novel.genre) }}
              </a-tag>
              <span class="meta-text">{{ novel?.currentChapterNumber || 0 }} 章</span>
              <span class="meta-text">{{ formatWordCount(novel?.totalWordCount || 0) }}</span>
            </div>
          </div>
        </div>
        <div class="header-actions">
          <a-button @click="showSettingEditor = true">编辑设定</a-button>
          <a-button @click="showStyleModal = true">风格分析</a-button>
          <a-button type="primary" @click="goToWrite">
            <template #icon><EditOutlined /></template>
            开始写作
          </a-button>
        </div>
      </div>
    </div>

    <div class="container">
      <div class="detail-grid">
        <!-- 左栏 -->
        <div class="main-column">
          <!-- 世界观设定 -->
          <a-card title="世界观设定" :bordered="false" class="section-card" v-if="novel?.worldSetting">
            <div class="world-setting">
              <div v-for="(value, key) in novel.worldSetting" :key="key" class="setting-item">
                <span class="setting-label">{{ key }}：</span>
                <span class="setting-value">{{ formatSettingValue(value) }}</span>
              </div>
            </div>
          </a-card>

          <!-- 章节列表 -->
          <a-card title="章节列表" :bordered="false" class="section-card">
            <template #extra>
              <a-button type="primary" size="small" @click="handlePlanChapter">
                <template #icon><PlusOutlined /></template>
                规划下一章
              </a-button>
            </template>
            <ChapterList
              :chapters="chapters"
              :active-chapter-id="null"
              @select="handleChapterSelect"
              @plan-new="handlePlanChapter"
            />
          </a-card>
        </div>

        <!-- 右栏 -->
        <div class="side-column">
          <!-- 统计卡片 -->
          <a-card :bordered="false" class="section-card stat-card">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ novel?.currentChapterNumber || 0 }}</div>
                <div class="stat-label">章节数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ formatWordCount(novel?.totalWordCount || 0) }}</div>
                <div class="stat-label">总字数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ characters.length }}</div>
                <div class="stat-label">角色数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ activeForeshadowing.length }}</div>
                <div class="stat-label">活跃伏笔</div>
              </div>
            </div>
          </a-card>

          <!-- 角色摘要 -->
          <a-card title="角色" :bordered="false" class="section-card">
            <template #extra>
              <a-button type="link" size="small" @click="showCharacterPanel = true">管理</a-button>
            </template>
            <div v-for="char in characters.slice(0, 5)" :key="char.id" class="char-mini">
              <a-tag :color="ROLE_TYPE_COLOR_MAP[char.roleType || '']" size="small">
                {{ ROLE_TYPE_TEXT_MAP[char.roleType || ''] || char.roleType }}
              </a-tag>
              <span class="char-name">{{ char.name }}</span>
            </div>
            <div v-if="!characters.length" class="empty-mini">暂无角色</div>
          </a-card>

          <!-- 伏笔提醒 -->
          <a-card title="伏笔" :bordered="false" class="section-card">
            <template #extra>
              <a-button type="link" size="small" @click="showForeshadowingPanel = true">管理</a-button>
            </template>
            <div v-for="fs in activeForeshadowing.slice(0, 3)" :key="fs.id" class="fs-mini">
              <span class="fs-surface">{{ fs.surface?.substring(0, 30) }}...</span>
            </div>
            <div v-if="!activeForeshadowing.length" class="empty-mini">暂无活跃伏笔</div>
          </a-card>

          <!-- 快捷操作 -->
          <a-card title="快捷操作" :bordered="false" class="section-card">
            <a-space direction="vertical" style="width: 100%">
              <a-button block @click="handleConsistency" :loading="checking">
                连贯性检查
              </a-button>
              <a-button block @click="handleExport">
                导出小说
              </a-button>
            </a-space>
          </a-card>
        </div>
      </div>
    </div>

    <!-- 弹窗组件 -->
    <CharacterPanel
      v-model:visible="showCharacterPanel"
      :novel-id="novelId"
      @refresh="loadAll"
    />
    <ForeshadowingPanel
      v-model:visible="showForeshadowingPanel"
      :novel-id="novelId"
      @refresh="loadAll"
    />
    <StyleAnalyzeModal
      v-model:visible="showStyleModal"
      :novel-id="novelId"
    />
    <NovelSettingEditor
      v-model:visible="showSettingEditor"
      :novel="novel"
      @saved="loadNovel"
    />

    <!-- 连贯性检查结果 -->
    <a-modal
      v-model:open="showConsistencyReport"
      title="连贯性检查报告"
      :footer="null"
      width="640px"
    >
      <ConsistencyReport
        v-if="consistencyResult"
        :report="consistencyResult"
        :novel-id="novelId"
        @go-to-chapter="handleGoToChapter"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  EditOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue'
import { getNovel, listChapters, listCharacters, listForeshadowing, checkConsistency, exportNovel, planChapter } from '@/api/novelController'
import { GENRE_OPTIONS, GENRE_COLOR_MAP, ROLE_TYPE_TEXT_MAP, ROLE_TYPE_COLOR_MAP } from '@/constants/novel'
import { formatWordCount } from '@/utils/novel'
import ChapterList from './components/ChapterList.vue'
import CharacterPanel from './components/CharacterPanel.vue'
import ForeshadowingPanel from './components/ForeshadowingPanel.vue'
import StyleAnalyzeModal from './components/StyleAnalyzeModal.vue'
import NovelSettingEditor from './components/NovelSettingEditor.vue'
import ConsistencyReport from './components/ConsistencyReport.vue'

const router = useRouter()
const route = useRoute()
const novelId = Number(route.params.id)

const novel = ref<API.NovelVO | null>(null)
const chapters = ref<API.ChapterVO[]>([])
const characters = ref<API.CharacterVO[]>([])
const foreshadowing = ref<API.ForeshadowingVO[]>([])
const checking = ref(false)
const consistencyResult = ref<API.ConsistencyReport | null>(null)

const showCharacterPanel = ref(false)
const showForeshadowingPanel = ref(false)
const showStyleModal = ref(false)
const showSettingEditor = ref(false)
const showConsistencyReport = ref(false)

const activeForeshadowing = computed(() =>
  foreshadowing.value.filter((fs) => fs.status === 'active')
)

const getGenreLabel = (genre: string) =>
  GENRE_OPTIONS.find((g) => g.value === genre)?.label || genre

const formatSettingValue = (value: any): string => {
  if (Array.isArray(value)) return value.join('、')
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

const loadNovel = async () => {
  const res = await getNovel({ novelId })
  if (res.data.code === 0) novel.value = res.data.data || null
}

const loadChapters = async () => {
  const res = await listChapters(novelId)
  if (res.data.code === 0) chapters.value = res.data.data || []
}

const loadCharacters = async () => {
  const res = await listCharacters(novelId)
  if (res.data.code === 0) characters.value = res.data.data || []
}

const loadForeshadowing = async () => {
  const res = await listForeshadowing(novelId)
  if (res.data.code === 0) foreshadowing.value = res.data.data || []
}

const loadAll = () => {
  loadNovel()
  loadChapters()
  loadCharacters()
  loadForeshadowing()
}

const goToWrite = (chapterId?: number) => {
  const query = chapterId ? `?chapter=${chapterId}` : ''
  router.push(`/novel/${novelId}/write${query}`)
}

const handleChapterSelect = (id: number) => {
  goToWrite(id)
}

const handlePlanChapter = async () => {
  try {
    const res = await planChapter(novelId, {})
    if (res.data.code === 0) {
      message.success('大纲规划成功')
      loadChapters()
    } else {
      message.error(res.data.message || '规划失败')
    }
  } catch (e) {
    message.error('规划失败')
  }
}

const handleConsistency = async () => {
  checking.value = true
  try {
    const res = await checkConsistency(novelId)
    if (res.data.code === 0) {
      consistencyResult.value = res.data.data || null
      showConsistencyReport.value = true
    } else {
      message.error(res.data.message || '检查失败')
    }
  } catch (e) {
    message.error('检查失败')
  } finally {
    checking.value = false
  }
}

const handleGoToChapter = (chapterNumber: number) => {
  // 查找章节
  const chapter = chapters.value.find(c => c.chapterNumber === chapterNumber)
  if (chapter) {
    // 跳转到写作页面并选中该章节
    router.push(`/novel/${novelId}/write?chapterId=${chapter.id}`)
    showConsistencyReport.value = false
  } else {
    message.warning(`未找到第${chapterNumber}章`)
  }
}

const handleExport = async () => {
  try {
    const res = await exportNovel(novelId, { format: 'docx' })
    if (res.data.code === 0) {
      message.success('导出成功')
    } else {
      message.error(res.data.message || '导出功能暂未实现')
    }
  } catch (e) {
    message.error('导出失败')
  }
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.novel-detail-page {
  min-height: calc(100vh - 64px);
  background: var(--bg-secondary, #F8FAFC);
}

.page-header {
  background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
  padding: 32px 0;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  color: rgba(255, 255, 255, 0.8);
}

.page-title {
  font-family: 'Outfit', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px;
}

.page-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-text {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
}

.section-card {
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.world-setting {
  font-size: 14px;
  line-height: 1.8;
}

.setting-item {
  margin-bottom: 8px;
}

.setting-label {
  font-weight: 600;
  color: #0F172A;
}

.setting-value {
  color: #374151;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #22C55E;
}

.stat-label {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 2px;
}

.char-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.char-name {
  font-size: 13px;
  color: #374151;
}

.fs-mini {
  padding: 4px 0;
}

.fs-surface {
  font-size: 13px;
  color: #374151;
}

.empty-mini {
  color: #9CA3AF;
  font-size: 13px;
  text-align: center;
  padding: 12px 0;
}

@media (max-width: 768px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .header-container {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>
