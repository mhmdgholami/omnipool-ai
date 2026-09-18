from __future__ import annotations
from dataclasses import dataclass
from pydantic import BaseModel, Field

@dataclass(frozen=True, slots=True)
class TrendFeatures:
    velocity: float
    acceleration: float
    cross_source: float
    novelty: float
    saturation: float
    memeability: float
    freshness: float

class GenerateRequest(BaseModel):
    trend_id: str | None = None
    title: str | None = None
    summary: str | None = None

class CampaignCreate(BaseModel):
    concept_id: str
    creator_wallet: str = Field(min_length=3, max_length=128)
    duration_minutes: int = Field(default=30, ge=5, le=1440)

class ContributionCreate(BaseModel):
    wallet: str = Field(min_length=3, max_length=128)
    amount_sol: float = Field(gt=0, le=10_000)
