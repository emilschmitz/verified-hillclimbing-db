# Hillclimbing interactive demo

## One command

```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

This script **only** (production stays default):

1. Clears **all** cached optimized queries (`cache.json`, `db_extension/bin/q_*`, `build/queries/q_*`)
2. Writes a **hardcoded** columnar RunQuery body for Q3 (override: `DEMO_QUERY_ID=5 ./scripts/demo.sh`)
3. Sets `HILLCLIMBING_DEMO=1`, `MOCK_AGENT=1`, `MAX_ITERATIONS=1`
4. Drops you into the **official DuckDB CLI** (downloaded to `build/duckdb` on first run — vendored binary, not built from source)

Prints the exact SQL to paste. **DuckDB timing** is DuckDB's own `.timer on` — we don't change that.

## In the DuckDB shell

```sql
.timer on

-- (1) Vanilla (DuckDB prints its own timing after the result)
SELECT SUM(...) FROM lineorder_flat WHERE ...;

-- (2) Hillclimbing (demo steps on stdout, then result)
SELECT hillclimbing('SELECT SUM(...) FROM lineorder_flat WHERE ...');

-- (3) Run (2) again → cached 💾 path
```

## Env toggles (set by demo.sh)

| Variable | Demo value | Purpose |
|----------|------------|---------|
| `HILLCLIMBING_DEMO=1` | on | Step emojis + durations on stdout |
| `MOCK_AGENT=1` | on | Skip LLM; use pre-seeded body |
| `HILLCLIMBING_LOG_LEVEL=WARN` | quiet stderr | Debug logs still on stderr if raised |

Production `config.env` keeps demo **off**.

## Re-run fresh pipeline

Run `./scripts/demo.sh` again — it clears cache every time.
