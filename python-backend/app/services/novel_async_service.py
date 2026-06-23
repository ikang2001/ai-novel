"""小说异步任务服务"""

import asyncio
import json
import logging
import uuid
from typing import Optional, Dict, Any, Callable, List

from app.exceptions import BusinessException, ErrorCode
from app.managers.sse_manager import sse_emitter_manager
from app.models.novel_enums import ChapterStatusEnum, NovelPhaseEnum, NovelSseMessageTypeEnum
from app.services.novel_agent_service import NovelAgentService
from app.services.novel_service import NovelService
from app.services.character_service import CharacterService
from app.services.revision_preference import build_revision_preference
from app.services.task_queue import enqueue_novel_job
from app.config import settings
from app.utils.session import (
    append_novel_task_event,
    get_novel_task,
    get_novel_task_events,
    save_novel_task,
)

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
        self._event_tasks: set[asyncio.Task] = set()

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态和缓存事件。"""
        task = await get_novel_task(task_id)
        if not task:
            raise ValueError("任务不存在")
        task["events"] = await get_novel_task_events(task_id)
        return task

    # ========== 章节生成（核心异步操作） ==========

    async def start_chapter_generation(self, novel_id: int, chapter_id: int,
                                       chapter_number: int,
                                       chapter_outline: str,
                                       author_note: Optional[str] = None,
                                       allowed_current_statuses: Optional[List[str]] = None) -> str:
        """启动章节生成任务，返回 task_id"""
        allowed_statuses = allowed_current_statuses or [
            ChapterStatusEnum.DRAFT.value,
            ChapterStatusEnum.REVISED.value,
            ChapterStatusEnum.FAILED.value,
        ]
        chapter = await self.novel_service.transition_chapter_status(
            chapter_id=chapter_id,
            allowed_current_statuses=allowed_statuses,
            target_status=ChapterStatusEnum.GENERATING.value,
        )
        if not chapter:
            raise BusinessException(ErrorCode.OPERATION_ERROR, "当前章节状态不允许生成")

        task_id = str(uuid.uuid4())
        await self._save_task_state(
            task_id,
            {
                "taskId": task_id,
                "taskType": "chapter_generation",
                "status": "pending",
                "novelId": novel_id,
                "chapterId": chapter_id,
                "chapterNumber": chapter_number,
                "phase": NovelPhaseEnum.CHAPTER_GENERATING.value,
            },
        )
        await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.CHAPTER_GENERATING.value)
        try:
            await self._dispatch_job(
                "execute_chapter_generation_job",
                {
                    "task_id": task_id,
                    "novel_id": novel_id,
                    "chapter_id": chapter_id,
                    "chapter_number": chapter_number,
                    "chapter_outline": chapter_outline,
                    "author_note": author_note,
                },
                lambda: self._execute_chapter_generation(
                    novel_id, chapter_id, chapter_number, chapter_outline, author_note, task_id
                ),
            )
        except Exception:
            await self.novel_service.update_chapter_status(chapter_id, ChapterStatusEnum.FAILED.value)
            await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.READY.value)
            await self._save_task_state(task_id, {"status": "failed", "error": "任务入队失败"})
            raise
        logger.info("章节生成任务已启动, task_id=%s, novel_id=%s, chapter=%s", task_id, novel_id, chapter_number)
        return task_id

    async def _execute_chapter_generation(self, novel_id: int, chapter_id: int,
                                          chapter_number: int,
                                          chapter_outline: str,
                                          author_note: Optional[str],
                                          task_id: str) -> None:
        """后台执行章节生成"""
        try:
            await self._save_task_state(task_id, {"status": "running"})
            await self._emit_async(task_id, NovelSseMessageTypeEnum.CONTEXT_PACKAGED, "正在组装上下文包...")

            # 定义流式回调：每个 chunk 通过 SSE 推送
            async def stream_handler(content: str):
                await self._emit_async(task_id, NovelSseMessageTypeEnum.CHAPTER_STREAMING, content)

            await self._emit_async(task_id, NovelSseMessageTypeEnum.CHAPTER_GENERATING, "开始生成章节...")
            generation_result = await self.agent_service.agent4_write_chapter_with_quality_loop(
                novel_id=novel_id,
                chapter_outline=chapter_outline,
                author_note=author_note,
                stream_handler=stream_handler,
                chapter_id=chapter_id,
                chapter_number=chapter_number,
            )
            full_content = generation_result["content"]
            draft_content = generation_result.get("draftContent") or full_content
            audit_report = generation_result.get("auditReport") or {}
            revised = bool(generation_result.get("revised"))

            await self.novel_service.create_context_snapshot(
                novel_id=novel_id,
                chapter_id=chapter_id,
                context_data=generation_result.get("contextPackage") or {},
                prompt_data=generation_result.get("promptData") or {},
                trace_data=(generation_result.get("contextPackage") or {}).get("trace") or {},
            )
            await self.novel_service.save_chapter_version(
                novel_id,
                chapter_id,
                "ai_draft",
                draft_content,
                meta_data={"chapterNumber": chapter_number},
            )
            await self._emit_async(task_id, NovelSseMessageTypeEnum.CHAPTER_REVIEWING, "正在审稿...")
            await self.novel_service.update_chapter_quality_report(chapter_id, audit_report)
            await self._emit_async(task_id, NovelSseMessageTypeEnum.CHAPTER_REVIEWED, audit_report)
            if revised:
                await self._emit_async(task_id, NovelSseMessageTypeEnum.CHAPTER_REVISING, "审稿发现问题，正在自动修订...")
                await self.novel_service.save_chapter_version(
                    novel_id,
                    chapter_id,
                    "auto_revised",
                    full_content,
                    meta_data={"chapterNumber": chapter_number, "auditReport": audit_report},
                )
                await self._emit_async(task_id, NovelSseMessageTypeEnum.CHAPTER_REVISED, {"wordCount": len(full_content)})

            # 计算字数（中文字符数）
            word_count = len(full_content)
            # 保存正文到数据库
            await self.novel_service.update_chapter_content(chapter_id, full_content, word_count)
            await self.novel_service.update_chapter_status(chapter_id, ChapterStatusEnum.DRAFT.value)

            # 发送完成消息
            payload = {
                "chapterId": chapter_id,
                "chapterNumber": chapter_number,
                "wordCount": word_count,
                "revised": revised,
                "qualityReport": audit_report,
            }
            await self._emit_async(task_id, NovelSseMessageTypeEnum.CHAPTER_GENERATED, payload)

            # 发送全部完成信号
            await self._emit_async(task_id, NovelSseMessageTypeEnum.ALL_COMPLETE)

            # 更新小说阶段
            await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.READY.value)
            await self._save_task_state(
                task_id,
                {"status": "completed", "result": payload, "phase": NovelPhaseEnum.READY.value},
            )

        except Exception as e:
            logger.error("章节生成失败, task_id=%s, error=%s", task_id, e)
            await self.novel_service.update_chapter_status(chapter_id, ChapterStatusEnum.FAILED.value)
            await self._emit_async(task_id, NovelSseMessageTypeEnum.ERROR, {"message": str(e)})
            await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.READY.value)
            await self._save_task_state(
                task_id,
                {"status": "failed", "error": str(e), "phase": NovelPhaseEnum.READY.value},
            )
        finally:
            await self._flush_event_tasks()
            sse_emitter_manager.complete(task_id)

    # ========== 归档（异步） ==========

    async def start_archive(self, novel_id: int, chapter_id: int,
                            chapter_number: int,
                            chapter_content: str,
                            allowed_current_statuses: Optional[List[str]] = None) -> str:
        """启动归档任务，返回 task_id"""
        allowed_statuses = allowed_current_statuses or [
            ChapterStatusEnum.DRAFT.value,
            ChapterStatusEnum.REVISED.value,
            ChapterStatusEnum.FAILED.value,
        ]
        chapter = await self.novel_service.transition_chapter_status(
            chapter_id=chapter_id,
            allowed_current_statuses=allowed_statuses,
            target_status=ChapterStatusEnum.ARCHIVING.value,
        )
        if not chapter:
            raise BusinessException(ErrorCode.OPERATION_ERROR, "当前章节状态不允许确认")

        task_id = str(uuid.uuid4())
        await self._save_task_state(
            task_id,
            {
                "taskId": task_id,
                "taskType": "chapter_archive",
                "status": "pending",
                "novelId": novel_id,
                "chapterId": chapter_id,
                "chapterNumber": chapter_number,
                "phase": NovelPhaseEnum.ARCHIVING.value,
            },
        )
        await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.ARCHIVING.value)
        try:
            await self._dispatch_job(
                "execute_archive_job",
                {
                    "task_id": task_id,
                    "novel_id": novel_id,
                    "chapter_id": chapter_id,
                    "chapter_number": chapter_number,
                    "chapter_content": chapter_content,
                },
                lambda: self._execute_archive(novel_id, chapter_id, chapter_number, chapter_content, task_id),
            )
        except Exception:
            await self.novel_service.update_chapter_status(chapter_id, ChapterStatusEnum.FAILED.value)
            await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.READY.value)
            await self._save_task_state(task_id, {"status": "failed", "error": "任务入队失败"})
            raise
        logger.info("归档任务已启动, task_id=%s, chapter_id=%s", task_id, chapter_id)
        return task_id

    async def _execute_archive(self, novel_id: int, chapter_id: int,
                               chapter_number: int,
                               chapter_content: str,
                               task_id: str) -> None:
        """后台执行归档"""
        try:
            await self._save_task_state(task_id, {"status": "running"})
            await self._emit_async(task_id, NovelSseMessageTypeEnum.ARCHIVING, "正在归档...")
            await self.novel_service.save_chapter_version(
                novel_id,
                chapter_id,
                "user_confirmed",
                chapter_content,
                meta_data={"chapterNumber": chapter_number},
            )
            ai_draft = await self.novel_service.get_latest_chapter_version(chapter_id, "ai_draft")
            if ai_draft and ai_draft.get("content"):
                previous_preference = await self.novel_service.get_novel_state(novel_id, "revision_preference")
                preference = build_revision_preference(
                    ai_draft=ai_draft.get("content") or "",
                    user_confirmed=chapter_content,
                    previous=(previous_preference or {}).get("stateData") if previous_preference else None,
                )
                await self.novel_service.upsert_novel_state(
                    novel_id,
                    "revision_preference",
                    preference,
                    source_chapter_id=chapter_id,
                )

            # 调用归档助手
            result = self._normalize_archive_result(
                await self.agent_service.agent5_archive(novel_id, chapter_content)
            )
            if result.get("wordCount", 0) <= 0:
                result["wordCount"] = len(chapter_content or "")

            # 应用归档结果到数据库
            await self.novel_service.with_transaction(
                lambda: self.agent_service._apply_archive_result(novel_id, chapter_id, chapter_number, result)
            )

            # 更新章节状态为已确认
            await self.novel_service.update_chapter_status(chapter_id, ChapterStatusEnum.CONFIRMED.value)
            await self.novel_service.recalculate_novel_stats(novel_id)

            # 发送完成消息
            payload = {
                "chapterId": chapter_id,
                "summary": result.get("summary", ""),
                "wordCount": result.get("wordCount", 0),
            }
            await self._emit_async(task_id, NovelSseMessageTypeEnum.ARCHIVE_COMPLETE, payload)
            await self._emit_async(task_id, NovelSseMessageTypeEnum.ALL_COMPLETE)
            await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.READY.value)
            await self._save_task_state(
                task_id,
                {"status": "completed", "result": payload, "phase": NovelPhaseEnum.READY.value},
            )

        except Exception as e:
            logger.exception(
                "归档失败, task_id=%s, novel_id=%s, chapter_id=%s, error=%s",
                task_id,
                novel_id,
                chapter_id,
                e,
            )
            await self.novel_service.update_chapter_status(chapter_id, ChapterStatusEnum.FAILED.value)
            await self._emit_async(task_id, NovelSseMessageTypeEnum.ERROR, {"message": f"归档失败: {str(e)}"})
            await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.READY.value)
            await self._save_task_state(
                task_id,
                {"status": "failed", "error": str(e), "phase": NovelPhaseEnum.READY.value},
            )
        finally:
            await self._flush_event_tasks()
            sse_emitter_manager.complete(task_id)

    # ========== 设定生成（异步操作） ==========

    async def start_setting_generation(self, novel_id: int, title: str, genre: str,
                                       target_readers: Optional[str],
                                       core_idea: Optional[str],
                                       initial_characters: Optional[list]) -> str:
        """启动设定生成任务，返回 task_id"""
        task_id = str(uuid.uuid4())
        await self._save_task_state(
            task_id,
            {
                "taskId": task_id,
                "taskType": "setting_generation",
                "status": "pending",
                "novelId": novel_id,
                "phase": NovelPhaseEnum.SETTING.value,
            },
        )
        await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.SETTING.value)
        try:
            await self._dispatch_job(
                "execute_setting_generation_job",
                {
                    "task_id": task_id,
                    "novel_id": novel_id,
                    "title": title,
                    "genre": genre,
                    "target_readers": target_readers,
                    "core_idea": core_idea,
                    "initial_characters": initial_characters,
                },
                lambda: self._execute_setting_generation(
                    novel_id, title, genre, target_readers, core_idea, initial_characters, task_id
                ),
            )
        except Exception:
            await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.PENDING.value)
            await self._save_task_state(task_id, {"status": "failed", "error": "任务入队失败"})
            raise
        logger.info("设定生成任务已启动, task_id=%s, novel_id=%s", task_id, novel_id)
        return task_id

    async def _execute_setting_generation(self, novel_id: int, title: str, genre: str,
                                          target_readers: Optional[str],
                                          core_idea: Optional[str],
                                          initial_characters: Optional[list],
                                          task_id: str) -> None:
        """后台执行设定生成"""
        try:
            await self._save_task_state(task_id, {"status": "running"})
            await self._emit_async(task_id, NovelSseMessageTypeEnum.SETTING_GENERATING, "AI 正在构建世界观和角色...")

            result = await self.agent_service.agent1_create_setting(
                title=title, genre=genre,
                target_readers=target_readers,
                core_idea=core_idea,
                initial_characters=initial_characters,
            )
            result = self._normalize_setting_result(result)

            # 保存世界观到数据库
            world_setting = result.get("worldSetting")
            volume_outline = result.get("volumeOutline")
            if world_setting:
                await self.novel_service.update_novel_setting(
                    novel_id, world_setting=world_setting, volume_outline=volume_outline
                )

            # 创建初始角色
            characters = result.get("characters", [])
            for char_data in characters:
                role_type = char_data.get("roleType", "minor")
                await self.character_service.create_character(
                    novel_id=novel_id,
                    name=char_data.get("name", ""),
                    role_type=role_type,
                    is_core=role_type in ("protagonist", "antagonist"),
                    appearance=char_data.get("appearance"),
                    personality=char_data.get("personality"),
                    background=char_data.get("background"),
                    skills=char_data.get("skills"),
                )

            # 更新小说阶段
            await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.READY.value)

            # 发送完成消息
            await self._emit_async(task_id, NovelSseMessageTypeEnum.SETTING_GENERATED, result)
            await self._emit_async(task_id, NovelSseMessageTypeEnum.ALL_COMPLETE)
            await self._save_task_state(
                task_id,
                {"status": "completed", "result": result, "phase": NovelPhaseEnum.READY.value},
            )
            logger.info("设定生成完成, task_id=%s, novel_id=%s", task_id, novel_id)

        except Exception as e:
            logger.error("设定生成失败, task_id=%s, error=%s", task_id, e)
            await self.novel_service.update_novel_phase(novel_id, NovelPhaseEnum.PENDING.value)
            await self._emit_async(task_id, NovelSseMessageTypeEnum.ERROR, {"message": str(e)})
            await self._save_task_state(
                task_id,
                {"status": "failed", "error": str(e), "phase": NovelPhaseEnum.PENDING.value},
            )
        finally:
            await self._flush_event_tasks()
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
        result = self._normalize_setting_result(result)

        # 保存世界观到数据库
        world_setting = result.get("worldSetting")
        volume_outline = result.get("volumeOutline")
        if world_setting:
            await self.novel_service.update_novel_setting(
                novel_id, world_setting=world_setting, volume_outline=volume_outline
            )

        # 创建初始角色
        characters = result.get("characters", [])
        for char_data in characters:
            role_type = char_data.get("roleType", "minor")
            await self.character_service.create_character(
                novel_id=novel_id,
                name=char_data.get("name", ""),
                role_type=role_type,
                is_core=role_type in ("protagonist", "antagonist"),
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

        result = self._normalize_outline_result(
            await self.agent_service.agent3_plan_outline(novel_id, author_intent, chapter_number)
        )

        # 创建章节记录
        novel = await self.novel_service.get_novel(novel_id)
        volume_number = novel.get("currentVolumeNumber", 1)

        chapter_id = await self.novel_service.create_chapter(
            novel_id=novel_id,
            volume_number=volume_number,
            chapter_number=chapter_number,
            title=result.get("chapterTitle"),
            outline=result,
        )
        await self.novel_service.update_chapter_memo(chapter_id, result)

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
        event_task = asyncio.create_task(append_novel_task_event(task_id, message))
        self._event_tasks.add(event_task)
        event_task.add_done_callback(self._event_tasks.discard)
        sse_emitter_manager.send(task_id, json.dumps(message, ensure_ascii=False))

    async def _emit_async(self, task_id: str, message_type: NovelSseMessageTypeEnum,
                          data: Any = None) -> None:
        """发送 SSE 消息，并按调用顺序写入 Redis 事件缓存。"""
        message = {
            "type": message_type.value,
            "data": data
        }
        await append_novel_task_event(task_id, message)
        sse_emitter_manager.send(task_id, json.dumps(message, ensure_ascii=False))

    def _emit_streaming(self, task_id: str, content: str) -> None:
        """发送流式内容 chunk"""
        self._emit(task_id, NovelSseMessageTypeEnum.CHAPTER_STREAMING, content)

    async def _save_task_state(self, task_id: str, patch: Dict[str, Any]) -> None:
        """增量保存任务状态。"""
        current = await get_novel_task(task_id) or {}
        current.update(patch)
        await save_novel_task(task_id, current)

    async def _dispatch_job(self, function_name: str, payload: Dict[str, Any], fallback: Callable[[], Any]) -> None:
        """Dispatch via ARQ; optionally fall back for local debugging."""
        if settings.novel_queue_enabled:
            await enqueue_novel_job(function_name, payload)
        else:
            asyncio.create_task(fallback())

    async def _flush_event_tasks(self) -> None:
        if self._event_tasks:
            await asyncio.gather(*list(self._event_tasks), return_exceptions=True)

    @staticmethod
    def _normalize_setting_result(result: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(result or {})
        normalized["worldSetting"] = result.get("worldSetting") or result.get("world_setting")
        normalized["volumeOutline"] = result.get("volumeOutline") or result.get("volume_outline") or []
        normalized["characters"] = [
            {
                **char_data,
                "roleType": char_data.get("roleType") or char_data.get("role_type", "minor"),
            }
            for char_data in result.get("characters", [])
        ]
        return normalized

    @staticmethod
    def _normalize_outline_result(result: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(result or {})
        normalized["chapterTitle"] = result.get("chapterTitle") or result.get("chapter_title")
        normalized["chapterHook"] = result.get("chapterHook") or result.get("chapter_hook")
        normalized["chapterTask"] = result.get("chapterTask") or result.get("chapter_task")
        normalized["readerExpectation"] = result.get("readerExpectation") or result.get("reader_expectation")
        normalized["previousEmotionalResidue"] = (
            result.get("previousEmotionalResidue") or result.get("previous_emotional_residue")
        )
        normalized["informationGap"] = result.get("informationGap") or result.get("information_gap")
        normalized["requiredEndingChange"] = result.get("requiredEndingChange") or result.get("required_ending_change")
        normalized["keyDialogues"] = result.get("keyDialogues") or result.get("key_dialogues") or []
        normalized["foreshadowingToUse"] = result.get("foreshadowingToUse") or result.get("foreshadowing_to_use") or []
        normalized["foreshadowingToPlant"] = result.get("foreshadowingToPlant") or result.get("foreshadowing_to_plant") or []
        normalized["hookOperations"] = result.get("hookOperations") or result.get("hook_operations") or []
        normalized["characterMotivations"] = (
            result.get("characterMotivations") or result.get("character_motivations") or []
        )
        normalized["prohibitions"] = result.get("prohibitions") or []
        normalized["scenes"] = [
            {
                **scene,
                "emotionalTone": scene.get("emotionalTone") or scene.get("emotional_tone"),
                "entryImage": scene.get("entryImage") or scene.get("entry_image"),
                "exitImage": scene.get("exitImage") or scene.get("exit_image"),
                "informationGap": scene.get("informationGap") or scene.get("information_gap"),
            }
            for scene in result.get("scenes", [])
        ]
        return normalized

    @staticmethod
    def _normalize_archive_result(result: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(result, dict):
            result = {}

        normalized = dict(result)
        normalized["summary"] = NovelAsyncService._normalize_text(result.get("summary"))
        normalized["wordCount"] = NovelAsyncService._normalize_int(
            result.get("wordCount", result.get("word_count")),
            default=0,
        )
        ending_state = result.get("endingState") or result.get("ending_state") or {}
        normalized["endingState"] = ending_state if isinstance(ending_state, dict) else {}
        normalized["readerExpectation"] = NovelAsyncService._normalize_text(
            result.get("readerExpectation") or result.get("reader_expectation")
        )
        normalized["timelineEvents"] = NovelAsyncService._normalize_dict_list(
            result.get("timelineEvents") or result.get("timeline_events")
        )
        normalized["styleMemoryUpdates"] = NovelAsyncService._normalize_string_list(
            result.get("styleMemoryUpdates") or result.get("style_memory_updates")
        )

        raw_character_updates = NovelAsyncService._normalize_dict_list(
            result.get("characterUpdates") or result.get("character_updates")
        )
        normalized["characterUpdates"] = []
        for char_update in raw_character_updates:
            updates = char_update.get("updates", {}) if isinstance(char_update.get("updates"), dict) else {}
            normalized["characterUpdates"].append({
                **char_update,
                "name": NovelAsyncService._normalize_text(char_update.get("name")),
                "action": NovelAsyncService._normalize_text(char_update.get("action")).lower(),
                "updates": {
                    **updates,
                    "roleType": NovelAsyncService._normalize_text(
                        updates.get("roleType") or updates.get("role_type"),
                        default="minor",
                    ),
                    "currentLocation": NovelAsyncService._normalize_text(
                        updates.get("currentLocation") or updates.get("current_location")
                    ),
                    "currentStatus": NovelAsyncService._normalize_text(
                        updates.get("currentStatus") or updates.get("current_status")
                    ),
                    "relationshipChanges": NovelAsyncService._normalize_text(
                        updates.get("relationshipChanges") or updates.get("relationship_changes")
                    ),
                    "newDetails": NovelAsyncService._normalize_text(
                        updates.get("newDetails") or updates.get("new_details")
                    ),
                },
            })

        raw_new_entities = NovelAsyncService._normalize_dict_list(
            result.get("newEntities") or result.get("new_entities")
        )
        normalized["newEntities"] = []
        for entity in raw_new_entities:
            details = entity.get("details", {}) if isinstance(entity.get("details"), dict) else {}
            normalized["newEntities"].append({
                **entity,
                "type": NovelAsyncService._normalize_text(entity.get("type")).lower(),
                "name": NovelAsyncService._normalize_text(entity.get("name")),
                "details": {
                    **details,
                    "roleType": NovelAsyncService._normalize_text(
                        details.get("roleType") or details.get("role_type"),
                        default="minor",
                    ),
                    "appearance": NovelAsyncService._normalize_text(details.get("appearance")),
                    "personality": NovelAsyncService._normalize_text(details.get("personality")),
                },
            })

        raw_fs_updates = NovelAsyncService._normalize_dict_list(
            result.get("foreshadowingUpdates") or result.get("foreshadowing_updates")
        )
        normalized["foreshadowingUpdates"] = []
        for fs_update in raw_fs_updates:
            normalized["foreshadowingUpdates"].append({
                **fs_update,
                "action": NovelAsyncService._normalize_text(fs_update.get("action")).lower(),
                "foreshadowingId": NovelAsyncService._normalize_int(
                    fs_update.get("foreshadowingId") or fs_update.get("foreshadowing_id")
                ),
                "surface": NovelAsyncService._normalize_text(fs_update.get("surface")),
                "hiddenTruth": NovelAsyncService._normalize_text(
                    fs_update.get("hiddenTruth") or fs_update.get("hidden_truth")
                ),
                "category": NovelAsyncService._normalize_text(fs_update.get("category")),
                "keywords": NovelAsyncService._normalize_string_list(fs_update.get("keywords")),
                "relatedCharacters": NovelAsyncService._normalize_string_list(
                    fs_update.get("relatedCharacters") or fs_update.get("related_characters")
                ),
                "importance": NovelAsyncService._normalize_int(fs_update.get("importance"), default=3),
                "targetChapter": NovelAsyncService._normalize_text(
                    fs_update.get("targetChapter") or fs_update.get("target_chapter")
                ),
                "lifecycleStage": NovelAsyncService._normalize_text(
                    fs_update.get("lifecycleStage") or fs_update.get("lifecycle_stage")
                ),
                "note": NovelAsyncService._normalize_text(fs_update.get("note")),
            })

        return normalized

    @staticmethod
    def _normalize_dict_list(value: Any) -> List[Dict[str, Any]]:
        if isinstance(value, dict):
            return [value]
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _normalize_string_list(value: Any) -> List[str]:
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @staticmethod
    def _normalize_text(value: Any, default: str = "") -> str:
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float, bool)):
            return str(value)
        return default

    @staticmethod
    def _normalize_int(value: Any, default: int = 0) -> int:
        if value is None or value == "":
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
