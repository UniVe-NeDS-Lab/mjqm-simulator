---
title: SMASH Window Size Comparison
tags:
  - examples
---

# SMASH window size comparison

Compare SMASH behaviour across different window sizes.

## Configuration

```toml
identifier = "smash_window_comparison"
events = 1000000
repetitions = 30
cores = 128

arrival.distribution = "exponential"
service.distribution = "exponential"

[[class]]
cores = 1
arrival.prob = 0.6
service.mean = 0.5

[[class]]
cores = 4
arrival.prob = 0.3
service.mean = 1.0

[[class]]
cores = 16
arrival.prob = 0.1
service.mean = 2.0

# Test multiple arrival rates
[[pivot]]
arrival.rate = [10, 20, 30, 40, 50, 60]

# Compare SMASH with different window sizes
policy = [
    { name = "smash", window = 1 },  # Equivalent to FIFO
    { name = "smash", window = 2 },
    { name = "smash", window = 5 },
    { name = "smash", window = 10 },
    { name = "smash", window = 0 }   # Unlimited window
]
```

## What this tests

- **Window size impact**: From strict FIFO (w=1) to unlimited lookahead (w=0)
- **Fairness vs efficiency**: Larger windows improve utilization but may starve large jobs
- **Service time heterogeneity**: Large jobs have 4× the service time of small jobs
- **Load progression**: From 10 jobs/time to 60 jobs/time (light to high load)

## Expected behaviour

As window size increases:

- **Waiting times decrease**: Larger lookahead enables better resource matching
- **Utilization improves**: Less fragmentation, fewer idle servers
- **FIFO violations increase**: More jobs admitted out of arrival order
- **Large job waiting times may increase**: Risk of starvation under heavy load

**Window = 1 (FIFO)**: Strict fairness, potential head-of-line blocking, limited by server fragmentation.

**Window = 2-5**: Modest lookahead, balance between fairness and efficiency, suitable for most workloads.

**Window = 10**: Aggressive scheduling, high utilization, increased risk of large job starvation.

**Window = 0 (unlimited)**: Full-queue lookahead; behaviour converges towards Most Server First.

## Key metrics to examine

- **Mean waiting time**: Should decrease with larger windows
- **Per-class waiting time**: Compare T1 vs T16 to assess fairness
- **FIFO violations**: Count of out-of-order admissions
- **Stability boundary**: Arrival rate where each policy becomes unstable

## Running the experiment

1. Save this configuration to `Inputs/smash_window_comparison.toml`
2. Run: `./simulator smash_window_comparison`
3. Results will generate 30 output files (6 arrival rates × 5 window sizes)

## Interpreting results

Plot mean waiting time vs arrival rate for each window size to visualize the trade-off:

- Look for the "knee" in each curve (stability boundary)
- Compare per-class metrics to assess fairness impact
- Check violation counters to quantify reordering frequency

The effect of the window size depends on the workload; use per-class waiting times and the CV to quantify the impact.
