#![allow(warnings, unconditional_panic)]
#![allow(nonstandard_style)]
#![cfg_attr(any(), rustfmt::skip)]

pub mod _module {
    static COL_D_YEAR: ::std::sync::OnceLock<Vec<u32>> = ::std::sync::OnceLock::new();
    static COL_LO_REVENUE: ::std::sync::OnceLock<Vec<u64>> = ::std::sync::OnceLock::new();
    static COL_P_BRAND: ::std::sync::OnceLock<Vec<String>> = ::std::sync::OnceLock::new();
    static COL_P_CATEGORY: ::std::sync::OnceLock<Vec<String>> = ::std::sync::OnceLock::new();
    static COL_S_REGION: ::std::sync::OnceLock<Vec<String>> = ::std::sync::OnceLock::new();

    pub use ::dafny_runtime::Sequence;
    pub use ::std::rc::Rc;
    pub use ::dafny_runtime::Map;
    pub use ::dafny_runtime::DafnyChar;
    pub use ::dafny_runtime::DafnyInt;
    pub use ::dafny_runtime::int;
    pub use ::dafny_runtime::map;
    pub use ::dafny_runtime::string_of;
    pub use ::dafny_runtime::truncate;
    pub use ::dafny_runtime::euclidian_modulo;
    pub use ::dafny_runtime::integer_range;
    pub use ::dafny_runtime::Zero;
    pub use ::dafny_runtime::DafnyPrintWrapper;
    pub use ::std::fmt::Debug;
    pub use ::std::fmt::Formatter;
    pub use ::std::fmt::Result;
    pub use ::dafny_runtime::DafnyPrint;
    pub use ::std::cmp::PartialEq;
    pub use ::std::cmp::Eq;
    pub use ::std::hash::Hash;
    pub use ::std::hash::Hasher;
    pub use ::std::convert::AsRef;

    pub struct _default {}

