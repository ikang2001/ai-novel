"""小说相关路由"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from databases import Database

from app.database import get_db
from app.deps import require_login
from app.exceptions import ErrorCode, throw_if, throw_if_not
from app.managers.sse_manager import sse_emitter_manager
from app.models.novel_enums import ChapterStatusEnum, NovelGenreEnum
from app.schemas.common import BaseResponse
from app.schemas.novel import (
    NovelCreateRequest, NovelIdeaEnhanceRequest, NovelSettingUpdateRequest, StyleAnalyzeRequest,
    ChapterPlanRequest, ChapterGenerateRequest, ChapterRegenerateRequest, ChapterConfirmRequest,
    ChapterContentUpdateRequest, ChapterCreateRequest,
    CharacterCreateRequest, CharacterUpdateRequest,
    ForeshadowingCreateRequest, ForeshadowingUpdateRequest,
    TaskStatusVO,
)
from app.schemas.user import LoginUserVO
from app.services.novel_service import NovelService
from app.services.character_service import CharacterService
from app.services.foreshadowing_service import ForeshadowingService
from app.services.context_builder import ContextBuilder
from app.services.novel_agent_service import NovelAgentService
from app.services.novel_async_service import NovelAsyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/novel", tags=["小说"])


def _get_services(db: Database = Depends(get_db)):
    """依赖注入：创建所有服务实例"""
    novel_service = NovelService(db)
    character_service = CharacterService(db)
    foreshadowing_service = ForeshadowingService(db)
    context_builder = ContextBuilder(novel_service, character_service, foreshadowing_service)
    agent_service = NovelAgentService(novel_service, character_service, foreshadowing_service, context_builder)
    async_service = NovelAsyncService(novel_service, agent_service, character_service)
    return {
        "novel_service": novel_service,
        "character_service": character_service,
        "foreshadowing_service": foreshadowing_service,
        "agent_service": agent_service,
        "async_service": async_service,
    }


def _check_novel_permission(novel: dict, current_user: LoginUserVO):
    """检查小说访问权限"""
    throw_if_not(novel, ErrorCode.NOT_FOUND_ERROR, "小说不存在")
    throw_if(
        novel["userId"] != current_user.id and current_user.user_role != "admin",
        ErrorCode.NO_AUTH_ERROR, "无权限访问"
    )


async def _get_chapter_with_permission(chapter_id: int, current_user: LoginUserVO, services: dict) -> dict:
    chapter = await services["novel_service"].get_chapter(chapter_id)
    throw_if_not(chapter, ErrorCode.NOT_FOUND_ERROR, "章节不存在")
    novel = await services["novel_service"].get_novel(chapter["novelId"])
    _check_novel_permission(novel, current_user)
    return chapter


async def _get_character_with_permission(character_id: int, current_user: LoginUserVO, services: dict) -> dict:
    char = await services["character_service"].get_character(character_id)
    throw_if_not(char, ErrorCode.NOT_FOUND_ERROR, "角色不存在")
    novel = await services["novel_service"].get_novel(char["novelId"])
    _check_novel_permission(novel, current_user)
    return char


async def _get_foreshadowing_with_permission(foreshadowing_id: int, current_user: LoginUserVO, services: dict) -> dict:
    foreshadowing = await services["foreshadowing_service"].get_foreshadowing(foreshadowing_id)
    throw_if_not(foreshadowing, ErrorCode.NOT_FOUND_ERROR, "伏笔不存在")
    novel = await services["novel_service"].get_novel(foreshadowing["novelId"])
    _check_novel_permission(novel, current_user)
    return foreshadowing


# ========== 小说管理 ==========


@router.post("/create", response_model=BaseResponse[dict])
async def create_novel(request: NovelCreateRequest,
                       current_user: LoginUserVO = Depends(require_login),
                       services: dict = Depends(_get_services)):
    """创建小说（阶段1：开书设定）"""
    throw_if(not request.title or not request.title.strip(), ErrorCode.PARAMS_ERROR, "书名不能为空")
    throw_if(not NovelGenreEnum.is_valid(request.genre), ErrorCode.PARAMS_ERROR, "无效的题材")

    novel_service = services["novel_service"]
    async_service = services["async_service"]

    # 创建小说记录
    novel_id = await novel_service.create_novel(
        user_id=current_user.id,
        title=request.title.strip(),
        genre=request.genre,
        target_readers=request.target_readers,
        target_word_count=request.target_word_count,
    )

    # 异步启动设定生成，立即返回 task_id
    task_id = await async_service.start_setting_generation(
        novel_id=novel_id,
        title=request.title.strip(),
        genre=request.genre,
        target_readers=request.target_readers,
        core_idea=request.core_idea,
        initial_characters=request.initial_characters,
    )

    return {"code": 0, "data": {"novelId": novel_id, "taskId": task_id}, "message": "ok"}


@router.post("/idea/enhance", response_model=BaseResponse[dict])
async def enhance_novel_idea(request: NovelIdeaEnhanceRequest,
                             current_user: LoginUserVO = Depends(require_login),
                             services: dict = Depends(_get_services)):
    """AI 完善小说核心创意，不创建小说记录。"""
    raw_idea = request.raw_idea.strip()
    throw_if(len(raw_idea) < 5, ErrorCode.PARAMS_ERROR, "请先输入你的小说创意")
    result = await services["agent_service"].agent0_enhance_core_idea(
        raw_idea=raw_idea,
        genre=request.genre,
        target_readers=request.target_readers,
        requirements=request.requirements,
    )
    return {"code": 0, "data": result, "message": "ok"}


@router.get("/list", response_model=BaseResponse[dict])
async def get_novel_list(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, alias="pageSize", description="每页数量"),
    current_user: LoginUserVO = Depends(require_login),
    services: dict = Depends(_get_services),
):
    """获取小说列表"""
    result = await services["novel_service"].get_novel_list(current_user.id, page, page_size)
    return {"code": 0, "data": result, "message": "ok"}


@router.get("/{novel_id}", response_model=BaseResponse[dict])
async def get_novel(novel_id: int,
                    current_user: LoginUserVO = Depends(require_login),
                    services: dict = Depends(_get_services)):
    """获取小说详情"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)

    # 自动修正统计：检查实际章节数与 novel 表记录是否一致
    actual = await services["novel_service"]._fetch_one(
        """SELECT COUNT(*) AS chapter_count,
                  COALESCE(SUM(wordCount), 0) AS total_wc
           FROM chapter WHERE novelId = :novelId AND isDelete = 0""",
        {"novelId": novel_id},
    )
    if (actual["chapter_count"] != novel.get("currentChapterNumber", 0) or
            actual["total_wc"] != novel.get("totalWordCount", 0)):
        await services["novel_service"].recalculate_novel_stats(novel_id)
        novel = await services["novel_service"].get_novel(novel_id)

    return {"code": 0, "data": novel, "message": "ok"}


