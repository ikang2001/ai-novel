# AI 小说创作助手 📚

<div align="center">

**AI 小说创作助手**

基于多智能体协作，自动完成从世界观设定、角色创建、章节规划到正文生成的全流程小说创作

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)
![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8-3178C6?style=flat-square&logo=typescript&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.x-DC382D?style=flat-square&logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

</div>

## 🏗 项目简介

AI 小说创作助手是一个基于 **多智能体协作** 的智能小说创作平台，通过 **6 个专业智能体分工协作**，完成从开书设定到章节写作的全流程创作。每个阶段都支持用户介入编辑，实现人机协作的创作体验。

```
阶段1: 输入创意 → Agent1 生成世界观、角色、卷大纲
阶段2: 规划章节 → Agent3 生成章节大纲
阶段3: 生成正文 → Agent4 流式生成章节内容
阶段4: 确认归档 → Agent5 生成章节摘要、更新角色状态
阶段5: 连贯检查 → Agent6 检查全书一致性问题
```

## 🎯 核心价值

| 特性 | 说明 | 价值 |
|------|------|------|
| 🤖 多智能体协作 | 6 个 Agent 分工协作 | 专业分工，质量更高 |
| 📡 实时流式输出 | SSE 推送创作过程 | 所见即所得 |
| 🧑‍💻 人机协作 | 每步可介入编辑 | 创作可控 |
| 🎨 风格学习 | 分析参考文本的写作风格 | 保持风格一致 |
| 🔍 连贯性检查 | AI 检查角色、时间线、伏笔问题 | 逻辑自洽 |
| 📝 三层记忆系统 | 梗概 → 章节摘要 → 原文，逐层检索 | 上下文连贯 |

## ✨ 功能特性

### 智能体协作

| 智能体 | 功能 | 说明 |
|--------|------|------|
| Agent 1 | 开书设定 | 生成世界观、角色表、卷大纲 |
| Agent 2 | 风格分析 | 分析参考文本，提取写作风格指南 |
| Agent 3 | 章节规划 | 生成章节大纲（标题、梗概、写作指导） |
| Agent 4 | 正文写作 | 流式生成 4000-6000 字章节内容 |
| Agent 5 | 归档处理 | 生成摘要、更新角色状态、埋设伏笔 |
| Agent 6 | 连贯检查 | 检查角色矛盾、时间线错误、伏笔遗忘等 |

### 核心功能

- ✅ **小说管理** - 创建、编辑、删除小说
- ✅ **世界观设定** - AI 生成并支持手动编辑
- ✅ **角色管理** - 主角/配角/反派，状态追踪
- ✅ **伏笔管理** - 埋设、揭示、放弃伏笔
- ✅ **章节创作** - 规划大纲 → 生成内容 → 确认归档
- ✅ **风格学习** - 粘贴参考文本，AI 分析写作风格
- ✅ **连贯性检查** - 检查全书逻辑问题并提供修改建议
- ✅ **实时流式输出** - SSE 推送创作进度
- ✅ **内容编辑** - 支持手动修改章节内容

### 三层记忆系统

```
第一层：全书梗概（synopsis）        → 始终注入，保证全局连贯
第二层：近 3 章摘要（summary）      → 始终注入，保证衔接
第三层：近 1 章原文（content）       → 按需检索，参考细节
```

## 🛠 技术栈

### 后端

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 运行环境 |
| FastAPI | 0.110+ | Web 框架 |
| DashScope | - | 通义千问大模型（qwen-plus） |
| databases | - | 异步数据库驱动 |
| PyMySQL | - | MySQL 客户端 |
| Redis | - | 缓存和会话存储 |
| SSE | - | Server-Sent Events 实时通信 |

### 前端

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5 | 前端框架 |
| TypeScript | 5.8 | 类型安全 |
| Ant Design Vue | 4.2 | UI 组件库 |
| Vite | 7.0 | 构建工具 |
| Pinia | 3.0 | 状态管理 |
| Vue Router | 4.5 | 路由管理 |
| Axios | 1.11 | HTTP 客户端 |
| Markdown-it | - | Markdown 渲染 |

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 7.x
- Conda（推荐）

### 1. 启动 MySQL 和 Redis

```bash
# 使用 Docker 启动
docker compose up -d mysql redis
```

### 2. 配置环境变量

```bash
cd python-backend
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ai_passage_creator
DB_USER=root
DB_PASSWORD=your_password

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# AI 配置（必填）
DASHSCOPE_API_KEY=your-dashscope-api-key
DASHSCOPE_MODEL=qwen-plus
```

### 3. 初始化数据库

```bash
mysql -uroot -p < sql/create_novel_tables.sql
```

### 4. 启动后端

```bash
# 创建 conda 环境
conda create -n novel python=3.10
conda activate novel

# 安装依赖
cd python-backend
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8567
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 测试账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | 12345678 | 管理员 |

## 📁 项目结构

```
ai-passage-creator-main/
├── python-backend/                  # Python 后端
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── config.py                # 配置管理
│   │   ├── database.py              # 数据库连接
│   │   ├── deps.py                  # 依赖注入
│   │   ├── exceptions.py            # 异常处理
│   │   ├── routers/                 # 路由模块
│   │   │   ├── novel.py             # 小说相关 API
│   │   │   ├── user.py              # 用户相关 API
│   │   │   └── ...
│   │   ├── services/                # 业务服务
│   │   │   ├── novel_service.py     # 小说 CRUD
│   │   │   ├── novel_async_service.py  # 异步任务编排
│   │   │   ├── novel_agent_service.py  # Agent 调用
│   │   │   ├── character_service.py    # 角色管理
│   │   │   ├── foreshadowing_service.py  # 伏笔管理
│   │   │   └── context_builder.py      # 上下文构建
│   │   ├── schemas/                 # Pydantic 模型
│   │   ├── models/                  # 数据模型和枚举
│   │   ├── constants/               # Prompt 模板
│   │   └── managers/                # 管理器（SSE 等）
│   ├── .env                         # 环境变量
│   └── requirements.txt             # Python 依赖
├── frontend/                        # 前端项目
│   ├── src/
│   │   ├── pages/                   # 页面组件
│   │   │   ├── novel/               # 小说相关页面
│   │   │   │   ├── NovelCreatePage.vue
│   │   │   │   ├── NovelListPage.vue
│   │   │   │   ├── NovelDetailPage.vue
│   │   │   │   ├── NovelWritePage.vue
│   │   │   │   └── components/      # 业务组件
│   │   │   └── user/                # 用户相关页面
│   │   ├── api/                     # API 接口定义
│   │   ├── components/              # 公共组件
│   │   ├── stores/                  # Pinia 状态管理
│   │   ├── utils/                   # 工具函数
│   │   ├── constants/               # 常量定义
│   │   └── config/                  # 配置文件
│   └── package.json
├── sql/                             # 数据库脚本
│   ├── create_novel_tables.sql      # 小说模块建表
│   └── create_article_tables.sql    # 文章模块建表
├── docker-compose.yml               # Docker 编排
└── README.md
```

## 🗄 数据库设计

### 核心表

| 表名 | 说明 |
|------|------|
| novel | 小说表（世界观、卷大纲、风格指南） |
| chapter | 章节表（大纲、正文、摘要） |
| character | 角色表（外貌、性格、背景、状态） |
| foreshadowing | 伏笔表（埋设章节、揭示章节、状态） |
| user | 用户表 |

### 小说表关键字段

```sql
worldSetting     -- 世界观设定（JSON）
volumeOutline    -- 卷级大纲（JSON）
styleGuide       -- 风格指南（JSON）
synopsis         -- 全书梗概
phase            -- 当前阶段：PENDING/READY/CHAPTER_GENERATING
```

## 🔑 API Key 获取

| 服务 | 获取地址 | 说明 |
|------|---------|------|
| 通义千问 | https://bailian.console.aliyun.com | 必填，用于 AI 创作 |

## 📡 API 接口

### 小说管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/novel/create | 创建小说 |
| GET | /api/novel/list | 小说列表 |
| GET | /api/novel/{id} | 小说详情 |
| PUT | /api/novel/{id}/setting | 修改设定 |
| DELETE | /api/novel/{id} | 删除小说 |

### 章节管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/novel/{id}/chapter/plan | 规划章节大纲 |
| POST | /api/novel/{id}/chapter/generate | 生成章节内容 |
| PUT | /api/novel/chapter/{id}/confirm | 确认章节 |
| PUT | /api/novel/chapter/{id}/regenerate | 重新生成 |
| PUT | /api/novel/chapter/{id}/content | 修改内容 |
| PUT | /api/novel/chapter/{id}/title | 修改标题 |
| DELETE | /api/novel/chapter/{id} | 删除章节 |

### 角色管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/novel/{id}/characters | 角色列表 |
| POST | /api/novel/{id}/characters | 创建角色 |
| PUT | /api/novel/character/{id} | 修改角色 |
| DELETE | /api/novel/character/{id} | 删除角色 |

### 伏笔管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/novel/{id}/foreshadowing | 伏笔列表 |
| POST | /api/novel/{id}/foreshadowing | 创建伏笔 |
| PUT | /api/novel/foreshadowing/{id}/resolve | 揭示伏笔 |
| PUT | /api/novel/foreshadowing/{id}/abandon | 放弃伏笔 |

### 其他功能

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/novel/{id}/style/analyze | 风格分析 |
| POST | /api/novel/{id}/consistency | 连贯性检查 |
| GET | /api/novel/{id}/export | 导出小说 |
| GET | /api/novel/progress/{taskId} | SSE 进度推送 |

## 🏛 架构特点

### 多智能体协作流程

```
用户输入创意
    ↓
Agent 1 (开书设定)
    ├── 世界观设定
    ├── 角色表
    └── 卷大纲
    ↓
用户确认/编辑设定
    ↓
Agent 3 (章节规划) → 章节大纲
    ↓
Agent 4 (正文写作) → 流式生成 4000-6000 字
    ↓
用户确认/编辑内容
    ↓
Agent 5 (归档处理)
    ├── 章节摘要
    ├── 角色状态更新
    └── 伏笔追踪
    ↓
Agent 6 (连贯检查) → 问题报告
```

### SSE 实时通信

基于 Server-Sent Events 实现实时进度推送：

| 消息类型 | 说明 |
|---------|------|
| CHAPTER_GENERATING | 开始生成章节 |
| CHAPTER_STREAMING | 正文流式输出中 |
| CHAPTER_GENERATED | 章节生成完成 |
| STYLE_ANALYZING | 风格分析中 |
| STYLE_ANALYZED | 风格分析完成 |
| ALL_COMPLETE | 全部完成 |
| ERROR | 错误通知 |

## 🔧 扩展指南

### 添加新的智能体

1. 在 `novel_agent_service.py` 添加新的 agent 方法
2. 在 `novel_async_service.py` 添加任务编排
3. 在 `novel_prompt.py` 添加 Prompt 模板
4. 在 `routers/novel.py` 添加 API 端点

### 修改 AI 模型

编辑 `.env` 文件：

```env
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_MODEL=qwen-plus  # 或 qwen-turbo、qwen-max 等
```

## 📖 相关文档

- [项目启动说明](启动.txt) - 详细的启动步骤
- [数据库设计](sql/) - 建表脚本

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License

## 👨‍💻 作者

[ikang2001](https://github.com/ikang2001)
