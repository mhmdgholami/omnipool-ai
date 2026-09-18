# Performance contract

Resource efficiency is part of the product definition.

## Current bounds

- observations per scan: MAX_OBSERVATIONS_PER_SCAN;
- clusters per scan: at most 60;
- trend list: MAX_TRENDS, default 100;
- DEX cache: MARKET_CACHE_SIZE, default 64;
- rate-limit clients: MAX_RATE_LIMIT_CLIENTS, default 2000;
- outbound HTTP connections: 8;
- outbound keep-alive connections: 4;
- request body: MAX_REQUEST_BYTES, default 64 KiB.

## Runtime rules

- no Pandas in request paths;
- no unbounded in-memory queue;
- no full-history scan inside an API request;
- no new HTTP client per request;
- no floating-point representation for financial state;
- no browser framework runtime unless a measured product need justifies it;
- no chart library for simple bars or counters.

## Benchmark loop

Run:

    pytest
    python scripts/benchmark.py

The benchmark is a regression signal, not a universal hardware claim. Compare the same workload on the same class of runner before and after a change.

## When to optimize further

Profile before adding complexity. The current bounded O(n*k) clustering is appropriate for hundreds of observations. Replace it only when measurements show the cap is constraining product quality or CPU budget.
