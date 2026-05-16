# AI 爆款文章创作器 - 后端学习方案

> 目标：10 天内掌握本项目后端核心技术，胜任面试

---

## 项目技术栈速览

| 层级 | 技术 |
|------|------|
| 框架 | FastAPI + Uvicorn |
| 数据库 | MySQL + SQLAlchemy + databases |
| 缓存 | Redis (Session 存储) |
| AI | 通义千问 (DashScope API) |
| 认证 | Cookie + Redis Session |
| 支付 | Stripe |

---

## 学习日程总览

| 天数 | 主题 | 核心技能 | 面试重点 |
|------|------|----------|----------|
| Day 1 | FastAPI 基础 | 路由、依赖注入、请求/响应模型 | ★★★ |
| Day 2 | 异步编程 | async/await、并发、异步数据库 | ★★★ |
| Day 3 | 数据库操作 | SQLAlchemy ORM、事务、databases 异步库 | ★★★ |
| Day 4 | Redis 实战 | Session 管理、缓存、异步 Redis | ★★ |
| Day 5 | 多智能体架构 | 设计模式、状态流转、SSE 流式推送 | ★★★ |
| Day 6 | 图片服务 | 策略模式、工厂模式、图片上传 COS | ★★ |
| Day 7 | 认证鉴权 | 中间件、Cookie、权限控制 | ★★ |
| Day 8 | 支付集成 | Stripe Webhook、异步回调处理 | ★ |
| Day 9 | 项目部署 | Docker、环境配置、生产环境优化 | ★ |
| Day 10 | 面试冲刺 | 架构设计、问题复盘、亮点提炼 | ★★★ |

---

## Day 1：FastAPI 基础

### 学习目标
- 理解 FastAPI 核心概念
- 掌握路由定义和请求处理
- 学会使用 Pydantic 定义数据模型

### 必读代码

#### 1.1 应用入口 (`app/main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 1. 生命周期管理（启动/关闭时执行）
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await init_redis()
    yield  # yield 之前是启动时，之后是关闭时
    await database.disconnect()
    await close_redis()

# 2. 创建 FastAPI 应用
app = FastAPI(
    title="AI 爆款文章创作器",
    version="0.0.1",
    lifespan=lifespan  # 注入生命周期
)

# 3. CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 全局异常处理
@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200,  # 注意：业务异常返回 200，前端通过 code 判断
        content={
            "code": exc.error_code.code,
            "data": None,
            "message": exc.message
        }
    )

# 5. 注册路由
app.include_router(health_router, prefix="/api")
app.include_router(user_router, prefix="/api")
```

**面试知识点：**
- `lifespan` 上下文管理器的执行时机
- 为什么业务异常返回 `status_code=200` 而不是 4xx？
- CORS 中 `allow_credentials=True` 时 `allow_origins` 不能用 `*`

#### 1.2 路由定义 (`app/routers/user.py`)

```python
from fastapi import APIRouter, Depends, Response, Cookie
from databases import Database
from app.database import get_db
from app.deps import require_login, require_admin

router = APIRouter(prefix="/user", tags=["用户管理"])

# GET 请求
@router.get("/get/login", response_model=BaseResponse[LoginUserVO])
async def get_login_user(current_user: LoginUserVO = Depends(require_login)):
    return BaseResponse.success(data=current_user)

# POST 请求
@router.post("/login", response_model=BaseResponse[LoginUserVO])
async def login(
    request: UserLoginRequest,
    response: Response,
    db: Database = Depends(get_db)
):
    service = UserService(db)
    user = await service.login(request)
    
    # 设置 Cookie
    response.set_cookie(
        key="SESSION",
        value=session_id,
        max_age=settings.session_max_age,
        httponly=True,  # 防止 XSS 攻击
        samesite="lax"  # CSRF 防护
    )
    return BaseResponse.success(data=user)

