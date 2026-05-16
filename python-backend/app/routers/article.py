"""文章路由"""

import asyncio
from fastapi import APIRouter, Depends
from databases import Database

from app.database import get_db
from app.schemas.common import BaseResponse, DeleteRequest
from app.schemas.article import (
    ArticleAiModifyOutlineRequest,
    ArticleConfirmOutlineRequest,
    ArticleConfirmTitleRequest,
    ArticleCreateRequest,
    ArticleQueryRequest,
    ArticleVO,
)
from app.schemas.user import LoginUserVO
from app.services.article_service import ArticleService
from app.services.article_async_service import article_async_service
from app.services.agent_log_service import AgentLogService
from app.schemas.statistics import AgentExecutionStatsVO
from app.deps import require_login
from app.managers.sse_manager import sse_emitter_manager
from app.exceptions import ErrorCode, throw_if

router = APIRouter(prefix="/article", tags=["文章管理"])

# 你读函数时，永远按这个顺序：
# 先看函数名
# 再看参数
# 再看函数体里做了哪几件大事
# 最后看返回值

@router.post("/create", response_model=BaseResponse[str])
async def create_article(
    request: ArticleCreateRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
# 你现在脑子里只要翻译成中文：
# - 这是一个 POST /article/create 接口
# - 它叫 create_article
# - 它会接收前端参数 request
# - 它会自动拿到数据库 db
# - 它会自动拿到当前登录用户 current_user


    """创建文章任务"""
    throw_if(
        not request.topic or not request.topic.strip(),
        ErrorCode.PARAMS_ERROR,
        "选题不能为空"
    )
    
    service = ArticleService(db)
# “为什么这里不直接写数据库逻辑，而是 new 一个 service？”
# 答案是：
# “router 负责接请求，service 负责业务处理。”
# 所以这行的人话就是：
# “把后续业务交给 ArticleService 去做。”
# 你现在要开始建立分层意识了。
    
    # 检查并消耗配额 + 创建文章任务（在同一事务中）
    task_id = await service.create_article_task_with_quota_check(
        request.topic,
        current_user,
        request.style,  # 第 5 期新增
        request.enabled_image_methods  # 第 5 期新增
    )
    
    # 异步执行阶段1：生成标题方案
    asyncio.create_task(
        article_async_service.execute_phase1(
            task_id,
            request.topic,
            request.style,
        )
    )
    # “为什么不是 await article_async_service.execute_phase1(...)，而是 create_task(...)？”
    # 答案是：
    # “因为 AI 生成标题比较慢，接口不能一直等着，所以放到后台异步跑。”
    # 这段人话翻译是：
    # “文章任务创建完以后，后台悄悄开始第一阶段：生成标题方案。”
    # 这里你已经能看出设计思路了：
    # 接口先快速返回
    # 真正耗时的 AI 工作放后台
    # 这就是异步任务的意义。

    return BaseResponse.success(data=task_id, message="任务创建成功")
    # 你只问一件事：
    # “这个接口最后返回给前端什么？”
    # 答案是：
    # “返回任务 ID。”
    # 为什么返回 task_id 很重要？
    # 因为前端后面要靠这个 task_id 去：
    # 查文章详情
    # 看生成进度
    # 确认标题
    # 确认大纲
    # 也就是说，task_id 是整条生成流程的主线索。
    # 现在我们把整个函数，完整翻译成人话：
    # 用户调用创建文章接口
    # 后端先检查题目是不是空的
    # 然后创建 ArticleService
    # 用 service 检查用户额度并创建文章任务
    # 拿到 task_id
    # 后台异步启动 phase1，开始生成标题
    # 立刻把 task_id 返回给前端
    # 如果你能把这 7 句说出来，你其实已经读懂这个函数了。

@router.get("/progress/{task_id}")
async def get_progress(
    task_id: str,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """SSE 进度推送"""
    throw_if(
        not task_id or not task_id.strip(),
        ErrorCode.PARAMS_ERROR,
        "任务ID不能为空"
    )
    
    # 校验权限（内部会检查任务是否存在以及用户是否有权限访问）
    service = ArticleService(db)
    await service.get_article_detail(task_id, current_user)
    
    # 创建 SSE Emitter
    return sse_emitter_manager.create_emitter(task_id)


@router.get("/{task_id}", response_model=BaseResponse[ArticleVO])
async def get_article(
    task_id: str,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """获取文章详情"""
    throw_if(
        not task_id or not task_id.strip(),
        ErrorCode.PARAMS_ERROR,
        "任务ID不能为空"
    )
    
    service = ArticleService(db)
    article_vo = await service.get_article_detail(task_id, current_user)
    
    return BaseResponse.success(data=article_vo)


@router.post("/list", response_model=BaseResponse[dict])
async def list_article(
    request: ArticleQueryRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """分页查询文章列表"""
    service = ArticleService(db)
    articles, total = await service.list_article_by_page(request, current_user)
    
    return BaseResponse.success(data={
        "records": articles,
        "total": total,
        "current": request.current,
        "size": request.page_size
    })


@router.post("/delete", response_model=BaseResponse[bool])
async def delete_article(
    request: DeleteRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """删除文章"""
    throw_if(not request.id, ErrorCode.PARAMS_ERROR, "文章ID不能为空")
    
    service = ArticleService(db)
    result = await service.delete_article(request.id, current_user)
    
    return BaseResponse.success(data=result, message="删除成功")


@router.post("/confirm-title", response_model=BaseResponse[None])
async def confirm_title(
    request: ArticleConfirmTitleRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
# 第一次读这个函数，你还是只看 4 件事：
# 它是哪个接口
# 是 POST /article/confirm-title
# 它接收什么
# 接收用户选中的标题、补充描述、当前用户、数据库连接

# 它调用谁
# 先调用 service.confirm_title(...)
# 再启动 execute_phase2(...)
# 它返回什么
# 返回一个成功响应，不直接返回大纲   

# 所以这整个函数的人话就是：
# “用户确认标题后，后端先把用户选中的标题写进数据库，然后后台异步启动第二阶段: 生成大纲。”
    """确认标题并输入补充描述"""
    service = ArticleService(db)
    await service.confirm_title(
        task_id=request.task_id,
        selected_main_title=request.selected_main_title,
        selected_sub_title=request.selected_sub_title,
        user_description=request.user_description,
        login_user=current_user,
    )
    asyncio.create_task(article_async_service.execute_phase2(request.task_id))
    return BaseResponse.success(data=None)
# 这里你要注意一个非常重要的点：

# 用户确认标题，不等于立刻返回大纲。
# 和标题阶段一样，大纲生成也是后台异步跑的。

@router.post("/confirm-outline", response_model=BaseResponse[None])
async def confirm_outline(
    request: ArticleConfirmOutlineRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """确认大纲"""
    service = ArticleService(db)
    await service.confirm_outline(
        task_id=request.task_id,
        outline=request.outline,
        login_user=current_user,
    )
    asyncio.create_task(article_async_service.execute_phase3(request.task_id))
    return BaseResponse.success(data=None)


@router.post("/ai-modify-outline", response_model=BaseResponse[list])
async def ai_modify_outline(
    request: ArticleAiModifyOutlineRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """AI 修改大纲"""
    service = ArticleService(db)
    modified_outline = await service.ai_modify_outline(
        task_id=request.task_id,
        modify_suggestion=request.modify_suggestion,
        login_user=current_user,
    )
    return BaseResponse.success(data=[section.model_dump() for section in modified_outline])


@router.get("/execution-logs/{task_id}", response_model=BaseResponse[AgentExecutionStatsVO])
async def get_execution_logs(
    task_id: str,
    db: Database = Depends(get_db),
):
    """获取任务执行日志"""
    throw_if(not task_id or not task_id.strip(), ErrorCode.PARAMS_ERROR, "任务ID不能为空")
    service = AgentLogService(db)
    stats = await service.get_execution_stats(task_id)
    return BaseResponse.success(data=stats)
