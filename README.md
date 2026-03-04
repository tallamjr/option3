# option3

A modern data engineering pipeline that ingests real-time Wikimedia edit events, transforms them with Polars, and serves analytics via a REST API.

This project replaces an earlier proof-of-concept Twitter streaming pipeline (Scala/Kafka/Spark) with a polyglot Rust + Python architecture built around freely available, high-volume event data from Wikimedia.

## Architecture

```
                         +---------------------+
                         | Wikimedia           |
                         | EventStreams (SSE)   |
                         | stream.wikimedia.org|
                         +----------+----------+
                                    |
                                    | Server-Sent Events
                                    v
                         +----------+----------+
                         | Rust Ingest Service  |
                         | (crates/ingest)      |
                         |                      |
                         | - reqwest-eventsource|
                         | - client-side filter |
                         | - rdkafka producer   |
                         +----------+----------+
                                    |
                                    | Kafka protocol (snappy, idempotent)
                                    v
                         +----------+----------+
                         | RedPanda             |
                         | (Kafka-compatible)   |
                         |                      |
                         | topic:               |
                         | wiki.recentchange.raw|
                         +----------+----------+
                                    |
                                    | confluent-kafka consumer
                                    v
                         +----------+----------+
                         | Python/Polars        |
                         | Transform Service    |
                         | (transform/)         |
                         |                      |
                         | - batch collection   |
                         | - Polars aggregation |
                         | - Parquet writer     |
                         +----------+----------+
                                    |
                                    | Timestamped .parquet files
                                    v
                         +----------+----------+
                         | data/                |
                         | (Parquet storage)    |
                         +----------+----------+
                                    |
                                    | Polars lazy scan
                                    v
                         +----------+----------+
                         | Rust/Axum API        |
                         | (crates/serve)       |
                         |                      |
                         | - REST endpoints     |
                         | - WebSocket          |
                         | - CORS + tracing     |
                         +---------------------+
```

See [docs/architecture.md](docs/architecture.md) for detailed design rationale.

## Data Source

