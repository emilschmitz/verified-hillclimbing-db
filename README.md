# Verified Hill-Climbing Query Optimizer

A DB system that uses Dafny formal verification to construct provably correct, hardware-optimized query implementations for analytical SQL workloads. Packaged as a DuckDB C++ Extension that processes queries by executing an autonomous optimization loop (using Z3 and Rust compilation). Optimized query code is cached for instant execution.

## What It Does

1. A SQL query is **deterministically transpiled** into a mathematical `MethodSpec` in Dafny — the ground truth.
2. The hill-climbing optimizer uses an agent (or mock mode) to write an optimized `method RunQuery`.
3. Dafny/Z3 formally proves that the agents output satisfies `MethodSpec`.
4. The verified Dafny is compiled to Rust.
4. We apply some heuristic postprocessing, since the Dafny output is not idiomatic performant Rust.*
5. The code is compiled and executed.
6. Successful optimized binaries are **cached** and loaded directly inside **DuckDB** via the C++ extension.

* This means that the final binary is not formally verified, even though the agents outputs are. Making sure this code is minimal and well tested is an ongoing project. Ideally this would give us the same level of practical guarantees of other DBs.

---

## Quick Start

```bash
# 1. Install dependencies
make install

# 2. Build the DuckDB loadable extension
make extension

# 3. Start the interactive REPL shell and load the extension
./run_duckdb_and_load_extension_and_sbb_dataset.sh
# In the shell:
# SELECT hillclimbing('SELECT SUM(LO_EXTENDEDPRICE * LO_DISCOUNT) FROM lineorder_flat WHERE LO_ORDERDATE >= 19930101 AND LO_ORDERDATE <= 19931231 AND LO_DISCOUNT >= 1 AND LO_DISCOUNT <= 3 AND LO_QUANTITY < 25');
```

### Requirements
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Dafny 4.x](https://github.com/dafny-lang/dafny) — in `PATH`
- [Rust/Cargo](https://rustup.rs/) — for native compilation
- [DuckDB CLI](https://duckdb.org/) — (optional) for running the extension in standard terminal sessions

---

## Repository Structure

```
verified-hillclimbing-db/
├── run_duckdb_and_load_extension_and_sbb_dataset.sh  # Interactive C++ CLI shell launcher
├── TODOS.md             # Consolidated project tasks
├── transpiler/          # SQL → Dafny transpiler (Python package: sql-transpiler)
├── db_extension/        # DuckDB loadable C++ extension and REPL helpers
└── research_loop/       # Autonomous optimization loop
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

