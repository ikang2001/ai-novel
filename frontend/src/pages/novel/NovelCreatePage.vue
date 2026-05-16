<template>
  <div class="novel-create-page">
    <div class="page-header">
      <div class="header-container">
        <h1 class="page-title">创建新小说</h1>
        <p class="page-subtitle">告诉 AI 你的故事构想，它会帮你构建世界观和角色</p>
      </div>
    </div>

    <div class="container">
      <!-- 阶段一：输入表单 -->
      <div v-if="phase === 'INPUT'" class="create-card">
        <a-form :model="form" layout="vertical" class="create-form">
          <a-form-item label="书名" required>
            <a-input
              v-model:value="form.title"
              placeholder="请输入书名"
              size="large"
              :maxlength="100"
              show-count
            />
          </a-form-item>

          <a-form-item label="题材" required>
            <a-select v-model:value="form.genre" placeholder="选择题材" size="large">
              <a-select-option v-for="g in GENRE_OPTIONS" :key="g.value" :value="g.value">
                {{ g.label }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="目标读者">
            <a-radio-group v-model:value="form.targetReaders" button-style="solid">
              <a-radio-button v-for="r in TARGET_READERS_OPTIONS" :key="r.value" :value="r.value">
                {{ r.label }}
              </a-radio-button>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="目标字数">
            <a-input-number
              v-model:value="form.targetWordCount"
              :min="10000"
              :step="50000"
              placeholder="如 200000"
              style="width: 100%"
              size="large"
              :formatter="(v: number) => v ? `${(v / 10000).toFixed(0)}万字` : ''"
              :parser="(v: string) => Number((v || '').replace('万字', '')) * 10000"
            />
          </a-form-item>

          <a-form-item label="核心创意">
            <a-textarea
              v-model:value="form.coreIdea"
              placeholder="用一两句话描述你的小说核心创意（可选）"
              :rows="3"
              :maxlength="500"
              show-count
            />
          </a-form-item>

          <a-form-item>
            <a-button
              type="primary"
              size="large"
              block
              :loading="creating"
              @click="handleCreate"
              class="submit-btn"
            >
              开始创建
            </a-button>
          </a-form-item>
        </a-form>
      </div>

      <!-- 阶段二：生成中 -->
      <div v-else-if="phase === 'GENERATING'" class="create-card generating-card">
        <a-spin size="large" />
        <p class="generating-text">AI 正在构建世界观和角色...</p>
        <p class="generating-hint">这可能需要 30-60 秒</p>
      </div>

      <!-- 阶段三：设定预览 -->
      <div v-else-if="phase === 'PREVIEW'" class="create-card">
        <h2 class="preview-title">{{ form.title }}</h2>
        <a-tag :color="GENRE_COLOR_MAP[form.genre || '']">{{ getGenreLabel(form.genre || '') }}</a-tag>

        <div v-if="settingResult" class="setting-preview">
          <!-- 世界观 -->
          <div v-if="settingResult.world_setting" class="setting-section">
            <h3>世界观设定</h3>
            <div class="setting-content">
              <pre>{{ JSON.stringify(settingResult.world_setting, null, 2) }}</pre>
            </div>
          </div>

          <!-- 角色 -->
          <div v-if="settingResult.characters?.length" class="setting-section">
            <h3>角色（{{ settingResult.characters.length }} 个）</h3>
            <div v-for="char in settingResult.characters" :key="char.name" class="char-card">
              <div class="char-header">
                <a-tag :color="ROLE_TYPE_COLOR_MAP[char.role_type] || 'default'">
                  {{ ROLE_TYPE_TEXT_MAP[char.role_type] || char.role_type }}
                </a-tag>
                <strong>{{ char.name }}</strong>
              </div>
              <p class="char-desc">{{ char.personality || char.background }}</p>
            </div>
          </div>

          <!-- 卷大纲 -->
          <div v-if="settingResult.volume_outline?.length" class="setting-section">
            <h3>卷大纲</h3>
            <div v-for="vol in settingResult.volume_outline" :key="vol.volume" class="vol-card">
              <strong>第{{ vol.volume }}卷：{{ vol.title }}</strong>
              <p>{{ vol.summary }}</p>
            </div>
          </div>
        </div>

        <div class="preview-actions">
          <a-button size="large" @click="phase = 'INPUT'">返回修改</a-button>
          <a-button type="primary" size="large" @click="handleConfirm">确认设定，开始写作</a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { createNovel } from '@/api/novelController'
import { connectNovelSSE } from '@/utils/novel'
import { GENRE_OPTIONS, TARGET_READERS_OPTIONS, GENRE_COLOR_MAP, ROLE_TYPE_TEXT_MAP, ROLE_TYPE_COLOR_MAP } from '@/constants/novel'
import type { SSEMessage } from '@/utils/sse'

const router = useRouter()

const phase = ref<'INPUT' | 'GENERATING' | 'PREVIEW'>('INPUT')
const creating = ref(false)
const novelId = ref<number | null>(null)

const form = reactive({
  title: '',
  genre: undefined as string | undefined,
  targetReaders: 'male',
  targetWordCount: 200000,
  coreIdea: '',
})

const settingResult = ref<any>(null)

const getGenreLabel = (genre: string) => {
  return GENRE_OPTIONS.find((g) => g.value === genre)?.label || genre
}

const handleCreate = async () => {
  if (!form.title?.trim()) {
    message.warning('请输入书名')
    return
  }
  if (!form.genre) {
    message.warning('请选择题材')
    return
  }

  creating.value = true
  try {
    const res = await createNovel({
      title: form.title.trim(),
      genre: form.genre,
      targetReaders: form.targetReaders,
      targetWordCount: form.targetWordCount,
      coreIdea: form.coreIdea || undefined,
    })

    if (res.data.code === 0 && res.data.data) {
      const data = res.data.data as any
      novelId.value = data.novelId
      settingResult.value = data.setting
      phase.value = 'PREVIEW'
      message.success('设定生成成功！')
    } else {
      message.error(res.data.message || '创建失败')
    }
  } catch (e) {
    message.error('创建失败，请重试')
  } finally {
    creating.value = false
  }
}

const handleConfirm = () => {
  if (novelId.value) {
    router.push(`/novel/${novelId.value}`)
  }
}
</script>

<style scoped>
.novel-create-page {
  min-height: calc(100vh - 64px);
  background: var(--bg-secondary, #F8FAFC);
}

.page-header {
  background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
  padding: 40px 0 32px;
  text-align: center;
}

.page-title {
  font-family: 'Outfit', sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
}

.page-subtitle {
  color: rgba(255, 255, 255, 0.85);
  margin: 0;
  font-size: 15px;
}

.container {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px;
}

.create-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.submit-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
  border: none;
}

.generating-card {
  text-align: center;
  padding: 80px 32px;
}

.generating-text {
  margin-top: 24px;
  font-size: 18px;
  font-weight: 600;
  color: #0F172A;
}

.generating-hint {
  color: #9CA3AF;
  font-size: 14px;
}

.preview-title {
  font-family: 'Outfit', sans-serif;
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px;
}

.setting-preview {
  margin-top: 24px;
}

.setting-section {
  margin-bottom: 24px;
}

.setting-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #22C55E;
  display: inline-block;
}

.setting-content {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 16px;
  font-size: 13px;
  max-height: 300px;
  overflow-y: auto;
}

.setting-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.char-card {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 8px;
}

.char-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.char-desc {
  color: #6B7280;
  font-size: 13px;
  margin: 0;
  line-height: 1.5;
}

.vol-card {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 8px;
}

.vol-card strong {
  display: block;
  margin-bottom: 4px;
}

.vol-card p {
  color: #6B7280;
  font-size: 13px;
  margin: 0;
}

.preview-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #E5E7EB;
}
</style>
