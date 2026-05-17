"""小说智能体服务"""

import json
import logging
import re
from typing import Optional, List, Dict, Any, Callable

from openai import AsyncOpenAI

from app.config import settings
from app.constants.novel_prompt import NovelPromptConstant
from app.services.context_builder import ContextBuilder
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

        # LLM 客户端（DashScope 兼容 OpenAI 接口）
        self.client = AsyncOpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url
        )
        self.model = settings.dashscope_model

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

        content = await self._call_llm(prompt)
        result = self._extract_json_from_response(content)
        logger.info("Agent1 设定生成成功, title=%s", title)
        return result

    # ========== Agent 2：风格分析 ==========

    async def agent2_analyze_style(self, samples: str) -> Dict[str, Any]:
        """风格分析助手：从样本中提取写作风格"""
        # 截取前 15000 字，避免超出上下文窗口
        truncated = samples[:15000] if len(samples) > 15000 else samples

        prompt = NovelPromptConstant.AGENT2_STYLE_ANALYZE_PROMPT.replace("{samples}", truncated)

        content = await self._call_llm(prompt)
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
            f"- {fs['surface']}" + (f"（真相：{fs['hidden_truth']}）" if fs.get('hidden_truth') else "")
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

        content = await self._call_llm(prompt)
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

        content = await self._call_llm(prompt)
        result = self._extract_json_from_response(content)
        if not isinstance(result, list):
            result = [result] if isinstance(result, dict) else []
        return result

    # ========== Agent 4：写作助手 ==========

    async def agent4_write_chapter(self, novel_id: int,
                                   chapter_outline: str,
                                   author_note: Optional[str] = None,
                                   stream_handler: Optional[Callable[[str], None]] = None) -> str:
        """写作助手：生成一章约 5000 字的小说正文

        这是最核心的 Agent。
        1. 调用 context_builder 组装三层记忆上下文
        2. 拼接完整的 prompt
        3. 流式调用 LLM
        """
        # 读取风格指南（用于风格约束）
        novel = await self.novel_service.get_novel(novel_id)
        style_guide = novel.get("style_guide") if novel else None

        # 组装三层记忆上下文
        context = await self.context_builder.build(novel_id, chapter_outline)

        # 构建风格约束部分
        style_constraints = ""
        if style_guide:
            if isinstance(style_guide, str):
                try:
                    style_guide = json.loads(style_guide)
                except json.JSONDecodeError:
                    pass
            if isinstance(style_guide, dict):
                guide_text = self._format_dict_brief(style_guide)
            else:
                guide_text = str(style_guide)
            style_constraints = NovelPromptConstant.AGENT4_STYLE_CONSTRAINTS_SECTION.replace(
                "{style_guide}", guide_text
            )

        # 构建作者交代部分
        author_note_section = ""
        if author_note:
            author_note_section = NovelPromptConstant.AGENT4_AUTHOR_NOTE_SECTION.replace(
                "{author_note}", author_note
            )

        # 拼接完整 prompt
        prompt = NovelPromptConstant.AGENT4_CHAPTER_WRITE_PROMPT
        prompt = prompt.replace("{context}", context)
        prompt = prompt.replace("{style_constraints}", style_constraints)
        prompt = prompt.replace("{outline}", chapter_outline)
        prompt = prompt.replace("{author_note_section}", author_note_section)

        # 流式调用
        if stream_handler:
            content = await self._call_llm_streaming(prompt, stream_handler)
        else:
            content = await self._call_llm(prompt)

        logger.info("Agent4 章节生成完成, novel_id=%s, 字数=%d", novel_id, len(content))
        return content

    # ========== Agent 5：归档助手 ==========

    async def agent5_archive(self, novel_id: int, chapter_content: str) -> Dict[str, Any]:
        """归档助手：分析本章内容，提取需要更新到知识库的信息"""
        # 读取当前角色列表
        all_chars = await self.character_service.get_all_characters(novel_id)
        chars_text = json.dumps(
            [{"name": c["name"], "role_type": c.get("role_type"), "status": c.get("current_status")}
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

        content = await self._call_llm(prompt)
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
        word_count = result.get("word_count", 0)
        if summary:
            await self.novel_service.update_chapter_summary(chapter_id, summary)
        if word_count > 0:
            # 只更新字数，不覆盖正文内容
            await self.novel_service._execute(
                "UPDATE chapter SET wordCount = :wc, updateTime = NOW() WHERE id = :id",
                {"wc": word_count, "id": chapter_id},
            )

        # 更新小说总字数
        novel = await self.novel_service.get_novel(novel_id)
        if novel:
            total = novel.get("totalWordCount", 0) + word_count
            await self.novel_service.update_novel_word_count(novel_id, total)

        # 2. 处理角色更新
        for char_update in result.get("character_updates", []):
            name = char_update.get("name")
            action = char_update.get("action")
            updates = char_update.get("updates", {})

            if action == "create":
                # 新角色
                new_char_id = await self.character_service.create_character(
                    novel_id=novel_id,
                    name=name,
                    role_type=updates.get("role_type", "minor"),
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
                        current_location=updates.get("current_location"),
                        current_status=updates.get("current_status"),
                        new_details=updates.get("new_details"),
                    )
                    await self.character_service.set_last_appearance(char["id"], chapter_id)

        # 3. 处理新实体
        for entity in result.get("new_entities", []):
            entity_type = entity.get("type")
            name = entity.get("name")
            details = entity.get("details", {})

            if entity_type == "character":
                # 检查是否已存在
                existing = await self.character_service.find_by_name(novel_id, name)
                if not existing:
                    await self.character_service.create_character(
                        novel_id=novel_id,
                        name=name,
                        role_type=details.get("role_type", "minor"),
                        appearance=details.get("appearance"),
                        personality=details.get("personality"),
                    )

        # 4. 处理伏笔更新
        for fs_update in result.get("foreshadowing_updates", []):
            action = fs_update.get("action")

            if action == "plant":
                # 新埋伏笔
                await self.foreshadowing_service.create_foreshadowing(
                    novel_id=novel_id,
                    surface=fs_update.get("surface", ""),
                    hidden_truth=fs_update.get("hidden_truth"),
                    category=fs_update.get("category"),
                    related_characters=fs_update.get("related_characters"),
                    keywords=fs_update.get("keywords"),
                    importance=fs_update.get("importance", 3),
                    planted_chapter_id=chapter_id,
                )
            elif action == "resolve":
                fs_id = fs_update.get("foreshadowing_id")
                if fs_id:
                    await self.foreshadowing_service.resolve_foreshadowing(fs_id, chapter_id)
            elif action == "mention":
                fs_id = fs_update.get("foreshadowing_id")
                if fs_id:
                    await self.foreshadowing_service.record_mention(
                        fs_id, chapter_id, chapter_number
                    )

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
            + (f"（真相：{fs['hidden_truth']}）" if fs.get('hidden_truth') else "")
            for fs in all_fs
        ) or "暂无伏笔"

        prompt = NovelPromptConstant.AGENT6_REVIEW_PROMPT
        prompt = prompt.replace("{title}", novel.get("title", ""))
        prompt = prompt.replace("{total_chapters}", str(len(all_chapters)))
        prompt = prompt.replace("{all_summaries}", summaries[:5000])  # 截取避免过长
        prompt = prompt.replace("{all_characters}", chars_text[:3000])
        prompt = prompt.replace("{all_foreshadowing}", fs_text[:2000])

        content = await self._call_llm(prompt)
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

        content = await self._call_llm(prompt)
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

        content = await self._call_llm(prompt)

        # 保存到数据库
        await self.novel_service.update_synopsis(novel_id, content)
        logger.info("全书梗概生成完成, novel_id=%s", novel_id)
        return content

    # ========== LLM 调用封装 ==========

    async def _call_llm(self, prompt: str) -> str:
        """非流式调用 LLM"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.choices:
            raise RuntimeError("LLM 返回空响应（choices 为空）")
        return response.choices[0].message.content

    async def _call_llm_streaming(self, prompt: str,
                                  stream_handler: Optional[Callable[[str], None]] = None) -> str:
        """流式调用 LLM

        每收到一个 chunk，就通过 stream_handler 推送给前端。
        同时拼接所有 chunk，最终返回完整文本。
        """
        content_builder = []

        stream = await self.client.chat.completions.create(
            model=self.model,
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
                stream_handler(delta.content)

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
