# Scripts

Plotting, data-processing, and utility scripts for the MJQM simulator.
All scripts run with `uv run` from the project root directory.

## Prerequisites

- **Python**: managed by `uv`; dependencies declared in `pyproject.toml`. Run `uv sync` once to set up.
- **LaTeX**: a TeX distribution (e.g., TeX Live) is needed for matplotlib's `usetex=True`.
- **Experiment data**: plotting scripts read from `Results/<experiment>.csv`. If the file is missing, generate it with:

```bash
uv run scripts/load_experiment_data.py <experiment>
```

This processes the raw per-policy CSVs in `Results/<experiment>/`, cleans column names, computes derived metrics (stability, power, throughput), and writes a unified CSV.

## Plot styles

All figures share a single style defined in `plot_config.py`:

- **Palette**: colourblind-safe colours from Paul Tol's muted/vibrant schemes.
- **Per-policy encoding**: each policy has a unique combination of colour, marker, and line style (`policy_styles` dict) for triple-redundant encoding.
- **Font and sizes**: `configure_matplotlib(font_size=21)` sets Palatino serif with LaTeX rendering.
- **Smoothing**: `smooth(y)` applies Savitzky-Golay filtering in log-space, used by most data-driven plots.

To change the global look, edit `plot_config.py`. Individual scripts import from it rather than defining their own styles.

## Utility scripts

| Script | What it does |
|---|---|
| `convert_conf.py` | Converts legacy configuration files to TOML format |
| `ensure_same_results.py` | Validates that two result sets produce identical output (regression testing) |
| `plotly_app.py` | Interactive Dash/Plotly web app for exploring experiment results |
| `plot_experiment.py` | General-purpose experiment plotter (used by `plotly_app.py`) |
| `select-g++.sh` | Selects the correct g++ compiler on macOS |
