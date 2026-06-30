use std::collections::{HashMap, HashSet};
use std::env;
use std::fs;
use std::path::Path;
use syn::visit_mut::VisitMut;
use syn::visit::Visit;
use syn::{Expr, Stmt, Type, Pat, Block, ItemEnum, parse_quote};
use quote::quote;

struct SchemaExtractor {
    row_types: HashMap<String, String>,
}

impl<'ast> Visit<'ast> for SchemaExtractor {
    fn visit_item_enum(&mut self, i: &'ast ItemEnum) {
        if i.ident == "Row" {
            for variant in &i.variants {
                if variant.ident == "Row" {
                    if let syn::Fields::Named(fields_named) = &variant.fields {
                        for field in &fields_named.named {
                            if let Some(ident) = &field.ident {
                                let ty_str = quote!(#field).to_string();
                                // Clean up the type string to extract the type name
                                let clean_ty = if ty_str.contains("Sequence") {
                                    "String".to_string()
                                } else if ty_str.contains("u64") {
                                    "u64".to_string()
                                } else if ty_str.contains("u32") {
                                    "u32".to_string()
                                } else {
                                    "u32".to_string()
                                };
                                self.row_types.insert(ident.to_string(), clean_ty);
                            }
                        }
                    }
                }
            }
        }
        syn::visit::visit_item_enum(self, i);
    }
}

struct RunQueryDetector {
    has_run_query: bool,
    is_scalar: bool,
}

impl<'ast> Visit<'ast> for RunQueryDetector {
    fn visit_impl_item_fn(&mut self, i: &'ast syn::ImplItemFn) {
        if i.sig.ident == "RunQuery" {
            self.has_run_query = true;
            if let syn::ReturnType::Type(_, ty) = &i.sig.output {
                let ty_str = quote!(#ty).to_string().replace(" ", "");
                if ty_str.contains("Map") || ty_str.contains("HashMap") {
                    self.is_scalar = false;
                }
            }
        }
        syn::visit::visit_impl_item_fn(self, i);
    }
    fn visit_item_fn(&mut self, i: &'ast syn::ItemFn) {
        if i.sig.ident == "RunQuery" {
            self.has_run_query = true;
            if let syn::ReturnType::Type(_, ty) = &i.sig.output {
                let ty_str = quote!(#ty).to_string().replace(" ", "");
                if ty_str.contains("Map") || ty_str.contains("HashMap") {
                    self.is_scalar = false;
                }
            }
        }
        syn::visit::visit_item_fn(self, i);
    }
}

struct RunQueryFinder {
    found: bool,
}

impl<'ast> Visit<'ast> for RunQueryFinder {
    fn visit_expr_call(&mut self, i: &'ast syn::ExprCall) {
        if let Expr::Path(expr_path) = &*i.func {
            if let Some(last_segment) = expr_path.path.segments.last() {
                if last_segment.ident == "RunQuery" {
                    self.found = true;
                }
            }
        }
        syn::visit::visit_expr_call(self, i);
    }
    fn visit_expr_method_call(&mut self, i: &'ast syn::ExprMethodCall) {
        if i.method == "RunQuery" {
            self.found = true;
        }
        syn::visit::visit_expr_method_call(self, i);
    }
}

fn expr_contains_run_query(expr: &Expr) -> bool {
    let mut visitor = RunQueryFinder { found: false };
    visitor.visit_expr(expr);
    visitor.found
}

struct PostProcessor {
    row_var: String,
    tbl_path_str: String,
}

impl VisitMut for PostProcessor {
    // 1. Optimize types everywhere
    fn visit_type_mut(&mut self, ty: &mut Type) {
        let ty_str = quote!(#ty).to_string().replace(" ", "");
        if ty_str.contains("DafnyInt") {
            *ty = parse_quote!(u64);
        } else if ty_str.contains("Map<(u32,Sequence<DafnyChar>),DafnyInt>") {
            *ty = parse_quote!(::std::collections::HashMap<(u32, String), u64>);
        } else if ty_str.contains("Map<(u32,Sequence<char>),DafnyInt>") {
            *ty = parse_quote!(::std::collections::HashMap<(u32, String), u64>);
        }
        syn::visit_mut::visit_type_mut(self, ty);
    }

    // 2. Rewrite expressions
    fn visit_expr_mut(&mut self, expr: &mut Expr) {
        // Rewrite DafnyInt::from(x) -> x as u64
        if let Expr::Call(expr_call) = expr {
            if let Expr::Path(expr_path) = &*expr_call.func {
                let path_str = quote!(#expr_path).to_string().replace(" ", "");
                if path_str.contains("DafnyInt::from") && expr_call.args.len() == 1 {
                    let arg = &expr_call.args[0];
                    *expr = parse_quote!((#arg as u64));
                    return;
                }
            }
        }

        // Rewrite int!(x) -> x (as suffixless literal) else (x as u64)
        if let Expr::Macro(expr_macro) = expr {
            if expr_macro.mac.path.is_ident("int") {
                let tokens = &expr_macro.mac.tokens;
                if let Ok(lit_int) = syn::parse2::<syn::LitInt>(tokens.clone()) {
                    let digits = lit_int.base10_digits();
                    let suffixless_lit = syn::LitInt::new(digits, proc_macro2::Span::call_site());
                    *expr = Expr::Lit(syn::ExprLit {
                        attrs: Vec::new(),
                        lit: syn::Lit::Int(suffixless_lit),
                    });
                } else {
                    *expr = parse_quote!((#tokens as u64));
                }
                return;
            }
        }

        // Rewrite index access: data.get(&i) -> data.get_usize(i)
        if let Expr::MethodCall(method_call) = expr {
            if method_call.method == "get" && method_call.args.len() == 1 {
                if let Expr::Reference(expr_ref) = &method_call.args[0] {
                    if let Expr::Path(expr_path) = &*expr_ref.expr {
                        if expr_path.path.is_ident("i") {
                            method_call.method = syn::Ident::new("get_usize", proc_macro2::Span::call_site());
                            method_call.args[0] = *expr_ref.expr.clone();
                        }
                    }
                }
            }
        }

        // Rewrite cardinality: LO_ORDERDATE.cardinality() -> LO_ORDERDATE.cardinality().as_usize()
        if let Expr::MethodCall(method_call) = expr {
            if method_call.method == "cardinality" {
                let receiver = &method_call.receiver;
                *expr = parse_quote!(#receiver.cardinality().as_usize());
                return;
            }
        }

        syn::visit_mut::visit_expr_mut(self, expr);
    }

    // 3. Rewrite statements inside blocks (Timing Wrapper & Loop index usize conversion)
    fn visit_block_mut(&mut self, block: &mut Block) {
        let mut new_stmts = Vec::new();
        for mut stmt in block.stmts.drain(..) {
            // Find row variable name dynamically from Rc<Row> initialization
            if let Stmt::Local(local) = &stmt {
                let local_str = quote!(#local).to_string().replace(" ", "");
                if local_str.contains("Rc<Row>=") && local_str.contains("_vec[i].clone()") {
                    if let Pat::Ident(pat_ident) = &local.pat {
                        self.row_var = pat_ident.ident.to_string();
                    } else if let Pat::Type(pat_type) = &local.pat {
                        if let Pat::Ident(pat_ident) = &*pat_type.pat {
                            self.row_var = pat_ident.ident.to_string();
                        }
                    }
                }
            }

            // Optimize loop row variable assignment: let mut row: Rc<Row> = data_vec[i].clone(); -> let row = &data_vec[i];
            if let Stmt::Local(local) = stmt.clone() {
                let local_str = quote!(#local).to_string().replace(" ", "");
                if local_str.contains("Rc<Row>=") && local_str.contains("_vec[i].clone()") {
                    let row_ident = syn::Ident::new(&self.row_var, proc_macro2::Span::call_site());
                    // Find receiver (e.g. data_vec)
                    let mut rec_name = "data".to_string();
                    if let Some(init) = &local.init {
                        let init_expr = &*init.expr;
                        let init_str = quote!(#init_expr).to_string();
                        if let Some(pos) = init_str.find("_vec") {
                            if let Some(start_pos) = init_str[..pos].rfind(' ') {
                                rec_name = init_str[start_pos..pos].trim().to_string();
                            } else {
                                rec_name = init_str[..pos].trim().to_string();
                            }
                        }
                    }
                    let rec_ident = syn::Ident::new(&format!("{}_vec", rec_name), proc_macro2::Span::call_site());
                    stmt = parse_quote!(let #row_ident = &#rec_ident[i];);
                }
            }

            // Replace mock data loading in Main
            if let Stmt::Local(local) = stmt.clone() {
                let local_str = quote!(#local).to_string().replace(" ", "");
                if local_str.starts_with("letmutdata:") || local_str.starts_with("letdata:") || local_str.starts_with("letmutdata=") || local_str.starts_with("letdata=") {
                    let tbl_path_str = &self.tbl_path_str;
                    stmt = parse_quote! {
                        let mut data: Sequence<Rc<Row>> = _default::load_dataset(#tbl_path_str, 50000);
                    };
                }
            }

            // If the local variable is named 'i' or 'len', force its type to 'usize' so indexing compiles
            if let Stmt::Local(mut local) = stmt.clone() {
                let mut is_index = false;
                if let Pat::Ident(pat_ident) = &local.pat {
                    let name = pat_ident.ident.to_string();
                    if name == "i" || name == "len" {
                        is_index = true;
                    }
                } else if let Pat::Type(pat_type) = &local.pat {
                    if let Pat::Ident(pat_ident) = &*pat_type.pat {
                        let name = pat_ident.ident.to_string();
                        if name == "i" || name == "len" {
                            is_index = true;
                        }
                    }
                }
                if is_index {
                    let pat_ident = match &local.pat {
                        Pat::Ident(pi) => pi.clone(),
                        Pat::Type(pt) => match &*pt.pat {
                            Pat::Ident(pi) => pi.clone(),
                            _ => continue,
                        },
                        _ => continue,
                    };
                    local.pat = Pat::Type(syn::PatType {
                        attrs: Vec::new(),
                        pat: Box::new(Pat::Ident(pat_ident)),
                        colon_token: syn::token::Colon::default(),
                        ty: Box::new(parse_quote!(usize)),
                    });
                    stmt = Stmt::Local(local);
                }
            }

            // Apply visitor to statement first
            self.visit_stmt_mut(&mut stmt);

            // Check if this statement is a RunQuery call to wrap in timing
            if let Stmt::Local(local) = &stmt {
                if let Some(init) = &local.init {
                    if expr_contains_run_query(&init.expr) {
                        let pat = &local.pat;
                        let query_expr = &init.expr;
                        let timing_block: Block = parse_quote! {
                            {
                                let start = ::std::time::Instant::now();
                                let #pat = ::std::hint::black_box(#query_expr);
                                let elapsed_us = start.elapsed().as_micros();
                                println!("QUERY_LATENCY_US: {}", elapsed_us);
                            }
                        };
                        new_stmts.extend(timing_block.stmts);
                        continue;
                    }
                }
            }

            new_stmts.push(stmt);
        }
        block.stmts = new_stmts;
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: postprocessor_rust <file_path> [dataset_file_path]");
        std::process::exit(1);
    }
    let file_path = &args[1];
    let path = Path::new(file_path);
    if !path.exists() {
        eprintln!("File not found: {}", file_path);
        std::process::exit(1);
    }

    let tbl_path_str = if args.len() >= 3 {
        args[2].clone()
    } else {
        "ssb-dbgen/lineorder_flat.tbl".to_string()
    };

    let content = fs::read_to_string(path).expect("failed to read file");
    let mut syntax = syn::parse_file(&content).expect("failed to parse rust file");

    // Step 1: Extract database schema variant fields from Row enum
    let mut extractor = SchemaExtractor {
        row_types: HashMap::new(),
    };
    extractor.visit_file(&syntax);

    // Detect if this is a scalar or map query by checking signature of RunQuery
    let mut detector = RunQueryDetector {
        has_run_query: false,
        is_scalar: true,
    };
    detector.visit_file(&syntax);

    if !detector.has_run_query {
        // Not a query file, skip postprocessing
        return;
    }

    // Step 2: Run AST transformations
    let mut processor = PostProcessor {
        row_var: "row".to_string(),
        tbl_path_str,
    };
    processor.visit_file_mut(&mut syntax);

    let mut transformed_code = quote!(#syntax).to_string();

    let mut row_fields_init = String::new();
    for (field, t) in &extractor.row_types {
        let field_upper = field.to_uppercase();
        if t == "String" {
            row_fields_init += &format!("                        {}: string_of(fields[*col_to_idx.get(\"{}\").unwrap_or_else(|| panic!(\"column {} not found\"))]),\n", field, field_upper, field_upper);
        } else {
            row_fields_init += &format!("                        {}: fields[*col_to_idx.get(\"{}\").unwrap_or_else(|| panic!(\"column {} not found\"))].parse::<{}>().unwrap(),\n", field, field_upper, field_upper, t);
        }
    }

    let load_dataset_fn = format!(r#"
        pub fn load_dataset(file_path: &str, limit: usize) -> Sequence<Rc<Row>> {{
            use std::fs::File;
            use std::io::{{BufRead, BufReader}};
            use std::path::PathBuf;

            let mut base_path = std::env::current_dir().unwrap();
            let mut tbl_path = base_path.join(file_path);
            while !tbl_path.exists() {{
                if let Some(parent) = base_path.parent() {{
                    base_path = parent.to_path_buf();
                    tbl_path = base_path.join(file_path);
                }} else {{
                    break;
                }}
            }}

            let file = File::open(&tbl_path).unwrap_or_else(|_| panic!("failed to open dataset file at: {{:?}}", tbl_path));
            let mut reader = BufReader::new(file);
            
            let mut header_line = String::new();
            reader.read_line(&mut header_line).expect("failed to read header line");
            let delim = if header_line.contains('|') {{ '|' }} else {{ ',' }};
            let mut col_to_idx = std::collections::HashMap::new();
            for (idx, col) in header_line.split(delim).enumerate() {{
                col_to_idx.insert(col.trim().to_uppercase().to_string(), idx);
            }}

            let mut rows = Vec::new();
            for line in reader.lines().take(limit) {{
                let line = line.expect("failed to read line");
                let fields: Vec<&str> = line.split(delim).collect();
                if fields.len() > 0 {{
                    let row = Rc::new(Row::Row {{
{}                    }});
                    rows.push(row);
                }}
            }}
            Sequence::from_array_owned(rows)
        }}
    "#, row_fields_init);

    // Append load_dataset function to _default module
    if let Some(pos) = transformed_code.find("impl _default {") {
        let insert_idx = pos + "impl _default {".len();
        transformed_code.insert_str(insert_idx, &format!("\n{}", load_dataset_fn));
    }

    fs::write(path, transformed_code).expect("failed to write output file");
}