# 路径参数 + 查询参数
@router.get("/{task_id}", response_model=BaseResponse[ArticleVO])
async def get_article(
    task_id: str,  # 路径参数
    status: str = None,  # 查询参数
    db: Database = Depends(get_db)
):
    ...
```

**面试知识点：**
- `Depends()` 依赖注入的原理
- `response_model` 的作用（数据验证 + JSON 序列化）
- 为什么使用 `Cookie` 而不是 `Header` 存储 Session ID？

#### 1.3 Pydantic 数据模型 (`app/schemas/common.py`)

```python
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = Field(default=0, description="状态码")
    data: Optional[T] = Field(default=None, description="响应数据")
    message: str = Field(default="ok", description="响应消息")
    
    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "ok"):
        return cls(code=0, data=data, message=message)

class PageRequest(BaseModel):
    """分页请求"""
    current: int = Field(default=1, ge=1)  # ge=1 表示 >= 1
    page_size: int = Field(default=10, ge=1, le=100, alias="pageSize")
```

**面试知识点：**
- `BaseModel` 的数据验证和序列化机制
- `Field` 的验证规则（ge, le, alias）
- 泛型 `Generic[T]` 在响应模型中的应用

### 实践任务

1. 启动项目，访问 `http://localhost:8123/docs` 查看自动生成的 API 文档
2. 尝试调用 `/api/user/login` 接口，理解请求/响应结构
3. 自己定义一个 `ArticleCreateRequest` 模型

---

## Day 2：异步编程

### 学习目标
- 理解 Python 异步编程模型
- 掌握 `async/await` 语法
- 理解 FastAPI 中的异步处理

### 核心概念

#### 2.1 同步 vs 异步

```python
# 同步代码（阻塞）
def sync_get_user(user_id):
    result = db.execute("SELECT * FROM user WHERE id = ?", user_id)
    return result  # 等待数据库返回才继续

# 异步代码（非阻塞）
async def async_get_user(user_id):
    result = await db.execute("SELECT * FROM user WHERE id = ?", user_id)
    return result  # I/O 等待时可以切换到其他任务
```

#### 2.2 异步任务调度 (`app/routers/article.py`)

```python
import asyncio
from fastapi import APIRouter

router = APIRouter(prefix="/article", tags=["文章管理"])

@router.post("/create")
async def create_article(request: ArticleCreateRequest):
    # 1. 同步处理：创建任务、保存数据库
    service = ArticleService(db)
    task_id = await service.create_article_task_with_quota_check(...)
    
    # 2. 异步调度：创建后台任务（不阻塞响应）
    asyncio.create_task(
        article_async_service.execute_phase1(task_id, request.topic, request.style)
    )
    
    # 3. 立即返回响应给前端
    return BaseResponse.success(data=task_id, message="任务创建成功")
```

**面试知识点：**
- `asyncio.create_task()` vs `await` 的区别
- 为什么要用 `asyncio.create_task()` 而不是直接 `await`？
- 异步任务的异常不会被自动捕获

#### 2.3 并发执行 (`app/services/article_async_service.py`)

```python
import asyncio
from app.services.image_service_strategy import ImageServiceStrategy

class ArticleAsyncService:
    async def agent5_generate_images(self, state: ArticleState, emit):
        """并行生成多张图片"""
        # 1. 准备所有图片请求
        tasks = []
        for image_req in state.images:
            task = self.image_service.get_image_and_upload(image_req.source, image_req)
            tasks.append(task)
        
        # 2. 并行执行（最多同时 3 个）
        semaphore = asyncio.Semaphore(3)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(
            *[bounded_task(t) for t in tasks],
            return_exceptions=True  # 单个失败不影响其他
        )
```

**面试知识点：**
- `asyncio.gather()` 并行执行多个协程
- `Semaphore` 信号量控制并发数
- `return_exceptions=True` 防止一个失败导致全部失败

### 面试高频问题

**Q: 什么时候用 async def，什么时候用 def？**