@router.put("/{novel_id}/setting", response_model=BaseResponse[dict])
async def update_novel_setting(novel_id: int, request: NovelSettingUpdateRequest,
                               current_user: LoginUserVO = Depends(require_login),
                               services: dict = Depends(_get_services)):
    """修改小说设定"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    await services["novel_service"].update_novel_setting(
        novel_id,
        world_setting=request.world_setting,
        volume_outline=request.volume_outline,
        style_guide=request.style_guide,
    )
    return {"code": 0, "data": None, "message": "ok"}


@router.delete("/{novel_id}", response_model=BaseResponse[bool])
async def delete_novel(novel_id: int,
                       current_user: LoginUserVO = Depends(require_login),
                       services: dict = Depends(_get_services)):
    """删除小说"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    await services["novel_service"].delete_novel(novel_id)
    return {"code": 0, "data": True, "message": "ok"}


# ========== 风格管理 ==========


@router.post("/{novel_id}/style/analyze", response_model=BaseResponse[dict])
async def analyze_style(novel_id: int, request: StyleAnalyzeRequest,
                        current_user: LoginUserVO = Depends(require_login),
                        services: dict = Depends(_get_services)):
    """风格分析（阶段2）"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    result = await services["async_service"].analyze_style_sync(novel_id, request.samples)
    return {"code": 0, "data": result, "message": "ok"}


@router.put("/{novel_id}/style", response_model=BaseResponse[bool])
async def update_style(novel_id: int, request: dict,
                       current_user: LoginUserVO = Depends(require_login),
                       services: dict = Depends(_get_services)):
    """手动修改风格指南"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    await services["novel_service"].update_novel_setting(novel_id, style_guide=request)
    return {"code": 0, "data": True, "message": "ok"}


