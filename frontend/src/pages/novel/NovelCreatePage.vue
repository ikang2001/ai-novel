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

          <a-form-item>
            <template #label>
              <div class="core-idea-label">
                <span>核心创意</span>
                <a-button type="link" size="small" @click="openIdeaAssistant">
                  <template #icon><BulbOutlined /></template>
                  AI完善创意
                </a-button>
              </div>
            </template>
            <a-textarea
              v-model:value="form.coreIdea"
              placeholder="用一两句话描述你的小说核心创意。创意不够完整时，可以先点“AI完善创意”。"
              :rows="5"
              :maxlength="2000"
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
        <p class="generating-text">{{ generatingStatus }}</p>
        <p class="generating-hint">这可能需要 30-120 秒，请耐心等待</p>
      </div>

      <!-- 阶段三：设定预览 -->
      <div v-else-if="phase === 'PREVIEW'" class="create-card">
        <h2 class="preview-title">{{ form.title }}</h2>
        <a-tag :color="GENRE_COLOR_MAP[form.genre || '']">{{ getGenreLabel(form.genre || '') }}</a-tag>

        <div v-if="settingResult" class="setting-preview">
          <!-- 世界观 -->
          <div v-if="previewWorldSetting" class="setting-section">
            <h3>世界观设定</h3>
            <div class="setting-content">
              <pre>{{ JSON.stringify(previewWorldSetting, null, 2) }}</pre>
            </div>
          </div>

          <!-- 角色 -->
          <div v-if="settingResult.characters?.length" class="setting-section">
            <h3>角色（{{ settingResult.characters.length }} 个）</h3>
            <div v-for="char in settingResult.characters" :key="char.name" class="char-card">
              <div class="char-header">
                <a-tag :color="ROLE_TYPE_COLOR_MAP[char.roleType || char.role_type] || 'default'">
                  {{ ROLE_TYPE_TEXT_MAP[char.roleType || char.role_type] || char.roleType || char.role_type }}
                </a-tag>
                <strong>{{ char.name }}</strong>
              </div>
              <p class="char-desc">{{ char.personality || char.background }}</p>
            </div>
          </div>

          <!-- 卷大纲 -->
          <div v-if="previewVolumeOutline.length" class="setting-section">
            <h3>卷大纲</h3>
            <div v-for="vol in previewVolumeOutline" :key="vol.volume" class="vol-card">
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

    <a-modal
      v-model:open="ideaAssistantOpen"
      title="AI完善核心创意"
      width="820px"
      :footer="null"
    >
      <div class="idea-assistant">
        <div class="idea-assistant-section">
          <div class="idea-assistant-label">你的原始想法</div>
          <a-textarea
            v-model:value="ideaDraft"
            :rows="6"
            :maxlength="3000"
            show-count
            placeholder="例如：我想写一本类似无限流闯关的小说，主角觉醒武装天赋，只要得到敌人的身体，就能解析融合成一套铠甲，天赋可以逐渐升级解锁新功能。"
          />
        </div>

        <div class="idea-assistant-section">
          <div class="idea-assistant-label">额外要求（可选）</div>
          <a-textarea
            v-model:value="ideaRequirements"
            :rows="3"
            :maxlength="1200"
            show-count
            placeholder="例如：不要一开始无敌；能力要有代价；主线要有长期悬念；偏男频升级爽文。"
          />
        </div>

        <div class="idea-actions">
          <a-button @click="ideaAssistantOpen = false">关闭</a-button>
          <a-button type="primary" :loading="ideaEnhancing" @click="handleEnhanceIdea">
            <template #icon><BulbOutlined /></template>
            生成完善方案
          </a-button>
        </div>

        <div v-if="ideaResult" class="idea-result">
          <div v-if="ideaResult.logline" class="idea-result-block">
            <div class="idea-result-title">一句话卖点</div>
            <p>{{ ideaResult.logline }}</p>
          </div>

          <div v-if="ideaResult.enhancedCoreIdea" class="idea-result-block">
            <div class="idea-result-title">可直接使用的核心创意</div>
            <p class="idea-core-text">{{ ideaResult.enhancedCoreIdea }}</p>
          </div>

          <div v-if="ideaResult.titleSuggestions?.length" class="idea-result-block">
            <div class="idea-result-title">书名建议</div>
            <a-space wrap>
              <a-tag
                v-for="title in ideaResult.titleSuggestions"
                :key="title"
                color="green"
                class="idea-title-tag"
                @click="applySuggestedTitle(title)"
              >
                {{ title }}
              </a-tag>
            </a-space>
          </div>

          <div class="idea-result-grid">
            <div v-if="ideaResult.protagonistDesign" class="idea-mini-block">
              <div class="idea-result-title">主角设计</div>
              <p>{{ formatIdeaObject(ideaResult.protagonistDesign) }}</p>
            </div>
            <div v-if="ideaResult.powerSystem" class="idea-mini-block">
              <div class="idea-result-title">能力体系</div>
              <p>{{ formatIdeaObject(ideaResult.powerSystem) }}</p>
            </div>
          </div>

          <div v-if="ideaResult.worldRules?.length" class="idea-result-block">
            <div class="idea-result-title">世界规则</div>
            <ul>
              <li v-for="item in ideaResult.worldRules" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div v-if="ideaResult.mainConflicts?.length" class="idea-result-block">
            <div class="idea-result-title">主线冲突</div>
            <ul>
              <li v-for="item in ideaResult.mainConflicts" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div v-if="ideaResult.openingHook" class="idea-result-block">
            <div class="idea-result-title">开篇钩子</div>
            <p>{{ ideaResult.openingHook }}</p>
          </div>

          <div class="idea-assistant-section idea-feedback-section">
            <div class="idea-assistant-label">不满意？继续提修改意见</div>
            <a-textarea
              v-model:value="ideaFeedback"
              :rows="3"
              :maxlength="1200"
              show-count
              placeholder="例如：主角更狠一点；能力代价更明确；减少同质化无限流设定；反派压迫感更强。"
            />
          </div>

          <div class="idea-apply-actions">
            <a-button :loading="ideaEnhancing" @click="handleReviseIdea">
              <template #icon><BulbOutlined /></template>
              按意见再改
            </a-button>
            <a-button @click="copyEnhancedIdea">
              <template #icon><CopyOutlined /></template>
              复制方案
            </a-button>
            <a-button type="primary" @click="applyEnhancedIdea">
              <template #icon><CheckOutlined /></template>
              应用到核心创意
            </a-button>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { BulbOutlined, CheckOutlined, CopyOutlined } from '@ant-design/icons-vue'
