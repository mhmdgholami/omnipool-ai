# OMNIPOOL AI

OMNIPOOL is a performance-first trend intelligence and Proof-of-Demand system for Solana-native launches.

The current alpha does four things:

1. collects bounded market observations;
2. clusters them into narratives and scores opportunity, evidence confidence, saturation and launch risk;
3. generates three launch concepts;
4. lets a community test demand before a graduation plan is produced.

The server never signs a user's wallet.

## Run locally

    python -m venv .venv
    source .venv/bin/activate
    pip install -e '.[dev]'
    uvicorn backend.app:app --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000.

## Checks

    ruff check backend tests scripts
    pytest
    python scripts/benchmark.py

## Engineering constraints

- Financial state is stored in integer lamports, not floating point.
- Contribution retries are idempotent.
- External HTTP calls share one bounded connection pool.
- Trend observations, clusters, caches, API lists and rate-limit clients are bounded.
- SQLite is a single-replica alpha store. Horizontal scaling requires PostgreSQL first.
- The browser has no framework runtime and no charting dependency.
- No user private key is stored or signed by the backend.

Read ARCHITECTURE.md, SECURITY.md and PERFORMANCE.md before changing core boundaries.
