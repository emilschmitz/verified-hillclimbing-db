# Design Note: Hybrid Bitvector/Int Query Compilation

This document outlines the design decisions, trade-offs, and verification strategies behind the Hybrid Bitvector/Int compilation approach used in the verified query optimizer.

---

## 1. The Core Trade-off

When compiling queries from Dafny to Rust, we face two competing requirements:
1. **Low Runtime Latency**: Column scans and comparisons must execute at native CPU speed without heap-allocated types.
2. **Fast Static Verification**: The SMT solver (Z3) must verify the query's correctness relative to the specification without timeouts.

| Data Representation | Z3 Verification | Rust Runtime Execution | Primary Bottleneck |
| :--- | :--- | :--- | :--- |
| **Pure Standard Integers (`int`)** | **Fast (<1s)** | **Slow (589ms)** | `BigInt` heap allocations in Rust loop |
| **Pure Native Bitvectors (`bv32`/`bv64`)** | **Timeouts (>30s)** | **Fast (1.98ms)** | Z3 Bit-Blasting of multiplications |
| **Hybrid Bitvector/Int (Chosen)** | **Fast (~1.5s)** | **Fast (4.43ms)** | Minor overhead on matching rows |

---

## 2. How the Hybrid Design Works

The hybrid design decouples the **storage layer** from the **aggregation layer**:

### 1. Storage & Scan Layer (Bitvectors)
The database row schema (`Row`) defines all columns as native bitvectors (`bv32` or `bv64` depending on size).
* **Rust Compilation**: Translates directly to primitive `u32` and `u64` values.
* **Scan Performance**: Filtering checks (e.g., `row.LO_ORDERDATE >= 19930101`) compile to native CPU comparisons, running with zero memory allocation.

### 2. Aggregation Layer (Standard `int`)
During the query aggregation stage, we cast the primitive values to mathematical `int` *after* the filters match, but before the math/addition is performed:
```dafny
function ComputeTerm(row: Row): int
{
  if row.LO_ORDERDATE >= 19930101 && ...
  then (row.LO_EXTENDEDPRICE as int) * (row.LO_DISCOUNT as int)
  else 0
}
```
* **Z3 Verification**: Because the multiplication and summation (`res = res + term`) are evaluated using infinite-precision `int`, Z3 can verify loop induction algebraically in milliseconds. It never has to "bit-blast" hardware multiplication circuits.
* **Rust Performance**: Since only a small percentage of rows pass OLAP query filters (typically ~1.5% in SSB/TPC-H workloads), the overhead of allocating `BigInt` wrappers for summation is negligible.

---

## 3. When This Approach Does and Does Not Work

### Where it works (Standard OLAP)
* **Selective Aggregation**: Queries with highly selective `WHERE` clauses (e.g., standard SSB/TPC-H workloads).
* **Non-aggregating/Filter-only Queries**: Queries returning raw rows (e.g. `SELECT col1, col2 WHERE ...`). Because there is no multiplication/summation, Z3 does not experience bit-blasting issues, and we can keep everything native.

### Limitations & Drawbacks
* **Non-selective Queries**: If a query has no filters (e.g. `SELECT SUM(col) FROM table` where 100% of rows match), the runtime will perform `N` `BigInt` allocations, degrading performance compared to a pure `u64` loop.
* **Complex Math in Filters**: If a query has math expressions inside the filter check itself (e.g. `WHERE price * discount > limit`), we must cast to `int` inside the filter. This introduces minor heap allocation overhead during the scan phase.
