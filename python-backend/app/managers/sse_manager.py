"""SSE Emitter 管理器"""

import asyncio
import json
import logging
from typing import Dict, Optional, Set

from fastapi.responses import StreamingResponse
from app.config import settings
from app.utils.session import get_novel_task, get_novel_task_events

logger = logging.getLogger(__name__)


class SseEmitterManager:
    """SSE Emitter 管理器"""

    def __init__(self):
        # 每个任务支持多个连接订阅
        self._queues: Dict[str, Set[asyncio.Queue]] = {}

    def create_emitter(self, task_id: str, redis_backed: bool = False) -> StreamingResponse:
        """
        创建 SSE Emitter

        Args:
            task_id: 任务ID

        Returns:
            StreamingResponse
        """
        if redis_backed:
            return self._create_redis_backed_emitter(task_id)

        queue: asyncio.Queue = asyncio.Queue()
        subscribers = self._queues.setdefault(task_id, set())
        subscribers.add(queue)

        logger.info(f"SSE 连接已创建, taskId={task_id}")

        # 创建事件流生成器
        async def event_generator():
            try:
                while True:
                    # 从队列获取消息
                    message = await queue.get()

                    # 如果是完成信号，结束流
                    if message == "__COMPLETE__":
                        break

                    # 格式化为 SSE 格式
                    yield f"data: {message}\n\n"
            except asyncio.CancelledError:
                logger.info(f"SSE 连接被取消, taskId={task_id}")
            except Exception as e:
                logger.error(f"SSE 连接错误, taskId={task_id}, error={e}")
            finally:
                subscribers = self._queues.get(task_id)
                if subscribers:
                    subscribers.discard(queue)
                    if not subscribers:
                        self._queues.pop(task_id, None)
                logger.info(f"SSE 连接已关闭, taskId={task_id}")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    def _create_redis_backed_emitter(self, task_id: str) -> StreamingResponse:
        """Create an SSE stream that polls Redis task events.

        This allows ARQ workers in another process to publish events through the
        existing Redis task cache without sharing in-memory queues.
        """

        async def event_generator():
            seen = 0
            idle_after_terminal = 0
            try:
                while True:
                    events = await get_novel_task_events(task_id)
                    if seen > len(events):
                        seen = 0
                    for event in events[seen:]:
                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    seen = len(events)

                    task = await get_novel_task(task_id)
                    if task and task.get("status") in {"completed", "failed"}:
                        idle_after_terminal += 1
                        if idle_after_terminal >= 2:
                            break
                    else:
                        idle_after_terminal = 0
                    await asyncio.sleep(settings.novel_sse_poll_interval_seconds)
            except asyncio.CancelledError:
                logger.info("Redis-backed SSE 连接被取消, taskId=%s", task_id)
            except Exception as e:
                logger.error("Redis-backed SSE 连接错误, taskId=%s, error=%s", task_id, e)
            finally:
                logger.info("Redis-backed SSE 连接已关闭, taskId=%s", task_id)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    def send(self, task_id: str, message: str):
        """
        发送消息
        
        Args:
            task_id: 任务ID
            message: 消息内容
        """
        queues = self._queues.get(task_id)
        if not queues:
            logger.debug(f"SSE Emitter 不存在, taskId={task_id}")
            return
        
        try:
            for queue in list(queues):
                queue.put_nowait(message)
            logger.debug(f"SSE 消息发送成功, taskId={task_id}")
        except Exception as e:
            logger.error(f"SSE 消息发送失败, taskId={task_id}, error={e}")
    
    def complete(self, task_id: str):
        """
        完成连接（生成任务结束后调用，负责清理队列）

        Args:
            task_id: 任务ID
        """
        queues = self._queues.get(task_id)
        if not queues:
            logger.debug(f"SSE Emitter 不存在, taskId={task_id}")
            return

        try:
            for queue in list(queues):
                queue.put_nowait("__COMPLETE__")
            logger.info(f"SSE 连接已完成, taskId={task_id}")
        except Exception as e:
            logger.error(f"SSE 连接完成失败, taskId={task_id}, error={e}")
    
    def exists(self, task_id: str) -> bool:
        """
        检查 Emitter 是否存在
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否存在
        """
        return bool(self._queues.get(task_id))


# 全局单例
sse_emitter_manager = SseEmitterManager()
