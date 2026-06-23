<h1 style="font-size: 3em; margin: 16px 0; font-weight: 900;">AI 小说创作助手</h1>

<div align="center">

基于 FastAPI、Vue 3、MySQL、Redis、ARQ 和大语言模型的长篇小说辅助创作平台。

从创意孵化、世界观与角色设定，到章节规划、正文生成、质量审稿、自动修订和状态归档，形成一套可追踪的小说创作工作流。

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=flat-square&logo=typescript&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.x-DC382D?style=flat-square&logo=redis&logoColor=white)

</div>

## 项目简介

本项目不是简单地将“设定 + 上一章”发送给模型，而是围绕长篇小说的连续创作构建了完整链路：

```text
创意孵化
  → 世界观、角色与卷纲
  → 章节规划与作者要求
  → 目标章上下文组装
  → 正文流式生成
  → 质量审稿与自动修订
  → 用户确认
  → 摘要、角色状态、伏笔和版本归档
```

后端通过 ARQ + Redis 执行耗时任务，通过 SSE 向前端推送生成状态和正文片段。MySQL 保存小说、章节、角色、伏笔、上下文快照和版本记录。

项目中还保留了文章生成、图片服务、VIP 与支付等扩展模块，但当前 README 主要介绍小说创作主链路。

## 主要功能

- AI 完善原始创意，生成卖点、主角设计、能力体系和长线冲突
- 自动生成世界观、初始角色和卷级大纲
- 分析样本文本并形成写作风格指南
- 支持作者指定本章意图和特别要求
- 生成结构化章节备忘录与目标章上下文包
- SSE 实时展示章节生成内容
- 生成后自动审稿，并按审稿结果进行一次修订
- 保存 AI 草稿、自动修订稿和用户确认稿
- 跟踪角色状态、关系、地点和伏笔生命周期
- 全书连贯性检查与问题报告
- 小说导出、章节编辑和重新生成

## 智能体工作流

| 智能体 | 职责 |
|---|---|
| Agent 0 | 创意孵化与二次打磨 |
| Agent 1 | 世界观、角色和卷纲生成 |
| Agent 2 | 样本文风分析 |
| Agent 3 | 章节方向建议与章节规划 |
| Agent 4 | 正文写作、质量审稿和自动修订 |
| Agent 5 | 章节摘要、角色状态和伏笔归档 |
| Agent 6 | 全书连贯性检查 |

## 技术栈

### 后端

- Python 3.10+
- FastAPI 0.115
- SQLAlchemy、databases、PyMySQL、aiomysql
- MySQL 8.0
- Redis 7
- ARQ 后台任务队列
- OpenAI Python SDK，调用 OpenAI-compatible Chat Completions 接口
- 支持 DashScope、豆包/火山方舟和自定义兼容服务

### 前端

- Vue 3.5
- TypeScript 5.8
- Vite 7
- Ant Design Vue
- Pinia、Vue Router、Axios
- ECharts、Marked、SortableJS

## 系统架构

```text
浏览器
  │
  ├── HTTP API ───────────────→ FastAPI ─────────────→ MySQL
  │                               │
  │                               ├── 任务入队 ───────→ Redis / ARQ
  │                               │                      │
  │                               │                      └── Novel Worker
  │                               │                           │
  │                               │                           └── LLM Provider
  │                               │
  └── SSE 进度与正文流 ←────────── Redis 事件流
```

## 快速部署：Docker Compose

这是最适合新人的启动方式。只需要安装 Git、Docker 和 Docker Compose，不需要在宿主机单独安装 Python、Node.js、MySQL 或 Redis。

### 1. 克隆项目

```bash
git clone <你的仓库地址>
cd ai-novel
```

### 2. 创建两份环境变量

macOS / Linux：

```bash
cp python-backend/.env.example .env
cp python-backend/.env.example python-backend/.env
```

Windows PowerShell：

