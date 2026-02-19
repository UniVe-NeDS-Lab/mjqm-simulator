#!/usr/bin/env python3
"""Generate LaTeX table rows for coefficient of variation (CV) comparison.

Reads cellA.csv and produces two tables:

  Table A: all policies at the highest common stable lambda
           (max lambda where ALL 11 policies are simultaneously stable)
  Table B: each policy at its own maximum stable lambda (lambda*)

Columns: Policy, Mean waiting time, CV (per-class),
         Min per-class WT (class), Max per-class WT (class)

Usage:
    python generate_cv_table.py [path/to/cellA.csv]
"""

import csv
import sys
from pathlib import Path

DEFAULT_CSV = Path(__file__).resolve().parent.parent / "Results" / "cellA.csv"

CLASS_NAMES = [
    "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10",
    "T11", "T14", "T18", "T20", "T24", "T27", "T28", "T30", "T38",
    "T40", "T42", "T50", "T60", "T80", "T98", "T100", "T120", "T498",
    "T2998",
]

POLICY_DISPLAY = {
    "fifo": "FIFO",
    "server filling memoryful": "Server Filling",
    "back filling": "Back Filling",
    "most server first": "Most Server First",
    "adaptive msf": "Adaptive MSF",
    "static msf": "Static MSF",
    "smash": "SMASH",
    "quick swap": "Quick Swap",
}


def policy_label(row):
    """Build a human-readable policy label from the CSV row."""
    policy = row["policy"].strip()
    label = row["label"].strip()
    base = POLICY_DISPLAY.get(policy, label)
    window = row.get("policy.window.1", "").strip()
    threshold = row.get("policy.threshold.1", "").strip()
    if window:
        base += f" ($w={window}$)"
    elif threshold:
        base += f" ($l={threshold}$)"
    return base


def policy_label_plain(row):
    """Plain text label for console output."""
    policy = row["policy"].strip()
    label = row["label"].strip()
    base = POLICY_DISPLAY.get(policy, label)
    window = row.get("policy.window.1", "").strip()
    threshold = row.get("policy.threshold.1", "").strip()
    if window:
        base += f" (w={window})"
    elif threshold:
        base += f" (l={threshold})"
    return base


def extract_per_class_waiting(row):
    """Return dict {class_name: waiting_time} for all classes."""
    result = {}
    for cls in CLASS_NAMES:
        col = f"{cls} Waiting"
        val = row.get(col, "").strip()
        if val:
            result[cls] = float(val)
    return result


def format_wt(val):
    """Format waiting time for display."""
    if val == 0:
        return "0"
    elif abs(val) < 0.0001:
        return f"{val:.2e}"
    elif abs(val) < 1:
        return f"{val:.4f}"
    elif abs(val) < 100:
        return f"{val:.3f}"
    else:
        return f"{val:.1f}"


def format_wt_latex(val):
    """Format waiting time for LaTeX."""
    if val == 0:
        return "0"
    elif abs(val) < 0.0001:
        exp = f"{val:.2e}"
        mantissa, power = exp.split("e")
        power = int(power)
        return f"${mantissa} \\times 10^{{{power}}}$"
    elif abs(val) < 0.01:
        return f"{val:.4f}"
    elif abs(val) < 1:
        return f"{val:.3f}"
    elif abs(val) < 100:
        return f"{val:.2f}"
    else:
        return f"{val:.1f}"


def find_row_at_utilisation(policy_rows, target_util):
    """Find the row closest to target utilisation for a given policy."""
    best = None
    best_diff = float("inf")
    for r in policy_rows:
        util = float(r["Utilisation"])
        diff = abs(util - target_util)
        if diff < best_diff:
            best_diff = diff
            best = r
    return best, best_diff


