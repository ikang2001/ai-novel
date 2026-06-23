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


class NovelIdeaEnhanceRequest(BaseModel):
    """AI 完善小说核心创意请求"""

    raw_idea: str = Field(..., alias="rawIdea", min_length=5, max_length=3000, description="作者原始创意")
    genre: Optional[str] = Field(None, description="题材")
    target_readers: Optional[str] = Field(None, alias="targetReaders", description="目标读者")
    requirements: Optional[str] = Field(None, max_length=1200, description="额外要求")

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
    chapter_id: Optional[int] = Field(None, alias="chapterId", description="目标章节 ID，不传则默认最新章节")
    author_note: Optional[str] = Field(None, alias="authorNote", description="作者特别交代")

    class Config:
        populate_by_name = True


class ChapterRegenerateRequest(BaseModel):
    """章节重新生成请求"""

    author_note: Optional[str] = Field(None, alias="authorNote", description="作者特别交代")

    class Config:
        populate_by_name = True


class ChapterConfirmRequest(BaseModel):
    """确认章节请求"""

    content: Optional[str] = Field(None, description="修改后的正文（为空则使用生成的内容）")


class ChapterContentUpdateRequest(BaseModel):
    """手动修改章节内容请求"""

    content: str = Field(..., min_length=1, description="修改后的正文")


class ChapterCreateRequest(BaseModel):
    """手动创建章节请求"""

    title: Optional[str] = Field(None, max_length=200, description="章节标题")
    chapter_number: Optional[int] = Field(None, alias="chapterNumber", description="章节号（为空则自动计算）")

    class Config:
        populate_by_name = True


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
    chapter_memo: Optional[Any] = Field(None, alias="chapterMemo")
    content: Optional[str] = None
    summary: Optional[str] = None
    ending_state: Optional[Any] = Field(None, alias="endingState")
    quality_report: Optional[Any] = Field(None, alias="qualityReport")
    word_count: int = Field(0, alias="wordCount")
    character_states: Optional[Any] = Field(None, alias="characterStates")
    context_snapshot_id: Optional[int] = Field(None, alias="contextSnapshotId")
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
    lifecycle_stage: Optional[str] = Field(None, alias="lifecycleStage")
    mention_history: Optional[List[Any]] = Field(None, alias="mentionHistory")
    last_mentioned_chapter: Optional[int] = Field(None, alias="lastMentionedChapter")
    last_action_type: Optional[str] = Field(None, alias="lastActionType")
    last_action_chapter: Optional[int] = Field(None, alias="lastActionChapter")
    last_action_note: Optional[str] = Field(None, alias="lastActionNote")
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
    entry_image: Optional[str] = Field(None, alias="entryImage")
    exit_image: Optional[str] = Field(None, alias="exitImage")
    information_gap: Optional[str] = Field(None, alias="informationGap")
    purpose: Optional[str] = None

    class Config:
        populate_by_name = True


class HookOperation(BaseModel):
    """本章伏笔操作"""

    action: str = Field(..., description="open/advance/resolve/defer/plant")
    foreshadowing_id: Optional[int] = Field(None, alias="foreshadowingId")
    surface: Optional[str] = None
    reason: Optional[str] = None
    expected_payoff: Optional[str] = Field(None, alias="expectedPayoff")

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
    chapter_task: Optional[str] = Field(None, alias="chapterTask")
    reader_expectation: Optional[str] = Field(None, alias="readerExpectation")
    previous_emotional_residue: Optional[str] = Field(None, alias="previousEmotionalResidue")
    required_ending_change: Optional[str] = Field(None, alias="requiredEndingChange")
    hook_operations: Optional[List[HookOperation]] = Field(None, alias="hookOperations")
    prohibitions: Optional[List[str]] = None

    class Config:
        populate_by_name = True


class CharacterMotivationBeat(BaseModel):
    """角色动机链"""

    character: str
    current_interest: Optional[str] = Field(None, alias="currentInterest")
    pressure: Optional[str] = None
    expected_action: Optional[str] = Field(None, alias="expectedAction")
    constraint: Optional[str] = None

    class Config:
        populate_by_name = True


