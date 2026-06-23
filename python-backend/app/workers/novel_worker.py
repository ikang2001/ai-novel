"""ARQ worker entrypoint for novel background jobs."""

import logging

from arq.connections import RedisSettings

from app.config import settings
from app.database import database
from app.services.character_service import CharacterService
from app.services.context_builder import ContextBuilder
from app.services.foreshadowing_service import ForeshadowingService
from app.services.novel_agent_service import NovelAgentService
from app.services.novel_async_service import NovelAsyncService
from app.services.novel_service import NovelService
from app.services.task_queue import get_arq_redis_settings
from app.utils.session import close_redis, init_redis

logger = logging.getLogger(__name__)


def _build_async_service() -> NovelAsyncService:
    novel_service = NovelService(database)
    character_service = CharacterService(database)
    foreshadowing_service = ForeshadowingService(database)
    context_builder = ContextBuilder(novel_service, character_service, foreshadowing_service)
    agent_service = NovelAgentService(novel_service, character_service, foreshadowing_service, context_builder)
    return NovelAsyncService(novel_service, agent_service, character_service)


async def startup(ctx):
    await database.connect()
    await init_redis()
    logger.info("Novel worker started")


async def shutdown(ctx):
    await database.disconnect()
    await close_redis()
    logger.info("Novel worker stopped")


async def execute_chapter_generation_job(ctx, payload: dict):
    service = _build_async_service()
    await service._execute_chapter_generation(
        novel_id=payload["novel_id"],
        chapter_id=payload["chapter_id"],
        chapter_number=payload["chapter_number"],
        chapter_outline=payload["chapter_outline"],
        author_note=payload.get("author_note"),
        task_id=payload["task_id"],
    )


async def execute_archive_job(ctx, payload: dict):
    service = _build_async_service()
    await service._execute_archive(
        novel_id=payload["novel_id"],
        chapter_id=payload["chapter_id"],
        chapter_number=payload["chapter_number"],
        chapter_content=payload["chapter_content"],
        task_id=payload["task_id"],
    )


async def execute_setting_generation_job(ctx, payload: dict):
    service = _build_async_service()
    await service._execute_setting_generation(
        novel_id=payload["novel_id"],
        title=payload["title"],
        genre=payload["genre"],
        target_readers=payload.get("target_readers"),
        core_idea=payload.get("core_idea"),
        initial_characters=payload.get("initial_characters"),
        task_id=payload["task_id"],
    )


class WorkerSettings:
    functions = [
        execute_chapter_generation_job,
        execute_archive_job,
        execute_setting_generation_job,
    ]
    redis_settings: RedisSettings = get_arq_redis_settings()
    queue_name = settings.novel_queue_name
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 2
    job_timeout = 900
