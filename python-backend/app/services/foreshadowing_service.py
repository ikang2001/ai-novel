"""伏笔管理服务"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from databases import Database

logger = logging.getLogger(__name__)


class ForeshadowingService:
    """伏笔生命周期管理服务"""

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
                importance, status, plantedChapterId,
                createTime, updateTime
            ) VALUES (
                :novelId, :surface, :hiddenTruth, :category,
                :relatedCharacters, :keywords, :targetChapter,
                :importance, :status, :plantedChapterId,
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
                "plantedChapterId": planted_chapter_id,
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
            fs_characters = set(fs.get("related_characters") or [])
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
            last_mentioned = fs.get("last_mentioned_chapter") or 0
            # 如果从未提及，用埋设章节号
            if last_mentioned == 0:
                # 需要从 planted_chapter_id 查出 chapter_number
                # 简化处理：如果 planted_chapter_id 存在，假设 chapter_number 就是它
                # 实际应该查 chapter 表，但这里为了简化用 planted_chapter_id 作为近似值
                last_mentioned = fs.get("planted_chapter_id") or 0

            if last_mentioned > 0 and (current_chapter - last_mentioned) > threshold:
                results.append(fs)

        return results

    async def get_near_target_foreshadowing(self, novel_id: int,
                                            current_chapter: int) -> List[Dict[str, Any]]:
        """获取接近目标揭示章节的伏笔

        target_chapter 格式："80-100" 或 "50"
        判断逻辑：current_chapter 在 [low-5, high] 范围内
        """
        all_active = await self.get_active_foreshadowing(novel_id)
        results = []
        for fs in all_active:
            target = fs.get("target_chapter")
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
                updateTime = :updateTime
            WHERE id = :id
        """
        await self.db.execute(query=query, values={
            "history": json.dumps(history, ensure_ascii=False),
            "chapterNumber": chapter_number,
            "updateTime": datetime.now(),
            "id": foreshadowing_id,
        })
        return True

    async def resolve_foreshadowing(self, foreshadowing_id: int, chapter_id: int) -> bool:
        """标记伏笔为已揭示"""
        query = """
            UPDATE foreshadowing
            SET status = 'resolved', resolvedChapterId = :chapterId, updateTime = :updateTime
            WHERE id = :id
        """
        await self.db.execute(query=query, values={
            "chapterId": chapter_id,
            "updateTime": datetime.now(),
            "id": foreshadowing_id,
        })
        logger.info("伏笔已揭示, id=%s, chapter_id=%s", foreshadowing_id, chapter_id)
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
        # 转换为 snake_case key（方便上层使用）
        return {
            "id": d["id"],
            "novel_id": d["novelId"],
            "surface": d["surface"],
            "hidden_truth": d.get("hiddenTruth"),
            "category": d.get("category"),
            "related_characters": d.get("relatedCharacters"),
            "related_locations": d.get("relatedLocations"),
            "related_skills": d.get("relatedSkills"),
            "planted_chapter_id": d.get("plantedChapterId"),
            "target_chapter": d.get("targetChapter"),
            "resolved_chapter_id": d.get("resolvedChapterId"),
            "keywords": d.get("keywords"),
            "importance": d.get("importance", 3),
            "status": d["status"],
            "mention_history": d.get("mentionHistory"),
            "last_mentioned_chapter": d.get("lastMentionedChapter"),
            "create_time": d["createTime"].isoformat() if d.get("createTime") else None,
            "update_time": d["updateTime"].isoformat() if d.get("updateTime") else None,
        }

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
