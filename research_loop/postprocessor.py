"""Minimal Python post-processor for Dafny→Rust output.

Keeps only semantic-preserving, RunQuery-scoped transforms:
  1. Strip MethodSpec (safety net)
  2. Rc<Row> clone → reference borrow in loops
  3. Empty data mock → dataset::load_dataset injection + Loadable impl
  4. Sequence index: data.get(&i) → data.get_usize(i) inside RunQuery

Removed (unsafe / handled by {:extern} newtypes in Dafny instead):
  - DafnyInt→u64, Map→HashMap, int!() rewrites, timing wrapper
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

import tree_sitter_rust as ts_rust
from tree_sitter import Language, Parser, Node

RUST_LANGUAGE = Language(ts_rust.language())
PARSER = Parser(RUST_LANGUAGE)

DEFAULT_TBL = "ssb-dbgen/lineorder_flat.tbl"
DEFAULT_LIMIT = 50000


@dataclass
class RowField:
    name: str
    rust_type: str  # u32, u64, or String


@dataclass
class PostProcessState:
    tbl_path: str = DEFAULT_TBL
    row_limit: int = DEFAULT_LIMIT
    row_fields: list[RowField] = field(default_factory=list)
    needs_dataset: bool = False


def postprocess(file_path: str, tbl_path: str = DEFAULT_TBL, row_limit: int = DEFAULT_LIMIT) -> None:
    if not os.path.exists(file_path):
        return
    with open(file_path, "r") as f:
        content = f.read()
    if "fn RunQuery" not in content:
        return
    state = PostProcessState(tbl_path=tbl_path, row_limit=row_limit)
    out = _transform(content, state)
    with open(file_path, "w") as f:
        f.write(out)


def _transform(content: str, state: PostProcessState) -> str:
    _extract_row_schema(content, state)
    content = _inject_dataset_loader(content, state)
    content = _rewrite_runquery_body(content)
    if state.needs_dataset:
        content = _ensure_mod_dataset(content)
        content = _inject_loadable_impl(content, state)
    return content


def _extract_row_schema(content: str, state: PostProcessState) -> None:
    m = re.search(r"pub enum Row\s*\{\s*Row\s*\{([^}]+)\}", content, re.DOTALL)
    if not m:
        return
    for part in m.group(1).split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        name, ty = part.split(":", 1)
        name = name.strip()
        ty = ty.strip()
        if "Sequence" in ty:
            rust_ty = "String"
        elif "u64" in ty:
            rust_ty = "u64"
        else:
            rust_ty = "u32"
        state.row_fields.append(RowField(name, rust_ty))


def _strip_method_spec(content: str) -> str:
    return re.sub(
        r"fn MethodSpec[\s\S]*?^\s*\}\s*\n(?=\s*(?:pub\s+)?fn\s|\s*#\[|\s*\})",
        "",
        content,
        flags=re.MULTILINE,
    )


def _inject_dataset_loader(content: str, state: PostProcessState) -> str:
    pat = re.compile(
        r"let mut data\s*:\s*Sequence\s*<\s*Rc\s*<\s*Row\s*>\s*>\s*=\s*(?:\[\s*\]|seq!\[\s*\])\s*;",
    )
    tbl_lit = json.dumps(state.tbl_path)
    repl = (
        f"let mut data: Sequence<Rc<Row>> = "
        f"crate::dataset::load_dataset::<Row>({tbl_lit}, {state.row_limit});"
    )
    if pat.search(content):
        state.needs_dataset = True
        content = pat.sub(repl, content, count=1)
    return content


def _ensure_mod_dataset(content: str) -> str:
    if "mod dataset;" in content:
        return content
    pos = content.find("pub mod _module")
    if pos != -1:
        return content[:pos] + "mod dataset; " + content[pos:]
    return "mod dataset;\n" + content


def _build_loadable_impl(state: PostProcessState) -> str:
    lines = []
    for fld in state.row_fields:
        col = fld.name.upper()
        access = f'f[ci["{col}"]]'
        if fld.rust_type == "String":
            lines.append(f"            {fld.name}: ::dafny_runtime::string_of({access}),")
        else:
            lines.append(f"            {fld.name}: {access}.parse::<{fld.rust_type}>().unwrap(),")
    body = "\n".join(lines)
    return f"""
    impl crate::dataset::Loadable for crate::_module::Row {{
        fn from_fields(f: &[&str], ci: &std::collections::HashMap<String, usize>) -> Self {{
            crate::_module::Row::Row {{
{body}
            }}
        }}
    }}