```powershell
Copy-Item python-backend/.env.example .env
Copy-Item python-backend/.env.example python-backend/.env
```

两份配置的用途不同：

| 文件 | 用途 |
|---|---|
| `.env` | Docker Compose、MySQL、Redis、容器后端和对外端口 |
| `python-backend/.env` | 本地运行 FastAPI 与 ARQ Worker |

为了同时支持 Docker 部署和本地调试，建议两份都创建并配置。数据库密码、Redis 密码、模型 Provider、API Key、Session 密钥等公共配置需要保持一致。

编辑项目根目录的 `.env`，至少修改以下内容：

```env
# 基础服务
MYSQL_ROOT_PASSWORD=请设置数据库密码
MYSQL_DATABASE=ai_passage_creator
REDIS_PASSWORD=请设置Redis密码

# 安全配置，生产环境必须换成随机值
SESSION_SECRET_KEY=请设置一个足够长的随机字符串
PASSWORD_SALT=请设置密码盐值

# 大模型：DashScope 示例
LLM_PROVIDER=dashscope
LLM_TIMEOUT_SECONDS=120
DASHSCOPE_API_KEY=你的API Key
DASHSCOPE_MODEL=qwen-plus
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 对外端口
BACKEND_PORT=8123
FRONTEND_PORT=80
```

然后将相同的模型和安全配置同步到 `python-backend/.env`。本地运行后端时，数据库与 Redis 地址应使用：

```env
DB_HOST=localhost
REDIS_HOST=localhost
SERVER_PORT=8567
```

其他图片、对象存储和支付配置是可选项，不使用相应功能时可以留空。

> Docker Compose 实际读取根目录 `.env`；本地 FastAPI 和 Worker 实际读取 `python-backend/.env`。不要把任意一份 `.env`、API Key、数据库密码或支付密钥提交到 GitHub。

### 3. 构建并启动

```bash
docker compose up -d --build
```

首次启动会自动：

1. 拉取 MySQL、Redis、Python、Node.js 和 Nginx 镜像。
2. 创建数据库并执行 `sql/` 中的初始化脚本。
3. 构建并启动 FastAPI 后端。
4. 启动 ARQ 小说任务 Worker。
5. 构建 Vue 前端并由 Nginx 提供访问。

查看服务状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f backend worker
```

### 4. 访问项目

默认地址：

| 服务 | 地址 |
|---|---|
| 前端页面 | http://localhost |
| 后端接口 | http://localhost:8123 |
| Swagger API 文档 | http://localhost:8123/docs |
| 健康检查 | http://localhost:8123/api/health |

如果修改了 `FRONTEND_PORT` 或 `BACKEND_PORT`，请使用修改后的端口。

### 5. 测试账号

数据库首次初始化会创建以下账号，默认密码均为 `12345678`：

| 账号 | 角色 |
|---|---|
| `admin` | 管理员 |
| `user` | 普通用户 |
| `test` | 普通用户 |

公开部署前请修改或删除默认账号。

### 6. 停止或重启

```bash
# 停止服务，保留数据库数据
docker compose down

# 重启
docker compose restart

# 更新代码后重新构建
docker compose up -d --build
```

彻底删除容器和数据库卷：

```bash
docker compose down -v
```

> `down -v` 会永久删除 MySQL 和 Redis 数据，仅适合确认不需要旧数据时使用。

## 本地开发启动

本地开发建议使用 Docker 只运行 MySQL 和 Redis，Python 后端、Worker 和 Vue 前端在宿主机运行。

### 环境要求

- Python 3.10 或 3.11
- Node.js `^20.19.0` 或 `>=22.12.0`
- npm
- Docker Desktop，或自行安装 MySQL 8.0 与 Redis 7

### 1. 检查两份配置

如果还没有创建环境文件，请先创建两份：

```powershell
Copy-Item python-backend/.env.example .env
Copy-Item python-backend/.env.example python-backend/.env
```

根目录 `.env` 负责 Docker 服务，`python-backend/.env` 负责本地后端和 Worker。两边的数据库密码、Redis 密码和模型配置必须保持一致。

### 2. 启动 MySQL 和 Redis

```bash
docker compose up -d mysql redis
```

在全新的 Docker 数据卷中，数据库表和测试账号会自动初始化。

### 3. 配置 Python 后端

编辑 `python-backend/.env`，确保本地连接配置与根目录 `.env` 一致：

```env
SERVER_HOST=0.0.0.0
SERVER_PORT=8567