# ========== 角色管理 ==========


@router.get("/{novel_id}/characters", response_model=BaseResponse[list])
async def get_characters(novel_id: int,
                         current_user: LoginUserVO = Depends(require_login),
                         services: dict = Depends(_get_services)):
    """获取角色列表"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    characters = await services["character_service"].get_all_characters(novel_id)
    return {"code": 0, "data": characters, "message": "ok"}


@router.post("/{novel_id}/characters", response_model=BaseResponse[int])
async def create_character(novel_id: int, request: CharacterCreateRequest,
                           current_user: LoginUserVO = Depends(require_login),
                           services: dict = Depends(_get_services)):
    """创建角色"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    char_id = await services["character_service"].create_character(
        novel_id=novel_id, name=request.name, role_type=request.role_type,
        is_core=request.is_core or False, aliases=request.aliases,
        appearance=request.appearance, personality=request.personality,
        background=request.background, skills=request.skills,
        speech_style=request.speech_style,
    )
    return {"code": 0, "data": char_id, "message": "ok"}


@router.put("/character/{character_id}", response_model=BaseResponse[bool])
async def update_character(character_id: int, request: CharacterUpdateRequest,
                           current_user: LoginUserVO = Depends(require_login),
                           services: dict = Depends(_get_services)):
    """修改角色"""
    await _get_character_with_permission(character_id, current_user, services)
    await services["character_service"].update_character(
        character_id, **request.model_dump(exclude_none=True)
    )
    return {"code": 0, "data": True, "message": "ok"}


@router.delete("/character/{character_id}", response_model=BaseResponse[bool])
async def delete_character(character_id: int,
                           current_user: LoginUserVO = Depends(require_login),
                           services: dict = Depends(_get_services)):
    """删除角色"""
    await _get_character_with_permission(character_id, current_user, services)
    await services["character_service"].delete_character(character_id)
    return {"code": 0, "data": True, "message": "ok"}


# ========== 伏笔管理 ==========


@router.get("/{novel_id}/foreshadowing", response_model=BaseResponse[list])
async def get_foreshadowing(novel_id: int, status: Optional[str] = None,
                            current_user: LoginUserVO = Depends(require_login),
                            services: dict = Depends(_get_services)):
    """获取伏笔列表"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    fs_list = await services["foreshadowing_service"].get_all_foreshadowing(novel_id, status)
    return {"code": 0, "data": fs_list, "message": "ok"}


@router.post("/{novel_id}/foreshadowing", response_model=BaseResponse[int])
async def create_foreshadowing(novel_id: int, request: ForeshadowingCreateRequest,
                               current_user: LoginUserVO = Depends(require_login),
                               services: dict = Depends(_get_services)):
    """创建伏笔"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    fs_id = await services["foreshadowing_service"].create_foreshadowing(
        novel_id=novel_id, surface=request.surface,
        hidden_truth=request.hidden_truth, category=request.category,
        related_characters=request.related_characters, keywords=request.keywords,
        target_chapter=request.target_chapter, importance=request.importance,
    )
    return {"code": 0, "data": fs_id, "message": "ok"}


