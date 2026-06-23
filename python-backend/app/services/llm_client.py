"""OpenAI-compatible LLM provider selection."""

from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import settings


@dataclass(frozen=True)
class LlmRuntimeConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    timeout: float


def get_llm_runtime_config() -> LlmRuntimeConfig:
    """Resolve the active chat model provider from environment settings."""
    provider = (settings.llm_provider or "dashscope").strip().lower()
    timeout = float(settings.llm_timeout_seconds or 120.0)

    if provider in {"dashscope", "qwen", "aliyun"}:
        api_key = settings.dashscope_api_key
        base_url = settings.dashscope_base_url
        model = settings.dashscope_model
        provider_name = "dashscope"
    elif provider in {"doubao", "volcengine", "ark"}:
        api_key = settings.doubao_api_key
        base_url = settings.doubao_base_url
        model = settings.doubao_model
        provider_name = "doubao"
    elif provider == "custom":
        api_key = settings.llm_api_key
        base_url = settings.llm_base_url
        model = settings.llm_model
        provider_name = "custom"
    else:
        raise ValueError(
            "Unsupported LLM_PROVIDER. Use dashscope, doubao, volcengine, ark, or custom."
        )

    missing = []
    if not api_key:
        missing.append("api key")
    if not base_url:
        missing.append("base url")
    if not model:
        missing.append("model")
    if missing:
        raise ValueError(
            f"LLM provider '{provider_name}' is missing: {', '.join(missing)}."
        )

    return LlmRuntimeConfig(
        provider=provider_name,
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        model=model,
        timeout=timeout,
    )


def create_chat_client() -> AsyncOpenAI:
    """Create an OpenAI-compatible async chat client."""
    cfg = get_llm_runtime_config()
    return AsyncOpenAI(
        api_key=cfg.api_key,
        base_url=cfg.base_url,
        timeout=cfg.timeout,
    )


def get_chat_model(stage: str | None = None) -> str:
    """Return the active chat model name, optionally overridden by stage."""
    stage_models = {
        "plan": settings.llm_model_plan,
        "write": settings.llm_model_write,
        "audit": settings.llm_model_audit,
        "revise": settings.llm_model_revise,
        "archive": settings.llm_model_archive,
    }
    if stage:
        configured = stage_models.get(stage.strip().lower())
        if configured:
            return configured
    return get_llm_runtime_config().model


def get_chat_provider() -> str:
    """Return the active provider name for logging or diagnostics."""
    return get_llm_runtime_config().provider
