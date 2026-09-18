# Codex operating contract

## Product
OMNIPOOL AI: **Trend -> AI concept -> Proof of Demand -> human approval -> token graduation**.

## Non-negotiable engineering rules
1. Python remains the backend language and owns quantitative logic.
2. Optimize for low RAM, low CPU, low network chatter and predictable latency.
3. Do not add a library unless its measured benefit outweighs runtime cost.
4. Never add Pandas to the hot path. Use pure Python; targeted NumPy only after benchmark evidence.
5. External I/O always needs timeouts, bounded concurrency and graceful fallback.
6. Caches are bounded and TTL-based. Lists are bounded/paginated.
7. Frontend changes must avoid unnecessary rerenders and large bundles.
8. Human wallet signature is mandatory for irreversible Solana actions. AI may prepare, never secretly sign.
9. Never present trend scores as guarantees of token performance.
10. Every milestone loop is: implement -> tests -> benchmark/resource check -> error-path review -> continue.

## Current gaps (do not fake them)
- X and Reddit adapters are visible but not connected until credentials exist.
- Solana graduation is a state + transaction-plan layer, not an on-chain program yet.
- Wallet connection is a demo identity.
- OpenAI uses deterministic local fallback until `OPENAI_API_KEY` is set.

## Next production milestones
1. X filtered-stream/webhook adapter and Reddit adapter with bounded rolling windows.
2. Narrative clustering/deduplication across sources.
3. PostgreSQL only when multi-instance deployment makes SQLite insufficient.
4. Solana devnet escrow program: funding target, expiry, permissionless refunds, contributor accounting, claims, authority revoke, liquidity graduation.
5. Phantom/Solflare browser wallet adapter; private keys never touch backend.
