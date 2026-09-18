from decimal import Decimal
from pathlib import Path

from backend.db import Database


def concept():
    return {
        "id": "concept-1",
        "trend_id": "trend-1",
        "name": "Retry Safe",
        "ticker": "RETRY",
        "thesis": "Retry semantics should not duplicate money.",
        "visual_prompt": "",
        "target_sol": 2.0,
        "novelty_score": 80,
        "momentum_score": 80,
        "saturation_score": 10,
        "risk_flags": [],
        "created_at": 0.0,
    }


def test_contribution_idempotency(tmp_path: Path):
    database = Database(str(tmp_path / "idempotency.db"))
    database.init()
    draft = concept()
    database.insert_concept(draft)
    campaign = database.create_campaign(draft, "wallet-a", 30)

    first = database.contribute(
        campaign["id"],
        "wallet-b",
        Decimal("1"),
        "request-1234",
    )
    replay = database.contribute(
        campaign["id"],
        "wallet-b",
        Decimal("1"),
        "request-1234",
    )

    assert first["raised_sol"] == 1.0
    assert replay["raised_sol"] == 1.0
    assert replay["accepted_sol"] == 1.0
    assert replay["idempotent_replay"] is True


def test_graduation_is_idempotent(tmp_path: Path):
    database = Database(str(tmp_path / "graduation.db"))
    database.init()
    draft = concept()
    database.insert_concept(draft)
    campaign = database.create_campaign(draft, "wallet-a", 30)

    database.contribute(campaign["id"], "wallet-b", Decimal("2"), "fund-once")
    first = database.graduate_campaign(campaign["id"])
    replay = database.graduate_campaign(campaign["id"])

    assert first["status"] == "live"
    assert replay["status"] == "live"