```python
# 使用 async def：当函数涉及 I/O 操作时
async def get_user(user_id: int):
    return await db.fetch_one("SELECT * FROM user WHERE id = ?", user_id)

# 使用 def：当函数只做 CPU 计算时
def validate_email(email: str):
    return "@" in email and "." in email.split("@")[1]
```

**Q: FastAPI 中异步和同步路由的性能差异？**

- 同步路由：每个请求占用一个线程，请求阻塞时线程也阻塞
- 异步路由：单线程可处理多个请求，I/O 等待时可切换任务
- 对于 I/O 密集型（数据库、API 调用），异步路由性能更好

---

## Day 3：数据库操作

### 学习目标
- 掌握 SQLAlchemy ORM 模型定义
- 理解 `databases` 异步库的使用
- 学会事务管理和并发控制

### 核心代码

#### 3.1 ORM 模型定义 (`app/models/user.py`)

```python
from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, SmallInteger
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "user"  # 表名
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_account = Column("userAccount", String(256), nullable=False, unique=True)
    user_password = Column("userPassword", String(512), nullable=False)
    user_name = Column("userName", String(256))
    user_role = Column("userRole", String(256), nullable=False, default="user")
    quota = Column("quota", Integer, nullable=False, default=5)
    vip_time = Column("vipTime", DateTime, nullable=True)
    
    # 自动时间戳
    create_time = Column("createTime", DateTime, nullable=False, default=func.now())
    update_time = Column("updateTime", DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_delete = Column("isDelete", SmallInteger, nullable=False, default=0)  # 软删除
```

**面试知识点：**
- `primary_key=True` 主键
- `autoincrement=True` 自增
- `default=func.now()` 数据库自动填充时间
- `onupdate=func.now()` 更新时自动填充时间
- 软删除 `is_delete` 字段 vs 物理删除

#### 3.2 数据库连接 (`app/database.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

# SQLAlchemy 同步引擎（用于创建表等操作）
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # 连接前检测
    pool_recycle=3600,       # 1小时回收连接
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# databases 异步数据库（用于 FastAPI 异步查询）
database = Database(settings.database_url.replace("+pymysql", ""))
```

#### 3.3 事务处理 (`app/services/article_service.py`)

```python
class ArticleService:
    async def create_article_task_with_quota_check(self, topic: str, login_user: LoginUserVO, ...):
        # VIP/管理员跳过配额检查
        if self._is_vip_or_admin(login_user):
            return await self.create_article_task(...)
        
        # 开启事务
        async with self.db.transaction():
            # 1. 查询当前配额（加锁防止并发）
            quota_row = await self.db.fetch_one(
                query="""
                    SELECT quota FROM user 
                    WHERE id = :userId AND isDelete = 0
                    FOR UPDATE  -- 行级锁
                """,
                values={"userId": login_user.id},
            )
            
            # 2. 校验配额
            throw_if(quota_row["quota"] <= 0, ErrorCode.OPERATION_ERROR, "配额不足")
            
            # 3. 扣减配额
            await self.db.execute(
                query="UPDATE user SET quota = quota - 1 WHERE id = :userId",
                values={"userId": login_user.id},
            )
            
            # 4. 创建文章任务（在同一事务中）
            return await self.create_article_task(...)
```

**面试知识点：**
- `FOR UPDATE` 行级锁防止超卖
- `async with self.db.transaction()` 事务上下文管理器
- 同一事务中完成多个操作保证原子性

#### 3.4 复杂查询 (`app/services/article_service.py`)

```python
async def list_article_by_page(self, request: ArticleQueryRequest, login_user: LoginUserVO):
    # 1. 构建查询条件
    conditions = [Article.is_delete == 0]
    
    if login_user.user_role != "admin":
        conditions.append(Article.user_id == login_user.id)  # 只能看自己的
    
    if request.topic:
        conditions.append(Article.topic.like(f"%{request.topic}%"))  # 模糊搜索
    
    # 2. 查询总数
    count_query = select(func.count(Article.id)).where(and_(*conditions))
    total = await self.db.fetch_val(count_query)
    
    # 3. 分页查询
    query = (
        select(Article)
        .where(and_(*conditions))
        .order_by(Article.create_time.desc())
        .limit(request.page_size)
        .offset((request.current - 1) * request.page_size)
    )
    articles = await self.db.fetch_all(query)
    
    return [self._to_article_vo(article) for article in articles], total
