# OMNIPOOL AI

OMNIPOOL is a low-overhead trend intelligence and Proof-of-Demand platform for Solana-native launch concepts.

The core product is designed to run at **€0/month** on a developer machine. No paid AI API, paid vector database, paid monitoring service, or paid database is required.

## What the alpha does

1. collects bounded market observations;
2. clusters them into narratives;
3. scores opportunity, evidence confidence, saturation and launch risk;
4. generates three launch concepts through a provider-independent AI router;
5. falls back to deterministic generation if every AI provider is unavailable;
6. lets a community test demand before a graduation plan is produced.

The server never signs a user's wallet.

## Architecture

    Browser
      |
      v
    FastAPI
      |-- trend ingestion + quantitative scoring
      |-- AI router
      |     |-- Ollama (primary, local)
      |     |-- Groq (optional hosted free-tier)
      |     |-- OpenRouter free models (optional)
      |     '-- controlled failure / deterministic product fallback
      |-- Proof-of-Demand campaign state machine
      '-- SQLite

Application code never talks directly to Groq, OpenRouter or Ollama. Product services call the AI router.

Financial state uses integer lamports. Scores may use floating point.

## Running Completely Free

### Option A: local Python + local Ollama

Install Python 3.11 or newer and Ollama.

Create the environment:

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -e '.[dev]'
    mkdir -p data
    export DATABASE_PATH=./data/omnipool.db

Start Ollama in another terminal:

    ollama serve

Install one lightweight generation model:

    ollama pull qwen3:1.7b

For higher-quality local generation on hardware with more RAM:

    ollama pull qwen3:4b

Optional local embedding model:

    ollama pull nomic-embed-text

Start OMNIPOOL:

    uvicorn backend.app:app --host 127.0.0.1 --port 8000

Open:

    http://127.0.0.1:8000

No API key is required.

If Ollama is stopped, the website still works. Concept generation falls back to deterministic logic rather than crashing.

### Option B: Docker

Run the application only:

    docker compose up --build app

Run the application plus CPU-capable Ollama:

    docker compose --profile local-ai up --build -d

Then install a model inside the Ollama container:

    docker compose exec ollama ollama pull qwen3:1.7b

No GPU is required.

## AI provider order

Default order:

1. Ollama
2. Groq, only when a key is configured
3. OpenRouter, only when a key is configured and the model is explicitly free
4. deterministic product fallback

Paid OpenRouter model slugs are blocked in code.

The hosted providers are accelerators, not dependencies. Their free quotas, model lists and rate limits may change without notice.

## Recommended local models

The defaults prioritize ordinary consumer hardware rather than maximum benchmark performance:

- classification / extraction: `qwen3:1.7b`
- general generation: `qwen3:4b`
- reasoning: `qwen3:4b`
- coding: `qwen2.5-coder:3b`
- embeddings: `nomic-embed-text`

Models are **not downloaded automatically**. Change any model with environment variables without editing application code.

## Optional Groq setup

For local Python, export:

    export GROQ_API_KEY=...
    export AI_ENABLE_GROQ=true

For Docker Compose, place the same values in a local `.env` file; Compose forwards them to the app container.

The default configured model is:

    GROQ_MODEL=openai/gpt-oss-20b

Groq is optional. If the key is absent, rate-limited, offline, or its model becomes unavailable, the router continues to the next provider.

## Optional OpenRouter setup

For local Python, export:

    export OPENROUTER_API_KEY=...
    export AI_ENABLE_OPENROUTER=true
    export OPENROUTER_MODEL=openrouter/free

For Docker Compose, the same values may live in a local `.env` file.

The code only permits `openrouter/free` or model slugs ending in `:free`.

## Environment variables

`.env.example` is the configuration reference. The Python application intentionally does not auto-parse dotenv files, which avoids another runtime dependency. For local Python runs, export only the variables you want to override. Docker Compose can read a local `.env` file for variable substitution.

