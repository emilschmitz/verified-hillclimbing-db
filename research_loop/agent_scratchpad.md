```dafny
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
```
