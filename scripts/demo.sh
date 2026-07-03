#!/usr/bin/env bash
# Interactive demo: clear cache → seed hardcoded RunQuery → DuckDB CLI with demo UI on.
# Production code unchanged except reading HILLCLIMBING_DEMO from the environment.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

QUERY_ID="${DEMO_QUERY_ID:-3}"

echo "==> Clearing hillclimbing cache (all optimized queries)..."
uv run python "$ROOT/scripts/demo_lib.py" clear

echo "==> Seeding hardcoded demo RunQuery body for Q${QUERY_ID}..."
uv run python "$ROOT/scripts/demo_lib.py" seed "$QUERY_ID"

SQL_ONELINE="$(uv run python -c "
import sys; sys.path.insert(0, '$ROOT')
from scripts.demo_lib import sql_one_line
print(sql_one_line($QUERY_ID))
")"

export HILLCLIMBING_DEMO=1
export MOCK_AGENT=1
export USE_AGENT_DOCKER=0
export MAX_ITERATIONS=1
export HILLCLIMBING_VERBOSE=0
export HILLCLIMBING_LOG_LEVEL=WARN

if [ ! -f "$ROOT/build/hillclimbing.duckdb_extension" ]; then
  echo "==> Building extension (first time)..."
  make extension
fi
uv run python -m db_extension.prepare_data

cat <<EOF

╔══════════════════════════════════════════════════════════════════════╗
║  Hillclimbing demo (Q${QUERY_ID}) — commands for the DuckDB shell below   ║
╚══════════════════════════════════════════════════════════════════════╝

  DuckDB's built-in timer is already on (.timer on in init.sql).
  After a plain SELECT, look for "Run Time (s): real ..." below the result.

  (1) Vanilla DuckDB:

    ${SQL_ONELINE}

  (2) Hillclimbing — must be quoted as one string. Demo steps + revenue print
      on stdout; ignore any empty 1-row table DuckDB shows as the SELECT result:

    SELECT hillclimbing('${SQL_ONELINE}');

  (3) Run (2) again → cached optimized binary (💾 path in demo UI).

  Tip: paste carefully — the prompt is "hillclimbing>" but your SQL must still
  start with SELECT. Do not merge the prompt text into the query.

  Our 🦆 DuckDB timing line only appears if HILLCLIMBING_DEMO_DUCKDB=1 (off by
  default). Use .timer on for the vanilla baseline instead.

Press Enter to open DuckDB CLI...
EOF
read -r _

exec "$ROOT/run_duckdb_and_load_extension_and_sbb_dataset.sh"