"""


def _inject_loadable_impl(content: str, state: PostProcessState) -> str:
    impl = _build_loadable_impl(state)
    if "impl crate::dataset::Loadable" in content:
        return content
    marker = "pub enum Row"
    pos = content.find(marker)
    if pos == -1:
        return content + impl
    end = content.find("} }", pos)
    if end == -1:
        return content + impl
    insert_at = end + 3
    return content[:insert_at] + impl + content[insert_at:]


def _rewrite_runquery_body(content: str) -> str:
    tree = PARSER.parse(content.encode("utf-8"))
    root = tree.root_node
    run_query = _find_run_query_fn(root)
    if run_query is None:
        return content
    edits: list[tuple[int, int, str]] = []

    body = run_query.child_by_field_name("body")
    if body:
        _collect_runquery_edits(body, content.encode("utf-8"), edits)

    edits.sort(key=lambda e: e[0], reverse=True)
    b = bytearray(content.encode("utf-8"))
    for start, end, repl in edits:
        b[start:end] = repl.encode("utf-8")
    return b.decode("utf-8")


def _find_run_query_fn(root: Node) -> Node | None:
    for child in root.children:
        if child.type == "function_item":
            name = child.child_by_field_name("name")
            if name and _node_text(name) == "RunQuery":
                return child
        if child.type in ("mod_item", "source_file", "declaration_list"):
            found = _find_run_query_fn(child)
            if found:
                return found
        if child.type == "impl_item":
            for item in child.children:
                if item.type == "function_item":
                    name = item.child_by_field_name("name")
                    if name and _node_text(name) == "RunQuery":
                        return item
    return None


def _collect_runquery_edits(node: Node, src: bytes, edits: list[tuple[int, int, str]]) -> None:
    if node.type == "let_declaration":
        txt = src[node.start_byte:node.end_byte].decode("utf-8")
        m = re.search(
            r"let mut (\w+)\s*:\s*Rc\s*<\s*Row\s*>\s*=\s*(\w+)_vec\[i\]\.clone\(\)",
            txt.replace(" ", ""),
        )
        if m:
            row, base = m.group(1), m.group(2)
            new = f"let mut {row} = &{base}_vec[i];"
            edits.append((node.start_byte, node.end_byte, new))
            return

    if node.type == "method_call_expression":
        method = node.child_by_field_name("name")
        args = node.child_by_field_name("arguments")
        if method and _node_text(method) == "get" and args:
            arg_txt = src[args.start_byte:args.end_byte].decode("utf-8").strip()
            if re.fullmatch(r"\(\s*&i\s*\)", arg_txt):
                recv = node.child_by_field_name("value")
                recv_txt = src[recv.start_byte:recv.end_byte].decode("utf-8") if recv else ""
                new = f"{recv_txt}.get_usize(i)"
                edits.append((node.start_byte, node.end_byte, new))
                return

    for child in node.children:
        _collect_runquery_edits(child, src, edits)


def _node_text(node: Node) -> str:
    return node.text.decode("utf-8") if isinstance(node.text, bytes) else (node.text or "")


def inject_hot_loop_main(file_path: str, tbl_path: str, row_limit: int) -> None:
    """Replace Dafny's main with: load once, warm 2x, time 3rd RunQuery."""
    with open(file_path) as f:
        content = f.read()
    content = re.sub(r"\nfn main\s*\(\)\s*\{[\s\S]*\}\s*$", "\n", content)
    tbl_lit = json.dumps(tbl_path)
    harness = f"""
fn main() {{
    use std::time::Instant;
    let data = crate::dataset::load_dataset::<crate::_module::Row>({tbl_lit}, {row_limit});
    for run in 0..3 {{
        let t0 = Instant::now();
        let _ = crate::_module::_default::RunQuery(&data);
        let dt = t0.elapsed().as_micros();
        if run == 2 {{
            println!("QUERY_LATENCY_US: {{}}", dt);
        }}
    }}
}}
"""
    if "mod dataset;" not in content:
        pos = content.find("pub mod _module")
        if pos != -1:
            content = content[:pos] + "mod dataset; " + content[pos:]
    state = PostProcessState(tbl_path=tbl_path, row_limit=row_limit)
    _extract_row_schema(content, state)
    if "impl crate::dataset::Loadable" not in content:
        content = _inject_loadable_impl(content, state)
    with open(file_path, "w") as f:
        f.write(content + harness)
