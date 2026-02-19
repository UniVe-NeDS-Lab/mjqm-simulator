#!/usr/bin/env python3
"""
Generate per-class waiting times plot at each policy's stability boundary (lambda*)
to demonstrate fairness differences between policies.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from plot_config import policy_styles, configure_matplotlib

configure_matplotlib()


def plot_per_class_waiting(csv_path, output_path):
    """
    Plot per-class waiting times at each policy's stability boundary lambda*.
    For each policy, find its lambda* (arrival rate at max Power),
    then plot per-class waiting times at that rate.
    X-axis: server requirement (cores, log scale).
    Y-axis: per-class waiting time (log scale).
    One marker series per policy.
    """
    df = pd.read_csv(csv_path)

    # Extract job class sizes and per-class waiting time column names
    waiting_cols = [col for col in df.columns if col.endswith("Waiting") and col.startswith("T")]
    class_ids = [int(col.split()[0][1:]) for col in waiting_cols]

    fig, ax = plt.subplots(figsize=(12, 8))

    for label, group in df.groupby("label"):
        if label not in policy_styles:
            continue

        style = policy_styles[label]

        # Find lambda* for this policy (arrival rate at max Power)
        knee_idx = group["Power"].idxmax()
        knee_lambda = group.loc[knee_idx, "arrival.rate"]

        # Get the row at lambda*
        row = group.loc[knee_idx]

        # Extract per-class waiting times
        waiting_times = np.array([row[col] for col in waiting_cols])

        # Replace zeros/negatives with small value for log scale
        waiting_times = np.where(waiting_times > 0, waiting_times, np.nan)

        # Plot as scatter with lines
        ax.scatter(class_ids, waiting_times,
                   color=style["color"],
                   marker=style["marker"],
                   s=80,
                   alpha=0.8,
                   edgecolors="black",
                   linewidths=0.75,
                   label=label,
                   zorder=3)
        ax.plot(class_ids, waiting_times,
                color=style["color"],
                linewidth=1.5,
                alpha=0.4)

    # Configure axes
    ax.set_xlabel("Server Requirement (cores)", fontsize=21)
    ax.set_ylabel("Waiting Time [s]", fontsize=21)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, which="both", alpha=0.3, linestyle="--", linewidth=1)
    ax.legend(loc="best", fontsize=14, framealpha=0.9, ncol=2)

    plt.tight_layout()

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved per-class waiting times plot to {output_path}")
    plt.close()


if __name__ == "__main__":
    csv_path = Path("Results/cellA.csv")
    output_path = Path("../tesi/figures/per-class-waiting-times.pdf")

    if not csv_path.exists():
        print(f"Error: Data file not found at {csv_path}")
        print("Run load_experiment_data.py first to generate the cleaned CSV.")
        exit(1)

    plot_per_class_waiting(csv_path, output_path)
