"""Deterministic prompt crafting for governed novel writing."""

import json
from typing import Any, Dict, Optional

from app.constants.novel_prompt import NovelPromptConstant


class PromptCrafter:
    """Turns a structured context package into the final writer prompt."""

    def craft_chapter_prompt(
        self,
        context_package: Dict[str, Any],
        author_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        layers = self._build_layers(context_package)
        context_layers = "\n\n".join(
            f"【L{index} {title}】\n{content}"
            for index, (title, content) in enumerate(layers, start=1)
        )
        author_note_section = ""
        if author_note:
            author_note_section = NovelPromptConstant.AGENT4_AUTHOR_NOTE_SECTION.replace("{author_note}", author_note)
        prompt = NovelPromptConstant.AGENT4_GOVERNED_CHAPTER_WRITE_PROMPT
        prompt = prompt.replace("{context_layers}", context_layers)
        prompt = prompt.replace("{author_note_section}", author_note_section)
        return {
            "prompt": prompt,
            "layers": [{"index": i + 1, "title": title, "content": content} for i, (title, content) in enumerate(layers)],
            "ruleStack": context_package.get("ruleStack", []),
        }

    def craft_audit_prompt(self, context_package: Dict[str, Any], draft_content: str) -> str:
        return (
            NovelPromptConstant.AGENT4_DRAFT_AUDIT_PROMPT
            .replace("{context_package}", self._format_json(context_package))
            .replace("{draft_content}", draft_content)
        )

    def craft_revision_prompt(
        self,
        context_package: Dict[str, Any],
        draft_content: str,
        audit_report: Dict[str, Any],
    ) -> str:
        return (
            NovelPromptConstant.AGENT4_DRAFT_REVISION_PROMPT
            .replace("{context_package}", self._format_json(context_package))
            .replace("{audit_report}", self._format_json(audit_report))
            .replace("{draft_content}", draft_content)
        )

    def _build_layers(self, package: Dict[str, Any]) -> list[tuple[str, str]]:
        novel = package.get("novel", {})
        target = package.get("targetChapter", {})
        stable = package.get("stableMemory", {})
        recent = package.get("recentMemory", {})
        long_term = package.get("longTermMemory", {})
        memo = package.get("chapterMemo", {})
        previous = recent.get("previousChapter") or {}

        return [
            (
                "元信息",
                "\n".join([
                    f"书名：{novel.get('title', '')}",
                    f"题材：{novel.get('genre', '')}",
                    f"目标章节：第{target.get('chapterNumber')}章",
                    "写作目标：写出可直接展示给读者的章节正文，不要输出分析。",
                ]),
            ),
            (
                "入场上下文",
                "\n".join([
                    f"上一章结尾画面/尾段：{previous.get('tail') or '无，这是开篇或缺少前章正文'}",
                    f"上一章结尾状态：{self._format_value(previous.get('endingState'))}",
                    f"上一章情绪残留：{memo.get('previousEmotionalResidue') or '无'}",
                    f"读者期待：{memo.get('readerExpectation') or '承接上一章并推进新问题'}",
                ]),
            ),
            (
                "本章出口",
                "\n".join([
                    f"本章核心任务：{memo.get('chapterTask')}",
                    f"本章信息差：{memo.get('informationGap')}",
                    f"必须形成的章尾变化：{memo.get('requiredEndingChange')}",
                    f"章末钩子：{memo.get('chapterHook') or memo.get('chapter_hook') or ''}",
                ]),
            ),
            (
                "人物弧线",
                "\n".join([
                    "当前角色状态：",
                    self._format_value(recent.get("characterStates")),
                    "角色动机链：",
                    self._format_value(memo.get("characterMotivations")),
                ]),
            ),
            (
                "场景序列",
                self._format_value(memo.get("scenes")),
            ),
            (
                "硬事实与长期记忆",
                "\n".join([
                    "世界观/设定：",
                    self._format_value(stable.get("worldSetting")),
                    "核心角色：",
                    self._format_value(stable.get("coreCharacters")),
                    "相关角色/伏笔/长期状态：",
                    self._format_value({
                        "relatedCharacters": long_term.get("relatedCharacters"),
                        "relatedForeshadowing": long_term.get("relatedForeshadowing"),
                        "currentState": long_term.get("currentState"),
                    }),
                ]),
            ),
            (
                "伏笔账本",
                "\n".join([
                    "本章伏笔操作：",
                    self._format_value(memo.get("hookOperations")),
                    "伏笔债务：",
                    self._format_value(package.get("hookDebt")),
                    "活跃伏笔：",
                    self._format_value(recent.get("activeForeshadowing")),
                ]),
            ),
            (
                "风格与反AI规则",
                "\n".join([
                    "风格指南：",
                    self._format_value(stable.get("styleGuide")),
                    "可学习风格记忆：",
                    self._format_value(long_term.get("styleMemory")),
                    "用户改稿偏好：",
                    self._format_value(long_term.get("revisionPreference")),
                    "规则栈：",
                    self._format_value(package.get("ruleStack")),
                ]),
            ),
            (
                "质量验收",
                "\n".join([
                    "正文必须让 chapter_task、reader_expectation、required_ending_change 可被读者感知。",
                    "每个场景至少改变一个事实、关系、情绪或读者问题。",
                    "伏笔推进必须落实到具体动作、物件、对话或选择。",
                    "不要输出标题、说明、审稿报告或列表。",
                ]),
            ),
        ]

    def _format_json(self, value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)

    def _format_value(self, value: Any) -> str:
        if value is None:
            return "无"
        if isinstance(value, str):
            return value or "无"
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