def build_row_data(row):
    """Extract table data from a single CSV row."""
    per_class = extract_per_class_waiting(row)
    if not per_class:
        return None

    cv_str = row.get("WaitTime CV", "").strip()
    wt_total = row.get("WaitTime Total", "").strip()
    util = float(row["Utilisation"])
    lam = float(row["arrival.rate"])
    stable = row.get("stable", "").strip()

    cv = float(cv_str) if cv_str else 0
    mean_wt = float(wt_total) if wt_total else 0
    min_cls = min(per_class, key=per_class.get)
    max_cls = max(per_class, key=per_class.get)

    return {
        "policy": policy_label(row),
        "policy_plain": policy_label_plain(row),
        "cv": cv,
        "mean_wt": mean_wt,
        "util": util,
        "lambda": lam,
        "min_wt": per_class[min_cls],
        "min_cls": min_cls,
        "max_wt": per_class[max_cls],
        "max_cls": max_cls,
        "stable": stable,
        "per_class": per_class,
    }


def build_table_at_lambda(all_rows, target_lambda, policies_grouped):
    """Build table data with all policies at the same lambda."""
    table = []
    for label, rows in sorted(policies_grouped.items()):
        best = min(rows, key=lambda r: abs(float(r["arrival.rate"]) - target_lambda))
        data = build_row_data(best)
        if data:
            table.append(data)
    return table


def build_table_at_utilisation(all_rows, target_util, policies_grouped):
    """Build table data by finding each policy's row at matched utilisation."""
    table = []
    for label, rows in sorted(policies_grouped.items()):
        stable_rows = [r for r in rows if r.get("stable", "").strip() == "True"]
        if not stable_rows:
            stable_rows = rows
        best, diff = find_row_at_utilisation(stable_rows, target_util)
        if best is None:
            continue
        data = build_row_data(best)
        if data:
            table.append(data)
    return table


def build_table_at_lambda_star(policies_grouped):
    """Build table data with each policy at its own max stable lambda."""
    table = []
    for label, rows in sorted(policies_grouped.items()):
        stable_rows = [r for r in rows if r.get("stable", "").strip() == "True"]
        if not stable_rows:
            continue
        # Find the row with the highest stable lambda
        best = max(stable_rows, key=lambda r: float(r["arrival.rate"]))
        data = build_row_data(best)
        if data:
            table.append(data)
    return table


