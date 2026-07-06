# Lemma

Verified query synthesis: SQL is transpiled to a Dafny spec, an agent (or mock) writes an optimized `RunQuery`, Dafny/Z3 proves correctness, and the result is compiled to native Rust. Contains a DuckDB extension where optimized binaries are cached and invoked on rerun.

https://github.com/user-attachments/assets/7f7891c7-5ef6-406b-882b-8e01134ed37c

## What It Does

1. A SQL query is **deterministically transpiled** into a mathematical `MethodSpec` in Dafny — the ground truth.
2. The Lemma optimizer uses an agent (or mock mode) to write an optimized `method RunQuery`.
3. Dafny/Z3 formally proves that the agent's output satisfies `MethodSpec`.
4. The verified Dafny is translated to Rust and post-processed for native performance.*
5. The code is compiled and executed.
6. Successful optimized binaries are **cached** and loaded via the DuckDB extension.

* Post-processing rewrites and a few assumptions in the Dafny spec are added for performance. These manipulations should match verified Dafny semantics, but that is only verified empirically; see `research_loop/COMPILATION_GUIDE.md`.

---

## Quick Start

One-time setup, then run the interactive demo:

```bash
make install
./scripts/build_ssb_flat_dataset.sh   # one-time: real ssb-dbgen flat table (~6M rows on disk)
./scripts/demo.sh                     # builds extension if needed, prepares data, opens DuckDB CLI
```

In the DuckDB shell, try Lemma on a query (see the on-screen instructions), e.g.:

```sql
SELECT lemma('SELECT SUM(LO_EXTENDEDPRICE * LO_DISCOUNT) FROM lineorder_flat WHERE ...');
```

`demo.sh` handles extension build, dataset loading (`prepare_data`), and launching DuckDB — you do not need to run those steps separately. The flat table only needs to be built once via `build_ssb_flat_dataset.sh`; after that, `prepare_data` runs automatically whenever you start the demo or the lower-level launcher.

**No agent / offline:** `./scripts/mockdemo.sh` — same UX with a pre-seeded RunQuery (no LLM).

**Lower-level launcher** (DuckDB shell only, no demo UI): `make extension` then `./scripts/duckdb_shell.sh`

### Requirements
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [Dafny 4.x](https://github.com/dafny-lang/dafny) — in `PATH`
- [Rust/Cargo](https://rustup.rs/) — for native compilation
- [DuckDB CLI](https://duckdb.org/) — vendored to `build/duckdb` on first launcher run
- [Cursor Agent CLI](https://cursor.com/docs/agent/cli) — `agent` on `PATH` (for `./scripts/demo.sh`; other agents work too if you set `AGENT_CMD` in `research_loop/config.env`)

---

## Results

Hot-loop latency on SSB `lineorder_flat` (**1.5M rows**) and TPC-H `lineitem` SF1 (**~6M rows**). All engines run **single-threaded** (DuckDB `threads=1`, PostgreSQL without parallel gather, Rust without OpenMP). The timed metric is **hot-loop latency** (`hot_us`): median of timed query-loop executions after warm-up, with table/column load **outside** the timer. Raw numbers: `data/benchmarks/scaling_results.json`, `data/benchmarks/tpch_sf1_results.json`. **Execution environment** (CPU, RAM, WSL): `data/benchmarks/benchmark_environment.json`. See also `docs/verified_benchmark_rundown.md`.

![Benchmark overview: SSB Q1–Q3 + TPC-H Q1/Q6 hot-loop latency](plots/benchmark_overview.png)

Row counts appear under each query label on the chart.

### Per-query notes

**SSB Q1** (revenue sum, 1.5M rows) — Verified **~28% faster than DuckDB** (~8 ms vs ~11 ms) but **~1.7× slower than bare** (~5 ms). Gain vs DuckDB: projected columns + native `MulU64U32`/`AddU64` in the inner loop instead of DuckDB’s generic vector path on a wide flat table. Gap vs bare: `Object<ColsNative>` indexing and the verified runtime wrapper on every row.

**SSB Q2** (selective scalar sum, 1.5M rows) — Verified **~10× faster than DuckDB** and essentially tied with bare (~1.6 ms). Almost no allocation; the loop is a tight filter + native arithmetic that LLVM can fuse. DuckDB pays interpreter/vector setup on a query that does very little work per matching row.

**SSB Q3** (another selective sum, 1.5M rows) — Same pattern as Q2: **~2.7× faster than DuckDB**, near bare (~2.2 ms). Native integer ops + minimal column footprint.

**TPC-H Q1** (two-key string group-by, ~6M rows) — Verified **~14× faster than DuckDB** (~35 ms vs ~480 ms) but **~1.3× slower than bare** (~27 ms). Gain vs DuckDB: `NativeAggStrMap` + schema-driven `AggPushStr_*` — hash aggregation stays in Rust instead of DuckDB’s general group-by. Gap vs bare: ghost map bookkeeping in Dafny codegen and string-key hashing through the verified API.

**TPC-H Q6** (filtered revenue sum, ~6M rows) — Verified **~1.8× faster than DuckDB** and slightly **faster than bare** (~37 ms vs ~41 ms / ~65 ms DuckDB). Selective scan with native mul/add; proof overhead is negligible when most rows are filtered early.

### From verified Dafny to fast Rust

Naive Dafny output is correct but slow: unbounded `int`/`nat`, functional `map` group-bys, sequence comprehensions, and `Object`/`Seq` wrappers everywhere — easy for Z3, bad for LLVM. The pipeline closes much of that gap **without breaking the proof**:

- **SQL → `MethodSpec`** — deterministic transpile; the agent only edits `RunQuery` under fixed `requires ValidCols` / `ensures res == MethodSpec(cols)`.
- **Native externs** — `NativeU32`/`NativeU64`/`NativeI64`, `AddU64`, `MulU64U32`, etc., so hot arithmetic stays fixed-width in Rust.
- **Native aggregation** — `NativeAggMap` / `NativeAggStrMap` + schema-driven `AggPush_*` replace Dafny `map` updates in group-by queries (TPC-H Q1, SSB Q4/Q5).
- **Column projection** — load only columns the query touches (same footprint as bare baseline).
- **Postprocessor** — forward scan, drop dead ghost tuples, `BenchFinish()` skips `ToMap()` materialization at the engine boundary.
- **Validation** — Dafny/Z3 proves `RunQuery` refines `MethodSpec`; Rust is Dafny-translated + postprocessed; benchmark harness checks result equality against DuckDB on sampled runs.

Dafny will always prefer **verified** constructs over fast ones — maps over hash tables, mathematical integers over machine words — so the agent and postprocessor must steer hot paths toward native externs; the proof contract stays the same.

Reproduce the chart:

```bash
uv run python research_loop/benchmark_scaling.py --refresh-queries 1,2,3
uv run python research_loop/benchmark_tpch.py
uv run python scripts/generate_benchmark_overview_plot.py
uv run python research_loop/benchmark_verified.py # single-point check at 50k rows
```
