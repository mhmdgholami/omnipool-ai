from __future__ import annotations

from backend.ai.config import ai_settings
from backend.config import settings


def source_status() -> list[dict]:
    hosted_configured = bool(
        (ai_settings.enable_groq and ai_settings.groq_api_key)
        or (
            ai_settings.enable_openrouter
            and ai_settings.openrouter_api_key
        )
    )
    return [
        {
            "id": "dexscreener",
            "label": "DEX Screener",
            "mode": "live",
            "configured": True,
            "detail": "Public Solana market signals",
        },
        {
            "id": "ai",
            "label": "AI engine",
            "mode": "local-first",
            "configured": True,
            "detail": (
                "Ollama first; optional free hosted failover; "
                "deterministic fallback if no model is available"
            ),
        },
        {
            "id": "hosted-ai",
            "label": "Hosted AI fallback",
            "mode": "optional",
            "configured": hosted_configured,
            "detail": "Groq/OpenRouter credentials are optional",
        },
        {
            "id": "x",
            "label": "X",
            "mode": "configured" if settings.x_bearer_token else "adapter",
            "configured": bool(settings.x_bearer_token),
            "detail": "Credential slot reserved for a filtered-stream adapter",
        },
        {
            "id": "reddit",
            "label": "Reddit",
            "mode": (
                "configured"
                if settings.reddit_client_id
                and settings.reddit_client_secret
                else "adapter"
            ),
            "configured": bool(
                settings.reddit_client_id
                and settings.reddit_client_secret
            ),
            "detail": "Credential slot reserved for a Developer API adapter",
        },
        {
            "id": "solana",
            "label": "Solana",
            "mode": "devnet-plan",
            "configured": bool(settings.solana_rpc_url),
            "detail": (
                "Graduation planning only; the server never signs "
                "the user wallet"
            ),
        },
    ]
