#!/usr/bin/env python3
"""
Generate policy behavior scenario diagrams showing how different scheduling
policies allocate jobs to servers in a unified example scenario.
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from pathlib import Path

# Plot configuration
plt.rc("font", **{"family": "serif", "serif": ["Palatino"]})
plt.rc("text", usetex=True)
matplotlib.rcParams["font.size"] = 12


def get_job_color_by_size(cores):
    """
    Return a unique color for each specific core requirement.
    Colors chosen to be distinguishable in both color and grayscale printing.
    """
    # Color palette with varying luminance for grayscale distinction
    color_map = {
        1: "#FFFFCC",  # Very light yellow (lightest - ~95% gray)
        2: "#B3E5B3",  # Light green (~75% gray)
        3: "#80B3FF",  # Medium blue (~60% gray)
        4: "#9370DB",  # Medium purple (~50% gray)
        5: "#CC6666",  # Dark red-orange (~40% gray)
        6: "#FF9933",  # Orange (~65% gray)
        7: "#66CCCC",  # Cyan (~70% gray)
        8: "#D966D9",  # Pink (~55% gray)
        9: "#99CC99",  # Medium green (~68% gray)
        10: "#6666B3", # Deep purple-blue (~35% gray)
    }

    # Return color for specific core count, or a default for larger values
    return color_map.get(cores, "#808080")  # Medium gray as default


def darken_color(hex_color, factor=0.8):
    """
    Darken a hex color by multiplying RGB values by a factor.
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    # Convert to RGB
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    # Darken
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    # Convert back to hex
    return f'#{r:02x}{g:02x}{b:02x}'


def draw_queue(ax, all_jobs, queue_x=1, allocated_jobs=None):
    """
    Draw the job queue on the left side, vertically arranged.
    Each job box contains small circles representing core demand.
    First-arrived job is rightmost (closest to servers).

    Parameters:
    - ax: matplotlib axis
    - all_jobs: list of (job_id, n_cores) tuples in arrival order
    - queue_x: x-position for the queue area
    - allocated_jobs: set of job IDs that are currently allocated to servers
    """
    if allocated_jobs is None:
        allocated_jobs = set()

    # Reverse jobs so first-arrived is on the right
    reversed_jobs = list(reversed(all_jobs))

    job_width = 1.2  # Match the width of server job boxes
    x_spacing = 1.5  # Spacing between queue items

    # Server spacing parameters (must match server drawing)
    server_spacing = 1.3
    server_radius = 0.4
    circle_radius = 0.3  # Slightly smaller circles inside queue boxes

    # Calculate max height for centering (based on server spacing)
    max_cores = max(cores for _, cores in all_jobs)
    max_height = (max_cores - 1) * server_spacing + 2 * server_radius * 1.3
    center_y = max_height / 2

    # Find bounds for queue border
    min_x = queue_x - job_width/2
    max_x = queue_x + (len(reversed_jobs) - 1) * x_spacing + job_width/2
    min_y = center_y - max_height / 2 - 0.3
    max_y = center_y + max_height / 2 + 0.3

    # Draw queue border
    queue_border = Rectangle((min_x - 0.3, min_y), max_x - min_x + 0.6, max_y - min_y,
                             facecolor="none", edgecolor="#BDBDBD", linewidth=4,
                             linestyle="--", alpha=0.5)
    ax.add_patch(queue_border)

    # Add "Queue" label above the border
    center_x_queue = (min_x - 0.3 + max_x + 0.3) / 2
    ax.text(center_x_queue, max_y + 0.3, "Queue", fontsize=28, fontweight="bold",
           ha="center", va="bottom")

    for idx, (job_id, cores) in enumerate(reversed_jobs):
        color = get_job_color_by_size(cores)
        border_color = darken_color(color)

        # Job height matching server spacing
        job_height = (cores - 1) * server_spacing + 2 * server_radius * 1.3

        x_pos = queue_x + idx * x_spacing
        # Center vertically
        y_pos = center_y - job_height / 2

        # Use dashed border if job is allocated to servers
        linestyle = "--" if job_id in allocated_jobs else "-"

        # Draw job rectangle (vertical bar) with rounded corners
        rect = FancyBboxPatch((x_pos - job_width/2, y_pos), job_width, job_height,
                             boxstyle="round,pad=0.05",
                             facecolor=color, edgecolor=border_color, linewidth=6,
                             linestyle=linestyle, alpha=0.7)
        ax.add_patch(rect)

        # Draw circles inside the box representing core demand
        circle_spacing = server_spacing  # Match server spacing
        total_circle_height = (cores - 1) * circle_spacing
        circle_base_y = center_y - total_circle_height / 2
        for c in range(cores):
            cy = circle_base_y + c * circle_spacing
            circle = plt.Circle((x_pos, cy), circle_radius,
                              facecolor="white", edgecolor=border_color,
                              linewidth=2.5, zorder=5, alpha=0.9)
            ax.add_patch(circle)

        # Job label above the box
        ax.text(x_pos, y_pos + job_height + 0.25, f"{job_id}",
               ha="center", va="bottom", fontsize=28, fontweight="bold")


