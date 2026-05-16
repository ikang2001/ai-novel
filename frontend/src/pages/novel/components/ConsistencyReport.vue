<template>
  <div class="consistency-report">
    <div class="report-summary">
      <a-tag :color="report.issues?.length ? 'warning' : 'success'">
        {{ report.summary || (report.issues?.length ? `发现 ${report.issues.length} 个问题` : '未发现问题') }}
      </a-tag>
    </div>

    <div v-if="report.issues?.length" class="issue-list">
      <div v-for="(issue, idx) in report.issues" :key="idx" class="issue-item">
        <div class="issue-header">
          <a-tag :color="severityColor(issue.severity)" size="small">
            {{ issue.severity === 'high' ? '高' : issue.severity === 'medium' ? '中' : '低' }}
          </a-tag>
          <a-tag size="small">{{ issueTypeText(issue.type) }}</a-tag>
          <span v-if="issue.chapters?.length" class="issue-chapters">
            第{{ issue.chapters.join('、') }}章
          </span>
        </div>
        <div class="issue-desc">{{ issue.description }}</div>
        <div v-if="issue.suggestion" class="issue-suggestion">
          <div class="suggestion-header">
            <strong>建议：</strong>
            <a-button type="link" size="small" @click="copySuggestion(issue.suggestion!)">
              <template #icon><CopyOutlined /></template>
              复制
            </a-button>
          </div>
          <div class="suggestion-text">{{ issue.suggestion }}</div>
        </div>
        <div v-if="issue.chapters?.length" class="issue-actions">
          <a-button type="link" size="small" @click="goToChapter(issue.chapters![0])">
            <template #icon><ExportOutlined /></template>
            跳转到第{{ issue.chapters[0] }}章
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CopyOutlined, ExportOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const props = defineProps<{
  report: API.ConsistencyReport
  novelId: number
}>()

const emit = defineEmits<{
  goToChapter: [chapterNumber: number]
}>()

const severityColor = (s?: string) => {
  return s === 'high' ? 'error' : s === 'medium' ? 'warning' : 'default'
}

const issueTypeText = (t?: string) => {
  const map: Record<string, string> = {
    character_inconsistency: '角色矛盾',
    timeline_error: '时间线错误',
    forgotten_foreshadowing: '遗忘伏笔',
    plot_hole: '剧情漏洞',
    setting_violation: '设定违反',
  }
  return map[t || ''] || t || '未知'
}

const copySuggestion = (text: string) => {
  navigator.clipboard.writeText(text).then(() => {
    message.success('已复制到剪贴板')
  }).catch(() => {
    message.error('复制失败')
  })
}

const goToChapter = (chapterNumber: number) => {
  emit('goToChapter', chapterNumber)
}
</script>

<style scoped>
.issue-list {
  margin-top: 16px;
}

.issue-item {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  border-left: 3px solid #E5E7EB;
}

.issue-item:has(.issue-header :first-child[color="error"]) {
  border-left-color: #EF4444;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.issue-chapters {
  font-size: 12px;
  color: #9CA3AF;
}

.issue-desc {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  margin-bottom: 8px;
}

.issue-suggestion {
  font-size: 12px;
  color: #6B7280;
  background: #F0FDF4;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.suggestion-text {
  white-space: pre-wrap;
  line-height: 1.6;
}

.issue-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
