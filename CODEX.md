# Engineering operating notes

Treat this repository like a small production system, not a demo generator.

Before changing architecture:

1. identify the invariant being protected;
2. identify the hot path;
3. state the memory and concurrency impact;
4. add or update a test;
5. run lint, tests and the benchmark;
6. keep the change reviewable.

Do not introduce a service because it sounds scalable. Add PostgreSQL before multiple API replicas. Add Redis only for cross-instance ephemeral coordination. Add an event bus only when ingestion throughput, replay or consumer isolation requires it.

Financial values use lamports internally. Retryable writes need idempotency. User wallet signing stays in the browser/wallet boundary.

The current clustering implementation is deliberately bounded and simple. If it is replaced, benchmark both CPU and recall/quality against the same observation corpus.

Avoid compressed one-line source files, generated archive blobs in CI, decorative abstractions and comments that only restate the code.
