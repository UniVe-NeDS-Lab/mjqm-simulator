#!/usr/bin/env python3
"""
Didactic three-panel figure showing how Kleinrock's power metric works.

Uses synthetic M/M/c data (c=10) to produce clean curves that illustrate
the throughput, response time, and power metric behaviour, highlighting
the knee (lambda*).
"""

import math
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from plot_config import BLACK, INDIGO, ORANGE, configure_matplotlib

configure_matplotlib(font_size=16)


def mm_c_metrics(lambdas, c=10, mu=1.0):
    """Approximate M/M/c throughput, response time, and power.

    Uses the Erlang-C based mean response time for M/M/c.
    """
    throughput = np.zeros_like(lambdas)
    resp_time = np.zeros_like(lambdas)

    for i, lam in enumerate(lambdas):
        rho = lam / (c * mu)
        if rho >= 1.0:
            # Unstable: throughput saturates, response time diverges
            throughput[i] = c * mu
            resp_time[i] = np.nan
            continue

        throughput[i] = lam  # stable: throughput = arrival rate

        # Erlang-C probability (iterative computation)
        a = lam / mu  # offered load
        p0_inv = 1.0
        term = 1.0
        for k in range(1, c):
            term *= a / k
            p0_inv += term
        term *= a / c
        p0_inv += term / (1.0 - rho)
        p0 = 1.0 / p0_inv
        pc = (a**c / math.factorial(c)) * p0 / (1.0 - rho)

        # Mean waiting time in queue
        wq = pc / (c * mu * (1.0 - rho))
        resp_time[i] = wq + 1.0 / mu

    power = throughput / resp_time
    return throughput, resp_time, power


def plot_kleinrock_theory(output_path):
    c = 10
    mu = 1.0
    max_lambda = c * mu
    lambdas = np.linspace(0.5, max_lambda * 1.05, 300)

    throughput, resp_time, power = mm_c_metrics(lambdas, c=c, mu=mu)

    # Find the knee (max power among finite values)
    finite_mask = np.isfinite(power)
    knee_idx = np.argmax(power[finite_mask])
    knee_lambda = lambdas[finite_mask][knee_idx]

    fig, axes = plt.subplots(3, 1, figsize=(6, 10), sharex=True)

    # ── Top: throughput ───────────────────────────────────────────────
    ax = axes[0]
    ax.plot(lambdas, throughput, color=INDIGO, linewidth=2.5)
    ax.axvline(knee_lambda, color=ORANGE, linestyle="--", linewidth=1.5, alpha=0.7)
    ax.set_ylabel(r"$X(\lambda)$ [jobs/s]")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_title("Throughput", fontsize=14)

    # ── Middle: response time ─────────────────────────────────────────
    ax = axes[1]
    ax.plot(lambdas[finite_mask], resp_time[finite_mask], color=INDIGO, linewidth=2.5)
    ax.axvline(knee_lambda, color=ORANGE, linestyle="--", linewidth=1.5, alpha=0.7)
    ax.set_ylabel(r"$R(\lambda)$ [s]")
    ax.set_yscale("log")
    ax.grid(True, which="both", alpha=0.3, linestyle="--")
    ax.set_title("Response time", fontsize=14)

    # ── Bottom: power metric ──────────────────────────────────────────
    ax = axes[2]
    ax.plot(lambdas[finite_mask], power[finite_mask], color=INDIGO, linewidth=2.5)
    ax.axvline(knee_lambda, color=ORANGE, linestyle="--", linewidth=1.5, alpha=0.7)
    ax.scatter([knee_lambda], [power[finite_mask][knee_idx]],
               color=ORANGE, s=120, zorder=5, edgecolors=BLACK, linewidths=1.5)
    ax.annotate(
        r"$\lambda^*$",
        xy=(knee_lambda, power[finite_mask][knee_idx]),
        xytext=(knee_lambda + 0.6, power[finite_mask][knee_idx] * 0.85),
        fontsize=16, color=ORANGE,
        arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.5),
    )
    ax.set_xlabel(r"Arrival rate $\lambda$ [jobs/s]")
    ax.set_ylabel(r"$P(\lambda) = X/R$ [s$^{-2}$]")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_title("Power metric", fontsize=14)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved Kleinrock theory plot to {output_path}")
    plt.close()


if __name__ == "__main__":
    output_path = Path("../tesi/figures/kleinrock-theory.pdf")
    plot_kleinrock_theory(output_path)
