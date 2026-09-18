from __future__ import annotations
from dataclasses import asdict
from backend.models import TrendFeatures

def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return low if value < low else high if value > high else value

def percent_velocity(current: float, previous: float) -> float:
    if current <= 0: return 0.0
    if previous <= 0: return 100.0
    return clamp(((current - previous) / previous) * 100.0)

def acceleration(current_velocity: float, previous_velocity: float) -> float:
    return clamp(50.0 + (current_velocity - previous_velocity) * 0.5)

def freshness_score(age_minutes: float, half_life_minutes: float = 90.0) -> float:
    if age_minutes <= 0: return 100.0
    return clamp(100.0 * (0.5 ** (age_minutes / half_life_minutes)))

def saturation_score(similar_assets: int) -> float:
    return clamp(similar_assets * 8.0)

def compute_trend_score(features: TrendFeatures) -> float:
    score = (
        clamp(features.velocity) * 0.20
        + clamp(features.acceleration) * 0.12
        + clamp(features.cross_source) * 0.16
        + clamp(features.novelty) * 0.16
        + (100.0 - clamp(features.saturation)) * 0.14
        + clamp(features.memeability) * 0.12
        + clamp(features.freshness) * 0.10
    )
    return round(clamp(score), 2)

def opportunity_score(base_score: float, confidence: float, risk: float) -> float:
    return round(clamp(base_score * 0.72 + confidence * 0.28 - risk * 0.22), 2)

def explain_score(features: TrendFeatures) -> dict[str, float]:
    data = asdict(features); data["score"] = compute_trend_score(features)
    return {k: round(float(v), 2) for k, v in data.items()}
