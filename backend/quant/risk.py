from __future__ import annotations

import re

_SENSITIVE = re.compile(
    r"\b(death|dead|killed|attack|shooting|war|earthquake|disaster|"
    r"victim|hostage|suicide|tragedy)\b",
    re.IGNORECASE,
)
_IMPERSONATION = re.compile(
    r"\b(official|foundation|president|ceo|company|inc|corp|support team)\b",
    re.IGNORECASE,
)
_RISK_WEIGHTS = {
    "sensitive_event": 45,
    "impersonation_review": 25,
    "high_token_saturation": 20,
    "low_evidence_confidence": 18,
    "single_source_signal": 12,
}


def trend_confidence(
    source_count: int,
    evidence_count: int,
    cross_source: float,
    freshness: float,
) -> float:
    score = (
        22
        + min(source_count, 4) * 13
        + min(evidence_count, 8) * 4
        + cross_source * 0.16
        + freshness * 0.09
    )
    return round(max(0.0, min(100.0, score)), 2)


def risk_flags(
    title: str,
    summary: str,
    saturation: float,
    confidence: float,
    source_count: int,
) -> list[str]:
    text = f"{title} {summary}"
    flags: list[str] = []

    if _SENSITIVE.search(text):
        flags.append("sensitive_event")
    if _IMPERSONATION.search(text):
        flags.append("impersonation_review")
    if saturation >= 65:
        flags.append("high_token_saturation")
    if confidence < 45:
        flags.append("low_evidence_confidence")
    if source_count <= 1:
        flags.append("single_source_signal")

    return flags[:8]


def risk_score(
    flags: list[str],
    saturation: float,
    confidence: float,
) -> float:
    flag_score = sum(_RISK_WEIGHTS.get(flag, 8) for flag in flags)
    score = (
        flag_score
        + saturation * 0.18
        + max(0.0, 50.0 - confidence) * 0.25
    )
    return round(max(0.0, min(100.0, score)), 2)
