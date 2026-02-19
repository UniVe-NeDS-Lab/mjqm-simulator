# Scripts

Plotting, data-processing, and utility scripts for the SMASH simulator project.
All scripts run with `uv run` from the `smash/` root directory.

## Prerequisites

- **Python**: managed by `uv`; dependencies declared in `pyproject.toml`. Run `uv sync` once to set up.
- **LaTeX**: a TeX distribution (e.g., TeX Live) is needed for matplotlib's `usetex=True`.
- **Experiment data**: most plotting scripts read `Results/cellA.csv`. If the file is missing, generate it with:

```bash
uv run scripts/load_experiment_data.py cellA
```

This processes the raw per-policy CSVs in `Results/cellA/`, cleans column names, computes derived metrics (stability, power, throughput), and writes the unified CSV.

## Generating thesis figures

### All at once

```bash
./scripts/generate_all_thesis_plots.sh
```

Runs steps 1--9 listed below in order, creating all PDFs in `../tesi/figures/`.
If `Results/cellA.csv` is missing, the shell script calls `load_experiment_data.py` automatically before starting.

### One at a time

Each script can be run individually. For example:

```bash
uv run scripts/plot_power_metric.py
```

The table below lists every script called by the automated pipeline, in execution order.

| # | Script | Output (`../tesi/figures/`) | What it shows |
|---|---|---|---|
| 1 | `plot_workload_distribution.py` | `workload-distribution.pdf` | Job class distribution (probabilities and service times) from `Inputs/cellA.toml` |
| 2 | `plot_power_metric.py` | `power-metric-comparison.pdf` | Kleinrock's power metric vs arrival rate; highlights the knee at stability boundaries |
| 3 | `plot_stability_boundary.py` | `response-time-stability.pdf` | Response time near stability boundaries, normalised by each policy's stability limit |
| 4 | `plot_per_class_waiting.py` | `per-class-waiting-times.pdf` | Per-class waiting times at a fixed arrival rate (default lambda=404); fairness comparison |
| 5 | `plot_per_class_throughput.py` | `per-class-throughput.pdf`, `per-class-throughput-80pct.pdf` | Per-class throughput at each policy's lambda* and at 80% of lambda* |
| 6 | `plot_fifo_violations.py` | `fifo-violations.pdf` | FIFO violation count vs arrival rate for SMASH variants (w=2, 5, 10) |
| 7 | `plot_welch_method.py` | `welch-method-example.pdf` | Synthetic illustration of Welch's method for transient removal |
| 8 | `plot_qs_cv.py` | `qs-cv-comparison.pdf` | Waiting-time CV vs arrival rate for Quick Swap l=1 and l=2048 |
| 9 | `plot_policy_scenarios.py` | `policy-fifo-scenario.pdf`, `policy-smash-w2-scenario.pdf`, `policy-smash-w5-scenario.pdf`, `policy-serverfilling-scenario.pdf`, `policy-backfilling-scenario.pdf`, `policy-msf-scenario.pdf` | Diagrams of how each policy allocates jobs to servers in a unified example |

### Scripts outside the pipeline

These produce thesis-related figures but are not called by `generate_all_thesis_plots.sh`.

| Script | Output | Notes |
|---|---|---|
| `plot_waiting_time_comparison.py` | `waiting-time-comparison.pdf` | Obsolete; kept for reference. Log-log waiting-time comparison across all policies. |
| `plot_all_cv.py` | `all-cv-comparison.pdf` | CV vs arrival rate for all 11 policies. |

## Generating LaTeX tables

```bash
uv run scripts/generate_cv_table.py                     # default: Results/cellA.csv
uv run scripts/generate_cv_table.py path/to/cellA.csv   # explicit path
```

`generate_cv_table.py` prints two sets of LaTeX table rows to stdout:

- **Table A** — all policies at the highest common stable lambda (the largest arrival rate where every policy is still stable).
- **Table B** — each policy at its own maximum stable lambda (lambda\*).

Columns: policy, mean waiting time, CV (per-class), min and max per-class waiting time (with class label).

## Customisation

### Plot styles

All thesis figures share a single style defined in `plot_config.py`:

- **Palette**: colourblind-safe colours from Paul Tol's muted/vibrant schemes.
- **Per-policy encoding**: each policy has a unique combination of colour, marker, and line style (`policy_styles` dict) for triple-redundant encoding.
- **Font and sizes**: `configure_matplotlib(font_size=21)` sets Palatino serif with LaTeX rendering.
- **Smoothing**: `smooth(y)` applies Savitzky-Golay filtering in log-space, used by most data-driven plots.

To change the global look, edit `plot_config.py`. Individual scripts import from it rather than defining their own styles (except `plot_policy_scenarios.py`, which uses its own colour map for job-size encoding).

### Arrival rate for per-class plots

`plot_per_class_waiting.py` fixes a single arrival rate for the snapshot. Change `target_lambda` in the `__main__` block:

```python
plot_per_class_waiting(csv_path, output_path, target_lambda=404)
```

### Policy selection

Several scripts filter to a subset of policies via a list variable near the top of the file. Edit as needed:

- `plot_fifo_violations.py` — `SMASH_POLICIES`
- `plot_qs_cv.py` — `QS_POLICIES`

Comparison plots that show all 11 policies iterate over `policy_styles` from `plot_config.py`; adding or removing entries there affects every such plot.

## Utility scripts

Not thesis-specific, but part of the simulator workflow.

| Script | What it does |
|---|---|
| `convert_conf.py` | Converts legacy configuration files to TOML format |
| `ensure_same_results.py` | Validates that two result sets produce identical output (regression testing) |
| `plotly_app.py` | Interactive Dash/Plotly web app for exploring experiment results |
| `plot_experiment.py` | General-purpose experiment plotter (used by `plotly_app.py`) |
| `select-g++.sh` | Selects the correct g++ compiler on macOS |
