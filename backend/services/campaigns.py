from __future__ import annotations

from backend.db import db


def list_campaigns() -> list[dict]:
    db.expire_campaigns()
    return db.list_campaigns(limit=100)


def graduate(campaign_id: str) -> dict:
    return db.graduate_campaign(campaign_id)


def refund(campaign_id: str, wallet: str) -> dict:
    return db.refund_campaign(campaign_id, wallet)
