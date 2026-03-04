# option3 task runner

default:
    @just --list

# Rust targets

check:
    cargo check --workspace

build:
    cargo build --workspace

test:
    cargo test --workspace

lint:
    cargo clippy --workspace --all-targets -- -D warnings

fmt:
    cargo fmt --all

fmt-check:
    cargo fmt --all -- --check

# Python targets

pytest:
    cd transform && python -m pytest -v

# Infrastructure

infra-up:
    docker compose -f docker/docker-compose.yml up -d

infra-down:
    docker compose -f docker/docker-compose.yml down

infra-clean:
    docker compose -f docker/docker-compose.yml down -v

# Run services

run-ingest *ARGS:
    cargo run --bin ingest -- {{ARGS}}

run-transform *ARGS:
    cd transform && python -m transform {{ARGS}}

run-serve *ARGS:
    cargo run --bin serve -- {{ARGS}}

# CI (runs all checks)

ci: fmt-check lint test pytest
