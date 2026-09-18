# OMNIPOOL AI

Performance-first **Trend -> AI Idea -> Proof of Demand -> Human Approval -> Token** prototype.

## Architecture
- Backend: Python + FastAPI
- Quant: pure Python scoring engine
- Store: SQLite/WAL for the current single-instance MVP
- Frontend: vanilla HTML/CSS/ES modules for minimum client RAM/CPU
- Live market signal: DEX Screener Solana adapter
- AI: server-side OpenAI Responses API adapter with deterministic fallback
- Solana: devnet graduation-plan boundary; no server-side user signing

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000`.

## Test
```bash
pytest
python scripts/benchmark.py
```

## What is real
Python quantitative scoring, SQLite persistence, DEX ingestion, optional OpenAI generation, proof-of-demand state machine, refund/graduation API states and lightweight UI.

## Explicitly not real yet
X/Reddit live streams, Phantom/Solflare signing, SPL deployment, on-chain escrow and liquidity creation. These are intentionally not faked.

## V1 economic invariant
Creator genesis: 0%. Platform genesis: 0%. Contributor supply: 50%. Initial liquidity supply: 50%. Failed campaign: refund path.

Read `CODEX.md` and `PERFORMANCE.md` before architectural changes.
