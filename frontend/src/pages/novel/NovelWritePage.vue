<template>
  <div class="novel-write-page">
    <div class="mobile-toolbar">
      <a-button @click="showChapterDrawer = true">
        <template #icon><UnorderedListOutlined /></template>
        章节
      </a-button>
      <a-button @click="showRightDrawer = true">
        <template #icon><AppstoreOutlined /></template>
        信息面板
      </a-button>
    </div>

    <aside class="sidebar-left">
      <div class="sidebar-actions">
        <a-button type="primary" block @click="handlePlanChapter" :loading="planning">
          <template #icon><PlusOutlined /></template>
          规划新章节
        </a-button>
      </div>
      <ChapterList
        :chapters="chapters"
        :active-chapter-id="activeChapterId"
        @select="handleSelectChapter"
        @refresh="handleChapterListRefresh"
      />
    </aside>

    <main class="main-content">
      <div v-if="!activeChapterId" class="welcome-state">
        <BookOutlined class="welcome-icon" />
        <h2>{{ novel?.title || '小说写作' }}</h2>
        <p>从左侧选择一个章节开始写作，或规划一个新章节</p>
        <a-button type="primary" size="large" @click="handlePlanChapter" :loading="planning">
          <template #icon><PlusOutlined /></template>
          规划新章节
        </a-button>
      </div>

      <div v-else class="chapter-workspace">
        <div class="chapter-header">
          <div class="chapter-header-left">
            <h2 class="chapter-title">
              第{{ activeChapter?.chapterNumber }}章 {{ activeChapter?.title || '' }}
            </h2>
            <a-tag :color="chapterStatusColor" size="small">
              {{ CHAPTER_STATUS_TEXT_MAP[activeChapter?.status || ''] }}
            </a-tag>
            <a-tag v-if="currentTaskLabel" color="processing" size="small">
              {{ currentTaskLabel }}
            </a-tag>
          </div>
          <div class="chapter-header-actions">
            <a-button
              v-if="canGenerate"
              @click="handleGenerate"
              :loading="isTaskLoading && currentTaskType === 'chapter_generation'"
            >
              <template #icon><ThunderboltOutlined /></template>
              生成内容
            </a-button>
            <a-button
              v-if="canConfirm"
              @click="handleConfirm"
              :loading="isTaskLoading && currentTaskType === 'chapter_archive'"
            >
              <template #icon><CheckOutlined /></template>
              确认章节
            </a-button>
            <a-button
              v-if="canRegenerate"
              @click="handleRegenerate"
              :loading="isTaskLoading && currentTaskType === 'chapter_generation'"
            >
              <template #icon><RedoOutlined /></template>
              重新生成
            </a-button>
            <a-button v-if="canEdit" @click="startEdit">
              <template #icon><EditOutlined /></template>
              编辑
            </a-button>
          </div>
        </div>

        <ChapterStreamingContent
          v-if="isStreamingTask"
          :content="displayContent"
          :is-streaming="true"
          :chapter-title="activeChapter?.title"
        />

        <div v-else-if="isEditing" class="edit-area">
          <a-textarea v-model:value="editContent" :rows="30" class="edit-textarea" />
          <div class="edit-actions">
            <a-button @click="cancelEdit">取消</a-button>
            <a-button type="primary" @click="saveEdit" :loading="saving">保存</a-button>
          </div>
        </div>

        <ChapterStreamingContent
          v-else-if="displayContent"
          :content="displayContent"
          :is-streaming="false"
          :chapter-title="activeChapter?.title"
        />

        <div v-else class="empty-content">
          <p v-if="activeChapter?.status === ChapterStatus.FAILED">本章上次处理失败，可重新生成或确认修订后再归档</p>
          <p v-else>点击“生成内容”按钮，AI 将根据大纲生成章节正文</p>
        </div>
      </div>
    </main>

    <aside class="sidebar-right">
      <div class="right-panel">
        <a-tabs v-model:activeKey="rightTab" class="right-tabs">
          <a-tab-pane key="outline" tab="大纲">
            <div v-if="outlineTitle || outlineScenes.length || outlineHook" class="outline-content">
              <div v-if="outlineTitle" class="outline-title">
                {{ outlineTitle }}
              </div>
              <div v-for="scene in outlineScenes" :key="scene.scene" class="scene-item">
                <div class="scene-header">
                  <a-tag size="small">场景{{ scene.scene }}</a-tag>
                  <span class="scene-location">{{ scene.location }}</span>
                </div>
                <div class="scene-events">{{ scene.events }}</div>
              </div>
              <div v-if="outlineHook" class="chapter-hook">
                <strong>章末钩子：</strong>{{ outlineHook }}
              </div>
            </div>
            <a-empty v-else description="暂无大纲" />
          </a-tab-pane>

          <a-tab-pane key="memo" tab="备忘录">
            <div v-if="hasChapterMemo" class="memo-content">
              <div v-if="chapterMemo.chapterTask" class="memo-block">
                <div class="memo-label">本章任务</div>
                <div class="memo-text">{{ chapterMemo.chapterTask }}</div>
              </div>
              <div v-if="chapterMemo.readerExpectation" class="memo-block">
                <div class="memo-label">读者期待</div>
                <div class="memo-text">{{ chapterMemo.readerExpectation }}</div>
              </div>
              <div v-if="chapterMemo.previousEmotionalResidue" class="memo-block">
                <div class="memo-label">情绪承接</div>
                <div class="memo-text">{{ chapterMemo.previousEmotionalResidue }}</div>
              </div>
              <div v-if="chapterMemo.requiredEndingChange" class="memo-block">
                <div class="memo-label">章尾变化</div>
                <div class="memo-text">{{ chapterMemo.requiredEndingChange }}</div>
              </div>
              <div v-if="memoHookOperations.length" class="memo-block">
                <div class="memo-label">伏笔操作</div>
                <div v-for="(hook, idx) in memoHookOperations" :key="idx" class="memo-list-item">
                  {{ hook.action || 'advance' }}：{{ hook.surface || hook.reason || '未命名伏笔' }}
                </div>
              </div>
            </div>
            <a-empty v-else description="暂无备忘录" />
          </a-tab-pane>

          <a-tab-pane key="quality" tab="质量">
            <div v-if="qualityReport.summary || qualityIssues.length" class="quality-content">
              <a-tag :color="qualityIssues.length ? 'warning' : 'success'">
                {{ qualityReport.summary || '未发现明显问题' }}
              </a-tag>
              <div v-for="(issue, idx) in qualityIssues" :key="idx" class="quality-issue">
                <div class="quality-issue-header">
                  <a-tag :color="severityColor(issue.severity)" size="small">{{ issue.severity || 'low' }}</a-tag>
                  <span>{{ issue.type || 'issue' }}</span>
                </div>
                <div class="quality-issue-desc">{{ issue.description }}</div>
                <div v-if="issue.paragraphIndex || issue.evidenceText" class="quality-issue-location">
                  <a-tag v-if="issue.paragraphIndex" size="small">第{{ issue.paragraphIndex }}段</a-tag>
                  <span v-if="issue.evidenceText">{{ issue.evidenceText }}</span>
                </div>
                <div v-if="issue.suggestion" class="quality-issue-suggestion">{{ issue.suggestion }}</div>
              </div>
            </div>
            <a-empty v-else description="暂无质量报告" />
          </a-tab-pane>

          <a-tab-pane key="snapshot" tab="快照">
            <a-spin :spinning="loadingSnapshot">
              <div v-if="hasSnapshotData" class="snapshot-content">
                <div v-if="contextSnapshot?.createTime" class="snapshot-meta">
                  {{ contextSnapshot.version || 'v1' }} · {{ contextSnapshot.createTime }}
                </div>
                <a-collapse ghost>
                  <a-collapse-panel key="trace" header="检索 Trace">
                    <pre>{{ formatJson(contextSnapshot?.traceData) }}</pre>
                  </a-collapse-panel>
                  <a-collapse-panel key="context" header="上下文包">
                    <pre>{{ formatJson(contextSnapshot?.contextData) }}</pre>
                  </a-collapse-panel>
                  <a-collapse-panel key="prompt" header="最终 Prompt">
                    <pre>{{ snapshotPrompt || formatJson(contextSnapshot?.promptData) }}</pre>
                  </a-collapse-panel>
                  <a-collapse-panel key="versions" header="章节版本">
                    <div v-for="version in chapterVersions" :key="version.id" class="version-item">
                      <div class="version-header">
                        <a-tag size="small">{{ version.versionType }}</a-tag>
                        <span>{{ version.contentLength || 0 }}字</span>
                      </div>
                      <div class="version-preview">{{ version.contentPreview || '暂无预览' }}</div>
                    </div>
                    <a-empty v-if="!chapterVersions.length" description="暂无版本记录" />
                  </a-collapse-panel>
                </a-collapse>
              </div>
              <a-empty v-else description="暂无上下文快照" />
            </a-spin>
          </a-tab-pane>

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

          <a-tab-pane key="foreshadowing" tab="伏笔">
            <div v-for="fs in activeForeshadowing" :key="fs.id" class="side-fs">
              <div class="fs-surface">{{ summarizeText(fs.surface) }}</div>
              <div class="fs-meta">
                第{{ fs.plantedChapterId || '?' }}章 | 重要度: {{ fs.importance }}/5
                <span v-if="fs.lifecycleStage"> | {{ fs.lifecycleStage }}</span>
              </div>
            </div>
            <a-empty v-if="!activeForeshadowing.length" description="暂无活跃伏笔" />
            <a-button type="link" block @click="showForeshadowingPanel = true" style="margin-top: 8px">
              管理伏笔
            </a-button>
          </a-tab-pane>
        </a-tabs>

        <div v-if="logs.length" class="log-section">
          <div class="log-header">实时日志</div>
          <div class="log-list">
            <div v-for="(log, idx) in logs" :key="idx" class="log-item">
              <span class="log-time">{{ log.time }}</span>
              <span :class="['log-msg', `log-${log.type}`]">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <a-drawer
      :open="showChapterDrawer"
      placement="left"
      width="300"
      title="章节列表"
      @update:open="showChapterDrawer = $event"
    >
      <div class="drawer-actions">
        <a-button type="primary" block @click="handlePlanChapter" :loading="planning">
          <template #icon><PlusOutlined /></template>
          规划新章节
        </a-button>
      </div>
      <ChapterList
        :chapters="chapters"
        :active-chapter-id="activeChapterId"
        @select="handleSelectFromDrawer"
        @refresh="handleChapterListRefresh"
      />
    </a-drawer>

    <a-drawer
      :open="showRightDrawer"
      placement="right"
      width="320"
      title="章节信息"
      @update:open="showRightDrawer = $event"
    >
      <div class="right-panel drawer-panel">
        <a-tabs v-model:activeKey="rightTab" class="right-tabs">
          <a-tab-pane key="outline" tab="大纲">
            <div v-if="outlineTitle || outlineScenes.length || outlineHook" class="outline-content">
              <div v-if="outlineTitle" class="outline-title">{{ outlineTitle }}</div>
              <div v-for="scene in outlineScenes" :key="`drawer-${scene.scene}`" class="scene-item">
                <div class="scene-header">
                  <a-tag size="small">场景{{ scene.scene }}</a-tag>
                  <span class="scene-location">{{ scene.location }}</span>
                </div>
                <div class="scene-events">{{ scene.events }}</div>
              </div>
              <div v-if="outlineHook" class="chapter-hook">
                <strong>章末钩子：</strong>{{ outlineHook }}
              </div>
            </div>
            <a-empty v-else description="暂无大纲" />
          </a-tab-pane>

          <a-tab-pane key="memo" tab="备忘录">
            <div v-if="hasChapterMemo" class="memo-content">
              <div v-if="chapterMemo.chapterTask" class="memo-block">
                <div class="memo-label">本章任务</div>
                <div class="memo-text">{{ chapterMemo.chapterTask }}</div>
              </div>
              <div v-if="chapterMemo.readerExpectation" class="memo-block">
                <div class="memo-label">读者期待</div>
                <div class="memo-text">{{ chapterMemo.readerExpectation }}</div>
              </div>
              <div v-if="chapterMemo.previousEmotionalResidue" class="memo-block">
                <div class="memo-label">情绪承接</div>
                <div class="memo-text">{{ chapterMemo.previousEmotionalResidue }}</div>
              </div>
              <div v-if="chapterMemo.requiredEndingChange" class="memo-block">
                <div class="memo-label">章尾变化</div>
                <div class="memo-text">{{ chapterMemo.requiredEndingChange }}</div>
              </div>
              <div v-if="memoHookOperations.length" class="memo-block">
                <div class="memo-label">伏笔操作</div>
                <div v-for="(hook, idx) in memoHookOperations" :key="`drawer-hook-${idx}`" class="memo-list-item">
                  {{ hook.action || 'advance' }}：{{ hook.surface || hook.reason || '未命名伏笔' }}
                </div>
              </div>
            </div>
            <a-empty v-else description="暂无备忘录" />
          </a-tab-pane>

          <a-tab-pane key="quality" tab="质量">
            <div v-if="qualityReport.summary || qualityIssues.length" class="quality-content">
              <a-tag :color="qualityIssues.length ? 'warning' : 'success'">
                {{ qualityReport.summary || '未发现明显问题' }}
              </a-tag>
              <div v-for="(issue, idx) in qualityIssues" :key="`drawer-quality-${idx}`" class="quality-issue">
                <div class="quality-issue-header">
                  <a-tag :color="severityColor(issue.severity)" size="small">{{ issue.severity || 'low' }}</a-tag>
                  <span>{{ issue.type || 'issue' }}</span>
                </div>
                <div class="quality-issue-desc">{{ issue.description }}</div>
                <div v-if="issue.paragraphIndex || issue.evidenceText" class="quality-issue-location">
                  <a-tag v-if="issue.paragraphIndex" size="small">第{{ issue.paragraphIndex }}段</a-tag>
                  <span v-if="issue.evidenceText">{{ issue.evidenceText }}</span>
                </div>
                <div v-if="issue.suggestion" class="quality-issue-suggestion">{{ issue.suggestion }}</div>
              </div>
            </div>
            <a-empty v-else description="暂无质量报告" />
          </a-tab-pane>

          <a-tab-pane key="snapshot" tab="快照">
            <a-spin :spinning="loadingSnapshot">
              <div v-if="hasSnapshotData" class="snapshot-content">
                <div v-if="contextSnapshot?.createTime" class="snapshot-meta">
                  {{ contextSnapshot.version || 'v1' }} · {{ contextSnapshot.createTime }}
                </div>
                <a-collapse ghost>
                  <a-collapse-panel key="drawer-trace" header="检索 Trace">
                    <pre>{{ formatJson(contextSnapshot?.traceData) }}</pre>
                  </a-collapse-panel>
                  <a-collapse-panel key="drawer-context" header="上下文包">
                    <pre>{{ formatJson(contextSnapshot?.contextData) }}</pre>
                  </a-collapse-panel>
                  <a-collapse-panel key="drawer-prompt" header="最终 Prompt">
                    <pre>{{ snapshotPrompt || formatJson(contextSnapshot?.promptData) }}</pre>
                  </a-collapse-panel>
                  <a-collapse-panel key="drawer-versions" header="章节版本">
                    <div v-for="version in chapterVersions" :key="`drawer-version-${version.id}`" class="version-item">
                      <div class="version-header">
                        <a-tag size="small">{{ version.versionType }}</a-tag>
                        <span>{{ version.contentLength || 0 }}字</span>
                      </div>
                      <div class="version-preview">{{ version.contentPreview || '暂无预览' }}</div>
                    </div>
                    <a-empty v-if="!chapterVersions.length" description="暂无版本记录" />
                  </a-collapse-panel>
                </a-collapse>
              </div>
              <a-empty v-else description="暂无上下文快照" />
            </a-spin>
          </a-tab-pane>

          <a-tab-pane key="characters" tab="角色">
            <div v-for="char in characters" :key="`drawer-char-${char.id}`" class="side-char">
              <a-tag :color="ROLE_TYPE_COLOR_MAP[char.roleType || '']" size="small">
                {{ ROLE_TYPE_TEXT_MAP[char.roleType || ''] }}
              </a-tag>
              <span class="char-name">{{ char.name }}</span>
              <div v-if="char.currentStatus" class="char-status">{{ char.currentStatus }}</div>
            </div>
            <a-empty v-if="!characters.length" description="暂无角色" />
          </a-tab-pane>

          <a-tab-pane key="foreshadowing" tab="伏笔">
            <div v-for="fs in activeForeshadowing" :key="`drawer-fs-${fs.id}`" class="side-fs">
              <div class="fs-surface">{{ summarizeText(fs.surface) }}</div>
              <div class="fs-meta">
                第{{ fs.plantedChapterId || '?' }}章 | 重要度: {{ fs.importance }}/5
                <span v-if="fs.lifecycleStage"> | {{ fs.lifecycleStage }}</span>
              </div>
            </div>
            <a-empty v-if="!activeForeshadowing.length" description="暂无活跃伏笔" />
          </a-tab-pane>
        </a-tabs>

        <div v-if="logs.length" class="log-section">
          <div class="log-header">实时日志</div>
          <div class="log-list">
            <div v-for="(log, idx) in logs" :key="`drawer-log-${idx}`" class="log-item">
              <span class="log-time">{{ log.time }}</span>
              <span :class="['log-msg', `log-${log.type}`]">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </a-drawer>

    <CharacterPanel v-model:visible="showCharacterPanel" :novel-id="novelId" @refresh="loadAll" />
    <ForeshadowingPanel v-model:visible="showForeshadowingPanel" :novel-id="novelId" @refresh="loadAll" />

    <a-modal
      v-model:open="chapterRequirementOpen"
      :title="chapterRequirementTitle"
      ok-text="确认生成"
      cancel-text="取消"
      :confirm-loading="isTaskLoading && currentTaskType === 'chapter_generation'"
      @ok="confirmChapterRequirement"
    >
      <div class="chapter-requirement-modal">
        <div class="chapter-requirement-label">本章特别要求（可选）</div>
        <a-textarea
          v-model:value="chapterAuthorNote"
          :rows="5"
          :maxlength="1200"
          show-count
          placeholder="例如：开头必须接住上一章结尾；本章不要揭露幕后黑手；多写打斗和压迫感；章尾留下强悬念。"
        />
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  BookOutlined,
  PlusOutlined,
  ThunderboltOutlined,
  CheckOutlined,
  RedoOutlined,
  EditOutlined,
  UnorderedListOutlined,
  AppstoreOutlined,
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
  getNovelTaskStatus,
  getChapterContextSnapshot,
  getChapterVersions,
} from '@/api/novelController'
import { connectNovelSSE } from '@/utils/novel'
import {
  CHAPTER_STATUS_TEXT_MAP,
  CHAPTER_STATUS_COLOR_MAP,
  ROLE_TYPE_TEXT_MAP,
  ROLE_TYPE_COLOR_MAP,
  NovelSseMessageType,
  ChapterStatus,
} from '@/constants/novel'
import ChapterList from './components/ChapterList.vue'
import ChapterStreamingContent from './components/ChapterStreamingContent.vue'
import CharacterPanel from './components/CharacterPanel.vue'
import ForeshadowingPanel from './components/ForeshadowingPanel.vue'
import type { SSEMessage } from '@/utils/sse'

