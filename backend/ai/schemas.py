from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class TaskKind(StrEnum):
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    GENERATION = "generation"
    REASONING = "reasoning"
    CODING = "coding"


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system: str = Field(default="", max_length=4000)
    task: TaskKind = TaskKind.GENERATION
    max_tokens: int = Field(default=600, ge=32, le=4096)
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    json_mode: bool = False
    model: str | None = None


class GenerationResult(BaseModel):
    text: str
    provider: str
    model: str
    latency_ms: float
    input_tokens_estimate: int
    output_tokens_estimate: int
    fallback_index: int = 0


class ProviderHealth(BaseModel):
    provider: str
    available: bool
    detail: str
    models: list[str] = Field(default_factory=list)


class EmbeddingResult(BaseModel):
    embeddings: list[list[float]]
    provider: str
    model: str