Important AI controls:

    AI_PRIMARY_PROVIDER=ollama
    AI_ALLOW_PAID_PROVIDERS=false
    AI_ENABLE_OLLAMA=true
    AI_ENABLE_GROQ=true
    AI_ENABLE_OPENROUTER=true
    OLLAMA_BASE_URL=http://127.0.0.1:11434
    AI_TIMEOUT_SECONDS=20
    AI_MAX_RETRIES=1
    AI_MAX_CONCURRENCY=2
    AI_MAX_INPUT_CHARS=12000
    AI_MAX_OUTPUT_TOKENS=900

The paid-provider flag is retained for explicit configuration visibility, but the current OpenRouter implementation remains free-model-only.

## API

Useful endpoints:

    GET  /api/health
    GET  /api/v1/trends
    POST /api/v1/trends/scan
    POST /api/v1/generate
    GET  /api/v1/ai/status
    GET  /api/v1/campaigns

The frontend never selects an AI provider directly.

## Tests

All default tests are offline and use mocked providers.

Run:

    ruff check backend tests scripts
    python -m compileall -q backend
    pytest
    python scripts/benchmark.py

Browser JavaScript checks:

    node --input-type=module --check < frontend/api.js
    node --input-type=module --check < frontend/app.js
    node --test tests/frontend_api.test.mjs

Tests cover provider fallback, HTTP 429/500 handling, timeouts, malformed structured output, missing keys, Ollama unavailable, configured-model removal, provider health caching, sequential provider failure, browser request cancellation, external-response size limits, integer money and idempotent campaign writes.

## Failure behavior

- no internet: local Ollama is attempted; deterministic fallback remains available;
- no API keys: startup succeeds;
- Ollama stopped: provider health reports unavailable;
- hosted 429/5xx: bounded retry then provider failover;
- malformed JSON: lightweight parse/repair, then safe failure;
- user cancels generation: browser aborts the request;
- all providers fail: product generation uses deterministic concepts;
- no embedding model: embedding request fails explicitly rather than using a wrong model.

There are no infinite retry loops.

## Performance

The application intentionally avoids:

- Pandas in request paths;
- model SDK dependencies;
- vector databases;
- unbounded queues;
- unbounded caches;
- per-request HTTP clients;
- large frontend frameworks.

AI concurrency is bounded. Provider health is cached for a short TTL. Ollama model discovery is reused through that health cache.

See `PERFORMANCE.md`.

## Security

Secrets remain server-side environment variables.

Never commit:

- `.env`;
- API keys;
- database files;
- logs;
- model weights;
- virtual environments.

AI output is treated as untrusted input. It is validated before structured use and is never executed as shell, SQL, Python, filesystem, or blockchain instructions.

See `SECURITY.md`.

## Deployment

The container entrypoint may start with root only to repair ownership on a runtime-mounted database directory. It immediately drops to `appuser` (UID 10001) before Uvicorn starts, and the application process itself runs non-root. The image also exposes a health check.

Railway is currently configured as an optional hosted deployment target. It is **not required** for the zero-cost core. Local execution remains the reference path.

SQLite is a single-replica store. Do not scale the API horizontally while SQLite remains the durable campaign store.

## Troubleshooting

### Ollama status says unavailable

Start Ollama:

    ollama serve

List installed models:

    ollama list

Install a lightweight model:

    ollama pull qwen3:1.7b

Then wait for the short provider-health cache to expire or restart the backend.

### AI still uses deterministic fallback

Check:

    curl http://127.0.0.1:8000/api/v1/ai/status

A provider must report `available: true` before it is used.

### OpenRouter model is rejected

Use:

    OPENROUTER_MODEL=openrouter/free

or another explicit `:free` model slug.

### Database directory error

For local Python use a writable path such as:

    DATABASE_PATH=./data/omnipool.db

Docker and the current Railway service use `/data/omnipool.db`. The container entrypoint repairs ownership for runtime-mounted `/data` volumes and then drops privileges before starting the API.

## Current limitations

- X and Reddit ingestion are adapter boundaries, not complete live streaming implementations.
- Solana escrow, minting and liquidity graduation are not yet an audited on-chain program.
- SQLite intentionally limits the hosted alpha to one application replica.
- Hosted free tiers can change or disappear; they are never required for the core product.