[Wikimedia EventStreams](https://stream.wikimedia.org) provides a real-time SSE feed of all changes across Wikimedia projects. The `recentchange` stream emits structured JSON events for every edit, page creation, log action, categorisation change, and external change across all wikis.

Key properties of this data source:

- **Free and open** -- no API key, no rate limits, no authentication required
- **High volume** -- hundreds of events per second across all Wikimedia wikis
- **Well-structured** -- events follow the [mediawiki/recentchange JSON schema](https://schema.wikimedia.org/repositories/primary/jsonschema/mediawiki/recentchange/latest.yaml)
- **Event types** -- `edit`, `new`, `log`, `categorize`, `external`
- **Default wiki filter** -- `enwiki`, `wikidatawiki`, `commonswiki` (configurable via CLI)

## Design Choices

### Polyglot split: Rust + Python

The pipeline deliberately uses two languages, each where it excels:

- **Rust** handles the ingest service and API server -- both are long-running, performance-critical processes where low memory usage, predictable latency, and strong type safety matter. The ingest service must sustain hundreds of events/second without back-pressure, and the API server benefits from Rust's async I/O model.

- **Python with Polars** handles the transform/analytics layer. Polars provides a mature DataFrame API that is well-suited for batch aggregation, exploratory analysis, and iterating on transformation logic. Python's ecosystem makes it straightforward to add new analytical queries or integrate with notebooks for ad-hoc exploration.

- **RedPanda** acts as the coordination layer between the two. It is Kafka-compatible (so all existing tooling works), but ships as a single binary with no JVM or ZooKeeper dependency, making it lightweight for both development and production.

### Parquet as the interchange format

Transformed data is written to timestamped Parquet files rather than a database. This keeps the system simple while providing:
- Columnar storage optimised for analytical queries
- Schema preservation without a separate catalogue
- Easy integration with any tool that reads Parquet (DuckDB, Spark, pandas, Polars)
- Append-only batches that avoid write contention

### Kafka producer configuration

The ingest producer is configured for throughput with safety:
- **Snappy compression** -- reduces network and storage overhead with minimal CPU cost
- **Batch settings** -- `linger.ms=5`, `batch.num.messages=1000` for micro-batching
- **Idempotent delivery** -- `enable.idempotence=true` with `acks=all` prevents duplicates
- **Message keying** -- `{wiki}:{id}` ensures events from the same wiki land on the same partition

### Event model

The `WikiEvent` struct in `crates/common/src/models.rs` is derived directly from the [official Wikimedia recentchange schema](https://schema.wikimedia.org/repositories/primary/jsonschema/mediawiki/recentchange/latest.yaml). All fields are `Option<T>` because the upstream schema does not require them (aside from `meta`), and different event types populate different subsets. An `EditSummary` struct provides a flattened, lightweight view with a computed `size_change` field for aggregation.

## Project Structure

```
option3/
├── Cargo.toml                         # Rust workspace root
├── Cargo.lock                         # Locked dependency versions
├── Justfile                           # Task runner (just)
├── LICENSE                            # Apache 2.0
├── .gitignore                         # Rust + Python combined
├── .github/workflows/ci.yml           # CI: Rust checks + Python tests
├── docker/
│   └── docker-compose.yml             # RedPanda + RedPanda Console
├── data/                              # Parquet output (.gitkeep)
├── docs/
│   ├── architecture.md                # Design rationale and data flow
│   └── imgs/option3-plan.svg          # Planning diagram
│
├── crates/
│   ├── common/                        # Shared library crate
│   │   ├── Cargo.toml
│   │   ├── src/
│   │   │   ├── lib.rs
│   │   │   ├── models.rs              # WikiEvent, EditSummary (serde)
│   │   │   ├── config.rs              # KafkaConfig, SseConfig, ApiConfig, StorageConfig
│   │   │   └── error.rs               # Option3Error (thiserror)
│   │   ├── tests/
│   │   │   └── integration_test.rs    # Deserialisation + config tests
│   │   └── benches/
│   │       └── ingest_bench.rs        # WikiEvent deserialisation benchmark
│   │
│   ├── ingest/                        # SSE -> RedPanda producer binary
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── main.rs                # CLI (clap), tokio runtime, Ctrl+C shutdown
│   │       └── sse.rs                 # SSE client, wiki filter, Kafka producer
│   │
│   └── serve/                         # Axum REST API + WebSocket binary
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs
│           ├── main.rs                # CLI (clap), parquet loader, server bind
│           ├── routes.rs              # Router, AppState (Arc<RwLock<DataFrame>>)
│           ├── handlers.rs            # /health, /api/stats, edits, editors, activity
│           └── ws.rs                  # WebSocket upgrade + echo handler
│
└── transform/                         # Python Polars transform service
    ├── pyproject.toml                 # uv/pip project (polars, confluent-kafka, click)
    ├── transform/
    │   ├── __init__.py
    │   ├── __main__.py                # CLI entrypoint (click)
    │   ├── consumer.py                # KafkaConsumer wrapper (confluent-kafka)
    │   ├── processor.py               # Polars transforms (edits_by_wiki, top_editors, ...)
    │   └── storage.py                 # Parquet writer/reader
    └── tests/
        ├── __init__.py
        ├── test_processor.py          # 6 tests: DataFrame creation + aggregations
        └── test_storage.py            # 4 tests: write, roundtrip, mkdir, multi-file
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (`{"status": "ok"}`) |
| GET | `/api/stats` | Row and column counts from loaded data |
| GET | `/api/edits/by-wiki` | Edit counts and unique wikis |
| GET | `/api/editors/top` | Edit counts and unique editors |
| GET | `/api/activity/by-type` | Event counts and unique event types |
| GET | `/api/ws` | WebSocket upgrade (echo-based scaffolding) |

## Prerequisites

- **Rust** -- stable toolchain (edition 2021)
- **Python** -- 3.11+ with [uv](https://github.com/astral-sh/uv) (recommended) or pip
- **Docker** -- Docker Engine + Docker Compose (for RedPanda)
- **just** -- [just](https://github.com/casey/just) task runner
- **cmake** -- required for building rdkafka's native C library (librdkafka)

## Quick Start

```bash
# 1. Start RedPanda (Kafka-compatible broker + web console)
just infra-up
# Console available at http://localhost:8080

# 2. Start the ingest service (SSE -> RedPanda)
just run-ingest
# Connects to stream.wikimedia.org, filters enwiki/wikidatawiki/commonswiki

# 3. In another terminal, start the transform service (RedPanda -> Parquet)
just run-transform
# Consumes from wiki.recentchange.raw, writes batches to data/

# 4. In another terminal, start the API server (Parquet -> REST)
just run-serve
# Serves on http://localhost:3000

# 5. Query the API
curl http://localhost:3000/health
curl http://localhost:3000/api/stats
curl http://localhost:3000/api/edits/by-wiki
```

### CLI Options

Each service accepts configuration via command-line flags:

```bash
# Ingest: custom broker, topic, wikis
cargo run --bin ingest -- --brokers localhost:19092 --topic wiki.recentchange.raw --wikis enwiki,dewiki

# Transform: custom batch size and flush interval
cd transform && python -m transform --batch-size 1000 --flush-interval 60 --output-dir data

# Serve: custom port and parquet directory
cargo run --bin serve -- --port 8000 --parquet-dir data
```

## Development

```bash
just check          # cargo check --workspace
just build          # cargo build --workspace
just test           # cargo test --workspace (6 integration tests)
just lint           # cargo clippy (deny warnings)
just fmt            # cargo fmt
just fmt-check      # cargo fmt -- --check
just pytest         # python -m pytest (10 tests)
just ci             # fmt-check + lint + test + pytest
```

### Infrastructure

```bash
just infra-up       # Start RedPanda + Console (docker compose up -d)
just infra-down     # Stop containers
just infra-clean    # Stop containers and remove volumes
```

### Python Environment Setup

```bash
cd transform
uv venv
uv pip install -e ".[dev]"
```

## Key Dependencies

### Rust

| Crate | Purpose |
|-------|---------|
| tokio | Async runtime |
| serde + serde_json | JSON serialisation/deserialisation |
| rdkafka (cmake-build) | Kafka/RedPanda client (librdkafka bindings) |
| reqwest + reqwest-eventsource | HTTP client + SSE stream |
| axum (ws) | Web framework with WebSocket support |
| tower-http (cors, trace) | HTTP middleware |
| polars (lazy, parquet) | DataFrame engine (used by serve for reads) |
| clap (derive) | CLI argument parsing |
| tracing + tracing-subscriber | Structured logging |
| thiserror | Error type derivation |
| anyhow | Ergonomic error handling |

### Python

| Package | Purpose |
|---------|---------|
| polars | DataFrame transforms and aggregation |
| confluent-kafka | Kafka consumer (librdkafka bindings) |
| click | CLI framework |
| structlog | Structured logging |
| pytest | Testing |

## Testing

Run the full test suite locally (no Docker or network access required):

```bash
# Run everything in one go
just ci

# Or run Rust and Python tests individually
just test           # 6 Rust integration tests
just pytest         # 10 Python tests
```

The Python tests require the virtual environment to be set up first (see Python Environment Setup above).

### What is tested

**Rust integration tests** (`crates/common/tests/integration_test.rs`):
- WikiEvent deserialisation from realistic JSON (edit and log event types)
- EditSummary conversion with size_change computation
- Default configuration validation for all config structs

**Python tests** (`transform/tests/`):
- `test_processor.py` -- DataFrame creation, edits_by_wiki aggregation, top_editors ranking, activity_by_type grouping
- `test_storage.py` -- Parquet write, roundtrip read, directory creation, multi-file scan

All test fixtures use data that mirrors real Wikimedia recentchange events. No running services (RedPanda, network) are needed -- the tests exercise the data models, transformations, and storage logic in isolation.

## Licence

Apache 2.0 -- see [LICENSE](LICENSE).
