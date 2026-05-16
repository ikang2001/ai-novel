<template>
  <div class="novel-write-page">
    <!-- 左侧栏：章节列表 -->
    <aside class="sidebar-left">
      <ChapterList
        :chapters="chapters"
        :active-chapter-id="activeChapterId"
        @select="handleSelectChapter"
        @plan-new="handlePlanChapter"
        @refresh="loadChapters"
      />
    </aside>

    <!-- 中间：内容区 -->
    <main class="main-content">
      <!-- 未选择章节 -->
      <div v-if="!activeChapterId" class="welcome-state">
        <BookOutlined class="welcome-icon" />
        <h2>{{ novel?.title || '小说写作' }}</h2>
        <p>从左侧选择一个章节开始写作，或规划一个新章节</p>
        <a-button type="primary" size="large" @click="handlePlanChapter">
          <template #icon><PlusOutlined /></template>
          规划新章节
        </a-button>
      </div>

      <!-- 章节内容 -->
      <div v-else class="chapter-workspace">
        <!-- 章节头部 -->
        <div class="chapter-header">
          <div class="chapter-header-left">
            <h2 class="chapter-title">
              第{{ activeChapter?.chapterNumber }}章 {{ activeChapter?.title || '' }}
            </h2>
            <a-tag :color="chapterStatusColor" size="small">
              {{ CHAPTER_STATUS_TEXT_MAP[activeChapter?.status || ''] }}
            </a-tag>
          </div>
          <div class="chapter-header-actions">
            <a-button v-if="activeChapter?.status === 'draft' && !isGenerating" @click="handleGenerate">
              <template #icon><ThunderboltOutlined /></template>
              生成内容
            </a-button>
            <a-button v-if="activeChapter?.status === 'draft' && chapterContent && !isGenerating" @click="handleConfirm">
              <template #icon><CheckOutlined /></template>
              确认章节
            </a-button>
            <a-button v-if="activeChapter?.status === 'draft' && chapterContent && !isGenerating" @click="handleRegenerate">
              <template #icon><RedoOutlined /></template>
              重新生成
            </a-button>
            <a-button v-if="chapterContent && !isEditing" @click="startEdit">
              <template #icon><EditOutlined /></template>
              编辑
            </a-button>
          </div>
        </div>

        <!-- 生成中：流式显示 -->
        <ChapterStreamingContent
          v-if="isGenerating"
          :content="streamingContent"
          :is-streaming="true"
          :chapter-title="activeChapter?.title"
        />

        <!-- 编辑中 -->
        <div v-else-if="isEditing" class="edit-area">
          <a-textarea v-model:value="editContent" :rows="30" class="edit-textarea" />
          <div class="edit-actions">
            <a-button @click="cancelEdit">取消</a-button>
            <a-button type="primary" @click="saveEdit" :loading="saving">保存</a-button>
          </div>
        </div>

        <!-- 已有内容：只读显示 -->
        <ChapterStreamingContent
          v-else-if="chapterContent"
          :content="chapterContent"
          :is-streaming="false"
          :chapter-title="activeChapter?.title"
        />

        <!-- 未生成 -->
        <div v-else class="empty-content">
          <p>点击"生成内容"按钮，AI 将根据大纲生成章节正文</p>
        </div>
      </div>
    </main>

    <!-- 右侧栏 -->
    <aside class="sidebar-right">
      <a-tabs v-model:activeKey="rightTab" class="right-tabs">
        <!-- 大纲 -->
        <a-tab-pane key="outline" tab="大纲">
          <div v-if="activeChapter?.outline" class="outline-content">
            <div v-if="activeChapter.outline.chapter_title" class="outline-title">
              {{ activeChapter.outline.chapter_title }}
            </div>
            <div v-for="scene in (activeChapter.outline.scenes || [])" :key="scene.scene" class="scene-item">
              <div class="scene-header">
                <a-tag size="small">场景{{ scene.scene }}</a-tag>
                <span class="scene-location">{{ scene.location }}</span>
              </div>
              <div class="scene-events">{{ scene.events }}</div>
            </div>
            <div v-if="activeChapter.outline.chapter_hook" class="chapter-hook">
              <strong>章末钩子：</strong>{{ activeChapter.outline.chapter_hook }}
            </div>
          </div>
          <a-empty v-else description="暂无大纲" />
        </a-tab-pane>

        <!-- 角色 -->
        <a-tab-pane key="characters" tab="角色">
          <div v-for="char in characters" :key="char.id" class="side-char">
            <a-tag :color="ROLE_TYPE_COLOR_MAP[char.roleType || '']" size="small">
              {{ ROLE_TYPE_TEXT_MAP[char.roleType || ''] }}
            </a-tag>
            <span class="char-name">{{ char.name }}</span>
            <div v-if="char.currentStatus" class="char-status">{{ char.currentStatus }}</div>
          </div>
          <a-empty v-if="!characters.length" description="暂无角色" />
          <a-button type="link" block @click="showCharacterPanel = true" style="margin-top: 8px">
            管理角色
          </a-button>
        </a-tab-pane>

        <!-- 伏笔 -->
        <a-tab-pane key="foreshadowing" tab="伏笔">
          <div v-for="fs in activeForeshadowing" :key="fs.id" class="side-fs">
            <div class="fs-surface">{{ fs.surface?.substring(0, 40) }}...</div>
            <div class="fs-meta">第{{ fs.plantedChapterId || '?' }}章 | 重要度: {{ fs.importance }}/5</div>
          </div>
          <a-empty v-if="!activeForeshadowing.length" description="暂无活跃伏笔" />
          <a-button type="link" block @click="showForeshadowingPanel = true" style="margin-top: 8px">
            管理伏笔
          </a-button>
        </a-tab-pane>
      </a-tabs>

      <!-- SSE 日志 -->
      <div v-if="logs.length" class="log-section">
        <div class="log-header">实时日志</div>
        <div class="log-list">
          <div v-for="(log, idx) in logs" :key="idx" class="log-item">
            <span class="log-time">{{ log.time }}</span>
            <span :class="['log-msg', `log-${log.type}`]">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- 弹窗 -->
    <CharacterPanel v-model:visible="showCharacterPanel" :novel-id="novelId" @refresh="loadAll" />
    <ForeshadowingPanel v-model:visible="showForeshadowingPanel" :novel-id="novelId" @refresh="loadAll" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  BookOutlined,
  PlusOutlined,
  ThunderboltOutlined,
  CheckOutlined,
  RedoOutlined,
  EditOutlined,
} from '@ant-design/icons-vue'
import {
  getNovel,
  listChapters,
  listCharacters,
  listForeshadowing,
  getChapter,
  generateChapter,
  confirmChapter,
  regenerateChapter,
  updateChapterContent,
  planChapter,
} from '@/api/novelController'
import { connectNovelSSE } from '@/utils/novel'
import { CHAPTER_STATUS_TEXT_MAP, CHAPTER_STATUS_COLOR_MAP, ROLE_TYPE_TEXT_MAP, ROLE_TYPE_COLOR_MAP } from '@/constants/novel'
import { NovelSseMessageType } from '@/constants/novel'
import ChapterList from './components/ChapterList.vue'
import ChapterStreamingContent from './components/ChapterStreamingContent.vue'
import CharacterPanel from './components/CharacterPanel.vue'
import ForeshadowingPanel from './components/ForeshadowingPanel.vue'
import type { SSEMessage } from '@/utils/sse'

