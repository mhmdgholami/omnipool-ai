from __future__ import annotations

from backend.config import settings


def source_status() -> list[dict]:
    return [
        {
            "id": "dexscreener",
            "label": "DEX Screener",
            "mode": "live",
            "configured": True,
            "detail": "Public Solana market signals",
        },
        {
            "id": "openai",
            "label": "OpenAI",
            "mode": "live" if settings.openai_api_key else "fallback",
            "configured": bool(settings.openai_api_key),
            "detail": "Server-side concept generation",
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
                if settings.reddit_client_id and settings.reddit_client_secret
                else "adapter"
            ),
            "configured": bool(
                settings.reddit_client_id and settings.reddit_client_secret
            ),
            "detail": "Credential slot reserved for a Developer API adapter",
        },
        {
            "id": "solana",
            "label": "Solana",
            "mode": "devnet-plan",
            "configured": bool(settings.solana_rpc_url),
            "detail": "Graduation planning only; the server never signs the user wallet",
        },
    ]