@router.put("/foreshadowing/{foreshadowing_id}", response_model=BaseResponse[bool])
async def update_foreshadowing(foreshadowing_id: int, request: ForeshadowingUpdateRequest,
                               current_user: LoginUserVO = Depends(require_login),
                               services: dict = Depends(_get_services)):
    """修改伏笔"""
    await _get_foreshadowing_with_permission(foreshadowing_id, current_user, services)
    await services["foreshadowing_service"].update_foreshadowing(
        foreshadowing_id, **request.model_dump(exclude_none=True)
    )
    return {"code": 0, "data": True, "message": "ok"}


@router.put("/foreshadowing/{foreshadowing_id}/resolve", response_model=BaseResponse[bool])
async def resolve_foreshadowing(foreshadowing_id: int,
                                current_user: LoginUserVO = Depends(require_login),
                                services: dict = Depends(_get_services)):
    """标记伏笔为已揭示"""
    await _get_foreshadowing_with_permission(foreshadowing_id, current_user, services)
    await services["foreshadowing_service"].resolve_foreshadowing(foreshadowing_id, chapter_id=None)
    return {"code": 0, "data": True, "message": "ok"}


@router.put("/foreshadowing/{foreshadowing_id}/abandon", response_model=BaseResponse[bool])
async def abandon_foreshadowing(foreshadowing_id: int,
                                current_user: LoginUserVO = Depends(require_login),
                                services: dict = Depends(_get_services)):
    """标记伏笔为已放弃"""
    await _get_foreshadowing_with_permission(foreshadowing_id, current_user, services)
    await services["foreshadowing_service"].abandon_foreshadowing(foreshadowing_id)
    return {"code": 0, "data": True, "message": "ok"}


# ========== 章节操作（核心） ==========


@router.post("/{novel_id}/chapter/plan", response_model=BaseResponse[dict])
async def plan_chapter(novel_id: int, request: ChapterPlanRequest,
                       current_user: LoginUserVO = Depends(require_login),
                       services: dict = Depends(_get_services)):
    """规划章节大纲（阶段3）"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    result = await services["async_service"].plan_outline_sync(novel_id, request.author_intent)
    return {"code": 0, "data": result, "message": "ok"}


@router.post("/{novel_id}/chapter/create", response_model=BaseResponse[dict])
async def create_chapter_manual(novel_id: int, request: ChapterCreateRequest,
                                current_user: LoginUserVO = Depends(require_login),
                                services: dict = Depends(_get_services)):
    """手动创建空白章节"""
    novel = await services["novel_service"].get_novel(novel_id)
    throw_if_not(novel, ErrorCode.NOT_FOUND_ERROR, "小说不存在")
    _check_novel_permission(novel, current_user)

    chapter_number = request.chapter_number or await services["novel_service"].get_next_chapter_number(novel_id)
    chapter_id = await services["novel_service"].create_chapter(
        novel_id=novel_id,
        volume_number=novel.get("currentVolumeNumber", 1),
        chapter_number=chapter_number,
        title=request.title or f"第{chapter_number}章",
    )
    await services["novel_service"].recalculate_novel_stats(novel_id)
    return {"code": 0, "data": {"chapterId": chapter_id, "chapterNumber": chapter_number}, "message": "ok"}


@router.post("/{novel_id}/chapter/generate", response_model=BaseResponse[dict])
async def generate_chapter(novel_id: int, request: ChapterGenerateRequest,
                           current_user: LoginUserVO = Depends(require_login),
                           services: dict = Depends(_get_services)):
    """生成章节内容（阶段4，返回 task_id 用于 SSE）"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)

    target_chapter = None
    if request.chapter_id:
        target_chapter = await services["novel_service"].get_chapter(request.chapter_id)
        throw_if_not(target_chapter, ErrorCode.NOT_FOUND_ERROR, "章节不存在")
        throw_if(target_chapter.get("novelId") != novel_id, ErrorCode.NO_AUTH_ERROR, "章节不属于当前小说")
    else:
        target_chapter = await services["novel_service"].get_latest_chapter(novel_id)

    throw_if_not(target_chapter, ErrorCode.PARAMS_ERROR, "请先规划章节大纲")
    throw_if(
        target_chapter.get("status") not in {ChapterStatusEnum.DRAFT.value, ChapterStatusEnum.FAILED.value},
        ErrorCode.OPERATION_ERROR,
        "当前章节状态不允许生成",
    )

    # 更新大纲（如果用户修改了）
    outline_text = json.dumps(request.outline, ensure_ascii=False) if request.outline else "{}"
    await services["novel_service"].update_chapter_outline(target_chapter["id"], request.outline)
    await services["novel_service"].update_chapter_memo(target_chapter["id"], request.outline or {})

    # 启动异步生成
    task_id = await services["async_service"].start_chapter_generation(
        novel_id=novel_id,
        chapter_id=target_chapter["id"],
        chapter_number=target_chapter["chapterNumber"],
        chapter_outline=outline_text,
        author_note=request.author_note,
        allowed_current_statuses=[ChapterStatusEnum.DRAFT.value, ChapterStatusEnum.FAILED.value],
    )

    return {"code": 0, "data": {"taskId": task_id, "chapterId": target_chapter["id"]}, "message": "ok"}