const route = useRoute()
const novelId = Number(route.params.id)

// 数据
const novel = ref<API.NovelVO | null>(null)
const chapters = ref<API.ChapterVO[]>([])
const characters = ref<API.CharacterVO[]>([])
const foreshadowing = ref<API.ForeshadowingVO[]>([])
const activeChapterId = ref<number | null>(null)
const activeChapter = ref<API.ChapterVO | null>(null)

// 状态
const isGenerating = ref(false)
const streamingContent = ref('')
const chapterContent = ref('')
const isEditing = ref(false)
const editContent = ref('')
const saving = ref(false)
const rightTab = ref('outline')

// 弹窗
const showCharacterPanel = ref(false)
const showForeshadowingPanel = ref(false)

// 日志
const logs = ref<{ time: string; type: string; message: string }[]>([])

// SSE
let eventSource: EventSource | null = null

const activeForeshadowing = computed(() =>
  foreshadowing.value.filter((fs) => fs.status === 'active')
)

const chapterStatusColor = computed(() =>
  CHAPTER_STATUS_COLOR_MAP[activeChapter.value?.status || ''] || '#6B7280'
)

const addLog = (message: string, type: string = 'info') => {
  const time = new Date().toLocaleTimeString()
  logs.value.push({ time, type, message })
  if (logs.value.length > 50) logs.value.shift()
}

