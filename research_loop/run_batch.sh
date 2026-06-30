#!/bin/bash
set -e
echo "=== Starting Batch Query Optimization Experiments (Q1-Q5) ==="
for q in 1 2 3 4 5
do
    echo "=========================================="
    echo "Running Query $q..."
    echo "=========================================="
    uv run python research_loop/run_experiments.py -q $q -d 50000 -n 1
done
echo "=== Batch Experiments Completed! ==="