import { createNovel, enhanceNovelIdea, getNovelTaskStatus } from '@/api/novelController'
import { connectNovelSSE } from '@/utils/novel'
import { NovelSseMessageType, GENRE_OPTIONS, TARGET_READERS_OPTIONS, GENRE_COLOR_MAP, ROLE_TYPE_TEXT_MAP, ROLE_TYPE_COLOR_MAP } from '@/constants/novel'

const router = useRouter()

const phase = ref<'INPUT' | 'GENERATING' | 'PREVIEW'>('INPUT')
const creating = ref(false)
const novelId = ref<number | null>(null)
const taskId = ref<string | null>(null)
const generatingStatus = ref('AI 正在构建世界观和角色...')
const recoveringTask = ref(false)
const ideaAssistantOpen = ref(false)
const ideaEnhancing = ref(false)
const ideaDraft = ref('')
const ideaRequirements = ref('')
const ideaFeedback = ref('')
const ideaResult = ref<Record<string, any> | null>(null)
let eventSource: EventSource | null = null

const form = reactive({
  title: '',
  genre: undefined as string | undefined,
  targetReaders: 'male',
  targetWordCount: 200000,
  coreIdea: '',
})

const settingResult = ref<any>(null)

onUnmounted(() => {
  eventSource?.close()
})

const previewWorldSetting = computed(() =>
  settingResult.value?.worldSetting || settingResult.value?.world_setting || null
)

const previewVolumeOutline = computed(() =>
  settingResult.value?.volumeOutline || settingResult.value?.volume_outline || []
)

const getGenreLabel = (genre: string) => {
  return GENRE_OPTIONS.find((g) => g.value === genre)?.label || genre
}

