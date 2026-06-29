# Compilation Reference: Dafny → Rust Translation Guide

This document explains how Dafny constructs map to Rust code after the two-stage
compilation pipeline (Dafny → Rust codegen → post-processor → Cargo release build).

**The optimization agent should read this file before writing code.**
The agent may only write to `research_loop/agent_scratchpad.md`.

---

## The Two-Stage Pipeline

```
Dafny verify  →  dafny translate rs  →  optimize_rust_file (harness.py)  →  cargo build --release
```

- **Stage 1 (Verification):** Dafny/Z3 proves the `ensures` clause using mathematical types.
  Write loop invariants here. Use `int` for the accumulator to avoid Z3 bit-blasting timeouts.
- **Stage 2 (Post-Processor):** `harness.py:optimize_rust_file()` rewrites the compiled Rust
  before Cargo sees it. Only constructs that the post-processor recognizes become fast.

> [!IMPORTANT]
> **Verification runs on the original Dafny. The post-processor only touches Rust output.**
> If you write a verified proof, it stays verified. If you write Rust-unfriendly Dafny,
> it compiles and runs correctly — just slowly.

---

## Type Translation Table

| Dafny type | Default Rust | After post-processor | Cost |
|:---|:---|:---|:---|
| `int` (accumulator `res`) | `DafnyInt` (heap `BigInt`) | `u64` ✅ | O(1) native |
| `int` (loop counter `i`) | `DafnyInt` | `usize` ✅ | O(1) native |
| `int` (other local vars) | `DafnyInt` | `u64` ✅ | O(1) native |
| `bv32` field | `u32` | `u32` (unchanged) | O(1) native |
| `bv64` field | `u64` | `u64` (unchanged) | O(1) native |
| `string` field (WHERE literal) | `Sequence<DafnyChar>` == `string_of(...)` | `&str` comparison ✅ | O(len) but fast |
| `string` field as GROUP BY key | `Sequence<DafnyChar>` | `String` ✅ | Heap alloc (once per row) |
| `seq<Row>` parameter | `&Sequence<Rc<Row>>` | unwrapped to `&[Rc<Row>]` via `.to_array()` ✅ | Direct slice index |
| `seq<bv32>` parameter | `&Sequence<u32>` | unwrapped to `&[u32]` via `.to_array()` ✅ | Direct slice index |
| `map<(bv32, string), int>` accumulator | `Map<(u32, Sequence<DafnyChar>), DafnyInt>` | `HashMap<(u32, String), u64>` ✅ | O(1) amortized |
| `seq<Row>` index `data[i]` | `data.get(&i)` (BigInt key lookup) | `data_vec[i]` (direct slice) ✅ | O(1) native |
| `data.get(&i)` (after seq unwrap) | Rc<Row> clone | `&data_vec[i]` reference ✅ | Zero copy |

---

## What the Post-Processor Actually Does

The full source is in `research_loop/harness.py` — function `optimize_rust_file()`.

### Scalar (SUM) queries:
- `DafnyInt` accumulator `res` → `u64`
- Loop counter `i`, `len` → `usize`
- `while i.clone() < len.clone()` → `while i < len`
- `i = i.clone() + int!(1)` → `i = i + 1`
- `data.get(&i)` → `data.get_usize(i)`
- `int!(N)` literals → bare `N`
- `int!(expr)` → `(expr as u64)`
- All `&Sequence<T>` parameters → `.to_array()` unwrap + direct slice indexing
- `Rc<Row>` clone → reference borrow

### GROUP BY (map) queries:
- All of the above loop/index passes
- `map<(bv32, string), int>` → `HashMap<(u32, String), u64>`
- `res.update_index(&key, &(prev + val))` → `*res.entry(key).or_insert(0) += val`
- `string_of("LITERAL")` comparisons → `&str` comparison
- `return res.clone()` → `return res`

### What the post-processor CANNOT handle (yet):
- Multi-level nested maps (`map<..., map<...>>`)
- `multiset` types
- `seq<seq<T>>` (nested sequences)
- Recursive function definitions (only `RunQuery` method is touched)
- Ghost variables and lemma calls (ignored safely — only method body is patched)

---

## Writing Optimization-Friendly Dafny

### DO ✅

```dafny
// Use int for the accumulator — instant verification, post-processor converts to u64
method RunQuery(data: seq<Row>) returns (res: int)
  ensures res == MethodSpec(data)
{
  res := 0;
  var i := 0;
  var len := |data|;
  while i < len
    invariant 0 <= i <= len
    invariant res + MethodSpec(data[i..]) == MethodSpec(data)
  {
    var row := data[i];    // post-processor replaces with direct slice ref
    if row.LO_ORDERDATE >= 19930101 && row.LO_DISCOUNT <= 3 {
      res := res + (row.LO_EXTENDEDPRICE as int) * (row.LO_DISCOUNT as int);
    }
    i := i + 1;
  }
}
```

```dafny
// GROUP BY: use map<(bv32, string), int> — post-processor converts to HashMap
method RunQuery(data: seq<Row>) returns (res: map<(bv32, string), int>)
  ensures res == MethodSpec(data)
{
  res := map[];
  var i := 0;
  var len := |data|;
  while i < len
    // ...loop invariant using MergeMap...
  {
    var row := data[i];
    if row.P_CATEGORY == "MFGR#12" && row.S_REGION == "AMERICA" {
      var key := (row.D_YEAR, row.P_BRAND);
      res := res[key := (if key in res then res[key] else 0) + (row.LO_REVENUE as int)];
    }
    i := i + 1;
  }
}
```

### AVOID ❌

```dafny
// ❌ Don't use bv64 for the accumulator — bit-blasting timeouts in Z3
var res: bv64 := 0;

// ❌ Don't use mathematical function calls inside the loop body (slow)
res := res + SomeHelper(data, i);

// ❌ Don't use seq comprehensions in the loop (functional, not imperative)
var filtered := seq(|data|, i => if Cond(data[i]) then data[i].val else 0);

// ❌ Don't declare ghost variables that shadow real ones (confuses the post-processor)
ghost var shadow := res;
```

---

## Performance Targets

All benchmarks on 50,000 SSB rows, `lineorder_flat.tbl`, on this machine:

| Query type | DuckDB baseline | Post-processed Rust target |
|:---|---:|---:|
| Scalar SUM (Q1, Q2, Q3) | ~1,500–3,000 µs | **< 500 µs** (3–10x faster) |
| GROUP BY (Q4, Q5, ...) | ~5,000–8,000 µs | **< 2,000 µs** (target 3–4x faster) |

The current iteration 2 of Q1 achieved **1,019 µs** (3x faster than DuckDB's 3,008 µs).
