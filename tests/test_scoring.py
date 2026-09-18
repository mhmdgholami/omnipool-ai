from backend.models import TrendFeatures
from backend.quant.scoring import compute_trend_score, freshness_score, percent_velocity

def test_velocity():
    assert percent_velocity(20, 10) == 100
    assert percent_velocity(5, 10) == 0

def test_freshness_decays():
    assert freshness_score(10) > freshness_score(100)

def test_less_saturation_scores_better():
    a = TrendFeatures(80, 70, 70, 80, 5, 80, 90)
    b = TrendFeatures(80, 70, 70, 80, 80, 80, 90)
    assert compute_trend_score(a) > compute_trend_score(b)
