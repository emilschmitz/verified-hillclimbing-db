// Hand-tuned Rust baseline for SSB Q1.1 — no formal verification, no Dafny
// runtime.  Used to measure the ceiling on what the verified Rust version
// could be targeting.
//
// Reads `lineorder_flat.tbl` once at startup into flat columnar `Vec`s,
// then runs the query in a tight autovectorizable loop.  Prints the warm
// cache latency.

use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::time::Instant;

fn main() {
    let args: Vec<String> = env::args().collect();
    let tbl_path = if args.len() >= 2 { &args[1] } else { "ssb-dbgen/lineorder_flat.tbl" };

    // Warm-up: load file into memory, parse into flat columnar vectors.
    let f = File::open(tbl_path).expect("open .tbl");
    let mut rdr = BufReader::new(f);
    let mut hdr = String::new();
    rdr.read_line(&mut hdr).unwrap();
    let mut col_idx: Vec<&str> = Vec::new();
    let mut name_to_idx: std::collections::HashMap<String, usize> = std::collections::HashMap::new();
    for (i, c) in hdr.split('|').enumerate() {
        let name = c.trim().to_uppercase();
        name_to_idx.insert(name, i);
        col_idx.push(Box::leak(c.trim().to_string().into_boxed_str()));
    }
    let take_col = |n: &str| *name_to_idx.get(n).expect("missing col");

    let orderdate_i = take_col("LO_ORDERDATE");
    let discount_i  = take_col("LO_DISCOUNT");
    let quantity_i  = take_col("LO_QUANTITY");
    let extprice_i  = take_col("LO_EXTENDEDPRICE");

    let mut orderdate: Vec<u32> = Vec::new();
    let mut discount:  Vec<u32> = Vec::new();
    let mut quantity:  Vec<u32> = Vec::new();
    let mut extprice:  Vec<u64> = Vec::new();
    let lines: Vec<String> = rdr.lines().map(|l| l.unwrap()).collect();
    for line in lines {
        let f: Vec<&str> = line.split('|').collect();
        if f.len() <= orderdate_i { continue; }
        orderdate.push(f[orderdate_i].parse::<u32>().unwrap());
        discount.push( f[discount_i].parse::<u32>().unwrap());
        quantity.push( f[quantity_i].parse::<u32>().unwrap());
        extprice.push( f[extprice_i].parse::<u64>().unwrap());
    }
    let n = orderdate.len() as u64;

    // Run the query 3x so the first two calls warm up the page cache and the
    // branch predictor, then time the third iteration.
    let mut last: u64 = 0;
    for run in 0..3 {
        let mut acc: u64 = 0;
        let t0 = Instant::now();
        for i in 0..n as usize {
            let q = quantity[i];
            if q < 25
                && (1_993_0101 <= orderdate[i] && orderdate[i] <= 1_993_1231)
                && (1 <= discount[i] && discount[i] <= 3)
            {
                acc = acc.wrapping_add(extprice[i].wrapping_mul(discount[i] as u64));
            }
        }
        let dt = t0.elapsed().as_micros();
        if run == 2 {
            println!("QUERY_LATENCY_US: {}", dt);
            last = acc;
        }
    }
    println!("RESULT: {}", last);
}