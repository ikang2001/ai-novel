"""Deterministic learning from user-confirmed chapter revisions."""

from __future__ import annotations

import difflib
import re
from typing import Any, Dict, Optional


def _paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text or "") if part.strip()]


def _dialogue_count(text: str) -> int:
    return len(re.findall(r"[“\"].+?[”\"]", text or "", flags=re.S))


def _changed_ratio(before: list[str], after: list[str]) -> float:
    if not before and not after:
        return 0.0
    matcher = difflib.SequenceMatcher(a=before, b=after)
    return round(1 - matcher.ratio(), 4)


def build_revision_preference(
    ai_draft: str,
    user_confirmed: str,
    previous: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a compact, deterministic preference profile from draft vs final text."""
    before = ai_draft or ""
    after = user_confirmed or ""
    before_paragraphs = _paragraphs(before)
    after_paragraphs = _paragraphs(after)

    length_delta = len(after) - len(before)
    before_dialogue = _dialogue_count(before)
    after_dialogue = _dialogue_count(after)
    dialogue_delta = after_dialogue - before_dialogue

    opening_changed = bool(before_paragraphs and after_paragraphs and before_paragraphs[0] != after_paragraphs[0])
    ending_changed = bool(before_paragraphs and after_paragraphs and before_paragraphs[-1] != after_paragraphs[-1])
    changed_paragraph_ratio = _changed_ratio(before_paragraphs, after_paragraphs)

    signals = []
    if length_delta > max(300, int(len(before) * 0.08)):
        signals.append("prefers_expansion")
    elif length_delta < -max(300, int(len(before) * 0.08)):
        signals.append("prefers_tighter_prose")
    if dialogue_delta >= 2:
        signals.append("adds_dialogue")
    elif dialogue_delta <= -2:
        signals.append("reduces_dialogue")
    if opening_changed:
        signals.append("rewrites_opening_bridge")
    if ending_changed:
        signals.append("rewrites_ending_hook")
    if changed_paragraph_ratio >= 0.35:
        signals.append("substantial_rewrite")

    summary_parts = []
    if "prefers_expansion" in signals:
        summary_parts.append("用户倾向扩写细节")
    if "prefers_tighter_prose" in signals:
        summary_parts.append("用户倾向压缩冗余")
    if "adds_dialogue" in signals:
        summary_parts.append("用户会增加对话推动")
    if "rewrites_opening_bridge" in signals:
        summary_parts.append("用户重视章节开头承接")
    if "rewrites_ending_hook" in signals:
        summary_parts.append("用户重视章尾钩子")
    if not summary_parts:
        summary_parts.append("用户本次改动较轻，保持当前风格")

    return {
        "source": "deterministic_diff",
        "lengthDelta": length_delta,
        "lengthRatio": round((len(after) / len(before)), 4) if before else 1,
        "paragraphCountDelta": len(after_paragraphs) - len(before_paragraphs),
        "changedParagraphRatio": changed_paragraph_ratio,
        "dialogueDelta": dialogue_delta,
        "openingChanged": opening_changed,
        "endingChanged": ending_changed,
        "signals": signals,
        "summary": "；".join(summary_parts),
        "previous": previous or None,
    }
