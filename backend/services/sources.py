from __future__ import annotations
import os
from backend.config import settings

def source_status() -> list[dict]:
    return [
        {'id':'dexscreener','label':'DEX Screener','mode':'live','configured':True,'detail':'Public Solana market signals'},
        {'id':'openai','label':'OpenAI','mode':'live' if settings.openai_api_key else 'fallback','configured':bool(settings.openai_api_key),'detail':'Server-side concept generation'},
        {'id':'x','label':'X','mode':'adapter','configured':bool(os.getenv('X_BEARER_TOKEN')),'detail':'Filtered stream/webhook adapter slot'},
        {'id':'reddit','label':'Reddit','mode':'adapter','configured':bool(os.getenv('REDDIT_CLIENT_ID')),'detail':'Developer API adapter slot'},
        {'id':'solana','label':'Solana','mode':'devnet-plan','configured':bool(settings.solana_rpc_url),'detail':'Graduation plan only; no server signing'},
    ]
