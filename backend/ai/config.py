from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class AISettings:
    primary_provider: str = field(
        default_factory=lambda: os.getenv("AI_PRIMARY_PROVIDER", "ollama").lower()
    )
    allow_paid_providers: bool = field(
        default_factory=lambda: _env_bool("AI_ALLOW_PAID_PROVIDERS", False)
    )
    enable_ollama: bool = field(
        default_factory=lambda: _env_bool("AI_ENABLE_OLLAMA", True)
    )
    enable_groq: bool = field(
        default_factory=lambda: _env_bool("AI_ENABLE_GROQ", True)
    )
    enable_openrouter: bool = field(
        default_factory=lambda: _env_bool("AI_ENABLE_OPENROUTER", True)
    )
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv(
            "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
        ).rstrip("/")
    )
    groq_base_url: str = field(
        default_factory=lambda: os.getenv(
            "GROQ_BASE_URL", "https://api.groq.com/openai/v1"
        ).rstrip("/")
    )
    openrouter_base_url: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).rstrip("/")
    )
    groq_api_key: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY", "")
    )
    openrouter_api_key: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "")
    )
    fast_model: str = field(
        default_factory=lambda: os.getenv("AI_FAST_MODEL", "qwen3:1.7b")
    )
    general_model: str = field(
        default_factory=lambda: os.getenv("AI_GENERAL_MODEL", "qwen3:4b")
    )
    reasoning_model: str = field(
        default_factory=lambda: os.getenv("AI_REASONING_MODEL", "qwen3:4b")
    )
    coding_model: str = field(
        default_factory=lambda: os.getenv(
            "AI_CODING_MODEL", "qwen2.5-coder:3b"
        )
    )
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "AI_EMBEDDING_MODEL", "nomic-embed-text"
        )
    )
    groq_model: str = field(
        default_factory=lambda: os.getenv(
            "GROQ_MODEL", "openai/gpt-oss-20b"
        )
    )
    openrouter_model: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_MODEL", "openrouter/free"
        )
    )
    timeout_seconds: float = field(
        default_factory=lambda: _env_float("AI_TIMEOUT_SECONDS", 20.0)
    )
    health_ttl_seconds: float = field(
        default_factory=lambda: _env_float("AI_HEALTH_TTL_SECONDS", 20.0)
    )
    health_timeout_seconds: float = field(
        default_factory=lambda: _env_float(
            "AI_HEALTH_TIMEOUT_SECONDS",
            1.5,
        )
    )
    max_retries: int = field(
        default_factory=lambda: max(0, min(2, _env_int("AI_MAX_RETRIES", 1)))
    )
    max_concurrency: int = field(
        default_factory=lambda: max(1, _env_int("AI_MAX_CONCURRENCY", 2))
    )
    queue_timeout_seconds: float = field(
        default_factory=lambda: _env_float("AI_QUEUE_TIMEOUT_SECONDS", 5.0)
    )
    max_input_chars: int = field(
        default_factory=lambda: max(
            1000, _env_int("AI_MAX_INPUT_CHARS", 12_000)
        )
    )
    max_output_tokens: int = field(
        default_factory=lambda: max(
            64, _env_int("AI_MAX_OUTPUT_TOKENS", 900)
        )
    )

    def local_model_for_task(self, task: str) -> str:
        return {
            "classification": self.fast_model,
            "extraction": self.fast_model,
            "generation": self.general_model,
            "reasoning": self.reasoning_model,
            "coding": self.coding_model,
        }.get(task, self.general_model)


ai_settings = AISettings()
