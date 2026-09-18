# Performance contract

Resource efficiency is part of the product definition.

## Bounds

- observations per scan: `MAX_OBSERVATIONS_PER_SCAN`;
- clusters per scan: at most 60;
- trend list: `MAX_TRENDS`;
- DEX cache: `MARKET_CACHE_SIZE`;
- AI concurrency: `AI_MAX_CONCURRENCY`;
- AI input: `AI_MAX_INPUT_CHARS`;
- AI output: `AI_MAX_OUTPUT_TOKENS`;
- rate-limit clients: `MAX_RATE_LIMIT_CLIENTS`;
- outbound HTTP connections: 8;
- outbound keep-alive connections: 4;
- request body: `MAX_REQUEST_BYTES`;
- external JSON response: `MAX_EXTERNAL_RESPONSE_BYTES`.

## AI memory policy

The backend never loads model weights itself.

Ollama owns the local model process. OMNIPOOL keeps only request/response payloads and small health metadata in memory.

Do not load multiple local models proactively. Model selection is lazy.

Ollama's configured `keep_alive` is short so unused model memory can be released by the inference server.

## Runtime rules

- no Pandas in request paths;
- no vector database unless measured product requirements justify it;
- no unbounded queue;
- no unbounded cache;
- no full-history scan in a request;
- no new HTTP client per request;
- no blocking network call inside async AI paths;
- no floating-point representation for financial state;
- no large frontend framework for the current UI;
- no polling loop for provider health.

Provider health is TTL-cached and uses a short dedicated timeout so an offline provider does not stall normal fallback.

## Benchmark loop

Run:

    pytest
    python scripts/benchmark.py

The benchmark is a regression signal, not a universal hardware claim.

Compare the same workload on comparable hardware before and after architectural changes.

## Optimization rule

Profile before adding infrastructure.

The bounded O(n*k) clustering algorithm is appropriate for hundreds of observations. Replace it only when measurements show the current cap is constraining CPU budget or product quality.
