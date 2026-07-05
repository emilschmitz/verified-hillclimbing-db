#!/usr/bin/env python3
"""Export TPC-H lineitem to pipe tbl with integer-friendly columns for Lemma loaders.

Uses DuckDB tpch extension (CALL dbgen). Normalization is workload ETL, not engine code:
  - dates → YYYYMMDD integers
  - money / quantity / discount → integer (discount ×100, extendedprice ×100)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "tpch-sf1" / "lineitem.tbl"
META_PATH = ROOT / "data" / "tpch-sf1" / "dataset_meta.json"


def export_lineitem(sf: float, out_path: Path) -> dict:
    import duckdb

    out_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("INSTALL tpch; LOAD tpch;")
    con.execute(f"CALL dbgen(sf={sf});")
    con.execute(f"""
        COPY (
            SELECT
                l_orderkey,
                l_partkey,
                l_suppkey,
                l_linenumber,
                CAST(l_quantity AS INTEGER) AS l_quantity,
                CAST(ROUND(l_extendedprice * 100) AS BIGINT) AS l_extendedprice,
                CAST(ROUND(l_discount * 100) AS INTEGER) AS l_discount,
                CAST(ROUND(l_tax * 100) AS INTEGER) AS l_tax,
                l_returnflag,
                l_linestatus,
                CAST(strftime(l_shipdate, '%Y%m%d') AS INTEGER) AS l_shipdate,
                CAST(strftime(l_commitdate, '%Y%m%d') AS INTEGER) AS l_commitdate,
                CAST(strftime(l_receiptdate, '%Y%m%d') AS INTEGER) AS l_receiptdate,
                l_shipinstruct,
                l_shipmode,
                l_comment
            FROM lineitem
        ) TO '{out_path.as_posix()}' (
            FORMAT CSV, DELIMITER '|', HEADER true, QUOTE '"'
        )
    """)
    rows = con.execute("SELECT count(*) FROM lineitem").fetchone()[0]
    meta = {"scale_factor": sf, "row_count": int(rows), "table": "lineitem", "path": str(out_path)}
    META_PATH.write_text(json.dumps(meta, indent=2))
    return meta


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sf", type=float, default=1.0, help="TPC-H scale factor (default 1)")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = p.parse_args()
    meta = export_lineitem(args.sf, args.out)
    print(f"Exported {meta['row_count']:,} rows → {args.out} ({args.out.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
