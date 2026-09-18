from __future__ import annotations
import asyncio, time
import httpx
from backend.config import settings

class DexScreenerAdapter:
    def __init__(self) -> None:
        self._cache: list[dict] = []
        self._cached_at = 0.0
        self._lock = asyncio.Lock()

    async def scan(self) -> list[dict]:
        now = time.monotonic()
        if self._cache and now - self._cached_at < settings.cache_ttl_seconds:
            return self._cache
        async with self._lock:
            now = time.monotonic()
            if self._cache and now - self._cached_at < settings.cache_ttl_seconds:
                return self._cache
            timeout = httpx.Timeout(5.0, connect=3.0)
            limits = httpx.Limits(max_connections=4, max_keepalive_connections=2)
            async with httpx.AsyncClient(timeout=timeout, limits=limits, headers={'User-Agent':'omnipool-ai/0.1'}) as client:
                urls = [f'{settings.dexscreener_base_url}/token-boosts/top/v1', f'{settings.dexscreener_base_url}/token-profiles/latest/v1']
                results = await asyncio.gather(*(client.get(u) for u in urls), return_exceptions=True)
            out=[]
            for kind,response in zip(('boost','profile'),results):
                if isinstance(response, Exception) or response.status_code != 200:
                    continue
                data=response.json()
                if not isinstance(data,list):
                    continue
                for item in data[:30]:
                    if item.get('chainId')!='solana':
                        continue
                    text=(item.get('description') or 'Solana token signal').strip()
                    out.append({'external_id':item.get('tokenAddress') or item.get('url') or text,'title':text[:72],'summary':text[:240],'kind':kind,'address':item.get('tokenAddress',''),'url':item.get('url','')})
            self._cache=out[:40]
            self._cached_at=time.monotonic()
            return self._cache

dex_adapter=DexScreenerAdapter()
