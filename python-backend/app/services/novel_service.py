"""小说服务"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Sequence, Callable, Awaitable

from databases import Database
from app.exceptions import ErrorCode, throw_if, throw_if_not
from app.models.novel_enums import ChapterStatusEnum

logger = logging.getLogger(__name__)


class NovelService:
    """小说 CRUD 服务"""

    # 需要做 JSON 反序列化的字段
    NOVEL_JSON_FIELDS = {"worldSetting", "volumeOutline", "styleGuide", "synopsis"}
    CHAPTER_JSON_FIELDS = {"outline", "chapterMemo", "endingState", "qualityReport", "characterStates"}

    def __init__(self, db: Database):
        self.db = db

    def _deserialize_json_fields(self, data: Dict[str, Any], json_fields: set) -> Dict[str, Any]:
        """将 TEXT 类型的 JSON 字段反序列化为 Python 对象"""
        for field in json_fields:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    pass  # 保持原值
        return data

    # ========== 小说 ==========

    async def create_novel(self, user_id: int, title: str, genre: str,
                           target_readers: Optional[str] = None,
                           target_word_count: Optional[int] = None) -> int:
        """创建小说，返回 novel_id"""
        now = datetime.now()
        query = """
            INSERT INTO novel (
                userId, title, genre, targetReaders, targetWordCount,
                status, phase, currentChapterNumber, currentVolumeNumber, totalWordCount,
                createTime, updateTime
            ) VALUES (
                :userId, :title, :genre, :targetReaders, :targetWordCount,
                :status, :phase, :currentChapterNumber, :currentVolumeNumber, :totalWordCount,
                :createTime, :updateTime
            )
        """
        # 为什么用 RETURNING id？
        # 因为 MySQL 的 LAST_INSERT_ID() 在并发时可能不准确，
        # 但 databases 库的 execute 不直接返回自增 ID，
        # 所以我们用 fetch_val 来拿。
        # 实际上 databases 库的 execute 对 INSERT 会返回 lastrowid。
        result = await self.db.execute(
            query=query,
            values={
                "userId": user_id,
                "title": title,
                "genre": genre,
                "targetReaders": target_readers,
                "targetWordCount": target_word_count,
                "status": "ongoing",
                "phase": "PENDING",
                "currentChapterNumber": 0,
                "currentVolumeNumber": 1,
                "totalWordCount": 0,
                "createTime": now,
                "updateTime": now,
            },
        )
        logger.info("小说创建成功, novel_id=%s, userId=%s, title=%s", result, user_id, title)
        return result

    async def get_novel(self, novel_id: int) -> Optional[Dict[str, Any]]:
        """获取小说详情"""
        query = """
            SELECT * FROM novel
            WHERE id = :novelId AND isDelete = 0
        """
        row = await self._fetch_one(query, {"novelId": novel_id})
        if not row:
            return None
        return self._deserialize_json_fields(dict(row), self.NOVEL_JSON_FIELDS)

    async def get_novel_list(self, user_id: int, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """获取用户的小说列表（分页）"""
        # 先查总数
        count_query = "SELECT COUNT(*) FROM novel WHERE userId = :userId AND isDelete = 0"
        total = await self.db.fetch_val(count_query, values={"userId": user_id})

        # 再查分页数据
        offset = (page - 1) * page_size
        query = """
            SELECT * FROM novel
            WHERE userId = :userId AND isDelete = 0
            ORDER BY updateTime DESC
            LIMIT :limit OFFSET :offset
        """
        rows = await self._fetch_all(query, {
            "userId": user_id,
            "limit": page_size,
            "offset": offset,
        })
        return {
            "records": [self._deserialize_json_fields(dict(row), self.NOVEL_JSON_FIELDS) for row in rows],
            "total": total,
            "current": page,
            "pageSize": page_size,
        }

    async def update_novel_setting(self, novel_id: int, world_setting: Optional[Dict] = None,
                                   volume_outline: Optional[List] = None,
                                   style_guide: Optional[Dict] = None) -> bool:
        """更新小说设定

        为什么用动态拼接 SQL？
        因为三个字段都是可选的，只更新传入的字段。
        """
        updates = []
        values = {"novelId": novel_id}
        if world_setting is not None:
            updates.append("worldSetting = :worldSetting")
            values["worldSetting"] = json.dumps(world_setting, ensure_ascii=False)
        if volume_outline is not None:
            updates.append("volumeOutline = :volumeOutline")
            values["volumeOutline"] = json.dumps(volume_outline, ensure_ascii=False)
        if style_guide is not None:
            updates.append("styleGuide = :styleGuide")
            values["styleGuide"] = json.dumps(style_guide, ensure_ascii=False)

        if not updates:
            return True  # 没有要更新的字段，直接返回成功

        updates.append("updateTime = :updateTime")
        values["updateTime"] = datetime.now()

        query = f"UPDATE novel SET {', '.join(updates)} WHERE id = :novelId AND isDelete = 0"
        await self._execute(query, values)
        logger.info("小说设定更新成功, novel_id=%s", novel_id)
        return True

    async def update_novel_status(self, novel_id: int, status: str) -> bool:
        """更新小说状态"""
        query = "UPDATE novel SET status = :status, updateTime = :updateTime WHERE id = :novelId AND isDelete = 0"
        await self._execute(query, {"status": status, "updateTime": datetime.now(), "novelId": novel_id})
        return True

    async def update_novel_phase(self, novel_id: int, phase: str) -> bool:
        """更新小说阶段"""
        query = "UPDATE novel SET phase = :phase, updateTime = :updateTime WHERE id = :novelId AND isDelete = 0"
        await self._execute(query, {"phase": phase, "updateTime": datetime.now(), "novelId": novel_id})
        return True

    async def update_novel_word_count(self, novel_id: int, word_count: int) -> bool:
        """更新小说总字数"""
        query = "UPDATE novel SET totalWordCount = :wc, updateTime = :updateTime WHERE id = :novelId AND isDelete = 0"
        await self._execute(query, {"wc": word_count, "updateTime": datetime.now(), "novelId": novel_id})
        return True

    async def increment_chapter_number(self, novel_id: int) -> int:
        """章节号 +1，返回新的章节号

        为什么用 UPDATE ... SET currentChapterNumber = currentChapterNumber + 1？
        因为这是原子操作，不会出现并发问题。
        """
        query = """
            UPDATE novel
            SET currentChapterNumber = currentChapterNumber + 1,
                updateTime = :updateTime
            WHERE id = :novelId AND isDelete = 0
        """
        await self._execute(query, {"updateTime": datetime.now(), "novelId": novel_id})
        # 读取更新后的值
        row = await self._fetch_one(
            "SELECT currentChapterNumber FROM novel WHERE id = :novelId",
            {"novelId": novel_id},
        )
        return row["currentChapterNumber"]

    async def get_next_chapter_number(self, novel_id: int) -> int:
        """计算下一个章节号，优先填补空缺（如删除第2章后，下一章为第2章）"""
        row = await self._fetch_one(
            """SELECT MIN(t.expected) AS next_num
               FROM (
                   SELECT 1 AS expected
                   UNION ALL
                   SELECT chapterNumber + 1 FROM chapter WHERE novelId = :novelId AND isDelete = 0
               ) t
               WHERE t.expected NOT IN (
                   SELECT chapterNumber FROM chapter WHERE novelId = :novelId AND isDelete = 0
               )""",
            {"novelId": novel_id},
        )
        return row["next_num"] if row and row["next_num"] else 1

    async def update_current_chapter_number(self, novel_id: int, chapter_number: int) -> None:
        """同步更新 novel 表的 currentChapterNumber（仅当新值更大时更新）"""
        query = """
            UPDATE novel
            SET currentChapterNumber = :num, updateTime = :updateTime
            WHERE id = :novelId AND isDelete = 0 AND currentChapterNumber < :num
        """
        await self._execute(query, {"num": chapter_number, "updateTime": datetime.now(), "novelId": novel_id})

    async def update_synopsis(self, novel_id: int, synopsis: str) -> bool:
        """更新全书梗概"""
        query = "UPDATE novel SET synopsis = :synopsis, updateTime = :updateTime WHERE id = :novelId AND isDelete = 0"
        await self._execute(query, {"synopsis": synopsis, "updateTime": datetime.now(), "novelId": novel_id})
        return True

    async def delete_novel(self, novel_id: int) -> bool:
        """删除小说（软删除）"""
        query = "UPDATE novel SET isDelete = 1, updateTime = :updateTime WHERE id = :novelId"
        await self._execute(query, {"updateTime": datetime.now(), "novelId": novel_id})
        logger.info("小说删除成功, novel_id=%s", novel_id)
        return True

    # ========== 章节 ==========

    async def create_chapter(self, novel_id: int, volume_number: int,
                             chapter_number: int, title: Optional[str] = None,
                             outline: Optional[Dict] = None) -> int:
        """创建章节，返回 chapter_id"""
        now = datetime.now()
        query = """
            INSERT INTO chapter (
                novelId, volumeNumber, chapterNumber, title, outline,
                wordCount, status, createTime, updateTime
            ) VALUES (
                :novelId, :volumeNumber, :chapterNumber, :title, :outline,
                :wordCount, :status, :createTime, :updateTime
            )
        """
        result = await self.db.execute(
            query=query,
            values={
                "novelId": novel_id,
                "volumeNumber": volume_number,
                "chapterNumber": chapter_number,
                "title": title,
                "outline": json.dumps(outline, ensure_ascii=False) if outline else None,
                "wordCount": 0,
                "status": "draft",
                "createTime": now,
                "updateTime": now,
            },
        )
        logger.info("章节创建成功, chapter_id=%s, novel_id=%s, chapterNumber=%s", result, novel_id, chapter_number)
        return result

    async def get_chapter(self, chapter_id: int) -> Optional[Dict[str, Any]]:
        """获取章节详情"""
        query = "SELECT * FROM chapter WHERE id = :chapterId AND isDelete = 0"
        row = await self._fetch_one(query, {"chapterId": chapter_id})
        return self._deserialize_json_fields(dict(row), self.CHAPTER_JSON_FIELDS) if row else None

    async def get_chapter_for_update(self, chapter_id: int) -> Optional[Dict[str, Any]]:
        """获取章节详情并加锁。"""
        query = "SELECT * FROM chapter WHERE id = :chapterId AND isDelete = 0 FOR UPDATE"
        row = await self._fetch_one(query, {"chapterId": chapter_id})
        return self._deserialize_json_fields(dict(row), self.CHAPTER_JSON_FIELDS) if row else None

    async def get_chapter_by_number(self, novel_id: int, chapter_number: int) -> Optional[Dict[str, Any]]:
        """根据章节号获取章节"""
        query = """
            SELECT * FROM chapter
            WHERE novelId = :novelId AND chapterNumber = :chapterNumber AND isDelete = 0
        """
        row = await self._fetch_one(query, {"novelId": novel_id, "chapterNumber": chapter_number})
        return self._deserialize_json_fields(dict(row), self.CHAPTER_JSON_FIELDS) if row else None

    async def get_chapters_by_novel(self, novel_id: int) -> List[Dict[str, Any]]:
        """获取小说的所有章节列表"""
        query = """
            SELECT * FROM chapter
            WHERE novelId = :novelId AND isDelete = 0
            ORDER BY chapterNumber ASC
        """
        rows = await self._fetch_all(query, {"novelId": novel_id})
        return [self._deserialize_json_fields(dict(row), self.CHAPTER_JSON_FIELDS) for row in rows]

    async def get_recent_chapters(self, novel_id: int, limit: int = 3) -> List[Dict[str, Any]]:
        """获取最近 N 章（按章节号倒序）"""
        query = """
            SELECT * FROM chapter
            WHERE novelId = :novelId AND isDelete = 0 AND status IN ('confirmed', 'revised', 'draft')
            ORDER BY chapterNumber DESC
            LIMIT :limit
        """
        rows = await self._fetch_all(query, {"novelId": novel_id, "limit": limit})
        # 返回时按章节号正序（最新的在最后）
        return [self._deserialize_json_fields(dict(row), self.CHAPTER_JSON_FIELDS) for row in reversed(rows)]

    async def get_recent_chapters_before(self, novel_id: int, chapter_number: int,
                                         limit: int = 3) -> List[Dict[str, Any]]:
        """获取目标章之前的最近 N 章，避免重写时把当前章旧稿注入上下文。"""
        query = """
            SELECT * FROM chapter
            WHERE novelId = :novelId
              AND chapterNumber < :chapterNumber
              AND isDelete = 0
              AND status IN ('confirmed', 'revised', 'draft')
            ORDER BY chapterNumber DESC
            LIMIT :limit
        """
        rows = await self._fetch_all(query, {
            "novelId": novel_id,
            "chapterNumber": chapter_number,
            "limit": limit,
        })
        return [self._deserialize_json_fields(dict(row), self.CHAPTER_JSON_FIELDS) for row in reversed(rows)]

    async def get_previous_chapter(self, novel_id: int, chapter_number: int) -> Optional[Dict[str, Any]]:
        """获取目标章之前最近一章。"""
        query = """
            SELECT * FROM chapter
            WHERE novelId = :novelId
              AND chapterNumber < :chapterNumber
              AND isDelete = 0
              AND status IN ('confirmed', 'revised', 'draft')
            ORDER BY chapterNumber DESC
            LIMIT 1
        """
        row = await self._fetch_one(query, {"novelId": novel_id, "chapterNumber": chapter_number})
        return self._deserialize_json_fields(dict(row), self.CHAPTER_JSON_FIELDS) if row else None

    async def get_latest_chapter(self, novel_id: int) -> Optional[Dict[str, Any]]:
        """获取最新一章"""
        query = """
            SELECT * FROM chapter
            WHERE novelId = :novelId AND isDelete = 0
            ORDER BY chapterNumber DESC
            LIMIT 1
        """
        row = await self._fetch_one(query, {"novelId": novel_id})
        return self._deserialize_json_fields(dict(row), self.CHAPTER_JSON_FIELDS) if row else None

    async def update_chapter_outline(self, chapter_id: int, outline: Dict) -> bool:
        """更新章节大纲"""
        query = "UPDATE chapter SET outline = :outline, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {
            "outline": json.dumps(outline, ensure_ascii=False) if outline is not None else None,
            "updateTime": datetime.now(),
            "chapterId": chapter_id,
        })
        return True

    async def update_chapter_memo(self, chapter_id: int, memo: Dict[str, Any]) -> bool:
        """更新章节备忘录。"""
        query = "UPDATE chapter SET chapterMemo = :memo, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {
            "memo": json.dumps(memo, ensure_ascii=False) if memo is not None else None,
            "updateTime": datetime.now(),
            "chapterId": chapter_id,
        })
        return True

    async def update_chapter_content(self, chapter_id: int, content: str, word_count: int) -> bool:
        """更新章节正文"""
        query = """
            UPDATE chapter
            SET content = :content, wordCount = :wordCount, updateTime = :updateTime
            WHERE id = :chapterId
        """
        await self._execute(query, {
            "content": content,
            "wordCount": word_count,
            "updateTime": datetime.now(),
            "chapterId": chapter_id,
        })
        return True

    async def update_chapter_summary(self, chapter_id: int, summary: str) -> bool:
        """更新章节摘要"""
        query = "UPDATE chapter SET summary = :summary, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {"summary": summary, "updateTime": datetime.now(), "chapterId": chapter_id})
        return True

    async def update_chapter_ending_state(self, chapter_id: int, ending_state: Dict[str, Any]) -> bool:
        """更新章节结尾状态快照。"""
        query = "UPDATE chapter SET endingState = :endingState, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {
            "endingState": json.dumps(ending_state, ensure_ascii=False) if ending_state is not None else None,
            "updateTime": datetime.now(),
            "chapterId": chapter_id,
        })
        return True

    async def update_chapter_quality_report(self, chapter_id: int, report: Dict[str, Any]) -> bool:
        """更新章节质量审稿报告。"""
        query = "UPDATE chapter SET qualityReport = :report, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {
            "report": json.dumps(report, ensure_ascii=False) if report is not None else None,
            "updateTime": datetime.now(),
            "chapterId": chapter_id,
        })
        return True

    async def update_chapter_context_snapshot_id(self, chapter_id: int, snapshot_id: int) -> bool:
        """关联章节生成时的上下文快照。"""
        query = "UPDATE chapter SET contextSnapshotId = :snapshotId, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {
            "snapshotId": snapshot_id,
            "updateTime": datetime.now(),
            "chapterId": chapter_id,
        })
        return True

    async def update_chapter_status(self, chapter_id: int, status: str) -> bool:
        """更新章节状态"""
        query = "UPDATE chapter SET status = :status, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {"status": status, "updateTime": datetime.now(), "chapterId": chapter_id})
        return True

    async def update_chapter_status_if_in(
        self,
        chapter_id: int,
        status: str,
        allowed_current_statuses: Sequence[str],
    ) -> bool:
        """仅在旧状态匹配时更新章节状态。"""
        placeholders = ", ".join(f":status_{index}" for index in range(len(allowed_current_statuses)))
        values = {
            "status": status,
            "updateTime": datetime.now(),
            "chapterId": chapter_id,
        }
        for index, allowed_status in enumerate(allowed_current_statuses):
            values[f"status_{index}"] = allowed_status
        query = f"""
            UPDATE chapter
            SET status = :status, updateTime = :updateTime
            WHERE id = :chapterId AND status IN ({placeholders}) AND isDelete = 0
        """
        result = await self.db.execute(query=query, values=values)
        return bool(result)

    async def transition_chapter_status(
        self,
        chapter_id: int,
        allowed_current_statuses: Sequence[str],
        target_status: str,
    ) -> Optional[Dict[str, Any]]:
        """在事务里检查并切换章节状态，避免重复提交。"""

        async def action() -> Optional[Dict[str, Any]]:
            chapter = await self.get_chapter_for_update(chapter_id)
            if not chapter or chapter.get("status") not in allowed_current_statuses:
                return None
            await self.update_chapter_status(chapter_id, target_status)
            chapter["status"] = target_status
            return chapter

        return await self.with_transaction(action)

    async def update_chapter_character_states(self, chapter_id: int, states: Dict) -> bool:
        """更新章节结束时角色状态快照"""
        query = "UPDATE chapter SET characterStates = :states, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {
            "states": json.dumps(states, ensure_ascii=False),
            "updateTime": datetime.now(),
            "chapterId": chapter_id,
        })
        return True

    async def create_context_snapshot(self, novel_id: int, chapter_id: int,
                                      context_data: Dict[str, Any],
                                      prompt_data: Optional[Dict[str, Any]] = None,
                                      trace_data: Optional[Dict[str, Any]] = None,
                                      version: str = "v1") -> int:
        """保存生成上下文快照，便于复盘和面试展示生成链路。"""
        query = """
            INSERT INTO context_snapshot (
                novelId, chapterId, contextData, promptData, traceData, version, createTime
            ) VALUES (
                :novelId, :chapterId, :contextData, :promptData, :traceData, :version, :createTime
            )
        """
        snapshot_id = await self.db.execute(query=query, values={
            "novelId": novel_id,
            "chapterId": chapter_id,
            "contextData": json.dumps(context_data, ensure_ascii=False, default=str),
            "promptData": json.dumps(prompt_data or {}, ensure_ascii=False, default=str),
            "traceData": json.dumps(trace_data or {}, ensure_ascii=False, default=str),
            "version": version,
            "createTime": datetime.now(),
        })
        await self.update_chapter_context_snapshot_id(chapter_id, snapshot_id)
        return snapshot_id

    async def get_context_snapshot_by_chapter(self, chapter_id: int) -> Optional[Dict[str, Any]]:
        """读取章节最近一次上下文快照。"""
        row = await self._fetch_one(
            """
            SELECT * FROM context_snapshot
            WHERE chapterId = :chapterId
            ORDER BY createTime DESC
            LIMIT 1
            """,
            {"chapterId": chapter_id},
        )
        if not row:
            return None
        data = dict(row)
        for field in ("contextData", "promptData", "traceData"):
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        if data.get("createTime"):
            data["createTime"] = data["createTime"].isoformat()
        return data

    async def save_chapter_version(self, novel_id: int, chapter_id: int,
                                   version_type: str, content: str,
                                   meta_data: Optional[Dict[str, Any]] = None) -> int:
        """保存章节版本：AI 初稿、自动修订稿、用户确认稿。"""
        query = """
            INSERT INTO chapter_version (
                novelId, chapterId, versionType, content, metaData, createTime
            ) VALUES (
                :novelId, :chapterId, :versionType, :content, :metaData, :createTime
            )
        """
        return await self.db.execute(query=query, values={
            "novelId": novel_id,
            "chapterId": chapter_id,
            "versionType": version_type,
            "content": content,
            "metaData": json.dumps(meta_data or {}, ensure_ascii=False, default=str),
            "createTime": datetime.now(),
        })

    async def get_chapter_versions(self, chapter_id: int, include_content: bool = False) -> List[Dict[str, Any]]:
        """读取章节版本，默认只返回摘要，避免前端调试面板过重。"""
        rows = await self._fetch_all(
            """
            SELECT * FROM chapter_version
            WHERE chapterId = :chapterId
            ORDER BY createTime ASC, id ASC
            """,
            {"chapterId": chapter_id},
        )
        versions = []
        for row in rows:
            data = dict(row)
            content = data.get("content") or ""
            data["contentLength"] = len(content)
            data["contentPreview"] = content[:500]
            if not include_content:
                data.pop("content", None)
            if data.get("metaData") and isinstance(data["metaData"], str):
                try:
                    data["metaData"] = json.loads(data["metaData"])
                except (json.JSONDecodeError, TypeError):
                    pass
            if data.get("createTime"):
                data["createTime"] = data["createTime"].isoformat()
            versions.append(data)
        return versions

    async def get_latest_chapter_version(self, chapter_id: int, version_type: str) -> Optional[Dict[str, Any]]:
        """读取某类章节版本的最新记录。"""
        row = await self._fetch_one(
            """
            SELECT * FROM chapter_version
            WHERE chapterId = :chapterId AND versionType = :versionType
            ORDER BY createTime DESC, id DESC
            LIMIT 1
            """,
            {"chapterId": chapter_id, "versionType": version_type},
        )
        if not row:
            return None
        data = dict(row)
        if data.get("metaData") and isinstance(data["metaData"], str):
            try:
                data["metaData"] = json.loads(data["metaData"])
            except (json.JSONDecodeError, TypeError):
                pass
        if data.get("createTime"):
            data["createTime"] = data["createTime"].isoformat()
        return data

    async def upsert_novel_state(self, novel_id: int, state_type: str,
                                 state_data: Dict[str, Any],
                                 source_chapter_id: Optional[int] = None) -> None:
        """保存或更新小说运行状态。"""
        query = """
            INSERT INTO novel_state (
                novelId, stateType, stateData, sourceChapterId, createTime, updateTime
            ) VALUES (
                :novelId, :stateType, :stateData, :sourceChapterId, :now, :now
            )
            ON DUPLICATE KEY UPDATE
                stateData = VALUES(stateData),
                sourceChapterId = VALUES(sourceChapterId),
                updateTime = VALUES(updateTime)
        """
        await self._execute(query, {
            "novelId": novel_id,
            "stateType": state_type,
            "stateData": json.dumps(state_data, ensure_ascii=False, default=str),
            "sourceChapterId": source_chapter_id,
            "now": datetime.now(),
        })

    async def get_novel_state(self, novel_id: int, state_type: str) -> Optional[Dict[str, Any]]:
        """读取小说运行状态。"""
        row = await self._fetch_one(
            "SELECT * FROM novel_state WHERE novelId = :novelId AND stateType = :stateType",
            {"novelId": novel_id, "stateType": state_type},
        )
        if not row:
            return None
        data = dict(row)
        if data.get("stateData"):
            try:
                data["stateData"] = json.loads(data["stateData"])
            except (json.JSONDecodeError, TypeError):
                pass
        return data

    async def delete_chapter(self, chapter_id: int) -> bool:
        """删除章节（软删除）"""
        query = "UPDATE chapter SET isDelete = 1, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {"updateTime": datetime.now(), "chapterId": chapter_id})
        logger.info("章节删除成功, chapter_id=%s", chapter_id)
        return True

    async def recalculate_novel_stats(self, novel_id: int) -> None:
        """重新计算小说的章节数和总字数（基于实际存在的章节）"""
        row = await self._fetch_one(
            """SELECT COUNT(*) AS chapter_count,
                      COALESCE(SUM(wordCount), 0) AS total_words
               FROM chapter WHERE novelId = :novelId AND isDelete = 0""",
            {"novelId": novel_id},
        )
        await self._execute(
            """UPDATE novel SET currentChapterNumber = :ch, totalWordCount = :wc, updateTime = :updateTime
               WHERE id = :novelId AND isDelete = 0""",
            {"ch": row["chapter_count"], "wc": row["total_words"], "updateTime": datetime.now(), "novelId": novel_id},
        )
        logger.info("小说统计已重算, novel_id=%s, chapters=%s, words=%s", novel_id, row["chapter_count"], row["total_words"])

    async def update_chapter_title(self, chapter_id: int, title: str) -> bool:
        """更新章节标题"""
        query = "UPDATE chapter SET title = :title, updateTime = :updateTime WHERE id = :chapterId"
        await self._execute(query, {"title": title, "updateTime": datetime.now(), "chapterId": chapter_id})
        return True

    async def get_chapter_owner_novel(self, chapter_id: int) -> Optional[Dict[str, Any]]:
        """获取章节所属小说。"""
        chapter = await self.get_chapter(chapter_id)
        if not chapter:
            return None
        novel = await self.get_novel(chapter["novelId"])
        if not novel:
            return None
        return {"chapter": chapter, "novel": novel}

    async def with_transaction(self, action: Callable[[], Awaitable[Any]]) -> Any:
        """在单事务内执行操作。"""
        async with self.db.transaction():
            return await action()

    # ========== 通用 ==========

    async def _execute(self, query: str, values: dict) -> None:
        """执行 SQL"""
        await self.db.execute(query, values)

    async def _fetch_one(self, query: str, values: dict) -> Optional[Any]:
        """查询单条"""
        return await self.db.fetch_one(query=query, values=values)

    async def _fetch_all(self, query: str, values: dict) -> List[Any]:
        """查询多条"""
        return await self.db.fetch_all(query=query, values=values)
