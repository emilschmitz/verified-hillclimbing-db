import os
import re
import sys
import json
import time
import subprocess
import hashlib
import shutil
import duckdb
import pandas as pd

# Try importing readline for command history and completion
try:
    import readline
except ImportError:
    readline = None

from db_extension.catalog import DatabaseCatalog
from db_extension.optimizer import run_optimization_loop, match_query_index

# ANSI Color Codes
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.json")
BIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")

def get_sql_hash(sql: str) -> str:
    # Normalize SQL for hashing
    norm = re.sub(r"\s+", " ", sql).strip().lower()
    return hashlib.md5(norm.encode("utf-8")).hexdigest()

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cache(cache: dict):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

def generate_synthetic_data(dataset_size=50000) -> pd.DataFrame:
    # Generate cyclic columns just like benchmark_duckdb.py
    columns = {
        "LO_ORDERKEY": [1 + (i % 100) for i in range(dataset_size)],
        "LO_LINENUMBER": [1 + (i % 100) for i in range(dataset_size)],
        "LO_CUSTKEY": [1 + (i % 100) for i in range(dataset_size)],
        "LO_PARTKEY": [1 + (i % 100) for i in range(dataset_size)],
        "LO_SUPPKEY": [1 + (i % 100) for i in range(dataset_size)],
        "LO_ORDERDATE": [19930101 + (i % 365) for i in range(dataset_size)],
        "LO_ORDERPRIORITY": ["1-URGENT" if (i % 2 == 0) else "2-HIGH" for i in range(dataset_size)],
        "LO_SHIPPRIORITY": [1 + (i % 100) for i in range(dataset_size)],
        "LO_QUANTITY": [i % 50 for i in range(dataset_size)],
        "LO_EXTENDEDPRICE": [1000 + (i % 1000) for i in range(dataset_size)],
        "LO_ORDTOTALPRICE": [1000 + (i % 1000) for i in range(dataset_size)],
        "LO_DISCOUNT": [i % 10 for i in range(dataset_size)],
        "LO_REVENUE": [1000 + (i % 1000) for i in range(dataset_size)],
        "LO_SUPPLYCOST": [1000 + (i % 1000) for i in range(dataset_size)],
        "LO_TAX": [1 + (i % 100) for i in range(dataset_size)],
        "LO_COMMITDATE": [1 + (i % 100) for i in range(dataset_size)],
        "LO_SHIPMODE": ["dummy"] * dataset_size,
        "C_NAME": ["dummy"] * dataset_size,
        "C_ADDRESS": ["dummy"] * dataset_size,
        "C_CITY": ["UNITED KI1" if (i % 2 == 0) else "UNITED KI2" for i in range(dataset_size)],
        "C_NATION": ["UNITED STATES" if (i % 5 == 0) else "UNITED KINGDOM" for i in range(dataset_size)],
        "C_REGION": ["AMERICA" if (i % 2 == 0) else "ASIA" for i in range(dataset_size)],
        "C_PHONE": ["dummy"] * dataset_size,
        "C_MKTSEGMENT": ["dummy"] * dataset_size,
        "S_NAME": ["dummy"] * dataset_size,
        "S_ADDRESS": ["dummy"] * dataset_size,
        "S_CITY": ["UNITED KI5" if (i % 2 == 0) else "UNITED KI6" for i in range(dataset_size)],
        "S_NATION": ["UNITED STATES" if (i % 5 == 0) else "UNITED KINGDOM" for i in range(dataset_size)],
        "S_REGION": ["AMERICA" if (i % 2 == 0) else "ASIA" for i in range(dataset_size)],
        "S_PHONE": ["dummy"] * dataset_size,
        "P_NAME": ["dummy"] * dataset_size,
        "P_MFGR": ["dummy"] * dataset_size,
        "P_CATEGORY": ["MFGR#12" if (i % 3 == 0) else "MFGR#14" for i in range(dataset_size)],
        "P_BRAND": ["MFGR#2221" if (i % 4 == 0) else "MFGR#2222" for i in range(dataset_size)],
        "P_COLOR": ["dummy"] * dataset_size,
        "P_TYPE": ["dummy"] * dataset_size,
        "P_SIZE": [1 + (i % 100) for i in range(dataset_size)],
        "P_CONTAINER": ["dummy"] * dataset_size,
        "D_YEAR": [1992 + (i % 7) for i in range(dataset_size)],
        "D_YEARMONTHNUM": [1 + (i % 100) for i in range(dataset_size)],
        "D_WEEKNUMINYEAR": [1 + (i % 52) for i in range(dataset_size)]
    }
    return pd.DataFrame(columns)

def print_result_table(df: pd.DataFrame):
    if df.empty:
        print("Empty result (0 rows)")
        return
    # Use pandas to format as string
    print(df.to_string(index=False))

