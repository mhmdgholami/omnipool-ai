# Performance contract

Resource efficiency is a product requirement, not a later optimization.

- No Pandas/DataFrame allocation in request paths.
- External calls are async with strict timeouts and small connection pools.
- DEX cache is bounded to 40 rows and TTL-based.
- API list endpoints are capped at 100 rows.
- SQLite uses WAL and short-lived connections; no ORM identity map stays in RAM.
- Frontend is vanilla JS/CSS: no React/Vue runtime and no charting library.
- No continuous polling loop. Scans are explicit; production streams should be event-driven.
- Campaign expiry is reconciled lazily; no permanent worker is required for V1.
- AI output is capped to exactly three concepts with bounded field lengths.
- Solana server code never stores/signs with user private keys.

Run `pytest` and `python scripts/benchmark.py` before merging architectural changes.