    impl _default {
        /// working_query.dfy(6,1)
        pub fn MethodSpec(data: &Sequence<Rc<Row>>) -> Map<(u32, Sequence<DafnyChar>), DafnyInt> {
            if data.cardinality() == int!(0) {
                map![] as Map<(u32, Sequence<DafnyChar>), DafnyInt>
            } else {
                let mut tailMap: Map<(u32, Sequence<DafnyChar>), DafnyInt> = _default::MethodSpec(&data.drop(&int!(1)));
                let mut row: Rc<Row> = data.get(&int!(0));
                if row.P_CATEGORY().clone() == string_of("MFGR#12") && row.S_REGION().clone() == string_of("AMERICA") {
                    let mut key: (u32, Sequence<DafnyChar>) = (
                            row.D_YEAR().clone(),
                            row.P_BRAND().clone()
                        );
                    let mut val: DafnyInt = if tailMap.contains(&key) {
                            tailMap.get(&key)
                        } else {
                            int!(0)
                        };
                    tailMap.update_index(&key, &(val.clone() + int!(row.LO_REVENUE().clone())))
                } else {
                    tailMap.clone()
                }
            }
        }
        /// working_query.dfy(18,1)
        pub fn RunQuery(data: &Sequence<Rc<Row>>) -> ::std::collections::HashMap<(u32, String), u64> {            let data_vec = data.to_array();
            let col_D_YEAR = COL_D_YEAR.get().expect("column not initialized");
            let col_LO_REVENUE = COL_LO_REVENUE.get().expect("column not initialized");
            let col_P_BRAND = COL_P_BRAND.get().expect("column not initialized");
            let col_P_CATEGORY = COL_P_CATEGORY.get().expect("column not initialized");
            let col_S_REGION = COL_S_REGION.get().expect("column not initialized");

            let mut res: ::std::collections::HashMap<(u32, String), u64> = ::std::collections::HashMap::new();
            let mut i: usize = data.cardinality().as_usize();
            while 0 < i {
                i = i - 1;
                let row = &data_vec[i];
                if col_P_CATEGORY[i] == "MFGR#12" && col_S_REGION[i] == "AMERICA" {
                    let mut key: (u32, String) = (
                            col_D_YEAR[i].clone(),
                            col_P_BRAND[i].clone()
                        );
                    *res.entry(key.clone()).or_insert(0) += (col_LO_REVENUE[i].clone()) as u64;
                }
            };
            return res;
        }
        pub fn load_dataset(file_path: &str, limit: usize) -> Sequence<Rc<Row>> {
            use std::fs::File;
            use std::io::{BufRead, BufReader};
            let file = File::open(file_path).expect("failed to open ssb-dbgen/lineorder_flat.tbl");
            let reader = BufReader::new(file);
            let mut rows = Vec::new();
            for line in reader.lines().skip(1).take(limit) {
                let line = line.expect("failed to read line");
                let fields: Vec<&str> = line.split('|').collect();
                if fields.len() >= 41 {
                    let row = Rc::new(Row::Row {
                        LO_ORDERKEY: fields[0].parse::<u32>().unwrap(),
                        LO_LINENUMBER: fields[1].parse::<u32>().unwrap(),
                        LO_CUSTKEY: fields[2].parse::<u32>().unwrap(),
                        LO_PARTKEY: fields[3].parse::<u32>().unwrap(),
                        LO_SUPPKEY: fields[4].parse::<u32>().unwrap(),
                        LO_ORDERDATE: fields[5].parse::<u32>().unwrap(),
                        LO_ORDERPRIORITY: string_of(fields[6]),
                        LO_SHIPPRIORITY: fields[7].parse::<u32>().unwrap(),
                        LO_QUANTITY: fields[8].parse::<u32>().unwrap(),
                        LO_EXTENDEDPRICE: fields[9].parse::<u64>().unwrap(),
                        LO_ORDTOTALPRICE: fields[10].parse::<u64>().unwrap(),
                        LO_DISCOUNT: fields[11].parse::<u32>().unwrap(),
                        LO_REVENUE: fields[12].parse::<u64>().unwrap(),
                        LO_SUPPLYCOST: fields[13].parse::<u64>().unwrap(),
                        LO_TAX: fields[14].parse::<u32>().unwrap(),
                        LO_COMMITDATE: fields[15].parse::<u32>().unwrap(),
                        LO_SHIPMODE: string_of(fields[16]),
                        C_NAME: string_of(fields[17]),
                        C_ADDRESS: string_of(fields[18]),
                        C_CITY: string_of(fields[19]),
                        C_NATION: string_of(fields[20]),
                        C_REGION: string_of(fields[21]),
                        C_PHONE: string_of(fields[22]),
                        C_MKTSEGMENT: string_of(fields[23]),
                        S_NAME: string_of(fields[24]),
                        S_ADDRESS: string_of(fields[25]),
                        S_CITY: string_of(fields[26]),
                        S_NATION: string_of(fields[27]),
                        S_REGION: string_of(fields[28]),
                        S_PHONE: string_of(fields[29]),
                        P_NAME: string_of(fields[30]),
                        P_MFGR: string_of(fields[31]),
                        P_CATEGORY: string_of(fields[32]),
                        P_BRAND: string_of(fields[33]),
                        P_COLOR: string_of(fields[34]),
                        P_TYPE: string_of(fields[35]),
                        P_SIZE: fields[36].parse::<u32>().unwrap(),
                        P_CONTAINER: string_of(fields[37]),
                        D_YEAR: fields[38].parse::<u32>().unwrap(),
                        D_YEARMONTHNUM: fields[39].parse::<u32>().unwrap(),
                        D_WEEKNUMINYEAR: fields[40].parse::<u32>().unwrap(),
                    });
                    rows.push(row);
                }
            }
                        COL_D_YEAR.get_or_init(|| rows.iter().map(|r| r.D_YEAR().clone()).collect());
            COL_LO_REVENUE.get_or_init(|| rows.iter().map(|r| r.LO_REVENUE().clone()).collect());
            COL_P_BRAND.get_or_init(|| rows.iter().map(|r| r.P_BRAND().to_array().iter().map(|c| c.0).collect::<String>()).collect());
            COL_P_CATEGORY.get_or_init(|| rows.iter().map(|r| r.P_CATEGORY().to_array().iter().map(|c| c.0).collect::<String>()).collect());
            COL_S_REGION.get_or_init(|| rows.iter().map(|r| r.S_REGION().to_array().iter().map(|c| c.0).collect::<String>()).collect());
            Sequence::from_array_owned(rows)
        }
    
