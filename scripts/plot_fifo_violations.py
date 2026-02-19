#!/usr/bin/env python3
"""
Generate FIFO violations vs arrival rate plot for SMASH scheduling policies.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from plot_config import policy_styles, configure_matplotlib, smooth

configure_matplotlib()

# Only SMASH policies report FIFO violation counts
SMASH_POLICIES = ["SMASH (w = 2)", "SMASH (w = 5)", "SMASH (w = 10)"]


def plot_fifo_violations(csv_path, output_path, do_smooth=True):
    """
    Create log-scale plot of FIFO violations vs arrival rate for SMASH variants.

    Only shows arrival rates where violations are large enough for
    window-size differences to be visible (>= 1e6).

    Parameters:
    - csv_path: Path to cleaned experiment data CSV
    - output_path: Path for output PDF
    - do_smooth: Apply Savitzky-Golay filter for smoother curves
    """
    df = pd.read_csv(csv_path)

    # Keep only SMASH policies with violations above threshold
    THRESHOLD = 1e6
    df_smash = df[df["label"].isin(SMASH_POLICIES)].copy()
    df_smash = df_smash[df_smash["FIFO Violations"] >= THRESHOLD]

    # Compute lambda* for each SMASH variant (arrival rate at max Power)
    lambda_stars = {}
    for label, group in df.groupby("label"):
        if label in SMASH_POLICIES:
            knee_idx = group["Power"].idxmax()
            lambda_stars[label] = group.loc[knee_idx, "arrival.rate"]

    # Trim x-range: small margin past the highest SMASH lambda*
    max_ls = max(lambda_stars.values())
    x_max = max_ls * 1.15

    fig, ax = plt.subplots(figsize=(12, 8))

    for label in SMASH_POLICIES:
        group = df_smash[df_smash["label"] == label].sort_values("arrival.rate")
        group = group[group["arrival.rate"] <= x_max]
        if group.empty:
            continue

        style = policy_styles[label]
        x_data = group["arrival.rate"].values
        y_data = group["FIFO Violations"].values
        ls_val = lambda_stars.get(label)

        # Apply smoothing if requested
        y_smooth = smooth(y_data, window=3) if do_smooth else y_data

        # Split into stable and unstable regions
        mask_stable = x_data <= ls_val
        mask_unstable = x_data >= ls_val

        ax.plot(x_data[mask_stable], y_smooth[mask_stable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=3,
                label=label)
        ax.plot(x_data[mask_unstable], y_smooth[mask_unstable],
                color=style["color"],
                linestyle=style["linestyle"],
                linewidth=3,
                alpha=0.25)
        ax.scatter(x_data[mask_stable], y_data[mask_stable],
                   color=style["color"],
                   marker=style["marker"],
                   s=60,
                   alpha=0.6,
                   edgecolors="black",
                   linewidths=0.75)
        ax.scatter(x_data[mask_unstable], y_data[mask_unstable],
                   color=style["color"],
                   marker=style["marker"],
                   s=60,
                   alpha=0.15,
                   edgecolors="black",
                   linewidths=0.75)

    # Add vertical dashed lines at each policy's lambda*
    for label, ls in lambda_stars.items():
        color = policy_styles[label]["color"]
        ax.axvline(x=ls, color=color, linestyle="--", linewidth=2, alpha=0.6)

    ax.set_yscale("log")
    ax.set_xlabel("Arrival Rate [s$^{-1}$]", fontsize=21)
    ax.set_ylabel("FIFO Violations", fontsize=21)
    ax.grid(True, which="both", alpha=0.3, linestyle="--", linewidth=1)
    ax.legend(loc="lower right", fontsize=14, framealpha=0.9)

    plt.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved FIFO violations plot to {output_path}")
    plt.close()


if __name__ == "__main__":
    csv_path = Path("Results/cellA.csv")
    output_path = Path("../tesi/figures/fifo-violations.pdf")

    if not csv_path.exists():
        print(f"Error: Data file not found at {csv_path}")
        print("Run load_experiment_data.py first to generate the cleaned CSV.")
        exit(1)

    plot_fifo_violations(csv_path, output_path)
