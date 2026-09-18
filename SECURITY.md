# Security

## Trust boundaries

The browser is untrusted. Wallet addresses, contribution amounts, concept IDs and idempotency keys are validated server-side.

The backend may prepare a Solana graduation plan. It must not possess or use the user's private key.

## Current alpha

- secrets are environment variables and never committed;
- request bodies have an explicit size cap;
- API traffic has a bounded process-local token-bucket limiter;
- response headers disable MIME sniffing and unnecessary browser permissions;
- external requests use timeouts and bounded connection pools;
- sensitive-event trend flags can block automated concept generation;
- contribution retries are idempotent;
- graduation is retry-safe.

## Before real funds

The current code is not an audited custody system. Before accepting real SOL:

1. move campaign truth to PostgreSQL or the on-chain program as appropriate;
2. deploy and independently audit the Solana escrow program;
3. fuzz state transitions and arithmetic;
4. add signed wallet authentication for privileged actions;
5. make idempotency keys mandatory for monetary endpoints;
6. add an append-only audit log;
7. enforce distributed rate limits at the edge;
8. add dependency and container scanning in CI;
9. run load tests and failure-injection tests;
10. document an incident and key-compromise procedure.

## Solana invariants

The intended V1 plan is:

- creator genesis allocation: 0%;
- platform genesis allocation: 0%;
- contributor allocation: 50%;
- liquidity allocation: 50%;
- mint authority after graduation: revoked;
- freeze authority after graduation: revoked;
- server signs user wallet: false.

These values should eventually be enforced on-chain, not merely trusted from API output.