DB_HOST=localhost
DB_PORT=3306
DB_NAME=ai_passage_creator
DB_USER=root
DB_PASSWORD=与MYSQL_ROOT_PASSWORD相同

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=与根目录REDIS_PASSWORD相同

NOVEL_QUEUE_ENABLED=true
NOVEL_QUEUE_NAME=ai_novel_tasks

SESSION_SECRET_KEY=本地开发密钥
PASSWORD_SALT=yupi

LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=你的API Key
DASHSCOPE_MODEL=qwen-plus
```

### 4. 安装后端依赖

Windows PowerShell：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r python-backend\requirements.txt
```

macOS / Linux：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r python-backend/requirements.txt
```

### 5. 安装前端依赖

```bash
cd frontend
npm ci
cd ..
```

### 6. 分别启动三个进程

终端一：FastAPI 后端

```bash
cd python-backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8567 --reload
```

终端二：ARQ Worker

```bash
cd python-backend
arq app.workers.novel_worker.WorkerSettings
```

终端三：Vue 前端

```bash
cd frontend
npm run dev
```

访问：

- 前端：http://localhost:5173
- 后端：http://localhost:8567
- API 文档：http://localhost:8567/docs

> Worker 必须运行。只启动后端和前端时，小说设定生成、章节生成和归档任务会进入队列，但不会被消费。

### 关于项目中的 PowerShell 启动脚本

`start-project.ps1`、`start-backend.ps1`、`start-frontend.ps1` 和 `start-worker.ps1` 是当前开发机器使用的快捷脚本，其中包含本机 Conda、MySQL 和 Memurai 路径。

其他开发者使用前必须修改这些路径，因此 GitHub 新用户应优先使用上面的 Docker 或手动启动方式。

## 手动初始化 MySQL

如果不使用 Docker 管理 MySQL，需要按以下顺序执行一次：

```bash
mysql -u root -p < sql/create_table.sql
mysql -u root -p < sql/update_quota.sql
mysql -u root -p < sql/add_phase_fields.sql
mysql -u root -p < sql/add_article_style.sql
mysql -u root -p < sql/add_vip_payment.sql
mysql -u root -p < sql/create_novel_tables.sql
```

Windows PowerShell 可通过 `cmd` 执行重定向：

```powershell
cmd /c "mysql -u root -p < sql\create_table.sql"
```

其余 SQL 文件按照上面的顺序执行。

`sql/add_novel_quality_loop.sql` 用于升级早期版本数据库。当前 `create_novel_tables.sql` 已包含质量闭环字段和表，新数据库不要重复执行该升级脚本。

## 大模型配置

### DashScope

```env
LLM_PROVIDER=dashscope
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_MODEL=qwen-plus
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 豆包 / 火山方舟