```

**面试知识点：**
- `func.count()` 聚合函数
- `like` 模糊匹配
- 分页公式：`offset = (page - 1) * page_size`
- 为什么先查总数再查列表？

---

## Day 4：Redis 实战

### 学习目标
- 理解 Redis 数据结构
- 掌握 Session 管理
- 学会 Redis 异步操作

### 核心代码 (`app/utils/session.py`)

```python
import redis.asyncio as redis
import json
from app.config import settings

# Redis 连接池（全局）
redis_client: Optional[redis.Redis] = None

async def init_redis():
    """初始化 Redis 连接"""
    global redis_client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True  # 自动将 bytes 转为 str
    )

async def set_session(session_id: str, data: dict, expire: Optional[int] = None):
    """设置 Session（带过期时间）"""
    key = f"session:{session_id}"  # 使用前缀避免键冲突
    expire_time = expire or settings.session_max_age  # 默认 30 天
    
    await redis_client.setex(
        name=key,
        time=expire_time,
        value=json.dumps(data)
    )

async def get_session(session_id: str) -> Optional[dict]:
    """获取 Session"""
    key = f"session:{session_id}"
    data = await redis_client.get(key)
    
    if data:
        return json.loads(data)
    return None

async def remove_session(session_id: str):
    """删除 Session（登出）"""
    key = f"session:{session_id}"
    await redis_client.delete(key)
```

### 面试知识点

**Q: 为什么用 Redis 而不是 MySQL 存储 Session？**

| 对比项 | Redis | MySQL |
|--------|-------|-------|
| 读写速度 | ~微秒级 | ~毫秒级 |
| 数据结构 | 丰富 | 有限 |
| 过期机制 | 原生支持 | 需额外实现 |
| 适用场景 | 高频读取 | 持久化存储 |

**Q: Session 过期时间如何设计？**

```python
# 方案1：固定过期时间
await redis_client.setex(key, 3600, value)  # 1小时后过期

# 方案2：滑动过期（推荐）
await redis_client.setex(key, settings.session_max_age, value)
# 每次访问时重新设置过期时间

# 方案3：Redis TTL
ttl = await redis_client.ttl(key)
if ttl > 0:
    await redis_client.expire(key, settings.session_max_age)
```

**Q: Session 被盗用怎么办？**

1. `HttpOnly=True` - 防止 JavaScript 读取 Cookie
2. `SameSite=Lax` - 防止 CSRF 攻击
3. 敏感操作时重新验证密码
4. 异地登录检测（IP/User-Agent 变化）

---

## Day 5：多智能体架构（核心！）

### 学习目标
- 理解多智能体编排模式
- 掌握状态流转机制
- 学会 SSE 流式推送

### 核心概念

#### 5.1 阶段流转 (`app/models/enums.py`)

```python
class ArticlePhaseEnum(str, Enum):
    """文章阶段枚举"""
    PENDING = "PENDING"
    TITLE_GENERATING = "TITLE_GENERATING"      # 阶段1：生成标题
    TITLE_SELECTING = "TITLE_SELECTING"        # 阶段1：选择标题（用户介入）
    OUTLINE_GENERATING = "OUTLINE_GENERATING"   # 阶段2：生成大纲
    OUTLINE_EDITING = "OUTLINE_EDITING"         # 阶段2：编辑大纲（用户介入）
    CONTENT_GENERATING = "CONTENT_GENERATING"    # 阶段3：生成正文

    def can_transition_to(self, target_phase: "ArticlePhaseEnum") -> bool:
        """校验阶段流转是否合法"""
        transitions = {
            ArticlePhaseEnum.PENDING: {ArticlePhaseEnum.TITLE_GENERATING},
            ArticlePhaseEnum.TITLE_GENERATING: {ArticlePhaseEnum.TITLE_SELECTING},
            ArticlePhaseEnum.TITLE_SELECTING: {ArticlePhaseEnum.OUTLINE_GENERATING},
            ArticlePhaseEnum.OUTLINE_GENERATING: {ArticlePhaseEnum.OUTLINE_EDITING},
            ArticlePhaseEnum.OUTLINE_EDITING: {ArticlePhaseEnum.CONTENT_GENERATING},
            ArticlePhaseEnum.CONTENT_GENERATING: set(),  # 最终阶段，不可再流转
        }
        return target_phase in transitions.get(self, set())