def setup_db(con: duckdb.DuckDBPyConnection):
    # Check if we can load the lineorder_flat table
    tbl_path = "/home/emil/projects/verified-hillclimbing-db/ssb-dbgen/lineorder_flat.tbl"
    if os.path.exists(tbl_path):
        print(f"Loading table 'lineorder_flat' from {tbl_path}...")
        try:
            con.execute(f"CREATE TABLE lineorder_flat AS SELECT * FROM read_csv('{tbl_path}', delim='|', header=True) LIMIT 50000")
            print(f"{COLOR_GREEN}Loaded 50,000 rows into 'lineorder_flat'.{COLOR_RESET}")
            return
        except Exception as e:
            print(f"{COLOR_YELLOW}Warning: Failed to load from CSV ({e}). Generating synthetic data...{COLOR_RESET}")
    else:
        print(f"{COLOR_YELLOW}Warning: ssb-dbgen/lineorder_flat.tbl not found. Generating synthetic data...{COLOR_RESET}")
    
    # Generate and load synthetic data
    df = generate_synthetic_data(50000)
    con.register("df_synth", df)
    con.execute("CREATE TABLE lineorder_flat AS SELECT * FROM df_synth")
    print(f"{COLOR_GREEN}Generated and loaded 50,000 synthetic rows into 'lineorder_flat'.{COLOR_RESET}")

def main():
    print(f"{COLOR_CYAN}===================================================={COLOR_RESET}")
    print(f"{COLOR_CYAN}  DuckDB Shell with Hillclimbing Optimizer Extension{COLOR_RESET}")
    print(f"{COLOR_CYAN}===================================================={COLOR_RESET}")

    # Read CLI args for custom DB file
    db_file = ":memory:"
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        db_file = sys.argv[1]
        print(f"Connecting to database file: {db_file}")

    con = duckdb.connect(db_file, config={'allow_unsigned_extensions': 'true'})
    setup_db(con)

    hillclimbing_loaded = False
    
    # Simple readline tab completion setup
    if readline:
        readline.parse_and_bind("tab: complete")
        # Add basic completions
        keywords = ["select", "from", "where", "group by", "load", "hillclimbing", ".tables", ".schema", ".exit"]
        def completer(text, state):
            options = [k for k in keywords if k.startswith(text.lower())]
            if state < len(options):
                return options[state]
            else:
                return None
        readline.set_completer(completer)

    # Main REPL Loop
    while True:
        try:
            prompt = f"{COLOR_GREEN}hillclimbing>{COLOR_RESET} " if hillclimbing_loaded else "duckdb> "
            sql = input(prompt).strip()
            if not sql:
                continue

            # Handle dot commands
            if sql.startswith("."):
                cmd = sql.split()
                if cmd[0] in (".exit", ".quit"):
                    break
                elif cmd[0] == ".help":
                    print("Available commands:")
                    print("  .tables              List tables")
                    print("  .schema <tbl>        Show table schema")
                    print("  .load hillclimbing   Load optimization extension")
                    print("  .exit / .quit        Exit")
                    continue
                elif cmd[0] == ".tables":
                    print(con.execute("PRAGMA show_tables").fetchall())
                    continue
                elif cmd[0] == ".schema":
                    if len(cmd) > 1:
                        print(con.execute(f"PRAGMA show('{cmd[1]}')").fetchall())
                    else:
                        print("Usage: .schema <table_name>")
                    continue
                elif cmd[0] == ".load" and len(cmd) > 1 and cmd[1].lower() == "hillclimbing":
                    try:
                        ext_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hillclimbing.duckdb_extension")
                        con.execute(f"LOAD '{ext_path}';")
                        hillclimbing_loaded = True
                        print(f'{COLOR_GREEN}Extension "hillclimbing" loaded successfully.{COLOR_RESET}')
                    except Exception as e:
                        print(f"{COLOR_RED}Error loading extension: {e}{COLOR_RESET}")
                    continue
                else:
                    print(f"Unknown command: {cmd[0]}")
                    continue

            # Handle standard SQL LOAD extension statement
            load_match = re.match(r"load\s+['\"]?hillclimbing['\"]?;?", sql, re.IGNORECASE)
            if load_match:
                try:
                    ext_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hillclimbing.duckdb_extension")
                    con.execute(f"LOAD '{ext_path}';")
                    hillclimbing_loaded = True
                    print(f'{COLOR_GREEN}Extension "hillclimbing" loaded successfully.{COLOR_RESET}')
                except Exception as e:
                    print(f"{COLOR_RED}Error loading extension: {e}{COLOR_RESET}")
                continue

            # Check if this is an SSB query that we should optimize
            is_ssb_query = "lineorder_flat" in sql.lower() and sql.strip().lower().startswith("select")

            if hillclimbing_loaded and is_ssb_query:
                # RUN OPTIMIZATION VIA THE COMPILED DUCKDB C++ EXTENSION UDF
                try:
                    escaped_sql = sql.replace("'", "''")
                    con.execute(f"SELECT hillclimbing_optimize('{escaped_sql}')")
                except Exception as e:
                    print(f"{COLOR_RED}Error running extension UDF: {e}{COLOR_RESET}")
            else:
                # Run query normally on DuckDB
                t_start = time.perf_counter()
                try:
                    df_res = con.execute(sql).df()
                    print_result_table(df_res)
                    elapsed_us = int((time.perf_counter() - t_start) * 1_000_000)
                    print(f"Executed in {elapsed_us} us (DuckDB baseline)")
                except Exception as e:
                    print(f"{COLOR_RED}Error: {e}{COLOR_RESET}")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"{COLOR_RED}Internal CLI Error: {e}{COLOR_RESET}")

if __name__ == "__main__":
    main()
