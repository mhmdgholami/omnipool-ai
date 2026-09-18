import asyncio

from backend.services.dexscreener import DexScreenerAdapter
from backend.services.http import external_http


def test_malformed_dex_items_are_ignored(monkeypatch):
    calls = 0

    async def fake_request(method, url, **kwargs):
        nonlocal calls
        calls += 1
        return [
            {"chainId": 42, "description": ["wrong types"]},
            {
                "chainId": "ethereum",
                "description": "not solana",
            },
            {
                "chainId": "solana",
                "tokenAddress": "abc",
                "description": "valid signal",
                "url": "https://example.test/token",
            },
        ]

    monkeypatch.setattr(
        external_http,
        "request_json",
        fake_request,
    )
    adapter = DexScreenerAdapter()

    result = asyncio.run(adapter.scan())

    assert calls == 2
    assert len(result) == 2
    assert all(item["address"] == "abc" for item in result)
