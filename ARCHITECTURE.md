# Architecture

## Principles

OMNIPOOL uses deterministic algorithms for work that does not need a language model. AI is reserved for tasks where generation, extraction or reasoning adds value.

The core must remain usable without internet access or hosted AI accounts.

## Request path

    Browser
      |
      v
    FastAPI
      |
      +-- quantitative trend engine
      |
      +-- product AI service
      |      |
      |      v
      |    AI Router
      |      |-- Ollama
      |      |-- Groq (optional)
      |      '-- OpenRouter free models (optional)
      |
      +-- Proof-of-Demand state machine
      |
      '-- SQLite

Provider-specific code is isolated under `backend/ai/providers/`.

Business logic imports application-level AI services, never provider classes.

## AI routing

The router enforces:

- bounded input size;
- bounded output tokens;
- global AI concurrency;
- queue timeout;
- request timeout;
- finite exponential retry;
- provider failover;
- cached provider health;
- free-model policy.

Task type affects local model selection:

- classification -> fast model;
- extraction -> fast model;
- generation -> general model;
- reasoning -> reasoning model;
- coding -> coding model.

Ollama dynamically discovers locally installed models. It tries the configured compatible local model and may fall back to another installed generation model. Embeddings are stricter: a missing embedding model fails explicitly instead of routing text through a generation-only model.

## Structured outputs

Structured application flows use Pydantic schemas.

The sequence is:

    generate JSON
      -> parse
      -> Pydantic validation
      -> one bounded repair attempt
      -> safe failure

Malformed AI output never reaches campaign persistence as trusted structure.

## Product fallback

Provider failure must not make the whole product unavailable.

For launch-concept generation:

    AI router unavailable
      -> deterministic concept generator
      -> same validated application data shape

The fallback is intentionally product-specific. The generic AI router itself does not fabricate model output when no provider exists.

## Data representation

Money is integer lamports.

Floating point is acceptable for non-financial scores, but not balances, accepted contributions, or funding targets.

Campaign writes use transactions and unique idempotency keys.

## Resource bounds

Current default bounds include:

- 240 observations per scan;
- 60 narrative clusters;
- 100 trends returned/stored in hot lists;
- 64 DEX cache items;
- 2 concurrent AI generations;
- 12,000 AI input characters;
- 900 AI output tokens;
- 2,000 rate-limit client buckets;
- 64 KiB request bodies.

The narrative clustering path remains intentionally bounded O(n*k). A vector database is not justified at the current scale.

## Database

SQLite is appropriate for the single-replica alpha.

It is the operational source of truth for campaigns and contributions.

Do not run multiple API replicas against separate SQLite files.

If real traffic requires horizontal API scaling, migrate durable campaign state to PostgreSQL first. A vector database is not required for that migration.

## Scaling path

### Stage 0

- one FastAPI process;
- SQLite;
- bounded in-memory caches;
- local Ollama or deterministic fallback.

### Stage 1

- PostgreSQL for durable multi-replica state;
- edge/distributed rate limiting only if multiple API instances require it.

### Stage 2

If ingestion throughput justifies it, separate source ingestion from request serving with a durable queue or event log.

Do not add Kafka, Redis, Kubernetes or a warehouse before measurements justify them.

### Stage 3

For very large historical event volumes, move analytics to a columnar system while keeping transactional campaign state relational.

## Consistency

Campaign funding needs strong transactional consistency.

Trend intelligence is eventually consistent.

A trend may be seconds stale. A contribution must never be counted twice.

## External I/O

All outbound HTTP uses one shared `httpx.AsyncClient` with bounded connections and timeouts.

Provider SDKs are deliberately avoided because plain HTTP already covers the required APIs and keeps dependency/runtime cost lower.

## Observability

Observability is local and free:

- Python logging;
- request IDs;
- route latency;
- provider name;
- model name;
- approximate token counts;
- fallback index;
- failure categories.

Prompts and API keys are not logged.