def draw_allocated_jobs_with_servers(ax, allocations, n_servers=6, n_occupied_existing=2):
    """
    Draw servers as circles arranged vertically on the right side.
    Occupied servers at the top. Allocated jobs shown as boxes spanning servers.

    Parameters:
    - ax: matplotlib axis
    - allocations: list of server allocations per server
    - n_servers: total number of servers
    - n_occupied_existing: number of servers occupied by existing jobs
    """
    # First, reorganize data: for each job, collect which servers it occupies
    job_to_servers = {}
    for server_idx, server_jobs in enumerate(allocations):
        for job_data in server_jobs:
            # Handle both (job_id, cores) and (job_id, cores, color) formats
            if len(job_data) >= 2:
                job_id, cores = job_data[0], job_data[1]
            else:
                continue

            if job_id not in job_to_servers:
                job_to_servers[job_id] = {"cores": cores, "servers": []}
            job_to_servers[job_id]["servers"].append(server_idx)

    # Draw all servers vertically on the right
    server_radius = 0.4
    server_spacing = 1.3
    server_x = 11
    base_y = 0

    server_positions = {}
    # Servers arranged from top (0) to bottom (n_servers-1)
    for server_idx in range(n_servers):
        y_pos = base_y + (n_servers - 1 - server_idx) * server_spacing
        server_positions[server_idx] = (server_x, y_pos)

        # Check if server is occupied by existing job (first n_occupied_existing servers)
        is_existing = server_idx < n_occupied_existing

        # Check if server is newly allocated to a job from queue
        is_newly_allocated = any(server_idx in job_data["servers"]
                                for job_data in job_to_servers.values())

        if is_existing:
            server_color = "#757575"  # Dark gray for existing occupied
            edge_color = "black"
            linewidth = 5
        elif is_newly_allocated:
            server_color = "#BDBDBD"  # Light gray, will be redrawn white inside job box
            edge_color = "black"
            linewidth = 4
        else:
            server_color = "#E0E0E0"  # Very light gray for idle
            edge_color = "#9E9E9E"
            linewidth = 4

        # Draw server circle
        circle = plt.Circle((server_x, y_pos), server_radius,
                          facecolor=server_color, edgecolor=edge_color,
                          linewidth=linewidth, zorder=1)
        ax.add_patch(circle)

    # Draw server area border
    top_server_y = server_positions[0][1]
    bottom_server_y = server_positions[n_servers - 1][1]
    server_border_x = server_x - server_radius - 0.8
    server_border_width = 2 * server_radius + 1.6
    server_border_y = bottom_server_y - server_radius - 0.3
    server_border_height = top_server_y - bottom_server_y + 2 * server_radius + 0.6

    server_border = Rectangle((server_border_x, server_border_y),
                              server_border_width, server_border_height,
                              facecolor="none", edgecolor="#BDBDBD", linewidth=4,
                              linestyle="--", alpha=0.5, zorder=0)
    ax.add_patch(server_border)

    # Add "Server" label above the border
    center_x_server = server_border_x + server_border_width / 2
    ax.text(center_x_server, server_border_y + server_border_height + 0.3, "Server",
           fontsize=28, fontweight="bold", ha="center", va="bottom")

    # Draw jobs as boxes overlaying the servers they occupy
    for job_id in sorted(job_to_servers.keys()):
        job_data = job_to_servers[job_id]
        cores = job_data["cores"]
        servers = job_data["servers"]

        if not servers:
            continue

        color = get_job_color_by_size(cores)
        border_color = darken_color(color)

        # Calculate job box dimensions (vertical span)
        min_server = min(servers)
        max_server = max(servers)

        top_y = server_positions[min_server][1] + server_radius * 1.3
        bottom_y = server_positions[max_server][1] - server_radius * 1.3
        job_height = top_y - bottom_y

        job_width = 1.2
        job_x_pos = server_x - job_width/2

        # Draw job box
        job_rect = FancyBboxPatch((job_x_pos, bottom_y), job_width, job_height,
                                 boxstyle="round,pad=0.05",
                                 facecolor=color, edgecolor=border_color,
                                 linewidth=6, alpha=0.6, zorder=3)
        ax.add_patch(job_rect)

        # Redraw server circles that are inside this job
        for server_idx in servers:
            x_pos, y_pos = server_positions[server_idx]
            circle = plt.Circle((x_pos, y_pos), server_radius,
                              facecolor="white", edgecolor="black",
                              linewidth=4, zorder=4)
            ax.add_patch(circle)

        # Job label to the left of the box
        center_y = (top_y + bottom_y) / 2
        ax.text(job_x_pos - 0.3, center_y, f"{job_id}",
               ha="right", va="center", fontsize=28, fontweight="bold",
               bbox=dict(boxstyle="round,pad=0.3", facecolor=color,
                        edgecolor=border_color, alpha=0.8, linewidth=4))


