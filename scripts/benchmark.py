from __future__ import annotations

import time
import tracemalloc

from backend.models import TrendFeatures, TrendObservation
from backend.quant.clustering import cluster_observations
from backend.quant.scoring import compute_trend_score


def benchmark_scoring() -> dict:
    features = TrendFeatures(80, 70, 75, 88, 12, 82, 91)
    started = time.perf_counter()
    for _ in range(250_000):
        compute_trend_score(features)
    return {
        "workload": "250k_scores",
        "seconds": round(time.perf_counter() - started, 3),
    }


def benchmark_clustering() -> dict:
    now = time.time()
    observations = [
        TrendObservation(
            source=f"source-{index % 4}",
            external_id=str(index),
            title=f"robot boxing clip {index % 10}",
            text="humanoid robot boxing reaction meme",
            url="",
            author="",
            created_at=now,
            engagement=float(index % 50),
        )
        for index in range(1000)
    ]

    tracemalloc.start()
    started = time.perf_counter()
    clusters = cluster_observations(
        observations,
        max_clusters=60,
        max_observations=240,
    )
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "workload": "cluster_240_of_1000",
        "seconds": round(elapsed, 3),
        "clusters": len(clusters),
        "peak_mb": round(peak / 1024 / 1024, 3),
    }


if __name__ == "__main__":
    print(benchmark_scoring())
    print(benchmark_clustering())
