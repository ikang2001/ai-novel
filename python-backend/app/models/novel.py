"""小说相关 ORM 模型"""

from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, String, DateTime, SmallInteger, Text, Integer, Boolean
)
from sqlalchemy.sql import func

from app.database import Base


class Novel(Base):
    """小说主表"""

    __tablename__ = "novel"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    user_id = Column("userId", BigInteger, nullable=False, comment="用户ID")
    title = Column(String(100), nullable=False, comment="书名")
    genre = Column(String(50), nullable=True, comment="题材：xuanhuan/dushi/xuanyi/kehuang/yanqing/lishi/qita")
    target_readers = Column("targetReaders", String(20), nullable=True, comment="目标读者：male/female/general")
    target_word_count = Column("targetWordCount", Integer, nullable=True, comment="目标总字数")

    # 设定（可随时修改）
    world_setting = Column("worldSetting", Text, nullable=True, comment="世界观设定（JSON）")
    volume_outline = Column("volumeOutline", Text, nullable=True, comment="卷级大纲（JSON）")
    style_guide = Column("styleGuide", Text, nullable=True, comment="风格指南（JSON）")
    synopsis = Column(Text, nullable=True, comment="全书梗概")

    # 状态
    status = Column(String(20), nullable=False, default="ongoing", comment="状态：ongoing/completed/paused")
    phase = Column(String(40), nullable=False, default="PENDING", comment="阶段")
    current_chapter_number = Column("currentChapterNumber", Integer, nullable=False, default=0, comment="当前章节数")
    current_volume_number = Column("currentVolumeNumber", Integer, nullable=False, default=1, comment="当前卷号")
    total_word_count = Column("totalWordCount", Integer, nullable=False, default=0, comment="总字数")

    # 时间
    create_time = Column("createTime", DateTime, nullable=False, default=func.now(), comment="创建时间")
    update_time = Column("updateTime", DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    is_delete = Column("isDelete", SmallInteger, nullable=False, default=0, comment="是否删除")


class Chapter(Base):
    """章节表"""

    __tablename__ = "chapter"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    novel_id = Column("novelId", BigInteger, nullable=False, comment="小说ID")
    volume_number = Column("volumeNumber", Integer, nullable=False, default=1, comment="卷号")
    chapter_number = Column("chapterNumber", Integer, nullable=False, comment="章节号")
    title = Column(String(100), nullable=True, comment="章节标题")

    # 内容
    outline = Column(Text, nullable=True, comment="本章大纲（JSON）")
    content = Column(Text, nullable=True, comment="正文（Markdown）")
    summary = Column(Text, nullable=True, comment="本章摘要（归档时生成，约150字）")
    word_count = Column("wordCount", Integer, nullable=False, default=0, comment="字数")

    # 归档数据
    character_states = Column("characterStates", Text, nullable=True, comment="本章结束时角色状态快照（JSON）")
    context_snapshot_id = Column("contextSnapshotId", BigInteger, nullable=True, comment="上下文快照ID")

    # 状态
    status = Column(String(20), nullable=False, default="draft", comment="状态：draft/confirmed/revised")

    # 时间
    create_time = Column("createTime", DateTime, nullable=False, default=func.now(), comment="创建时间")
    update_time = Column("updateTime", DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    is_delete = Column("isDelete", SmallInteger, nullable=False, default=0, comment="是否删除")


class Character(Base):
    """角色表"""

    __tablename__ = "character"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    novel_id = Column("novelId", BigInteger, nullable=False, comment="小说ID")

    # 基本信息
    name = Column(String(50), nullable=False, comment="角色名")
    aliases = Column(Text, nullable=True, comment="别名列表（JSON）")
    role_type = Column("roleType", String(20), nullable=True, comment="类型：protagonist/supporting/antagonist/minor")
    is_core = Column("isCore", SmallInteger, nullable=False, default=0, comment="是否核心角色（始终注入上下文）")

    # 描述
    appearance = Column(Text, nullable=True, comment="外貌")
    personality = Column(Text, nullable=True, comment="性格")
    background = Column(Text, nullable=True, comment="背景")
    skills = Column(Text, nullable=True, comment="技能列表（JSON）")
    speech_style = Column("speechStyle", Text, nullable=True, comment="说话风格")

    # 动态状态（随剧情更新）
    current_location = Column("currentLocation", String(100), nullable=True, comment="当前位置")
    current_status = Column("currentStatus", Text, nullable=True, comment="当前状态")
    relationship_map = Column("relationshipMap", Text, nullable=True, comment="与其他角色的关系（JSON）")

    # 记录
    first_appearance_chapter_id = Column("firstAppearanceChapterId", BigInteger, nullable=True, comment="首次出场章节ID")
    last_appearance_chapter_id = Column("lastAppearanceChapterId", BigInteger, nullable=True, comment="最后出场章节ID")
    notes = Column(Text, nullable=True, comment="零散细节记录")

    # 时间
    create_time = Column("createTime", DateTime, nullable=False, default=func.now(), comment="创建时间")
    update_time = Column("updateTime", DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    is_delete = Column("isDelete", SmallInteger, nullable=False, default=0, comment="是否删除")


class Foreshadowing(Base):
    """伏笔表"""

    __tablename__ = "foreshadowing"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    novel_id = Column("novelId", BigInteger, nullable=False, comment="小说ID")

    # 内容
    surface = Column(Text, nullable=False, comment="表面信息（读者看到的）")
    hidden_truth = Column("hiddenTruth", Text, nullable=True, comment="隐藏真相（作者知道的）")
    category = Column(String(20), nullable=True, comment="类型：character/plot/setting/emotion")

    # 关联
    related_characters = Column("relatedCharacters", Text, nullable=True, comment="涉及的角色名（JSON）")
    related_locations = Column("relatedLocations", Text, nullable=True, comment="涉及的地点（JSON）")
    related_skills = Column("relatedSkills", Text, nullable=True, comment="涉及的技能/设定（JSON）")

    # 生命周期
    planted_chapter_id = Column("plantedChapterId", BigInteger, nullable=True, comment="哪章埋的")
    target_chapter = Column("targetChapter", String(50), nullable=True, comment="计划揭示章节范围，如 80-100")
    resolved_chapter_id = Column("resolvedChapterId", BigInteger, nullable=True, comment="实际揭示章节ID（null=未解决）")

    # 检索
    keywords = Column(Text, nullable=True, comment="检索关键词（JSON）")
    importance = Column(SmallInteger, nullable=False, default=3, comment="重要度 1-5")

    # 状态
    status = Column(String(20), nullable=False, default="active", comment="状态：active/resolved/abandoned")

    # 呼应记录
    mention_history = Column("mentionHistory", Text, nullable=True, comment="历史呼应记录（JSON）")
    last_mentioned_chapter = Column("lastMentionedChapter", Integer, nullable=True, comment="最后一次提及的章节号")

    # 时间
    create_time = Column("createTime", DateTime, nullable=False, default=func.now(), comment="创建时间")
    update_time = Column("updateTime", DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")


class Location(Base):
    """地点表"""

    __tablename__ = "location"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    novel_id = Column("novelId", BigInteger, nullable=False, comment="小说ID")
    name = Column(String(100), nullable=False, comment="地点名称")
    description = Column(Text, nullable=True, comment="地点描述")
    first_appearance_chapter_id = Column("firstAppearanceChapterId", BigInteger, nullable=True, comment="首次出现章节ID")
    notes = Column(Text, nullable=True, comment="备注")

    # 时间
    create_time = Column("createTime", DateTime, nullable=False, default=func.now(), comment="创建时间")
    update_time = Column("updateTime", DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")


class ContextSnapshot(Base):
    """上下文快照表（调试用）"""

    __tablename__ = "context_snapshot"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    novel_id = Column("novelId", BigInteger, nullable=False, comment="小说ID")
    chapter_id = Column("chapterId", BigInteger, nullable=False, comment="章节ID")
    context_data = Column("contextData", Text, nullable=True, comment="生成本章时注入的完整上下文（JSON）")
    create_time = Column("createTime", DateTime, nullable=False, default=func.now(), comment="创建时间")
