"""小说相关请求/响应模型"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from app.schemas.common import PageRequest


# ========== 请求模型 ==========


class NovelCreateRequest(BaseModel):
    """创建小说请求"""

    title: str = Field(..., min_length=1, max_length=100, description="书名")
    genre: str = Field(..., description="题材：xuanhuan/dushi/xuanyi/kehuang/yanqing/lishi/qita")
    target_readers: Optional[str] = Field(None, alias="targetReaders", description="目标读者：male/female/general")
    target_word_count: Optional[int] = Field(None, alias="targetWordCount", description="目标总字数")
    core_idea: Optional[str] = Field(None, alias="coreIdea", description="核心创意（一句话描述）")
    initial_characters: Optional[List[Dict[str, Any]]] = Field(
        None, alias="initialCharacters", description="初始角色列表（可选，不填则AI生成）"
    )

    class Config:
        populate_by_name = True


class NovelSettingUpdateRequest(BaseModel):
    """修改小说设定请求"""

    world_setting: Optional[Dict[str, Any]] = Field(None, alias="worldSetting", description="世界观设定")
    volume_outline: Optional[List[Dict[str, Any]]] = Field(None, alias="volumeOutline", description="卷级大纲")
    style_guide: Optional[Dict[str, Any]] = Field(None, alias="styleGuide", description="风格指南")

    class Config:
        populate_by_name = True


class StyleAnalyzeRequest(BaseModel):
    """风格分析请求"""

    samples: str = Field(..., min_length=100, description="作者提供的样本文本（2-5章）")


class ChapterPlanRequest(BaseModel):
    """章节大纲规划请求"""

    author_intent: Optional[str] = Field(None, alias="authorIntent", description="作者意图，如'这章写主角在酒吧遇到反派'。为空则AI建议。")

    class Config:
        populate_by_name = True


class ChapterGenerateRequest(BaseModel):
    """章节生成请求"""

    outline: Dict[str, Any] = Field(..., description="本章大纲（JSON）")
    author_note: Optional[str] = Field(None, alias="authorNote", description="作者特别交代")

    class Config:
        populate_by_name = True


class ChapterConfirmRequest(BaseModel):
    """确认章节请求"""

    content: Optional[str] = Field(None, description="修改后的正文（为空则使用生成的内容）")


class ChapterContentUpdateRequest(BaseModel):
    """手动修改章节内容请求"""

    content: str = Field(..., min_length=1, description="修改后的正文")


class CharacterCreateRequest(BaseModel):
    """创建角色请求"""

    name: str = Field(..., min_length=1, max_length=50, description="角色名")
    aliases: Optional[List[str]] = Field(None, description="别名列表")
    role_type: Optional[str] = Field(None, alias="roleType", description="类型：protagonist/supporting/antagonist/minor")
    is_core: Optional[bool] = Field(False, alias="isCore", description="是否核心角色")
    appearance: Optional[str] = Field(None, description="外貌")
    personality: Optional[str] = Field(None, description="性格")
    background: Optional[str] = Field(None, description="背景")
    skills: Optional[List[str]] = Field(None, description="技能列表")
    speech_style: Optional[str] = Field(None, alias="speechStyle", description="说话风格")

    class Config:
        populate_by_name = True


class CharacterUpdateRequest(BaseModel):
    """修改角色请求"""

    name: Optional[str] = Field(None, max_length=50)
    aliases: Optional[List[str]] = None
    role_type: Optional[str] = Field(None, alias="roleType")
    is_core: Optional[bool] = Field(None, alias="isCore")
    appearance: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    skills: Optional[List[str]] = None
    speech_style: Optional[str] = Field(None, alias="speechStyle")
    current_location: Optional[str] = Field(None, alias="currentLocation")
    current_status: Optional[str] = Field(None, alias="currentStatus")
    notes: Optional[str] = None

    class Config:
        populate_by_name = True


class ForeshadowingCreateRequest(BaseModel):
    """创建伏笔请求"""

    surface: str = Field(..., min_length=1, description="表面信息（读者看到的）")
    hidden_truth: Optional[str] = Field(None, alias="hiddenTruth", description="隐藏真相")
    category: Optional[str] = Field(None, description="类型：character/plot/setting/emotion")
    related_characters: Optional[List[str]] = Field(None, alias="relatedCharacters", description="涉及的角色")
    keywords: Optional[List[str]] = Field(None, description="检索关键词")
    target_chapter: Optional[str] = Field(None, alias="targetChapter", description="计划揭示章节范围，如 80-100")
    importance: Optional[int] = Field(3, ge=1, le=5, description="重要度 1-5")

    class Config:
        populate_by_name = True


class ForeshadowingUpdateRequest(BaseModel):
    """修改伏笔请求"""

    surface: Optional[str] = None
    hidden_truth: Optional[str] = Field(None, alias="hiddenTruth")
    category: Optional[str] = None
    related_characters: Optional[List[str]] = Field(None, alias="relatedCharacters")
    keywords: Optional[List[str]] = None
    target_chapter: Optional[str] = Field(None, alias="targetChapter")
    importance: Optional[int] = Field(None, ge=1, le=5)

    class Config:
        populate_by_name = True


# ========== 响应模型（VO） ==========


class NovelVO(BaseModel):
    """小说视图对象"""

    id: int
    user_id: int = Field(..., alias="userId")
    title: str
    genre: Optional[str] = None
    target_readers: Optional[str] = Field(None, alias="targetReaders")
    target_word_count: Optional[int] = Field(None, alias="targetWordCount")
    world_setting: Optional[Any] = Field(None, alias="worldSetting")
    volume_outline: Optional[Any] = Field(None, alias="volumeOutline")
    style_guide: Optional[Any] = Field(None, alias="styleGuide")
    synopsis: Optional[str] = None
    status: str
    phase: Optional[str] = None
    current_chapter_number: int = Field(0, alias="currentChapterNumber")
    current_volume_number: int = Field(1, alias="currentVolumeNumber")
    total_word_count: int = Field(0, alias="totalWordCount")
    create_time: str = Field(..., alias="createTime")
    update_time: str = Field(..., alias="updateTime")

    class Config:
        populate_by_name = True


class ChapterVO(BaseModel):
    """章节视图对象"""

    id: int
    novel_id: int = Field(..., alias="novelId")
    volume_number: int = Field(..., alias="volumeNumber")
    chapter_number: int = Field(..., alias="chapterNumber")
    title: Optional[str] = None
    outline: Optional[Any] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    word_count: int = Field(0, alias="wordCount")
    status: str
    create_time: str = Field(..., alias="createTime")
    update_time: str = Field(..., alias="updateTime")

    class Config:
        populate_by_name = True


class CharacterVO(BaseModel):
    """角色视图对象"""

    id: int
    novel_id: int = Field(..., alias="novelId")
    name: str
    aliases: Optional[List[str]] = None
    role_type: Optional[str] = Field(None, alias="roleType")
    is_core: bool = Field(False, alias="isCore")
    appearance: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    skills: Optional[List[str]] = None
    speech_style: Optional[str] = Field(None, alias="speechStyle")
    current_location: Optional[str] = Field(None, alias="currentLocation")
    current_status: Optional[str] = Field(None, alias="currentStatus")
    relationship_map: Optional[Any] = Field(None, alias="relationshipMap")
    first_appearance_chapter_id: Optional[int] = Field(None, alias="firstAppearanceChapterId")
    last_appearance_chapter_id: Optional[int] = Field(None, alias="lastAppearanceChapterId")
    notes: Optional[str] = None
    create_time: str = Field(..., alias="createTime")
    update_time: str = Field(..., alias="updateTime")

    class Config:
        populate_by_name = True


class ForeshadowingVO(BaseModel):
    """伏笔视图对象"""

    id: int
    novel_id: int = Field(..., alias="novelId")
    surface: str
    hidden_truth: Optional[str] = Field(None, alias="hiddenTruth")
    category: Optional[str] = None
    related_characters: Optional[List[str]] = Field(None, alias="relatedCharacters")
    related_locations: Optional[List[str]] = Field(None, alias="relatedLocations")
    related_skills: Optional[List[str]] = Field(None, alias="relatedSkills")
    planted_chapter_id: Optional[int] = Field(None, alias="plantedChapterId")
    target_chapter: Optional[str] = Field(None, alias="targetChapter")
    resolved_chapter_id: Optional[int] = Field(None, alias="resolvedChapterId")
    keywords: Optional[List[str]] = None
    importance: int = Field(3)
    status: str = "active"
    mention_history: Optional[List[Any]] = Field(None, alias="mentionHistory")
    last_mentioned_chapter: Optional[int] = Field(None, alias="lastMentionedChapter")
    create_time: str = Field(..., alias="createTime")
    update_time: str = Field(..., alias="updateTime")

    class Config:
        populate_by_name = True


# ========== 内部状态模型 ==========


class SceneOutline(BaseModel):
    """场景大纲"""

    scene: int
    location: Optional[str] = None
    characters: Optional[List[str]] = None
    events: str
    emotional_tone: Optional[str] = Field(None, alias="emotionalTone")

    class Config:
        populate_by_name = True


class ChapterOutline(BaseModel):
    """章节大纲"""

    chapter_title: Optional[str] = Field(None, alias="chapterTitle")
    scenes: List[SceneOutline]
    key_dialogues: Optional[List[str]] = Field(None, alias="keyDialogues")
    foreshadowing_to_use: Optional[List[str]] = Field(None, alias="foreshadowingToUse")
    foreshadowing_to_plant: Optional[List[str]] = Field(None, alias="foreshadowingToPlant")
    chapter_hook: Optional[str] = Field(None, alias="chapterHook")

    class Config:
        populate_by_name = True


class ArchiveResult(BaseModel):
    """归档结果（Agent5 输出）"""

    summary: str = Field(..., description="本章摘要（150字以内）")
    word_count: int = Field(0, alias="wordCount", description="实际字数")
    character_updates: Optional[List[Dict[str, Any]]] = Field(None, alias="characterUpdates")
    new_entities: Optional[List[Dict[str, Any]]] = Field(None, alias="newEntities")
    foreshadowing_updates: Optional[List[Dict[str, Any]]] = Field(None, alias="foreshadowingUpdates")
    timeline_events: Optional[List[Dict[str, Any]]] = Field(None, alias="timelineEvents")

    class Config:
        populate_by_name = True


class ConsistencyIssue(BaseModel):
    """连贯性问题"""

    type: str = Field(..., description="问题类型：character_inconsistency/timeline_error/forgotten_foreshadowing/plot_hole/setting_violation")
    severity: str = Field(..., description="严重程度：high/medium/low")
    description: str
    chapters: Optional[List[int]] = None
    suggestion: Optional[str] = None


class ConsistencyReport(BaseModel):
    """连贯性检查报告"""

    issues: List[ConsistencyIssue]
    summary: str
