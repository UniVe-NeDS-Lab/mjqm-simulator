#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from pathlib import Path

import pandas as pd
from colorama import Fore, Style
from colorama import init as colorama_init
from tqdm import tqdm

colorama_init(autoreset=True)

################################ KNOWN POLICIES ################################
policies_keys = [
    "smash",
    "fifo",
    "most server first",
    "server filling",
    "server filling memoryful",
    "back filling",
    "kill smart",
    "quick swap",
    "first fit",
    "adaptive msf",
    "static msf",
]
policies_labels = [
    "SMASH (w = {0})",
    "First-In First-Out",
    "Most Server First",
    "Server Filling",
    "Server Filling",
    "Back Filling",
    "Kill Smart (k = {0}, v = {1})",
    "Quick Swap (l = {0})",
    "First-Fit",
    "Adaptive MSF",
    "Static MSF",
]
policies = dict(zip(policies_keys, policies_labels))
policies_wins = {
    1: "fifo",
    0: "most server first",
    -1: "server filling",
    -2: "server filling memoryful",
    -3: "back filling",
    -16: "kill smart",
    -4: "quick swap",
    -14: "first fit",
    -7: "adaptive msf",
    -8: "static msf",
}


################################ PANDAS CONFIGS ################################
policies_dtype = pd.api.types.CategoricalDtype(
    categories=policies_keys, ordered=True
)
stability_check_mapping = {
    "0": True,
    "1": False,
}  # we invert them because the column actually means "warning"


def fix_policy(row, win):
    if "policy" not in row and "policy.name" not in row:
        if win > 1:
            return "smash"
        else:
            return policies_wins[win]
    elif "policy.name" in row:
        return row["policy.name"]
    return row["policy"]


def row_label(row, win):
    if row["policy"] == "smash":
        if "policy.window" in row:
            return policies[row["policy"]].format(row["policy.window"])
        elif "smash.window" in row:
            return policies[row["policy"]].format(row["smash.window"])
        else:
            return policies[row["policy"]].format(win)
    elif row["policy"] == "quick swap":
        if "policy.threshold" in row:
            return policies[row["policy"]].format(row["policy.threshold"])
        else:
            return policies[row["policy"]].format(1)
    elif row["policy"] == "kill smart":
        print(policies)
        return policies[row["policy"]].format(row["policy.k"],row["policy.v"])
    else:
        return policies[row["policy"]]


required_columns = set(["arrival.rate", "Utilisation"])


def read_csv(f: Path):
    try:
        df = pd.read_csv(f, delimiter=";")
    except Exception as e:
        print(f"Error reading {f}: {e}", file=sys.stderr)
        return None
    if df.empty:
        return None
    win = None
    if match := re.search(r"Win(?P<win>-?\d+)", f.stem):
        win = int(match.group("win"))
    df["policy"] = df.apply(fix_policy, axis=1, args=(win,))
    if "policy.name" in df.columns:
        del df["policy.name"]
    df.insert(0, "label", df.apply(row_label, axis=1, args=(win,)))
    missing_columns = {"arrival.rate", "Utilisation"} - set(df.columns)
    if missing_columns:
        print(f"Missing columns in {f}: {missing_columns}", file=sys.stderr)
        return None
    actual_check = False
    stability_columns = []
    for column in df.columns:
        if "policy" == column:
            df[column] = df[column].astype(policies_dtype)
        elif "Stability Check" in column:
            df[column] = df[column].map(stability_check_mapping).astype(bool)
            if "Stability Check" == column:
                actual_check = True
            else:
                stability_columns.append(column)
    if not actual_check:
        df["Stability Check"] = df[stability_columns].all(axis=1)
    return df


def concat_csv_files(filenames: list[Path], progress: tqdm):
    dfs = []
    for f in filenames:
        df = read_csv(f)
        progress.update(1)
        if df is None:
            continue
        dfs.append(df)
    if not dfs:
        return None
    return pd.concat(dfs)


