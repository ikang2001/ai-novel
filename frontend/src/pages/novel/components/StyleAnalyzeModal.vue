<template>
  <a-modal
    :open="visible"
    @update:open="$emit('update:visible', $event)"
    title="风格分析"
    width="640px"
    :footer="null"
  >
    <div v-if="!result" class="analyze-form">
      <p class="hint">粘贴你写的 2-5 章样本文字，AI 会分析你的写作风格。</p>
      <a-textarea
        v-model:value="samples"
        placeholder="粘贴你的小说样本..."
        :rows="10"
        :maxlength="15000"
        show-count
      />
      <a-button
        type="primary"
        block
        :loading="analyzing"
        @click="handleAnalyze"
        style="margin-top: 16px"
      >
        开始分析
      </a-button>
    </div>

    <div v-else class="analyze-result">
      <a-descriptions :column="1" bordered size="small">
        <a-descriptions-item label="叙述视角">{{ result.narrative_perspective }}</a-descriptions-item>
        <a-descriptions-item label="语言风格">{{ result.language_style }}</a-descriptions-item>
        <a-descriptions-item label="对话风格">{{ result.dialogue_style }}</a-descriptions-item>
        <a-descriptions-item label="描写偏好">{{ result.description_preference }}</a-descriptions-item>
        <a-descriptions-item label="节奏特点">{{ result.rhythm }}</a-descriptions-item>
        <a-descriptions-item label="情感基调">{{ result.emotional_tone }}</a-descriptions-item>
        <a-descriptions-item label="常用手法">
          <a-tag v-for="t in (result.techniques || [])" :key="t">{{ t }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="禁忌词汇">
          <a-tag v-for="w in (result.forbidden_words || [])" :key="w" color="red">{{ w }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="参考句式">
          <div v-for="s in (result.sample_sentences || [])" :key="s" class="sample-sentence">
            "{{ s }}"
          </div>
        </a-descriptions-item>
      </a-descriptions>
      <a-button type="primary" block @click="$emit('update:visible', false)" style="margin-top: 16px">
        确认
      </a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { analyzeStyle } from '@/api/novelController'

const props = defineProps<{ visible: boolean; novelId: number }>()
const emit = defineEmits(['update:visible', 'refresh'])

const samples = ref('')
const analyzing = ref(false)
const result = ref<Record<string, any> | null>(null)

const handleAnalyze = async () => {
  if (samples.value.length < 100) {
    message.warning('请至少粘贴 100 字的样本')
    return
  }
  analyzing.value = true
  try {
    const res = await analyzeStyle(props.novelId, { samples: samples.value })
    if (res.data.code === 0) {
      result.value = res.data.data || null
      message.success('分析完成')
    } else {
      message.error(res.data.message || '分析失败')
    }
  } catch (e) {
    message.error('分析失败')
  } finally {
    analyzing.value = false
  }
}
</script>

<style scoped>
.hint {
  color: #6B7280;
  margin-bottom: 16px;
}

.sample-sentence {
  font-style: italic;
  color: #374151;
  margin-bottom: 4px;
}
</style>
