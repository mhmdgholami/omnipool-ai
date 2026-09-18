from __future__ import annotations
import os
from dataclasses import dataclass

def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = _int("PORT", 8000)
    database_path: str = os.getenv("DATABASE_PATH", "./omnipool.db")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    dexscreener_base_url: str = os.getenv("DEXSCREENER_BASE_URL", "https://api.dexscreener.com")
    solana_rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
    solana_cluster: str = os.getenv("SOLANA_CLUSTER", "devnet")
    max_trends: int = _int("MAX_TRENDS", 100)
    cache_ttl_seconds: int = _int("CACHE_TTL_SECONDS", 30)

settings = Settings()
