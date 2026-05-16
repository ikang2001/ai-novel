<template>
  <a-modal
    :open="visible"
    @update:open="$emit('update:visible', $event)"
    title="编辑设定"
    width="640px"
    @ok="handleSave"
    :confirm-loading="saving"
  >
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="world" tab="世界观">
        <a-textarea v-model:value="worldSettingText" :rows="10" placeholder="世界观设定（JSON格式）" />
      </a-tab-pane>
      <a-tab-pane key="volume" tab="卷大纲">
        <a-textarea v-model:value="volumeOutlineText" :rows="10" placeholder="卷大纲（JSON格式）" />
      </a-tab-pane>
    </a-tabs>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { updateNovelSetting } from '@/api/novelController'

const props = defineProps<{ visible: boolean; novel: API.NovelVO | null }>()
const emit = defineEmits(['update:visible', 'saved'])

const activeTab = ref('world')
const saving = ref(false)
const worldSettingText = ref('')
const volumeOutlineText = ref('')

watch(() => props.visible, (v) => {
  if (v && props.novel) {
    worldSettingText.value = props.novel.worldSetting
      ? JSON.stringify(props.novel.worldSetting, null, 2)
      : ''
    volumeOutlineText.value = props.novel.volumeOutline
      ? JSON.stringify(props.novel.volumeOutline, null, 2)
      : ''
  }
})

const handleSave = async () => {
  if (!props.novel?.id) return
  saving.value = true
  try {
    const body: any = {}
    if (worldSettingText.value) {
      try { body.worldSetting = JSON.parse(worldSettingText.value) } catch { message.error('世界观JSON格式错误'); saving.value = false; return }
    }
    if (volumeOutlineText.value) {
      try { body.volumeOutline = JSON.parse(volumeOutlineText.value) } catch { message.error('卷大纲JSON格式错误'); saving.value = false; return }
    }
    const res = await updateNovelSetting(props.novel.id, body)
    if (res.data.code === 0) {
      message.success('保存成功')
      emit('saved')
      emit('update:visible', false)
    } else {
      message.error(res.data.message || '保存失败')
    }
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>
