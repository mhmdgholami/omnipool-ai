# Engineering operating contract

OMNIPOOL must remain fully usable without a paid AI API or paid data infrastructure.

Before changing architecture:

1. identify the invariant;
2. identify the hot path;
3. state memory and concurrency impact;
4. prefer deterministic Python when AI is unnecessary;
5. add or update tests;
6. run lint, tests, benchmark and browser syntax checks.

## AI rules

Business logic talks to `backend.ai` services, not provider classes.

Provider order is local-first.

Do not add OpenAI, Anthropic, Gemini or another paid API as a required path.

OpenRouter must remain explicit-free-model-only.

Do not auto-download large model weights.

Do not log prompts or secret values.

AI output is untrusted data.

## Infrastructure rules

Do not add Redis because caching exists.

Do not add Kafka because events exist.

Do not add a vector database because embeddings exist.

Add infrastructure only when a measured requirement needs it.

SQLite remains single-replica. Move durable state to PostgreSQL before horizontal API scaling.

Financial values use lamports internally. Retryable writes need idempotency. User wallet signing stays outside the backend.

Avoid compressed source files, generated archive blobs in CI, decorative abstractions and comments that only restate syntax.
