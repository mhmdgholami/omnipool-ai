from backend.quant.risk import risk_flags, risk_score, trend_confidence


def test_sensitive_event_is_flagged():
    confidence = trend_confidence(
        source_count=3,
        evidence_count=5,
        cross_source=80,
        freshness=90,
    )
    flags = risk_flags(
        "Breaking attack",
        "Victims reported after an attack",
        saturation=15,
        confidence=confidence,
        source_count=3,
    )

    assert "sensitive_event" in flags
    assert risk_score(flags, saturation=15, confidence=confidence) >= 45
