#!/usr/bin/env python3
"""
Generate response time plot near stability boundaries showing system behaviour
as policies approach their maximum sustainable load.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from plot_config import CYAN, policy_styles, configure_matplotlib

CYAN_DARK = "#4A90A8"

# Policies whose near-zero waiting times at low relative load create
# misleading vertical drops on the log scale.
HIDE_INITIAL = {"Most Server First"}

configure_matplotlib()


def plot_stability_boundary(csv_path, output_path):
    """
    Plot response time near stability boundaries.
    Normalises arrival rate by each policy's stability boundary to show
    comparative behaviour near the critical transition.
    """
    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(12, 8))

    for label, group in df.groupby("label"):
        if label not in policy_styles:
            continue

        style = policy_styles[label]

        # Find stability boundary (knee)
        knee_idx = group["Power"].idxmax()
        knee_lambda = group.loc[knee_idx, "arrival.rate"]

        # Normalise arrival rate by stability boundary
        x_data = group["arrival.rate"].values / knee_lambda
        y_data = group["WaitTime Total"].values

        # Focus on approach to stability boundary, with small margin past it
        x_lo = 0.55 if label in HIDE_INITIAL else 0.4
        mask = (x_data >= x_lo) & (x_data <= 1.1)
        x_plot = x_data[mask]
        y_plot = y_data[mask]

        # Sort
        sort_idx = np.argsort(x_plot)
        x_plot = x_plot[sort_idx]
        y_plot = y_plot[sort_idx]

        # Split into stable (before boundary) and unstable (after)
        mask_stable = x_plot <= 1.0
        mask_unstable = x_plot >= 1.0

        ax.plot(x_plot[mask_stable], y_plot[mask_stable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=3,
                label=label)
        ax.plot(x_plot[mask_unstable], y_plot[mask_unstable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=3,
                alpha=0.25)


    # Mark the stability boundary at normalised lambda = 1.0
    ax.axvline(x=1.0, color=CYAN_DARK, linestyle="--", linewidth=3,
               label="Stability Boundary", alpha=0.8)

    # Configure axes
    ax.set_xlabel(r"$\lambda / \lambda^*$", fontsize=21)
    ax.set_ylabel("Waiting Time [s]", fontsize=21)
    ax.set_yscale("log")
    ax.grid(True, which="both", alpha=0.3, linestyle="--", linewidth=1)
    ax.legend(loc="upper left", fontsize=14, framealpha=0.9, ncol=2)

    ax.axvspan(0.4, 1.0, alpha=0.08, color=CYAN)

    plt.tight_layout()

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved stability boundary plot to {output_path}")
    plt.close()


if __name__ == "__main__":
    csv_path = Path("Results/cellA.csv")
    output_path = Path("../tesi/figures/waiting-time-stability.pdf")

    if not csv_path.exists():
        print(f"Error: Data file not found at {csv_path}")
        print("Run load_experiment_data.py first to generate the cleaned CSV.")
        exit(1)

    plot_stability_boundary(csv_path, output_path)
