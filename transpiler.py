import re
import sqlglot
from sqlglot import exp

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
        self.agg_expr_dafny: str = ""

def parse_sql(sql_str: str, schema_dict: dict[str, str]) -> SQLQuery:
    """Parses a SQL statement within the supported dashboard contract boundary using sqlglot."""
    # Build a case-insensitive schema mapping to match columns correctly and preserve their original case
    schema_resolved = {k.lower(): (k, v) for k, v in schema_dict.items()}

    try:
        expression = sqlglot.parse_one(sql_str)
    except Exception as e:
        raise UnsupportedContractError(f"Query parsing failed: {e}")

    if not isinstance(expression, exp.Select):
        raise UnsupportedContractError("Query falls outside the supported dashboard subset.")

    # 1. Check for forbidden node types (JOINs, UNIONs, subqueries, complex predicates)
    for node in expression.walk():
        if isinstance(node, (
            exp.Join, exp.Union, exp.Subquery, exp.Having, exp.Order, 
            exp.Limit, exp.Exists, exp.In, exp.Like, exp.Between,
            exp.Max, exp.Min, exp.Distinct
        )):
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")

    # 2. FROM clause validation
    from_clause = expression.args.get("from_")
    if not from_clause:
        raise UnsupportedContractError("Query must have a FROM clause.")
    if not isinstance(from_clause.this, exp.Table):
        raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
    table_name = from_clause.this.name

    query = SQLQuery()
    query.table = table_name

    # 3. GROUP BY clause validation
    groupby_clause = expression.args.get("group")
    if groupby_clause:
        groupby_exprs = groupby_clause.expressions
        if len(groupby_exprs) != 1:
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        groupby_node = groupby_exprs[0]
        if not isinstance(groupby_node, exp.Column):
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        groupby_col_lower = groupby_node.name.lower()
        if groupby_col_lower not in schema_resolved:
            raise UnsupportedContractError(f"Group by column '{groupby_node.name}' not found in schema.")
        query.groupby_column = schema_resolved[groupby_col_lower][0]

    # Helper to strip alias
    def unwrap_alias(node):
        if isinstance(node, exp.Alias):
            return node.this
        return node

    # 4. SELECT items validation
    select_items = expression.expressions
    if query.groupby_column:
        if len(select_items) != 2:
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        unwrapped = [unwrap_alias(item) for item in select_items]
        
        col_node = None
        agg_node = None
        for item in unwrapped:
            if isinstance(item, exp.Column) and item.name.lower() == query.groupby_column.lower():
                col_node = item
            elif isinstance(item, (exp.Sum, exp.Count, exp.Avg)):
                agg_node = item
        if not col_node or not agg_node:
            raise UnsupportedContractError("Query select clause must include the group by column.")
    else:
        if len(select_items) != 1:
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
        agg_node = unwrap_alias(select_items[0])
        if not isinstance(agg_node, (exp.Sum, exp.Count, exp.Avg)):
            raise UnsupportedContractError("Query falls outside the supported dashboard subset.")

    # Helper to recursively compile expression to Dafny
    def to_dafny_expr(node):
        if isinstance(node, exp.Column):
            col_lower = node.name.lower()
            if col_lower not in schema_resolved:
                raise UnsupportedContractError(f"Identifier '{node.name}' not found in schema.")
            real_col, col_type = schema_resolved[col_lower]
            if col_type != 'int':
                raise UnsupportedContractError(f"Column '{real_col}' in expression must be of type 'int'.")
            return f"row.{real_col}"
        elif isinstance(node, exp.Literal):
            if node.is_number and node.this.isdigit():
                return str(node.this)
            raise UnsupportedContractError(f"Only integer literals supported in expressions.")
        elif isinstance(node, exp.Paren):
            return f"({to_dafny_expr(node.this)})"
        elif isinstance(node, exp.Mul):
            return f"{to_dafny_expr(node.left)} * {to_dafny_expr(node.right)}"
        elif isinstance(node, exp.Div):
            return f"{to_dafny_expr(node.left)} / {to_dafny_expr(node.right)}"
        elif isinstance(node, exp.Add):
            return f"{to_dafny_expr(node.left)} + {to_dafny_expr(node.right)}"
        elif isinstance(node, exp.Sub):
            return f"{to_dafny_expr(node.left)} - {to_dafny_expr(node.right)}"
        elif isinstance(node, exp.Star):
            return "*"
        else:
            raise UnsupportedContractError(f"Unsupported expression construct: {type(node)}")

    # Parse and validate aggregation node
    if isinstance(agg_node, exp.Count):
        query.agg_type = "COUNT"
        if isinstance(agg_node.this, exp.Star):
            query.agg_column = "*"
            query.agg_expr_dafny = "1"
        else:
            if not isinstance(agg_node.this, exp.Column):
                raise UnsupportedContractError("COUNT argument must be * or a column.")
            col_lower = agg_node.this.name.lower()
            if col_lower not in schema_resolved:
                raise UnsupportedContractError(f"Aggregate column '{agg_node.this.name}' not found in schema.")
            real_col, _ = schema_resolved[col_lower]
            query.agg_column = real_col
            query.agg_expr_dafny = "1"
    else:
        query.agg_type = "SUM" if isinstance(agg_node, exp.Sum) else "AVG"
        query.agg_expr_dafny = to_dafny_expr(agg_node.this)
        # Preserve original sql string for functional test runner compatibility
        query.agg_column = agg_node.this.sql()

    # 5. Parse WHERE clause
    where_clause = expression.args.get("where")
    if where_clause:
        # Walk and forbid any Or or Not nodes
        for w_node in where_clause.walk():
            if isinstance(w_node, (exp.Or, exp.Not)):
                raise UnsupportedContractError("Query falls outside the supported dashboard subset.")

        # Helper to flatten Ands
        def flatten_and(node):
            if isinstance(node, exp.And):
                return flatten_and(node.left) + flatten_and(node.right)
            return [node]

        conditions = flatten_and(where_clause.this)
        
        op_map = {
            exp.EQ: '=',
            exp.NEQ: '!=',
            exp.GT: '>',
            exp.LT: '<',
            exp.GTE: '>=',
            exp.LTE: '<='
        }

        for cond in conditions:
            # Must be a valid comparison
            op_type = type(cond)
            op = op_map.get(op_type)
            if not op:
                raise UnsupportedContractError("Query falls outside the supported dashboard subset.")

            # Left side must be a Column
            if not isinstance(cond.left, exp.Column):
                raise UnsupportedContractError("Left hand side of comparison must be a column.")
            col_lower = cond.left.name.lower()
            if col_lower not in schema_resolved:
                raise UnsupportedContractError(f"Filter column '{cond.left.name}' not found in schema.")
            real_col, col_type = schema_resolved[col_lower]

            # Right side can be Literal or Column
            right_node = cond.right
            if isinstance(right_node, exp.Literal):
                if right_node.is_string:
                    val_resolved = right_node.this
                    val_type = 'string'
                elif right_node.is_number and right_node.this.isdigit():
                    val_resolved = int(right_node.this)
                    val_type = 'int'
                else:
                    raise UnsupportedContractError("Query falls outside the supported dashboard subset.")
            elif isinstance(right_node, exp.Column):
                rcol_lower = right_node.name.lower()
                if rcol_lower not in schema_resolved:
                    raise UnsupportedContractError(f"Filter column '{right_node.name}' not found in schema.")
                rreal_col, rcol_type = schema_resolved[rcol_lower]
                val_resolved = rreal_col
                val_type = 'column'
            else:
                raise UnsupportedContractError("Query falls outside the supported dashboard subset.")

            # Type checking
            if col_type == 'int':
                if val_type == 'column':
                    if schema_resolved[val_resolved.lower()][1] != 'int':
                        raise UnsupportedContractError(f"Type mismatch: comparing int column '{real_col}' with non-int column '{val_resolved}'.")
                elif val_type != 'int':
                    raise UnsupportedContractError(f"Type mismatch: comparing int column '{real_col}' with non-int value.")
            elif col_type == 'string':
                if val_type == 'column':
                    if schema_resolved[val_resolved.lower()][1] != 'string':
                        raise UnsupportedContractError(f"Type mismatch: comparing string column '{real_col}' with non-string column '{val_resolved}'.")
                elif val_type != 'string':
                    raise UnsupportedContractError(f"Type mismatch: comparing string column '{real_col}' with non-string value.")
                if op not in ('=', '!='):
                    raise UnsupportedContractError(f"Unsupported operator '{op}' for string type comparison.")

            query.where_conditions.append((real_col, op, val_resolved, val_type))

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
            term_expr = query.agg_expr_dafny if is_sum else "1"
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
            term_expr = query.agg_expr_dafny if is_sum else "1"
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
                    f"{term_expr} + {func_name}(tail)"
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
