#!/usr/bin/env python3
"""
Generate CV (coefficient of variation) vs arrival rate for Quick Swap variants.

Compares l=1 and l=2048 to show how threshold affects fairness under load.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from plot_config import policy_styles, configure_matplotlib, smooth

configure_matplotlib()

QS_POLICIES = ["Quick Swap (l = 1)", "Quick Swap (l = 2048)"]


def plot_qs_cv(csv_path, output_path, do_smooth=True):
    """
    Plot WaitTime CV vs arrival rate for Quick Swap l=1 and l=2048.
    """
    df = pd.read_csv(csv_path)

    # Compute lambda* for each QS variant
    lambda_stars = {}
    for label, group in df.groupby("label"):
        if label in QS_POLICIES:
            knee_idx = group["Power"].idxmax()
            lambda_stars[label] = group.loc[knee_idx, "arrival.rate"]

    fig, ax = plt.subplots(figsize=(12, 8))

    for label in QS_POLICIES:
        group = df[df["label"] == label].sort_values("arrival.rate")
        style = policy_styles[label]

        x = group["arrival.rate"].values
        y = group["WaitTime CV"].values
        ls_val = lambda_stars.get(label)

        y_plot = smooth(y, window=3) if do_smooth else y

        # Split into stable and unstable regions
        mask_stable = x <= ls_val
        mask_unstable = x >= ls_val

        ax.plot(x[mask_stable], y_plot[mask_stable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=3,
                label=label)
        ax.plot(x[mask_unstable], y_plot[mask_unstable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=3,
                alpha=0.25)
        ax.scatter(x[mask_stable], y[mask_stable],
                   color=style["color"],
                   marker=style["marker"],
                   s=60, alpha=0.6,
                   edgecolors="black", linewidths=0.75)
        ax.scatter(x[mask_unstable], y[mask_unstable],
                   color=style["color"],
                   marker=style["marker"],
                   s=60, alpha=0.15,
                   edgecolors="black", linewidths=0.75)

    # Vertical lines at lambda*
    for label, ls_val in lambda_stars.items():
        color = policy_styles[label]["color"]
        ax.axvline(x=ls_val, color=color, linestyle="--", linewidth=2, alpha=0.6)

    ax.set_xlabel("Arrival Rate [s$^{-1}$]", fontsize=21)
    ax.set_ylabel("Coefficient of Variation of $W$", fontsize=21)
    ax.grid(True, which="both", alpha=0.3, linestyle="--", linewidth=1)
    ax.legend(loc="best", fontsize=14, framealpha=0.9)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved Quick Swap CV plot to {output_path}")
    plt.close()


if __name__ == "__main__":
    csv_path = Path("Results/cellA.csv")
    output_path = Path("../tesi/figures/qs-cv-comparison.pdf")

    if not csv_path.exists():
        print(f"Error: Data file not found at {csv_path}")
        print("Run load_experiment_data.py first to generate the cleaned CSV.")
        exit(1)

    plot_qs_cv(csv_path, output_path)
