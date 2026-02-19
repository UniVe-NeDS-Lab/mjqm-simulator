#!/usr/bin/env bash
#
# Generate all thesis plots from experimental data.
# Run this script from the smash/ directory after experiments are complete.
#

set -e  # Exit on error

echo "==================================================================="
echo "Generating all thesis figures from experimental data"
echo "==================================================================="

# Ensure we're in the smash directory
if [ ! -f "simulator_toml" ]; then
    echo "Error: Must run from smash/ directory"
    exit 1
fi

# Check if Results/cellA.csv exists
if [ ! -f "Results/cellA.csv" ]; then
    echo "Warning: Results/cellA.csv not found."
    echo "Running data loader to generate cleaned CSV..."
    uv run scripts/load_experiment_data.py cellA
fi

echo ""
echo "Step 1/9: Workload distribution..."
uv run scripts/plot_workload_distribution.py

echo ""
echo "Step 2/9: Kleinrock's power metric..."
uv run scripts/plot_power_metric.py

echo ""
echo "Step 3/9: Waiting time near stability boundaries..."
uv run scripts/plot_stability_boundary.py

echo ""
echo "Step 4/9: Per-class waiting times..."
uv run scripts/plot_per_class_waiting.py

echo ""
echo "Step 5/9: Per-class throughput..."
uv run scripts/plot_per_class_throughput.py

echo ""
echo "Step 6/9: FIFO violations..."
uv run scripts/plot_fifo_violations.py

echo ""
echo "Step 7/9: Welch's method illustration..."
uv run scripts/plot_welch_method.py

echo ""
echo "Step 8/9: Quick Swap CV comparison..."
uv run scripts/plot_qs_cv.py

echo ""
echo "Step 9/9: Policy behavior scenarios..."
uv run scripts/plot_policy_scenarios.py

echo ""
echo "==================================================================="
echo "All thesis figures generated successfully!"
echo "Figures saved to: ../tesi/figures/"
echo "==================================================================="
echo ""
echo "You can now rebuild your thesis with: make -C ../tesi"
