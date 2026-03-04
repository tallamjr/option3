# Architecture

## Overview

option3 is a streaming data pipeline that captures real-time edit events from Wikimedia projects, transforms them into analytical summaries, and serves the results via a REST API. The system is deliberately polyglot -- Rust handles I/O-bound services (ingestion and serving), Python handles analytical transformations -- coordinated through RedPanda as a Kafka-compatible message broker.

## Data Flow

```
+----------------------------+
| Wikimedia EventStreams      |
| stream.wikimedia.org       |
| /v2/stream/recentchange    |
+-------------+--------------+
              |
              | SSE (HTTP chunked transfer, text/event-stream)
              | ~hundreds of events/second across all wikis
              v
+-------------+--------------+
| Ingest Service (Rust)      |
| crates/ingest/             |
|                            |
| 1. Connect via reqwest-    |
|    eventsource             |
| 2. Parse JSON -> WikiEvent |
| 3. Filter by wiki db name  |
| 4. Produce to RedPanda     |
|    key: {wiki}:{id}        |
|    compression: snappy     |
+-------------+--------------+
              |
              | Kafka protocol (port 19092)
              v
+-------------+--------------+
| RedPanda                   |
| topic: wiki.recentchange   |
|        .raw                |
|                            |
| Single-node dev mode       |
| Schema Registry: 18081     |
| HTTP Proxy: 18082          |
| Console UI: 8080           |
+-------------+--------------+
              |
              | confluent-kafka consumer
              | group: option3-transform
              v
+-------------+--------------+
| Transform Service (Python) |
| transform/                 |
|                            |
| 1. Consume JSON events     |
| 2. Batch into list[dict]   |
| 3. Convert to Polars DF    |
| 4. Write Parquet batch     |
|    (size or time trigger)  |
+-------------+--------------+
              |
              | Timestamped .parquet files
              | events_YYYYMMDDTHHMMSS.parquet
              v
+-------------+--------------+
| data/                      |
| Columnar Parquet storage   |
+-------------+--------------+
              |
              | polars::LazyFrame::scan_parquet
              v
+-------------+--------------+
| Serve API (Rust)           |
| crates/serve/              |
|                            |
| Axum router:               |
|  GET /health               |
|  GET /api/stats            |
|  GET /api/edits/by-wiki    |
|  GET /api/editors/top      |
|  GET /api/activity/by-type |
|  GET /api/ws (WebSocket)   |
|                            |
| Middleware:                |
|  - CORS (permissive)      |
|  - tower-http tracing     |
+----------------------------+
```

## Component Details

### Ingest (`crates/ingest/`)

The ingest service is a long-running Rust binary that maintains a persistent SSE connection to Wikimedia's EventStreams endpoint.

**SSE client** (`sse.rs`):
- Uses `reqwest-eventsource` which handles automatic reconnection on connection drops
- Parses each SSE message payload as a `WikiEvent` struct via serde
- Filters events client-side by wiki database name (e.g. `enwiki`, `wikidatawiki`) since EventStreams has no server-side filtering
- Unparseable messages are logged at debug level and skipped -- the upstream schema allows additional properties and not all fields are guaranteed

**Kafka producer**:
- Built on `rdkafka` (Rust bindings for librdkafka, compiled via cmake)
- Configured for throughput without sacrificing delivery guarantees:
  - `compression.type=snappy` -- fast compression, good for JSON payloads
  - `linger.ms=5` -- micro-batch for 5ms before sending, amortises network overhead
  - `batch.num.messages=1000` -- cap on batch size
  - `enable.idempotence=true` + `acks=all` -- exactly-once semantics within a producer session
- Message key format: `{wiki}:{rc_id}` -- ensures events from the same wiki are partitioned together, enabling ordered consumption per wiki

