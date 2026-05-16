<template>
  <a-drawer
    :open="visible"
    @update:open="$emit('update:visible', $event)"
    title="伏笔管理"
    width="480"
    placement="right"
  >
    <div class="foreshadowing-panel">
      <a-button type="primary" block @click="showCreate = true" style="margin-bottom: 16px">
        <template #icon><PlusOutlined /></template>
        添加伏笔
      </a-button>

      <a-select v-model:value="statusFilter" style="width: 100%; margin-bottom: 16px" @change="loadData">
        <a-select-option value="">全部</a-select-option>
        <a-select-option value="active">活跃</a-select-option>
        <a-select-option value="resolved">已揭示</a-select-option>
        <a-select-option value="abandoned">已放弃</a-select-option>
      </a-select>

      <div v-for="fs in foreshadowingList" :key="fs.id" class="fs-item">
        <div class="fs-header">
          <a-tag :color="FORESHADOWING_STATUS_TAG_MAP[fs.status || '']" size="small">
            {{ FORESHADOWING_STATUS_TEXT_MAP[fs.status || ''] }}
          </a-tag>
          <span class="fs-importance">
            <a-rate :value="fs.importance" disabled :count="5" style="font-size: 12px" />
          </span>
        </div>
        <div class="fs-surface">{{ fs.surface }}</div>
        <div v-if="fs.hiddenTruth" class="fs-truth">真相：{{ fs.hiddenTruth }}</div>
        <div class="fs-actions" v-if="fs.status === 'active'">
          <a-button size="small" @click="handleResolve(fs.id!)">揭示</a-button>
          <a-button size="small" danger @click="handleAbandon(fs.id!)">放弃</a-button>
        </div>
      </div>

      <a-empty v-if="!foreshadowingList.length" description="暂无伏笔" />
    </div>

    <!-- 创建弹窗 -->
    <a-modal v-model:open="showCreate" title="添加伏笔" @ok="handleCreate" :confirm-loading="submitting">
      <a-form :model="form" layout="vertical">
        <a-form-item label="表面信息（读者看到的）" required>
          <a-textarea v-model:value="form.surface" :rows="2" placeholder="如：主角手腕有道旧伤疤" />
        </a-form-item>
        <a-form-item label="隐藏真相">
          <a-textarea v-model:value="form.hiddenTruth" :rows="2" placeholder="如：小时候救反派女儿时留的" />
        </a-form-item>
        <a-form-item label="重要度">
          <a-rate v-model:value="form.importance" :count="5" />
        </a-form-item>
        <a-form-item label="计划揭示章节">
          <a-input v-model:value="form.targetChapter" placeholder="如：80-100" />
        </a-form-item>
      </a-form>
    </a-modal>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import {
  listForeshadowing,
  createForeshadowing,
  resolveForeshadowing,
  abandonForeshadowing,
} from '@/api/novelController'
import {
  FORESHADOWING_STATUS_TEXT_MAP,
  FORESHADOWING_STATUS_TAG_MAP,
} from '@/constants/novel'

const props = defineProps<{ visible: boolean; novelId: number }>()
const emit = defineEmits(['update:visible', 'refresh'])

const foreshadowingList = ref<API.ForeshadowingVO[]>([])
const statusFilter = ref('')
const showCreate = ref(false)
const submitting = ref(false)

const form = reactive({
  surface: '',
  hiddenTruth: '',
  importance: 3,
  targetChapter: '',
})

const loadData = async () => {
  const res = await listForeshadowing(props.novelId, statusFilter.value ? { status: statusFilter.value } : undefined)
  if (res.data.code === 0) foreshadowingList.value = res.data.data || []
}

watch(() => props.visible, (v) => { if (v) loadData() })

const handleCreate = async () => {
  if (!form.surface?.trim()) {
    message.warning('请输入表面信息')
    return
  }
  submitting.value = true
  try {
    await createForeshadowing(props.novelId, {
      surface: form.surface,
      hiddenTruth: form.hiddenTruth || undefined,
      importance: form.importance,
      targetChapter: form.targetChapter || undefined,
    })
    message.success('创建成功')
    showCreate.value = false
    form.surface = ''
    form.hiddenTruth = ''
    form.importance = 3
    form.targetChapter = ''
    loadData()
    emit('refresh')
  } catch (e) {
    message.error('创建失败')
  } finally {
    submitting.value = false
  }
}

const handleResolve = async (id: number) => {
  await resolveForeshadowing(id)
  message.success('已揭示')
  loadData()
  emit('refresh')
}

const handleAbandon = async (id: number) => {
  await abandonForeshadowing(id)
  message.success('已放弃')
  loadData()
  emit('refresh')
}
</script>

<style scoped>
.fs-item {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.fs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.fs-surface {
  font-size: 14px;
  color: #0F172A;
  margin-bottom: 4px;
}

.fs-truth {
  font-size: 12px;
  color: #9CA3AF;
  font-style: italic;
}

.fs-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
</style>
