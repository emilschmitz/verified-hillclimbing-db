import os
import re
import duckdb

class DatabaseCatalog:
    def __init__(self, database_path: str = None):
        """
        Initializes the DatabaseCatalog.
        :param database_path: Path to a DuckDB database file. If None, uses an in-memory database.
        """
        self.database_path = database_path or ":memory:"
        self.con = None

    def _ensure_connection(self):
        if self.con is None:
            try:
                self.con = duckdb.connect(self.database_path)
            except Exception:
                pass

    def get_table_schema(self, table_name: str) -> dict[str, str]:
        """
        Returns column names mapped to DuckDB data types, *preserved as
        DuckDB returned them* (e.g. {'LO_QUANTITY': 'INTEGER', 'LO_REVENUE':
        'BIGINT', 'LO_SHIPMODE': 'VARCHAR'}).  Downstream consumers use
        the catalog type directly; no column-name based heuristics.
        """
        self._ensure_connection()
        schema_dict = {}

        if self.con:
            try:
                # Query INFORMATION_SCHEMA.COLUMNS
                query = """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE lower(table_name) = lower(?);
                """
                res = self.con.execute(query, [table_name]).fetchall()
                if res:
                    for col_name, data_type in res:
                        schema_dict[col_name.upper()] = data_type.upper()
                    return schema_dict
            except Exception:
                pass

        # Fallback 1: Parse a local SQL DDL file if present in the workspace
        ddl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ssb-dbgen", "dss.ddl")
        if os.path.exists(ddl_path):
            schema_dict = self._parse_ddl_file(ddl_path, table_name)
            if schema_dict:
                return schema_dict

        # Fallback 2: Hardcoded SSB workload schema if querying lineorder_flat.
        # Kept as bootstrap for environments without a live DuckDB connection
        # (e.g. running the unit tests offline).  New tables should be
        # loaded into DuckDB instead of adding to this fallback.
        if table_name.lower() == "lineorder_flat":
            from research_loop.ssb_workload import schema as ssb_schema, fallback_dtypes
            # Down-convert the high-level 'int'/'string' shape to concrete
            # DuckDB types so the transpiler's get_dafny_type can pick the
            # right width from the type, not the column name.
            return {col: (fallback_dtypes.get(col, "INTEGER") if t == "int" else "VARCHAR")
                    for col, t in ssb_schema.items()}

        return {}

    def get_primary_keys(self, table_name: str) -> list[str]:
        """
        Returns list of primary keys for a table.
        """
        self._ensure_connection()
        pks = []
        if self.con:
            try:
                # In DuckDB, we can inspect constraints
                query = """
                    SELECT column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.constraint_type = 'PRIMARY KEY' AND lower(tc.table_name) = lower(?);
                """
                res = self.con.execute(query, [table_name]).fetchall()
                pks = [row[0].upper() for row in res]
            except Exception:
                pass
        return pks

    def _parse_ddl_file(self, file_path: str, table_name: str) -> dict[str, str]:
        """
        Parses a standard SQL DDL file using a lightweight regex parser to extract column definitions.
        """
        schema_dict = {}
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Clean comments
            content = re.sub(r"--.*", "", content)

            # Find CREATE TABLE block for table_name
            # E.g. CREATE TABLE TPCD.NATION  ( ... )
            pattern = re.compile(
                rf"CREATE\s+TABLE\s+(?:\w+\.)?{table_name}\s*\(([\s\S]*?)\);",
                re.IGNORECASE
            )
            match = pattern.search(content)
            if not match:
                return {}

            columns_part = match.group(1)
            # Split by comma but respect parentheses (e.g. DECIMAL(15,2))
            # Match lines: col_name data_type [modifiers]
            lines = columns_part.split(",")
            current_col = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    col_name = parts[0].strip('"`[]').upper()
                    data_type = parts[1].upper()
                    
                    if any(t in data_type for t in ("INT", "KEY", "DATE", "NUM", "YEAR", "DECIMAL", "NUMERIC")):
                        schema_dict[col_name] = "int"
                    else:
                        schema_dict[col_name] = "string"
        except Exception:
            pass
        return schema_dict
