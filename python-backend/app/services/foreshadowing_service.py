"""伏笔管理服务"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from databases import Database

logger = logging.getLogger(__name__)


class ForeshadowingService:
    """伏笔生命周期管理服务"""

    DEFAULT_DEBT_POLICY = {
        "importanceThresholds": {"5": 8, "4": 10, "default": 14},
        "nearTargetLeadChapters": 3,
    }

    def __init__(self, db: Database):
        self.db = db

    async def create_foreshadowing(self, novel_id: int, surface: str,
                                   hidden_truth: Optional[str] = None,
                                   category: Optional[str] = None,
                                   related_characters: Optional[List[str]] = None,
                                   keywords: Optional[List[str]] = None,
                                   target_chapter: Optional[str] = None,
                                   importance: int = 3,
                                   planted_chapter_id: Optional[int] = None) -> int:
        """创建伏笔，返回 foreshadowing_id"""
        now = datetime.now()
        query = """
            INSERT INTO foreshadowing (
                novelId, surface, hiddenTruth, category,
                relatedCharacters, keywords, targetChapter,
                importance, status, lifecycleStage, plantedChapterId,
                lastActionType, lastActionChapter, lastActionNote,
                createTime, updateTime
            ) VALUES (
                :novelId, :surface, :hiddenTruth, :category,
                :relatedCharacters, :keywords, :targetChapter,
                :importance, :status, :lifecycleStage, :plantedChapterId,
                :lastActionType, :lastActionChapter, :lastActionNote,
                :createTime, :updateTime
            )
        """
        result = await self.db.execute(
            query=query,
            values={
                "novelId": novel_id,
                "surface": surface,
                "hiddenTruth": hidden_truth,
                "category": category,
                "relatedCharacters": json.dumps(related_characters, ensure_ascii=False) if related_characters else None,
                "keywords": json.dumps(keywords, ensure_ascii=False) if keywords else None,
                "targetChapter": target_chapter,
                "importance": importance,
                "status": "active",
                "lifecycleStage": "planted",
                "plantedChapterId": planted_chapter_id,
                "lastActionType": "plant",
                "lastActionChapter": None,
                "lastActionNote": "新埋伏笔",
                "createTime": now,
                "updateTime": now,
            },
        )
        logger.info("伏笔创建成功, id=%s, surface=%s", result, surface[:20])
        return result

    async def get_foreshadowing(self, foreshadowing_id: int) -> Optional[Dict[str, Any]]:
        """获取伏笔详情"""
        query = "SELECT * FROM foreshadowing WHERE id = :id"
        row = await self.db.fetch_one(query=query, values={"id": foreshadowing_id})
        return self._parse(row) if row else None

    async def get_active_foreshadowing(self, novel_id: int) -> List[Dict[str, Any]]:
        """获取所有活跃伏笔"""
        return await self.get_all_foreshadowing(novel_id, status="active")

    async def get_all_foreshadowing(self, novel_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取伏笔列表（可按状态筛选）"""
        if status:
            query = """
                SELECT * FROM foreshadowing
                WHERE novelId = :novelId AND status = :status
                ORDER BY importance DESC, createTime DESC
            """
            rows = await self.db.fetch_all(query=query, values={"novelId": novel_id, "status": status})
        else:
            query = """
                SELECT * FROM foreshadowing
                WHERE novelId = :novelId
                ORDER BY status, importance DESC, createTime DESC
            """
            rows = await self.db.fetch_all(query=query, values={"novelId": novel_id})
        return [self._parse(row) for row in rows]

    async def search_by_keywords(self, novel_id: int, keywords: List[str]) -> List[Dict[str, Any]]:
        """根据关键词检索活跃伏笔

        检索逻辑：
        1. 伏笔的 keywords 字段（JSON数组）与传入关键词有交集
        2. 或 伏笔的 related_characters 字段（JSON数组）与传入关键词有交集
        3. 只搜活跃的伏笔

        为什么用 Python 过滤而不是 SQL？
        因为 keywords 和 related_characters 是 JSON 数组字段，
        MySQL 的 JSON 查询语法复杂且性能不稳定。
        先查出所有活跃伏笔，再在 Python 里过滤，代码更清晰。
        """
        all_active = await self.get_active_foreshadowing(novel_id)
        results = []
        keyword_set = set(keywords)

        for fs in all_active:
            # 检查 keywords 字段
            fs_keywords = set(fs.get("keywords") or [])
            if fs_keywords & keyword_set:
                results.append(fs)
                continue

            # 检查 related_characters 字段
            fs_characters = set(fs.get("relatedCharacters") or [])
            if fs_characters & keyword_set:
                results.append(fs)
                continue

        return results

    async def get_stale_foreshadowing(self, novel_id: int, current_chapter: int,
                                      threshold: int = 20) -> List[Dict[str, Any]]:
        """获取超过 threshold 章未提及的活跃伏笔

        计算逻辑：
        staleness = current_chapter - (last_mentioned_chapter or planted_chapter_number)
        如果 staleness > threshold，则认为"过期"
        """
        all_active = await self.get_active_foreshadowing(novel_id)
        results = []
        for fs in all_active:
            last_mentioned = fs.get("lastMentionedChapter") or 0
            # 如果从未提及，用埋设章节号
            if last_mentioned == 0:
                # 需要从 planted_chapter_id 查出 chapter_number
                # 简化处理：如果 planted_chapter_id 存在，假设 chapter_number 就是它
                # 实际应该查 chapter 表，但这里为了简化用 planted_chapter_id 作为近似值
                last_mentioned = fs.get("plantedChapterId") or 0

            if last_mentioned > 0 and (current_chapter - last_mentioned) > threshold:
                results.append(fs)

        return results

    async def get_hook_debt(self, novel_id: int, current_chapter: int,
                            limit: int = 10) -> List[Dict[str, Any]]:
        """按沉默章节数和重要度计算需要提醒的伏笔债务。"""
        policy = await self._get_debt_policy(novel_id)
        query = """
            SELECT f.*, c.chapterNumber AS plantedChapterNumber
            FROM foreshadowing f
            LEFT JOIN chapter c ON f.plantedChapterId = c.id
            WHERE f.novelId = :novelId AND f.status = 'active'
            ORDER BY f.importance DESC, f.createTime ASC
        """
        rows = await self.db.fetch_all(query=query, values={"novelId": novel_id})
        debts = []
        for row in rows:
            fs = self._parse(row)
            planted_number = fs.get("plantedChapterNumber") or 0
            anchor = max(
                fs.get("lastMentionedChapter") or 0,
                fs.get("lastActionChapter") or 0,
                planted_number,
            )
            if not anchor:
                anchor = current_chapter
            silent_chapters = max(0, current_chapter - anchor)
            importance = int(fs.get("importance") or 3)
            threshold = self._threshold_for_importance(importance, policy)
            stage = fs.get("lifecycleStage") or "open"

            low, high = self._parse_chapter_range(fs.get("targetChapter") or "")
            near_lead = int(policy.get("nearTargetLeadChapters") or 3)
            near_target = low is not None and (low - near_lead) <= current_chapter <= (high or low)
            if silent_chapters >= threshold:
                stage = "pressured"
            elif near_target:
                stage = "near_payoff"
            elif fs.get("lastActionType") in {"mention", "advance"}:
                stage = "progressing"
            elif stage == "planted" and silent_chapters > 0:
                stage = "open"

            if stage in {"pressured", "near_payoff", "progressing"}:
                fs["silentChapters"] = silent_chapters
                fs["debtReason"] = self._build_debt_reason(fs, stage, silent_chapters)
                fs["computedLifecycleStage"] = stage
                debts.append(fs)

        return sorted(
            debts,
            key=lambda item: (
                0 if item.get("computedLifecycleStage") == "pressured" else 1,
                -(item.get("importance") or 0),
                -(item.get("silentChapters") or 0),
            ),
        )[:limit]

    async def _get_debt_policy(self, novel_id: int) -> Dict[str, Any]:
        """读取伏笔债务策略；未配置时使用默认策略。"""
        policy = dict(self.DEFAULT_DEBT_POLICY)
        row = await self.db.fetch_one(
            "SELECT stateData FROM novel_state WHERE novelId = :novelId AND stateType = 'foreshadowing_debt_policy'",
            values={"novelId": novel_id},
        )
        if row and row["stateData"]:
            try:
                custom = json.loads(row["stateData"])
                if isinstance(custom, dict):
                    thresholds = custom.get("importanceThresholds")
                    if isinstance(thresholds, dict):
                        policy["importanceThresholds"] = {**policy["importanceThresholds"], **thresholds}
                    if custom.get("nearTargetLeadChapters") is not None:
                        policy["nearTargetLeadChapters"] = int(custom["nearTargetLeadChapters"])
            except (json.JSONDecodeError, TypeError, ValueError):
                logger.warning("伏笔债务策略解析失败, novel_id=%s", novel_id)
        return policy

    @classmethod
    def _threshold_for_importance(cls, importance: int, policy: Optional[Dict[str, Any]] = None) -> int:
        """根据重要度和策略返回沉默章节阈值。"""
        active_policy = policy or cls.DEFAULT_DEBT_POLICY
        thresholds = active_policy.get("importanceThresholds") or {}
        if importance >= 5:
            key = "5"
        elif importance == 4:
            key = "4"
        else:
            key = str(importance)
        return int(thresholds.get(key, thresholds.get("default", 14)))

    async def get_near_target_foreshadowing(self, novel_id: int,
                                            current_chapter: int) -> List[Dict[str, Any]]:
        """获取接近目标揭示章节的伏笔

        target_chapter 格式："80-100" 或 "50"
        判断逻辑：current_chapter 在 [low-5, high] 范围内
        """
        all_active = await self.get_active_foreshadowing(novel_id)
        results = []
        for fs in all_active:
            target = fs.get("targetChapter")
            if not target:
                continue

            low, high = self._parse_chapter_range(target)
            if low is not None and (low - 5) <= current_chapter <= (high or low):
                results.append(fs)

        return results

    async def record_mention(self, foreshadowing_id: int, chapter_id: int,
                             chapter_number: int, context: Optional[str] = None) -> bool:
        """记录伏笔被提及（呼应）

        为什么用追加而不是覆盖 mention_history？
        因为一个伏笔可能被提及多次，每次都要记录。
        """
        # 读取现有的 mention_history
        row = await self.db.fetch_one(
            "SELECT mentionHistory FROM foreshadowing WHERE id = :id",
            {"id": foreshadowing_id},
        )
        history = []
        if row and row["mentionHistory"]:
            try:
                history = json.loads(row["mentionHistory"])
            except json.JSONDecodeError:
                history = []

        # 追加新记录
        history.append({
            "chapterId": chapter_id,
            "chapterNumber": chapter_number,
            "context": context,
            "time": datetime.now().isoformat(),
        })

        # 更新
        query = """
            UPDATE foreshadowing
            SET mentionHistory = :history,
                lastMentionedChapter = :chapterNumber,
                lifecycleStage = :lifecycleStage,
                lastActionType = :lastActionType,
                lastActionChapter = :chapterNumber,
                lastActionNote = :lastActionNote,
                updateTime = :updateTime
            WHERE id = :id
        """
        await self.db.execute(query=query, values={
            "history": json.dumps(history, ensure_ascii=False),
            "chapterNumber": chapter_number,
            "lifecycleStage": "progressing",
            "lastActionType": "mention",
            "lastActionNote": context or "本章呼应",
            "updateTime": datetime.now(),
            "id": foreshadowing_id,
        })
        return True

    async def resolve_foreshadowing(self, foreshadowing_id: int, chapter_id: Optional[int] = None) -> bool:
        """标记伏笔为已揭示"""
        query = """
            UPDATE foreshadowing
            SET status = 'resolved',
                lifecycleStage = 'near_payoff',
                resolvedChapterId = :chapterId,
                lastActionType = 'resolve',
                lastActionNote = '伏笔揭示',
                updateTime = :updateTime
            WHERE id = :id
        """
        await self.db.execute(query=query, values={
            "chapterId": chapter_id,
            "updateTime": datetime.now(),
            "id": foreshadowing_id,
        })
        logger.info("伏笔已揭示, id=%s, chapter_id=%s", foreshadowing_id, chapter_id)
        return True

    async def update_lifecycle(self, foreshadowing_id: int, lifecycle_stage: str,
                               action_type: Optional[str] = None,
                               chapter_number: Optional[int] = None,
                               note: Optional[str] = None) -> bool:
        """更新伏笔内部生命周期。"""
        query = """
            UPDATE foreshadowing
            SET lifecycleStage = :lifecycleStage,
                lastActionType = :lastActionType,
                lastActionChapter = :lastActionChapter,
                lastActionNote = :lastActionNote,
                updateTime = :updateTime
            WHERE id = :id
        """
        await self.db.execute(query=query, values={
            "lifecycleStage": lifecycle_stage,
            "lastActionType": action_type,
            "lastActionChapter": chapter_number,
            "lastActionNote": note,
            "updateTime": datetime.now(),
            "id": foreshadowing_id,
        })
        return True

    async def abandon_foreshadowing(self, foreshadowing_id: int) -> bool:
        """标记伏笔为已放弃"""
        query = "UPDATE foreshadowing SET status = 'abandoned', updateTime = :updateTime WHERE id = :id"
        await self.db.execute(query=query, values={"updateTime": datetime.now(), "id": foreshadowing_id})
        return True

    async def update_foreshadowing(self, foreshadowing_id: int, **kwargs) -> bool:
        """更新伏笔信息"""
        if not kwargs:
            return True

        field_mapping = {
            "surface": "surface",
            "hidden_truth": "hiddenTruth",
            "category": "category",
            "related_characters": "relatedCharacters",
            "keywords": "keywords",
            "target_chapter": "targetChapter",
            "importance": "importance",
            "lifecycle_stage": "lifecycleStage",
            "last_action_type": "lastActionType",
            "last_action_chapter": "lastActionChapter",
            "last_action_note": "lastActionNote",
        }
        json_fields = {"related_characters", "keywords"}

        updates = []
        values = {"id": foreshadowing_id}
        for python_key, db_key in field_mapping.items():
            if python_key in kwargs:
                value = kwargs[python_key]
                if python_key in json_fields and value is not None:
                    value = json.dumps(value, ensure_ascii=False)
                updates.append(f"{db_key} = :{python_key}")
                values[python_key] = value

        if not updates:
            return True

        updates.append("updateTime = :updateTime")
        values["updateTime"] = datetime.now()

        query = f"UPDATE foreshadowing SET {', '.join(updates)} WHERE id = :id"
        await self.db.execute(query=query, values=values)
        return True

    def _parse(self, row) -> Dict[str, Any]:
        """解析数据库行，处理 JSON 字段"""
        d = dict(row)
        for field in ("relatedCharacters", "relatedLocations", "relatedSkills",
                       "keywords", "mentionHistory"):
            if d.get(field) and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except json.JSONDecodeError:
                    pass
        if d.get("createTime"):
            d["createTime"] = d["createTime"].isoformat()
        if d.get("updateTime"):
            d["updateTime"] = d["updateTime"].isoformat()
        return d

    def _build_debt_reason(self, fs: Dict[str, Any], stage: str, silent_chapters: int) -> str:
        """生成伏笔债务说明。"""
        if stage == "pressured":
            return f"已沉默{silent_chapters}章，重要度{fs.get('importance', 3)}，本章应推进、解释或明确暂缓。"
        if stage == "near_payoff":
            return f"接近计划揭示区间{fs.get('targetChapter')}，需要制造清晰铺垫或兑现。"
        return f"已有推进记录，需避免只口头提及，最好用动作、物件或对话继续推进。"

    def _parse_chapter_range(self, target: str):
        """解析章节范围字符串，如 '80-100' -> (80, 100)，'50' -> (50, 50)"""
        try:
            if "-" in target:
                parts = target.split("-")
                return int(parts[0].strip()), int(parts[1].strip())
            else:
                val = int(target.strip())
                return val, val
        except (ValueError, IndexError):
            return None, None
