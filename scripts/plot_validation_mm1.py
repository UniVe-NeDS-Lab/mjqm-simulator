#!/usr/bin/env python3
"""
Plot M/M/1 validation: simulated mean response time vs analytical curve.

Left panel:  representative load levels, no error bars.
Right panel: zoomed view at rho=0.7 showing the actual 95% CI at true scale.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from plot_config import BLACK, INDIGO, configure_matplotlib

configure_matplotlib()

# Representative rho values for the overview panel
OVERVIEW_RHOS = {0.1, 0.3, 0.5, 0.7, 0.9}
# rho value to zoom on for the CI panel
ZOOM_RHO = 0.7


def plot_validation(csv_path, output_path):
    df = pd.read_csv(csv_path)

    lambdas = df["arrival.rate"].values
    resp_sim = df["RespTime Total"].values
    resp_var = df["RespTime Variance"].values
    n_reps = 40
    n_events = 5_000_000

    # Between-replicate variance of means: job-level variance / n_events,
    # then CI from n_reps replications.
    se = np.sqrt(resp_var / n_events) / np.sqrt(n_reps)
    ci_half = 1.96 * se

    # Analytical M/M/1: E[R] = 1/(1-rho)  (with tau=1, mu=1)
    rho_curve = np.linspace(0.01, 0.99, 500)
    resp_analytical = 1.0 / (1.0 - rho_curve)

    # Pick representative points for overview
    overview_mask = np.array([
        any(abs(lam - rho) < 0.01 for rho in OVERVIEW_RHOS)
        for lam in lambdas
    ])

    # Find the zoom point
    zoom_idx = np.argmin(np.abs(lambdas - ZOOM_RHO))

    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(14, 6),
        gridspec_kw={"width_ratios": [2, 1], "wspace": 0.3},
    )

    # ── Left panel: overview (no error bars) ──────────────────────────
    ax_left.plot(
        rho_curve, resp_analytical,
        color=INDIGO, linewidth=2.5, linestyle="--",
        label=r"Analytical $\mathbb{E}[R] = \frac{\tau}{1-\rho}$", zorder=2,
    )
    ax_left.scatter(
        lambdas[overview_mask], resp_sim[overview_mask],
        color=BLACK, s=80, zorder=3, label="Simulated",
    )

    ax_left.set_xlabel(r"$\rho = \lambda \tau$")
    ax_left.set_ylabel(r"Mean response time $\mathbb{E}[R]$ [s]")
    ax_left.set_xlim(0, 1)
    ax_left.set_ylim(0, 25)
    ax_left.grid(True, alpha=0.3, linestyle="--", linewidth=1)
    ax_left.legend(fontsize=14, framealpha=0.9)
    ax_left.set_title("Overview", fontsize=18)

    # ── Right panel: zoomed CI at true scale ──────────────────────────
    zoom_rho = lambdas[zoom_idx]
    zoom_resp = resp_sim[zoom_idx]
    zoom_ci = ci_half[zoom_idx]
    zoom_analytical = 1.0 / (1.0 - zoom_rho)

    # Bar for the CI
    ax_right.errorbar(
        zoom_rho, zoom_resp, yerr=zoom_ci,
        fmt="o", color=BLACK, markersize=10, capsize=8,
        linewidth=2, capthick=2, label="Simulated (95\\% CI)", zorder=3,
    )
    # Analytical reference
    ax_right.axhline(
        y=zoom_analytical, color=INDIGO, linestyle="--", linewidth=2,
        label=f"Analytical ({zoom_analytical:.4f})", zorder=2,
    )

    # Tight y-axis to show the CI scale
    margin = max(zoom_ci * 8, 0.005)
    ax_right.set_ylim(zoom_resp - margin, zoom_resp + margin)
    ax_right.set_xlim(zoom_rho - 0.05, zoom_rho + 0.05)
    ax_right.set_xlabel(r"$\rho$")
    ax_right.set_ylabel(r"$\mathbb{E}[R]$ [s]")
    ax_right.grid(True, alpha=0.3, linestyle="--", linewidth=1)
    ax_right.legend(fontsize=12, framealpha=0.9)
    ax_right.set_title(rf"Zoom at $\rho = {zoom_rho:.1f}$", fontsize=18)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved validation plot to {output_path}")
    plt.close()


if __name__ == "__main__":
    csv_path = Path("Results/validation_mm1.csv")
    output_path = Path("../tesi/figures/validation-mm1.pdf")

    if not csv_path.exists():
        print(f"Error: Data file not found at {csv_path}")
        exit(1)

    plot_validation(csv_path, output_path)