type LogItem = { time: string; type: string; message: string }
type TaskMode = 'generate' | 'regenerate' | 'confirm'
type ChapterGenerationMode = Extract<TaskMode, 'generate' | 'regenerate'>

const TASK_STORAGE_KEY = 'novel-active-task'

const route = useRoute()
const router = useRouter()
const novelId = Number(route.params.id)

const novel = ref<API.NovelVO | null>(null)
const chapters = ref<API.ChapterVO[]>([])
const characters = ref<API.CharacterVO[]>([])
const foreshadowing = ref<API.ForeshadowingVO[]>([])
const activeChapterId = ref<number | null>(null)
const activeChapter = ref<API.ChapterVO | null>(null)
const contextSnapshot = ref<API.ContextSnapshotVO | null>(null)
const chapterVersions = ref<API.ChapterVersionVO[]>([])
const loadingSnapshot = ref(false)

const planning = ref(false)
const isEditing = ref(false)
const editContent = ref('')
const saving = ref(false)
const rightTab = ref('outline')
const showCharacterPanel = ref(false)
const showForeshadowingPanel = ref(false)
const showChapterDrawer = ref(false)
const showRightDrawer = ref(false)
const chapterRequirementOpen = ref(false)
const chapterRequirementMode = ref<ChapterGenerationMode>('generate')
const chapterAuthorNote = ref('')

