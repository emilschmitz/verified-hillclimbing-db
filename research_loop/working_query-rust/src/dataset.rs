use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::rc::Rc;
use dafny_runtime::{DafnyType, Sequence};

pub trait Loadable: Sized + DafnyType {
    fn from_fields(f: &[&str], ci: &HashMap<String, usize>) -> Self;
}

pub fn load_dataset<T: Loadable>(file_path: &str, limit: usize) -> Sequence<Rc<T>> {
    let mut base = std::env::current_dir().unwrap();
    let mut p = base.join(file_path);
    while !p.exists() {
        match base.parent() {
            Some(par) => { base = par.to_path_buf(); p = base.join(file_path); }
            None => break,
        }
    }
    let mut rdr = BufReader::new(File::open(&p).unwrap());
    let mut hdr = String::new();
    rdr.read_line(&mut hdr).unwrap();
    let d = if hdr.contains('|') { '|' } else { ',' };
    let mut ci: HashMap<String, usize> = HashMap::new();
    for (i, c) in hdr.split(d).enumerate() { ci.insert(c.trim().to_uppercase(), i); }

    let mut rows = Vec::new();
    for ln in rdr.lines().take(limit) {
        let line = ln.unwrap();
        let f: Vec<&str> = line.split(d).collect();
        if f.len() > 0 {
            rows.push(Rc::new(T::from_fields(&f, &ci)));
        }
    }
    Sequence::from_array_owned(rows)
}