**CLI and lifecycle** (`main.rs`):
- `clap` derive-based CLI with `--brokers`, `--topic`, `--sse-url`, `--wikis` flags
- `tokio::select!` between the ingestion loop and `ctrl_c()` for graceful shutdown
- `tracing-subscriber` with `RUST_LOG` env filter support

### Transform (`transform/`)

The transform service is a Python application that consumes raw events from RedPanda, applies Polars transformations, and writes Parquet batches.

**Consumer** (`consumer.py`):
- Wraps `confluent_kafka.Consumer` with JSON deserialisation
- Yields parsed dicts from an infinite polling loop
- Handles `PARTITION_EOF`, decode errors, and JSON parse failures gracefully

**Processor** (`processor.py`) -- pure functions operating on Polars DataFrames:
- `events_to_dataframe()` -- converts `list[dict]` to a typed DataFrame, flattening nested `length.old`/`length.new` into top-level columns
- `edits_by_wiki()` -- filters to `edit`/`new` types, groups by wiki, counts edits, sums size changes
- `top_editors()` -- ranks users by edit count with a configurable limit, includes bot flag
- `activity_by_type()` -- counts events per event type

All transforms use the Polars lazy API (`.lazy()` -> `.collect()`) for query optimisation.

**Storage** (`storage.py`):
- `write_batch_to_parquet()` -- writes a DataFrame to `events_YYYYMMDDTHHMMSS.parquet`, creates output directories as needed
- `read_all_parquet()` -- lazily scans all `*.parquet` files in a directory

**CLI** (`__main__.py`):
- `click`-based CLI with `--brokers`, `--topic`, `--group-id`, `--output-dir`, `--batch-size`, `--flush-interval`
- Batch collection with dual flush trigger: by count (default 500 events) or by time (default 30 seconds)
- Graceful shutdown on `KeyboardInterrupt` flushes the remaining batch

### Serve (`crates/serve/`)

The API server is a Rust binary built on Axum that loads Parquet data and serves analytics queries.

**State management** (`routes.rs`):
- `AppState` holds an `Arc<RwLock<Option<DataFrame>>>` -- the loaded Polars DataFrame shared across all request handlers
- The `Option` allows the server to start even when no Parquet data exists yet
- `RwLock` enables concurrent reads from multiple handlers

**Handlers** (`handlers.rs`):
- Each endpoint reads from the shared DataFrame and returns JSON
- Currently returns summary statistics (row counts, unique value counts); full aggregation queries are planned for a later phase
- Errors from lock poisoning return HTTP 500

**WebSocket** (`ws.rs`):
- Upgrade handler at `/api/ws`
- Sends a welcome message on connection
- Echo-based scaffolding -- intended for future real-time event streaming

**Parquet loader** (`main.rs`):
- On startup, scans `{parquet_dir}/*.parquet` via `polars::LazyFrame::scan_parquet`
- Logs a warning and starts with empty state if no files are found

### Common (`crates/common/`)

Shared types used by both Rust crates.

