import re

class UnsupportedContractError(Exception):
    """Raised when a SQL query falls outside the supported dashboard subset."""
    pass

class DafnyLiteral:
    """Represents a literal value or a raw code fragment in Dafny."""
    def __init__(self, value: str):
        self.value = value

    def to_dafny(self) -> str:
        return str(self.value)

class DafnyIf:
    """Represents an if-then-else expression in Dafny."""
    def __init__(self, condition: str, then_expr, else_expr):
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr

    def to_dafny(self) -> str:
        then_str = self.then_expr.to_dafny() if hasattr(self.then_expr, 'to_dafny') else str(self.then_expr)
        else_str = self.else_expr.to_dafny() if hasattr(self.else_expr, 'to_dafny') else str(self.else_expr)
        return f"if {self.condition} then {then_str} else {else_str}"

class DafnyFunction:
    """Represents a mathematical function definition in Dafny."""
    def __init__(self, name: str, params: list[tuple[str, str]], return_type: str, body):
        self.name = name
        self.params = params  # list of (name, type)
        self.return_type = return_type
        self.body = body

    def to_dafny(self) -> str:
        params_str = ", ".join(f"{name}: {type_}" for name, type_ in self.params)
        body_str = self.body.to_dafny() if hasattr(self.body, 'to_dafny') else str(self.body)
        
        # Indent the body nicely
        indented_body = "\n".join("  " + line for line in body_str.split("\n"))
        return (
            f"function {self.name}({params_str}): {self.return_type}\n"
            f"{{\n"
            f"{indented_body}\n"
            f"}}"
        )

class SQLQuery:
    """AST representation of a supported SQL query."""
    def __init__(self):
        self.table: str = ""
        self.agg_type: str = ""  # SUM, COUNT, AVG
        self.agg_column: str = ""  # Column name or "*"
        self.groupby_column: str = None  # Group by column name, if any
        self.where_conditions: list[tuple[str, str, any, str]] = []  # list of (col, op, val, val_type)

