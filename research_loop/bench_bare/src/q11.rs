// Hand-tuned Rust baseline for SSB Q11 (Q4.1) — SUM(LO_REVENUE - LO_SUPPLYCOST)
// grouped by (D_YEAR, C_NATION) with WHERE C_REGION='AMERICA' AND
// S_REGION='AMERICA' AND P_MFGR='MFGR#1'.
//
// Like bench_q1, reads `lineorder_flat.tbl` once into columnar Vec<u32/u64> /
// Vec<String>, then runs a tight loop building a HashMap<(u32, String), u64>.
//
// The subtraction is done as i128 to avoid panic on underflow (SBB synthetic
// data may have negative profits on some rows).

use std::collections::HashMap;
use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::time::Instant;

fn read_col<'a>(name: &str, name_to_idx: &HashMap<String, usize>, lines: &[String]) -> Vec<String> {
    let i = *name_to_idx.get(name).expect("missing col");
    lines.iter().map(|l| {
        let f: Vec<&str> = l.split('|').collect();
        f.get(i).map(|s| s.to_string()).unwrap_or_default()
    }).collect()
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let tbl_path = if args.len() >= 2 { &args[1] } else { "ssb-dbgen/lineorder_flat.tbl" };

    let limit: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(50_000);

    let f = File::open(tbl_path).expect("open .tbl");
    let mut rdr = BufReader::new(f);
    let mut hdr = String::new();
    rdr.read_line(&mut hdr).unwrap();
    let mut name_to_idx: HashMap<String, usize> = HashMap::new();
    for (i, c) in hdr.split('|').enumerate() {
        name_to_idx.insert(c.trim().to_uppercase(), i);
    }

    let lines: Vec<String> = rdr.lines().take(limit).map(|l| l.unwrap()).collect();
    let utf = |name: &str, idx: &HashMap<String, usize>, ls: &[String]| -> Vec<String> {
        let i = *idx.get(name).expect("missing col");
        ls.iter().map(|l| {
            let f: Vec<&str> = l.split('|').collect();
            let s = f.get(i).copied().unwrap_or("");
            // .tbl wraps string fields in double quotes; strip them so the
            // literal comparison in the WHERE clause matches.
            s.trim_matches('"').to_string()
        }).collect()
    };
    let rev_i     = utf("LO_REVENUE",     &name_to_idx, &lines);
    let cost_i    = utf("LO_SUPPLYCOST", &name_to_idx, &lines);
    let year_i    = utf("D_YEAR",         &name_to_idx, &lines);
    let cnat_i    = utf("C_NATION",      &name_to_idx, &lines);
    let creg_i    = utf("C_REGION",      &name_to_idx, &lines);
    let sreg_i    = utf("S_REGION",      &name_to_idx, &lines);
    let pmfgr_i   = utf("P_MFGR",        &name_to_idx, &lines);

    let revenue: Vec<i128> = rev_i.iter().map(|s| s.parse::<i128>().unwrap_or(0)).collect();
    let supplycost: Vec<i128> = cost_i.iter().map(|s| s.parse::<i128>().unwrap_or(0)).collect();
    let year: Vec<u32> = year_i.iter().map(|s| s.parse::<u32>().unwrap_or(0)).collect();

    let n = revenue.len() as u64;

    let mut acc: HashMap<(u32, String), i128> = HashMap::new();

    for run in 0..3 {
        acc.clear();
        let t0 = Instant::now();
        for i in 0..n as usize {
            if creg_i[i] == "AMERICA" && sreg_i[i] == "AMERICA" && pmfgr_i[i] == "MFGR#1" {
                let key = (year[i], cnat_i[i].clone());
                let v = revenue[i] - supplycost[i];
                *acc.entry(key).or_insert(0) += v;
            }
        }
        let dt = t0.elapsed().as_micros();
        if run == 2 {
            println!("QUERY_LATENCY_US: {}", dt);
            println!("RESULT_GROUPS: {}", acc.len());
        }
    }
}