const logs = ref<LogItem[]>([])
const streamingContent = ref('')
const currentTaskId = ref<string | null>(null)
const currentTaskType = ref<string | null>(null)
const currentTaskStatus = ref<string | null>(null)
const currentTaskChapterId = ref<number | null>(null)
const lastTaskError = ref('')

let eventSource: EventSource | null = null

const activeForeshadowing = computed(() =>
  foreshadowing.value.filter((fs) => fs.status === 'active')
)

const chapterStatusColor = computed(() =>
  CHAPTER_STATUS_COLOR_MAP[activeChapter.value?.status || ''] || '#6B7280'
)

const isTaskLoading = computed(() =>
  ['pending', 'running'].includes(currentTaskStatus.value || '')
)

const isStreamingTask = computed(() =>
  isTaskLoading.value && activeChapter.value?.status === ChapterStatus.GENERATING
)

const displayContent = computed(() => {
  if (isStreamingTask.value) {
    return streamingContent.value || activeChapter.value?.content || ''
  }
  return activeChapter.value?.content || ''
})

const chapterRequirementTitle = computed(() =>
  chapterRequirementMode.value === 'regenerate' ? '重新生成前确认本章要求' : '生成前确认本章要求'
)

const canGenerate = computed(() =>
  [ChapterStatus.DRAFT, ChapterStatus.FAILED].includes(activeChapter.value?.status as ChapterStatus) && !isTaskLoading.value
)