// 加载数据
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

const loadChapterDetail = async (chapterId: number) => {
  const res = await getChapter({ chapterId })
  if (res.data.code === 0 && res.data.data) {
    activeChapter.value = res.data.data
    chapterContent.value = res.data.data.content || ''
  }
}

// 选择章节
const handleSelectChapter = (id: number) => {
  activeChapterId.value = id
  loadChapterDetail(id)
  streamingContent.value = ''
}

// 规划新章节
const handlePlanChapter = async () => {
  try {
    const res = await planChapter(novelId, {})
    if (res.data.code === 0) {
      message.success('大纲规划成功')
      await loadChapters()
      const data = res.data.data as any
      if (data?.chapterId) {
        handleSelectChapter(data.chapterId)
      }
    } else {
      message.error(res.data.message || '规划失败')
    }
  } catch (e) {
    message.error('规划失败')
  }
}

// 生成章节内容
const handleGenerate = async () => {
  if (!activeChapterId.value) return

  const chapter = activeChapter.value
  const outline = chapter?.outline || {}

  isGenerating.value = true
  streamingContent.value = ''
  logs.value = []

  try {
    const res = await generateChapter(novelId, { outline })
    if (res.data.code === 0) {
      const data = res.data.data as any
      const taskId = data.taskId

      addLog('开始生成...', 'info')

      eventSource = connectNovelSSE(taskId, {
        onMessage: handleSSEMessage,
        onError: () => {
          addLog('连接错误', 'error')
          isGenerating.value = false
        },
        onComplete: () => {
          isGenerating.value = false
          loadChapterDetail(activeChapterId.value!)
          loadChapters()
        },
      })
    } else {
      message.error(res.data.message || '生成失败')
      isGenerating.value = false
    }
  } catch (e) {
    message.error('生成失败')
    isGenerating.value = false
  }
}

// SSE 消息处理
const handleSSEMessage = (msg: SSEMessage) => {
  switch (msg.type) {
    case NovelSseMessageType.CHAPTER_GENERATING:
      addLog('正在生成章节...', 'info')
      break
    case NovelSseMessageType.CHAPTER_STREAMING:
      streamingContent.value += msg.data || msg.content || ''
      break
    case NovelSseMessageType.CHAPTER_GENERATED:
      addLog('章节生成完成', 'success')
      break
    case NovelSseMessageType.ARCHIVING:
      addLog('正在归档...', 'info')
      break
    case NovelSseMessageType.ARCHIVE_COMPLETE:
      addLog('归档完成', 'success')
      break
    case NovelSseMessageType.ERROR:
      addLog(`错误: ${msg.data || msg.content || '未知错误'}`, 'error')
      message.error('生成失败')
      break
    case NovelSseMessageType.ALL_COMPLETE:
      addLog('全部完成', 'success')
      message.success('章节生成完成！')
      break
  }
}

// 确认章节
const handleConfirm = async () => {
  if (!activeChapterId.value) return
  try {
    const res = await confirmChapter(activeChapterId.value)
    if (res.data.code === 0) {
      message.success('章节已确认')
      loadChapterDetail(activeChapterId.value)
      loadChapters()
    } else {
      message.error(res.data.message || '确认失败')
    }
  } catch (e) {
    message.error('确认失败')
  }
}