**Models** (`models.rs`):
- `WikiEvent` -- full serde model matching the [Wikimedia recentchange JSON schema](https://schema.wikimedia.org/repositories/primary/jsonschema/mediawiki/recentchange/latest.yaml)
- All fields are `Option<T>` because the upstream schema does not enforce required fields (aside from `meta`), and different event types (`edit`, `log`, `new`, etc.) populate different subsets of fields
- Uses `#[serde(rename = "...")]` for `$schema` (not a valid Rust identifier) and `type` (reserved keyword)
- `EditSummary` -- flattened view with computed `size_change` (new length minus old length), intended for API responses and aggregation
- Nested structs: `EventMeta` (event envelope), `Revision` (old/new revision IDs), `Length` (old/new page sizes in bytes)

**Config** (`config.rs`):
- `KafkaConfig` -- brokers (`localhost:19092`), topic (`wiki.recentchange.raw`), group_id (`option3-transform`)
- `SseConfig` -- stream URL, default wiki filter list
- `ApiConfig` -- host (`0.0.0.0`), port (`3000`)
- `StorageConfig` -- parquet output directory (`data`)
- `AppConfig` -- top-level struct combining all sub-configs, derives `Default`

**Errors** (`error.rs`):
- `Option3Error` enum using `thiserror` with variants for SSE, JSON, Kafka, Parquet, HTTP, config, and I/O errors
- Implements `From<serde_json::Error>` and `From<std::io::Error>` automatically via `#[from]`

## Design Decisions

### Why Wikimedia EventStreams instead of Twitter?

Twitter's API became restrictive and paid in 2023. Wikimedia EventStreams is:
- Completely free with no authentication
- Higher volume than most free streaming APIs
- Well-documented with a stable JSON schema
- Genuinely interesting data for analytics (edit patterns, bot activity, wiki growth)

### Why a polyglot Rust + Python architecture?

A single-language solution would be simpler, but the polyglot split plays to each language's strengths:

| Concern | Rust | Python |
|---------|------|--------|
| Long-running network I/O | Excellent (async, zero-cost futures) | Adequate but higher memory |
| Serialisation throughput | Fast (serde, zero-copy where possible) | Slower (json module) |
| DataFrame analytics | Polars Rust API is lower-level | Polars Python API is more ergonomic |
| Iteration speed on queries | Compile cycle | Immediate |
| Production deployment | Static binary, small image | Needs runtime, larger image |

The coordination cost is low because RedPanda speaks the Kafka protocol, which both `rdkafka` (Rust) and `confluent-kafka` (Python) implement natively.

### Why RedPanda over Apache Kafka?

- **No JVM** -- single Go binary, starts in seconds, uses ~10x less memory
- **Kafka-compatible** -- all existing Kafka client libraries (rdkafka, confluent-kafka) work without modification
- **Built-in schema registry and HTTP proxy** -- no separate services to deploy
- **Console UI** -- RedPanda Console provides topic inspection, consumer group monitoring, and message browsing at http://localhost:8080
- **Dev mode** -- `--mode dev-container` with `--smp 1 --memory 512M` runs comfortably on a laptop

### Why Parquet over a database?

For this use case, Parquet files are sufficient and simpler:
- No database server to manage
- Columnar format matches analytical query patterns
- Append-only batches avoid write contention between the transform service and the API server
- Any tool in the data ecosystem can read Parquet directly
- Easy to archive, partition by date, or migrate to object storage later

A database (e.g. DuckDB, PostgreSQL) would make sense if the API needed complex ad-hoc queries, but the current fixed set of aggregation endpoints reads well from Parquet via Polars.

### Why `Option<T>` for all WikiEvent fields?

The Wikimedia recentchange schema is permissive -- it allows additional properties and only strictly requires the `meta` object. In practice:
- `edit` events have `length` and `revision` but no `log_*` fields
- `log` events have `log_id`, `log_type`, `log_action` but no `length` or `revision`
- Some fields like `patrolled` are conditionally present based on wiki configuration

Making all fields optional ensures deserialisation never fails on valid upstream data, even as the schema evolves.

## Infrastructure

### Docker Compose (`docker/docker-compose.yml`)

Single-node RedPanda with dual Kafka listeners:
- **Internal** (`redpanda:9092`) -- for inter-container communication
- **External** (`localhost:19092`) -- for host access from ingest/transform services

The console service waits for RedPanda's health check before starting.

### CI Pipeline (`.github/workflows/ci.yml`)

Five independent jobs run in parallel:
1. `cargo check --workspace` -- type checking
2. `cargo test --workspace` -- integration tests
3. `cargo clippy -- -D warnings` -- lint with zero-warning policy
4. `cargo fmt -- --check` -- formatting verification
5. `python -m pytest -v` -- Python test suite

All Rust jobs install cmake for the rdkafka native build and use `Swatinem/rust-cache` for dependency caching.