@router.put("/chapter/{chapter_id}/confirm", response_model=BaseResponse[dict])
async def confirm_chapter(chapter_id: int, request: ChapterConfirmRequest,
                          current_user: LoginUserVO = Depends(require_login),
                          services: dict = Depends(_get_services)):
    """确认章节（阶段5，触发归档）"""
    chapter = await _get_chapter_with_permission(chapter_id, current_user, services)
    throw_if(
        chapter.get("status") not in {ChapterStatusEnum.DRAFT.value, ChapterStatusEnum.REVISED.value, ChapterStatusEnum.FAILED.value},
        ErrorCode.OPERATION_ERROR,
        "当前章节状态不允许确认",
    )

    # 如果用户修改了内容，先更新
    if request.content:
        word_count = len(request.content)
        await services["novel_service"].update_chapter_content(chapter_id, request.content, word_count)

    # 获取章节内容
    chapter = await services["novel_service"].get_chapter(chapter_id)
    content = chapter.get("content", "")
    throw_if(not content, ErrorCode.OPERATION_ERROR, "章节内容为空")

    # 启动异步归档
    task_id = await services["async_service"].start_archive(
        novel_id=chapter["novelId"],
        chapter_id=chapter_id,
        chapter_number=chapter["chapterNumber"],
        chapter_content=content,
        allowed_current_statuses=[
            ChapterStatusEnum.DRAFT.value,
            ChapterStatusEnum.REVISED.value,
            ChapterStatusEnum.FAILED.value,
        ],
    )

    return {"code": 0, "data": {"taskId": task_id, "chapterId": chapter_id}, "message": "ok"}


@router.put("/chapter/{chapter_id}/regenerate", response_model=BaseResponse[dict])
async def regenerate_chapter(chapter_id: int,
                             request: Optional[ChapterRegenerateRequest] = None,
                             current_user: LoginUserVO = Depends(require_login),
                             services: dict = Depends(_get_services)):
    """重新生成章节"""
    chapter = await _get_chapter_with_permission(chapter_id, current_user, services)
    throw_if(
        chapter.get("status") not in {
            ChapterStatusEnum.DRAFT.value,
            ChapterStatusEnum.REVISED.value,
            ChapterStatusEnum.FAILED.value,
        },
        ErrorCode.OPERATION_ERROR,
        "当前章节状态不允许重新生成",
    )

    outline = chapter.get("outline", "{}")
    task_id = await services["async_service"].start_chapter_generation(
        novel_id=chapter["novelId"],
        chapter_id=chapter_id,
        chapter_number=chapter["chapterNumber"],
        chapter_outline=outline,
        author_note=request.author_note if request else None,
        allowed_current_statuses=[
            ChapterStatusEnum.DRAFT.value,
            ChapterStatusEnum.REVISED.value,
            ChapterStatusEnum.FAILED.value,
        ],
    )
    return {"code": 0, "data": {"taskId": task_id, "chapterId": chapter_id}, "message": "ok"}


