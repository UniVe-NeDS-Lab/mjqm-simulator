#!/usr/bin/env python3
"""
Generate per-class throughput plots at each policy's stability boundary (lambda*)
and at 80% of lambda* for comparison.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from plot_config import policy_styles, configure_matplotlib

configure_matplotlib()


def find_knee_row(group):
    """Return the row at the policy's lambda* (arrival rate at max Power)."""
    knee_idx = group["Power"].idxmax()
    return group.loc[knee_idx]


def find_80pct_row(group):
    """Return the row closest to 80% of the policy's lambda*."""
    knee_idx = group["Power"].idxmax()
    knee_lambda = group.loc[knee_idx, "arrival.rate"]
    target = 0.8 * knee_lambda
    closest_idx = (group["arrival.rate"] - target).abs().idxmin()
    return group.loc[closest_idx]


def plot_throughput(df, row_selector, output_path, caption_suffix=""):
    """
    Plot per-class throughput for each policy.
    row_selector: callable that takes a group DataFrame and returns a single row.
    """
    throughput_cols = [
        col for col in df.columns
        if col.endswith("Throughput") and col.startswith("T")
    ]
    class_ids = [int(col.split()[0][1:]) for col in throughput_cols]

    fig, ax = plt.subplots(figsize=(12, 8))

    for label, group in df.groupby("label"):
        if label not in policy_styles:
            continue

        style = policy_styles[label]
        row = row_selector(group)

        throughput_vals = np.array([row[col] for col in throughput_cols])
        throughput_vals = np.where(throughput_vals > 0, throughput_vals, np.nan)

        ax.scatter(class_ids, throughput_vals,
                   color=style["color"],
                   marker=style["marker"],
                   s=80,
                   alpha=0.8,
                   edgecolors="black",
                   linewidths=0.75,
                   label=label,
                   zorder=3)
        ax.plot(class_ids, throughput_vals,
                color=style["color"],
                linewidth=1.5,
                alpha=0.4)

    ax.set_xlabel("Server Requirement (cores)", fontsize=21)
    ax.set_ylabel("Throughput [jobs/s]", fontsize=21)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, which="both", alpha=0.3, linestyle="--", linewidth=1)
    ax.legend(loc="best", fontsize=14, framealpha=0.9, ncol=2)

    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved per-class throughput plot{caption_suffix} to {output_path}")
    plt.close()


if __name__ == "__main__":
    csv_path = Path("Results/cellA.csv")
    output_lambda = Path("../tesi/figures/per-class-throughput.pdf")
    output_80pct = Path("../tesi/figures/per-class-throughput-80pct.pdf")

    if not csv_path.exists():
        print(f"Error: Data file not found at {csv_path}")
        print("Run load_experiment_data.py first to generate the cleaned CSV.")
        exit(1)

    df = pd.read_csv(csv_path)

    plot_throughput(df, find_knee_row, output_lambda)
    plot_throughput(df, find_80pct_row, output_80pct,
                    caption_suffix=" (80% of lambda*)")
