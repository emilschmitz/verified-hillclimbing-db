//! Hand-tuned bare Rust for TPC-H lineitem (integer-normalized tbl from export_tpch_lineitem.py).
//! Usage: bench_tpch <q1|q6> <tbl> [limit]

use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::time::Instant;

struct Lineitem {
    quantity: Vec<u32>,
    extendedprice: Vec<u64>,
    discount: Vec<u32>,
    shipdate: Vec<u32>,
    returnflag: Vec<u8>,
    linestatus: Vec<u8>,
}

fn load(tbl_path: &str, limit: usize) -> Lineitem {
    let f = File::open(tbl_path).expect("open tbl");
    let mut rdr = BufReader::new(f);
    let mut hdr = String::new();
    rdr.read_line(&mut hdr).unwrap();
    let mut idx = std::collections::HashMap::new();
    for (i, c) in hdr.split('|').enumerate() {
        idx.insert(c.trim().to_uppercase(), i);
    }
    let col = |name: &str| *idx.get(name).expect("missing col");

    let mut out = Lineitem {
        quantity: Vec::with_capacity(limit),
        extendedprice: Vec::with_capacity(limit),
        discount: Vec::with_capacity(limit),
        shipdate: Vec::with_capacity(limit),
        returnflag: Vec::with_capacity(limit),
        linestatus: Vec::with_capacity(limit),
    };

    for line in rdr.lines().take(limit) {
        let line = line.unwrap();
        let f: Vec<&str> = line.split('|').collect();
        let u32_at = |i: usize| f.get(i).and_then(|s| s.parse().ok()).unwrap_or(0);
        let u64_at = |i: usize| f.get(i).and_then(|s| s.parse().ok()).unwrap_or(0);
        let ch_at = |i: usize| -> u8 {
            f.get(i)
                .and_then(|s| s.trim_matches('"').bytes().next())
                .unwrap_or(0)
        };

        out.quantity.push(u32_at(col("L_QUANTITY")));
        out.extendedprice.push(u64_at(col("L_EXTENDEDPRICE")));
        out.discount.push(u32_at(col("L_DISCOUNT")));
        out.shipdate.push(u32_at(col("L_SHIPDATE")));
        out.returnflag.push(ch_at(col("L_RETURNFLAG")));
        out.linestatus.push(ch_at(col("L_LINESTATUS")));
    }
    out
}

fn time_loop<F: FnMut()>(mut f: F) {
    for run in 0..3 {
        let t0 = Instant::now();
        f();
        let dt = t0.elapsed().as_micros();
        if run == 2 {
            println!("QUERY_LATENCY_US: {}", dt);
        }
    }
}

/// TPC-H Q1 shape: 6 buckets (returnflag × linestatus), direct array — no hash map.
fn run_q1(c: &Lineitem) {
    time_loop(|| {
        let mut acc = [0u64; 6];
        let n = c.shipdate.len();
        for i in 0..n {
            if c.shipdate[i] > 19_980_902 {
                continue;
            }
            let g = group_index(c.returnflag[i], c.linestatus[i]);
            if let Some(gi) = g {
                acc[gi] = acc[gi].wrapping_add(c.quantity[i] as u64);
            }
        }
        std::hint::black_box(acc);
    });
}

#[inline]
fn group_index(rf: u8, ls: u8) -> Option<usize> {
    let r = match rf {
        b'N' => 0,
        b'R' => 1,
        b'A' => 2,
        _ => return None,
    };
    let s = match ls {
        b'O' => 0,
        b'F' => 1,
        _ => return None,
    };
    Some(r * 2 + s)
}

/// TPC-H Q6 shape: selective filter + sum(extendedprice × discount).
fn run_q6(c: &Lineitem) {
    time_loop(|| {
        let mut acc: u64 = 0;
        let n = c.shipdate.len();
        for i in 0..n {
            let qty = c.quantity[i];
            if qty < 1 || qty > 50 {
                continue;
            }
            let disc = c.discount[i];
            if disc < 1 || disc > 5 {
                continue;
            }
            let sd = c.shipdate[i];
            if sd < 19_960_101 || sd > 19_961_231 {
                continue;
            }
            acc = acc.wrapping_add(c.extendedprice[i].wrapping_mul(disc as u64));
        }
        std::hint::black_box(acc);
    });
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let q = args.get(1).map(|s| s.as_str()).expect("usage: bench_tpch <q1|q6> <tbl> [limit]");
    let tbl = args.get(2).map(|s| s.as_str()).expect("usage: bench_tpch <q1|q6> <tbl> [limit]");
    let limit: usize = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(usize::MAX);
    let cols = load(tbl, limit);
    match q.to_lowercase().as_str() {
        "q1" => run_q1(&cols),
        "q6" => run_q6(&cols),
        _ => panic!("unsupported query {q}"),
    }
}