const canConfirm = computed(() =>
  !!displayContent.value &&
  [ChapterStatus.DRAFT, ChapterStatus.REVISED, ChapterStatus.FAILED].includes(activeChapter.value?.status as ChapterStatus) &&
  !isTaskLoading.value
)

const canRegenerate = computed(() =>
  !!displayContent.value &&
  [ChapterStatus.DRAFT, ChapterStatus.REVISED, ChapterStatus.FAILED].includes(activeChapter.value?.status as ChapterStatus) &&
  !isTaskLoading.value
)

const canEdit = computed(() =>
  !!displayContent.value &&
  !isEditing.value &&
  ![ChapterStatus.GENERATING, ChapterStatus.ARCHIVING].includes(activeChapter.value?.status as ChapterStatus) &&
  !isTaskLoading.value
)

const currentTaskLabel = computed(() => {
  if (!isTaskLoading.value) {
    return ''
  }
  return currentTaskType.value === 'chapter_archive' ? '归档任务进行中' : '生成任务进行中'
})

const outlineData = computed<Record<string, any>>(() => {
  const raw = activeChapter.value?.outline
  if (!raw || typeof raw !== 'object') {
    return {}
  }
  return raw
})

const outlineTitle = computed(() =>
  outlineData.value.chapterTitle || outlineData.value.chapter_title || ''
)