def parse_sql(sql_str: str, schema_dict: dict[str, str]) -> SQLQuery:
    """Parses a SQL statement within the supported dashboard contract boundary."""
    # 1. Normalize whitespaces
    sql_clean = " ".join(sql_str.strip().split())
    
    # 2. Extract string literals to avoid false keyword matching
    literals = []
    def replace_lit(match):
        lit = match.group(0)
        literals.append(lit)
        return f"__LIT_{len(literals)-1}__"
    
    sql_placeholder = re.sub(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"", replace_lit, sql_clean)
    
    # 3. Check for forbidden keywords / patterns case-insensitively on placeholder
    sql_upper = sql_placeholder.upper()
    
    forbidden = [
        r'\bJOIN\b', r'\bUNION\b', r'\bOR\b', r'\bHAVING\b', 
        r'\bORDER\s+BY\b', r'\bLIMIT\b', r'\bIN\b', r'\bLIKE\b', 
        r'\bBETWEEN\b', r'\bNOT\b', r'\bEXISTS\b', r'\bMIN\b', r'\bMAX\b'
    ]
    for pattern in forbidden:
        if re.search(pattern, sql_upper):
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
            
    # Check for multiple SELECT, FROM, or GROUP BY to prevent subqueries or complex syntax
    if len(re.findall(r'\bSELECT\b', sql_upper)) > 1:
        raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
    if len(re.findall(r'\bGROUP\b', sql_upper)) > 1:
        raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
    if len(re.findall(r'\bFROM\b', sql_upper)) > 1:
        raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        
    # 4. Match overall query structure
    pattern = r'^SELECT\s+(.*?)\s+FROM\s+(.*?)(?:\s+WHERE\s+(.*?))?(?:\s+GROUP\s+BY\s+(.*?))?$'
    match = re.match(pattern, sql_placeholder, re.IGNORECASE)
    if not match:
        raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        
    select_body = match.group(1).strip()
    from_body = match.group(2).strip()
    where_body = match.group(3).strip() if match.group(3) else None
    groupby_body = match.group(4).strip() if match.group(4) else None
    
    # Validate FROM clause (only a single table identifier)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', from_body):
        raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        
    query = SQLQuery()
    query.table = from_body
    
    # Validate and parse GROUP BY (only a single column identifier)
    if groupby_body:
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', groupby_body):
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        if groupby_body not in schema_dict:
            raise UnsupportedContractError(f"Group by column '{groupby_body}' not found in schema.")
        query.groupby_column = groupby_body

    # Validate and parse SELECT body
    select_items = [item.strip() for item in select_body.split(',')]
    if query.groupby_column:
        if len(select_items) != 2:
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        # One must be the group by column, the other the aggregation
        if select_items[0] == query.groupby_column:
            agg_item = select_items[1]
        elif select_items[1] == query.groupby_column:
            agg_item = select_items[0]
        else:
            raise UnsupportedContractError("Query select clause must include the group by column.")
    else:
        if len(select_items) != 1:
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        agg_item = select_items[0]
        
    # Match the aggregation expression
    agg_match = re.match(r'^(SUM|COUNT|AVG)\s*\(\s*(.*?)\s*\)$', agg_item, re.IGNORECASE)
    if not agg_match:
        raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        
    query.agg_type = agg_match.group(1).upper()
    query.agg_column = agg_match.group(2).strip()
    
    # Validate aggregation column
    if query.agg_type == 'COUNT':
        if query.agg_column != '*':
            if query.agg_column not in schema_dict:
                raise UnsupportedContractError(f"Aggregate column '{query.agg_column}' not found in schema.")
    else: # SUM or AVG
        if query.agg_column not in schema_dict:
            raise UnsupportedContractError(f"Aggregate column '{query.agg_column}' not found in schema.")
        if schema_dict[query.agg_column] != 'int':
            raise UnsupportedContractError(f"Aggregate column '{query.agg_column}' must be of type 'int'.")
            
    # 5. Parse WHERE conditions
    if where_body:
        # Split on AND, keeping word boundaries
        conditions_raw = re.split(r'\bAND\b', where_body, flags=re.IGNORECASE)
        for cond_str in conditions_raw:
            cond_str = cond_str.strip()
            # Match: column operator value
            cond_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*(=|!=|<>|>|<)\s*(.*)$', cond_str)
            if not cond_match:
                raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
            
            col = cond_match.group(1).strip()
            op = cond_match.group(2).strip()
            if op == '<>':
                op = '!='
            val_expr = cond_match.group(3).strip()
            
            if col not in schema_dict:
                raise UnsupportedContractError(f"Filter column '{col}' not found in schema.")
                
            col_type = schema_dict[col]
            
            # Resolve value expression
            # Check for literal placeholder
            lit_match = re.match(r'^__LIT_(\d+)__$', val_expr)
            if lit_match:
                lit_idx = int(lit_match.group(1))
                raw_lit = literals[lit_idx]
                # Strip quotes
                lit_val = raw_lit[1:-1]
                # In SQL, an escaped quote '' is replaced by '
                if raw_lit.startswith("'"):
                    lit_val = lit_val.replace("''", "'")
                else:
                    lit_val = lit_val.replace('""', '"')
                val_resolved = lit_val
                val_type = 'string'
            else:
                # Try parsing as int
                try:
                    val_resolved = int(val_expr)
                    val_type = 'int'
                except ValueError:
                    # Check if it's a column in schema
                    if val_expr in schema_dict:
                        val_resolved = val_expr
                        val_type = 'column'
                    else:
                        raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
                        
            # Type check operator and operands
            if col_type == 'int':
                if val_type == 'column':
                    if schema_dict[val_resolved] != 'int':
                        raise UnsupportedContractError(f"Type mismatch: comparing int column '{col}' with non-int column '{val_resolved}'.")
                elif val_type != 'int':
                    raise UnsupportedContractError(f"Type mismatch: comparing int column '{col}' with non-int value.")
            elif col_type == 'string':
                if val_type == 'column':
                    if schema_dict[val_resolved] != 'string':
                        raise UnsupportedContractError(f"Type mismatch: comparing string column '{col}' with non-string column '{val_resolved}'.")
                elif val_type != 'string':
                    raise UnsupportedContractError(f"Type mismatch: comparing string column '{col}' with non-string value.")
                if op not in ('=', '!='):
                    raise UnsupportedContractError(f"Unsupported operator '{op}' for string type comparison.")
            
            query.where_conditions.append((col, op, val_resolved, val_type))
            
    return query

