---
title: Multi-Policy Comparison
tags:
  - examples
---

# Multi-policy comparison

Side-by-side comparison of six scheduling policies on the same workload.

## Configuration

```toml
identifier = "policy_comparison"
events = 2000000
repetitions = 40
cores = 256

arrival.distribution = "exponential"
service.distribution = "exponential"

[[class]]
cores = 1
arrival.prob = 0.5
service.mean = 0.2

[[class]]
cores = 2
arrival.prob = 0.3
service.mean = 0.5

[[class]]
cores = 8
arrival.prob = 0.15
service.mean = 1.0

[[class]]
cores = 32
arrival.prob = 0.05
service.mean = 3.0

# Test across operational range
[[pivot]]
arrival.rate = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]

# Compare representative policies
policy = [
    "fifo",
    "back filling",
    "server filling memoryful",
    "most server first",
    { name = "smash", window = 5 },
    { name = "quick swap", threshold = 128 }
]
```

## What this tests

This experiment compares six fundamentally different scheduling approaches:

1. **FIFO**: Strict arrival-order admission
2. **Back Filling**: Reservation for the head-of-line job; other jobs admitted only if they complete before the reservation
3. **Server Filling**: Working-set construction with reallocation and preemption
4. **Most Server First**: Admits the largest feasible job regardless of arrival order
5. **SMASH (w=5)**: Bounded lookahead window of 5 jobs
6. **Quick Swap (threshold=128)**: MSF with admission freeze when free servers reach the threshold and a largest-class job is waiting

## Workload characteristics

- **Moderate heterogeneity**: 32:1 ratio between largest and smallest jobs
- **Service time correlation**: Larger jobs have 15× longer service times
- **Realistic distribution**: 50% small jobs, 5% very large jobs
- **Broad load range**: From light (20 jobs/time) to potentially unstable (200 jobs/time)

## Expected performance characteristics

Performance depends heavily on workload heterogeneity and system parameters. General expectations:

### Load regimes

At low load (λ=20–40), all policies deliver comparable performance with negligible waiting times. Differences become visible as load increases — use per-class waiting times and Kleinrock's power metric to identify where each policy's stability boundary lies.

## Key metrics to compare

### Aggregate metrics

- **Mean waiting time**: Overall system responsiveness
- **Mean response time**: Including service time effects
- **Utilization at stability**: Maximum sustainable load
- **Queue length**: Congestion indicator

### Per-class metrics

- **Waiting time per class**: Fairness assessment
- **CV of waiting times**: Quantify disparity (coefficient of variation)
- **Max/min ratio**: Worst-treated vs best-treated class
- **Throughput per class**: Verify all classes are served

### Stability indicators

- **Kleinrock's Power Metric**: Throughput/response time ratio
- **Queue growth rate**: Linear vs super-linear
- **Waiting time slope**: Gradual vs explosive increase

## Running the experiment

1. Save this configuration to `Inputs/policy_comparison.toml`
2. Run: `./simulator_toml policy_comparison`
3. This generates 240 output files (10 arrival rates × 6 policies × 4 repetition groups)
4. Use the analysis dashboard or plotting tools to visualize results

## Analysis workflow

1. **Identify stability boundaries**: Find arrival rate where each policy's power metric peaks
2. **Compare at matched load**: Pick λ where all policies are stable (e.g., λ=80)
3. **Examine per-class fairness**: Plot waiting times for T1, T2, T8, T32 classes
4. **Assess trade-offs**: Balance stability, fairness, and aggregate performance

## What to look for

- **Stability boundaries**: At which arrival rate does each policy's power metric peak?
- **Per-class disparity**: How do T1 and T32 waiting times compare within each policy?
- **CV of per-class waiting times**: Which policies treat classes more uniformly?
