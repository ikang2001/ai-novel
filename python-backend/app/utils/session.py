"""Session 管理工具"""

import json
from typing import Optional, Any, Dict, List

import redis.asyncio as redis

from app.config import settings

# Redis 连接池
redis_client: Optional[redis.Redis] = None
NOVEL_TASK_TTL_SECONDS = 3600
NOVEL_TASK_STREAM_MAX_LEN = settings.novel_task_stream_max_len


async def init_redis():
    """初始化 Redis 连接"""
    global redis_client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )


async def close_redis():
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        await redis_client.close()


def _get_session_key(session_id: str) -> str:
    """获取 Session Key"""
    return f"session:{session_id}"


async def get_session(session_id: str) -> Optional[dict]:
    """获取 Session 数据"""
    if not redis_client:
        return None
    
    key = _get_session_key(session_id)
    data = await redis_client.get(key)
    
    if data:
        return json.loads(data)
    return None


async def set_session(session_id: str, data: dict, expire: Optional[int] = None):
    """设置 Session 数据"""
    if not redis_client:
        return
    
    key = _get_session_key(session_id)
    expire_time = expire or settings.session_max_age
    
    await redis_client.setex(
        key,
        expire_time,
        json.dumps(data)
    )


async def remove_session(session_id: str):
    """删除 Session"""
    if not redis_client:
        return
    
    key = _get_session_key(session_id)
    await redis_client.delete(key)


def _get_novel_task_key(task_id: str) -> str:
    return f"novel:task:{task_id}"


def _get_novel_task_stream_key(task_id: str) -> str:
    return f"novel:task:{task_id}:events"


async def save_novel_task(task_id: str, payload: Dict[str, Any], expire: int = NOVEL_TASK_TTL_SECONDS):
    """保存小说任务状态。"""
    if not redis_client:
        return
    await redis_client.setex(_get_novel_task_key(task_id), expire, json.dumps(payload, ensure_ascii=False))


async def get_novel_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取小说任务状态。"""
    if not redis_client:
        return None
    data = await redis_client.get(_get_novel_task_key(task_id))
    return json.loads(data) if data else None


async def append_novel_task_event(task_id: str, event: Dict[str, Any], expire: int = NOVEL_TASK_TTL_SECONDS):
    """追加任务事件缓存，支持刷新后恢复。"""
    if not redis_client:
        return
    stream_key = _get_novel_task_stream_key(task_id)
    await redis_client.rpush(stream_key, json.dumps(event, ensure_ascii=False))
    await redis_client.ltrim(stream_key, -NOVEL_TASK_STREAM_MAX_LEN, -1)
    await redis_client.expire(stream_key, expire)


async def get_novel_task_events(task_id: str) -> List[Dict[str, Any]]:
    """读取任务事件缓存。"""
    if not redis_client:
        return []
    stream_key = _get_novel_task_stream_key(task_id)
    values = await redis_client.lrange(stream_key, 0, -1)
    return [json.loads(value) for value in values]