def clean_dfs(dfs):
    types = {}
    drops = []
    Ts = set()
    for column in dfs.columns:
        if "policy" == column:
            pass
        elif "label" == column:
            pass
        elif "Stability Check" in column:
            pass
        elif (
            "ConfInt" not in column
            and "Unnamed" not in column
            and not column.endswith(".window")
            and not column.endswith(".threshold")
            and not column.endswith(".k")
            and not column.endswith(".v")
        ):
            types[column] = float
        else:
            drops.append(column)
        if match := re.match(r"T(?P<T>\d+)", column):
            Ts.add(int(match.group("T")))
    Ts = sorted(list(Ts))
    progress.write(f"{len(Ts)} classes: {', '.join(map(str, Ts))}")
    rates = sorted(list(dfs["arrival.rate"].unique()))
    progress.write(f"{len(rates)} arrival rates: {', '.join(map(str, rates))}")
    dfs = dfs.drop(columns=drops)
    dfs = dfs.astype(types)

    idx = ["label", "arrival.rate"]
    dupes = dfs.duplicated(subset=idx, keep="last")
    if dupes.any():
        progress.write(
            f"{Fore.YELLOW}{Style.BRIGHT}Dropping {dupes.sum()} duplicate rows (keeping latest)"
        )
        dfs = dfs[~dupes]
    dfs.sort_values(
        by=idx,
        inplace=True,
        ignore_index=True,
    )
    dfs.set_index(idx, drop=False, inplace=True)
    dfs.sort_index(inplace=True)

    exp = dfs.index.names.difference(["arrival.rate"])
    if len(exp) == 1:
        exp = exp[0]

    return dfs, Ts, exp


def compute_stability(dfs, exp, response_col="RespTime Total"):
    """
    Identifies stability using Kleinrock's Power Metric (The Knee).

    Stability is defined as the operating range up to the point of
    maximum system power (Throughput / Response Time).

    Logic:
    1. Calculate total throughput by summing per-class throughputs.
    2. Calculate Power = Throughput / Response Time.
    3. Find the arrival rate that maximizes Power (The Knee).
    4. Mark all arrival rates <= Knee as 'stable'.
    """

    # 1. Compute total throughput from per-class throughputs
    # Find all columns matching the pattern "T{number} Throughput" (excluding ConfInt)
    throughput_cols = [col for col in dfs.columns
                       if col.startswith('T')
                       and col.endswith('Throughput')
                       and 'ConfInt' not in col]

    # Sum across all job classes to get total system throughput
    # In stable operation, this equals arrival rate; beyond stability, it saturates
    dfs["Throughput Total"] = dfs[throughput_cols].sum(axis=1)

    # 2. Calculate Kleinrock's Power
    # Power = effective work done (throughput) / delay experienced (response time)
    dfs["Power"] = dfs["Throughput Total"] / dfs[response_col]

    # 3. Define the Knee detection logic
    def apply_knee_detection(group):
        # Find the index of the row with the maximum Power
        knee_idx = group["Power"].idxmax()

        # Get the arrival rate at the knee
        knee_lambda = group.loc[knee_idx, "arrival.rate"]

        # Propagate stability:
        # Anything with load <= knee_lambda is stable (Pre-knee + Knee).
        # Anything with load > knee_lambda is considered saturated/unstable.
        group["stable"] = group["arrival.rate"] <= knee_lambda

        return group

    # We use apply() to handle the per-experiment masking
    dfs = dfs.groupby(level=exp, group_keys=False).apply(apply_knee_detection)

    # Optional: Combine with previous checks if they exist
    if "Stability Check" in dfs.columns:
        dfs["stable"] = dfs["stable"] & dfs["Stability Check"]

    return dfs


def compute_utilisation(dfs, Ts, exp, n_cores=None):
    asymptotes = dfs.groupby(
        level=exp
    ).apply(
        lambda x: (
            x["arrival.rate"]
            # this shift makes the "minimum" extraction do what we want
            .shift(1, fill_value=x["arrival.rate"].max())
            # we keep all non-stable columns (but given the previous shift, we get also the last stable value)
            .where(~x["stable"], x["arrival.rate"].max())
            .min()  # keep the maximum (known) arrival rate where the system is still stable
        )
    )
    asymptotes.name = "asymptote"

    max_arrival_rates = dfs.groupby(level=exp)["arrival.rate"].max()
    instability_not_reached = max_arrival_rates == asymptotes
    for idx, not_reached in instability_not_reached.items():
        if not_reached:
            progress.write(
                f"{Fore.YELLOW}{Style.BRIGHT}Instability region not reached for {idx} with maximum arrival rate tested: {max_arrival_rates[idx]}"
            )

    actual_util = pd.Series(
        pd.NA, index=asymptotes.index, name="system_utilisation"
    )
    for idx, df_select in dfs.groupby(level=exp):
        summ_util = 0
        asymptote = asymptotes[idx]
        asymp_row = df_select.loc[idx, asymptote]
        Ps = [asymp_row[f"T{T} lambda"] / asymp_row["arrival.rate"] for T in Ts]
        serTimes = [
            asymp_row[f"T{T} RespTime"] - asymp_row[f"T{T} Waiting"] for T in Ts
        ]
        for t in range(len(Ts)):
            summ_util += asymptote * Ps[t] * serTimes[t] * Ts[t] * (1 / n_cores)
        actual_util[idx] = summ_util * 100.0

    return asymptotes, actual_util


