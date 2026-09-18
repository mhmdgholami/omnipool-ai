from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

from backend.config import settings


@dataclass(frozen=True, slots=True)
class GraduationPlan:
    plan_id: str
    campaign_id: str
    cluster: str
    contributor_supply_pct: int = 50
    liquidity_supply_pct: int = 50
    creator_genesis_pct: int = 0
    platform_genesis_pct: int = 0
    mint_authority_after: str = "revoked"
    freeze_authority_after: str = "revoked"
    server_signs_user_wallet: bool = False


def build_graduation_plan(campaign_id: str) -> dict:
    digest = hashlib.blake2s(
        f"omnipool:v1:{settings.solana_cluster}:{campaign_id}".encode(),
        digest_size=16,
    ).hexdigest()
    plan = GraduationPlan(
        plan_id=digest,
        campaign_id=campaign_id,
        cluster=settings.solana_cluster,
    )
    return asdict(plan)