        /// working_query.dfy(37,1)
        pub fn Main(_noArgsParameter: &Sequence<Sequence<DafnyChar>>) -> () {
            let mut data: Sequence<Rc<Row>> = _default::load_dataset("/home/emil/projects/verified-hillclimbing-db/ssb-dbgen/lineorder_flat.tbl", 50000);
            let mut opt_res: ::std::collections::HashMap<(u32, String), u64>;
            let start = ::std::time::Instant::now();
            let mut _out0: ::std::collections::HashMap<(u32, String), u64> = ::std::hint::black_box(_default::RunQuery(&data));
            let elapsed_us = start.elapsed().as_micros();
            print!("QUERY_LATENCY_US: {}\n", elapsed_us);
            opt_res = _out0.clone();
            print!("{}", DafnyPrintWrapper(&string_of("SUCCESS\n")));
            return ();
        }
    }

    /// working_query.dfy(1,1)
    pub type uint64 = DafnyInt;

    /// working_query.dfy(2,1)
    pub type uint32 = DafnyInt;

    /// working_query.dfy(4,1)
    #[derive(Clone)]
    pub enum Row {
        Row {
            LO_ORDERKEY: u32,
            LO_LINENUMBER: u32,
            LO_CUSTKEY: u32,
            LO_PARTKEY: u32,
            LO_SUPPKEY: u32,
            LO_ORDERDATE: u32,
            LO_ORDERPRIORITY: Sequence<DafnyChar>,
            LO_SHIPPRIORITY: u32,
            LO_QUANTITY: u32,
            LO_EXTENDEDPRICE: u64,
            LO_ORDTOTALPRICE: u64,
            LO_DISCOUNT: u32,
            LO_REVENUE: u64,
            LO_SUPPLYCOST: u64,
            LO_TAX: u32,
            LO_COMMITDATE: u32,
            LO_SHIPMODE: Sequence<DafnyChar>,
            C_NAME: Sequence<DafnyChar>,
            C_ADDRESS: Sequence<DafnyChar>,
            C_CITY: Sequence<DafnyChar>,
            C_NATION: Sequence<DafnyChar>,
            C_REGION: Sequence<DafnyChar>,
            C_PHONE: Sequence<DafnyChar>,
            C_MKTSEGMENT: Sequence<DafnyChar>,
            S_NAME: Sequence<DafnyChar>,
            S_ADDRESS: Sequence<DafnyChar>,
            S_CITY: Sequence<DafnyChar>,
            S_NATION: Sequence<DafnyChar>,
            S_REGION: Sequence<DafnyChar>,
            S_PHONE: Sequence<DafnyChar>,
            P_NAME: Sequence<DafnyChar>,
            P_MFGR: Sequence<DafnyChar>,
            P_CATEGORY: Sequence<DafnyChar>,
            P_BRAND: Sequence<DafnyChar>,
            P_COLOR: Sequence<DafnyChar>,
            P_TYPE: Sequence<DafnyChar>,
            P_SIZE: u32,
            P_CONTAINER: Sequence<DafnyChar>,
            D_YEAR: u32,
            D_YEARMONTHNUM: u32,
            D_WEEKNUMINYEAR: u32
        }
    }

