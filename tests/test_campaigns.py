import time
from pathlib import Path

import pytest

from backend.db import Database


def concept() -> dict:
    return {
        "id": "c1",
        "trend_id": "t1",
        "name": "Test",
        "ticker": "TEST",
        "thesis": "A test concept with enough detail.",
        "visual_prompt": "",
        "target_sol": 2.0,
        "novelty_score": 80,
        "momentum_score": 80,
        "saturation_score": 10,
        "risk_flags": [],
        "created_at": 0.0,
    }


def test_campaign_reaches_ready_without_overfunding(tmp_path: Path):
    database = Database(str(tmp_path / "campaign.db"))
    database.init()
    draft = concept()
    database.insert_concept(draft)
    campaign = database.create_campaign(draft, "wallet", 30)

    first = database.contribute(campaign["id"], "w1", 1)
    ready = database.contribute(campaign["id"], "w2", 9)

    assert first["status"] == "funding"
    assert ready["status"] == "ready"
    assert ready["raised_sol"] == 2.0

    rows = database.rows(
        "SELECT amount_lamports FROM contributions WHERE campaign_id=?",
        (campaign["id"],),
    )
    assert sum(row["amount_lamports"] for row in rows) == 2_000_000_000


def test_expired_campaign_rejects_contribution(tmp_path: Path):
    database = Database(str(tmp_path / "expired.db"))
    database.init()
    draft = concept()
    database.insert_concept(draft)
    campaign = database.create_campaign(draft, "wallet", 30)

    database.execute(
        "UPDATE campaigns SET expires_at=? WHERE id=?",
        (time.time() - 1, campaign["id"]),
    )

    with pytest.raises(ValueError, match="campaign_expired"):
        database.contribute(campaign["id"], "w1", 1)