const openIdeaAssistant = () => {
  ideaDraft.value = form.coreIdea || ''
  ideaRequirements.value = ''
  ideaFeedback.value = ''
  ideaResult.value = null
  ideaAssistantOpen.value = true
}

const limitText = (text: string, maxLength: number) => {
  return text.length > maxLength ? text.slice(0, maxLength) : text
}

const requestIdeaEnhancement = async (rawIdea: string, requirements?: string, successText = '核心创意已完善') => {
  const normalizedIdea = rawIdea.trim()
  if (normalizedIdea.length < 5) {
    message.warning('请先输入你的小说创意')
    return
  }

  ideaEnhancing.value = true
  try {
    const res = await enhanceNovelIdea({
      rawIdea: limitText(normalizedIdea, 3000),
      genre: form.genre,
      targetReaders: form.targetReaders,
      requirements: requirements ? limitText(requirements.trim(), 1200) : undefined,
    })
    if (res.data.code === 0 && res.data.data) {
      ideaResult.value = res.data.data
      ideaFeedback.value = ''
      message.success(successText)
    } else {
      message.error(res.data.message || '创意完善失败')
    }
  } catch (error) {
    console.error('AI完善创意失败:', error)
    message.error('创意完善失败，请稍后重试')
  } finally {
    ideaEnhancing.value = false
  }
}

const handleEnhanceIdea = async () => {
  await requestIdeaEnhancement(
    ideaDraft.value,
    ideaRequirements.value.trim() || undefined,
    '核心创意已完善'
  )
}

const handleReviseIdea = async () => {
  if (!ideaResult.value) {
    message.warning('请先生成一版完善方案')
    return
  }
  if (!ideaFeedback.value.trim()) {
    message.warning('请先写下你想调整的方向')
    return
  }

  const previousIdea = buildEnhancedIdeaText() || ideaDraft.value
  const reviseRequirements = [
    ideaRequirements.value.trim() ? `原始额外要求：${ideaRequirements.value.trim()}` : '',
    `请基于上一版方案继续修改，不要完全推翻；重点处理这些反馈：${ideaFeedback.value.trim()}`,
  ]
    .filter(Boolean)
    .join('\n')

  await requestIdeaEnhancement(previousIdea, reviseRequirements, '已按意见重新完善')
}

const formatIdeaObject = (value?: Record<string, any> | null) => {
  if (!value || typeof value !== 'object') {
    return ''
  }
  return Object.entries(value)
    .filter(([, item]) => item !== undefined && item !== null && item !== '')
    .map(([key, item]) => {
      const text = Array.isArray(item) ? item.join('；') : String(item)
      return `${key}：${text}`
    })
    .join('；')
}

const buildEnhancedIdeaText = () => {
  const result = ideaResult.value
  if (!result) {
    return ''
  }

  const lines: string[] = []
  if (result.logline) lines.push(`【一句话卖点】${result.logline}`)
  if (result.enhancedCoreIdea) lines.push(`【核心创意】${result.enhancedCoreIdea}`)
  if (result.genrePositioning) lines.push(`【题材定位】${result.genrePositioning}`)
  if (result.protagonistDesign) lines.push(`【主角设计】${formatIdeaObject(result.protagonistDesign)}`)
  if (result.powerSystem) lines.push(`【能力体系】${formatIdeaObject(result.powerSystem)}`)
  if (Array.isArray(result.worldRules) && result.worldRules.length) {
    lines.push(`【世界规则】${result.worldRules.join('；')}`)
  }
  if (Array.isArray(result.mainConflicts) && result.mainConflicts.length) {
    lines.push(`【主线冲突】${result.mainConflicts.join('；')}`)
  }
  if (Array.isArray(result.longTermHooks) && result.longTermHooks.length) {
    lines.push(`【长线悬念】${result.longTermHooks.join('；')}`)
  }
  if (result.openingHook) lines.push(`【开篇钩子】${result.openingHook}`)
  return lines.join('\n')
}

const copyEnhancedIdea = async () => {
  const text = buildEnhancedIdeaText()
  if (!text) {
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制完善方案')
  } catch {
    message.error('复制失败')
  }
}

