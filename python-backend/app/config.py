"""配置管理 - 第 3 期：添加 AI 相关配置"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 获取项目根目录（python-backend 目录）
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """应用配置（第 3 期：AI 核心创作流程）"""
    
    # 服务器配置
    server_port: int = 8567
    server_host: str = "0.0.0.0"
    
    # 数据库配置
    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: str
    
    # Redis 配置
    redis_host: str
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Session 配置
    session_secret_key: str
    session_max_age: int = 2592000  # 30 天
    
    # 密码加密盐值
    password_salt: str
    
    # AI 配置（第 3 期新增）
    dashscope_api_key: str = ""
    dashscope_model: str = "qwen-plus"
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # OpenAI-compatible LLM provider selection.
    # Supported values: dashscope, doubao, volcengine, ark, custom.
    llm_provider: str = "dashscope"
    llm_timeout_seconds: float = 120.0

    # Generic OpenAI-compatible provider settings for LLM_PROVIDER=custom.
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""
    llm_model_plan: str = ""
    llm_model_write: str = ""
    llm_model_audit: str = ""
    llm_model_revise: str = ""
    llm_model_archive: str = ""

    # Doubao / Volcano Ark OpenAI-compatible settings.
    doubao_api_key: str = ""
    doubao_model: str = ""
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"

    # 小说任务队列。使用 ARQ + Redis，保留接口兼容。
    novel_queue_enabled: bool = True
    novel_queue_name: str = "ai_novel_tasks"
    novel_stream_chunk_chars: int = 40
    novel_stream_min_chunk_chars: int = 12
    novel_stream_flush_interval_seconds: float = 0.12
    novel_sse_poll_interval_seconds: float = 0.15
    novel_task_stream_max_len: int = 2000
    
    # Pexels 图片搜索（第 3 期新增）
    pexels_api_key: str = ""
    
    # 腾讯云 COS（第 3 期新增）
    tencent_cos_secret_id: str = ""
    tencent_cos_secret_key: str = ""
    tencent_cos_region: str = "ap-beijing"
    tencent_cos_bucket: str = ""
    tencent_cos_domain: str = ""
    
    # Nano Banana / Gemini AI 生图（第 5 期新增）
    nano_banana_api_key: str = ""
    nano_banana_model: str = "gemini-2.5-flash-image"
    nano_banana_aspect_ratio: str = "16:9"
    nano_banana_image_size: str = "1K"
    nano_banana_output_mime_type: str = "image/png"
    
    # Mermaid 配置（第 5 期新增）
    mermaid_cli_command: str = "mmdc"
    mermaid_background_color: str = "transparent"
    mermaid_output_format: str = "svg"
    mermaid_width: int = 1200
    mermaid_timeout: int = 30000
    
    # Iconify 配置（第 5 期新增）
    iconify_api_url: str = "https://api.iconify.design"
    iconify_search_limit: int = 10
    iconify_default_height: int = 64
    iconify_default_color: str = ""
    
    # 表情包配置（第 5 期新增）
    emoji_pack_search_url: str = "https://cn.bing.com/images/async"
    emoji_pack_suffix: str = "表情包"
    emoji_pack_timeout: int = 10000
    
    # SVG 示意图配置（第 5 期新增）
    svg_diagram_default_width: int = 800
    svg_diagram_default_height: int = 600
    svg_diagram_folder: str = "svg-diagrams"

    # 第 9 期：多智能体并行编排配置
    agent_image_max_concurrency: int = 3
    agent_image_fail_fast: bool = True

    # Stripe 支付配置（第 7 期新增）
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_success_url: str = "http://localhost:5173/payment/success"
    stripe_cancel_url: str = "http://localhost:5173/payment/cancel"
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def database_url(self) -> str:
        """获取数据库连接 URL"""
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
    
    @property
    def redis_url(self) -> str:
        """获取 Redis 连接 URL"""
        host = "127.0.0.1" if self.redis_host in {"localhost", "::1"} else self.redis_host
        if self.redis_password:
            return f"redis://:{self.redis_password}@{host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
