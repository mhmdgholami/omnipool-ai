# Architecture

## Design goal

OMNIPOOL should be cheap to run at small scale without painting itself into a corner at large scale. The design therefore keeps the single-node alpha deliberately simple while making the boundaries that change under scale explicit.

## Current process

Browser
  -> FastAPI
     -> trend service
     -> quantitative engine
     -> concept generation
     -> campaign state machine
     -> SQLite

External APIs are accessed through one shared HTTP connection pool. The quantitative engine uses pure Python data structures and has no dataframe dependency in request paths.

## Data representation

Money is integer lamports. Floating-point values are acceptable for non-financial scores, but not for balances, targets or accepted contributions.

Campaign state is relational because the important operations are transactional:

- read campaign;
- cap a contribution to remaining capacity;
- insert contribution;
- update aggregate raised amount;
- commit atomically.

Idempotency keys are unique so an HTTP retry cannot double-count the same contribution.

Trend observations are ephemeral and bounded. The clustering algorithm is intentionally O(n*k), where n is capped observations and k is capped clusters. At the current caps this is cheaper and easier to reason about than adding a vector database. If the observation set becomes large enough that the bound is restrictive, the next step is approximate nearest-neighbor or locality-sensitive hashing, not an unbounded nested loop.

The rate limiter uses a token bucket per client and an OrderedDict-style bounded client set. It stores constant state per client rather than a timestamp for every request.

## Consistency model

Campaign funding needs strong local consistency. SQLite uses BEGIN IMMEDIATE so only one writer updates funding state at a time.

Trend intelligence is eventually consistent. It is acceptable for a trend card to lag a source by seconds; it is not acceptable for a contribution to be counted twice.

Graduation is retry-safe. A campaign already marked live returns the same state rather than failing a repeated request.

## Scaling stages

### Stage 0: alpha

- one FastAPI replica;
- SQLite on persistent disk;
- shared outbound HTTP pool;
- process-local cache and rate limiter.

Do not run multiple API replicas against independent SQLite files.

### Stage 1: production beta

Move campaigns, concepts and audit data to managed PostgreSQL before horizontal scaling.

Add Redis only for things that require cross-instance coordination:

- distributed rate limits;
- short-lived market caches;
- idempotency lookup acceleration if PostgreSQL becomes a bottleneck.

Do not put durable campaign truth in Redis.

### Stage 2: sustained ingestion

Separate ingestion workers from request-serving API instances.

A practical topology is:

source adapters
  -> durable queue or event log
  -> normalization workers
  -> narrative clustering/scoring
  -> PostgreSQL + analytical sink

Use NATS JetStream, Kafka or a managed equivalent only when replay, consumer groups and sustained throughput justify the operational cost. For modest traffic, PostgreSQL-backed jobs or a managed queue are simpler.

### Stage 3: analytical scale

If historical observations reach tens or hundreds of millions, keep operational campaign state in PostgreSQL and move time-series/analytical scans to a columnar system such as ClickHouse, BigQuery or a warehouse.

The online API should read compact materialized trend summaries rather than scanning raw history.

## Partitioning

Good partition keys are stable and high-cardinality:

- campaign writes: campaign_id;
- contribution lookup: campaign_id plus wallet;
- observations: source plus time bucket;
- analytical history: event time.

Avoid partitioning by ticker. Tickers are not unique and can become hot keys.

## Backpressure

Every ingestion boundary needs a maximum queue depth or batch size. When downstream processing is behind, lower-value observations should be aggregated or delayed rather than allowing memory to grow without bound.

External source timeouts are short. A failed source degrades its own contribution to the trend score; it does not block the whole radar.

## SLO targets for the beta

Excluding third-party latency:

- p95 health/list API latency under 50 ms on a small VM;
- p95 campaign write latency under 100 ms;
- no unbounded process memory growth during repeated scans;
- zero duplicate accepted contribution for a repeated idempotency key.

These are engineering budgets, not marketing claims.
