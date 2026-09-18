from __future__ import annotations
import time
from backend.db import db

def list_campaigns() -> list[dict]:
    db.execute("UPDATE campaigns SET status='expired' WHERE status='funding' AND expires_at<=?", (time.time(),))
    return db.rows("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 100")

def graduate(campaign_id: str) -> dict:
    campaign = db.row("SELECT * FROM campaigns WHERE id=?", (campaign_id,))
    if not campaign: raise KeyError("campaign_not_found")
    if campaign['status'] != 'ready': raise ValueError("campaign_not_ready")
    db.execute("UPDATE campaigns SET status='live' WHERE id=?", (campaign_id,))
    return db.row("SELECT * FROM campaigns WHERE id=?", (campaign_id,)) or {}

def refund(campaign_id: str, wallet: str) -> dict:
    campaign = db.row("SELECT * FROM campaigns WHERE id=?", (campaign_id,))
    if not campaign: raise KeyError("campaign_not_found")
    if campaign['status'] not in ('expired','refunding'): raise ValueError("campaign_not_refundable")
    rows = db.rows("SELECT * FROM contributions WHERE campaign_id=? AND wallet=? AND status='committed'", (campaign_id,wallet))
    amount = sum(r['amount_sol'] for r in rows)
    if amount <= 0: raise ValueError("nothing_to_refund")
    db.execute("UPDATE contributions SET status='refunded' WHERE campaign_id=? AND wallet=? AND status='committed'", (campaign_id,wallet))
    return {'campaign_id': campaign_id, 'wallet': wallet, 'refunded_sol': round(amount, 9)}
