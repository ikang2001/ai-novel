/**
 * 小说相关常量定义
 */

// 小说状态枚举
export enum NovelStatus {
  ONGOING = 'ongoing',
  COMPLETED = 'completed',
  PAUSED = 'paused',
}

// 小说阶段枚举
export enum NovelPhase {
  PENDING = 'PENDING',
  SETTING = 'SETTING',
  STYLE_ANALYZING = 'STYLE_ANALYZING',
  READY = 'READY',
  CHAPTER_PLANNING = 'CHAPTER_PLANNING',
  CHAPTER_GENERATING = 'CHAPTER_GENERATING',
  ARCHIVING = 'ARCHIVING',
  REVIEWING = 'REVIEWING',
}

// 章节状态枚举
export enum ChapterStatus {
  DRAFT = 'draft',
  CONFIRMED = 'confirmed',
  REVISED = 'revised',
}

// 角色类型枚举
export enum CharacterRoleType {
  PROTAGONIST = 'protagonist',
  SUPPORTING = 'supporting',
  ANTAGONIST = 'antagonist',
  MINOR = 'minor',
}

// 伏笔状态枚举
export enum ForeshadowingStatus {
  ACTIVE = 'active',
  RESOLVED = 'resolved',
  ABANDONED = 'abandoned',
}

// 伏笔类型枚举
export enum ForeshadowingCategory {
  CHARACTER = 'character',
  PLOT = 'plot',
  SETTING = 'setting',
  EMOTION = 'emotion',
}

// 小说SSE消息类型
export enum NovelSseMessageType {
  SETTING_GENERATING = 'SETTING_GENERATING',
  SETTING_GENERATED = 'SETTING_GENERATED',
  STYLE_ANALYZING = 'STYLE_ANALYZING',
  STYLE_ANALYZED = 'STYLE_ANALYZED',
  OUTLINE_GENERATING = 'OUTLINE_GENERATING',
  OUTLINE_GENERATED = 'OUTLINE_GENERATED',
  CHAPTER_GENERATING = 'CHAPTER_GENERATING',
  CHAPTER_STREAMING = 'CHAPTER_STREAMING',
  CHAPTER_GENERATED = 'CHAPTER_GENERATED',
  ARCHIVING = 'ARCHIVING',
  ARCHIVE_COMPLETE = 'ARCHIVE_COMPLETE',
  CONSISTENCY_CHECKING = 'CONSISTENCY_CHECKING',
  CONSISTENCY_RESULT = 'CONSISTENCY_RESULT',
  FORESHADOWING_ALERT = 'FORESHADOWING_ALERT',
  ERROR = 'ERROR',
  ALL_COMPLETE = 'ALL_COMPLETE',
}

// 小说状态文本映射
export const NOVEL_STATUS_TEXT_MAP: Record<string, string> = {
  [NovelStatus.ONGOING]: '连载中',
  [NovelStatus.COMPLETED]: '已完结',
  [NovelStatus.PAUSED]: '暂停',
}

// 小说状态颜色映射
export const NOVEL_STATUS_TAG_COLOR_MAP: Record<string, string> = {
  [NovelStatus.ONGOING]: 'processing',
  [NovelStatus.COMPLETED]: 'success',
  [NovelStatus.PAUSED]: 'warning',
}

// 章节状态文本映射
export const CHAPTER_STATUS_TEXT_MAP: Record<string, string> = {
  [ChapterStatus.DRAFT]: '草稿',
  [ChapterStatus.CONFIRMED]: '已确认',
  [ChapterStatus.REVISED]: '已修订',
}

// 章节状态颜色映射
export const CHAPTER_STATUS_COLOR_MAP: Record<string, string> = {
  [ChapterStatus.DRAFT]: '#3B82F6',
  [ChapterStatus.CONFIRMED]: '#22C55E',
  [ChapterStatus.REVISED]: '#F59E0B',
}

// 角色类型文本映射
export const ROLE_TYPE_TEXT_MAP: Record<string, string> = {
  [CharacterRoleType.PROTAGONIST]: '主角',
  [CharacterRoleType.SUPPORTING]: '配角',
  [CharacterRoleType.ANTAGONIST]: '反派',
  [CharacterRoleType.MINOR]: '龙套',
}

// 角色类型颜色映射
export const ROLE_TYPE_COLOR_MAP: Record<string, string> = {
  [CharacterRoleType.PROTAGONIST]: '#22C55E',
  [CharacterRoleType.SUPPORTING]: '#3B82F6',
  [CharacterRoleType.ANTAGONIST]: '#EF4444',
  [CharacterRoleType.MINOR]: '#6B7280',
}

// 伏笔状态文本映射
export const FORESHADOWING_STATUS_TEXT_MAP: Record<string, string> = {
  [ForeshadowingStatus.ACTIVE]: '活跃',
  [ForeshadowingStatus.RESOLVED]: '已揭示',
  [ForeshadowingStatus.ABANDONED]: '已放弃',
}

// 伏笔状态颜色映射
export const FORESHADOWING_STATUS_TAG_MAP: Record<string, string> = {
  [ForeshadowingStatus.ACTIVE]: 'success',
  [ForeshadowingStatus.RESOLVED]: 'default',
  [ForeshadowingStatus.ABANDONED]: 'error',
}

// 题材选项
export const GENRE_OPTIONS = [
  { value: 'xuanhuan', label: '玄幻' },
  { value: 'dushi', label: '都市' },
  { value: 'xuanyi', label: '悬疑' },
  { value: 'kehuang', label: '科幻' },
  { value: 'yanqing', label: '言情' },
  { value: 'lishi', label: '历史' },
  { value: 'qita', label: '其他' },
]

// 题材标签颜色
export const GENRE_COLOR_MAP: Record<string, string> = {
  xuanhuan: 'purple',
  dushi: 'blue',
  xuanyi: 'red',
  kehuang: 'cyan',
  yanqing: 'pink',
  lishi: 'orange',
  qita: 'default',
}

// 目标读者选项
export const TARGET_READERS_OPTIONS = [
  { value: 'male', label: '男频' },
  { value: 'female', label: '女频' },
  { value: 'general', label: '通用' },
]

// 状态筛选选项
export const NOVEL_STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: NovelStatus.ONGOING, label: '连载中' },
  { value: NovelStatus.COMPLETED, label: '已完结' },
  { value: NovelStatus.PAUSED, label: '暂停' },
]
