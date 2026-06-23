"""Context package builder for novel chapter generation."""

import json
import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.services.character_service import CharacterService
from app.services.foreshadowing_service import ForeshadowingService
from app.services.novel_service import NovelService

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds governed context for a target chapter.

    The public `build` method remains for backward compatibility. New code should
    use `build_package` and feed it into PromptCrafter.
    """

    def __init__(
        self,
        novel_service: NovelService,
        character_service: CharacterService,
        foreshadowing_service: ForeshadowingService,
    ):
        self.novel_service = novel_service
        self.character_service = character_service
        self.foreshadowing_service = foreshadowing_service

    async def build(
        self,
        novel_id: int,
        chapter_outline: Any,
        chapter_id: Optional[int] = None,
        chapter_number: Optional[int] = None,
    ) -> str:
        """Return a readable context string for legacy prompt usage."""
        package = await self.build_package(novel_id, chapter_outline, chapter_id, chapter_number)
        return self.format_package_for_prompt(package)

    async def build_package(
        self,
        novel_id: int,
        chapter_outline: Any,
        chapter_id: Optional[int] = None,
        chapter_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Build a structured context package for a specific target chapter."""
        outline = self._coerce_dict(chapter_outline)
        novel = await self.novel_service.get_novel(novel_id)
        if not novel:
            raise ValueError(f"小说不存在: {novel_id}")

        target_number = chapter_number or await self.novel_service.get_next_chapter_number(novel_id)
        target_chapter = {
            "chapterId": chapter_id,
            "chapterNumber": target_number,
            "volumeNumber": novel.get("currentVolumeNumber", 1),
        }

        stable_memory = await self._build_stable_memory(novel_id, novel)
        recent_memory = await self._build_recent_memory(novel_id, target_number)
        long_term_memory = await self._build_long_term_memory(novel_id, outline, target_number)
        hook_debt = await self.foreshadowing_service.get_hook_debt(novel_id, target_number, limit=8)
        chapter_memo = self._ensure_chapter_memo(outline, recent_memory, hook_debt)
        rule_stack = self._build_rule_stack(novel, chapter_memo, hook_debt)

        package = {
            "version": "v1",
            "novel": {
                "id": novel_id,
                "title": novel.get("title"),
                "genre": novel.get("genre"),
                "targetReaders": novel.get("targetReaders"),
                "currentChapterNumber": novel.get("currentChapterNumber", 0),
                "currentVolumeNumber": novel.get("currentVolumeNumber", 1),
            },
            "targetChapter": target_chapter,
            "stableMemory": stable_memory,
            "recentMemory": recent_memory,
            "longTermMemory": long_term_memory,
            "hookDebt": hook_debt,
            "chapterMemo": chapter_memo,
            "ruleStack": rule_stack,
            "trace": {
                "excludedChapterNumber": target_number,
                "recentChapterNumbers": [c.get("chapterNumber") for c in recent_memory.get("recentChapters", [])],
                "previousChapterNumber": recent_memory.get("previousChapter", {}).get("chapterNumber"),
                "hookDebtCount": len(hook_debt),
                "contextPolicy": "Only chapters with chapterNumber < target chapter are eligible for recent context.",
            },
        }
        safe_package = self._json_safe(package)
        logger.info(
            "上下文包组装完成, novel_id=%s, chapter=%s, recent=%s, hook_debt=%s",
            novel_id,
            target_number,
            safe_package["trace"]["recentChapterNumbers"],
            len(hook_debt),
        )
        return safe_package

    async def _build_stable_memory(self, novel_id: int, novel: Dict[str, Any]) -> Dict[str, Any]:
        core_chars = await self.character_service.get_core_characters(novel_id)
        style_guide = self._coerce_dict(novel.get("styleGuide")) or novel.get("styleGuide")
        world_setting = self._coerce_dict(novel.get("worldSetting")) or novel.get("worldSetting")
        volume_outline = self._coerce_list(novel.get("volumeOutline")) or novel.get("volumeOutline")
        return {
            "styleGuide": style_guide,
            "worldSetting": world_setting,
            "volumeOutline": volume_outline,
            "coreCharacters": core_chars,
            "synopsis": novel.get("synopsis"),
        }

    async def _build_recent_memory(self, novel_id: int, chapter_number: int) -> Dict[str, Any]:
        recent_chapters = await self.novel_service.get_recent_chapters_before(novel_id, chapter_number, limit=3)
        previous_chapter = await self.novel_service.get_previous_chapter(novel_id, chapter_number)
        char_states = await self.character_service.get_all_current_states(novel_id)
        active_fs = await self.foreshadowing_service.get_active_foreshadowing(novel_id)
        previous_tail = ""
        if previous_chapter and previous_chapter.get("content"):
            content = previous_chapter["content"]
            previous_tail = ("..." if len(content) > 600 else "") + content[-600:]
        return {
            "recentChapters": [
                {
                    "chapterId": ch.get("id"),
                    "chapterNumber": ch.get("chapterNumber"),
                    "title": ch.get("title"),
                    "summary": ch.get("summary"),
                    "endingState": ch.get("endingState"),
                }
                for ch in recent_chapters
            ],
            "previousChapter": {
                "chapterId": previous_chapter.get("id") if previous_chapter else None,
                "chapterNumber": previous_chapter.get("chapterNumber") if previous_chapter else None,
                "title": previous_chapter.get("title") if previous_chapter else None,
                "summary": previous_chapter.get("summary") if previous_chapter else None,
                "endingState": previous_chapter.get("endingState") if previous_chapter else None,
                "tail": previous_tail,
            },
            "characterStates": char_states,
            "activeForeshadowing": active_fs[:12],
        }

    async def _build_long_term_memory(
        self,
        novel_id: int,
        outline: Dict[str, Any],
        chapter_number: int,
    ) -> Dict[str, Any]:
        outline_text = json.dumps(outline, ensure_ascii=False)
        all_chars = await self.character_service.get_all_characters(novel_id)
        char_names = [c["name"] for c in all_chars if c.get("name")]
        for char in all_chars:
            aliases = char.get("aliases") or []
            if isinstance(aliases, list):
                char_names.extend(aliases)

        entities = self._extract_entities(outline_text, known_characters=char_names)
        core_names = {c["name"] for c in await self.character_service.get_core_characters(novel_id)}
        extra_chars = []
        for name in entities.get("characters", []):
            if name not in core_names:
                char = await self.character_service.find_by_name(novel_id, name)
                if char:
                    extra_chars.append(char)

        keywords = list(dict.fromkeys(entities.get("keywords", []) + entities.get("characters", [])))
        related_fs = await self.foreshadowing_service.search_by_keywords(novel_id, keywords) if keywords else []
        stale_fs = await self.foreshadowing_service.get_stale_foreshadowing(novel_id, chapter_number, threshold=20)
        near_target = await self.foreshadowing_service.get_near_target_foreshadowing(novel_id, chapter_number)
        current_state = await self.novel_service.get_novel_state(novel_id, "current_state")
        reader_expectation = await self.novel_service.get_novel_state(novel_id, "reader_expectation")
        style_memory = await self.novel_service.get_novel_state(novel_id, "style_memory")
        revision_preference = await self.novel_service.get_novel_state(novel_id, "revision_preference")

        return {
            "matchedEntities": entities,
            "relatedCharacters": extra_chars[:6],
            "relatedForeshadowing": related_fs[:6],
            "staleForeshadowing": stale_fs[:5],
            "nearTargetForeshadowing": near_target[:5],
            "currentState": current_state.get("stateData") if current_state else None,
            "readerExpectation": reader_expectation.get("stateData") if reader_expectation else None,
            "styleMemory": style_memory.get("stateData") if style_memory else None,
            "revisionPreference": revision_preference.get("stateData") if revision_preference else None,
        }

    def _ensure_chapter_memo(
        self,
        outline: Dict[str, Any],
        recent_memory: Dict[str, Any],
        hook_debt: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        memo = dict(outline)
        previous = recent_memory.get("previousChapter") or {}
        previous_ending = previous.get("endingState") or {}
        if not isinstance(previous_ending, dict):
            previous_ending = {}
        memo.setdefault("chapterTask", outline.get("chapterTask") or outline.get("chapter_task") or "推进本章剧情，制造可见状态变化")
        memo.setdefault(
            "readerExpectation",
            outline.get("readerExpectation")
            or previous_ending.get("readerExpectation")
            or "承接上一章结尾，给读者一个新的问题、行动或情绪落点",
        )
        memo.setdefault(
            "previousEmotionalResidue",
            outline.get("previousEmotionalResidue")
            or previous_ending.get("emotionalResidue")
            or previous.get("summary")
            or "",
        )
        memo.setdefault("requiredEndingChange", outline.get("requiredEndingChange") or outline.get("chapterHook") or "")
        memo.setdefault("informationGap", outline.get("informationGap") or "本章至少保留一个读者想继续追问的信息差")
        memo.setdefault("hookOperations", self._default_hook_operations(outline, hook_debt))
        memo.setdefault("prohibitions", [
            "不要复述上一章剧情当开头",
            "不要让角色只为推动剧情而突然改变立场",
            "不要用总结式旁白替代具体行动、物件、对话或场景变化",
        ])
        memo.setdefault("sceneCraft", self._infer_scene_craft(memo))
        return memo

    def _default_hook_operations(self, outline: Dict[str, Any], hook_debt: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        operations = []
        for item in hook_debt[:3]:
            stage = item.get("computedLifecycleStage") or item.get("lifecycleStage") or "open"
            operations.append({
                "action": "advance" if stage != "pressured" else "resolve_or_advance",
                "foreshadowingId": item.get("id"),
                "surface": item.get("surface"),
                "reason": item.get("debtReason"),
            })
        for surface in outline.get("foreshadowingToPlant") or outline.get("foreshadowing_to_plant") or []:
            operations.append({"action": "plant", "surface": surface, "reason": "本章大纲要求新埋伏笔"})
        for surface in outline.get("foreshadowingToUse") or outline.get("foreshadowing_to_use") or []:
            operations.append({"action": "advance", "surface": surface, "reason": "本章大纲要求呼应"})
        return operations

    def _infer_scene_craft(self, memo: Dict[str, Any]) -> List[str]:
        outline_text = json.dumps(memo, ensure_ascii=False)
        craft = []
        if any(word in outline_text for word in ("战", "打", "追", "逃", "袭")):
            craft.append("动作场面：动作必须体现目标、阻碍和代价，避免只写招式名。")
        if any(word in outline_text for word in ("谈", "问", "说", "对话", "争执")):
            craft.append("对话场面：每句台词都带立场、试探或隐瞒，避免解释设定。")
        if any(word in outline_text for word in ("发现", "线索", "秘密", "真相")):
            craft.append("悬疑场面：线索必须有可见载体，揭示一层同时保留一层。")
        if not craft:
            craft.append("场景推进：每个场景至少改变一个事实、关系、情绪或读者问题。")
        return craft

    def _build_rule_stack(
        self,
        novel: Dict[str, Any],
        chapter_memo: Dict[str, Any],
        hook_debt: List[Dict[str, Any]],
    ) -> List[str]:
        rules = [
            "硬事实、角色状态、伏笔账本优先于临场发挥。",
            "每个场景必须有入口画面、角色目标、阻碍、转折和出口状态。",
            "承接上一章时写情绪和行动的自然延续，不要概括复盘。",
            "角色行为必须由过往经历、当前利益和性格共同推出。",
            "避免AI腔：少用空泛形容词、宏大总结、重复主语、同质化段落。",
        ]
        if hook_debt:
            rules.append("伏笔债务必须用动作、物件、对话或选择推进；单纯内心提到不算推进。")
        style_guide = self._coerce_dict(novel.get("styleGuide"))
        if isinstance(style_guide, dict):
            forbidden = style_guide.get("forbidden_words") or style_guide.get("forbidden_patterns")
            if forbidden:
                rules.append(f"遵守风格禁忌：{forbidden}")
        prohibitions = chapter_memo.get("prohibitions") or []
        rules.extend(str(item) for item in prohibitions if item)
        return rules

    def format_package_for_prompt(self, package: Dict[str, Any]) -> str:
        """Render the structured package into readable text."""
        lines = []
        novel = package.get("novel", {})
        target = package.get("targetChapter", {})
        lines.append(f"[目标章节]\n书名：{novel.get('title', '')}\n第{target.get('chapterNumber')}章")

        stable = package.get("stableMemory", {})
        if stable.get("worldSetting"):
            lines.append(f"[世界观设定]\n{self._format_value(stable['worldSetting'])}")
        if stable.get("styleGuide"):
            lines.append(f"[风格指南]\n{self._format_value(stable['styleGuide'])}")
        if stable.get("coreCharacters"):
            lines.append("[核心角色]\n" + "\n\n".join(self._format_character_detail(c) for c in stable["coreCharacters"]))

        recent = package.get("recentMemory", {})
        recent_chapters = recent.get("recentChapters") or []
        if recent_chapters:
            summaries = [
                f"第{ch.get('chapterNumber')}章 {ch.get('title') or ''}：{ch.get('summary') or '暂无摘要'}"
                for ch in recent_chapters
            ]
            lines.append("[最近章节摘要]\n" + "\n".join(summaries))
        previous = recent.get("previousChapter") or {}
        if previous.get("tail"):
            lines.append(f"[上一章末尾]\n{previous['tail']}")
        if previous.get("endingState"):
            lines.append(f"[上一章结尾状态]\n{self._format_value(previous['endingState'])}")
        if recent.get("characterStates"):
            states = [
                f"- {s.get('name')}（{s.get('role_type')}）：在{s.get('location')}，{s.get('status')}"
                for s in recent["characterStates"]
            ]
            lines.append("[当前角色状态]\n" + "\n".join(states))

        long_term = package.get("longTermMemory", {})
        if long_term.get("relatedCharacters"):
            lines.append("[相关角色详情]\n" + "\n\n".join(self._format_character_detail(c) for c in long_term["relatedCharacters"]))
        if long_term.get("relatedForeshadowing"):
            lines.append("[相关伏笔]\n" + self._format_foreshadowing_list(long_term["relatedForeshadowing"]))
        if package.get("hookDebt"):
            debt_lines = [
                f"- {fs.get('surface')}：{fs.get('debtReason')}"
                for fs in package["hookDebt"]
            ]
            lines.append("[伏笔债务]\n" + "\n".join(debt_lines))

        lines.append(f"[本章备忘录]\n{self._format_value(package.get('chapterMemo', {}))}")
        lines.append("[规则栈]\n" + "\n".join(f"- {rule}" for rule in package.get("ruleStack", [])))
        return "\n\n".join(lines)

    def _extract_entities(
        self,
        outline: str,
        known_characters: Optional[List[str]] = None,
        known_locations: Optional[List[str]] = None,
    ) -> Dict[str, List[str]]:
        result = {"characters": [], "locations": [], "keywords": []}
        if not outline:
            return result
        if known_characters:
            for name in set(known_characters):
                if name and len(name) >= 2 and name in outline:
                    result["characters"].append(name)
        if known_locations:
            for name in set(known_locations):
                if name and len(name) >= 2 and name in outline:
                    result["locations"].append(name)
        chinese_words = re.findall(r"[\u4e00-\u9fff]{2,4}", outline)
        stopwords = {
            "一个", "他们", "我们", "这个", "那个", "什么", "怎么", "可以", "没有",
            "不是", "但是", "然后", "因为", "所以", "如果", "已经", "还是", "只是",
            "在场", "开始", "出现", "发现", "决定", "告诉", "知道", "看到", "感到",
        }
        result["keywords"] = list(dict.fromkeys(w for w in chinese_words if w not in stopwords))[:12]
        return result

    def _format_character_detail(self, char: Dict[str, Any]) -> str:
        parts = [f"角色[{char.get('name', '')}]"]
        role_type = char.get("roleType")
        if role_type:
            role_map = {"protagonist": "主角", "supporting": "配角", "antagonist": "反派", "minor": "龙套"}
            parts.append(role_map.get(role_type, role_type))
        if char.get("appearance"):
            parts.append(char["appearance"])
        text = "，".join(parts)
        for label, key in (
            ("性格", "personality"),
            ("说话风格", "speechStyle"),
            ("当前状态", "currentStatus"),
            ("当前位置", "currentLocation"),
            ("备注", "notes"),
        ):
            if char.get(key):
                text += f"\n{label}：{char[key]}"
        if char.get("skills"):
            text += f"\n技能：{self._format_value(char['skills'])}"
        return text

    def _format_foreshadowing_brief(self, fs: Dict[str, Any]) -> str:
        planted = fs.get("plantedChapterNumber") or fs.get("plantedChapterId") or "?"
        text = f"[第{planted}章] {fs.get('surface', '')}"
        if fs.get("hiddenTruth"):
            text += f"（真相：{fs['hiddenTruth']}）"
        if fs.get("computedLifecycleStage") or fs.get("lifecycleStage"):
            text += f"｜阶段：{fs.get('computedLifecycleStage') or fs.get('lifecycleStage')}"
        return text

    def _format_foreshadowing_list(self, foreshadowing_list: List[Dict[str, Any]]) -> str:
        return "\n".join(f"- {self._format_foreshadowing_brief(fs)}" for fs in foreshadowing_list)

    def _format_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return "\n".join(f"- {self._format_value(item)}" for item in value)
        if isinstance(value, dict):
            lines = []
            field_names = {
                "era": "时代背景",
                "rules": "核心规则",
                "factions": "势力分布",
                "locations": "重要地点",
                "narrative_perspective": "叙述视角",
                "language_style": "语言风格",
                "dialogue_style": "对话风格",
                "description_preference": "描写偏好",
                "rhythm": "节奏特点",
                "techniques": "常用手法",
                "forbidden_words": "禁忌词汇",
                "forbidden_patterns": "禁忌句式",
                "chapterTask": "本章任务",
                "readerExpectation": "读者期待",
                "previousEmotionalResidue": "上一章情绪残留",
                "requiredEndingChange": "章尾必须变化",
                "informationGap": "信息差",
                "hookOperations": "伏笔操作",
                "prohibitions": "禁止事项",
                "sceneCraft": "场景技法",
            }
            for key, item in value.items():
                label = field_names.get(key, key)
                if isinstance(item, (dict, list)):
                    lines.append(f"{label}：\n{self._format_value(item)}")
                else:
                    lines.append(f"{label}：{item}")
            return "\n".join(lines)
        return str(value)

    def _coerce_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {"raw": value}
        return {}

    def _coerce_list(self, value: Any) -> List[Any]:
        if isinstance(value, list):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                return []
        return []

    def _json_safe(self, value: Any) -> Any:
        """Convert database rows and datetime values into JSON-safe objects."""
        if isinstance(value, dict):
            return {key: self._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [self._json_safe(item) for item in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)