class ChapterMemo(ChapterOutline):
    """章节备忘录，兼容旧章节大纲字段"""

    information_gap: Optional[str] = Field(None, alias="informationGap")
    opening_bridge: Optional[str] = Field(None, alias="openingBridge")
    character_motivations: Optional[List[CharacterMotivationBeat]] = Field(None, alias="characterMotivations")
    payoff_design: Optional[str] = Field(None, alias="payoffDesign")
    scene_craft: Optional[List[str]] = Field(None, alias="sceneCraft")

    class Config:
        populate_by_name = True


class ContextPackage(BaseModel):
    """生成前结构化上下文包"""

    version: str = "v1"
    novel: Dict[str, Any]
    target_chapter: Dict[str, Any] = Field(..., alias="targetChapter")
    stable_memory: Dict[str, Any] = Field(default_factory=dict, alias="stableMemory")
    recent_memory: Dict[str, Any] = Field(default_factory=dict, alias="recentMemory")
    long_term_memory: Dict[str, Any] = Field(default_factory=dict, alias="longTermMemory")
    hook_debt: List[Dict[str, Any]] = Field(default_factory=list, alias="hookDebt")
    chapter_memo: Dict[str, Any] = Field(default_factory=dict, alias="chapterMemo")
    rule_stack: List[str] = Field(default_factory=list, alias="ruleStack")
    trace: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class EndingState(BaseModel):
    """章节结尾状态"""

    final_image: Optional[str] = Field(None, alias="finalImage")
    location: Optional[str] = None
    emotional_residue: Optional[str] = Field(None, alias="emotionalResidue")
    open_conflict: Optional[str] = Field(None, alias="openConflict")
    reader_expectation: Optional[str] = Field(None, alias="readerExpectation")
    character_states: Optional[List[Dict[str, Any]]] = Field(None, alias="characterStates")

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
    ending_state: Optional[Dict[str, Any]] = Field(None, alias="endingState")
    reader_expectation: Optional[str] = Field(None, alias="readerExpectation")
    style_memory_updates: Optional[List[str]] = Field(None, alias="styleMemoryUpdates")

    class Config:
        populate_by_name = True


class ConsistencyIssue(BaseModel):
    """连贯性问题"""

    type: str = Field(..., description="问题类型：character_inconsistency/timeline_error/forgotten_foreshadowing/plot_hole/setting_violation")
    severity: str = Field(..., description="严重程度：high/medium/low")
    description: str
    chapters: Optional[List[int]] = None
    suggestion: Optional[str] = None
    paragraph_index: Optional[int] = Field(None, alias="paragraphIndex")
    evidence_text: Optional[str] = Field(None, alias="evidenceText")
    start_offset: Optional[int] = Field(None, alias="startOffset")
    end_offset: Optional[int] = Field(None, alias="endOffset")

    class Config:
        populate_by_name = True


class ConsistencyReport(BaseModel):
    """连贯性检查报告"""

    issues: List[ConsistencyIssue]
    summary: str


class DraftAuditReport(BaseModel):
    """单章草稿审稿报告"""

    issues: List[ConsistencyIssue] = Field(default_factory=list)
    summary: str = ""
    should_revise: bool = Field(False, alias="shouldRevise")
    revision_brief: Optional[str] = Field(None, alias="revisionBrief")

    class Config:
        populate_by_name = True


class TaskEventVO(BaseModel):
    """任务事件"""

    type: str
    data: Optional[Any] = None


class TaskStatusVO(BaseModel):
    """任务状态"""

    task_id: str = Field(..., alias="taskId")
    task_type: str = Field(..., alias="taskType")
    status: str
    novel_id: Optional[int] = Field(None, alias="novelId")
    chapter_id: Optional[int] = Field(None, alias="chapterId")
    chapter_number: Optional[int] = Field(None, alias="chapterNumber")
    phase: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    events: List[TaskEventVO] = Field(default_factory=list)

    class Config:
        populate_by_name = True
