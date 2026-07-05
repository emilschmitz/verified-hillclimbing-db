"""TPC-H lineitem workload: schema + representative queries for Lemma benchmarks.

GenDB reports TPC-H Q1, Q3, Q6, Q9, Q18; we start with single-table lineitem Q1 + Q6.
Integer-normalized tbl from scripts/export_tpch_lineitem.py (ETL, not engine hardcoding).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TBL = ROOT / "data" / "tpch-sf1" / "lineitem.tbl"

# DuckDB/catalog types after integer ETL export.
schema = {
    "L_ORDERKEY": "BIGINT",
    "L_PARTKEY": "BIGINT",
    "L_SUPPKEY": "BIGINT",
    "L_LINENUMBER": "BIGINT",
    "L_QUANTITY": "INTEGER",
    "L_EXTENDEDPRICE": "BIGINT",
    "L_DISCOUNT": "INTEGER",
    "L_TAX": "INTEGER",
    "L_RETURNFLAG": "VARCHAR",
    "L_LINESTATUS": "VARCHAR",
    "L_SHIPDATE": "INTEGER",
    "L_COMMITDATE": "INTEGER",
    "L_RECEIPTDATE": "INTEGER",
    "L_SHIPINSTRUCT": "VARCHAR",
    "L_SHIPMODE": "VARCHAR",
    "L_COMMENT": "VARCHAR",
}

# TPC-H Q1 shape: 2-char group-by keys, one SUM (full Q1 has 8 aggregates; transpiler: one).
Q1_SQL = """
SELECT l_returnflag, l_linestatus, SUM(l_quantity) AS sum_qty
FROM lineitem
WHERE l_shipdate <= 19980902
GROUP BY l_returnflag, l_linestatus
"""

# TPC-H Q6 shape on integer-normalized discount (stored as hundredths: 4 → 0.04).
Q6_SQL = """
SELECT SUM(l_extendedprice * l_discount) AS revenue
FROM lineitem
WHERE l_quantity >= 1 AND l_quantity <= 50
  AND l_discount >= 1 AND l_discount <= 5
  AND l_shipdate >= 19960101 AND l_shipdate <= 19961231
"""

queries = {"Q1": Q1_SQL.strip(), "Q6": Q6_SQL.strip()}

Q1_RUNQUERY = """
method RunQuery(cols: Cols) returns (res: map<(string, string), NativeU64>)
  requires ValidCols(cols)
  ensures res == MethodSpec(cols)
{
  var agg := new NativeAggStrMap();
  ghost var g: map<(string, string), NativeU64> := map[];
  var i := cols.n();
  while i > 0
    invariant 0 <= i <= cols.n()
    invariant g == MethodSpecHelper(cols, i)
    invariant forall k :: k in g ==> k in agg.Snapshot() && agg.Snapshot()[k] as int == g[k] as int
    invariant forall k :: k in agg.Snapshot() ==> k in g
  {
    i := i - 1;
    if cols.GetL_SHIPDATE(i) <= 19980902
    {
      var term := cols.GetL_QUANTITY(i) as NativeU64;
      cols.AggPushStr_L_RETURNFLAG_L_LINESTATUS(agg, i, term);
      ghost var key := (cols.GetL_RETURNFLAG(i), cols.GetL_LINESTATUS(i));
      ghost var prev := if key in g then g[key] else 0 as NativeU64;
      g := g[key := AddU64(prev, term)];
    }
  }
  res := agg.ToMap();
}
"""

Q6_RUNQUERY = """
method RunQuery(cols: Cols) returns (res: NativeU64)
  requires ValidCols(cols)
  ensures res == MethodSpec(cols)
{
  res := 0 as NativeU64;
  var i := cols.n();
  while i > 0
    invariant 0 <= i <= cols.n()
    invariant res as int == MethodSpecHelper(cols, i) as int
  {
    i := i - 1;
    if cols.GetL_QUANTITY(i) >= 1 && cols.GetL_QUANTITY(i) <= 50
       && cols.GetL_DISCOUNT(i) >= 1 && cols.GetL_DISCOUNT(i) <= 5
       && cols.GetL_SHIPDATE(i) >= 19960101 && cols.GetL_SHIPDATE(i) <= 19961231
    {
      res := AddU64(res, MulU64U32(
        cols.GetL_EXTENDEDPRICE(i) as NativeU64,
        cols.GetL_DISCOUNT(i) as NativeU32));
    }
  }
}
"""

RUNQUERIES = {"Q1": Q1_RUNQUERY, "Q6": Q6_RUNQUERY}
