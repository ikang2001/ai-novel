"""角色知识库服务"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from databases import Database

logger = logging.getLogger(__name__)


class CharacterService:
    """角色知识库管理服务"""

    def __init__(self, db: Database):
        self.db = db

    async def create_character(self, novel_id: int, name: str,
                               role_type: Optional[str] = None,
                               is_core: bool = False,
                               aliases: Optional[List[str]] = None,
                               appearance: Optional[str] = None,
                               personality: Optional[str] = None,
                               background: Optional[str] = None,
                               skills: Optional[List[str]] = None,
                               speech_style: Optional[str] = None) -> int:
        """创建角色，返回 character_id"""
        now = datetime.now()
        query = """
            INSERT INTO `character` (
                novelId, name, aliases, roleType, isCore,
                appearance, personality, background, skills, speechStyle,
                createTime, updateTime
            ) VALUES (
                :novelId, :name, :aliases, :roleType, :isCore,
                :appearance, :personality, :background, :skills, :speechStyle,
                :createTime, :updateTime
            )
        """
        # 为什么表名用反引号 `character`？
        # 因为 character 是 MySQL 保留字，不加反引号会报语法错误。
        result = await self.db.execute(
            query=query,
            values={
                "novelId": novel_id,
                "name": name,
                "aliases": json.dumps(aliases, ensure_ascii=False) if aliases else None,
                "roleType": role_type,
                "isCore": 1 if is_core else 0,
                "appearance": appearance,
                "personality": personality,
                "background": background,
                "skills": json.dumps(skills, ensure_ascii=False) if skills else None,
                "speechStyle": speech_style,
                "createTime": now,
                "updateTime": now,
            },
        )
        logger.info("角色创建成功, character_id=%s, name=%s", result, name)
        return result

    async def get_character(self, character_id: int) -> Optional[Dict[str, Any]]:
        """获取角色详情"""
        query = "SELECT * FROM `character` WHERE id = :characterId AND isDelete = 0"
        row = await self.db.fetch_one(query=query, values={"characterId": character_id})
        if row:
            return self._parse_character(row)
        return None

    async def get_all_characters(self, novel_id: int) -> List[Dict[str, Any]]:
        """获取小说的所有角色"""
        query = """
            SELECT * FROM `character`
            WHERE novelId = :novelId AND isDelete = 0
            ORDER BY roleType, name
        """
        rows = await self.db.fetch_all(query=query, values={"novelId": novel_id})
        return [self._parse_character(row) for row in rows]

    async def get_core_characters(self, novel_id: int) -> List[Dict[str, Any]]:
        """获取核心角色（始终注入上下文的角色）

        核心角色的判断逻辑：
        1. isCore = 1（作者手动标记为核心）
        2. 或 role_type 为 protagonist/supporting/antagonist（主角/配角/反派默认为核心）
        """
        query = """
            SELECT * FROM `character`
            WHERE novelId = :novelId AND isDelete = 0
              AND (isCore = 1 OR roleType IN ('protagonist', 'supporting', 'antagonist'))
            ORDER BY
              CASE roleType
                WHEN 'protagonist' THEN 1
                WHEN 'antagonist' THEN 2
                WHEN 'supporting' THEN 3
                ELSE 4
              END,
              name
        """
        rows = await self.db.fetch_all(query=query, values={"novelId": novel_id})
        return [self._parse_character(row) for row in rows]

    async def find_by_name(self, novel_id: int, name: str) -> Optional[Dict[str, Any]]:
        """根据角色名查找角色（精确匹配 name 或 aliases 中包含）

        为什么先查 name 再查 aliases？
        因为 name 是精确匹配（用 =），效率高；
        aliases 是 JSON 字段，需要用 LIKE 模糊匹配，效率低。
        先试快的，再试慢的。
        """
        # 先精确匹配 name
        query = """
            SELECT * FROM `character`
            WHERE novelId = :novelId AND name = :name AND isDelete = 0
        """
        row = await self.db.fetch_one(query=query, values={"novelId": novel_id, "name": name})
        if row:
            return self._parse_character(row)

        # 再模糊匹配 aliases（JSON 数组中包含该名字）
        query = """
            SELECT * FROM `character`
            WHERE novelId = :novelId AND aliases LIKE :name AND isDelete = 0
        """
        row = await self.db.fetch_one(query=query, values={"novelId": novel_id, "name": f'%"{name}"%'})
        if row:
            return self._parse_character(row)

        return None

    async def update_character(self, character_id: int, **kwargs) -> bool:
        """更新角色信息

        为什么用 **kwargs？
        因为角色字段很多，调用方可能只更新其中几个。
        用 kwargs 可以灵活传入要更新的字段。
        """
        if not kwargs:
            return True

        # 字段名映射：Python snake_case -> 数据库 camelCase
        field_mapping = {
            "name": "name",
            "aliases": "aliases",
            "role_type": "roleType",
            "is_core": "isCore",
            "appearance": "appearance",
            "personality": "personality",
            "background": "background",
            "skills": "skills",
            "speech_style": "speechStyle",
            "current_location": "currentLocation",
            "current_status": "currentStatus",
            "relationship_map": "relationshipMap",
            "first_appearance_chapter_id": "firstAppearanceChapterId",
            "last_appearance_chapter_id": "lastAppearanceChapterId",
            "notes": "notes",
        }

        # 需要 JSON 序列化的字段
        json_fields = {"aliases", "skills", "relationship_map"}

        updates = []
        values = {"characterId": character_id}
        for python_key, db_key in field_mapping.items():
            if python_key in kwargs:
                value = kwargs[python_key]
                if python_key in json_fields and value is not None:
                    value = json.dumps(value, ensure_ascii=False)
                if python_key == "is_core":
                    value = 1 if value else 0
                updates.append(f"`{db_key}` = :{python_key}")
                values[python_key] = value

        if not updates:
            return True

        updates.append("updateTime = :updateTime")
        values["updateTime"] = datetime.now()

        query = f"UPDATE `character` SET {', '.join(updates)} WHERE id = :characterId AND isDelete = 0"
        await self.db.execute(query=query, values=values)
        return True

    async def update_character_state(self, character_id: int,
                                     current_location: Optional[str] = None,
                                     current_status: Optional[str] = None,
                                     new_details: Optional[str] = None) -> bool:
        """更新角色动态状态（归档时自动调用）

        特别处理 new_details：
        不是覆盖 notes，而是追加到 notes 末尾。
        这样角色的细节记录会随章节积累。
        """
        updates = []
        values = {"characterId": character_id}

        if current_location is not None:
            updates.append("currentLocation = :currentLocation")
            values["currentLocation"] = current_location

        if current_status is not None:
            updates.append("currentStatus = :currentStatus")
            values["currentStatus"] = current_status

        if new_details:
            # 追加到 notes 字段（如果已有内容，用换行连接）
            # 先读取现有 notes
            row = await self.db.fetch_one(
                "SELECT notes FROM `character` WHERE id = :characterId",
                {"characterId": character_id},
            )
            existing_notes = row["notes"] if row and row["notes"] else ""
            combined_notes = f"{existing_notes}\n{new_details}".strip()
            updates.append("notes = :notes")
            values["notes"] = combined_notes

        if not updates:
            return True

        updates.append("updateTime = :updateTime")
        values["updateTime"] = datetime.now()

        query = f"UPDATE `character` SET {', '.join(updates)} WHERE id = :characterId AND isDelete = 0"
        await self.db.execute(query=query, values=values)
        return True

    async def set_last_appearance(self, character_id: int, chapter_id: int) -> bool:
        """更新角色最后出场章节"""
        query = """
            UPDATE `character`
            SET lastAppearanceChapterId = :chapterId, updateTime = :updateTime
            WHERE id = :characterId AND isDelete = 0
        """
        await self.db.execute(query=query, values={
            "chapterId": chapter_id,
            "updateTime": datetime.now(),
            "characterId": character_id,
        })
        return True

    async def delete_character(self, character_id: int) -> bool:
        """删除角色（软删除）"""
        query = "UPDATE `character` SET isDelete = 1, updateTime = :updateTime WHERE id = :characterId"
        await self.db.execute(query=query, values={"updateTime": datetime.now(), "characterId": character_id})
        return True

    async def get_all_current_states(self, novel_id: int) -> List[Dict[str, Any]]:
        """获取所有角色的当前状态（用于上下文注入）"""
        query = """
            SELECT name, roleType, currentLocation, currentStatus
            FROM `character`
            WHERE novelId = :novelId AND isDelete = 0
            ORDER BY
              CASE roleType
                WHEN 'protagonist' THEN 1
                WHEN 'antagonist' THEN 2
                WHEN 'supporting' THEN 3
                ELSE 4
              END
        """
        rows = await self.db.fetch_all(query=query, values={"novelId": novel_id})
        return [
            {
                "name": row["name"],
                "role_type": row["roleType"],
                "location": row["currentLocation"] or "未知",
                "status": row["currentStatus"] or "正常",
            }
            for row in rows
        ]

    def _parse_character(self, row) -> Dict[str, Any]:
        """解析数据库行为字典，处理 JSON 字段"""
        d = dict(row)
        # 解析 JSON 字段
        for field in ("aliases", "skills", "relationshipMap"):
            if d.get(field) and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except json.JSONDecodeError:
                    pass
        return d