const outlineScenes = computed(() =>
  Array.isArray(outlineData.value.scenes) ? outlineData.value.scenes : []
)

const outlineHook = computed(() =>
  outlineData.value.chapterHook || outlineData.value.chapter_hook || ''
)

const chapterMemo = computed<Record<string, any>>(() => {
  const raw = activeChapter.value?.chapterMemo || outlineData.value
  return raw && typeof raw === 'object' ? raw : {}
})

const hasChapterMemo = computed(() =>
  Boolean(
    chapterMemo.value.chapterTask ||
    chapterMemo.value.readerExpectation ||
    chapterMemo.value.previousEmotionalResidue ||
    chapterMemo.value.requiredEndingChange ||
    memoHookOperations.value.length
  )
)

const memoHookOperations = computed<Record<string, any>[]>(() =>
  Array.isArray(chapterMemo.value.hookOperations) ? chapterMemo.value.hookOperations : []
)

const qualityReport = computed<Record<string, any>>(() => {
  const raw = activeChapter.value?.qualityReport
  return raw && typeof raw === 'object' ? raw : {}
})

const qualityIssues = computed<Record<string, any>[]>(() =>
  Array.isArray(qualityReport.value.issues) ? qualityReport.value.issues : []
)

const hasSnapshotData = computed(() =>
  Boolean(
    contextSnapshot.value?.id ||
    contextSnapshot.value?.contextData ||
    contextSnapshot.value?.promptData ||
    contextSnapshot.value?.traceData ||
    chapterVersions.value.length
  )
)

const snapshotPrompt = computed(() => {
  const promptData = contextSnapshot.value?.promptData || {}
  return typeof promptData.prompt === 'string' ? promptData.prompt : ''
})

const formatJson = (value?: Record<string, any> | null) =>
  value && Object.keys(value).length ? JSON.stringify(value, null, 2) : '暂无数据'

const severityColor = (severity?: string) => {
  if (severity === 'high') {
    return 'error'
  }
  if (severity === 'medium') {
    return 'warning'
  }
  return 'default'
}

const summarizeText = (text?: string, maxLength = 40) => {
  if (!text) {
    return ''
  }
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text
}

const addLog = (logMessage: string, type: string = 'info') => {
  const time = new Date().toLocaleTimeString()
  logs.value.push({ time, type, message: logMessage })
  if (logs.value.length > 50) {
    logs.value.shift()
  }
}

const closeTaskStream = () => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

const clearCurrentTask = () => {
  closeTaskStream()
  currentTaskId.value = null
  currentTaskType.value = null
  currentTaskStatus.value = null
  currentTaskChapterId.value = null
  lastTaskError.value = ''
  sessionStorage.removeItem(TASK_STORAGE_KEY)
}