@router.put("/chapter/{chapter_id}/content", response_model=BaseResponse[bool])
async def update_chapter_content(chapter_id: int, request: ChapterContentUpdateRequest,
                                 current_user: LoginUserVO = Depends(require_login),
                                 services: dict = Depends(_get_services)):
    """手动修改章节内容"""
    chapter = await _get_chapter_with_permission(chapter_id, current_user, services)
    throw_if(
        chapter.get("status") in {ChapterStatusEnum.GENERATING.value, ChapterStatusEnum.ARCHIVING.value},
        ErrorCode.OPERATION_ERROR,
        "处理中章节暂不能编辑",
    )
    word_count = len(request.content)
    await services["novel_service"].update_chapter_content(chapter_id, request.content, word_count)
    await services["novel_service"].update_chapter_status(chapter_id, ChapterStatusEnum.REVISED.value)
    await services["novel_service"].recalculate_novel_stats(chapter["novelId"])
    return {"code": 0, "data": True, "message": "ok"}


@router.delete("/chapter/{chapter_id}", response_model=BaseResponse[bool])
async def delete_chapter(chapter_id: int,
                         current_user: LoginUserVO = Depends(require_login),
                         services: dict = Depends(_get_services)):
    """删除章节"""
    chapter = await _get_chapter_with_permission(chapter_id, current_user, services)
    throw_if(
        chapter.get("status") in {ChapterStatusEnum.GENERATING.value, ChapterStatusEnum.ARCHIVING.value},
        ErrorCode.OPERATION_ERROR,
        "处理中章节不能删除",
    )

    await services["novel_service"].delete_chapter(chapter_id)
    await services["novel_service"].recalculate_novel_stats(chapter["novelId"])
    return {"code": 0, "data": True, "message": "ok"}


@router.put("/chapter/{chapter_id}/title", response_model=BaseResponse[bool])
async def update_chapter_title(chapter_id: int,
                               request: dict,
                               current_user: LoginUserVO = Depends(require_login),
                               services: dict = Depends(_get_services)):
    """修改章节标题"""
    chapter = await _get_chapter_with_permission(chapter_id, current_user, services)
    throw_if(
        chapter.get("status") in {ChapterStatusEnum.GENERATING.value, ChapterStatusEnum.ARCHIVING.value},
        ErrorCode.OPERATION_ERROR,
        "处理中章节暂不能改名",
    )

    title = request.get("title", "").strip()
    throw_if(not title, ErrorCode.PARAMS_ERROR, "标题不能为空")

    await services["novel_service"].update_chapter_title(chapter_id, title)
    return {"code": 0, "data": True, "message": "ok"}


