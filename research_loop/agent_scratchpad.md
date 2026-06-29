# Agent Optimization Scratchpad

## Design Hypothesis
- Process elements iteratively in O(N) linear time.
- Accumulate the sum using suffix verification state `res + MethodSpec(data[i..]) == MethodSpec(data)`.

## Correctness & Proof Strategy
- Standard inductive invariant on the suffix slice of the sequence.

## Optimized Code Variant
```dafny
method RunQuery(data: seq<Row>) returns (res: int)
  ensures res == MethodSpec(data)
{
  res := 0;
  var min_date: bv32 := 19930101;
  var max_date: bv32 := 19931231;
  var min_disc: bv32 := 1;
  var max_disc: bv32 := 3;
  var max_qty: bv32 := 25;
  for i := 0 to |data|
    invariant res + MethodSpec(data[i..]) == MethodSpec(data)
  {
    var row := data[i];
    var term := if row.LO_ORDERDATE >= min_date && row.LO_ORDERDATE <= max_date && row.LO_DISCOUNT >= min_disc && row.LO_DISCOUNT <= max_disc && row.LO_QUANTITY < max_qty then (row.LO_EXTENDEDPRICE as int) * (row.LO_DISCOUNT as int) else 0;
    res := res + term;
  }
}
```
