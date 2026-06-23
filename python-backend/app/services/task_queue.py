"""ARQ task queue helpers for long-running novel jobs."""

from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings


def get_arq_redis_settings() -> RedisSettings:
    host = "127.0.0.1" if settings.redis_host in {"localhost", "::1"} else settings.redis_host
    return RedisSettings(
        host=host,
        port=settings.redis_port,
        database=settings.redis_db,
        password=settings.redis_password or None,
    )


async def enqueue_novel_job(function_name: str, payload: dict):
    """Enqueue a novel job and close the short-lived producer connection."""
    redis = await create_pool(get_arq_redis_settings(), default_queue_name=settings.novel_queue_name)
    try:
        job = await redis.enqueue_job(
            function_name,
            payload,
            _job_id=f"novel:{payload.get('task_id')}",
            _queue_name=settings.novel_queue_name,
        )
        if job is None:
            raise RuntimeError("任务入队失败或任务ID重复")
        return job
    finally:
        await redis.close()
