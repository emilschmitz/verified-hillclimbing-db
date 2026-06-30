
datatype Row = Row(
  LO_ORDERKEY: bv32,
  LO_LINENUMBER: bv32,
  LO_CUSTKEY: bv32,
  LO_PARTKEY: bv32,
  LO_SUPPKEY: bv32,
  LO_ORDERDATE: bv32,
  LO_ORDERPRIORITY: string,
  LO_SHIPPRIORITY: bv32,
  LO_QUANTITY: bv32,
  LO_EXTENDEDPRICE: bv64,
  LO_ORDTOTALPRICE: bv64,
  LO_DISCOUNT: bv32,
  LO_REVENUE: bv64,
  LO_SUPPLYCOST: bv64,
  LO_TAX: bv32,
  LO_COMMITDATE: bv32,
  LO_SHIPMODE: string,
  C_NAME: string,
  C_ADDRESS: string,
  C_CITY: string,
  C_NATION: string,
  C_REGION: string,
  C_PHONE: string,
  C_MKTSEGMENT: string,
  S_NAME: string,
  S_ADDRESS: string,
  S_CITY: string,
  S_NATION: string,
  S_REGION: string,
  S_PHONE: string,
  P_NAME: string,
  P_MFGR: string,
  P_CATEGORY: string,
  P_BRAND: string,
  P_COLOR: string,
  P_TYPE: string,
  P_SIZE: bv32,
  P_CONTAINER: string,
  D_YEAR: bv32,
  D_YEARMONTHNUM: bv32,
  D_WEEKNUMINYEAR: bv32
)

method RunQuery(data: seq<Row>) returns (res: int)
{
  res := 0;
  var len := |data|;
  var i := 0;
  while i < len {
    var row := data[i];
    res := res + row.LO_TAX as int;
    i := i + 1;
  }
}

method Main() {
  var data := seq(10, i => Row(0,0,0,0,0,0,"",0,0,0,0,0,0,0,3,0,"","","","","","","","","","","","","","","","","","","","",0,"",0,0,0));
  var opt_res := RunQuery(data);
  print "OUTPUT: ", opt_res, "\n";
}
