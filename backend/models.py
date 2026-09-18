from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

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
    def validate_input(self) -> GenerateRequest:
        if not self.trend_id and not self.title:
            raise ValueError("trend_id_or_title_required")
        return self


class CampaignCreate(BaseModel):
    concept_id: str
    creator_wallet: str = Field(min_length=3, max_length=128)
    duration_minutes: int = Field(default=30, ge=5, le=1440)
    risk_acknowledged: bool = False


class ContributionCreate(BaseModel):
    wallet: str = Field(min_length=3, max_length=128)
    amount_sol: Decimal = Field(gt=0, le=10_000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)
