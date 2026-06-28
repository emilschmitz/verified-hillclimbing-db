import unittest
from transpiler import transpile_sql_to_dafny, UnsupportedContractError

class TestTranspilerUnit(unittest.TestCase):
    def setUp(self):
        # Set up a standard schema dictionary for testing
        self.schema = {
            "category": "string",
            "value": "int",
            "age": "int",
            "name": "string"
        }

    def test_basic_sum(self):
        sql = "SELECT SUM(value) FROM my_table"
        result = transpile_sql_to_dafny(sql, self.schema)
        self.assertIn("datatype Row = Row(category: string, value: int, age: int, name: string)", result)
        self.assertIn("function MethodSpec(data: seq<Row>): int", result)
        self.assertIn("row.value + MethodSpec(tail)", result)

    def test_basic_count(self):
        sql = "SELECT COUNT(*) FROM my_table WHERE category = 'A'"
        result = transpile_sql_to_dafny(sql, self.schema)
        self.assertIn("datatype Row = Row(category: string, value: int, age: int, name: string)", result)
        self.assertIn("function MethodSpec(data: seq<Row>): int", result)
        self.assertIn("var term := if row.category == \"A\" then 1 else 0;", result)

    def test_avg_no_groupby(self):
        sql = "SELECT AVG(value) FROM my_table WHERE age > 18"
        result = transpile_sql_to_dafny(sql, self.schema)
        self.assertIn("function SumHelper(data: seq<Row>): int", result)
        self.assertIn("function CountHelper(data: seq<Row>): int", result)
        self.assertIn("function MethodSpec(data: seq<Row>): int", result)
        self.assertIn("var sum := SumHelper(data);", result)
        self.assertIn("var count := CountHelper(data);", result)
        self.assertIn("if count == 0 then 0 else sum / count", result)

    def test_sum_groupby(self):
        sql = "SELECT category, SUM(value) FROM my_table GROUP BY category"
        result = transpile_sql_to_dafny(sql, self.schema)
        self.assertIn("function MethodSpec(data: seq<Row>): map<string, int>", result)
        self.assertIn("var key := row.category;", result)
        self.assertIn("tailMap[key := val + row.value]", result)

    def test_avg_groupby(self):
        sql = "SELECT category, AVG(value) FROM my_table GROUP BY category"
        result = transpile_sql_to_dafny(sql, self.schema)
        self.assertIn("function SumMapHelper(data: seq<Row>): map<string, int>", result)
        self.assertIn("function CountMapHelper(data: seq<Row>): map<string, int>", result)
        self.assertIn("function MethodSpec(data: seq<Row>): map<string, int>", result)
        self.assertIn("map k | k in sums && k in counts :: if counts[k] == 0 then 0 else sums[k] / counts[k]", result)

    def test_groupby_int_key(self):
        sql = "SELECT age, SUM(value) FROM my_table GROUP BY age"
        result = transpile_sql_to_dafny(sql, self.schema)
        self.assertIn("function MethodSpec(data: seq<Row>): map<int, int>", result)
        self.assertIn("var key := row.age;", result)

    def test_where_multiple_conditions(self):
        sql = "SELECT SUM(value) FROM my_table WHERE category = 'A' AND age > 21 AND name != 'Bob'"
        result = transpile_sql_to_dafny(sql, self.schema)
        self.assertIn('row.category == "A" && row.age > 21 && row.name != "Bob"', result)

    def test_unsupported_queries(self):
        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT SUM(value) FROM my_table JOIN other_table", self.schema)
        
        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT SUM(value) FROM my_table WHERE value > (SELECT AVG(value) FROM my_table)", self.schema)

        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT MIN(value) FROM my_table", self.schema)

        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT SUM(value) FROM my_table WHERE category = 'A' OR age > 18", self.schema)

        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT SUM(non_existent) FROM my_table", self.schema)

        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT SUM(category) FROM my_table", self.schema)

        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT SUM(value) FROM my_table WHERE value = 'A'", self.schema)

        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT SUM(value) FROM my_table WHERE category > 'A'", self.schema)

        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT SUM(value) FROM my_table, other_table", self.schema)

        with self.assertRaises(UnsupportedContractError):
            transpile_sql_to_dafny("SELECT category, SUM(value) FROM my_table GROUP BY category, age", self.schema)

if __name__ == '__main__':
    unittest.main()
