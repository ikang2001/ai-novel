<template>
  <div class="chapter-list">
    <div class="chapter-list-header">
      <span class="title">章节列表</span>
    </div>

    <div class="chapter-scroll">
      <div
        v-for="ch in chapters"
        :key="ch.id"
        :class="['chapter-item', { active: ch.id === activeChapterId }]"
        @click="ch.id && $emit('select', ch.id)"
      >
        <div class="chapter-left">
          <span :class="['status-dot', `status-${ch.status}`]"></span>
          <div class="chapter-info">
            <div class="chapter-title" @dblclick.stop="startRename(ch)">
              <template v-if="editingId === ch.id">
                <a-input
                  v-model:value="editingTitle"
                  size="small"
                  @press-enter="finishRename(ch)"
                  @blur="finishRename(ch)"
                  @click.stop
                  :ref="(el: unknown) => setEditInputRef(ch.id!, el)"
                />
              </template>
              <template v-else>
                第{{ ch.chapterNumber }}章 {{ ch.title || '未命名' }}
              </template>
            </div>
            <div class="chapter-meta">
              {{ ch.wordCount || 0 }} 字
              <span v-if="ch.status" class="status-text">{{ CHAPTER_STATUS_TEXT_MAP[ch.status] || ch.status }}</span>
            </div>
          </div>
        </div>
        <a-dropdown :trigger="['click']" @click.stop>
          <MoreOutlined class="action-icon" />
          <template #overlay>
            <a-menu @click="handleMenuClick($event.key, ch)">
              <a-menu-item key="rename" :disabled="isProcessingChapter(ch)">
                <EditOutlined /> 重命名
              </a-menu-item>
              <a-menu-item key="delete" class="danger-item" :disabled="isProcessingChapter(ch)">
                <DeleteOutlined /> 删除
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>

      <div v-if="!chapters.length" class="empty-hint">
        <p>暂无章节</p>
        <p class="sub">点击上方按钮规划第一章</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { MoreOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import { deleteChapter, updateChapterTitle } from '@/api/novelController'
import { CHAPTER_STATUS_TEXT_MAP } from '@/constants/novel'

const props = defineProps<{
  chapters: API.ChapterVO[]
  activeChapterId: number | null
}>()

const emit = defineEmits<{
  select: [chapterId: number]
  planNew: []
  refresh: []
}>()

// 重命名相关
const editingId = ref<number | null>(null)
const editingTitle = ref('')
const editInputRefs = new Map<number, HTMLInputElement>()
const lockedStatuses = new Set(['generating', 'archiving'])

const setEditInputRef = (chapterId: number, el: any) => {
  const input = el?.input as HTMLInputElement | undefined
  if (input) {
    editInputRefs.set(chapterId, input)
  } else {
    editInputRefs.delete(chapterId)
  }
}

const isProcessingChapter = (ch: API.ChapterVO) => lockedStatuses.has(ch.status || '')

const startRename = (ch: API.ChapterVO) => {
  if (isProcessingChapter(ch)) {
    message.warning('处理中章节暂不能重命名')
    return
  }
  editingId.value = ch.id!
  editingTitle.value = ch.title || ''
  nextTick(() => {
    const input = editInputRefs.get(ch.id!)
    input?.focus()
    input?.select()
  })
}

const finishRename = async (ch: API.ChapterVO) => {
  const nextTitle = editingTitle.value.trim()
  if (!nextTitle) {
    message.warning('标题不能为空')
    editingId.value = null
    return
  }
  if (nextTitle !== ch.title) {
    try {
      const res = await updateChapterTitle(ch.id!, nextTitle)
      if (res.data.code === 0) {
        message.success('重命名成功')
        emit('refresh')
      } else {
        message.error(res.data.message || '重命名失败')
      }
    } catch {
      message.error('重命名失败')
    }
  }
  editingId.value = null
}

const handleAction = (key: string, ch: API.ChapterVO) => {
  if (key === 'rename') {
    startRename(ch)
  } else if (key === 'delete') {
    if (isProcessingChapter(ch)) {
      message.warning('处理中章节暂不能删除')
      return
    }
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除「第${ch.chapterNumber}章 ${ch.title || '未命名'}」吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const res = await deleteChapter(ch.id!)
          if (res.data.code === 0) {
            message.success('删除成功')
            emit('refresh')
          } else {
            message.error(res.data.message || '删除失败')
          }
        } catch {
          message.error('删除失败')
        }
      },
    })
  }
}

const handleMenuClick = (key: string, ch: API.ChapterVO) => {
  handleAction(key, ch)
}
</script>

<style scoped>
.chapter-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chapter-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #E5E7EB;
}

.title {
  font-weight: 600;
  font-size: 14px;
  color: #0F172A;
}

.chapter-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.chapter-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.15s ease;
  border-left: 3px solid transparent;
}

.chapter-item:hover {
  background: #F0FDF4;
}

.chapter-item.active {
  background: #F0FDF4;
  border-left-color: #22C55E;
}

.chapter-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.status-draft { background: #3B82F6; }
.status-dot.status-generating { background: #8B5CF6; }
.status-dot.status-archiving { background: #0EA5E9; }
.status-dot.status-confirmed { background: #22C55E; }
.status-dot.status-revised { background: #F59E0B; }
.status-dot.status-failed { background: #EF4444; }

.chapter-info {
  flex: 1;
  min-width: 0;
}

.chapter-title {
  font-size: 13px;
  font-weight: 500;
  color: #0F172A;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chapter-meta {
  font-size: 12px;
  color: #9CA3AF;
  margin-top: 2px;
}

.status-text {
  color: #6B7280;
  margin-left: 8px;
}

.action-icon {
  color: #9CA3AF;
  padding: 4px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}

.chapter-item:hover .action-icon {
  opacity: 1;
}

.action-icon:hover {
  color: #0F172A;
}

:deep(.danger-item) {
  color: #EF4444;
}

:deep(.danger-item:hover) {
  background: #FEF2F2;
}

.empty-hint {
  text-align: center;
  padding: 32px 16px;
  color: #9CA3AF;
}

.empty-hint p {
  margin: 0;
}

.empty-hint .sub {
  font-size: 12px;
  margin-top: 4px;
}
</style>
