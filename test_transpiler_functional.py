import unittest
import subprocess
import tempfile
import os
import sqlite3
from transpiler import transpile_sql_to_dafny, UnsupportedContractError, parse_sql

@unittest.skipIf(os.environ.get("RUN_SLOW") != "1", "Skipping slow Dafny functional tests. Run with RUN_SLOW=1 to execute.")
class TestTranspilerFunctional(unittest.TestCase):
    def setUp(self):
        # Set up a rich schema dictionary and dummy dataset for functional verification
        self.schema = {
            "category": "string",
            "value": "int",
            "age": "int",
            "name": "string"
        }
        
        self.dummy_data = [
            {"category": "A", "value": 10, "age": 20, "name": "Alice"},
            {"category": "B", "value": 20, "age": 30, "name": "Bob"},
            {"category": "A", "value": 30, "age": 25, "name": "Charlie"},
            {"category": "C", "value": 15, "age": 22, "name": "David"},
            {"category": "B", "value": 25, "age": 35, "name": "Eve"},
            {"category": "A", "value": 5, "age": 19, "name": "Frank"},
        ]

    def evaluate_query_python(self, query_str):
        query = parse_sql(query_str, self.schema)
        
        # 1. Filter rows
        filtered_rows = []
        for row in self.dummy_data:
            keep = True
            for col, op, val, val_type in query.where_conditions:
                row_val = row[col]
                if val_type == 'column':
                    right_val = row[val]
                else:
                    right_val = val
                
                if op == '=':
                    match = (row_val == right_val)
                elif op == '!=':
                    match = (row_val != right_val)
                elif op == '>':
                    match = (row_val > right_val)
                elif op == '<':
                    match = (row_val < right_val)
                else:
                    match = False
                
                if not match:
                    keep = False
                    break
            if keep:
                filtered_rows.append(row)
                
        # 2. Group by
        groups = {}
        if query.groupby_column:
            for row in filtered_rows:
                key = row[query.groupby_column]
                groups.setdefault(key, []).append(row)
        else:
            groups[None] = filtered_rows
            
        # 3. Aggregate
        results = {}
        for gkey, g_rows in groups.items():
            if query.agg_type == 'COUNT':
                val = len(g_rows)
            elif query.agg_type == 'SUM':
                val = sum(r[query.agg_column] for r in g_rows)
            elif query.agg_type == 'AVG':
                s = sum(r[query.agg_column] for r in g_rows)
                c = len(g_rows)
                val = s // c if c > 0 else 0
            else:
                raise ValueError(f"Unknown aggregation: {query.agg_type}")
            results[gkey] = val
            
        if query.groupby_column:
            return results
        else:
            return results[None]

    def verify_query(self, query_str):
        # 1. Get expected result from Python reference evaluation
        expected = self.evaluate_query_python(query_str)
        
        # 2. Transpile SQL to Dafny
        dafny_spec = transpile_sql_to_dafny(query_str, self.schema)
        
        # 3. Generate the full Dafny program with runner
        row_exprs = []
        for row in self.dummy_data:
            vals = []
            for col in self.schema:
                val = row[col]
                if self.schema[col] == 'int':
                    vals.append(str(val))
                elif self.schema[col] == 'string':
                    vals.append(f'"{val}"')
            row_exprs.append(f"Row({', '.join(vals)})")
            
        data_seq = f"[{', '.join(row_exprs)}]"
        
        print_lines = ['print "---BEGIN---", "\\n";']
        if isinstance(expected, dict):
            print_lines.append('print "size:", |res|, "\\n";')
            for key in expected:
                if isinstance(key, str):
                    dafny_key = f'"{key}"'
                else:
                    dafny_key = str(key)
                print_lines.append(
                    f'print {dafny_key}, ":", if {dafny_key} in res then res[{dafny_key}] else -999999, "\\n";'
                )
        else:
            print_lines.append('print res, "\\n";')
        print_lines.append('print "---END---", "\\n";')
        
        prints_str = "\n  ".join(print_lines)
        
        dafny_code = f"""
{dafny_spec}

method Main() {{
  var data := {data_seq};
  var res := MethodSpec(data);
  {prints_str}
}}
"""
        # 4. Write to a temp file and execute dafny
        with tempfile.NamedTemporaryFile(suffix=".dfy", mode="w", delete=False) as tmp:
            tmp.write(dafny_code)
            tmp_name = tmp.name
            
        try:
            res = subprocess.run(
                ["dafny", "run", tmp_name],
                capture_output=True,
                text=True
            )
            if res.returncode != 0:
                self.fail(
                    f"Dafny compilation or execution failed for query: {query_str}\n"
                    f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
                )
            
            # 5. Parse output
            lines = res.stdout.splitlines()
            in_block = False
            block_lines = []
            for line in lines:
                line_str = line.strip()
                if line_str == "---BEGIN---":
                    in_block = True
                    continue
                elif line_str == "---END---":
                    in_block = False
                    break
                if in_block:
                    block_lines.append(line_str)
                    
            # 6. Assert correctness
            if isinstance(expected, dict):
                parsed_dict = {}
                size = None
                for line in block_lines:
                    if line.startswith("size:"):
                        size = int(line.split(":")[1])
                    else:
                        key_part, val_part = line.split(":", 1)
                        try:
                            key = int(key_part)
                        except ValueError:
                            key = key_part
                        val = int(val_part)
                        parsed_dict[key] = val
                self.assertEqual(size, len(expected), f"Map size mismatch for query: {query_str}")
                self.assertEqual(parsed_dict, expected, f"Result mapping mismatch for query: {query_str}")
            else:
                self.assertTrue(len(block_lines) > 0, "No output found between markers")
                actual_val = int(block_lines[0])
                self.assertEqual(actual_val, expected, f"Scalar result mismatch for query: {query_str}")
                
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def test_functional_basic_sum(self):
        self.verify_query("SELECT SUM(value) FROM my_table")

    def test_functional_basic_count(self):
        self.verify_query("SELECT COUNT(*) FROM my_table")

    def test_functional_basic_avg(self):
        self.verify_query("SELECT AVG(value) FROM my_table")

    def test_functional_sum_groupby_string(self):
        self.verify_query("SELECT category, SUM(value) FROM my_table GROUP BY category")

    def test_functional_avg_groupby_string(self):
        self.verify_query("SELECT category, AVG(value) FROM my_table GROUP BY category")

    def test_functional_sum_groupby_int(self):
        self.verify_query("SELECT age, SUM(value) FROM my_table GROUP BY age")

    def test_functional_where_filter_string(self):
        self.verify_query("SELECT SUM(value) FROM my_table WHERE category = 'A'")

    def test_functional_where_filter_int_inequality(self):
        self.verify_query("SELECT SUM(value) FROM my_table WHERE age > 21")

    def test_functional_where_multiple_conditions(self):
        self.verify_query("SELECT COUNT(*) FROM my_table WHERE category = 'A' AND age > 19 AND name != 'Frank'")

    def test_functional_empty_dataset(self):
        orig = self.dummy_data
        self.dummy_data = []
        try:
            # SUM on empty set
            self.verify_query("SELECT SUM(value) FROM my_table")
            # COUNT on empty set
            self.verify_query("SELECT COUNT(*) FROM my_table")
            # AVG on empty set
            self.verify_query("SELECT AVG(value) FROM my_table")
            # SUM GROUP BY on empty set
            self.verify_query("SELECT category, SUM(value) FROM my_table GROUP BY category")
        finally:
            self.dummy_data = orig

if __name__ == '__main__':
    unittest.main()
