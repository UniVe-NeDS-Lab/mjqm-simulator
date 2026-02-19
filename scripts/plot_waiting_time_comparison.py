#!/usr/bin/env python3
"""
Generate waiting time vs arrival rate comparison for all scheduling policies (log-log plot).
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from plot_config import policy_styles, configure_matplotlib, smooth

configure_matplotlib()


def plot_waiting_time_comparison(csv_path, output_path, do_smooth=True):
    """
    Create log-log plot comparing waiting times across all policies.

    Parameters:
    - csv_path: Path to cleaned experiment data CSV
    - output_path: Path for output PDF
    - smooth: Apply Savitzky-Golay filter for smoother curves
    """
    # Load data
    df = pd.read_csv(csv_path)

    # Filter to only stable configurations
    df_stable = df[df["stable"] == True].copy()

    fig, ax = plt.subplots(figsize=(12, 8))

    # Compute lambda* for each policy (arrival rate at max Power)
    lambda_stars = {}
    for label, group in df.groupby("label"):
        knee_idx = group["Power"].idxmax()
        lambda_stars[label] = group.loc[knee_idx, "arrival.rate"]

    # Plot each policy
    for label, group in df_stable.groupby("label"):
        if label not in policy_styles:
            continue

        style = policy_styles[label]

        x_data = group["arrival.rate"].values
        y_data = group["WaitTime Total"].values

        # Sort by arrival rate
        sort_idx = np.argsort(x_data)
        x_data = x_data[sort_idx]
        y_data = y_data[sort_idx]

        # Apply smoothing if requested
        y_smooth = smooth(y_data) if do_smooth else y_data

        # Plot
        ax.plot(x_data, y_smooth,
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=3,
                label=label)
        ax.scatter(x_data, y_data,
                   color=style["color"],
                   marker=style["marker"],
                   s=60,
                   alpha=0.6,
                   edgecolors="black",
                   linewidths=0.75)

    # Add vertical dashed lines at each policy's lambda*
    # Group overlapping lambda* values to avoid clutter
    from collections import defaultdict
    lambda_groups = defaultdict(list)
    for label, ls in lambda_stars.items():
        lambda_groups[ls].append(label)

    for ls, labels in lambda_groups.items():
        # Use the colour of the first policy in the group
        first_label = labels[0]
        if first_label in policy_styles:
            color = policy_styles[first_label]["color"]
        else:
            color = "gray"
        # Compute utilisation percentage
        util = ls / max(lambda_stars.values()) * 96.1  # scale relative to max
        # Actually compute from the data: util = Utilisation at lambda*
        util_val = df[(df["label"] == first_label) & (np.isclose(df["arrival.rate"], ls))]["Utilisation"].values
        if len(util_val) > 0:
            util_pct = util_val[0] * 100
        else:
            util_pct = None

        ax.axvline(x=ls, color=color, linestyle="--", linewidth=2, alpha=0.6)

    # Configure axes
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Arrival Rate [s$^{-1}$]", fontsize=21)
    ax.set_ylabel("Average Waiting Time [s]", fontsize=21)
    ax.grid(True, which="both", alpha=0.3, linestyle="--", linewidth=1)
    ax.legend(loc="upper left", fontsize=14, framealpha=0.9, ncol=2)

    plt.tight_layout()

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved waiting time comparison to {output_path}")
    plt.close()


if __name__ == "__main__":
    csv_path = Path("Results/cellA.csv")
    output_path = Path("../tesi/figures/waiting-time-comparison.pdf")

    if not csv_path.exists():
        print(f"Error: Data file not found at {csv_path}")
        print("Run load_experiment_data.py first to generate the cleaned CSV.")
        exit(1)

    plot_waiting_time_comparison(csv_path, output_path, do_smooth=False)
