#!/usr/bin/env python3
"""
Generate CV (coefficient of variation) vs arrival rate for all policies.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from plot_config import policy_styles, configure_matplotlib, smooth

configure_matplotlib()


def plot_all_cv(csv_path, output_path, do_smooth=True):
    df = pd.read_csv(csv_path)

    fig, ax = plt.subplots(figsize=(14, 9))

    for label in policy_styles:
        group = df[df["label"] == label].sort_values("arrival.rate")
        if group.empty:
            continue
        style = policy_styles[label]

        x = group["arrival.rate"].values
        y = group["WaitTime CV"].values

        y_plot = smooth(y, window=3) if do_smooth else y

        # Find lambda* for this policy
        knee_idx = group["Power"].idxmax()
        ls_val = group.loc[knee_idx, "arrival.rate"]

        # Split into stable (before lambda*) and unstable (after)
        mask_stable = x <= ls_val
        mask_unstable = x >= ls_val

        ax.plot(x[mask_stable], y_plot[mask_stable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2.5,
                label=label)
        ax.plot(x[mask_unstable], y_plot[mask_unstable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=2.5,
                alpha=0.25)
        # Scatter only the lambda* point
        ax.scatter(ls_val,
                   group.loc[knee_idx, "WaitTime CV"],
                   color=style["color"],
                   marker=style["marker"],
                   s=120, alpha=0.9,
                   edgecolors="black", linewidths=1,
                   zorder=5)

    ax.set_xlabel("Arrival Rate [s$^{-1}$]", fontsize=21)
    ax.set_ylabel("Coefficient of Variation of $W$", fontsize=21)
    ax.grid(True, which="both", alpha=0.3, linestyle="--", linewidth=1)
    ax.legend(loc="best", fontsize=11, framealpha=0.9, ncol=2)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved all-policies CV plot to {output_path}")
    plt.close()


if __name__ == "__main__":
    csv_path = Path("Results/cellA.csv")
    output_path = Path("../tesi/figures/all-cv-comparison.pdf")

    if not csv_path.exists():
        print(f"Error: Data file not found at {csv_path}")
        exit(1)

    plot_all_cv(csv_path, output_path)