```

**面试知识点：**
- 状态机模式保证业务流程的合法性
- 每个阶段只能流转到指定的后续阶段
- 用户介入点（TITLE_SELECTING、OUTLINE_EDITING）设计

#### 5.2 智能体编排 (`app/agent/orchestrator.py`)

```python
class ArticleAgentOrchestrator:
    """多智能体编排器"""
    
    def __init__(self):
        self.title_agent = TitleGeneratorAgent()
        self.outline_agent = OutlineGeneratorAgent()
        self.content_agent = ContentGeneratorAgent()
        self.image_analyzer_agent = ImageAnalyzerAgent()
        self.content_merger_agent = ContentMergerAgent()
    
    async def execute_phase1(self, service, state, stream_handler):
        """阶段1：生成标题方案"""
        await self.title_agent.run(service, state)
        stream_handler(SseMessageTypeEnum.AGENT1_COMPLETE.value)
    
    async def execute_phase2(self, service, state, stream_handler):
        """阶段2：生成大纲"""
        await self.outline_agent.run(service, state, stream_handler.emit)
        stream_handler(SseMessageTypeEnum.AGENT2_COMPLETE.value)
    
    async def execute_phase3(self, service, state, stream_handler):
        """阶段3：生成正文 + 配图 + 合成"""
        # 3.1 生成正文
        await self.content_agent.run(service, state, stream_handler.emit)
        
        # 3.2 分析配图需求
        await self.image_analyzer_agent.run(service, state)
        
        # 3.3 生成配图（并行）
        await service.agent5_generate_images(state, stream_handler.emit)
        
        # 3.4 图文合成
        self.content_merger_agent.run(service, state)
```

**面试知识点：**
- 编排器（Orchestrator）模式协调多个智能体
- 每个阶段专注单一任务（SRP 原则）
- 阶段之间有用户介入点（Human-in-the-Loop）

#### 5.3 SSE 流式推送 (`app/managers/sse_manager.py`)

```python
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

router = APIRouter()

# SSE 管理器（存储所有活跃连接）
sse_emitter_manager = SSEEmitterManager()

@router.get("/article/progress/{task_id}")
async def get_progress(task_id: str):
    """SSE 流式推送文章生成进度"""
    
    async def event_generator():
        queue = asyncio.Queue()
        sse_emitter_manager.add_listener(task_id, queue)
        
        try:
            while True:
                # 从队列获取消息
                message = await queue.get()
                
                # 解析消息类型
                msg_type = message.get("type")
                
                if msg_type == "AGENT2_STREAMING":
                    # 流式输出：返回当前生成的内容
                    yield {
                        "event": "streaming",
                        "data": json.dumps({
                            "type": msg_type,
                            "content": message.get("content", "")
                        })
                    }
                else:
                    # 普通消息：返回完整数据
                    yield {
                        "event": "message",
                        "data": json.dumps(message)
                    }
                
                # 任务完成，关闭连接
                if msg_type in ["ALL_COMPLETE", "ERROR"]:
                    break
                    
        finally:
            sse_emitter_manager.remove_listener(task_id, queue)
    
    return EventSourceResponse(event_generator())
