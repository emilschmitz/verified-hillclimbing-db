#!/usr/bin/env python3
"""Benchmark verified Q1/Q11 against DuckDB and bare Rust baselines."""
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from db_extension import DatabaseCatalog
from research_loop.postprocessor import postprocess, inject_hot_loop_main
from research_loop.ssb_workload import queries
from sql_transpiler import transpile_sql_to_dafny

RESEARCH = os.path.join(ROOT, "research_loop")
RUNTIME = os.path.join(RESEARCH, "working_query-rust", "runtime")
TBL = os.path.join(ROOT, "ssb-dbgen", "lineorder_flat.tbl")
LIMIT = 50000

Q1_RUNQUERY = """
method RunQuery(data: seq<Row>) returns (res: NativeU64)
  ensures res == MethodSpec(data)
{
  res := 0 as NativeU64;
  var i := |data|;
  while i > 0
    invariant 0 <= i <= |data|
    invariant (res as int) == MethodSpec(data[i..]) as int
  {
    i := i - 1;
    var row := data[i];
    if row.LO_ORDERDATE >= 19930101 && row.LO_ORDERDATE <= 19931231
       && row.LO_DISCOUNT >= 1 && row.LO_DISCOUNT <= 3
       && row.LO_QUANTITY < 25
    {
      assume 0 <= (row.LO_EXTENDEDPRICE as int) * (row.LO_DISCOUNT as int) < 18446744073709551616;
      var term := ((row.LO_EXTENDEDPRICE as int) * (row.LO_DISCOUNT as int)) as NativeU64;
      assume (res as int) + (term as int) < 18446744073709551616;
      res := ((res as int) + (term as int)) as NativeU64;
    }
  }
}
"""

Q11_RUNQUERY = """
method RunQuery(data: seq<Row>) returns (res: map<(NativeU32, string), NativeI64>)
  ensures res == MethodSpec(data)
  requires forall j :: 0 <= j < |data| ==>
    -9223372036854775808 <= (data[j].LO_REVENUE as int) - (data[j].LO_SUPPLYCOST as int) < 9223372036854775808
{
  res := map[];
  var i := |data|;
  while i > 0
    invariant 0 <= i <= |data|
    invariant res == MethodSpec(data[i..])
    invariant forall k :: k in res ==>
      -9223372036854775808 <= res[k] as int < 9223372036854775808
  {
    i := i - 1;
    var row := data[i];
    if row.C_REGION == "AMERICA" && row.S_REGION == "AMERICA" && row.P_MFGR == "MFGR#1" {
      var key := (row.D_YEAR, row.C_NATION);
      var term := ((row.LO_REVENUE as int) - (row.LO_SUPPLYCOST as int)) as NativeI64;
      var prev := if key in res then res[key] else 0 as NativeI64;
      assume -9223372036854775808 <= (prev as int) + (term as int) < 9223372036854775808;
      res := res[key := ((prev as int) + (term as int)) as NativeI64];
    }
  }
}
"""


def run_cmd(cmd, cwd=None, timeout=120):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def bench_duckdb(sql: str) -> int:
    """Load once, warm up 2x, time 3rd query only (matches bare Rust)."""
    import duckdb
    con = duckdb.connect()
    con.execute(
        f"CREATE TABLE lineorder_flat AS "
        f"SELECT * FROM read_csv('{TBL}', delim='|', header=true, quote='\"') "
        f"LIMIT {LIMIT}"
    )
    for _ in range(2):
        con.execute(sql).fetchall()
    t0 = time.perf_counter()
    con.execute(sql).fetchall()
    return int((time.perf_counter() - t0) * 1_000_000)


def bench_bare(name: str) -> int:
    res = run_cmd(
        ["cargo", "run", "--release", "--bin", name, TBL, str(LIMIT)],
        cwd=os.path.join(RESEARCH, "bench_bare"),
    )
    m = re.search(r"QUERY_LATENCY_US:\s*(\d+)", res.stdout)
    return int(m.group(1)) if m else -1


def bench_verified(query_idx: int, runquery: str) -> tuple[int, bool]:
    catalog = DatabaseCatalog()
    schema = catalog.get_table_schema("lineorder_flat")
    spec = transpile_sql_to_dafny(queries[query_idx - 1], schema)
    main = 'method {:verify false} Main() { var data: seq<Row> := []; var _ := RunQuery(data); print "SUCCESS\\n"; }'
    src = f"{spec}\n\n{runquery}\n\n{main}\n"

    build = os.path.join(RESEARCH, "bench_build")
    shutil.rmtree(build, ignore_errors=True)
    os.makedirs(build)
    dfy = os.path.join(build, "q.dfy")
    with open(dfy, "w") as f:
        f.write(src)

    v = run_cmd(["dafny", "verify", "--allow-warnings", dfy], timeout=60)
    if v.returncode != 0:
        print(v.stdout, v.stderr)
        return -1, False

    t = run_cmd(["dafny", "translate", "rs", "--enforce-determinism", "--no-verify", "--allow-warnings", dfy], cwd=build)
    if t.returncode != 0:
        print(t.stdout, t.stderr)
        return -1, False

    proj = os.path.join(build, "q-rust")
    rs = os.path.join(proj, "src", "q.rs")
    main_rs = os.path.join(proj, "src", "main.rs")
    shutil.copy(rs, main_rs)
    shutil.copy(os.path.join(RESEARCH, "working_query-rust", "src", "dataset.rs"), os.path.join(proj, "src", "dataset.rs"))
    cargo = os.path.join(proj, "Cargo.toml")
    with open(cargo, "w") as f:
        f.write(f'[package]\nname = "bench"\nversion = "0.1.0"\nedition = "2021"\n[dependencies]\ndafny_runtime = {{ path = "{RUNTIME}" }}\n')

    postprocess(main_rs, TBL, LIMIT)
    inject_hot_loop_main(main_rs, TBL, LIMIT)
    env = os.environ.copy()
    env["RUSTFLAGS"] = "-C target-cpu=native"
    b = run_cmd(["cargo", "build", "--release"], cwd=proj, timeout=120)
    if b.returncode != 0:
        print(b.stdout, b.stderr)
        return -1, True

    bin_path = os.path.join(proj, "target", "release", "bench")
    r = run_cmd([bin_path], timeout=30)
    m = re.search(r"QUERY_LATENCY_US:\s*(\d+)", r.stdout)
    return (int(m.group(1)) if m else -1), True


def main():
    q1_sql = queries[0]
    q11_sql = queries[10]
    print("=== Benchmarks (50k rows, hot RunQuery loop only) ===")
    print(f"DuckDB Q1:  {bench_duckdb(q1_sql)} us")
    print(f"Bare Q1:    {bench_bare('bench_q1')} us")
    v1, ok1 = bench_verified(1, Q1_RUNQUERY)
    print(f"Verified Q1: {v1} us (verified={ok1})")
    print(f"DuckDB Q11: {bench_duckdb(q11_sql)} us")
    print(f"Bare Q11:   {bench_bare('bench_q11')} us")
    v11, ok11 = bench_verified(11, Q11_RUNQUERY)
    print(f"Verified Q11: {v11} us (verified={ok11})")


if __name__ == "__main__":
    main()
