from __future__ import annotations

from dataclasses import dataclass, field

from backend.models import TrendObservation
from backend.quant.text import canonical_label, jaccard, tokens


@dataclass(slots=True)
class NarrativeCluster:
    label: str
    token_set: frozenset[str]
    observations: list[TrendObservation] = field(default_factory=list)

    @property
    def sources(self) -> set[str]:
        return {observation.source for observation in self.observations}

    @property
    def engagement(self) -> float:
        return sum(
            observation.engagement
            for observation in self.observations
        )


def _best_cluster(
    observation_tokens: frozenset[str],
    clusters: list[NarrativeCluster],
) -> tuple[int, float]:
    best_index = -1
    best_similarity = 0.0

    for index, cluster in enumerate(clusters):
        similarity = jaccard(observation_tokens, cluster.token_set)
        if similarity > best_similarity:
            best_index = index
            best_similarity = similarity

    return best_index, best_similarity


def cluster_observations(
    observations: list[TrendObservation],
    threshold: float = 0.34,
    max_clusters: int = 60,
    max_observations: int = 240,
) -> list[NarrativeCluster]:
    clusters: list[NarrativeCluster] = []
    ordered = sorted(
        observations[:max_observations],
        key=lambda observation: (
            observation.engagement,
            observation.created_at,
        ),
        reverse=True,
    )

    for observation in ordered:
        observation_tokens = tokens(
            f"{observation.title} {observation.text}"
        )
        if not observation_tokens:
            continue

        best_index, best_similarity = _best_cluster(
            observation_tokens,
            clusters,
        )

        if best_index >= 0 and best_similarity >= threshold:
            cluster = clusters[best_index]
            cluster.observations.append(observation)
            merged = set(cluster.token_set)
            merged.update(observation_tokens)
            cluster.token_set = frozenset(sorted(merged)[:40])
            continue

        if len(clusters) < max_clusters:
            clusters.append(
                NarrativeCluster(
                    label=canonical_label(
                        observation.title,
                        observation.text,
                    ),
                    token_set=observation_tokens,
                    observations=[observation],
                )
            )

    clusters.sort(
        key=lambda cluster: (
            len(cluster.sources),
            len(cluster.observations),
            cluster.engagement,
        ),
        reverse=True,
    )
    return clusters
