import os
import sys
import subprocess
import unittest
import shutil
import re

# Ensure root directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from research_loop.postprocessor import postprocess

class TestPostProcessor(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.research_dir = os.path.join(self.root_dir, "research_loop")
        self.test_project_dir = os.path.join(self.research_dir, "temp_test_project")
        
        # Cleanup any leftover temp projects
        if os.path.exists(self.test_project_dir):
            shutil.rmtree(self.test_project_dir)
            
        # Create a new cargo project
        res = subprocess.run(["cargo", "new", "--bin", "temp_test_project"], cwd=self.research_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Cargo new failed: {res.stderr}")
        
        # Add dependency to Cargo.toml
        cargo_toml_path = os.path.join(self.test_project_dir, "Cargo.toml")
        with open(cargo_toml_path, "a") as f:
            f.write('\ndafny_runtime = { path = "../working_query-rust/runtime" }\n')

    def tearDown(self):
        if os.path.exists(self.test_project_dir):
            shutil.rmtree(self.test_project_dir)

    def test_semantic_divergence_underflow(self):
        # Write custom Dafny code that contains the full SSB schema Row definition
        # but executes a RunQuery loop that does (5 - 10 = -5) subtraction,
        # verifying successfully in Dafny but triggering unsigned underflow under u64.
        dfy_file = os.path.join(self.test_project_dir, "working_query.dfy")
        dafny_code = """
datatype Row = Row(
  LO_ORDERKEY: bv32,
  LO_LINENUMBER: bv32,
  LO_CUSTKEY: bv32,
  LO_PARTKEY: bv32,
  LO_SUPPKEY: bv32,
  LO_ORDERDATE: bv32,
  LO_ORDERPRIORITY: string,
  LO_SHIPPRIORITY: bv32,
  LO_QUANTITY: bv32,
  LO_EXTENDEDPRICE: bv64,
  LO_ORDTOTALPRICE: bv64,
  LO_DISCOUNT: bv32,
  LO_REVENUE: bv64,
  LO_SUPPLYCOST: bv64,
  LO_TAX: bv32,
  LO_COMMITDATE: bv32,
  LO_SHIPMODE: string,
  C_NAME: string,
  C_ADDRESS: string,
  C_CITY: string,
  C_NATION: string,
  C_REGION: string,
  C_PHONE: string,
  C_MKTSEGMENT: string,
  S_NAME: string,
  S_ADDRESS: string,
  S_CITY: string,
  S_NATION: string,
  S_REGION: string,
  S_PHONE: string,
  P_NAME: string,
  P_MFGR: string,
  P_CATEGORY: string,
  P_BRAND: string,
  P_COLOR: string,
  P_TYPE: string,
  P_SIZE: bv32,
  P_CONTAINER: string,
  D_YEAR: bv32,
  D_YEARMONTHNUM: bv32,
  D_WEEKNUMINYEAR: bv32
)

function MethodSpec(data: seq<Row>): int {
  -5
}

method RunQuery(data: seq<Row>) returns (res: int)
  ensures res == MethodSpec(data)
{
  res := 0; // Initialize res to 0 so the u64 replacement matches
  var val1: int := 5;
  var val2: int := 10;
  res := val1 - val2;
}

method Main() {
  var data: seq<Row> := [];
  var opt_res := RunQuery(data);
  print "OUTPUT: ", opt_res, "\\n";
}
"""
        with open(dfy_file, "w") as f:
            f.write(dafny_code)

        # 2. Translate Dafny to Rust
        translate_cmd = [
            "dafny", "translate", "rs",
            "--enforce-determinism",
            "working_query.dfy"
        ]
        res = subprocess.run(translate_cmd, cwd=self.test_project_dir, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Dafny translation failed: {res.stderr}\nSTDOUT: {res.stdout}")

        # 3. Copy the compiled Rust file to src/main.rs
        generated_rs = os.path.join(self.test_project_dir, "working_query-rust", "src", "working_query.rs")
        main_rs = os.path.join(self.test_project_dir, "src", "main.rs")
        shutil.copy2(generated_rs, main_rs)

        # 4. Compile and run the NORMAL (unoptimized) Rust binary
        run_cmd = ["cargo", "run", "--release"]
        normal_res = subprocess.run(run_cmd, cwd=self.test_project_dir, capture_output=True, text=True)
        self.assertEqual(normal_res.returncode, 0, f"Cargo run failed: {normal_res.stderr}")
        
        normal_output = normal_res.stdout
        print(f"Normal stdout: {normal_output.strip()}")

        # Extract output value
        normal_match = re.search(r"OUTPUT:\s*(-?\d+)", normal_output)
        self.assertTrue(normal_match, f"Failed to parse normal output: {normal_output}")
        normal_val = int(normal_match.group(1))
        
        # Without optimization, DafnyInt (BigInt) subtraction 5 - 10 must be -5
        self.assertEqual(normal_val, -5)

        # 5. Apply the harness post-processing optimization pass
        postprocess(main_rs)

        # 6. Compile and run the OPTIMIZED Rust binary
        opt_res = subprocess.run(run_cmd, cwd=self.test_project_dir, capture_output=True, text=True)
        self.assertEqual(opt_res.returncode, 0, f"Cargo run with optimization failed: {opt_res.stderr}")
        
        opt_output = opt_res.stdout
        print(f"Optimized stdout: {opt_output.strip()}")

        opt_match = re.search(r"OUTPUT:\s*(\d+)", opt_output)
        self.assertTrue(opt_match, f"Failed to parse optimized output: {opt_output}")
        opt_val = int(opt_match.group(1))

        # Under u64, 5 - 10 will wrap around to 2^64 - 5 (18446744073709551611)
        self.assertEqual(opt_val, 18446744073709551611)
        
        # Assert semantic divergence!
        self.assertNotEqual(normal_val, opt_val)
        print("SUCCESS: Confirmed semantic divergence! Normal: -5, Optimized: 18446744073709551611")

if __name__ == "__main__":
    unittest.main()