const persistTask = () => {
  if (!currentTaskId.value || !currentTaskChapterId.value) {
    return
  }
  sessionStorage.setItem(TASK_STORAGE_KEY, JSON.stringify({
    novelId,
    taskId: currentTaskId.value,
    chapterId: currentTaskChapterId.value,
  }))
}

const restorePersistedTaskId = (): { taskId: string; chapterId: number } | null => {
  const raw = sessionStorage.getItem(TASK_STORAGE_KEY)
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw)
    if (parsed?.novelId === novelId && parsed?.taskId && parsed?.chapterId) {
      return parsed
    }
  } catch {
    sessionStorage.removeItem(TASK_STORAGE_KEY)
  }
  return null
}

const loadNovel = async () => {
  const res = await getNovel({ novelId })
  if (res.data.code === 0) {
    novel.value = res.data.data || null
  }
}

const loadChapters = async () => {
  const res = await listChapters(novelId)
  if (res.data.code === 0) {
    chapters.value = res.data.data || []
  }
}

const handleChapterListRefresh = async () => {
  await loadChapters()
  await refreshCurrentChapter()
}

const loadCharacters = async () => {
  const res = await listCharacters(novelId)
  if (res.data.code === 0) {
    characters.value = res.data.data || []
  }
}

const loadForeshadowing = async () => {
  const res = await listForeshadowing(novelId)
  if (res.data.code === 0) {
    foreshadowing.value = res.data.data || []
  }
}

const loadAll = async () => {
  await Promise.all([loadNovel(), loadChapters(), loadCharacters(), loadForeshadowing()])
}

const loadChapterDetail = async (chapterId: number) => {
  const res = await getChapter({ chapterId })
  if (res.data.code === 0 && res.data.data) {
    activeChapter.value = res.data.data
    if (activeChapter.value.status !== ChapterStatus.GENERATING) {
      streamingContent.value = ''
    }
    await loadChapterDebugData(chapterId)
  }
}

const loadChapterDebugData = async (chapterId: number) => {
  loadingSnapshot.value = true
  try {
    const [snapshotRes, versionsRes] = await Promise.all([
      getChapterContextSnapshot({ chapterId }),
      getChapterVersions({ chapterId }),
    ])
    contextSnapshot.value = snapshotRes.data.code === 0 ? snapshotRes.data.data || null : null
    chapterVersions.value = versionsRes.data.code === 0 ? versionsRes.data.data || [] : []
  } finally {
    loadingSnapshot.value = false
  }
}

const refreshCurrentChapter = async () => {
  if (activeChapterId.value) {
    await loadChapterDetail(activeChapterId.value)
  }
}

const refreshAfterTask = async () => {
  await Promise.all([refreshCurrentChapter(), loadChapters(), loadNovel(), loadCharacters(), loadForeshadowing()])
}

const updateRouteChapter = (chapterId: number | null) => {
  router.replace({
    path: route.path,
    query: chapterId ? { ...route.query, chapter: String(chapterId) } : { ...route.query, chapter: undefined },
  })
}

const applyTaskStatus = async (task: API.TaskStatusVO, replayOnly = false) => {
  currentTaskId.value = task.taskId || null
  currentTaskType.value = task.taskType || null
  currentTaskStatus.value = task.status || null
  currentTaskChapterId.value = task.chapterId || null
  lastTaskError.value = task.error || ''
  if (currentTaskId.value && currentTaskChapterId.value) {
    persistTask()
  }

  if (task.chapterId && activeChapterId.value !== task.chapterId) {
    activeChapterId.value = task.chapterId
    updateRouteChapter(task.chapterId)
  }
  if (task.chapterId && !replayOnly) {
    await loadChapterDetail(task.chapterId)
  }

  if (task.events?.length) {
    logs.value = []
    if (!replayOnly) {
      streamingContent.value = ''
    }
    for (const event of task.events) {
      handleSSEMessage({ type: event.type || '', data: event.data }, true)
    }
  }

  if (task.status === 'completed' || task.status === 'failed') {
    await refreshAfterTask()
    clearCurrentTask()
  }
}

const connectTaskStream = (taskId: string) => {
  closeTaskStream()
  eventSource = connectNovelSSE(taskId, {
    onMessage: (msg) => handleSSEMessage(msg, false),
    onError: () => {
      addLog('实时连接中断，正在尝试通过任务状态恢复', 'error')
      recoverTask(taskId, true)
    },
    onComplete: async () => {
      const finishedTaskType = currentTaskType.value
      currentTaskStatus.value = 'completed'
      await refreshAfterTask()
      clearCurrentTask()
      if (finishedTaskType === 'chapter_archive') {
        message.success('章节归档完成')
      } else {
        message.success('章节生成完成')
      }
    },
    onClosed: async (msg) => {
      if (msg?.type === NovelSseMessageType.ERROR) {
        currentTaskStatus.value = 'failed'
        await refreshAfterTask()
        clearCurrentTask()
      }
    },
  })
}

const recoverTask = async (taskId: string, reconnectIfRunning = true) => {
  try {
    const res = await getNovelTaskStatus({ taskId })
    if (res.data.code !== 0 || !res.data.data) {
      clearCurrentTask()
      return
    }
    await applyTaskStatus(res.data.data)
    if (reconnectIfRunning && ['pending', 'running'].includes(res.data.data.status || '')) {
      connectTaskStream(taskId)
    }
  } catch {
    clearCurrentTask()
  }
}

