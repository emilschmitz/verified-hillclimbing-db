```dafny
method RunQuery(data: seq<Row>) returns (res: map<(bv32, string), int>)
  ensures res == MethodSpec(data)
{
  res := map[];
  var i := |data|;
  while i > 0
    invariant 0 <= i <= |data|
    invariant res == MethodSpec(data[i..])
  {
    i := i - 1;
    var row := data[i];
    if (row.P_CATEGORY == "MFGR#12" && row.S_REGION == "AMERICA") {
      var key := (row.D_YEAR, row.P_BRAND);
      res := res[key := (if key in res then res[key] else 0) + (row.LO_REVENUE as int)];
    }
  }
}
```