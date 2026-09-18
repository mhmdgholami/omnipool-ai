# Security

## Trust boundaries

The browser, third-party APIs, social data, crypto APIs and AI output are untrusted.

The backend may prepare a graduation plan. It must never possess or use a user's private key.

## Secrets

Secrets are environment variables only.

They must never appear in:

- frontend JavaScript;
- localStorage;
- API responses;
- Git commits;
- logs.

The repository contains placeholders only.

## AI safety boundary

AI output cannot directly execute:

- shell commands;
- SQL;
- Python;
- filesystem actions;
- blockchain transactions;
- privileged administrative actions.

Structured AI output is parsed and validated with Pydantic before use.

The router logs metadata, not full prompts.

## Free-provider policy

Ollama is the primary provider.

Groq and OpenRouter are optional.

OpenRouter requests are hard-blocked unless the model is `openrouter/free` or an explicit `:free` slug. Core functionality does not require a hosted provider.

## Request controls

The service enforces:

- request-body size limits;
- bounded per-client rate limiting;
- AI input limits;
- AI output limits;
- bounded AI concurrency;
- queue timeout;
- request timeout;
- finite retry count.

## Financial state

SOL accounting is integer lamports.

Contribution writes are transactional and idempotent.

Graduation requests are retry-safe.

## Before real funds

The current application is not an audited custody system.

Before accepting real SOL:

1. deploy and independently audit the Solana escrow program;
2. require signed-wallet authentication for privileged actions;
3. fuzz state transitions and arithmetic;
4. make monetary idempotency mandatory at every public boundary;
5. add an append-only audit trail;
6. run load and failure-injection tests;
7. define key-compromise and incident-response procedures.

## Solana invariants

Intended V1:

- creator genesis allocation: 0%;
- platform genesis allocation: 0%;
- contributor allocation: 50%;
- liquidity allocation: 50%;
- mint authority after graduation: revoked;
- freeze authority after graduation: revoked;
- server signs user wallet: false.

These should eventually be enforced on-chain rather than trusted from API output.