    impl Row {
        /// Returns a borrow of the field LO_ORDERKEY
        pub fn LO_ORDERKEY(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_ORDERKEY,
            }
        }
        /// Returns a borrow of the field LO_LINENUMBER
        pub fn LO_LINENUMBER(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_LINENUMBER,
            }
        }
        /// Returns a borrow of the field LO_CUSTKEY
        pub fn LO_CUSTKEY(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_CUSTKEY,
            }
        }
        /// Returns a borrow of the field LO_PARTKEY
        pub fn LO_PARTKEY(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_PARTKEY,
            }
        }
        /// Returns a borrow of the field LO_SUPPKEY
        pub fn LO_SUPPKEY(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_SUPPKEY,
            }
        }
        /// Returns a borrow of the field LO_ORDERDATE
        pub fn LO_ORDERDATE(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_ORDERDATE,
            }
        }
        /// Returns a borrow of the field LO_ORDERPRIORITY
        pub fn LO_ORDERPRIORITY(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_ORDERPRIORITY,
            }
        }
        /// Returns a borrow of the field LO_SHIPPRIORITY
        pub fn LO_SHIPPRIORITY(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_SHIPPRIORITY,
            }
        }
        /// Returns a borrow of the field LO_QUANTITY
        pub fn LO_QUANTITY(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_QUANTITY,
            }
        }
        /// Returns a borrow of the field LO_EXTENDEDPRICE
        pub fn LO_EXTENDEDPRICE(&self) -> &u64 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_EXTENDEDPRICE,
            }
        }
        /// Returns a borrow of the field LO_ORDTOTALPRICE
        pub fn LO_ORDTOTALPRICE(&self) -> &u64 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_ORDTOTALPRICE,
            }
        }
        /// Returns a borrow of the field LO_DISCOUNT
        pub fn LO_DISCOUNT(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_DISCOUNT,
            }
        }
        /// Returns a borrow of the field LO_REVENUE
        pub fn LO_REVENUE(&self) -> &u64 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_REVENUE,
            }
        }
        /// Returns a borrow of the field LO_SUPPLYCOST
        pub fn LO_SUPPLYCOST(&self) -> &u64 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_SUPPLYCOST,
            }
        }
        /// Returns a borrow of the field LO_TAX
        pub fn LO_TAX(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_TAX,
            }
        }
        /// Returns a borrow of the field LO_COMMITDATE
        pub fn LO_COMMITDATE(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_COMMITDATE,
            }
        }
        /// Returns a borrow of the field LO_SHIPMODE
        pub fn LO_SHIPMODE(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => LO_SHIPMODE,
            }
        }
        /// Returns a borrow of the field C_NAME
        pub fn C_NAME(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => C_NAME,
            }
        }
        /// Returns a borrow of the field C_ADDRESS
        pub fn C_ADDRESS(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => C_ADDRESS,
            }
        }
        /// Returns a borrow of the field C_CITY
        pub fn C_CITY(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => C_CITY,
            }
        }
        /// Returns a borrow of the field C_NATION
        pub fn C_NATION(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => C_NATION,
            }
        }
        /// Returns a borrow of the field C_REGION
        pub fn C_REGION(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => C_REGION,
            }
        }
        /// Returns a borrow of the field C_PHONE
        pub fn C_PHONE(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => C_PHONE,
            }
        }
        /// Returns a borrow of the field C_MKTSEGMENT
        pub fn C_MKTSEGMENT(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => C_MKTSEGMENT,
            }
        }
        /// Returns a borrow of the field S_NAME
        pub fn S_NAME(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => S_NAME,
            }
        }
        /// Returns a borrow of the field S_ADDRESS
        pub fn S_ADDRESS(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => S_ADDRESS,
            }
        }
        /// Returns a borrow of the field S_CITY
        pub fn S_CITY(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => S_CITY,
            }
        }
        /// Returns a borrow of the field S_NATION
        pub fn S_NATION(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => S_NATION,
            }
        }
        /// Returns a borrow of the field S_REGION
        pub fn S_REGION(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => S_REGION,
            }
        }
        /// Returns a borrow of the field S_PHONE
        pub fn S_PHONE(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => S_PHONE,
            }
        }
        /// Returns a borrow of the field P_NAME
        pub fn P_NAME(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => P_NAME,
            }
        }
        /// Returns a borrow of the field P_MFGR
        pub fn P_MFGR(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => P_MFGR,
            }
        }
        /// Returns a borrow of the field P_CATEGORY
        pub fn P_CATEGORY(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => P_CATEGORY,
            }
        }
        /// Returns a borrow of the field P_BRAND
        pub fn P_BRAND(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => P_BRAND,
            }
        }
        /// Returns a borrow of the field P_COLOR
        pub fn P_COLOR(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => P_COLOR,
            }
        }
        /// Returns a borrow of the field P_TYPE
        pub fn P_TYPE(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => P_TYPE,
            }
        }
        /// Returns a borrow of the field P_SIZE
        pub fn P_SIZE(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => P_SIZE,
            }
        }
        /// Returns a borrow of the field P_CONTAINER
        pub fn P_CONTAINER(&self) -> &Sequence<DafnyChar> {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => P_CONTAINER,
            }
        }
        /// Returns a borrow of the field D_YEAR
        pub fn D_YEAR(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => D_YEAR,
            }
        }
        /// Returns a borrow of the field D_YEARMONTHNUM
        pub fn D_YEARMONTHNUM(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => D_YEARMONTHNUM,
            }
        }
        /// Returns a borrow of the field D_WEEKNUMINYEAR
        pub fn D_WEEKNUMINYEAR(&self) -> &u32 {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => D_WEEKNUMINYEAR,
            }
        }
    }

    impl Debug
        for Row {
        fn fmt(&self, f: &mut Formatter) -> Result {
            DafnyPrint::fmt_print(self, f, true)
        }
    }

    impl DafnyPrint
        for Row {
        fn fmt_print(&self, _formatter: &mut Formatter, _in_seq: bool) -> std::fmt::Result {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => {
                    write!(_formatter, "Row.Row(")?;
                    DafnyPrint::fmt_print(LO_ORDERKEY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_LINENUMBER, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_CUSTKEY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_PARTKEY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_SUPPKEY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_ORDERDATE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_ORDERPRIORITY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_SHIPPRIORITY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_QUANTITY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_EXTENDEDPRICE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_ORDTOTALPRICE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_DISCOUNT, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_REVENUE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_SUPPLYCOST, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_TAX, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_COMMITDATE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(LO_SHIPMODE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(C_NAME, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(C_ADDRESS, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(C_CITY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(C_NATION, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(C_REGION, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(C_PHONE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(C_MKTSEGMENT, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(S_NAME, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(S_ADDRESS, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(S_CITY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(S_NATION, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(S_REGION, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(S_PHONE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(P_NAME, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(P_MFGR, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(P_CATEGORY, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(P_BRAND, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(P_COLOR, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(P_TYPE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(P_SIZE, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(P_CONTAINER, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(D_YEAR, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(D_YEARMONTHNUM, _formatter, false)?;
                    write!(_formatter, ", ")?;
                    DafnyPrint::fmt_print(D_WEEKNUMINYEAR, _formatter, false)?;
                    write!(_formatter, ")")?;
                    Ok(())
                },
            }
        }
    }

    impl PartialEq
        for Row {
        fn eq(&self, other: &Self) -> bool {
            match (
                    self,
                    other
                ) {
                (Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, }, Row::Row{LO_ORDERKEY: _2_LO_ORDERKEY, LO_LINENUMBER: _2_LO_LINENUMBER, LO_CUSTKEY: _2_LO_CUSTKEY, LO_PARTKEY: _2_LO_PARTKEY, LO_SUPPKEY: _2_LO_SUPPKEY, LO_ORDERDATE: _2_LO_ORDERDATE, LO_ORDERPRIORITY: _2_LO_ORDERPRIORITY, LO_SHIPPRIORITY: _2_LO_SHIPPRIORITY, LO_QUANTITY: _2_LO_QUANTITY, LO_EXTENDEDPRICE: _2_LO_EXTENDEDPRICE, LO_ORDTOTALPRICE: _2_LO_ORDTOTALPRICE, LO_DISCOUNT: _2_LO_DISCOUNT, LO_REVENUE: _2_LO_REVENUE, LO_SUPPLYCOST: _2_LO_SUPPLYCOST, LO_TAX: _2_LO_TAX, LO_COMMITDATE: _2_LO_COMMITDATE, LO_SHIPMODE: _2_LO_SHIPMODE, C_NAME: _2_C_NAME, C_ADDRESS: _2_C_ADDRESS, C_CITY: _2_C_CITY, C_NATION: _2_C_NATION, C_REGION: _2_C_REGION, C_PHONE: _2_C_PHONE, C_MKTSEGMENT: _2_C_MKTSEGMENT, S_NAME: _2_S_NAME, S_ADDRESS: _2_S_ADDRESS, S_CITY: _2_S_CITY, S_NATION: _2_S_NATION, S_REGION: _2_S_REGION, S_PHONE: _2_S_PHONE, P_NAME: _2_P_NAME, P_MFGR: _2_P_MFGR, P_CATEGORY: _2_P_CATEGORY, P_BRAND: _2_P_BRAND, P_COLOR: _2_P_COLOR, P_TYPE: _2_P_TYPE, P_SIZE: _2_P_SIZE, P_CONTAINER: _2_P_CONTAINER, D_YEAR: _2_D_YEAR, D_YEARMONTHNUM: _2_D_YEARMONTHNUM, D_WEEKNUMINYEAR: _2_D_WEEKNUMINYEAR, }) => {
                    LO_ORDERKEY == _2_LO_ORDERKEY && LO_LINENUMBER == _2_LO_LINENUMBER && LO_CUSTKEY == _2_LO_CUSTKEY && LO_PARTKEY == _2_LO_PARTKEY && LO_SUPPKEY == _2_LO_SUPPKEY && LO_ORDERDATE == _2_LO_ORDERDATE && LO_ORDERPRIORITY == _2_LO_ORDERPRIORITY && LO_SHIPPRIORITY == _2_LO_SHIPPRIORITY && LO_QUANTITY == _2_LO_QUANTITY && LO_EXTENDEDPRICE == _2_LO_EXTENDEDPRICE && LO_ORDTOTALPRICE == _2_LO_ORDTOTALPRICE && LO_DISCOUNT == _2_LO_DISCOUNT && LO_REVENUE == _2_LO_REVENUE && LO_SUPPLYCOST == _2_LO_SUPPLYCOST && LO_TAX == _2_LO_TAX && LO_COMMITDATE == _2_LO_COMMITDATE && LO_SHIPMODE == _2_LO_SHIPMODE && C_NAME == _2_C_NAME && C_ADDRESS == _2_C_ADDRESS && C_CITY == _2_C_CITY && C_NATION == _2_C_NATION && C_REGION == _2_C_REGION && C_PHONE == _2_C_PHONE && C_MKTSEGMENT == _2_C_MKTSEGMENT && S_NAME == _2_S_NAME && S_ADDRESS == _2_S_ADDRESS && S_CITY == _2_S_CITY && S_NATION == _2_S_NATION && S_REGION == _2_S_REGION && S_PHONE == _2_S_PHONE && P_NAME == _2_P_NAME && P_MFGR == _2_P_MFGR && P_CATEGORY == _2_P_CATEGORY && P_BRAND == _2_P_BRAND && P_COLOR == _2_P_COLOR && P_TYPE == _2_P_TYPE && P_SIZE == _2_P_SIZE && P_CONTAINER == _2_P_CONTAINER && D_YEAR == _2_D_YEAR && D_YEARMONTHNUM == _2_D_YEARMONTHNUM && D_WEEKNUMINYEAR == _2_D_WEEKNUMINYEAR
                },
                _ => {
                    false
                },
            }
        }
    }

    impl Eq
        for Row {}

    impl Hash
        for Row {
        fn hash<_H: Hasher>(&self, _state: &mut _H) {
            match self {
                Row::Row{LO_ORDERKEY, LO_LINENUMBER, LO_CUSTKEY, LO_PARTKEY, LO_SUPPKEY, LO_ORDERDATE, LO_ORDERPRIORITY, LO_SHIPPRIORITY, LO_QUANTITY, LO_EXTENDEDPRICE, LO_ORDTOTALPRICE, LO_DISCOUNT, LO_REVENUE, LO_SUPPLYCOST, LO_TAX, LO_COMMITDATE, LO_SHIPMODE, C_NAME, C_ADDRESS, C_CITY, C_NATION, C_REGION, C_PHONE, C_MKTSEGMENT, S_NAME, S_ADDRESS, S_CITY, S_NATION, S_REGION, S_PHONE, P_NAME, P_MFGR, P_CATEGORY, P_BRAND, P_COLOR, P_TYPE, P_SIZE, P_CONTAINER, D_YEAR, D_YEARMONTHNUM, D_WEEKNUMINYEAR, } => {
                    Hash::hash(LO_ORDERKEY, _state);
                    Hash::hash(LO_LINENUMBER, _state);
                    Hash::hash(LO_CUSTKEY, _state);
                    Hash::hash(LO_PARTKEY, _state);
                    Hash::hash(LO_SUPPKEY, _state);
                    Hash::hash(LO_ORDERDATE, _state);
                    Hash::hash(LO_ORDERPRIORITY, _state);
                    Hash::hash(LO_SHIPPRIORITY, _state);
                    Hash::hash(LO_QUANTITY, _state);
                    Hash::hash(LO_EXTENDEDPRICE, _state);
                    Hash::hash(LO_ORDTOTALPRICE, _state);
                    Hash::hash(LO_DISCOUNT, _state);
                    Hash::hash(LO_REVENUE, _state);
                    Hash::hash(LO_SUPPLYCOST, _state);
                    Hash::hash(LO_TAX, _state);
                    Hash::hash(LO_COMMITDATE, _state);
                    Hash::hash(LO_SHIPMODE, _state);
                    Hash::hash(C_NAME, _state);
                    Hash::hash(C_ADDRESS, _state);
                    Hash::hash(C_CITY, _state);
                    Hash::hash(C_NATION, _state);
                    Hash::hash(C_REGION, _state);
                    Hash::hash(C_PHONE, _state);
                    Hash::hash(C_MKTSEGMENT, _state);
                    Hash::hash(S_NAME, _state);
                    Hash::hash(S_ADDRESS, _state);
                    Hash::hash(S_CITY, _state);
                    Hash::hash(S_NATION, _state);
                    Hash::hash(S_REGION, _state);
                    Hash::hash(S_PHONE, _state);
                    Hash::hash(P_NAME, _state);
                    Hash::hash(P_MFGR, _state);
                    Hash::hash(P_CATEGORY, _state);
                    Hash::hash(P_BRAND, _state);
                    Hash::hash(P_COLOR, _state);
                    Hash::hash(P_TYPE, _state);
                    Hash::hash(P_SIZE, _state);
                    Hash::hash(P_CONTAINER, _state);
                    Hash::hash(D_YEAR, _state);
                    Hash::hash(D_YEARMONTHNUM, _state);
                    Hash::hash(D_WEEKNUMINYEAR, _state)
                },
            }
        }
    }

    impl AsRef<Row>
        for Row {
        fn as_ref(&self) -> &Self {
            self
        }
    }
}
fn main() {
  let args: Vec<String> = ::std::env::args().collect();
  let dafny_args =
    ::dafny_runtime::dafny_runtime_conversions::vec_to_dafny_sequence(
    &args, |s| 
  ::dafny_runtime::dafny_runtime_conversions::unicode_chars_true::string_to_dafny_string(s));
  crate::_module::_default::Main(&dafny_args);
}