```

**前端接收示例：**

```javascript
const eventSource = new EventSource(`/api/article/progress/${taskId}`);

eventSource.addEventListener("streaming", (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "AGENT2_STREAMING") {
        // 追加显示流式内容
        outlineContent += data.content;
    }
});

eventSource.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "ALL_COMPLETE") {
        // 任务完成
        eventSource.close();
    }
});
```

**面试知识点：**
- SSE vs WebSocket：SSE 单向通信、更轻量、自动重连
- 为什么使用队列而不是直接 yield？
- 如何避免连接泄漏（`finally` 块中清理）

---

## Day 6：图片服务（策略模式）

### 学习目标
- 理解策略模式的应用
- 掌握工厂模式
- 学会图片上传 COS

### 核心代码 (`app/services/image_service_strategy.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict

class ImageSearchService(ABC):
    """图片服务抽象基类"""
    
    @abstractmethod
    def get_method(self) -> ImageMethodEnum:
        pass
    
    @abstractmethod
    async def get_image_data(self, request: ImageRequest) -> Optional[ImageData]:
        pass
    
    def is_available(self) -> bool:
        """服务是否可用（API Key 等）"""
        return True

class PexelsService(ImageSearchService):
    """Pexels 图库服务"""
    
    def get_method(self) -> ImageMethodEnum:
        return ImageMethodEnum.PEXELS
    
    async def get_image_data(self, request: ImageRequest) -> Optional[ImageData]:
        # 调用 Pexels API 获取图片
        ...
        return ImageData(url=url, format="jpeg")

class NanoBananaService(ImageSearchService):
    """Nano Banana AI 生图服务"""
    
    def get_method(self) -> ImageMethodEnum:
        return ImageMethodEnum.NANO_BANANA
    
    async def get_image_data(self, request: ImageRequest) -> Optional[ImageData]:
        # 调用 Gemini AI 生成图片
        ...
        return ImageData(data=bytes_data, format="png")

class ImageServiceStrategy:
    """图片服务策略选择器"""
    
    def __init__(self):
        self.service_map: Dict[ImageMethodEnum, ImageSearchService] = {}
        self._register_services()
    
    def _register_services(self):
        """注册所有图片服务"""
        services = [
            PexelsService(),
            NanoBananaService(),
            MermaidService(),
            IconifyService(),
            EmojiPackService(),
            SvgDiagramService(),
        ]
        
        for service in services:
            method = service.get_method()
            self.service_map[method] = service
    
    async def get_image_and_upload(
        self,
        image_source: str,
        request: ImageRequest
    ) -> ImageResult:
        """获取图片并上传到 COS"""
        method = self._resolve_method(image_source)
        service = self.service_map.get(method)
        
        if service is None or not service.is_available():
            return await self._handle_fallback(request.position)
        
        try:
            image_data = await service.get_image_data(request)
            if image_data is None:
                return await self._handle_fallback(request.position)
            
            # 上传到 COS
            cos_url = await self.cos_service.upload_image_data(image_data)
            return ImageResult(cos_url, method)
        except Exception as e:
            return await self._handle_fallback(request.position)
    
    async def _handle_fallback(self, position: int) -> ImageResult:
        """降级处理：当主服务不可用时使用 Picsum"""
        fallback_url = f"https://picsum.photos/seed/{position}/1200/800"
        return ImageResult(fallback_url, ImageMethodEnum.PICSUM)