def create_scenario_plot(policy_name, allocations, all_jobs, output_path, n_servers=6, n_cores=10):
    """
    Create a visualization of how a policy allocates jobs to servers.
    Layout: Queue on left (vertical bars), Servers on right (vertical circles).

    Parameters:
    - policy_name: Name of the scheduling policy
    - allocations: list of server allocations (one per server)
    - all_jobs: list of (job_id, n_cores) tuples for the queue
    - output_path: where to save the plot
    - n_servers: number of servers to show
    - n_cores: cores per server
    """
    fig, ax = plt.subplots(figsize=(14, 8))

    # Extract job IDs that are allocated to servers
    allocated_jobs = set()
    for server_jobs in allocations:
        for job_data in server_jobs:
            if len(job_data) >= 1:
                allocated_jobs.add(job_data[0])

    # Draw the job queue on the left
    draw_queue(ax, all_jobs, queue_x=1, allocated_jobs=allocated_jobs)

    # Draw servers and allocated jobs on the right
    draw_allocated_jobs_with_servers(ax, allocations, n_servers, n_occupied_existing=2)

    # Draw flow arrow between queue and servers
    server_spacing = 1.3
    center_y = ((n_servers - 1) * server_spacing) / 2
    # Arrow from right edge of queue area to left edge of server area
    max_queue_x = 1 + (len(all_jobs) - 1) * 1.5 + 0.6 + 0.3  # queue right edge
    server_left_x = 11 - 0.4 - 0.8  # server border left edge
    arrow_x_start = max_queue_x + 0.2
    arrow_x_end = server_left_x - 0.2
    ax.annotate("", xy=(arrow_x_end, center_y), xytext=(arrow_x_start, center_y),
                arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.3",
                                lw=4, color="#666666"))

    # Configure axes
    ax.set_xlim(-1, 14)
    ax.set_ylim(-1.5, 7.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{policy_name}", fontsize=40, fontweight="bold", pad=10)

    plt.tight_layout()

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved {policy_name} scenario to {output_path}")
    plt.close()


def plot_fifo_scenario():
    """
    FIFO: Unified scenario - waits for Job A (head-of-line blocking).
    Queue: A(5), B(2), C(2), D(1), E(4). 4 servers idle, 2 occupied.
    FIFO admits nothing because Job A needs 5 servers but only 4 are available.
    """
    # Unified scenario queue (in arrival order)
    all_jobs = [("A", 5), ("B", 2), ("C", 2), ("D", 1), ("E", 4)]

    # No new jobs admitted - all 4 idle servers remain idle
    # Servers 0-1 are occupied by existing jobs (not shown)
    # Servers 2-5 are idle
    allocations = [
        [],  # Server 1: occupied by existing job
        [],  # Server 2: occupied by existing job
        [],  # Server 3: idle (FIFO waits for Job A)
        [],  # Server 4: idle
        [],  # Server 5: idle
        [],  # Server 6: idle
    ]

    output_path = Path("../tesi/figures/policy-fifo-scenario.pdf")
    create_scenario_plot("First-In First-Out (FIFO)", allocations, all_jobs, output_path, n_servers=6)


def plot_smash_w2_scenario():
    """
    SMASH (w=2): Unified scenario with window size 2.
    First iteration: examines A, B. Admits B (2 servers), s=2 remaining.
    Second iteration: examines A, C. Admits C (2 servers), s=0 remaining.
    """
    all_jobs = [("A", 5), ("B", 2), ("C", 2), ("D", 1), ("E", 4)]

    # Servers 0-1: occupied by existing jobs
    # Servers 2-3: admit Job B (2 servers)
    # Servers 4-5: admit Job C (2 servers)
    allocations = [
        [],  # Server 1: occupied by existing job
        [],  # Server 2: occupied by existing job
        [("B", 2)],  # Server 3: Job B
        [("B", 2)],  # Server 4: Job B
        [("C", 2)],  # Server 5: Job C
        [("C", 2)],  # Server 6: Job C
    ]

    output_path = Path("../tesi/figures/policy-smash-w2-scenario.pdf")
    create_scenario_plot("SMASH (w=2)", allocations, all_jobs, output_path, n_servers=6)


def plot_smash_w5_scenario():
    """
    SMASH (w=5): Unified scenario with window size 5.
    Examines all 5 jobs. Among feasible (B, C, D, E), E is largest.
    Admits Job E (4 servers), s=0 remaining.
    """
    all_jobs = [("A", 5), ("B", 2), ("C", 2), ("D", 1), ("E", 4)]

    # Servers 0-1: occupied by existing jobs
    # Servers 2-5: admit Job E (4 servers)
    allocations = [
        [],  # Server 1: occupied by existing job
        [],  # Server 2: occupied by existing job
        [("E", 4)],  # Server 3: Job E
        [("E", 4)],  # Server 4: Job E
        [("E", 4)],  # Server 5: Job E
        [("E", 4)],  # Server 6: Job E
    ]

    output_path = Path("../tesi/figures/policy-smash-w5-scenario.pdf")
    create_scenario_plot("SMASH (w=5)", allocations, all_jobs, output_path, n_servers=6)


def plot_server_filling_scenario():
    """
    Server Filling: Unified scenario - preemptive reallocation.
    Working set: {X(2) in-service, A(5) from queue}. Total = 7 ≥ 6.
    Sorted: {A(5), X(2)}. Reallocation: A(5) admitted, X(2) preempted.
    Result: A occupies 5 servers, X preempted and returns to queue, 1 idle server.
    """
    all_jobs = [("X", 2), ("A", 5), ("B", 2), ("C", 2), ("D", 1), ("E", 4)]

    # After reallocation: Job A occupies servers 0-4, server 5 is idle
    # The existing job X that was on servers 0-1 has been preempted and returns to the queue
    allocations = [
        [("A", 5)],  # Server 0: Job A
        [("A", 5)],  # Server 1: Job A
        [("A", 5)],  # Server 2: Job A
        [("A", 5)],  # Server 3: Job A
        [("A", 5)],  # Server 4: Job A
        [],          # Server 5: idle (was occupied, now freed after preemption)
    ]

    output_path = Path("../tesi/figures/policy-serverfilling-scenario.pdf")
    create_scenario_plot("Server Filling", allocations, all_jobs, output_path, n_servers=6)


def plot_backfilling_scenario():
    """
    Back Filling: Unified scenario - reserves Job A, conditionally admits Job E.
    Computes reservation for Job A (5 servers needed).
    Conditionally admits Job E (4 servers) if it won't delay Job A's reservation.
    """
    all_jobs = [("A", 5), ("B", 2), ("C", 2), ("D", 1), ("E", 4)]

    # Servers 0-1: occupied by existing jobs
    # Servers 2-5: admit Job E (4 servers) if service times allow
    allocations = [
        [],  # Server 1: occupied by existing job
        [],  # Server 2: occupied by existing job
        [("E", 4)],  # Server 3: Job E (conditional)
        [("E", 4)],  # Server 4: Job E (conditional)
        [("E", 4)],  # Server 5: Job E (conditional)
        [("E", 4)],  # Server 6: Job E (conditional)
    ]

    output_path = Path("../tesi/figures/policy-backfilling-scenario.pdf")
    create_scenario_plot("Back Filling", allocations, all_jobs, output_path, n_servers=6)


def plot_msf_scenario():
    """
    Most Server First (MSF): Unified scenario - admits largest feasible job.
    Among feasible jobs (B, C, D, E), Job E is largest (4 servers).
    """
    all_jobs = [("A", 5), ("B", 2), ("C", 2), ("D", 1), ("E", 4)]

    # Servers 0-1: occupied by existing jobs
    # Servers 2-5: admit Job E (4 servers)
    allocations = [
        [],  # Server 1: occupied by existing job
        [],  # Server 2: occupied by existing job
        [("E", 4)],  # Server 3: Job E
        [("E", 4)],  # Server 4: Job E
        [("E", 4)],  # Server 5: Job E
        [("E", 4)],  # Server 6: Job E
    ]

    output_path = Path("../tesi/figures/policy-msf-scenario.pdf")
    create_scenario_plot("Most Server First (MSF)", allocations, all_jobs, output_path, n_servers=6)


if __name__ == "__main__":
    print("Generating policy scenario diagrams...")
    plot_fifo_scenario()
    plot_smash_w2_scenario()
    plot_smash_w5_scenario()
    plot_server_filling_scenario()
    plot_backfilling_scenario()
    plot_msf_scenario()
    print("All policy scenarios generated successfully!")
