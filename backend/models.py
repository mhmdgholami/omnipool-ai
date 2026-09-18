from __future__ import annotations
from dataclasses import dataclass
from pydantic import BaseModel, Field, model_validator

@dataclass(frozen=True, slots=True)
class TrendFeatures:
    velocity: float
    acceleration: float
    cross_source: float
    novelty: float
    saturation: float
    memeability: float
    freshness: float

@dataclass(frozen=True, slots=True)
class TrendObservation:
    source: str
    external_id: str
    title: str
    text: str
    url: str
    author: str
    created_at: float
    engagement: float

class GenerateRequest(BaseModel):
    trend_id: str | None = None
    title: str | None = Field(default=None, max_length=100)
    summary: str | None = Field(default=None, max_length=600)

    @model_validator(mode="after")
    def has_input(self):
        if not self.trend_id and not self.title:
            raise ValueError("trend_id_or_title_required")
        return self

class MarketCheckRequest(BaseModel):
    query: str = Field(min_length=2, max_length=80)

class CampaignCreate(BaseModel):
    concept_id: str
    creator_wallet: str = Field(min_length=3, max_length=128)
    duration_minutes: int = Field(default=30, ge=5, le=1440)
    risk_acknowledged: bool = True

class ContributionCreate(BaseModel):
    wallet: str = Field(min_length=3, max_length=128)
    amount_sol: float = Field(gt=0, le=10_000)