```

**面试知识点：**
- **策略模式**：定义一系列算法，把它们一个个封装起来，使它们可以互相替换
- **开闭原则**：新增图片服务无需修改 `ImageServiceStrategy`
- **降级策略**：服务不可用时自动切换到备用方案

---

## Day 7：认证鉴权

### 学习目标
- 掌握依赖注入实现认证
- 理解 Cookie + Session 认证流程
- 学会权限控制

### 核心代码 (`app/deps.py`)

```python
from fastapi import Cookie, Depends, HTTPException, status
from typing import Optional

async def get_session_id(session_id: Optional[str] = Cookie(None, alias="SESSION")):
    """从 Cookie 中获取 Session ID"""
    return session_id

async def get_current_user(
    session_id: Optional[str] = Depends(get_session_id)
) -> Optional[LoginUserVO]:
    """获取当前登录用户（可选）- 用于需要登录但非强制的地方"""
    if not session_id:
        return None
    
    session_data = await get_session(session_id)
    if not session_data or "user" not in session_data:
        return None
    
    return LoginUserVO(**session_data["user"])

async def require_login(
    current_user: Optional[LoginUserVO] = Depends(get_current_user)
) -> LoginUserVO:
    """要求必须登录 - 用于需要登录的接口"""
    if not current_user:
        raise BusinessException(ErrorCode.NOT_LOGIN_ERROR)
    return current_user

async def require_admin(
    current_user: LoginUserVO = Depends(require_login)
) -> LoginUserVO:
    """要求必须是管理员"""
    if current_user.user_role != "admin":
        raise BusinessException(ErrorCode.NO_AUTH_ERROR)
    return current_user
```

### 使用示例

```python
@router.post("/article/create")
async def create_article(
    request: ArticleCreateRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)  # 必须登录
):
    # current_user.id 就是当前登录用户 ID
    ...

@router.post("/user/list/page")
async def list_users(
    request: UserQueryRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_admin)  # 必须管理员
):
    # 只有管理员才能访问
    ...
```

**面试知识点：**
- 依赖注入链：`get_session_id` → `get_current_user` → `require_login` → `require_admin`
- 为什么用 `Cookie` 而不用 `Header`？
- `Optional[LoginUserVO]` vs `LoginUserVO` 的区别

---

## Day 8：Stripe 支付

### 学习目标
- 理解 Stripe Checkout 流程
- 掌握 Webhook 回调处理
- 学会支付状态管理

### 核心流程

```
用户点击购买 VIP
    ↓
后端创建 Stripe Checkout Session
    ↓
返回 Session URL，前端跳转到 Stripe 页面
    ↓
用户完成支付
    ↓
Stripe 发送 Webhook 回调
    ↓
