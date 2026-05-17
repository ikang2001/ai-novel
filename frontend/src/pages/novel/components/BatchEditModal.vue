<template>
  <a-modal
    :open="visible"
    title="批量编辑章节"
    width="560px"
    @cancel="handleClose"
    :footer="null"
  >
    <!-- 手动添加章节 -->
    <div class="add-section">
      <a-input
        v-model:value="newTitle"
        placeholder="新章节标题（留空自动生成）"
        style="width: 280px"
        @press-enter="handleAdd"
      />
      <a-button type="primary" @click="handleAdd" :loading="adding">
        <template #icon><PlusOutlined /></template>
        添加章节
      </a-button>
    </div>

    <!-- 章节列表 -->
    <div class="chapter-check-list">
      <div class="list-header">
        <a-checkbox
          :checked="allChecked"
          :indeterminate="indeterminate"
          @change="toggleAll"
        >
          全选
        </a-checkbox>
        <span class="selected-count" v-if="selectedIds.size > 0">
          已选 {{ selectedIds.size }} 章
        </span>
      </div>

      <div class="list-body">
        <div
          v-for="ch in chapters"
          :key="ch.id"
          class="check-item"
        >
          <a-checkbox
            :checked="selectedIds.has(ch.id!)"
            @change="toggleOne(ch.id!)"
          >
            <span class="ch-title">第{{ ch.chapterNumber }}章 {{ ch.title || '未命名' }}</span>
            <span class="ch-meta">{{ ch.wordCount || 0 }} 字</span>
          </a-checkbox>
        </div>
        <div v-if="!chapters.length" class="empty">暂无章节</div>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div class="action-bar" v-if="selectedIds.size > 0">
      <a-popconfirm
        :title="`确认删除选中的 ${selectedIds.size} 个章节？`"
        ok-text="删除"
        cancel-text="取消"
        ok-type="danger"
        @confirm="handleBatchDelete"
      >
        <a-button danger :loading="deleting">
          <template #icon><DeleteOutlined /></template>
          删除选中 ({{ selectedIds.size }})
        </a-button>
      </a-popconfirm>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { deleteChapter, createChapter } from '@/api/novelController'

const props = defineProps<{
  visible: boolean
  novelId: number
  chapters: API.ChapterVO[]
}>()

const emit = defineEmits<{
  'update:visible': [val: boolean]
  refresh: []
}>()

const selectedIds = ref(new Set<number>())
const newTitle = ref('')
const adding = ref(false)
const deleting = ref(false)

const allChecked = computed(() =>
  props.chapters.length > 0 && selectedIds.value.size === props.chapters.length
)
const indeterminate = computed(() =>
  selectedIds.value.size > 0 && selectedIds.value.size < props.chapters.length
)

const toggleAll = () => {
  if (allChecked.value) {
    selectedIds.value.clear()
  } else {
    selectedIds.value = new Set(props.chapters.map((c) => c.id!))
  }
}

const toggleOne = (id: number) => {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

const handleAdd = async () => {
  adding.value = true
  try {
    const res = await createChapter(props.novelId, { title: newTitle.value.trim() || undefined })
    if (res.data.code === 0) {
      message.success('章节已添加')
      newTitle.value = ''
      emit('refresh')
    } else {
      message.error(res.data.message || '添加失败')
    }
  } catch {
    message.error('添加失败')
  } finally {
    adding.value = false
  }
}

const handleBatchDelete = async () => {
  deleting.value = true
  let success = 0
  let fail = 0
  for (const id of selectedIds.value) {
    try {
      const res = await deleteChapter(id)
      if (res.data.code === 0) success++
      else fail++
    } catch {
      fail++
    }
  }
  deleting.value = false
  selectedIds.value.clear()

  if (success > 0) message.success(`成功删除 ${success} 个章节`)
  if (fail > 0) message.error(`${fail} 个章节删除失败`)
  emit('refresh')
}

const handleClose = () => {
  selectedIds.value.clear()
  emit('update:visible', false)
}
</script>

<style scoped>
.add-section {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.chapter-check-list {
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  overflow: hidden;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
}

.selected-count {
  font-size: 12px;
  color: #22C55E;
  font-weight: 500;
}

.list-body {
  max-height: 360px;
  overflow-y: auto;
}

.check-item {
  padding: 6px 12px;
  border-bottom: 1px solid #F3F4F6;
  transition: background 0.15s;
}

.check-item:hover {
  background: #F0FDF4;
}

.check-item:last-child {
  border-bottom: none;
}

.ch-title {
  font-size: 13px;
  font-weight: 500;
}

.ch-meta {
  font-size: 12px;
  color: #9CA3AF;
  margin-left: 8px;
}

.empty {
  text-align: center;
  padding: 24px;
  color: #9CA3AF;
}

.action-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
