# Agent Optimization Scratchpad

## Design Hypothesis
- Query 4 = SSB Q2.1: GROUP BY D_YEAR, P_BRAND with filter P_CATEGORY='MFGR#12' AND S_REGION='AMERICA'.
- MethodSpec returns `map<(bv32, string), int>` — NOT int.
- Accumulate via an imperative map with O(N) per-row update.
- Use a `MergeMap` ghost helper defined over finite key sets (.Keys union).
- The loop invariant expresses: `MergeMap(res, MethodSpec(data[i..])) == MethodSpec(data)`

## Correctness & Proof Strategy
- MergeMap is defined over `m1.Keys + m2.Keys` (both finite) so Dafny can bound the comprehension.
- Key lemma: at loop end i==len, MethodSpec(data[len..]) == MethodSpec([]) == map[].
- MergeMap(res, map[]) == res, so res == MethodSpec(data).

## Optimized Code Variant
```dafny
function MergeMap(m1: map<(bv32, string), int>, m2: map<(bv32, string), int>): map<(bv32, string), int>
{
  map k | k in m1.Keys + m2.Keys ::
    (if k in m1 then m1[k] else 0) + (if k in m2 then m2[k] else 0)
}

lemma MergeMapEmpty(m: map<(bv32, string), int>)
  ensures MergeMap(m, map[]) == m
{
  var empty: map<(bv32, string), int> := map[];
  assert m.Keys + empty.Keys == m.Keys;
  assert forall k :: k in MergeMap(m, empty) <==> k in m;
  assert forall k | k in m :: MergeMap(m, empty)[k] == m[k];
}

lemma MethodSpecUnroll(data: seq<Row>)
  requires |data| > 0
  ensures MethodSpec(data) ==
    (var row := data[0];
     var tailMap := MethodSpec(data[1..]);
     if row.P_CATEGORY == "MFGR#12" && row.S_REGION == "AMERICA" then
       var key := (row.D_YEAR, row.P_BRAND);
       var val := if key in tailMap then tailMap[key] else 0;
       tailMap[key := val + (row.LO_REVENUE as int)]
     else
       tailMap)
{
}

lemma MergeMapStepMatch(
  res: map<(bv32, string), int>,
  key: (bv32, string),
  term: int,
  tail: map<(bv32, string), int>
)
  ensures
    var newRes := res[key := (if key in res then res[key] else 0) + term];
    var newTail := tail[key := (if key in tail then tail[key] else 0) + term];
    MergeMap(newRes, tail) == MergeMap(res, newTail)
{
  var newRes := res[key := (if key in res then res[key] else 0) + term];
  var newTail := tail[key := (if key in tail then tail[key] else 0) + term];
  assert newRes.Keys == res.Keys + {key};
  assert newTail.Keys == tail.Keys + {key};
  assert MergeMap(newRes, tail).Keys == MergeMap(res, newTail).Keys;
  forall k | k in MergeMap(newRes, tail) {
    assert MergeMap(newRes, tail)[k] == MergeMap(res, newTail)[k];
  }
}

method RunQuery(data: seq<Row>) returns (res: map<(bv32, string), int>)
  ensures res == MethodSpec(data)
{
  res := map[];
  var i := 0;
  var len := |data|;
  while i < len
    invariant 0 <= i <= len
    invariant MergeMap(res, MethodSpec(data[i..])) == MethodSpec(data)
  {
    var row := data[i];
    ghost var tailSpec := MethodSpec(data[i+1..]);
    MethodSpecUnroll(data[i..]);
    assert data[i..][1..] == data[i+1..];
    if row.P_CATEGORY == "MFGR#12" && row.S_REGION == "AMERICA" {
      var key := (row.D_YEAR, row.P_BRAND);
      MergeMapStepMatch(res, key, (row.LO_REVENUE as int), tailSpec);
      res := res[key := (if key in res then res[key] else 0) + (row.LO_REVENUE as int)];
    }
    i := i + 1;
  }
  MergeMapEmpty(res);
}
```