const startTask = async (mode: TaskMode, authorNote?: string) => {
  if (!activeChapter.value?.id) {
    return
  }

  const normalizedAuthorNote = authorNote?.trim() || undefined

  try {
    logs.value = []
    lastTaskError.value = ''
    if (mode !== 'confirm') {
      streamingContent.value = ''
    }

    let res
    if (mode === 'generate') {
      res = await generateChapter(novelId, {
        chapterId: activeChapter.value.id,
        outline: activeChapter.value.outline || {},
        authorNote: normalizedAuthorNote,
      })
    } else if (mode === 'regenerate') {
      res = await regenerateChapter(activeChapter.value.id, {
        authorNote: normalizedAuthorNote,
      })
    } else {
      res = await confirmChapter(activeChapter.value.id)
    }

    if (res.data.code !== 0 || !res.data.data?.taskId) {
      message.error(res.data.message || '任务启动失败')
      return
    }

    currentTaskId.value = res.data.data.taskId
    currentTaskType.value = mode === 'confirm' ? 'chapter_archive' : 'chapter_generation'
    currentTaskStatus.value = 'pending'
    currentTaskChapterId.value = res.data.data.chapterId || activeChapter.value.id || null
    persistTask()
    addLog(mode === 'confirm' ? '归档任务已启动' : '生成任务已启动', 'info')
    await refreshCurrentChapter()
    connectTaskStream(res.data.data.taskId)
  } catch {
    message.error(mode === 'confirm' ? '确认失败' : '生成失败')
  }
}

const handleSSEMessage = (msg: SSEMessage, replayOnly = false) => {
  const payload = msg.data
  switch (msg.type) {
    case NovelSseMessageType.CONTEXT_PACKAGED:
      currentTaskStatus.value = 'running'
      addLog(typeof payload === 'string' ? payload : '上下文包已组装', 'info')
      break
    case NovelSseMessageType.CHAPTER_GENERATING:
      currentTaskStatus.value = 'running'
      addLog('正在生成章节...', 'info')
      break
    case NovelSseMessageType.CHAPTER_STREAMING:
      streamingContent.value += typeof payload === 'string' ? payload : payload?.content || ''
      break
    case NovelSseMessageType.CHAPTER_GENERATED:
      addLog('章节生成完成', 'success')
      break
    case NovelSseMessageType.CHAPTER_REVIEWING:
      addLog('正在审稿...', 'info')
      break
    case NovelSseMessageType.CHAPTER_REVIEWED:
      addLog('审稿完成', 'success')
      break
    case NovelSseMessageType.CHAPTER_REVISING:
      addLog(typeof payload === 'string' ? payload : '正在自动修订...', 'info')
      break
    case NovelSseMessageType.CHAPTER_REVISED:
      addLog('自动修订完成', 'success')
      break
    case NovelSseMessageType.ARCHIVING:
      currentTaskStatus.value = 'running'
      addLog('正在归档...', 'info')
      break
    case NovelSseMessageType.ARCHIVE_COMPLETE:
      addLog('归档完成', 'success')
      break
    case NovelSseMessageType.ERROR: {
      const errorText = typeof payload === 'string' ? payload : payload?.message || '未知错误'
      lastTaskError.value = errorText
      addLog(`错误: ${errorText}`, 'error')
      if (!replayOnly) {
        message.error(errorText)
      }
      break
    }
    case NovelSseMessageType.ALL_COMPLETE:
      addLog('全部完成', 'success')
      break
  }
}

const handleSelectChapter = async (id: number) => {
  activeChapterId.value = id
  updateRouteChapter(id)
  await loadChapterDetail(id)
  await tryRecoverChapterTask(id)
}

const handleSelectFromDrawer = async (id: number) => {
  showChapterDrawer.value = false
  await handleSelectChapter(id)
}

const tryRecoverChapterTask = async (chapterId: number) => {
  const persisted = restorePersistedTaskId()
  if (persisted && persisted.chapterId === chapterId) {
    await recoverTask(persisted.taskId)
    return
  }

  if ([ChapterStatus.GENERATING, ChapterStatus.ARCHIVING].includes(activeChapter.value?.status as ChapterStatus)) {
    clearCurrentTask()
    addLog('检测到章节处于处理中，但当前浏览器没有缓存任务 ID，请从同一浏览器继续等待或稍后刷新查看结果', 'info')
  }
}

const handlePlanChapter = async () => {
  planning.value = true
  try {
    const res = await planChapter(novelId, {})
    if (res.data.code === 0) {
      message.success('大纲规划成功')
      await loadChapters()
      await loadNovel()
      const data = res.data.data as Record<string, any> | undefined
      if (typeof data?.chapterId === 'number') {
        await handleSelectChapter(data.chapterId)
      }
    } else {
      message.error(res.data.message || '规划失败')
    }
  } catch {
    message.error('规划失败')
  } finally {
    planning.value = false
  }
}

const openChapterRequirement = (mode: ChapterGenerationMode) => {
  if (!activeChapter.value?.id) {
    return
  }
  chapterRequirementMode.value = mode
  chapterAuthorNote.value = ''
  chapterRequirementOpen.value = true
}

const confirmChapterRequirement = async () => {
  chapterRequirementOpen.value = false
  await startTask(chapterRequirementMode.value, chapterAuthorNote.value)
}

