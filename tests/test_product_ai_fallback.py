import asyncio

from backend.ai.exceptions import AllProvidersUnavailable
from backend.services import ai as product_ai


def trend() -> dict:
    return {
        "id": "trend-1",
        "title": "Robot Boxing",
        "summary": "Humanoid robot fighting clips are spreading.",
        "score": 80,
        "confidence": 70,
        "risk": 15,
        "novelty": 85,
        "saturation": 10,
        "risk_flags": [],
    }


def test_product_generation_survives_all_provider_failure(monkeypatch):
    async def unavailable(*args, **kwargs):
        raise AllProvidersUnavailable("offline")

    monkeypatch.setattr(
        product_ai,
        "generate_structured",
        unavailable,
    )
    monkeypatch.setattr(
        product_ai.db,
        "insert_concept",
        lambda concept: None,
    )

    concepts = asyncio.run(
        product_ai.generate_concepts(trend())
    )

    assert len(concepts) == 3
    assert all(
        "deterministic_fallback" in item["risk_flags"]
        for item in concepts
    )
