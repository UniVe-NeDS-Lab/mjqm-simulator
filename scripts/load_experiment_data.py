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
    -4: "quick swap",
    -14: "first fit",
    -7: "adaptive msf",
    -8: "static msf",
}


################################ PANDAS CONFIGS ################################
policies_dtype = pd.api.types.CategoricalDtype(categories=policies_keys, ordered=True)
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
    else:
        return policies[row["policy"]]


required_columns = set(["arrival.rate", "Utilisation"])


def read_csv(f: Path):
    df = pd.read_csv(f, delimiter=";")
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


def compute_stability(dfs, exp):
    arr_rate_increase = dfs.groupby(level=exp)["arrival.rate"].transform(
        lambda x: x.rolling(2).sem()
    )
    util_increase = dfs.groupby(level=exp)["Utilisation"].transform(
        lambda x: x.rolling(2).sem()
    )
    util_increase_ratio = arr_rate_increase / util_increase
    util_increase_ratio.name = "Utilisation Increase Ratio"
    dfs = pd.concat([dfs, util_increase_ratio], axis=1)
    divergence = dfs.groupby(level=exp)["Utilisation Increase Ratio"].transform(
        lambda x: (
            x.rolling(2)
            .apply(lambda x: abs(1.0 - x.iloc[1] / x.iloc[0]))
            .fillna(0)
            .cummax()
        )
    )
    stable = dfs["Stability Check"] & (divergence < 0.01)
    stable.name = "stable"
    dfs = pd.concat([dfs, stable], axis=1)
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

    actual_util = pd.Series(pd.NA, index=asymptotes.index, name="system_utilisation")
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


def load_experiments_list():
    results = Path("Results")
    return results, list(
        f for f in results.glob("**/") if f != results and list(f.glob("*.csv"))
    )


def select_experiment(preselected: str):
    base, available = load_experiments_list()
    if preselected:
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
    folder = folder if isinstance(folder, Path) else Path("Results") / folder
    filenames = list(folder.glob("*.csv"))
    if not filenames:
        print(
            f"{Fore.RED}{Style.BRIGHT}No CSV files found in {folder}",
            file=sys.stderr,
        )
        return None, None, None, None, None
    progress = tqdm(None, desc="Loading data", total=len(filenames) + 4)
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
    progress.close()

    return dfs, Ts, exp, asymptotes, actual_util


def main():
    folder = select_experiment(sys.argv[1] if len(sys.argv) > 1 else None)
    if not folder:
        exit(0)
    dfs, Ts, exp, asymptotes, actual_util = load_experiment_data(folder, n_cores=2048)

    return dfs, Ts, exp, asymptotes, actual_util


if __name__ == "__main__":
    main()
