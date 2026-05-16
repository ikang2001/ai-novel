"""小说相关枚举类型定义"""

from enum import Enum
from typing import Optional, Set


class NovelStatusEnum(str, Enum):
    """小说状态枚举"""

    ONGOING = "ongoing"
    COMPLETED = "completed"
    PAUSED = "paused"


class NovelGenreEnum(str, Enum):
    """小说题材枚举"""

    XUANHUAN = "xuanhuan"       # 玄幻
    DUSHI = "dushi"             # 都市
    XUANYI = "xuanyi"           # 悬疑
    KEHUAN = "kehuang"          # 科幻
    YANQING = "yanqing"         # 言情
    LISHI = "lishi"             # 历史
    QITA = "qita"               # 其他

    @classmethod
    def is_valid(cls, value: Optional[str]) -> bool:
        """校验是否为有效的题材值"""
        if not value:
            return False
        return value in [e.value for e in cls]


class TargetReadersEnum(str, Enum):
    """目标读者枚举"""

    MALE = "male"               # 男频
    FEMALE = "female"           # 女频
    GENERAL = "general"         # 通用


class NovelPhaseEnum(str, Enum):
    """小说阶段枚举"""

    PENDING = "PENDING"
    SETTING = "SETTING"                     # 开书设定中
    STYLE_ANALYZING = "STYLE_ANALYZING"     # 风格分析中
    READY = "READY"                         # 就绪（可开始写章节）
    CHAPTER_PLANNING = "CHAPTER_PLANNING"   # 章节大纲规划中
    CHAPTER_GENERATING = "CHAPTER_GENERATING"  # 章节生成中
    ARCHIVING = "ARCHIVING"                 # 归档中
    REVIEWING = "REVIEWING"                 # 连贯性检查中

    def can_transition_to(self, target_phase: "NovelPhaseEnum") -> bool:
        """校验是否可流转到目标阶段"""
        transitions = {
            NovelPhaseEnum.PENDING: {NovelPhaseEnum.SETTING},
            NovelPhaseEnum.SETTING: {NovelPhaseEnum.STYLE_ANALYZING, NovelPhaseEnum.READY},
            NovelPhaseEnum.STYLE_ANALYZING: {NovelPhaseEnum.READY},
            NovelPhaseEnum.READY: {NovelPhaseEnum.CHAPTER_PLANNING, NovelPhaseEnum.REVIEWING},
            NovelPhaseEnum.CHAPTER_PLANNING: {NovelPhaseEnum.CHAPTER_GENERATING, NovelPhaseEnum.READY},
            NovelPhaseEnum.CHAPTER_GENERATING: {NovelPhaseEnum.ARCHIVING, NovelPhaseEnum.READY},
            NovelPhaseEnum.ARCHIVING: {NovelPhaseEnum.READY},
            NovelPhaseEnum.REVIEWING: {NovelPhaseEnum.READY},
        }
        return target_phase in transitions.get(self, set())


class ChapterStatusEnum(str, Enum):
    """章节状态枚举"""

    DRAFT = "draft"             # 草稿（生成中或刚生成）
    CONFIRMED = "confirmed"     # 已确认（作者审阅通过）
    REVISED = "revised"         # 已修订（确认后又修改过）


class CharacterRoleTypeEnum(str, Enum):
    """角色类型枚举"""

    PROTAGONIST = "protagonist"     # 主角
    SUPPORTING = "supporting"       # 配角
    ANTAGONIST = "antagonist"       # 反派
    MINOR = "minor"                 # 龙套

    @classmethod
    def get_core_types(cls) -> Set["CharacterRoleTypeEnum"]:
        """获取核心角色类型（始终注入上下文）"""
        return {cls.PROTAGONIST, cls.SUPPORTING, cls.ANTAGONIST}


class ForeshadowingStatusEnum(str, Enum):
    """伏笔状态枚举"""

    ACTIVE = "active"           # 活跃（未解决）
    RESOLVED = "resolved"       # 已揭示
    ABANDONED = "abandoned"     # 已放弃


class ForeshadowingCategoryEnum(str, Enum):
    """伏笔类型枚举"""

    CHARACTER = "character"     # 角色相关
    PLOT = "plot"               # 剧情相关
    SETTING = "setting"         # 设定相关
    EMOTION = "emotion"         # 情感相关


class NovelSseMessageTypeEnum(str, Enum):
    """小说 SSE 消息类型枚举"""

    # 设定生成
    SETTING_GENERATING = "SETTING_GENERATING"
    SETTING_GENERATED = "SETTING_GENERATED"

    # 风格分析
    STYLE_ANALYZING = "STYLE_ANALYZING"
    STYLE_ANALYZED = "STYLE_ANALYZED"

    # 大纲生成
    OUTLINE_GENERATING = "OUTLINE_GENERATING"
    OUTLINE_GENERATED = "OUTLINE_GENERATED"

    # 章节生成（流式）
    CHAPTER_GENERATING = "CHAPTER_GENERATING"
    CHAPTER_STREAMING = "CHAPTER_STREAMING"
    CHAPTER_GENERATED = "CHAPTER_GENERATED"

    # 归档
    ARCHIVING = "ARCHIVING"
    ARCHIVE_COMPLETE = "ARCHIVE_COMPLETE"

    # 连贯性检查
    CONSISTENCY_CHECKING = "CONSISTENCY_CHECKING"
    CONSISTENCY_RESULT = "CONSISTENCY_RESULT"

    # 伏笔提醒
    FORESHADOWING_ALERT = "FORESHADOWING_ALERT"

    # 错误
    ERROR = "ERROR"

    # 全部完成
    ALL_COMPLETE = "ALL_COMPLETE"

    def get_streaming_prefix(self) -> str:
        """获取流式输出消息前缀"""
        return f"{self.value}:"
