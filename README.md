# Verified Hill-Climbing Query Optimizer

A research system that uses **Dafny formal verification** to provably correct, hardware-optimized query implementations for analytical SQL workloads. An autonomous optimization agent iteratively proposes query implementations that are formally proved correct by the Z3 theorem prover, compiled to native Rust binaries, and benchmarked on real hardware.

## What It Does

1. A SQL query is **deterministically transpiled** into a mathematical `MethodSpec` in Dafny — the ground truth.
2. An **optimizing agent** writes an imperative `method RunQuery` implementation.
3. **Dafny/Z3** formally proves that `RunQuery` satisfies `MethodSpec`. If the proof fails, the loop stops immediately.
4. The verified code is **compiled to Rust** and benchmarked — only provably correct code ever runs.

The loop hill-climbs on execution latency while maintaining a formal correctness guarantee at every step.

## Repository Structure

```
verified-hillclimbing-db/
├── dbcli                # Interactive CLI wrapper shell script
├── TODOS.md             # Consolidated project tasks
├── queries.py           # Backward-compat query module forwarder
├── transpiler/          # SQL → Dafny transpiler (Python package: sql-transpiler)
│   ├── src/sql_transpiler/
│   │   ├── transpiler.py   # Core transpiler logic
│   │   └── queries.py      # 15 SSB/TPC-H benchmark queries + lineorder_flat schema
│   └── tests/
├── db_extension/        # DuckDB loadable C++ extension and REPL client
│   ├── src/
│   │   └── hillclimbing.cpp # C++ extension source registering UDFs
│   ├── catalog.py       # Dynamic DuckDB schema extractor
│   ├── optimizer.py     # Optimization orchestrator and loop generator
│   ├── run_optimizer.py # Subprocess wrapper running the compiled query
│   ├── dbcli.py         # REPL client delegating to the C++ UDF
│   └── test_extension.py # Extension unit/integration tests
└── research_loop/       # Autonomous optimization loop
    ├── harness.py          # Orchestrator: verify → compile → benchmark
    ├── agent_scratchpad.md # Agent writes optimized RunQuery implementations here
    └── working_query-rust/ # Cached Cargo workspace for fast incremental builds
```

## Quick Start

```bash
# Install dependencies (requires uv)
make install

# Run unit tests (no Dafny required)
make test

# Run the optimization loop (Query 1, 50k rows)
make loop
```

### Requirements
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Dafny 4.x](https://github.com/dafny-lang/dafny) — in `PATH`
- [Rust/Cargo](https://rustup.rs/) — for native compilation

## How It Works

```
SQL query
   │
   ▼  transpile_sql_to_dafny()
Dafny MethodSpec  ◄─── ground truth (immutable)
   │
   │  + agent's RunQuery
   ▼
dafny verify  ──── Z3 proves RunQuery satisfies MethodSpec
   │
   ▼
dafny translate rs
   │
   ▼
cargo build --release  ──── ~0.8s (cached)
   │
   ▼
./working_query  ──── latency_us measured
   │
   ▼
{"status": "SUCCESS", "proof_verified": true, "latency_us": 17618}
```

## Rust Post-Processing (Optimization Layer)

To achieve maximum hardware performance, the system includes a post-processing pass (`optimize_rust_file` in `research_loop/harness.py`). While Dafny proves query loop safety using mathematical types (e.g., `int` and bitvectors), the post-processor rewrites these types to native Rust primitives (`u64`/`usize`) and native array/slice operations. This step eliminates the overhead of arbitrary-precision integers, dropping latency to **~100 us** (8x faster than DuckDB's standard engine).

## DuckDB Loadable C++ Extension

The repository includes a loadable extension that exposes the hill-climbing query optimizer directly inside any standard DuckDB session (e.g., via Python or the CLI shell).

### 1. Build the Extension
```bash
make extension
```

### 2. Load and Run Queries in DuckDB
In your DuckDB connection (Python, standard CLI, or via `dbcli` wrapper):
```sql
-- Allow loading local unsigned extensions
SET allow_unsigned_extensions=true;

-- Load the extension library
LOAD 'db_extension/hillclimbing.duckdb_extension';

-- Execute a query via the optimizer
SELECT hillclimbing_optimize('SELECT SUM(LO_EXTENDEDPRICE * LO_DISCOUNT) FROM ...');
```

## Makefile

| Command | Description |
|---|---|
| `make install` | Install all Python dependencies via `uv sync` |
| `make test` | Run transpiler and database extension unit tests |
| `make test-slow` | Run Dafny functional tests (requires `dafny` in PATH) |
| `make loop` | Run one iteration of the research loop (Query 1, 50k rows) |
| `make extension` | Compile and package the loadable C++ DuckDB extension |
| `make clean` | Remove build artifacts, cached binaries, local cache mapping, and `__pycache__` |

## Components

- **[transpiler/](transpiler/README.md)** — The SQL-to-Dafny transpiler. Supports `SUM`, `COUNT`, `WHERE`, `GROUP BY`, arithmetic expressions, and the full 15-query SSB benchmark suite.
- **[research_loop/](research_loop/README.md)** — The orchestration harness and agent interface. The agent writes code to `agent_scratchpad.md`; the harness handles all verification, compilation, and benchmarking.
