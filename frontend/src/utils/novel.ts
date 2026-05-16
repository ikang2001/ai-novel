/**
 * 小说相关工具函数
 */

import { connectSSE, type SSEOptions } from './sse'
import { CHAPTER_STATUS_COLOR_MAP } from '@/constants/novel'

/**
 * 连接小说 SSE 流
 */
export const connectNovelSSE = (taskId: string, options: SSEOptions): EventSource => {
  return connectSSE(`/api/novel/progress/${taskId}`, options)
}

/**
 * 获取章节状态颜色
 */
export const getChapterStatusColor = (status: string): string => {
  return CHAPTER_STATUS_COLOR_MAP[status] || '#6B7280'
}

/**
 * 计算总字数
 */
export const calculateTotalWordCount = (chapters: { wordCount?: number }[]): number => {
  return chapters.reduce((sum, ch) => sum + (ch.wordCount || 0), 0)
}

/**
 * 格式化字数显示
 */
export const formatWordCount = (count: number): string => {
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万字`
  }
  return `${count}字`
}

/**
 * 格式化小说进度
 */
export const formatNovelProgress = (current: number, target?: number): string => {
  if (!target) return `已写 ${current} 章`
  return `${current} / ${target} 章`
}
