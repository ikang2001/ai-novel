"""小说智能体服务"""

import json
import logging
import re
import inspect
import time
from typing import Optional, List, Dict, Any, Callable

from app.config import settings
from app.constants.novel_prompt import NovelPromptConstant
from app.services.context_builder import ContextBuilder
from app.services.llm_client import create_chat_client, get_chat_model
from app.services.prompt_crafter import PromptCrafter
from app.services.novel_service import NovelService
from app.services.character_service import CharacterService
from app.services.foreshadowing_service import ForeshadowingService

logger = logging.getLogger(__name__)


class NovelAgentService:
    """小说智能体服务——封装所有 LLM 调用"""

    def __init__(self, novel_service: NovelService,
                 character_service: CharacterService,
                 foreshadowing_service: ForeshadowingService,
                 context_builder: ContextBuilder):
        self.novel_service = novel_service
        self.character_service = character_service
        self.foreshadowing_service = foreshadowing_service
        self.context_builder = context_builder
        self.prompt_crafter = PromptCrafter()

        self.client = create_chat_client()
        self.model = get_chat_model()

    # ========== Agent 0：创意孵化助手 ==========

    async def agent0_enhance_core_idea(
        self,
        raw_idea: str,
        genre: Optional[str] = None,
        target_readers: Optional[str] = None,
        requirements: Optional[str] = None,
    ) -> Dict[str, Any]:
        """把作者的粗略点子完善成可用于开书的核心创意方案。"""
        prompt = NovelPromptConstant.AGENT0_IDEA_ENHANCE_PROMPT
        prompt = prompt.replace("{raw_idea}", raw_idea.strip())
        prompt = prompt.replace("{genre}", genre or "未指定")
        prompt = prompt.replace("{target_readers}", target_readers or "通用")
        prompt = prompt.replace("{requirements}", requirements or "无")

        content = await self._call_llm(prompt, stage="plan")
        result = self._extract_json_from_response(content)
        normalized = self._normalize_idea_enhancement(result, raw_idea)
        logger.info("Agent0 核心创意完善完成, raw_len=%s", len(raw_idea or ""))
        return normalized

    # ========== Agent 1：设定助手 ==========

    async def agent1_create_setting(self, title: str, genre: str,
                                    target_readers: Optional[str],
                                    core_idea: Optional[str],
                                    initial_characters: Optional[List[Dict]]) -> Dict[str, Any]:
        """设定助手：生成世界观 + 角色 + 卷大纲"""
        # 构建初始角色部分（如果用户提供了）
        initial_characters_section = ""
        if initial_characters:
            chars_text = json.dumps(initial_characters, ensure_ascii=False, indent=2)
            initial_characters_section = f"\n【用户提供的初始角色】\n{chars_text}\n请在此基础上完善和扩展。"

        prompt = NovelPromptConstant.AGENT1_SETTING_PROMPT.replace("{title}", title)
        prompt = prompt.replace("{genre}", genre)
        prompt = prompt.replace("{target_readers}", target_readers or "通用")
        prompt = prompt.replace("{core_idea}", core_idea or "无")
        prompt = prompt.replace("{initial_characters_section}", initial_characters_section)

        content = await self._call_llm(prompt, stage="plan")
        result = self._extract_json_from_response(content)
        logger.info("Agent1 设定生成成功, title=%s", title)
        return result

    # ========== Agent 2：风格分析 ==========

    async def agent2_analyze_style(self, samples: str) -> Dict[str, Any]:
        """风格分析助手：从样本中提取写作风格"""
        # 截取前 15000 字，避免超出上下文窗口
        truncated = samples[:15000] if len(samples) > 15000 else samples

        prompt = NovelPromptConstant.AGENT2_STYLE_ANALYZE_PROMPT.replace("{samples}", truncated)

        content = await self._call_llm(prompt, stage="plan")
        result = self._extract_json_from_response(content)
        logger.info("Agent2 风格分析完成")
        return result

    # ========== Agent 3：大纲助手 ==========

    async def agent3_plan_outline(self, novel_id: int,
                                  author_intent: Optional[str] = None,
                                  chapter_number: Optional[int] = None) -> Dict[str, Any]:
        """大纲助手：生成本章详细大纲"""
        # 读取小说信息
        novel = await self.novel_service.get_novel(novel_id)
        if not novel:
            raise ValueError(f"小说不存在: {novel_id}")

        # 读取角色状态
        char_states = await self.character_service.get_all_current_states(novel_id)
        states_text = "\n".join(
            f"- {s['name']}（{s['role_type']}）：在{s['location']}，{s['status']}"
            for s in char_states
        ) if char_states else "暂无"

        # 读取最近章节摘要
        recent = await self.novel_service.get_recent_chapters(novel_id, limit=3)
        summaries_text = "\n".join(
            f"第{c.get('chapterNumber', '?')}章：{c.get('summary', '暂无摘要')}"
            for c in recent
        ) if recent else "暂无（这是第一章）"

        # 读取活跃伏笔
        active_fs = await self.foreshadowing_service.get_active_foreshadowing(novel_id)
        fs_text = "\n".join(
            f"- {fs['surface']}" + (f"（真相：{fs['hiddenTruth']}）" if fs.get('hiddenTruth') else "")
            for fs in active_fs[:5]
        ) if active_fs else "暂无"

        # 构建作者意图部分
        author_intent_section = ""
        if author_intent:
            author_intent_section = NovelPromptConstant.AGENT3_AUTHOR_INTENT_SECTION.replace(
                "{author_intent}", author_intent
            )

        prompt = NovelPromptConstant.AGENT3_OUTLINE_PROMPT
        prompt = prompt.replace("{title}", novel.get("title", ""))
        prompt = prompt.replace("{genre}", novel.get("genre", ""))
        prompt = prompt.replace("{chapter_number}", str(chapter_number or novel.get("currentChapterNumber", 0) + 1))
        prompt = prompt.replace("{volume_number}", str(novel.get("currentVolumeNumber", 1)))
        prompt = prompt.replace("{character_states}", states_text)
        prompt = prompt.replace("{recent_summaries}", summaries_text)
        prompt = prompt.replace("{active_foreshadowing}", fs_text)
        prompt = prompt.replace("{author_intent_section}", author_intent_section)

        content = await self._call_llm(prompt, stage="plan")
        result = self._extract_json_from_response(content)
        logger.info("Agent3 大纲生成成功, novel_id=%s", novel_id)
        return result

    async def agent3_suggest_directions(self, novel_id: int) -> List[Dict[str, Any]]:
        """大纲助手（建议模式）：给出 2-3 个剧情方向"""
        novel = await self.novel_service.get_novel(novel_id)
        recent = await self.novel_service.get_recent_chapters(novel_id, limit=3)
        summaries_text = "\n".join(
            f"第{c.get('chapterNumber', '?')}章：{c.get('summary', '暂无')}"
            for c in recent
        ) if recent else "暂无"

        chapter_number = await self.novel_service.get_next_chapter_number(novel_id)

        prompt = NovelPromptConstant.AGENT3_AI_SUGGESTION_PROMPT
        prompt = prompt.replace("{title}", novel.get("title", ""))
        prompt = prompt.replace("{chapter_number}", str(chapter_number))
        prompt = prompt.replace("{recent_summaries}", summaries_text)

        content = await self._call_llm(prompt, stage="plan")
        result = self._extract_json_from_response(content)
        if not isinstance(result, list):
            result = [result] if isinstance(result, dict) else []
        return result

    # ========== Agent 4：写作助手 ==========

    async def agent4_write_chapter(self, novel_id: int,
                                   chapter_outline: Any,
                                   author_note: Optional[str] = None,
                                   stream_handler: Optional[Callable[[str], None]] = None,
                                   chapter_id: Optional[int] = None,
                                   chapter_number: Optional[int] = None) -> str:
        """兼容旧调用：返回质量闭环后的最终正文。"""
        result = await self.agent4_write_chapter_with_quality_loop(
            novel_id=novel_id,
            chapter_outline=chapter_outline,
            author_note=author_note,
            stream_handler=stream_handler,
            chapter_id=chapter_id,
            chapter_number=chapter_number,
        )
        return result["content"]

    async def agent4_write_chapter_with_quality_loop(
        self,
        novel_id: int,
        chapter_outline: Any,
        author_note: Optional[str] = None,
        stream_handler: Optional[Callable[[str], None]] = None,
        chapter_id: Optional[int] = None,
        chapter_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """写作助手：上下文包 -> 九层 prompt -> 初稿 -> 审稿 -> 最多一次修订。"""
        context_package = await self.context_builder.build_package(
            novel_id=novel_id,
            chapter_outline=chapter_outline,
            chapter_id=chapter_id,
            chapter_number=chapter_number,
        )
        prompt_data = self.prompt_crafter.craft_chapter_prompt(context_package, author_note)
        prompt = prompt_data["prompt"]

        if stream_handler:
            draft_content = await self._call_llm_streaming(prompt, stream_handler, stage="write")
        else:
            draft_content = await self._call_llm(prompt, stage="write")

        audit_report = await self.agent4_audit_draft(context_package, draft_content)
        final_content = draft_content
        revised = False
        if self._audit_requires_revision(audit_report):
            try:
                final_content = await self.agent4_revise_draft(context_package, draft_content, audit_report)
                revised = True
            except Exception as exc:
                logger.warning("自动修订失败，保留初稿, novel_id=%s, chapter=%s, error=%s", novel_id, chapter_number, exc)
                audit_report.setdefault("issues", []).append({
                    "type": "revision_failed",
                    "severity": "low",
                    "description": "自动修订失败，系统已保留 AI 初稿。",
                    "chapters": [chapter_number] if chapter_number else [],
                    "suggestion": str(exc),
                })

        logger.info(
            "Agent4 章节质量闭环完成, novel_id=%s, chapter=%s, draft=%d, final=%d, revised=%s",
            novel_id,
            chapter_number,
            len(draft_content),
            len(final_content),
            revised,
        )
        return {
            "content": final_content,
            "draftContent": draft_content,
            "auditReport": audit_report,
            "revised": revised,
            "contextPackage": context_package,
            "promptData": prompt_data,
        }

    async def agent4_audit_draft(self, context_package: Dict[str, Any],
                                 draft_content: str) -> Dict[str, Any]:
        """审稿助手：检查单章草稿。"""
        prompt = self.prompt_crafter.craft_audit_prompt(context_package, draft_content[:12000])
        try:
            content = await self._call_llm(prompt, stage="audit")
            result = self._extract_json_from_response(content)
        except Exception as exc:
            logger.warning("草稿审稿失败，跳过自动修订, error=%s", exc)
            return {
                "issues": [{
                    "type": "audit_failed",
                    "severity": "low",
                    "description": "草稿审稿失败，系统已保留生成正文。",
                    "chapters": [],
                    "suggestion": str(exc),
                }],
                "summary": "审稿失败，已降级保存草稿",
                "shouldRevise": False,
                "revisionBrief": "",
            }
        return self._normalize_audit_report(result, draft_content)

    async def agent4_revise_draft(self, context_package: Dict[str, Any],
                                  draft_content: str,
                                  audit_report: Dict[str, Any]) -> str:
        """修订助手：根据审稿报告修订正文。"""
        prompt = self.prompt_crafter.craft_revision_prompt(
            context_package=context_package,
            draft_content=draft_content,
            audit_report=audit_report,
        )
        return await self._call_llm(prompt, stage="revise")

    def _audit_requires_revision(self, audit_report: Dict[str, Any]) -> bool:
        """Only high/medium issues trigger the single automatic revision pass."""
        if audit_report.get("shouldRevise") is True:
            return True
        for issue in audit_report.get("issues") or []:
            if str(issue.get("severity", "")).lower() in {"high", "medium"}:
                return True
        return False

    @staticmethod
    def _normalize_audit_report(result: Any, draft_content: str = "") -> Dict[str, Any]:
        """Normalize audit report and enrich issue paragraph positions when possible."""
        if not isinstance(result, dict):
            result = {}
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", draft_content or "") if part.strip()]
        normalized_issues = []
        for raw_issue in result.get("issues") or []:
            if not isinstance(raw_issue, dict):
                continue
            issue = dict(raw_issue)
            issue["type"] = str(issue.get("type") or "issue")
            issue["severity"] = str(issue.get("severity") or "low").lower()
            issue["description"] = str(issue.get("description") or "")
            issue["suggestion"] = issue.get("suggestion") or ""

            evidence = issue.get("evidenceText") or issue.get("evidence_text") or ""
            paragraph_index = issue.get("paragraphIndex") or issue.get("paragraph_index")
            start_offset = issue.get("startOffset") or issue.get("start_offset")
            end_offset = issue.get("endOffset") or issue.get("end_offset")

            try:
                paragraph_index = int(paragraph_index) if paragraph_index not in (None, "") else None
            except (TypeError, ValueError):
                paragraph_index = None

            if not evidence and paragraph_index and 1 <= paragraph_index <= len(paragraphs):
                evidence = paragraphs[paragraph_index - 1][:160]

            if evidence and not paragraph_index:
                for index, paragraph in enumerate(paragraphs, start=1):
                    if evidence in paragraph:
                        paragraph_index = index
                        break

            if evidence and (start_offset in (None, "") or end_offset in (None, "")):
                found = (draft_content or "").find(evidence)
                if found >= 0:
                    start_offset = found
                    end_offset = found + len(evidence)

            for key, value in (("paragraphIndex", paragraph_index), ("startOffset", start_offset), ("endOffset", end_offset)):
                try:
                    issue[key] = int(value) if value not in (None, "") else None
                except (TypeError, ValueError):
                    issue[key] = None
            issue["evidenceText"] = str(evidence)[:240] if evidence else ""
            normalized_issues.append(issue)

        return {
            **result,
            "issues": normalized_issues,
            "summary": result.get("summary") or "未发现明显问题",
            "shouldRevise": bool(result.get("shouldRevise", result.get("should_revise", False))),
            "revisionBrief": result.get("revisionBrief") or result.get("revision_brief") or "",
        }

    # ========== Agent 5：归档助手 ==========

    async def agent5_archive(self, novel_id: int, chapter_content: str) -> Dict[str, Any]:
        """归档助手：分析本章内容，提取需要更新到知识库的信息"""
        # 读取当前角色列表
        all_chars = await self.character_service.get_all_characters(novel_id)
        chars_text = json.dumps(
            [{"name": c["name"], "roleType": c.get("roleType"), "status": c.get("currentStatus")}
             for c in all_chars],
            ensure_ascii=False
        ) if all_chars else "暂无"

        # 读取活跃伏笔
        active_fs = await self.foreshadowing_service.get_active_foreshadowing(novel_id)
        fs_text = json.dumps(
            [{"id": fs["id"], "surface": fs["surface"], "keywords": fs.get("keywords", [])}
             for fs in active_fs],
            ensure_ascii=False
        ) if active_fs else "暂无"

        # 截取正文（避免太长）
        truncated_content = chapter_content[:8000] if len(chapter_content) > 8000 else chapter_content

        prompt = NovelPromptConstant.AGENT5_ARCHIVE_PROMPT
        prompt = prompt.replace("{existing_characters}", chars_text)
        prompt = prompt.replace("{active_foreshadowing}", fs_text)
        prompt = prompt.replace("{chapter_content}", truncated_content)

        content = await self._call_llm(prompt, stage="archive")
        result = self._extract_json_from_response(content)
        logger.info("Agent5 归档分析完成, novel_id=%s", novel_id)
        return result

    async def _apply_archive_result(self, novel_id: int, chapter_id: int,
                                    chapter_number: int, result: Dict[str, Any]) -> None:
        """应用归档结果到数据库

        这是归档的核心——把 Agent 提取的信息写入各个表。
        """
        # 1. 更新章节摘要和字数
        summary = result.get("summary", "")
        word_count = result.get("wordCount", 0)
        if summary:
            await self.novel_service.update_chapter_summary(chapter_id, summary)
        if word_count > 0:
            # 只更新字数，不覆盖正文内容
            await self.novel_service._execute(
                "UPDATE chapter SET wordCount = :wc, updateTime = NOW() WHERE id = :id",
                {"wc": word_count, "id": chapter_id},
            )

        ending_state = result.get("endingState") or result.get("ending_state") or {}
        if isinstance(ending_state, dict) and ending_state:
            await self.novel_service.update_chapter_ending_state(chapter_id, ending_state)
            await self.novel_service.upsert_novel_state(
                novel_id,
                "current_state",
                ending_state,
                source_chapter_id=chapter_id,
            )
            if ending_state.get("readerExpectation"):
                await self.novel_service.upsert_novel_state(
                    novel_id,
                    "reader_expectation",
                    {"text": ending_state.get("readerExpectation")},
                    source_chapter_id=chapter_id,
                )
            if ending_state.get("characterStates"):
                await self.novel_service.update_chapter_character_states(
                    chapter_id,
                    {"characters": ending_state.get("characterStates")},
                )

        reader_expectation = result.get("readerExpectation") or result.get("reader_expectation")
        if reader_expectation:
            await self.novel_service.upsert_novel_state(
                novel_id,
                "reader_expectation",
                {"text": reader_expectation},
                source_chapter_id=chapter_id,
            )

        style_updates = result.get("styleMemoryUpdates") or result.get("style_memory_updates") or []
        if style_updates:
            await self.novel_service.upsert_novel_state(
                novel_id,
                "style_memory",
                {"updates": style_updates},
                source_chapter_id=chapter_id,
            )

        # 2. 处理角色更新
        for char_update in result.get("characterUpdates", []):
            name = char_update.get("name")
            action = char_update.get("action")
            updates = char_update.get("updates", {})

            if not name or action not in {"create", "update"}:
                logger.warning("跳过无效角色更新, novel_id=%s, chapter_id=%s, payload=%s", novel_id, chapter_id, char_update)
                continue

            if action == "create":
                # 新角色
                new_char_id = await self.character_service.create_character(
                    novel_id=novel_id,
                    name=name,
                    role_type=updates.get("roleType", "minor"),
                    appearance=updates.get("appearance"),
                    personality=updates.get("personality"),
                    skills=updates.get("skills"),
                )
                await self.character_service.set_last_appearance(new_char_id, chapter_id)
            elif action == "update":
                char = await self.character_service.find_by_name(novel_id, name)
                if char:
                    await self.character_service.update_character_state(
                        character_id=char["id"],
                        current_location=updates.get("currentLocation"),
                        current_status=updates.get("currentStatus"),
                        new_details=updates.get("newDetails"),
                    )
                    await self.character_service.set_last_appearance(char["id"], chapter_id)

        # 3. 处理新实体
        for entity in result.get("newEntities", []):
            entity_type = entity.get("type")
            name = entity.get("name")
            details = entity.get("details", {})

            if not name:
                logger.warning("跳过无效新实体, novel_id=%s, chapter_id=%s, payload=%s", novel_id, chapter_id, entity)
                continue

            if entity_type == "character":
                # 检查是否已存在
                existing = await self.character_service.find_by_name(novel_id, name)
                if not existing:
                    await self.character_service.create_character(
                        novel_id=novel_id,
                        name=name,
                        role_type=details.get("roleType", "minor"),
                        appearance=details.get("appearance"),
                        personality=details.get("personality"),
                    )

        # 4. 处理伏笔更新
        for fs_update in result.get("foreshadowingUpdates", []):
            action = fs_update.get("action")

            note = fs_update.get("note") or fs_update.get("lastActionNote")
            lifecycle_stage = fs_update.get("lifecycleStage") or fs_update.get("lifecycle_stage")

            if action == "plant":
                surface = fs_update.get("surface", "")
                if not surface:
                    logger.warning("跳过无效伏笔创建, novel_id=%s, chapter_id=%s, payload=%s", novel_id, chapter_id, fs_update)
                    continue
                # 新埋伏笔
                new_fs_id = await self.foreshadowing_service.create_foreshadowing(
                    novel_id=novel_id,
                    surface=surface,
                    hidden_truth=fs_update.get("hiddenTruth"),
                    category=fs_update.get("category"),
                    related_characters=fs_update.get("relatedCharacters"),
                    keywords=fs_update.get("keywords"),
                    target_chapter=fs_update.get("targetChapter") or fs_update.get("target_chapter"),
                    importance=fs_update.get("importance", 3),
                    planted_chapter_id=chapter_id,
                )
                if lifecycle_stage:
                    await self.foreshadowing_service.update_lifecycle(
                        new_fs_id,
                        lifecycle_stage,
                        action_type="plant",
                        chapter_number=chapter_number,
                        note=note or "本章新埋伏笔",
                    )
            elif action == "resolve":
                fs_id = fs_update.get("foreshadowingId")
                if fs_id:
                    await self.foreshadowing_service.resolve_foreshadowing(fs_id, chapter_id)
                    if lifecycle_stage:
                        await self.foreshadowing_service.update_lifecycle(
                            fs_id,
                            lifecycle_stage,
                            action_type="resolve",
                            chapter_number=chapter_number,
                            note=note or "本章揭示伏笔",
                        )
                else:
                    logger.warning("跳过无效伏笔揭示, novel_id=%s, chapter_id=%s, payload=%s", novel_id, chapter_id, fs_update)
            elif action in {"mention", "advance"}:
                fs_id = fs_update.get("foreshadowingId")
                if fs_id:
                    await self.foreshadowing_service.record_mention(
                        fs_id, chapter_id, chapter_number, context=note or fs_update.get("surface")
                    )
                    if lifecycle_stage:
                        await self.foreshadowing_service.update_lifecycle(
                            fs_id,
                            lifecycle_stage,
                            action_type=action,
                            chapter_number=chapter_number,
                            note=note or "本章推进伏笔",
                        )
                else:
                    logger.warning("跳过无效伏笔呼应, novel_id=%s, chapter_id=%s, payload=%s", novel_id, chapter_id, fs_update)
            elif action == "defer":
                fs_id = fs_update.get("foreshadowingId")
                if fs_id:
                    await self.foreshadowing_service.update_lifecycle(
                        fs_id,
                        lifecycle_stage or "open",
                        action_type="defer",
                        chapter_number=chapter_number,
                        note=note or "本章明确暂缓",
                    )
                else:
                    logger.warning("跳过无效伏笔暂缓, novel_id=%s, chapter_id=%s, payload=%s", novel_id, chapter_id, fs_update)
            elif action:
                logger.warning("未知伏笔动作, novel_id=%s, chapter_id=%s, payload=%s", novel_id, chapter_id, fs_update)

        logger.info("归档结果应用完成, novel_id=%s, chapter_id=%s", novel_id, chapter_id)

    # ========== Agent 6：审查助手 ==========

    async def agent6_review(self, novel_id: int) -> Dict[str, Any]:
        """审查助手：检查小说的连贯性问题"""
        novel = await self.novel_service.get_novel(novel_id)
        if not novel:
            raise ValueError(f"小说不存在: {novel_id}")

        # 读取全书摘要
        all_chapters = await self.novel_service.get_chapters_by_novel(novel_id)
        summaries = "\n".join(
            f"第{c.get('chapterNumber', '?')}章 {c.get('title', '')}：{c.get('summary', '暂无')}"
            for c in all_chapters if c.get("summary")
        ) or "暂无章节摘要"

        # 读取角色表
        all_chars = await self.character_service.get_all_characters(novel_id)
        chars_text = "\n".join(
            f"- {c['name']}（{c.get('roleType', '?')}）：{c.get('appearance', '')}，"
            f"性格：{c.get('personality', '')}，技能：{c.get('skills', '')}"
            for c in all_chars
        ) or "暂无角色"

        # 读取伏笔表
        all_fs = await self.foreshadowing_service.get_all_foreshadowing(novel_id)
        fs_text = "\n".join(
            f"- [{fs['status']}] {fs['surface']}"
            + (f"（真相：{fs['hiddenTruth']}）" if fs.get('hiddenTruth') else "")
            for fs in all_fs
        ) or "暂无伏笔"

        prompt = NovelPromptConstant.AGENT6_REVIEW_PROMPT
        prompt = prompt.replace("{title}", novel.get("title", ""))
        prompt = prompt.replace("{total_chapters}", str(len(all_chapters)))
        prompt = prompt.replace("{all_summaries}", summaries[:5000])  # 截取避免过长
        prompt = prompt.replace("{all_characters}", chars_text[:3000])
        prompt = prompt.replace("{all_foreshadowing}", fs_text[:2000])

        content = await self._call_llm(prompt, stage="audit")
        result = self._extract_json_from_response(content)
        logger.info("Agent6 连贯性检查完成, novel_id=%s", novel_id)
        return result

    # ========== 卷摘要生成 ==========

    async def generate_volume_summary(self, novel_id: int, volume_number: int,
                                      chapter_summaries: List[str]) -> str:
        """生成卷摘要（压缩该卷所有章节摘要）"""
        summaries_text = "\n".join(chapter_summaries)
        prompt = NovelPromptConstant.CHAPTER_SUMMARY_COMPRESS_PROMPT.replace(
            "{summaries}", summaries_text
        ).replace("{target_words}", "500")

        content = await self._call_llm(prompt, stage="archive")
        logger.info("卷摘要生成完成, novel_id=%s, volume=%d", novel_id, volume_number)
        return content

    async def generate_synopsis(self, novel_id: int) -> str:
        """生成全书梗概（压缩所有卷摘要）"""
        # 获取所有章节摘要
        all_chapters = await self.novel_service.get_chapters_by_novel(novel_id)
        summaries = [c.get("summary", "") for c in all_chapters if c.get("summary")]

        summaries_text = "\n".join(summaries)
        prompt = NovelPromptConstant.CHAPTER_SUMMARY_COMPRESS_PROMPT.replace(
            "{summaries}", summaries_text
        ).replace("{target_words}", "800")

        content = await self._call_llm(prompt, stage="archive")

        # 保存到数据库
        await self.novel_service.update_synopsis(novel_id, content)
        logger.info("全书梗概生成完成, novel_id=%s", novel_id)
        return content

    # ========== LLM 调用封装 ==========

    async def _call_llm(self, prompt: str, stage: Optional[str] = None) -> str:
        """非流式调用 LLM"""
        model = get_chat_model(stage)
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.choices:
            raise RuntimeError("LLM 返回空响应（choices 为空）")
        return response.choices[0].message.content

    async def _call_llm_streaming(self, prompt: str,
                                  stream_handler: Optional[Callable[[str], None]] = None,
                                  stage: Optional[str] = None) -> str:
        """流式调用 LLM

        每收到一个 chunk，就通过 stream_handler 推送给前端。
        同时拼接所有 chunk，最终返回完整文本。
        """
        content_builder = []
        stream_buffer: List[str] = []
        stream_buffer_length = 0
        last_flush_time = time.monotonic()

        async def flush_stream_buffer(force: bool = False) -> None:
            nonlocal stream_buffer_length, last_flush_time
            if not stream_handler or not stream_buffer:
                return
            if not force and stream_buffer_length < settings.novel_stream_min_chunk_chars:
                return

            content = "".join(stream_buffer)
            stream_buffer.clear()
            stream_buffer_length = 0
            last_flush_time = time.monotonic()

            result = stream_handler(content)
            if inspect.isawaitable(result):
                await result

        model = get_chat_model(stage)
        stream = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if not delta or not delta.content:
                continue
            content_builder.append(delta.content)
            if stream_handler:
                stream_buffer.append(delta.content)
                stream_buffer_length += len(delta.content)
                now = time.monotonic()
                reached_size = stream_buffer_length >= settings.novel_stream_chunk_chars
                reached_time = (
                    stream_buffer_length >= settings.novel_stream_min_chunk_chars
                    and now - last_flush_time >= settings.novel_stream_flush_interval_seconds
                )
                reached_boundary = (
                    stream_buffer_length >= settings.novel_stream_min_chunk_chars
                    and delta.content.endswith(("。", "！", "？", "；", "\n", ".", "!", "?"))
                )
                if reached_size or reached_time or reached_boundary:
                    await flush_stream_buffer()

        await flush_stream_buffer(force=True)

        return "".join(content_builder)

    def _extract_json_from_response(self, response: str) -> Any:
        """从 LLM 响应中提取 JSON

        LLM 经常在 JSON 前后加废话，这个方法负责提取出纯 JSON。
        尝试顺序：
        1. 直接 json.loads
        2. 提取 ```json ... ``` 中的内容
        3. 找第一个 { 或 [ 到最后一个 } 或 ]
        """
        # 1. 直接尝试
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 2. 提取 ```json ... ```
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 3. 找第一个 { 或 [ 到最后一个 } 或 ]
        first_brace = response.find('{')
        first_bracket = response.find('[')

        if first_brace == -1 and first_bracket == -1:
            logger.error("LLM 响应中未找到 JSON, response=%s", response[:200])
            raise RuntimeError("LLM 响应中未找到 JSON")

        if first_brace == -1:
            start = first_bracket
        elif first_bracket == -1:
            start = first_brace
        else:
            start = min(first_brace, first_bracket)

        # 找最后一个 } 或 ]
        last_brace = response.rfind('}')
        last_bracket = response.rfind(']')
        end = max(last_brace, last_bracket)

        if end <= start:
            logger.error("JSON 提取失败, response=%s", response[:200])
            raise RuntimeError("JSON 提取失败")

        json_str = response[start:end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error("JSON 解析失败, json_str=%s, error=%s", json_str[:200], e)
            raise RuntimeError(f"JSON 解析失败: {e}")

    def _format_dict_brief(self, d: Dict[str, Any]) -> str:
        """把字典转成简洁的文本格式（用于 prompt 注入）"""
        lines = []
        field_names = {
            "narrative_perspective": "叙述视角", "language_style": "语言风格",
            "dialogue_style": "对话风格", "description_preference": "描写偏好",
            "rhythm": "节奏特点", "techniques": "常用手法", "forbidden_words": "禁忌词汇",
            "forbidden_patterns": "禁忌句式", "sample_sentences": "参考句式",
            "chapter_opening_style": "章节开头", "chapter_ending_style": "章节结尾",
            "emotional_tone": "情感基调",
        }
        for key, value in d.items():
            display = field_names.get(key, key)
            if isinstance(value, list):
                lines.append(f"- {display}：{'、'.join(str(v) for v in value)}")
            else:
                lines.append(f"- {display}：{value}")
        return "\n".join(lines)

    @staticmethod
    def _normalize_idea_enhancement(result: Dict[str, Any], raw_idea: str) -> Dict[str, Any]:
        normalized = dict(result or {})
        normalized["logline"] = (
            normalized.get("logline")
            or normalized.get("oneLinePitch")
            or normalized.get("one_line_pitch")
            or ""
        )
        normalized["enhancedCoreIdea"] = (
            normalized.get("enhancedCoreIdea")
            or normalized.get("enhanced_core_idea")
            or normalized.get("coreIdea")
            or normalized.get("core_idea")
            or raw_idea
        )
        normalized["titleSuggestions"] = (
            normalized.get("titleSuggestions")
            or normalized.get("title_suggestions")
            or []
        )
        normalized["genrePositioning"] = (
            normalized.get("genrePositioning")
            or normalized.get("genre_positioning")
            or ""
        )
        normalized["protagonistDesign"] = (
            normalized.get("protagonistDesign")
            or normalized.get("protagonist_design")
            or {}
        )
        normalized["powerSystem"] = (
            normalized.get("powerSystem")
            or normalized.get("power_system")
            or {}
        )
        normalized["worldRules"] = normalized.get("worldRules") or normalized.get("world_rules") or []
        normalized["mainConflicts"] = normalized.get("mainConflicts") or normalized.get("main_conflicts") or []
        normalized["longTermHooks"] = normalized.get("longTermHooks") or normalized.get("long_term_hooks") or []
        normalized["openingHook"] = normalized.get("openingHook") or normalized.get("opening_hook") or ""
        normalized["risksAndFixes"] = normalized.get("risksAndFixes") or normalized.get("risks_and_fixes") or []
        return normalized