// 重新生成
const handleRegenerate = async () => {
  if (!activeChapterId.value) return
  try {
    const res = await regenerateChapter(activeChapterId.value)
    if (res.data.code === 0) {
      message.success('已重新生成')
      const data = res.data.data as any
      if (data?.taskId) {
        handleGenerate()
      }
      loadChapterDetail(activeChapterId.value)
    }
  } catch (e) {
    message.error('重新生成失败')
  }
}

// 编辑
const startEdit = () => {
  editContent.value = chapterContent.value
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
}

const saveEdit = async () => {
  if (!activeChapterId.value) return
  saving.value = true
  try {
    const res = await updateChapterContent(activeChapterId.value, { content: editContent.value })
    if (res.data.code === 0) {
      message.success('保存成功')
      chapterContent.value = editContent.value
      isEditing.value = false
      loadChapters()
    } else {
      message.error(res.data.message || '保存失败')
    }
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadAll()
  // 从 URL 参数获取章节 ID
  const chapterQuery = route.query.chapter
  if (chapterQuery) {
    activeChapterId.value = Number(chapterQuery)
    loadChapterDetail(Number(chapterQuery))
  }
})

onBeforeUnmount(() => {
  if (eventSource) {
    eventSource.close()
  }
})
</script>

<style scoped>
.novel-write-page {
  display: grid;
  grid-template-columns: 260px 1fr 300px;
  height: calc(100vh - 64px);
  overflow: hidden;
}

/* 左侧栏 */
.sidebar-left {
  border-right: 1px solid #E5E7EB;
  background: #fff;
  overflow-y: auto;
}

/* 中间 */
.main-content {
  overflow-y: auto;
  background: #fff;
}

.welcome-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9CA3AF;
}

.welcome-icon {
  font-size: 64px;
  color: #D1D5DB;
  margin-bottom: 16px;
}

.welcome-state h2 {
  font-family: 'Outfit', sans-serif;
  color: #0F172A;
  margin-bottom: 8px;
}

.chapter-workspace {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #E5E7EB;
  flex-wrap: wrap;
  gap: 12px;
}

.chapter-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chapter-title {
  font-family: 'Outfit', sans-serif;
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.chapter-header-actions {
  display: flex;
  gap: 8px;
}

.edit-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
}

.edit-textarea {
  flex: 1;
  font-size: 15px;
  line-height: 1.8;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9CA3AF;
  font-size: 15px;
}

/* 右侧栏 */
.sidebar-right {
  border-left: 1px solid #E5E7EB;
  background: #fff;
  overflow-y: auto;
  padding: 0 12px;
}

.right-tabs {
  margin-top: 8px;
}

.outline-title {
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 12px;
  color: #0F172A;
}

.scene-item {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 8px;
}

.scene-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.scene-location {
  font-size: 13px;
  color: #6B7280;
}

.scene-events {
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
}

.chapter-hook {
  margin-top: 12px;
  padding: 10px;
  background: #F0FDF4;
  border-radius: 8px;
  font-size: 13px;
  color: #374151;
}

.side-char {
  padding: 8px 0;
  border-bottom: 1px solid #F3F4F6;
}

.char-name {
  font-weight: 500;
  color: #0F172A;
  margin-left: 8px;
}

.char-status {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 2px;
  padding-left: 8px;
}

.side-fs {
  padding: 8px 0;
  border-bottom: 1px solid #F3F4F6;
}

.fs-surface {
  font-size: 13px;
  color: #374151;
}

.fs-meta {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 2px;
}

/* 日志 */
.log-section {
  margin-top: 16px;
  border-top: 1px solid #E5E7EB;
  padding-top: 12px;
}

.log-header {
  font-weight: 600;
  font-size: 13px;
  color: #0F172A;
  margin-bottom: 8px;
}

.log-list {
  max-height: 200px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  gap: 8px;
  padding: 3px 0;
  font-size: 12px;
}

.log-time {
  color: #9CA3AF;
  flex-shrink: 0;
}

.log-msg { color: #374151; }
.log-error { color: #EF4444; }
.log-success { color: #22C55E; }

@media (max-width: 992px) {
  .novel-write-page {
    grid-template-columns: 1fr;
  }
  .sidebar-left,
  .sidebar-right {
    display: none;
  }
}
</style>
