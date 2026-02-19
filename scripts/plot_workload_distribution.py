#!/usr/bin/env python3
"""
Generate workload distribution plot showing job class probabilities and service times.
This plot visualizes the heterogeneity of the Google Borg Cell A workload.
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import tomllib
from plot_config import BLUE, ORANGE, configure_matplotlib

configure_matplotlib()


def load_workload_config(config_path):
    """Load workload configuration from TOML file."""
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    classes = []
    for job_class in config.get("class", []):
        cores = job_class.get("cores", 1)
        prob = job_class["arrival"].get("prob", 0)
        service_mean = job_class["service"].get("mean", 0)
        classes.append({
            "cores": cores,
            "probability": prob,
            "service_mean": service_mean
        })

    return classes


def plot_workload_distribution(classes, output_path):
    """
    Create a dual-axis plot showing:
    - Bar plot: arrival probabilities for each job class
    - Line plot: mean service times for each job class
    Both against server requirements (log scale).
    """
    cores = [c["cores"] for c in classes]
    probs = [c["probability"] for c in classes]
    service_times = [c["service_mean"] for c in classes]

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Primary axis: arrival probabilities
    color = BLUE
    ax1.bar(range(len(cores)), probs, color=color, alpha=0.7,
            edgecolor="black", linewidth=1.5, label="Arrival Probability")
    ax1.set_xlabel("Job Class (by Server Requirement)", fontsize=21)
    ax1.set_ylabel("Arrival Probability", color=color, fontsize=21)
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.set_yscale("log")
    ax1.grid(True, alpha=0.3, which="both", axis="y", linewidth=1)

    # Secondary axis: service times
    ax2 = ax1.twinx()
    color = ORANGE
    ax2.plot(range(len(cores)), service_times, color=color, marker="o",
             linewidth=3, markersize=6, label="Mean Service Time")
    ax2.set_ylabel("Mean Service Time [s]", color=color, fontsize=21)
    ax2.tick_params(axis="y", labelcolor=color)

    # X-axis labels showing core counts
    ax1.set_xticks(range(len(cores)))
    ax1.set_xticklabels([str(c) for c in cores], rotation=90, ha="center")

    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=17)

    plt.tight_layout()

    # Save as PDF for thesis
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved workload distribution plot to {output_path}")
    plt.close()


if __name__ == "__main__":
    # Load configuration from Inputs folder
    config_path = Path("Inputs/cellA_Sorted_4096.toml")
    output_path = Path("../tesi/figures/workload-distribution.pdf")

    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        exit(1)

    classes = load_workload_config(config_path)
    plot_workload_distribution(classes, output_path)
