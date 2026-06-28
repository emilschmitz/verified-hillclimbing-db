# Auto-Research and Benchmarking Sandbox Loop

This folder contains an isolated sandbox environment designed for a Karpathy-style auto-research loop. It allows an optimizing agent to write verified, hardware-optimized query implementation variants and test them against deterministic Dafny proof verification, compilation, and latency profiling.

## Directory Structure
- `config.env`: Configures verify and compile timeouts.
- `agent_scratchpad.md`: The interface file for the optimization agent. The agent writes its design hypothesis, invariants, and implementation block (`method RunQuery`) here.
- `harness.py`: The orchestrator script. It dynamically transpiles the target SQL query, embeds the agent's optimized code block, runs Dafny static-proof verification, compiles the binary to native Rust in release mode, and measures the execution latency in microseconds.
- `working_query-rust/`: Persistent Cargo workspace acting as a compilation cache to bring rebuild times down to ~0.8 seconds.

---

## Running the Benchmarks

You can run the harness using the virtual environment's python interpreter:

```bash
# Run benchmarking for Query 1 with a dataset size of 50000 (default)
.venv/bin/python3 research_loop/harness.py -q 1 --dataset-size 50000

# Run benchmarking for Query 4 with a smaller dataset size
.venv/bin/python3 research_loop/harness.py -q 4 --dataset-size 5000
```

The harness output is structured JSON sent to stdout:
```json
{
  "status": "SUCCESS",
  "proof_verified": true,
  "latency_us": 17618,
  "compiler_error": ""
}
```

---

## Query Specifications and Return Signatures

When switching query indexes via `-q/--query`, the type signature of `MethodSpec` and `RunQuery` will change. Below is the mapping of all 15 SSB queries to their expected return types:

| Query Index | Return Type | Description |
|---|---|---|
| **Query 1, 2, 3, 14** | `int` | Aggregations returning a single integer sum |
| **Query 4, 5, 6, 11, 12** | `map<(int, string), int>` | Grouping by year and nation/category/brand |
| **Query 7, 8, 9, 10** | `map<(string, string, int), int>` | Grouping by customer nation, supplier nation, and year |
| **Query 13** | `map<(int, string, string), int>` | Grouping by year, category, and brand |
| **Query 15** | `map<string, int>` | Grouping by category |

### Example for Query 1, 2, 3, 14:
```dafny
method RunQuery(data: seq<Row>) returns (res: int)
  ensures res == MethodSpec(data)
{
  res := MethodSpec(data);
}
```

### Example for Query 4, 5, 6, 11, 12:
```dafny
method RunQuery(data: seq<Row>) returns (res: map<(int, string), int>)
  ensures res == MethodSpec(data)
{
  res := MethodSpec(data);
}
```

### Example for Query 7, 8, 9, 10:
```dafny
method RunQuery(data: seq<Row>) returns (res: map<(string, string, int), int>)
  ensures res == MethodSpec(data)
{
  res := MethodSpec(data);
}
```

### Example for Query 13:
```dafny
method RunQuery(data: seq<Row>) returns (res: map<(int, string, string), int>)
  ensures res == MethodSpec(data)
{
  res := MethodSpec(data);
}
```

### Example for Query 15:
```dafny
method RunQuery(data: seq<Row>) returns (res: map<string, int>)
  ensures res == MethodSpec(data)
{
  res := MethodSpec(data);
}
```

---

## Caching Strategy
To enable rapid optimization loops, `harness.py` implements a persistent workspace cache:
1. **First Run / Missing Workspace**: If `working_query-rust/` or its `Cargo.toml` is missing (e.g. after a `git clean`), the harness automatically calls `dafny build --target:rs` to generate the complete Cargo project and compile dependencies.
2. **Subsequent Runs**: The harness calls `dafny translate rs` which only outputs the raw Rust file (`src/working_query.rs`), and then builds using `cargo build --release`. This keeps the Cargo build cache hot and keeps iteration compile times **under 1 second**.
