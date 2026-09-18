from __future__ import annotations

import os
from dataclasses import dataclass


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = _int("PORT", 8000)
    database_path: str = os.getenv("DATABASE_PATH", "./omnipool.db")

    dexscreener_base_url: str = os.getenv(
        "DEXSCREENER_BASE_URL",
        "https://api.dexscreener.com",
    )
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "")
    x_query: str = os.getenv(
        "X_QUERY",
        "(meme OR viral OR trending OR launch) -is:retweet lang:en",
    )
    reddit_client_id: str = os.getenv("REDDIT_CLIENT_ID", "")
    reddit_client_secret: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    reddit_user_agent: str = os.getenv(
        "REDDIT_USER_AGENT",
        "omnipool-ai/0.4",
    )
    news_rss_url: str = os.getenv(
        "NEWS_RSS_URL",
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    )

    solana_rpc_url: str = os.getenv(
        "SOLANA_RPC_URL",
        "https://api.devnet.solana.com",
    )
    solana_cluster: str = os.getenv("SOLANA_CLUSTER", "devnet")

    max_trends: int = _int("MAX_TRENDS", 100)
    max_observations_per_scan: int = _int("MAX_OBSERVATIONS_PER_SCAN", 240)
    cache_ttl_seconds: int = _int("CACHE_TTL_SECONDS", 30)
    market_cache_size: int = _int("MARKET_CACHE_SIZE", 64)
    market_cache_ttl_seconds: int = _int("MARKET_CACHE_TTL_SECONDS", 120)

    request_timeout_seconds: float = _float("REQUEST_TIMEOUT_SECONDS", 8.0)
    max_request_bytes: int = _int("MAX_REQUEST_BYTES", 65_536)
    rate_limit_per_minute: int = _int("RATE_LIMIT_PER_MINUTE", 120)
    max_rate_limit_clients: int = _int("MAX_RATE_LIMIT_CLIENTS", 2_000)

    enable_demo_seeds: bool = _bool("ENABLE_DEMO_SEEDS", True)
    scan_on_startup: bool = _bool("SCAN_ON_STARTUP", True)


settings = Settings()