def transpile_sql_to_dafny(sql_str: str, schema_dict: dict[str, str]) -> str:
    """Translates SQL query to mathematical Dafny specification."""
    # 1. Parse and validate schema
    for col, col_type in schema_dict.items():
        if col_type not in ('int', 'string'):
            raise UnsupportedContractError(f"Unsupported column type in schema: {col_type}")

    # 2. Parse SQL
    query = parse_sql(sql_str, schema_dict)

    # 3. Generate schema datatype representation
    fields = [f"{col}: {schema_dict[col]}" for col in schema_dict]
    fields_str = ", ".join(fields)
    schema_dafny = f"datatype Row = Row({fields_str})"

    # 4. Determine key variables
    agg_col = query.agg_column
    groupby_col = query.groupby_column
    
    # Construct WHERE clause condition for row
    if query.where_conditions:
        cond_parts = []
        for col, op, val, val_type in query.where_conditions:
            dafny_op = "==" if op == "=" else op
            if val_type == 'column':
                right = f"row.{val}"
            elif val_type == 'string':
                right = f'"{val}"'
            else:
                right = str(val)
            cond_parts.append(f"row.{col} {dafny_op} {right}")
        where_expr = " && ".join(cond_parts)
    else:
        where_expr = None

    # Helper function to generate a SUM or COUNT recursive body
    def make_recursive_body(func_name: str, is_sum: bool, return_type: str):
        # Base case
        cond = "|data| == 0"
        then_val = "map[]" if "map" in return_type else "0"
        
        # Else case
        if groupby_col:
            # GROUP BY recursive logic
            term_expr = f"row.{agg_col}" if is_sum else "1"
            if where_expr:
                else_body = (
                    f"var tailMap := {func_name}(data[1..]);\n"
                    f"var row := data[0];\n"
                    f"if {where_expr} then\n"
                    f"  var key := row.{groupby_col};\n"
                    f"  var val := if key in tailMap then tailMap[key] else 0;\n"
                    f"  tailMap[key := val + {term_expr}]\n"
                    f"else\n"
                    f"  tailMap"
                )
            else:
                else_body = (
                    f"var tailMap := {func_name}(data[1..]);\n"
                    f"var row := data[0];\n"
                    f"var key := row.{groupby_col};\n"
                    f"var val := if key in tailMap then tailMap[key] else 0;\n"
                    f"tailMap[key := val + {term_expr}]"
                )
        else:
            # Single aggregation recursive logic
            term_expr = f"row.{agg_col}" if is_sum else "1"
            if where_expr:
                else_body = (
                    f"var row := data[0];\n"
                    f"var tail := data[1..];\n"
                    f"var term := if {where_expr} then {term_expr} else 0;\n"
                    f"term + {func_name}(tail)"
                )
            else:
                else_body = (
                    f"var row := data[0];\n"
                    f"var tail := data[1..];\n"
                    f"row.{agg_col} + {func_name}(tail)" if is_sum else
                    f"var row := data[0];\n"
                    f"var tail := data[1..];\n"
                    f"1 + {func_name}(tail)"
                )
                
        return DafnyIf(cond, DafnyLiteral(then_val), DafnyLiteral(else_body))

    # Generate function definitions based on aggregation type
    functions = []
    
    if query.agg_type == 'AVG':
        if groupby_col:
            key_type = schema_dict[groupby_col]
            ret_type = f"map<{key_type}, int>"
            
            # Generate SumMapHelper
            sum_body = make_recursive_body("SumMapHelper", is_sum=True, return_type=ret_type)
            sum_func = DafnyFunction("SumMapHelper", [("data", "seq<Row>")], ret_type, sum_body)
            functions.append(sum_func)
            
            # Generate CountMapHelper
            count_body = make_recursive_body("CountMapHelper", is_sum=False, return_type=ret_type)
            count_func = DafnyFunction("CountMapHelper", [("data", "seq<Row>")], ret_type, count_body)
            functions.append(count_func)
            
            # Generate MethodSpec combining them
            spec_body = DafnyLiteral(
                f"var sums := SumMapHelper(data);\n"
                f"var counts := CountMapHelper(data);\n"
                f"map k | k in sums && k in counts :: if counts[k] == 0 then 0 else sums[k] / counts[k]"
            )
            spec_func = DafnyFunction("MethodSpec", [("data", "seq<Row>")], ret_type, spec_body)
            functions.append(spec_func)
        else:
            # Generate SumHelper
            sum_body = make_recursive_body("SumHelper", is_sum=True, return_type="int")
            sum_func = DafnyFunction("SumHelper", [("data", "seq<Row>")], "int", sum_body)
            functions.append(sum_func)
            
            # Generate CountHelper
            count_body = make_recursive_body("CountHelper", is_sum=False, return_type="int")
            count_func = DafnyFunction("CountHelper", [("data", "seq<Row>")], "int", count_body)
            functions.append(count_func)
            
            # Generate MethodSpec combining them
            spec_body = DafnyLiteral(
                f"var sum := SumHelper(data);\n"
                f"var count := CountHelper(data);\n"
                f"if count == 0 then 0 else sum / count"
            )
            spec_func = DafnyFunction("MethodSpec", [("data", "seq<Row>")], "int", spec_body)
            functions.append(spec_func)
    else:
        # SUM or COUNT
        is_sum = (query.agg_type == 'SUM')
        if groupby_col:
            key_type = schema_dict[groupby_col]
            ret_type = f"map<{key_type}, int>"
        else:
            ret_type = "int"
            
        spec_body = make_recursive_body("MethodSpec", is_sum=is_sum, return_type=ret_type)
        spec_func = DafnyFunction("MethodSpec", [("data", "seq<Row>")], ret_type, spec_body)
        functions.append(spec_func)

    # Combine everything
    functions_dafny = "\n\n".join(func.to_dafny() for func in functions)
    return f"{schema_dafny}\n\n{functions_dafny}"
