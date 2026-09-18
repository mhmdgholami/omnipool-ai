from __future__ import annotations
from dataclasses import dataclass, field
from backend.models import TrendObservation
from backend.quant.text import tokens, jaccard, canonical_label

@dataclass(slots=True)
class NarrativeCluster:
    label: str
    token_set: frozenset[str]
    observations: list[TrendObservation] = field(default_factory=list)

    @property
    def sources(self) -> set[str]:
        return {x.source for x in self.observations}

    @property
    def engagement(self) -> float:
        return sum(x.engagement for x in self.observations)

def cluster_observations(observations: list[TrendObservation], threshold: float = 0.34, max_clusters: int = 60, max_observations: int = 240) -> list[NarrativeCluster]:
    clusters: list[NarrativeCluster] = []
    ordered = sorted(observations[:max_observations], key=lambda x: (x.engagement, x.created_at), reverse=True)
    for obs in ordered:
        obs_tokens=tokens(obs.title+" "+obs.text)
        if not obs_tokens: continue
        best_i=-1; best=0.0
        for i,c in enumerate(clusters):
            sim=jaccard(obs_tokens,c.token_set)
            if sim > best: best_i=i; best=sim
        if best_i >= 0 and best >= threshold:
            c=clusters[best_i]; c.observations.append(obs)
            merged=set(c.token_set); merged.update(obs_tokens)
            c.token_set=frozenset(list(merged)[:40])
        elif len(clusters) < max_clusters:
            clusters.append(NarrativeCluster(canonical_label(obs.title,obs.text),obs_tokens,[obs]))
    clusters.sort(key=lambda c:(len(c.sources),len(c.observations),c.engagement),reverse=True)
    return clusters
