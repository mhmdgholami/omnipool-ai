import time

from backend.models import TrendObservation
from backend.quant.clustering import cluster_observations


def test_clustering_is_bounded():
    now = time.time()
    observations = [
        TrendObservation(
            source="source-a",
            external_id=str(index),
            title=f"robot boxing clip {index % 4}",
            text="humanoid robot boxing reaction meme",
            url="",
            author="",
            created_at=now,
            engagement=float(index),
        )
        for index in range(1000)
    ]

    clusters = cluster_observations(
        observations,
        max_clusters=20,
        max_observations=120,
    )

    assert len(clusters) <= 20
    assert sum(len(cluster.observations) for cluster in clusters) <= 120
