#!/usr/bin/env python3
"""
Generate illustrative plot of Welch's method for initial transient removal.
This is a conceptual illustration for the methodology chapter.
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from plot_config import BLUE, CYAN, ORANGE, RED, TEAL, configure_matplotlib

configure_matplotlib()


def generate_synthetic_trace():
    """
    Generate synthetic queueing system trace with initial transient.
    Simulates response time measurements from empty start to steady state.
    """
    n_points = 500
    time = np.arange(n_points)

    # Initial transient: exponential decay from high values
    transient_length = 100
    transient = 50 * np.exp(-time / 30)

    # Steady state: oscillating around mean with noise
    steady_mean = 10
    steady_noise = 2 * np.sin(time / 20) + np.random.normal(0, 1, n_points)
    steady_state = steady_mean + steady_noise

    # Combine with smooth transition
    weight = 1 / (1 + np.exp(-(time - transient_length) / 10))
    response_time = (1 - weight) * transient + weight * steady_state

    return time, response_time


def apply_welch_moving_average(data, window_size=50):
    """Apply moving average for Welch's method visualization."""
    n = len(data)
    moving_avg = np.zeros(n - window_size + 1)

    for i in range(n - window_size + 1):
        moving_avg[i] = np.mean(data[i:i + window_size])

    return moving_avg


def plot_welch_method(output_path):
    """
    Create illustration of Welch's method showing:
    1. Raw response time trace
    2. Moving average to identify transient
    3. Detected truncation point
    """
    time, response_time = generate_synthetic_trace()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Panel 1: Raw trace with moving average
    window_size = 50
    moving_avg = apply_welch_moving_average(response_time, window_size)
    time_avg = time[window_size//2 : -(window_size//2) + 1]

    ax1.plot(time, response_time, color="gray", alpha=0.5, linewidth=1.5, label="Raw Measurements")
    ax1.plot(time_avg, moving_avg, color=BLUE, linewidth=4, label="Moving Average")

    # Detect truncation point (where moving average stabilizes)
    # Simple heuristic: where derivative is small
    derivative = np.abs(np.diff(moving_avg))
    stable_threshold = np.percentile(derivative, 10)
    stable_idx = np.where(derivative < stable_threshold)[0]
    if len(stable_idx) > 0:
        truncation_point = time_avg[stable_idx[0]]
    else:
        truncation_point = 100

    ax1.axvline(x=truncation_point, color=RED, linestyle="--", linewidth=3,
                label="Truncation Point")
    ax1.axvspan(0, truncation_point, alpha=0.2, color=ORANGE, label="Initial Transient")
    ax1.axvspan(truncation_point, time[-1], alpha=0.2, color=CYAN, label="Steady State")

    ax1.set_ylabel("Response Time [s]", fontsize=21)
    ax1.set_title("Welch's Method: Initial Transient Detection", fontsize=24, pad=20)
    ax1.legend(loc="upper right", fontsize=17, framealpha=0.9)
    ax1.grid(True, alpha=0.3, linewidth=1)

    # Panel 2: Steady-state portion only
    steady_mask = time >= truncation_point
    steady_time = time[steady_mask]
    steady_data = response_time[steady_mask]

    ax2.plot(steady_time, steady_data, color=TEAL, linewidth=1.5, alpha=0.7)
    ax2.axhline(y=np.mean(steady_data), color="black", linestyle="-", linewidth=3,
                label=f"Steady-State Mean = {np.mean(steady_data):.2f} s")
    ax2.fill_between(steady_time,
                      np.mean(steady_data) - np.std(steady_data),
                      np.mean(steady_data) + np.std(steady_data),
                      color="black", alpha=0.2, label="$\\pm 1$ Std. Dev.")

    ax2.set_xlabel("Simulation Time [s]", fontsize=21)
    ax2.set_ylabel("Response Time [s]", fontsize=21)
    ax2.set_title("Retained Steady-State Measurements", fontsize=21)
    ax2.legend(loc="upper right", fontsize=17, framealpha=0.9)
    ax2.grid(True, alpha=0.3, linewidth=1)

    plt.tight_layout()

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved Welch's method illustration to {output_path}")
    plt.close()


if __name__ == "__main__":
    output_path = Path("../tesi/figures/welch-method-example.pdf")
    plot_welch_method(output_path)