const applyEnhancedIdea = () => {
  const text = buildEnhancedIdeaText()
  if (!text) {
    return
  }
  form.coreIdea = text
  ideaAssistantOpen.value = false
  message.success('已应用到核心创意')
}

const applySuggestedTitle = (title: string) => {
  if (!title) {
    return
  }
  form.title = title
  message.success('已填入书名')
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
      taskId.value = data.taskId
      creating.value = false
      phase.value = 'GENERATING'
      generatingStatus.value = 'AI 正在构建世界观和角色...'
      connectTaskStream(data.taskId)
    } else {
      message.error(res.data.message || '创建失败')
      creating.value = false
    }
  } catch (e) {
    console.error('创建小说失败:', e)
    message.error('创建失败，请重试')
    creating.value = false
  }
}

const connectTaskStream = (tid: string) => {
  eventSource?.close()
  eventSource = connectNovelSSE(tid, {
    onMessage(msg) {
      if (msg.type === NovelSseMessageType.SETTING_GENERATING) {
        generatingStatus.value = typeof msg.data === 'string' ? msg.data : 'AI 正在构建世界观和角色...'
      } else if (msg.type === NovelSseMessageType.SETTING_GENERATED) {
        settingResult.value = msg.data
      }
    },
    onError() {
      recoverTask(tid)
    },
    onComplete() {
      phase.value = 'PREVIEW'
      message.success('设定生成成功！')
    },
    onClosed(msg) {
      if (msg?.type === NovelSseMessageType.ERROR) {
        message.error(msg.data?.message || '设定生成失败，请重试')
        phase.value = 'INPUT'
        creating.value = false
      }
      eventSource = null
    },
  })
}

const recoverTask = async (tid: string) => {
  if (recoveringTask.value) {
    return
  }
  recoveringTask.value = true

  try {
    const res = await getNovelTaskStatus({ taskId: tid })
    const task = res.data.data

    if (res.data.code !== 0 || !task) {
      message.error(res.data.message || '设定生成状态获取失败，请重试')
      phase.value = 'INPUT'
      return
    }

    if (Array.isArray(task.events)) {
      for (const event of task.events) {
        if (event?.type === NovelSseMessageType.SETTING_GENERATING) {
          generatingStatus.value =
            typeof event.data === 'string' ? event.data : 'AI 正在构建世界观和角色...'
        } else if (event?.type === NovelSseMessageType.SETTING_GENERATED) {
          settingResult.value = event.data
        }
      }
    }

    if (task.status === 'completed') {
      phase.value = 'PREVIEW'
      if (settingResult.value) {
        message.success('设定生成成功！')
      }
      return
    }

    if (task.status === 'failed') {
      message.error(task.error || '设定生成失败，请重试')
      phase.value = 'INPUT'
      return
    }

    connectTaskStream(tid)
  } catch (error) {
    console.error('恢复小说任务失败:', error)
    message.error('设定生成连接中断，请重试')
    phase.value = 'INPUT'
  } finally {
    creating.value = false
    recoveringTask.value = false
  }
}

const handleConfirm = () => {
  if (novelId.value) {
    router.push(`/novel/${novelId.value}/write`)
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

.core-idea-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
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

.idea-assistant {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.idea-assistant-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.idea-assistant-label,
.idea-result-title {
  font-size: 13px;
  font-weight: 600;
  color: #0F172A;
}

.idea-actions,
.idea-apply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.idea-result {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 4px;
  padding-top: 16px;
  border-top: 1px solid #E5E7EB;
}

.idea-feedback-section {
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  border-radius: 8px;
  padding: 12px 14px;
}

.idea-title-tag {
  cursor: pointer;
}

.idea-result-block,
.idea-mini-block {
  background: #F8FAFC;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 12px 14px;
}

.idea-result-block p,
.idea-mini-block p {
  margin: 8px 0 0;
  color: #374151;
  line-height: 1.7;
  white-space: pre-wrap;
}

.idea-core-text {
  font-size: 14px;
}

.idea-result-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.idea-result ul {
  margin: 8px 0 0;
  padding-left: 20px;
  color: #374151;
  line-height: 1.7;
}

@media (max-width: 768px) {
  .idea-result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
