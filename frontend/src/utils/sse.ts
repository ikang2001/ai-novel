/**
 * SSE 工具函数
 * @author <a href="https://codefather.cn">编程导航学习圈</a>
 */

export interface SSEMessage {
  type: string
  data?: any
  [key: string]: any
}

export interface SSEOptions {
  onMessage: (message: SSEMessage) => void
  onError?: (error: Event) => void
  onComplete?: () => void
  onClosed?: (message?: SSEMessage) => void
}

/**
 * 建立 SSE 连接
 * @param url SSE 连接地址（如 /api/article/progress/{taskId} 或 /api/novel/progress/{taskId}）
 */
export const connectSSE = (url: string, options: SSEOptions): EventSource => {
  const { onMessage, onError, onComplete, onClosed } = options

  const eventSource = new EventSource(url)
  let closedByClient = false

  eventSource.onmessage = (event) => {
    try {
      const message: SSEMessage = JSON.parse(event.data)
      onMessage(message)

      // 检查是否完成
      if (message.type === 'ALL_COMPLETE') {
        closedByClient = true
        eventSource.close()
        onComplete?.()
        onClosed?.(message)
      } else if (message.type === 'ERROR') {
        closedByClient = true
        eventSource.close()
        onClosed?.(message)
      }
    } catch (error) {
      console.error('SSE 消息解析失败:', error)
    }
  }

  eventSource.onerror = (error) => {
    if (closedByClient || eventSource.readyState === EventSource.CLOSED) {
      return
    }
    console.error('SSE 连接错误:', error)
    onError?.(error)
    eventSource.close()
  }

  return eventSource
}

/**
 * 关闭 SSE 连接
 */
export const closeSSE = (eventSource: EventSource | null) => {
  if (eventSource) {
    eventSource.close()
  }
}