def print_table(table, title, caption_detail, show_lambda=False):
    """Print table in both readable and LaTeX formats."""
    print(f"\n{'=' * 110}")
    print(f"  {title}")
    print(f"{'=' * 110}\n")

    table.sort(key=lambda r: r["cv"])

    header = f"{'Policy':<28} "
    if show_lambda:
        header += f"{'lambda':>8} "
    header += (f"{'Util%':>6} {'Mean WT':>12} {'CV':>8} "
               f"{'Min WT':>12} {'Class':>6} {'Max WT':>12} {'Class':>6} {'Stable':>6}")
    print(header)
    print("-" * 120)
    for r in table:
        line = f"{r['policy_plain']:<28} "
        if show_lambda:
            line += f"{r['lambda']:>8.1f} "
        line += (f"{r['util'] * 100:>5.1f}% "
                 f"{format_wt(r['mean_wt']):>12} {r['cv']:>8.2f} "
                 f"{format_wt(r['min_wt']):>12} {r['min_cls']:>6} "
                 f"{format_wt(r['max_wt']):>12} {r['max_cls']:>6} "
                 f"{r['stable']:>6}")
        print(line)

    print("\n\nLaTeX table (sorted by CV):\n")
    print(r"\begin{table}[ht]")
    print(r"\centering")
    print(f"\\caption{{{caption_detail}}}")
    print(r"\label{tab:cv-comparison}")
    cols = "lcccc"
    col_header = (r"\textbf{Policy} & \textbf{Mean $W$} & \textbf{CV} "
                  r"& \textbf{Min class $W_i$} & \textbf{Max class $W_i$} \\")
    print(f"\\begin{{tabular}}{{{cols}}}")
    print(r"\toprule")
    print(col_header)
    print(r"\midrule")
    for r in table:
        min_info = f"{format_wt_latex(r['min_wt'])} ({r['min_cls']})"
        max_info = f"{format_wt_latex(r['max_wt'])} ({r['max_cls']})"
        print(f"  {r['policy']:<28} & {format_wt_latex(r['mean_wt']):>12} "
              f"& {r['cv']:.2f} "
              f"& {min_info} "
              f"& {max_info} \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table}")


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    if not csv_path.exists():
        print(f"Error: CSV not found at {csv_path}", file=sys.stderr)
        sys.exit(1)

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    # Group rows by policy label
    policies_grouped = {}
    for r in all_rows:
        label = r["label"].strip()
        policies_grouped.setdefault(label, []).append(r)

    print(f"Found {len(policies_grouped)} policies:")
    for label in sorted(policies_grouped):
        utils = [float(r["Utilisation"]) for r in policies_grouped[label]]
        print(f"  {label}: {len(policies_grouped[label])} rates, "
              f"util range {min(utils)*100:.1f}% - {max(utils)*100:.1f}%")

    # --- Find max stable utilisation for each policy ---
    max_stable_util = {}
    for label, rows in policies_grouped.items():
        stable_utils = [float(r["Utilisation"]) for r in rows
                        if r.get("stable", "").strip() == "True"]
        if stable_utils:
            max_stable_util[label] = max(stable_utils)
        else:
            max_stable_util[label] = 0

    print("\nMax stable utilisation per policy:")
    for label in sorted(max_stable_util, key=max_stable_util.get):
        print(f"  {label}: {max_stable_util[label]*100:.1f}%")

    common_max_util = min(max_stable_util.values())
    print(f"\nHighest common stable utilisation: {common_max_util*100:.1f}%")

    # --- Table A: highest common stable lambda ---
    # For each policy, find the set of lambda values where it is stable
    stable_lambdas_by_policy = {}
    for label, rows in policies_grouped.items():
        stable_lambdas_by_policy[label] = set()
        for r in rows:
            if r.get("stable", "").strip() == "True":
                stable_lambdas_by_policy[label].add(float(r["arrival.rate"]))

    common_stable_lambdas = set.intersection(*stable_lambdas_by_policy.values())
    if common_stable_lambdas:
        target_a = max(common_stable_lambdas)
    else:
        print("ERROR: No common stable lambda found!")
        sys.exit(1)

    print(f"\nHighest common stable lambda: {target_a:.1f}")
    table_a = build_table_at_lambda(all_rows, target_a, policies_grouped)
    print_table(table_a,
                f"Table A: CV comparison at highest common stable lambda = {target_a:.1f}",
                f"Per-class fairness comparison at $\\lambda = {target_a:.0f}$ jobs/time unit")

    # --- Table B: each policy at its own lambda* ---
    table_b = build_table_at_lambda_star(policies_grouped)
    print_table(table_b,
                "Table B: CV comparison at each policy's stability boundary (lambda*)",
                "Per-class fairness comparison at each policy's stability boundary $\\lambda^*$",
                show_lambda=True)

    # --- Cross-check: prose values at lambda ~ 404 ---
    print("\n" + "=" * 110)
    print("  Cross-check: per-class WT at lambda ~ 404 for thesis prose classes")
    print("=" * 110)
    for label in sorted(policies_grouped):
        rows_at_lam = [r for r in policies_grouped[label]
                       if abs(float(r["arrival.rate"]) - target_a) < 0.1]
        if not rows_at_lam:
            continue
        r = rows_at_lam[0]
        per_class = extract_per_class_waiting(r)
        wt_total = r.get("WaitTime Total", "").strip()
        cv_str = r.get("WaitTime CV", "").strip()
        util = float(r["Utilisation"])
        stable = r.get("stable", "").strip()
        print(f"\n{policy_label_plain(r):30} (WT Total={wt_total}, CV={cv_str}, "
              f"Util={util*100:.1f}%, Stable={stable})")
        for cls in ["T1", "T2", "T100", "T2998"]:
            val = per_class.get(cls, "N/A")
            print(f"  {cls:>6}: {format_wt(val) if isinstance(val, float) else val}")


if __name__ == "__main__":
    main()