```env
LLM_PROVIDER=doubao
DOUBAO_API_KEY=your-api-key
DOUBAO_MODEL=your-model-or-endpoint-id
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

### 其他 OpenAI-compatible 服务

```env
LLM_PROVIDER=custom
LLM_API_KEY=your-api-key
LLM_MODEL=your-model
LLM_BASE_URL=https://example.com/v1
```

还可以为不同阶段指定不同模型：

```env
LLM_MODEL_PLAN=
LLM_MODEL_WRITE=
LLM_MODEL_AUDIT=
LLM_MODEL_REVISE=
LLM_MODEL_ARCHIVE=
```

留空时使用当前 Provider 的默认模型。

## 项目结构

```text
ai-novel/
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── api/                 # API 客户端
│   │   ├── pages/               # 页面
│   │   ├── stores/              # Pinia 状态
│   │   └── config/env.ts        # 前端 API 基础路径
│   ├── Dockerfile
│   └── nginx.conf
├── python-backend/
│   ├── app/
│   │   ├── constants/           # Prompt 模板
│   │   ├── managers/            # SSE 管理
│   │   ├── models/              # 数据模型和枚举
│   │   ├── routers/             # FastAPI 路由
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── services/            # 小说业务、Agent、上下文与队列
│   │   └── workers/             # ARQ Worker
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── sql/                         # 初始化和升级 SQL
├── docker-compose.yml
├── Dockerfile                   # Python 后端镜像
└── README.md
```

## API 与健康检查

所有业务接口统一使用 `/api` 前缀，完整接口和请求模型请查看 Swagger：

- Docker：http://localhost:8123/docs
- 本地开发：http://localhost:8567/docs

常用小说接口：

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/novel/idea/enhance` | 完善核心创意 |
| POST | `/api/novel/create` | 创建小说并生成初始设定 |
| GET | `/api/novel/list` | 小说列表 |
| POST | `/api/novel/{id}/chapter/plan` | 规划章节 |
| POST | `/api/novel/{id}/chapter/generate` | 生成正文 |
| PUT | `/api/novel/chapter/{id}/confirm` | 确认并归档章节 |
| POST | `/api/novel/{id}/consistency` | 全书连贯性检查 |
| GET | `/api/novel/progress/{taskId}` | SSE 任务进度 |
| GET | `/api/novel/{id}/export` | 导出小说 |

## 验证与测试

后端单元测试：

```bash
cd python-backend
python -m unittest discover -s tests
```

前端类型检查和生产构建：

```bash
cd frontend
npm run build
```

Docker 服务检查：

```bash
docker compose ps
docker compose logs --tail=100 backend worker
```

## 常见问题

### 任务一直停留在生成中

检查 Worker 是否启动：

```bash
docker compose ps worker
docker compose logs -f worker
```

本地开发则确认 `arq app.workers.novel_worker.WorkerSettings` 正在运行。

### 后端无法连接 MySQL 或 Redis

确认：

- `DB_PASSWORD` 与 `MYSQL_ROOT_PASSWORD` 一致。
- `REDIS_PASSWORD` 在根目录 `.env` 和 `python-backend/.env` 中一致。
- 本地后端使用 `localhost`，Docker 容器内部使用服务名 `mysql` 和 `redis`。

### 修改 SQL 后没有自动生效

MySQL Docker 初始化脚本只会在数据卷第一次创建时执行。开发环境不需要旧数据时可执行：

```bash
docker compose down -v
docker compose up -d --build
```

需要保留旧数据时，请编写并手动执行增量迁移，不要删除数据卷。

### 端口被占用

修改根目录 `.env`：

```env
MYSQL_PORT=3307
REDIS_PORT=6380
BACKEND_PORT=8124
FRONTEND_PORT=8080
```

如果本地运行后端和前端，还需要同步修改对应启动命令或 Vite 代理配置。

## 上传 GitHub 前检查

```bash
git status
git ls-files | grep -E "(^|/)\.env$|\.local-services"
```

Windows PowerShell 可使用：

```powershell
git status
git ls-files | Select-String '\.env$|\.local-services'
```

确认以下内容没有被提交：

- 根目录 `.env`
- `python-backend/.env`
- `.local-services/`
- API Key、数据库密码、Session 密钥和支付密钥

如果密钥曾经出现在 Git 历史、终端截图或公开文件中，应先在对应平台作废并重新生成。

## 贡献

欢迎通过 Issue 或 Pull Request 提交问题和改进。

## License

当前仓库尚未包含开源许可证。公开发布前，请根据实际授权意图添加 `LICENSE` 文件；在许可证明确之前，默认保留全部权利。
