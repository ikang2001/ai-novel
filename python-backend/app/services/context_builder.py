"""上下文组装器（三层记忆系统的核心）"""

import json
import logging
import re
from typing import Optional, List, Dict, Any

from app.services.novel_service import NovelService
from app.services.character_service import CharacterService
from app.services.foreshadowing_service import ForeshadowingService

logger = logging.getLogger(__name__)


class ContextBuilder:
    """组装每章生成时的完整上下文

    三层记忆架构：
    - 第一层：恒定记忆（世界观、核心角色、风格指南）~1500字
    - 第二层：近期记忆（最近3章摘要、上一章末尾、角色状态）~1200字
    - 第三层：长期记忆（按需检索：相关角色、伏笔、地点）~300-500字
    """

    def __init__(self, novel_service: NovelService,
                 character_service: CharacterService,
                 foreshadowing_service: ForeshadowingService):
        self.novel_service = novel_service
        self.character_service = character_service
        self.foreshadowing_service = foreshadowing_service

    async def build(self, novel_id: int, chapter_outline: str) -> str:
        """组装完整上下文，返回拼接后的字符串

        这是整个记忆系统的入口方法。
        它协调三层记忆的构建，最终拼接成一个完整的 prompt 上下文。
        """
        sections = []

        # === 第一层：恒定记忆 ===
        constant = await self._build_constant_memory(novel_id)
        if constant:
            sections.append(constant)

        # === 第二层：近期记忆 ===
        recent = await self._build_recent_memory(novel_id)
        if recent:
            sections.append(recent)

        # === 第三层：长期记忆（按需检索）===
        long_term = await self._build_long_term_memory(novel_id, chapter_outline)
        if long_term:
            sections.append(long_term)

        # === 本章大纲 ===
        sections.append(f"[本章大纲]\n{chapter_outline}")

        context = "\n\n".join(sections)
        logger.info("上下文组装完成, novel_id=%s, 总长度=%d字", novel_id, len(context))
        return context

    async def _build_constant_memory(self, novel_id: int) -> str:
        """构建恒定记忆（每次注入，内容不变除非作者修改）

        包含：风格指南、世界观设定、核心角色档案、全书梗概（如果有）
        """
        sections = []

        novel = await self.novel_service.get_novel(novel_id)
        if not novel:
            return ""

        # 风格指南
        style_guide = novel.get("style_guide")
        if style_guide:
            if isinstance(style_guide, str):
                try:
                    style_guide = json.loads(style_guide)
                except json.JSONDecodeError:
                    pass
            if isinstance(style_guide, dict):
                # 把字典格式转成可读文本
                guide_text = self._format_dict_as_text(style_guide)
                sections.append(f"[风格指南]\n{guide_text}")
            elif isinstance(style_guide, str):
                sections.append(f"[风格指南]\n{style_guide}")

        # 世界观设定
        world_setting = novel.get("world_setting")
        if world_setting:
            if isinstance(world_setting, str):
                try:
                    world_setting = json.loads(world_setting)
                except json.JSONDecodeError:
                    pass
            if isinstance(world_setting, dict):
                setting_text = self._format_dict_as_text(world_setting)
                sections.append(f"[世界观设定]\n{setting_text}")
            elif isinstance(world_setting, str):
                sections.append(f"[世界观设定]\n{world_setting}")

        # 核心角色档案
        core_chars = await self.character_service.get_core_characters(novel_id)
        if core_chars:
            char_text = "\n\n".join(self._format_character_detail(c) for c in core_chars)
            sections.append(f"[核心角色档案]\n{char_text}")

        # 全书梗概（超过50章时注入）
        chapter_count = novel.get("currentChapterNumber", 0)
        synopsis = novel.get("synopsis")
        if chapter_count > 50 and synopsis:
            sections.append(f"[全书梗概]\n{synopsis}")

        return "\n\n".join(sections)

    async def _build_recent_memory(self, novel_id: int) -> str:
        """构建近期记忆（随新章归档自动滚动）

        包含：最近3章摘要、上一章末尾、角色当前状态、活跃伏笔
        """
        sections = []

        # 最近3章摘要
        recent_chapters = await self.novel_service.get_recent_chapters(novel_id, limit=3)
        if recent_chapters:
            summaries = []
            for ch in recent_chapters:
                summary = ch.get("summary")
                if summary:
                    ch_num = ch.get("chapterNumber", "?")
                    ch_title = ch.get("title", "")
                    title_part = f" {ch_title}" if ch_title else ""
                    summaries.append(f"第{ch_num}章{title_part}：{summary}")
            if summaries:
                sections.append("[最近章节摘要]\n" + "\n".join(summaries))

        # 上一章末尾（最后500字，保持语感衔接）
        latest_chapter = await self.novel_service.get_latest_chapter(novel_id)
        if latest_chapter and latest_chapter.get("content"):
            content = latest_chapter["content"]
            # 取最后500个字符
            tail = content[-500:] if len(content) > 500 else content
            # 如果截断了，加省略号
            prefix = "..." if len(content) > 500 else ""
            sections.append(f"[上一章末尾]\n{prefix}{tail}")

        # 当前角色状态
        char_states = await self.character_service.get_all_current_states(novel_id)
        if char_states:
            states_text = "\n".join(
                f"- {s['name']}（{s['role_type']}）：在{s['location']}，{s['status']}"
                for s in char_states
            )
            sections.append(f"[当前角色状态]\n{states_text}")

        # 活跃伏笔列表（简要）
        active_fs = await self.foreshadowing_service.get_active_foreshadowing(novel_id)
        if active_fs:
            fs_text = "\n".join(
                f"- {self._format_foreshadowing_brief(fs)}"
                for fs in active_fs[:10]  # 最多显示10条，避免上下文过长
            )
            sections.append(f"[活跃伏笔]\n{fs_text}")

        return "\n\n".join(sections)

    async def _build_long_term_memory(self, novel_id: int, chapter_outline: str) -> str:
        """构建长期记忆（按需检索注入）

        根据本章大纲，检索相关的角色、伏笔、地点信息。
        这是解决"写到第100章还记得第3章细节"的关键。
        """
        sections = []

        # 获取所有角色名和地点名（用于实体提取）
        all_chars = await self.character_service.get_all_characters(novel_id)
        char_names = [c["name"] for c in all_chars]
        # 也收集别名
        for c in all_chars:
            aliases = c.get("aliases") or []
            if isinstance(aliases, list):
                char_names.extend(aliases)

        # 从大纲中提取实体
        entities = self._extract_entities(chapter_outline, known_characters=char_names)

        # 检索非核心角色的详细信息
        # （核心角色已在恒定记忆中注入，这里只查非核心的）
        core_chars = await self.character_service.get_core_characters(novel_id)
        core_names = {c["name"] for c in core_chars}

        extra_chars = []
        for name in entities.get("characters", []):
            if name not in core_names:
                char = await self.character_service.find_by_name(novel_id, name)
                if char:
                    extra_chars.append(char)

        if extra_chars:
            char_text = "\n".join(self._format_character_detail(c) for c in extra_chars)
            sections.append(f"[相关角色详情]\n{char_text}")

        # 检索相关伏笔（通过关键词匹配）
        keywords = entities.get("keywords", [])
        # 也把提到的角色名作为关键词
        keywords.extend(entities.get("characters", []))

        if keywords:
            related_fs = await self.foreshadowing_service.search_by_keywords(novel_id, keywords)
            if related_fs:
                fs_text = "\n".join(
                    f"- [第{fs.get('planted_chapter_id', '?')}章] {fs['surface']}"
                    + (f"（真相：{fs['hidden_truth']}）" if fs.get('hidden_truth') else "")
                    for fs in related_fs[:5]  # 最多5条
                )
                sections.append(f"[相关伏笔]\n{fs_text}")

        # 长期未提及的伏笔提醒（超过20章未提及）
        # 需要当前章节号
        novel = await self.novel_service.get_novel(novel_id)
        current_chapter = novel.get("currentChapterNumber", 0) if novel else 0
        if current_chapter > 0:
            stale_fs = await self.foreshadowing_service.get_stale_foreshadowing(
                novel_id, current_chapter, threshold=20
            )
            if stale_fs:
                stale_text = "、".join(
                    f"第{fs.get('planted_chapter_id', '?')}章'{fs['surface'][:15]}'"
                    for fs in stale_fs[:3]
                )
                sections.append(f"[伏笔提醒] 以下伏笔已很久未提及，本章如合适可呼应：{stale_text}")

            # 接近目标揭示的伏笔
            near_target = await self.foreshadowing_service.get_near_target_foreshadowing(
                novel_id, current_chapter
            )
            if near_target:
                target_text = "\n".join(
                    f"- {fs['surface']}(计划在第{fs['target_chapter']}章揭示)"
                    for fs in near_target[:3]
                )
                sections.append(f"[揭示提示] 以下伏笔接近计划揭示时间，可开始铺垫：\n{target_text}")

        return "\n\n".join(sections)

    def _extract_entities(self, outline: str, known_characters: List[str] = None,
                          known_locations: List[str] = None) -> Dict[str, List[str]]:
        """从大纲文本中提取实体（角色名、地点名、关键词）

        简单实现：遍历已知名称列表，检查是否出现在大纲文本中。
        更好的实现可以用 NER 或 LLM，但会增加延迟和成本。
        """
        result = {"characters": [], "locations": [], "keywords": []}

        if not outline:
            return result

        # 提取角色名
        if known_characters:
            for name in set(known_characters):
                if name and len(name) >= 2 and name in outline:
                    result["characters"].append(name)

        # 提取地点名
        if known_locations:
            for name in set(known_locations):
                if name and len(name) >= 2 and name in outline:
                    result["locations"].append(name)

        # 提取关键词（简单的：去掉常见词，取有意义的词）
        # 这里用一个简单的方法：提取中文词（2-4字的连续中文）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,4}', outline)
        # 去掉常见停用词
        stopwords = {"一个", "他们", "我们", "这个", "那个", "什么", "怎么", "可以", "没有",
                      "不是", "但是", "然后", "因为", "所以", "如果", "已经", "还是", "只是",
                      "在场", "开始", "出现", "发现", "决定", "告诉", "知道", "看到", "感到"}
        keywords = [w for w in chinese_words if w not in stopwords and len(w) >= 2]
        # 去重并取前10个
        result["keywords"] = list(set(keywords))[:10]

        return result

    def _format_character_detail(self, char: Dict[str, Any]) -> str:
        """格式化角色详情为可读文本"""
        parts = [f"角色[{char['name']}]"]

        role_type = char.get("role_type")
        if role_type:
            role_map = {"protagonist": "主角", "supporting": "配角", "antagonist": "反派", "minor": "龙套"}
            parts.append(role_map.get(role_type, role_type))

        if char.get("appearance"):
            parts.append(char["appearance"])

        text = "，".join(parts)

        if char.get("personality"):
            text += f"\n性格：{char['personality']}"

        skills = char.get("skills")
        if skills:
            if isinstance(skills, list):
                text += f"\n技能：{'、'.join(skills)}"
            elif isinstance(skills, str):
                text += f"\n技能：{skills}"

        if char.get("current_status"):
            text += f"\n当前状态：{char['current_status']}"

        if char.get("current_location"):
            text += f"\n当前位置：{char['current_location']}"

        if char.get("notes"):
            text += f"\n备注：{char['notes']}"

        return text

    def _format_foreshadowing_brief(self, fs: Dict[str, Any]) -> str:
        """格式化伏笔简要信息"""
        planted = fs.get("planted_chapter_id") or fs.get("planted_chapter_number") or "?"
        text = f"[第{planted}章] {fs['surface']}"
        if fs.get("hidden_truth"):
            text += f"（真相：{fs['hidden_truth']}）"
        return text

    def _format_foreshadowing_list(self, foreshadowing_list: List[Dict]) -> str:
        """格式化伏笔列表"""
        if not foreshadowing_list:
            return ""
        return "\n".join(
            f"- {self._format_foreshadowing_brief(fs)}"
            for fs in foreshadowing_list
        )

    def _format_dict_as_text(self, d: Dict[str, Any], indent: int = 0) -> str:
        """把字典格式转成可读文本

        为什么不用 JSON.dumps？
        因为 JSON 格式对 LLM 来说不如自然语言友好。
        例如：{"era": "现代", "rules": "灵力九阶"}
        转成："时代背景：现代\n核心规则：灵力九阶"
        """
        lines = []
        # 字段名的中文映射
        field_names = {
            "era": "时代背景", "rules": "核心规则", "factions": "势力分布",
            "locations": "重要地点", "narrative_perspective": "叙述视角",
            "language_style": "语言风格", "dialogue_style": "对话风格",
            "description_preference": "描写偏好", "rhythm": "节奏特点",
            "techniques": "常用手法", "forbidden_words": "禁忌词汇",
            "forbidden_patterns": "禁忌句式", "sample_sentences": "参考句式",
            "chapter_opening_style": "章节开头风格", "chapter_ending_style": "章节结尾风格",
            "emotional_tone": "情感基调",
        }
        for key, value in d.items():
            display_name = field_names.get(key, key)
            if isinstance(value, list):
                lines.append(f"{display_name}：{'、'.join(str(v) for v in value)}")
            elif isinstance(value, dict):
                lines.append(f"{display_name}：")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key}：{sub_value}")
            else:
                lines.append(f"{display_name}：{value}")
        return "\n".join(lines)