后端更新用户 VIP 状态
```

### 核心代码

```python
@router.post("/payment/createVipSession")
async def create_vip_session(
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login)
):
    """创建 VIP 购买会话"""
    service = PaymentService(db)
    session_url = await service.create_vip_checkout_session(current_user.id)
    return BaseResponse.success(data={"url": session_url})

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Database = Depends(get_db)
):
    """处理 Stripe 回调"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    # 1. 验证签名
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        return {"error": "Invalid payload"}
    except stripe.error.SignatureVerificationError:
        return {"error": "Invalid signature"}
    
    # 2. 处理不同事件
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await service.handle_checkout_completed(session)
    
    elif event["type"] == "charge.refunded":
        charge = event["data"]["object"]
        await service.handle_refund(charge)
    
    return {"received": True}
```

**面试知识点：**
- 为什么需要 Webhook 验证签名？
- 幂等性处理：同一支付可能触发多次回调
- 事务安全：支付状态更新必须原子

---

## Day 9：项目部署

### 学习目标
- 理解 Docker 部署
- 掌握环境配置管理
- 学会生产环境优化

### Docker 配置

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY pyproject.toml .
RUN pip install -e .

# 复制代码
COPY . .

# 运行
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8123"]
```

```yaml
# docker-compose.yml
services:
  backend:
    build: .
    ports:
      - "8123:8123"
    environment:
      - DB_HOST=mysql
      - REDIS_HOST=redis
    depends_on:
      - mysql
      - redis

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: ai_passage

  redis:
    image: redis:7-alpine
```

### 生产环境优化

```python
# uvicorn 配置
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8123,
    workers=4,              # 多进程
    loop="uvloop",         # 高性能事件循环
    http="httptools",      # 高性能 HTTP 解析
)
```

**面试知识点：**
- `workers > 1` 时需注意：每个 worker 有独立的数据库连接池
- 异步 + 多进程组合的坑
- 健康检查接口设计

---

## Day 10：面试冲刺

### 架构设计问题

**Q: 项目的整体架构是怎样的？**

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│   前端 Vue   │────▶│   FastAPI 后端   │────▶│    MySQL     │
│  localhost   │     │   localhost:8123 │     │              │
└─────────────┘     └────────┬─────────┘     └──────────────┘
       │                      │
       │                      ▼
       │              ┌───────────────┐
       │              │     Redis     │
       │              │  (Session)    │
       │              └───────────────┘
       │                      │
       ▼                      ▼
┌─────────────┐     ┌─────────────────┐
│  外部 API    │◀────│   图片服务       │
│  通义千问     │     │  Pexels/COS     │
│  Stripe     │     │  Gemini         │
└─────────────┘     └─────────────────┘
```

**Q: 为什么选择 FastAPI 而不是 Django/Flask？**

| 框架 | 特点 | FastAPI 优势 |
|------|------|-------------|
| Django | 大而全、ORM 强大 | 轻量、异步、性能高 |
| Flask | 灵活、微框架 | 自动 API 文档、类型提示 |
| FastAPI | 现代、高性能、自动文档 | 异步支持、数据验证 |

**Q: 多智能体架构解决了什么问题？**

1. **解耦复杂流程**：每个智能体专注单一任务
2. **人机协作**：用户可在关键节点介入调整
3. **可扩展性**：新增智能体无需修改现有代码
4. **可观测性**：每个智能体独立日志

**Q: 图片服务为什么用策略模式？**

1. **统一接口**：所有图片服务实现相同接口
2. **灵活切换**：运行时选择不同服务
3. **易于扩展**：新增服务只需实现接口
4. **降级策略**：主服务不可用时自动切换

### 技术亮点总结

| 亮点 | 说明 |
|------|------|
| 异步编排 | `asyncio` + `create_task` 实现非阻塞任务调度 |
| 状态机 | `ArticlePhaseEnum.can_transition_to()` 保证流程合法 |
| 策略模式 | 图片服务可插拔、自动降级 |
| SSE 流式推送 | 实时展示 AI 生成进度 |
| Redis Session | 高性能分布式会话存储 |
| 行级锁事务 | `FOR UPDATE` 防止并发超卖 |

---

## 学习资源

### 官方文档
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Redis: https://redis.io/docs/

### 项目关键文件索引

| 文件 | 用途 |
|------|------|
| `app/main.py` | 应用入口、中间件、异常处理 |
| `app/config.py` | 配置管理（Pydantic Settings） |
| `app/database.py` | 数据库连接 |
| `app/deps.py` | 依赖注入（认证、权限） |
| `app/routers/*.py` | API 路由定义 |
| `app/services/*.py` | 业务逻辑 |
| `app/agent/orchestrator.py` | 智能体编排 |
| `app/models/*.py` | ORM 模型 |
| `app/schemas/*.py` | Pydantic 数据模型 |
| `app/utils/session.py` | Redis Session |

---

## 下一步建议

1. **代码通读**：按上面的文件索引，逐一阅读理解
2. **本地运行**：`start.sh` 启动项目，实际操作一遍
3. **抓重点**：Day 1-5 是核心，必须掌握
4. **模拟面试**：找朋友或用 AI 模拟技术面试
5. **准备亮点**：每个项目亮点准备 2-3 分钟的讲解

---

> 祝你面试顺利！有问题随时问我。
