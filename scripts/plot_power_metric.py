#!/usr/bin/env python3
"""
Generate Kleinrock's Power Metric plot showing the characteristic "knee" for stability detection.
"""

import argparse
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from plot_config import policy_styles, EXEMPLAR_POLICIES, configure_matplotlib

configure_matplotlib()


def plot_power_metric(csv_path, output_path, exemplars_only=False):
    """
    Plot Kleinrock's Power Metric (Throughput / Response Time) vs arrival rate.
    Highlights the "knee" which indicates the stability boundary.
    """
    df = pd.read_csv(csv_path)
    allowed = set(EXEMPLAR_POLICIES) if exemplars_only else set(policy_styles)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot policies
    for label, group in df.groupby("label"):
        if label not in policy_styles or label not in allowed:
            continue

        style = policy_styles[label]

        x_data = group["arrival.rate"].values
        power_data = group["Power"].values
        stable = group["stable"].values

        # Sort by arrival rate
        sort_idx = np.argsort(x_data)
        x_data = x_data[sort_idx]
        power_data = power_data[sort_idx]
        stable = stable[sort_idx]

        # Mark the knee (maximum power = lambda*)
        knee_idx = np.argmax(power_data)

        # Split into stable and unstable regions around lambda*
        mask_stable = np.arange(len(x_data)) <= knee_idx
        mask_unstable = np.arange(len(x_data)) >= knee_idx

        ax.plot(x_data[mask_stable], power_data[mask_stable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=3,
                label=label)
        ax.plot(x_data[mask_unstable], power_data[mask_unstable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=3,
                alpha=0.25)
        ax.scatter(x_data[knee_idx], power_data[knee_idx],
                   color=style["color"],
                   marker="*",
                   s=450,
                   edgecolors="black",
                   linewidths=2.25,
                   zorder=5)

        # Add vertical line at knee
        ax.axvline(x=x_data[knee_idx],
                   color=style["color"],
                   linestyle="--",
                   linewidth=2,
                   alpha=0.6)

    # Configure axes
    ax.set_xlabel("Arrival Rate [s$^{-1}$]", fontsize=21)
    ax.set_ylabel("Power Metric [s$^{-2}$]", fontsize=21)
    ax.grid(True, alpha=0.3, linestyle="--", linewidth=1)
    ax.legend(loc="upper left", fontsize=14, framealpha=0.9, ncol=2)

    plt.tight_layout()

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved power metric plot to {output_path}")
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Kleinrock's power metric.")
    parser.add_argument("--exemplars", action="store_true",
                        help="Plot only one representative per policy family")
    args = parser.parse_args()

    csv_path = Path("Results/cellA.csv")
    output_path = Path("../tesi/figures/power-metric-comparison.pdf")

    if not csv_path.exists():
        print(f"Error: Data file not found at {csv_path}")
        print("Run load_experiment_data.py first to generate the cleaned CSV.")
        exit(1)

    plot_power_metric(csv_path, output_path, exemplars_only=args.exemplars)
