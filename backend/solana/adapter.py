from __future__ import annotations
from dataclasses import dataclass,asdict
from backend.config import settings

@dataclass(frozen=True,slots=True)
class GraduationPlan:
    campaign_id:str
    cluster:str
    rpc_url:str
    contributor_supply_pct:int=50
    liquidity_supply_pct:int=50
    creator_genesis_pct:int=0
    platform_genesis_pct:int=0
    mint_authority_after:str='revoked'
    freeze_authority_after:str='revoked'

def build_graduation_plan(campaign_id):
    return asdict(GraduationPlan(campaign_id,settings.solana_cluster,settings.solana_rpc_url))