@router.get("/{novel_id}/chapters", response_model=BaseResponse[list])
async def get_chapters(novel_id: int,
                       current_user: LoginUserVO = Depends(require_login),
                       services: dict = Depends(_get_services)):
    """获取章节列表"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    chapters = await services["novel_service"].get_chapters_by_novel(novel_id)
    return {"code": 0, "data": chapters, "message": "ok"}


@router.get("/chapter/{chapter_id}", response_model=BaseResponse[dict])
async def get_chapter(chapter_id: int,
                      current_user: LoginUserVO = Depends(require_login),
                      services: dict = Depends(_get_services)):
    """获取章节详情"""
    chapter = await _get_chapter_with_permission(chapter_id, current_user, services)
    return {"code": 0, "data": chapter, "message": "ok"}


@router.get("/chapter/{chapter_id}/context-snapshot", response_model=BaseResponse[dict])
async def get_chapter_context_snapshot(chapter_id: int,
                                       current_user: LoginUserVO = Depends(require_login),
                                       services: dict = Depends(_get_services)):
    """读取章节最近一次上下文快照。"""
    await _get_chapter_with_permission(chapter_id, current_user, services)
    snapshot = await services["novel_service"].get_context_snapshot_by_chapter(chapter_id)
    return {"code": 0, "data": snapshot or {}, "message": "ok"}


@router.get("/chapter/{chapter_id}/versions", response_model=BaseResponse[list])
async def get_chapter_versions(chapter_id: int,
                               include_content: bool = Query(False, alias="includeContent"),
                               current_user: LoginUserVO = Depends(require_login),
                               services: dict = Depends(_get_services)):
    """读取章节版本记录。"""
    await _get_chapter_with_permission(chapter_id, current_user, services)
    versions = await services["novel_service"].get_chapter_versions(chapter_id, include_content=include_content)
    return {"code": 0, "data": versions, "message": "ok"}


# ========== 审查与导出 ==========


@router.post("/{novel_id}/consistency", response_model=BaseResponse[dict])
async def check_consistency(novel_id: int,
                            current_user: LoginUserVO = Depends(require_login),
                            services: dict = Depends(_get_services)):
    """连贯性检查（阶段6）"""
    novel = await services["novel_service"].get_novel(novel_id)
    _check_novel_permission(novel, current_user)
    try:
        result = await services["async_service"].review_sync(novel_id)
    except ValueError as e:
        throw_if(True, ErrorCode.NOT_FOUND_ERROR, str(e))
    except Exception as e:
        logger.error("连贯性检查失败: %s", e)
        throw_if(True, ErrorCode.SYSTEM_ERROR, f"连贯性检查失败: {str(e)}")
    return {"code": 0, "data": result, "message": "ok"}


@router.get("/{novel_id}/export")
async def export_novel(novel_id: int, format: str = "docx",
                       current_user: LoginUserVO = Depends(require_login),
                       services: dict = Depends(_get_services)):
    """导出小说"""
    # TODO: 实现 DOCX/EPUB 导出（需要 export_service）
    return {"code": 50000, "data": None, "message": "导出功能暂未实现"}


@router.get("/task/{task_id}", response_model=BaseResponse[TaskStatusVO])
async def get_task_status(task_id: str,
                          current_user: LoginUserVO = Depends(require_login),
                          services: dict = Depends(_get_services)):
    """获取任务状态和已缓存事件。"""
    try:
        task = await services["async_service"].get_task_status(task_id)
    except ValueError as error:
        throw_if(True, ErrorCode.NOT_FOUND_ERROR, str(error))
    novel_id = task.get("novelId")
    if novel_id:
        novel = await services["novel_service"].get_novel(novel_id)
        _check_novel_permission(novel, current_user)
    return {"code": 0, "data": task, "message": "ok"}


# ========== SSE 进度流 ==========


@router.get("/progress/{task_id}")
async def progress_stream(task_id: str,
                          current_user: LoginUserVO = Depends(require_login),
                          services: dict = Depends(_get_services)):
    """SSE 进度流

    复用现有 sse_emitter_manager 的模式。
    前端通过 EventSource 连接这个接口，实时接收进度消息。
    """
    task = await services["async_service"].get_task_status(task_id)
    novel_id = task.get("novelId")
    if novel_id:
        novel = await services["novel_service"].get_novel(novel_id)
        _check_novel_permission(novel, current_user)
    return sse_emitter_manager.create_emitter(task_id, redis_backed=True)
