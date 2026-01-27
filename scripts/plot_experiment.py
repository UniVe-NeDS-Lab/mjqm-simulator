#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  7 16:21:22 2024

@author: dilettaolliaro
"""

import math
import sys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from load_experiment_data import load_experiment_data, select_experiment
from scipy.signal import savgol_filter
from tqdm import tqdm

################################ PANDAS AND PLOT CONFIGS ################################
fsize = 150
legend_size = 200
label_size = 220
title_size = 195
tuplesize = (90, 70)
marker_size = 70**2
line_size = 25
tick_size = 180
l_pad = 40
asym_size = 20

cols = [
    "black",
    "peru",
    "darkorange",
    "royalblue",
    "crimson",
    "purple",
    "darkgreen",
    "pink",
    "brown",
    "gray",
    "orange",
]
markers = ["P", "o", "v", "s", "X", "D", "H", "<", ">", "x", "p"]
markers_plotly = [
    "cross",
    "circle",
    "triangle-down",
    "square",
    "x",
    "diamond",
    "triangle-up",
    "triangle-left",
    "triangle-right",
    "star",
    "star-triangle-up",
]
styles = ["solid", "dashdot", "dotted", "dashed", (0, (3, 5, 1, 5, 1, 5))]

cell = "cellA"
n_cores = 4096

cell = "cellB"
n_cores = 2048
# -3 : backfilling
# -2 : server filling
# 0: Most Server First
# 1: First-In First-Out
# i: SMASH w/ w=i

if cell == "cellB":
    ys_bigResp = [7000, 5000, 3000, 500, 700, 1000, 2000]
    ys_resp = [2500, 750, 450, 15, 40, 100, 250]

    """
    ys_bigResp = [700, 6000, 4700, 1000, 3000]
    ys_resp = [800, 550, 350, 7, 40]"""

    xs = [5.4, 5.4, 5.4, 5.4, 5.4, 5.4, 5.4, 5.4, 5.4]
    legend_locs = [
        "upper left",
        "upper left",
        "lower left",
        "upper left",
        "upper left",
        "lower right",
    ]

    ylims_totResp = [5, 10000]
    ylims_totWait = [0.01, 10**5]
    ylims_bigResp = [100, 10000]
    ylims_smallResp = [1, 10000]
    ylims_smallWait = [0.01, 10000]

    ylims = [0.1, 10**5]
    ylims_v2 = [0.1, 10**5]

    xlims = [0.01, 10]
    st = styles[0]

elif cell == "cellA":
    if n_cores == 4096:
        # ys_bigResp = [550, 400, 7, 15, 40, 100, 170, 200]
        # ys_resp = [70, 50, 4, 6, 8, 10, 25, 35]

        ys_bigResp = [550, 350, 400, 7, 15, 40, 100]
        ys_resp = [40, 30, 50, 2, 5, 8, 11]

        """
        types = [0 for i in range(20)]
        ys_bigResp = [650, 550, 400, 7, 40]
        ys_resp = [100, 70, 50, 4, 8]
        """

        xs = [725 for w in range(20)]
        # xs = [602, 739, 561, 614, 667, 711]

        ylims_totResp = [1, 100]
        ylims_totWait = [10**-3, 100]
        ylims_bigResp = [1, 1000]
        ylims_smallResp = [1, 100]
        ylims_smallWait = [10**-3, 100]
        legend_locs = [
            "upper left",
            "upper left",
            "lower left",
            "upper left",
            "upper left",
            "lower center",
        ]
        ylims = [1, 10**4]
        ylims_v2 = [0.001, 1000]

        xlims = [100, 10**3]
        st = styles[0]
    elif n_cores == 3072:
        ys_bigResp = [800, 500, 20, 60, 120, 240]
        ys_resp = [10000, 6000, 200, 400, 800, 1400]

        xs = [370 for i in range(20)]
        # xs = [602, 739, 561, 614, 667, 711]

        ylims_totResp = [1, 100]
        ylims_totWait = [10**-3, 100]
        ylims_bigResp = [1, 1000]
        ylims_smallResp = [1, 100]
        ylims_smallWait = [10**-3, 100]

        ylims = [1, 10**4]
        ylims_v2 = [0.001, 1000]

        xlims = [100, 10**3]
        st = styles[0]
    elif n_cores == 2048:
        ys_bigResp = [800]
        ys_resp = [1000]

        xs = [50 for i in range(20)]
        # xs = [602, 739, 561, 614, 667, 711]

        ylims_totResp = [0.001, 100]
        ylims_totWait = [0.001, 100]
        ylims_bigResp = [0.001, 1000]
        ylims_smallResp = [0.001, 100]
        ylims_smallWait = [0.001, 100]

        ylims = [0.001, 10**4]
        ylims_v2 = [0.001, 1000]

        xlims = [1, 500]
        xlims_big = [1, 30]
        st = styles[0]


############################### PLOT UTILITIES ###############################


def prepare_cosmetics(dfs, exp):
    policy_groups = dfs.groupby(level=exp).groups.keys()
    # per each group, create a df with colors and markers
    colors = pd.Series(
        dtype=pd.api.types.CategoricalDtype(categories=cols, ordered=True),
        name="color",
    )
    marks = pd.Series(
        dtype=pd.api.types.CategoricalDtype(categories=markers, ordered=True),
        name="marker",
    )
    marks_plotly = pd.Series(
        dtype=pd.api.types.CategoricalDtype(
            categories=markers_plotly, ordered=True
        ),
        name="marker_plotly",
    )
    i = 0
    for group in policy_groups:
        colors[group] = cols[i]
        marks[group] = markers[i]
        marks_plotly[group] = markers_plotly[i]
        i += 1

    return colors, marks, marks_plotly


def add_legend(ax, legend):
    if legend:
        if isinstance(legend, tuple) or isinstance(legend, list):
            legend = legend[0]
            ncol = legend[1]
        else:
            ncol = 1
        ax.legend(fontsize=legend_size, loc=legend, ncol=ncol)


def add_utilisation_labels(
    ax, policy_groups, xs, ys, actual_util, util_percentages
):
    i = 0
    for idx, df_select in policy_groups:
        f, i = i, i + 1
        if util_percentages:
            plt.text(
                x=xs[f],
                y=ys[f],
                s=f"{actual_util[idx]:.1f}\\%",
                rotation=0,
                c=colors[idx],
                fontsize=tick_size,
                weight="extra bold",
            )
        ax.axvline(
            x=asymptotes[idx],
            color=colors[idx],
            linestyle="dotted",
            lw=asym_size,
        )


def compute_limits(ax, ylims, ns):
    ax.set_yscale("log")
    if ylims:
        ax.set_ylim(*ylims)
    ymin, ymax = ax.get_ylim()
    skip = (16 - ns) // 2

    ax.set_xscale("log")
    ax.set_xmargin(0)
    # print("xbounds =", ax.get_xbound())
    xmin, xmax = ax.get_xbound()
    ax.set_xlim(xmin, 10 ** math.ceil(math.log10(xmax)))
    # print("xbounds =", ax.get_xbound())

    return np.geomspace(ymin, ymax, num=16, endpoint=False)[-skip::-1]


def save_files(fig, folder, basename: str, formats):
    if "png" in formats or "pdf" in formats:
        folder.mkdir(parents=True, exist_ok=True)
        if "pdf" in formats:
            fig.savefig(folder / f"{basename}.pdf", bbox_inches="tight")
        if "png" in formats:
            fig.savefig(folder / f"{basename}.png", bbox_inches="tight")


############################# TOTAL RESPONSE TIME #############################


def plot_total_response_time(
    folder,
    dfs,
    exp,
    actual_util,
    asymptotes,
    ylims=None,
    legend=None,
    util_percentages=True,
    result=[],
):
    plt.figure(dpi=1200)
    plt.rc("font", **{"family": "serif", "serif": ["Palatino"]})
    plt.rc("text", usetex=True)
    matplotlib.rcParams["font.size"] = fsize
    matplotlib.rcParams["xtick.major.pad"] = 8
    matplotlib.rcParams["ytick.major.pad"] = 8
    fig, ax = plt.subplots(figsize=tuplesize)

    policy_groups = dfs.groupby(level=exp)
    for idx, df_select in policy_groups:
        x_data = df_select["arrival.rate"][df_select["stable"]]
        y_data = df_select["RespTime Total"][df_select["stable"]]
        y_interp = savgol_filter(y_data, 3, 2)

        ax.scatter(
            x_data, y_data, color=colors[idx], marker=marks[idx], s=marker_size
        )
        ax.plot(
            x_data,
            y_interp,
            color=colors[idx],
            label=str(idx),
            ls=st,
            lw=line_size,
        )

    ys = compute_limits(ax, ylims, policy_groups.ngroups)
    add_utilisation_labels(
        ax, policy_groups, xs, ys, actual_util, util_percentages
    )

    ax.set_xlabel("Arrival Rate $\\quad[$s$^{-1}]$", fontsize=label_size)
    ax.set_ylabel("Avg. Response Time $\\quad[$s$]$", fontsize=label_size)
    ax.set_title(
        "Avg. Overall Response Time vs. Arrival Rate", fontsize=title_size
    )
    ax.tick_params(axis="both", which="major", labelsize=tick_size, pad=l_pad)
    ax.tick_params(axis="both", which="minor", labelsize=tick_size, pad=l_pad)
    add_legend(ax, legend)
    ax.grid()
    save_files(fig, folder / "RespTime", "lambdasVsTotRespTime", result)
    if "return" in result:
        return fig, ax
    plt.close("all")


########################## SMALL CLASS RESPONSE TIME ##########################


def plot_class_response_time(
    folder,
    dfs,
    exp,
    T,
    actual_util,
    asymptotes,
    ylims=None,
    legend=None,
    util_percentages=True,
    result=[],
):
    plt.figure(dpi=1200)
    plt.rc("font", **{"family": "serif", "serif": ["Palatino"]})
    plt.rc("text", usetex=True)
    matplotlib.rcParams["font.size"] = fsize
    fig, ax = plt.subplots(figsize=tuplesize)

    policy_groups = dfs.groupby(level=exp)
    for idx, df_select in policy_groups:
        x_data = df_select["arrival.rate"][df_select["stable"]]
        y_data = df_select[f"T{T} RespTime"][df_select["stable"]]
        y_interp = savgol_filter(y_data, 3, 2)

        ax.scatter(
            x_data, y_data, color=colors[idx], marker=marks[idx], s=marker_size
        )
        ax.plot(
            x_data,
            y_interp,
            color=colors[idx],
            label=str(idx),
            ls=st,
            lw=line_size,
        )

    ys = compute_limits(ax, ylims, policy_groups.ngroups)
    add_utilisation_labels(
        ax, policy_groups, xs, ys, actual_util, util_percentages
    )

    ax.set_xlabel("Arrival Rate $\\quad[$s$^{-1}]$", fontsize=label_size)
    ax.set_ylabel("Avg. Response Time $\\quad[$s$]$", fontsize=label_size)
    ax.set_title(
        f"Avg. Response Time for Class ${T}$ vs. Arrival Rate",
        fontsize=title_size,
    )
    ax.tick_params(axis="both", which="major", labelsize=tick_size, pad=l_pad)
    ax.tick_params(axis="both", which="minor", labelsize=tick_size, pad=l_pad)

    add_legend(ax, legend)

    ax.grid()
    save_files(fig, folder / "RespTime", f"lambdasVsT{T}RespTime", result)
    if "return" in result or len(result) == 0:
        return fig, ax
    plt.close("all")


############################## TOTAL WAITING TIME ##############################


def plot_total_waiting_time(
    folder,
    dfs,
    exp,
    actual_util,
    asymptotes,
    ylims=None,
    legend=None,
    util_percentages=True,
    result=[],
):
    plt.figure(dpi=1200)
    plt.rc("font", **{"family": "serif", "serif": ["Palatino"]})
    plt.rc("text", usetex=True)
    matplotlib.rcParams["font.size"] = fsize
    matplotlib.rcParams["xtick.major.pad"] = 8
    matplotlib.rcParams["ytick.major.pad"] = 8
    fig, ax = plt.subplots(figsize=tuplesize)

    policy_groups = dfs.groupby(level=exp)
    for idx, df_select in policy_groups:
        x_data = df_select["arrival.rate"][df_select["stable"]]
        y_data = df_select["WaitTime Total"][df_select["stable"]]
        y_interp = savgol_filter(y_data, 3, 2)

        ax.scatter(
            x_data, y_data, color=colors[idx], marker=marks[idx], s=marker_size
        )
        ax.plot(
            x_data,
            y_interp,
            color=colors[idx],
            label=str(idx),
            ls=st,
            lw=line_size,
        )

    ys = compute_limits(ax, ylims, policy_groups.ngroups)
    add_utilisation_labels(
        ax, policy_groups, xs, ys, actual_util, util_percentages
    )

    ax.set_xlabel("Arrival Rate $\\quad[$s$^{-1}]$", fontsize=label_size)
    ax.set_ylabel("Avg. Waiting Time $\\quad[$s$]$", fontsize=label_size)
    ax.set_title(
        "Avg. Overall Waiting Time vs. Arrival Rate", fontsize=title_size
    )
    ax.tick_params(axis="both", which="major", labelsize=tick_size, pad=l_pad)
    ax.tick_params(axis="both", which="minor", labelsize=tick_size, pad=l_pad)
    add_legend(ax, legend)
    ax.grid()
    save_files(fig, folder / "WaitTime", "lambdasVsTotWaitTime", result)
    if "return" in result or len(result) == 0:
        return fig, ax
    plt.close("all")


########################### SMALL CLASS WAITING TIME ###########################


def plot_class_waiting_time(
    folder,
    dfs,
    exp,
    T,
    actual_util,
    asymptotes,
    ylims=None,
    legend=None,
    util_percentages=True,
    result=[],
):
    plt.figure(dpi=1200)
    plt.rc("font", **{"family": "serif", "serif": ["Palatino"]})
    plt.rc("text", usetex=True)
    matplotlib.rcParams["font.size"] = fsize
    fig, ax = plt.subplots(figsize=tuplesize)

    policy_groups = dfs.groupby(level=exp)
    for idx, df_select in policy_groups:
        x_data = df_select["arrival.rate"][df_select["stable"]]
        y_data = df_select[f"T{T} Waiting"][df_select["stable"]]
        y_interp = savgol_filter(y_data, 3, 2)

        ax.scatter(
            x_data, y_data, color=colors[idx], marker=marks[idx], s=marker_size
        )
        ax.plot(
            x_data,
            y_interp,
            color=colors[idx],
            label=str(idx),
            ls=st,
            lw=line_size,
        )

    ys = compute_limits(ax, ylims, policy_groups.ngroups)
    add_utilisation_labels(
        ax, policy_groups, xs, ys, actual_util, util_percentages
    )

    ax.set_xlabel("Arrival Rate $\\quad[$s$^{-1}]$", fontsize=label_size)
    ax.set_ylabel("Avg. Waiting Time $\\quad[$s$]$", fontsize=label_size)
    ax.set_title(
        f"Avg. Waiting Time for Class ${T}$ vs. Arrival Rate",
        fontsize=title_size,
    )
    ax.tick_params(axis="both", which="major", labelsize=tick_size, pad=l_pad)
    ax.tick_params(axis="both", which="minor", labelsize=tick_size, pad=l_pad)

    add_legend(ax, legend)

    ax.grid()
    save_files(fig, folder / "WaitTime", f"lambdasVsT{T}WaitTime", result)
    if "return" in result or len(result) == 0:
        return fig, ax
    plt.close("all")


################################################################################


if __name__ == "__main__":
    folder = select_experiment(sys.argv[1] if len(sys.argv) > 1 else None)
    if not folder:
        exit(0)
    dfs, Ts, exp, asymptotes, actual_util = load_experiment_data(
        folder, n_cores=n_cores
    )
    if dfs is None:
        exit(0)

    progress = tqdm(None, desc="Plotting", total=len(Ts) * 2 + 2)
    colors, marks, _ = prepare_cosmetics(dfs, exp)

    plot_total_response_time(
        folder,
        dfs,
        exp,
        actual_util,
        asymptotes,
        ylims=ylims_totResp,
        legend="upper left",
        result=["png", "pdf"],
    )
    progress.update(1)
    for T in Ts:
        plot_class_response_time(
            folder, dfs, exp, T, actual_util, asymptotes, result=["png", "pdf"]
        )
        progress.update(1)

    plot_total_waiting_time(
        folder,
        dfs,
        exp,
        actual_util,
        asymptotes,
        ylims=ylims_totWait,
        legend="upper left",
        result=["png", "pdf"],
    )
    progress.update(1)

    for T in Ts:
        plot_class_waiting_time(
            folder, dfs, exp, T, actual_util, asymptotes, result=["png", "pdf"]
        )
        progress.update(1)

    progress.close()