const handleGenerate = async () => {
  openChapterRequirement('generate')
}

const handleConfirm = async () => {
  await startTask('confirm')
}

const handleRegenerate = async () => {
  openChapterRequirement('regenerate')
}

const startEdit = () => {
  editContent.value = activeChapter.value?.content || ''
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
}

const saveEdit = async () => {
  if (!activeChapterId.value) {
    return
  }
  saving.value = true
  try {
    const res = await updateChapterContent(activeChapterId.value, { content: editContent.value })
    if (res.data.code === 0) {
      message.success('保存成功')
      isEditing.value = false
      await refreshAfterTask()
    } else {
      message.error(res.data.message || '保存失败')
    }
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

watch(
  () => route.query.chapter,
  async (chapter) => {
    if (!chapter) {
      return
    }
    const chapterId = Number(chapter)
    if (!chapterId || chapterId === activeChapterId.value) {
      return
    }
    activeChapterId.value = chapterId
    await loadChapterDetail(chapterId)
    await tryRecoverChapterTask(chapterId)
  }
)

onMounted(async () => {
  await loadAll()
  const chapterQuery = route.query.chapter
  if (chapterQuery) {
    const chapterId = Number(chapterQuery)
    if (chapterId) {
      activeChapterId.value = chapterId
      await loadChapterDetail(chapterId)
      await tryRecoverChapterTask(chapterId)
      return
    }
  }

  const persisted = restorePersistedTaskId()
  if (persisted) {
    activeChapterId.value = persisted.chapterId
    updateRouteChapter(persisted.chapterId)
    await loadChapterDetail(persisted.chapterId)
    await recoverTask(persisted.taskId)
  }
})

onBeforeUnmount(() => {
  closeTaskStream()
})
</script>

<style scoped>
.novel-write-page {
  display: grid;
  grid-template-columns: 260px 1fr 300px;
  height: calc(100vh - 64px);
  overflow: hidden;
}

.mobile-toolbar {
  display: none;
  padding: 12px 16px 0;
  gap: 8px;
  background: #fff;
  border-bottom: 1px solid #E5E7EB;
}

.mobile-toolbar :deep(.ant-btn) {
  flex: 1;
}

.sidebar-left {
  border-right: 1px solid #E5E7EB;
  background: #fff;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.sidebar-actions {
  padding: 12px;
  border-bottom: 1px solid #E5E7EB;
  flex-shrink: 0;
}

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
  padding: 24px;
  text-align: center;
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
  flex-wrap: wrap;
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
  flex-wrap: wrap;
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

.chapter-requirement-modal {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chapter-requirement-label {
  font-size: 13px;
  font-weight: 600;
  color: #0F172A;
}

.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9CA3AF;
  font-size: 15px;
  padding: 24px;
  text-align: center;
}

.sidebar-right {
  border-left: 1px solid #E5E7EB;
  background: #fff;
  overflow-y: auto;
}

.right-panel {
  padding: 0 12px 12px;
}

.drawer-panel {
  padding: 0;
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

.memo-block,
.quality-issue {
  background: #F8FAFC;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 8px;
}

.memo-label {
  font-size: 12px;
  font-weight: 600;
  color: #0F172A;
  margin-bottom: 4px;
}

.memo-text,
.memo-list-item {
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
}

.memo-list-item + .memo-list-item {
  margin-top: 4px;
}

.quality-content :deep(.ant-tag) {
  white-space: normal;
  line-height: 1.5;
  margin-bottom: 8px;
}

.quality-issue-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6B7280;
  margin-bottom: 6px;
}

.quality-issue-desc {
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
}

.quality-issue-location {
  margin-top: 6px;
  display: flex;
  gap: 6px;
  align-items: flex-start;
  font-size: 12px;
  color: #4B5563;
  line-height: 1.5;
}

.quality-issue-suggestion {
  margin-top: 6px;
  font-size: 12px;
  color: #166534;
  background: #F0FDF4;
  border-radius: 6px;
  padding: 6px;
  line-height: 1.5;
}

.snapshot-meta {
  font-size: 12px;
  color: #6B7280;
  margin-bottom: 8px;
}

.snapshot-content pre {
  max-height: 260px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background: #F8FAFC;
  border-radius: 6px;
  padding: 8px;
  font-size: 12px;
  line-height: 1.5;
  color: #374151;
}

.version-item {
  padding: 8px 0;
  border-bottom: 1px solid #F3F4F6;
}

.version-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #6B7280;
  margin-bottom: 4px;
}

.version-preview {
  font-size: 12px;
  color: #374151;
  line-height: 1.5;
  max-height: 96px;
  overflow: hidden;
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

.log-msg {
  color: #374151;
}

.log-error {
  color: #EF4444;
}

.log-success {
  color: #22C55E;
}

.drawer-actions {
  margin-bottom: 12px;
}

@media (max-width: 992px) {
  .novel-write-page {
    grid-template-columns: 1fr;
    height: auto;
    min-height: calc(100vh - 64px);
  }

  .mobile-toolbar {
    display: flex;
  }

  .sidebar-left,
  .sidebar-right {
    display: none;
  }

  .main-content {
    min-height: calc(100vh - 132px);
  }

  .chapter-header {
    padding: 16px;
  }

  .edit-area {
    padding: 16px;
  }
}
</style>