def compute_fairness_cv(dfs, Ts):
    """
    Computes the Coefficient of Variation (CV) of per-class waiting times.

    CV = (standard deviation / mean) across all job classes

    Lower CV indicates more uniform (fair) treatment across classes.
    Higher CV indicates greater dispersion (unfairness).

    Parameters:
    - dfs: DataFrame with per-class waiting time columns
    - Ts: List of job class identifiers (e.g., [1, 100, 2998])

    Returns:
    - DataFrame with added column "WaitTime CV"
    """
    # Find all per-class waiting time columns (excluding ConfInt columns)
    waiting_cols = [f"T{T} Waiting" for T in Ts]

    # Verify all columns exist
    missing_cols = [col for col in waiting_cols if col not in dfs.columns]
    if missing_cols:
        print(f"Warning: Missing waiting time columns: {missing_cols}", file=sys.stderr)
        waiting_cols = [col for col in waiting_cols if col in dfs.columns]

    if not waiting_cols:
        print("Error: No waiting time columns found for CV computation", file=sys.stderr)
        dfs["WaitTime CV"] = pd.NA
        return dfs

    # Compute mean and std across classes for each row (experiment configuration)
    dfs["WaitTime Mean (per-class)"] = dfs[waiting_cols].mean(axis=1)
    dfs["WaitTime Std (per-class)"] = dfs[waiting_cols].std(axis=1)

    # Compute CV = std / mean
    # Handle division by zero: if mean is very close to zero, set CV to NaN
    dfs["WaitTime CV"] = dfs["WaitTime Std (per-class)"] / dfs["WaitTime Mean (per-class)"]
    dfs.loc[dfs["WaitTime Mean (per-class)"].abs() < 1e-9, "WaitTime CV"] = pd.NA

    return dfs


def load_experiments_list():
    results = Path("Results")
    return results, list(
        f for f in results.glob("**/") if f != results and list(f.glob("*.csv"))
    )


def select_experiment(preselected: str):
    base, available = load_experiments_list()
    if preselected:
        if preselected.startswith("/"):
            selected = Path(preselected)
            if selected.is_dir() and list(selected.glob("*.csv")):
                print(selected)
                return selected
            print(
                f"{Fore.YELLOW}{Style.BRIGHT}No CSV files found in: {preselected}",
                file=sys.stderr,
            )
            return None
        if (selected := base / preselected) in available:
            print(selected)
            return selected
        print(
            f"{Fore.YELLOW}{Style.BRIGHT}Unknown folder: {preselected}",
            file=sys.stderr,
        )
    selected = None
    while selected not in available:
        print(f"Available folders in {base}:")
        for f in available:
            print("-", f.relative_to(base))
        selected = input("Enter folder to read results from: ")
        if not selected:
            print(f"{Fore.YELLOW}{Style.BRIGHT}No folder selected, exiting")
            return None
        selected = base / selected
    return selected


def load_experiment_data(folder, n_cores=None):
    global progress
    if isinstance(folder, Path):
        pass
    elif folder.startswith("/"):
        folder = Path(folder)
    else:
        folder = Path("Results") / folder
    filenames = list(folder.glob("*.csv"))
    if not filenames:
        print(
            f"{Fore.RED}{Style.BRIGHT}No CSV files found in {folder}",
            file=sys.stderr,
        )
        return None, None, None, None, None
    progress = tqdm(None, desc="Loading data", total=len(filenames) + 5)
    dfs = concat_csv_files(filenames, progress)
    if "cores" in dfs.columns:
        n_cores = dfs["cores"].max()
    progress.update(1)
    if dfs is None:
        progress.close()
        print(
            f"{Fore.RED}{Style.BRIGHT}No data found in CSV files from {folder}",
            file=sys.stderr,
        )
        return None, None, None, None, None
    dfs, Ts, exp = clean_dfs(dfs)
    progress.update(1)
    dfs = compute_stability(dfs, exp)
    progress.update(1)
    asymptotes, actual_util = compute_utilisation(dfs, Ts, exp, n_cores=n_cores)
    progress.update(1)
    dfs = compute_fairness_cv(dfs, Ts)
    progress.update(1)
    progress.close()

    # write final dfs to folder parent using folder name as prefix
    output_folder = folder.parent
    output_file = output_folder / f"{folder.name}.csv"
    dfs.to_csv(output_file, index=False)
    print(f"{Fore.GREEN}{Style.BRIGHT}Cleaned data saved to {output_file}")

    return dfs, Ts, exp, asymptotes, actual_util


def main():
    folder = select_experiment(sys.argv[1] if len(sys.argv) > 1 else None)
    if not folder:
        exit(0)
    dfs, Ts, exp, asymptotes, actual_util = load_experiment_data(
        folder, n_cores=2048
    )

    return dfs, Ts, exp, asymptotes, actual_util


if __name__ == "__main__":
    main()
