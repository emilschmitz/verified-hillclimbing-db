#!/usr/bin/env python3
"""Quick TPC-H lineitem benchmark: DuckDB vs verified Rust (Q1 + Q6, SF1 default)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db_extension import DatabaseCatalog
from research_loop.admit_runquery import admit_runquery
from research_loop.postprocessor import postprocess, inject_hot_loop_main
from research_loop.tpch_workload import (
    DEFAULT_TBL,
    Q1_SQL,
    Q6_SQL,
    RUNQUERIES,
    queries,
)

RESEARCH = ROOT / "research_loop"
RUNTIME = RESEARCH / "working_query-rust" / "runtime"
NATIVE_OPS = RESEARCH / "native_bridge" / "src" / "native_ops.rs"
NATIVE_AGG = RESEARCH / "native_bridge" / "src" / "native_agg.rs"
RESULTS_PATH = ROOT / "data" / "benchmarks" / "tpch_sf1_results.json"

TABLE = "lineitem"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def duckdb_connect(tbl: Path):
    import duckdb

    con = duckdb.connect()
    con.execute(
        f"CREATE TABLE {TABLE} AS "
        f"SELECT * FROM read_csv('{tbl}', delim='|', header=true, quote='\"')"
    )
    return con


def bench_duckdb(con, sql: str, *, threads: int | None = None) -> int:
    if threads is not None:
        con.execute(f"SET threads TO {threads}")
    for _ in range(2):
        con.execute(sql).fetchall()
    t0 = time.perf_counter()
    con.execute(sql).fetchall()
    return int((time.perf_counter() - t0) * 1_000_000)


def bench_bare(query_key: str, tbl: Path, limit: int) -> int:
    env = os.environ.copy()
    env["RUSTFLAGS"] = "-C target-cpu=native"
    r = run(
        [
            "cargo", "run", "--release", "--quiet", "--bin", "bench_tpch",
            query_key.lower(), str(tbl), str(limit),
        ],
        cwd=RESEARCH / "bench_bare",
        timeout=600,
        env=env,
    )
    if r.returncode != 0:
        return -1
    m = re.search(r"QUERY_LATENCY_US:\s*(\d+)", r.stdout)
    return int(m.group(1)) if m else -1


def build_and_bench_verified(query_key: str, tbl: Path, *, rebuild: bool = False) -> dict:
    """Build verified binary once per query id; reuse benchmark_scaling helpers."""
    from sql_transpiler import transpile_sql_to_dafny_columnar, generate_cols_native_rs, project_schema_for_query

    q_sql = queries[query_key]
    runquery = RUNQUERIES[query_key]
    catalog = DatabaseCatalog()
    schema = catalog.get_table_schema(TABLE)
    query_schema = project_schema_for_query(q_sql, schema)
    spec = transpile_sql_to_dafny_columnar(q_sql, query_schema)
    src = f'{spec}\n\n{runquery}\n\nmethod {{:verify false}} Main() {{ print "SUCCESS\\n"; }}\n'

    work = RESEARCH / "bench_build" / f"tpch_{query_key.lower()}"
    bin_path = work / "q-rust" / "target" / "release" / "bench"
    meta_path = tbl.parent / "dataset_meta.json"
    if meta_path.is_file():
        limit = int(json.loads(meta_path.read_text())["row_count"])
    else:
        limit = sum(1 for _ in open(tbl)) - 1

    if not rebuild and bin_path.is_file():
        t0 = time.perf_counter()
        r = run([str(bin_path), str(tbl), str(limit)], cwd=ROOT, timeout=600)
        wall_s = time.perf_counter() - t0
        if r.returncode != 0:
            return {"error": (r.stdout + r.stderr)[-500:], "wall_s": round(wall_s, 3)}
        m = re.search(r"QUERY_LATENCY_US:\s*(\d+)", r.stdout)
        hot = int(m.group(1)) if m else -1
        return {"hot_us": hot, "wall_s": round(wall_s, 3), "rows": limit, "cached": True}

    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    dfy = work / "q.dfy"
    cols_rs = work / "cols_native.rs"
    dfy.write_text(src)
    cols_rs.write_text(generate_cols_native_rs(query_schema, sql_str=q_sql))

    admission = admit_runquery(src)
    if not admission.ok:
        return {"error": "; ".join(admission.violations)}

    v = run(["dafny", "verify", "--allow-warnings", str(dfy)], timeout=600)
    if v.returncode != 0:
        return {"error": (v.stdout + v.stderr)[-800:]}

    t = run(
        [
            "dafny", "translate", "rs", "--enforce-determinism", "--no-verify", "--allow-warnings",
            str(dfy), str(cols_rs), str(NATIVE_OPS), str(NATIVE_AGG),
        ],
        cwd=work,
        timeout=600,
    )
    if t.returncode != 0:
        return {"error": (t.stdout + t.stderr)[-800:]}

    proj = work / "q-rust"
    main_rs = proj / "src" / "main.rs"
    shutil.copy(proj / "src" / "q.rs", main_rs)
    (proj / "Cargo.toml").write_text(
        f'[package]\nname = "bench"\nversion = "0.1.0"\nedition = "2021"\n'
        f'[dependencies]\ndafny_runtime = {{ path = "{RUNTIME}" }}\n'
    )
    postprocess(str(main_rs), str(tbl), 50_000, allow_fast_native_agg=admission.allow_fast_native_agg)
    inject_hot_loop_main(str(main_rs), str(tbl), 50_000)
    env = os.environ.copy()
    env["RUSTFLAGS"] = "-C target-cpu=native"
    b = run(["cargo", "build", "--release"], cwd=proj, timeout=600, env=env)
    if b.returncode != 0:
        return {"error": (b.stdout + b.stderr)[-800:]}

    bin_path = proj / "target" / "release" / "bench"
    t0 = time.perf_counter()
    r = run([str(bin_path), str(tbl), str(limit)], cwd=ROOT, timeout=600)
    wall_s = time.perf_counter() - t0
    if r.returncode != 0:
        return {"error": (r.stdout + r.stderr)[-500:], "wall_s": round(wall_s, 3)}
    m = re.search(r"QUERY_LATENCY_US:\s*(\d+)", r.stdout)
    hot = int(m.group(1)) if m else -1
    return {"hot_us": hot, "wall_s": round(wall_s, 3), "rows": limit, "cached": False}


def main() -> None:
    tbl = Path(os.environ.get("LEMMA_TPCH_LINEITEM_TBL", DEFAULT_TBL))
    if not tbl.is_file():
        print(f"Missing {tbl}; run: uv run python scripts/export_tpch_lineitem.py --sf 1")
        sys.exit(1)

    meta = json.loads((tbl.parent / "dataset_meta.json").read_text()) if (tbl.parent / "dataset_meta.json").is_file() else {}
    rows = meta.get("row_count", "?")
    print(f"=== TPC-H lineitem SF1 ({rows:,} rows) — DuckDB 1t vs bare vs verified ===\n" if isinstance(rows, int) else f"=== TPC-H lineitem ({tbl.name}) ===\n")

    con = duckdb_connect(tbl)
    limit = int(meta.get("row_count", 0)) if meta else 0
    results = {"table": str(tbl), "meta": meta, "queries": {}}

    for key, sql in [("Q1", Q1_SQL.strip()), ("Q6", Q6_SQL.strip())]:
        print(f"--- {key} ---")
        duck1 = bench_duckdb(con, sql, threads=1)
        duck_mt = bench_duckdb(con, sql, threads=None)
        bare = bench_bare(key, tbl, limit) if limit else -1
        ver = build_and_bench_verified(key, tbl, rebuild=False)
        v_us = ver.get("hot_us", -1)
        print(f"  DuckDB 1t:     {duck1:>10,} µs")
        print(f"  DuckDB MT:     {duck_mt:>10,} µs")
        print(f"  Bare Rust 1t:  {bare:>10,} µs")
        if "error" in ver:
            print(f"  Verified 1t:   ERROR — {ver['error'][:200]}")
        else:
            tag = " (cached)" if ver.get("cached") else ""
            print(f"  Verified 1t:   {v_us:>10,} µs{tag}")
        if bare > 0 and duck1 > 0:
            print(f"  bare vs duck1t: {duck1 / bare:.2f}× ({'bare wins' if bare < duck1 else 'duck wins'})")
        if v_us > 0 and duck1 > 0:
            print(f"  ver vs duck1t:  {duck1 / v_us:.2f}× ({'verified wins' if v_us < duck1 else 'duck wins'})")
        results["queries"][key] = {
            "sql": sql,
            "duckdb_1t_us": duck1,
            "duckdb_mt_us": duck_mt,
            "bare_rust_us": bare,
            "verified_rust": ver,
        }
        print()

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"Saved {RESULTS_PATH}")


if __name__ == "__main__":
    main()
