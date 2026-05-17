"""小说异步任务服务"""

import asyncio
import json
import logging
import uuid
from typing import Optional, Dict, Any, Callable

from app.managers.sse_manager import sse_emitter_manager
from app.models.novel_enums import NovelSseMessageTypeEnum
from app.services.novel_agent_service import NovelAgentService
from app.services.novel_service import NovelService
from app.services.character_service import CharacterService

logger = logging.getLogger(__name__)


class NovelAsyncService:
    """小说异步任务管理服务

    负责：
    1. 创建异步任务（返回 task_id）
    2. 启动后台协程执行 Agent 调用
    3. 通过 SSE 推送进度给前端
    4. 处理错误和清理
    """

    def __init__(self, novel_service: NovelService,
                 agent_service: NovelAgentService,
                 character_service: CharacterService):
        self.novel_service = novel_service
        self.agent_service = agent_service
        self.character_service = character_service

    # ========== 章节生成（核心异步操作） ==========

    async def start_chapter_generation(self, novel_id: int, chapter_id: int,
                                       chapter_number: int,
                                       chapter_outline: str,
                                       author_note: Optional[str] = None) -> str:
        """启动章节生成任务，返回 task_id"""
        task_id = str(uuid.uuid4())
        # 创建 SSE 队列
        sse_emitter_manager.create_emitter(task_id)
        # 更新小说阶段
        await self.novel_service.update_novel_phase(novel_id, "CHAPTER_GENERATING")
        # 启动后台任务
        asyncio.create_task(
            self._execute_chapter_generation(
                novel_id, chapter_id, chapter_number, chapter_outline, author_note, task_id
            )
        )
        logger.info("章节生成任务已启动, task_id=%s, novel_id=%s, chapter=%s", task_id, novel_id, chapter_number)
        return task_id

    async def _execute_chapter_generation(self, novel_id: int, chapter_id: int,
                                          chapter_number: int,
                                          chapter_outline: str,
                                          author_note: Optional[str],
                                          task_id: str) -> None:
        """后台执行章节生成"""
        try:
            self._emit(task_id, NovelSseMessageTypeEnum.CHAPTER_GENERATING, "开始生成章节...")

            # 定义流式回调：每个 chunk 通过 SSE 推送
            def stream_handler(content: str):
                self._emit(task_id, NovelSseMessageTypeEnum.CHAPTER_STREAMING, content)

            # 调用写作助手
            full_content = await self.agent_service.agent4_write_chapter(
                novel_id=novel_id,
                chapter_outline=chapter_outline,
                author_note=author_note,
                stream_handler=stream_handler,
            )

            # 计算字数（中文字符数）
            word_count = len(full_content)
            # 保存正文到数据库
            await self.novel_service.update_chapter_content(chapter_id, full_content, word_count)
            await self.novel_service.update_chapter_status(chapter_id, "draft")

            # 发送完成消息
            self._emit(task_id, NovelSseMessageTypeEnum.CHAPTER_GENERATED, json.dumps({
                "chapterId": chapter_id,
                "chapterNumber": chapter_number,
                "wordCount": word_count,
            }, ensure_ascii=False))

            # 发送全部完成信号
            self._emit(task_id, NovelSseMessageTypeEnum.ALL_COMPLETE)

            # 更新小说阶段
            await self.novel_service.update_novel_phase(novel_id, "READY")

        except Exception as e:
            logger.error("章节生成失败, task_id=%s, error=%s", task_id, e)
            self._emit(task_id, NovelSseMessageTypeEnum.ERROR, str(e))
            await self.novel_service.update_novel_phase(novel_id, "READY")
        finally:
            sse_emitter_manager.complete(task_id)

    # ========== 归档（异步） ==========

    async def start_archive(self, novel_id: int, chapter_id: int,
                            chapter_number: int,
                            chapter_content: str) -> str:
        """启动归档任务，返回 task_id"""
        task_id = str(uuid.uuid4())
        sse_emitter_manager.create_emitter(task_id)
        asyncio.create_task(
            self._execute_archive(novel_id, chapter_id, chapter_number, chapter_content, task_id)
        )
        logger.info("归档任务已启动, task_id=%s, chapter_id=%s", task_id, chapter_id)
        return task_id

    async def _execute_archive(self, novel_id: int, chapter_id: int,
                               chapter_number: int,
                               chapter_content: str,
                               task_id: str) -> None:
        """后台执行归档"""
        try:
            self._emit(task_id, NovelSseMessageTypeEnum.ARCHIVING, "正在归档...")

            # 调用归档助手
            result = await self.agent_service.agent5_archive(novel_id, chapter_content)

            # 应用归档结果到数据库
            await self.agent_service._apply_archive_result(novel_id, chapter_id, chapter_number, result)

            # 更新章节状态为已确认
            await self.novel_service.update_chapter_status(chapter_id, "confirmed")

            # 发送完成消息
            self._emit(task_id, NovelSseMessageTypeEnum.ARCHIVE_COMPLETE, json.dumps({
                "chapterId": chapter_id,
                "summary": result.get("summary", ""),
                "wordCount": result.get("word_count", 0),
            }, ensure_ascii=False))

        except Exception as e:
            logger.error("归档失败, task_id=%s, error=%s", task_id, e)
            self._emit(task_id, NovelSseMessageTypeEnum.ERROR, f"归档失败: {str(e)}")
        finally:
            sse_emitter_manager.complete(task_id)

    # ========== 同步操作 ==========

    async def create_setting_sync(self, novel_id: int, title: str, genre: str,
                                  target_readers: Optional[str],
                                  core_idea: Optional[str],
                                  initial_characters: Optional[list]) -> Dict[str, Any]:
        """同步创建设定（Agent1）"""
        # 调用 Agent1
        result = await self.agent_service.agent1_create_setting(
            title=title, genre=genre,
            target_readers=target_readers,
            core_idea=core_idea,
            initial_characters=initial_characters,
        )

        # 保存世界观到数据库
        world_setting = result.get("world_setting")
        volume_outline = result.get("volume_outline")
        if world_setting:
            await self.novel_service.update_novel_setting(
                novel_id, world_setting=world_setting, volume_outline=volume_outline
            )

        # 创建初始角色
        characters = result.get("characters", [])
        for char_data in characters:
            await self.character_service.create_character(
                novel_id=novel_id,
                name=char_data.get("name", ""),
                role_type=char_data.get("role_type", "minor"),
                is_core=char_data.get("role_type") in ("protagonist", "antagonist"),
                appearance=char_data.get("appearance"),
                personality=char_data.get("personality"),
                background=char_data.get("background"),
                skills=char_data.get("skills"),
            )

        # 更新小说阶段
        await self.novel_service.update_novel_phase(novel_id, "READY")

        logger.info("设定创建完成, novel_id=%s", novel_id)
        return result

    async def analyze_style_sync(self, novel_id: int, samples: str) -> Dict[str, Any]:
        """同步分析风格（Agent2）"""
        result = await self.agent_service.agent2_analyze_style(samples)
        # 保存风格指南
        await self.novel_service.update_novel_setting(novel_id, style_guide=result)
        logger.info("风格分析完成, novel_id=%s", novel_id)
        return result

    async def plan_outline_sync(self, novel_id: int,
                                author_intent: Optional[str]) -> Dict[str, Any]:
        """同步规划大纲（Agent3）"""
        # 从已有章节中计算下一个章节号（避免删除后跳号）
        chapter_number = await self.novel_service.get_next_chapter_number(novel_id)

        result = await self.agent_service.agent3_plan_outline(novel_id, author_intent, chapter_number)

        # 创建章节记录
        novel = await self.novel_service.get_novel(novel_id)
        volume_number = novel.get("currentVolumeNumber", 1)

        chapter_id = await self.novel_service.create_chapter(
            novel_id=novel_id,
            volume_number=volume_number,
            chapter_number=chapter_number,
            title=result.get("chapter_title"),
            outline=result,
        )

        # 同步更新 novel 表的章节数和总字数
        await self.novel_service.recalculate_novel_stats(novel_id)

        result["chapterId"] = chapter_id
        result["chapterNumber"] = chapter_number
        logger.info("大纲规划完成, novel_id=%s, chapter=%s", novel_id, chapter_number)
        return result

    async def review_sync(self, novel_id: int) -> Dict[str, Any]:
        """同步连贯性检查（Agent6）"""
        result = await self.agent_service.agent6_review(novel_id)
        logger.info("连贯性检查完成, novel_id=%s", novel_id)
        return result

    # ========== 辅助方法 ==========

    def _emit(self, task_id: str, message_type: NovelSseMessageTypeEnum,
              data: Any = None) -> None:
        """发送 SSE 消息（JSON 格式）"""
        message = {
            "type": message_type.value,
            "data": data
        }
        sse_emitter_manager.send(task_id, json.dumps(message, ensure_ascii=False))

    def _emit_streaming(self, task_id: str, content: str) -> None:
        """发送流式内容 chunk"""
        self._emit(task_id, NovelSseMessageTypeEnum.CHAPTER_STREAMING, content)
