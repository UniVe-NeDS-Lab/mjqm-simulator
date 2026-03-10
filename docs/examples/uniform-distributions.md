---
title: Uniform Service Time Distributions
tags:
  - examples
---

# Uniform service time distributions

Example using uniform service time distributions instead of exponential, with varied server requirements.

## Configuration

```toml
identifier = "uniform_service_times"
events = 500000
repetitions = 25
cores = 1024

policy = "most server first"

arrival.distribution = "exponential"
service.distribution = "uniform"

[[class]]
cores = 1
arrival.prob = 0.8
service.min = 0.1
service.max = 0.5

[[class]]
cores = 4
arrival.prob = 0.15
service.min = 0.5
service.max = 2.0

[[class]]
cores = 16
arrival.prob = 0.04
service.min = 1.0
service.max = 5.0

[[class]]
cores = 128
arrival.prob = 0.01
service.min = 3.0
service.max = 10.0

[[pivot]]
arrival.rate = [10, 30, 50, 70, 90, 110, 130, 150]
```

## What this tests

- **Uniform vs exponential service times**: Bounded service duration instead of memoryless distribution
- **High server capacity**: 1024 cores enables large-scale scenarios
- **Extreme heterogeneity**: 128:1 ratio between largest and smallest jobs
- **Realistic variance**: Service times vary 100× between classes

## Why uniform distributions?

Uniform distributions are useful when:

- **Bounded service times**: Jobs have minimum and maximum duration guarantees
- **Less variability**: Compared to exponential (CV=1), uniform has lower coefficient of variation
- **Predictable behaviour**: No extremely long service times as in exponential tail
- **Modelling batch jobs**: Many HPC workloads have relatively bounded runtimes

## Service time characteristics

Each class has different service time ranges:

- **T1** (1 core): [0.1, 0.5] time units, mean = 0.3
- **T4** (4 cores): [0.5, 2.0] time units, mean = 1.25
- **T16** (16 cores): [1.0, 5.0] time units, mean = 3.0
- **T128** (128 cores): [3.0, 10.0] time units, mean = 6.5

Mean service time increases with job size, but variance is bounded.

## Expected behaviour differences

Compared to exponential service times:

### Lower variance in response time

Uniform distributions have CV ≈ 0.29 vs exponential CV = 1.0. This means:

- More predictable response times
- Fewer extreme outliers
- Tighter confidence intervals

### Different queueing dynamics

Without exponential's memoryless property:

- Remaining service time depends on elapsed time
- Less probability of very long service times
- Different stability characteristics

### Policy impact

This example uses Most Server First, which admits the largest feasible job at each scheduling event regardless of arrival order. With bounded service times, fragmentation patterns differ from the exponential case.

## Comparing to exponential

Run the same configuration with exponential distributions:

```toml
service.distribution = "exponential"

[[class]]
cores = 1
arrival.prob = 0.8
service.mean = 0.3

[[class]]
cores = 4
arrival.prob = 0.15
service.mean = 1.25

[[class]]
cores = 16
arrival.prob = 0.04
service.mean = 3.0

[[class]]
cores = 128
arrival.prob = 0.01
service.mean = 6.5
```

Then compare:

- **Waiting times**: Likely lower with uniform due to reduced variance
- **Queue lengths**: More stable with uniform
- **Utilization**: Similar across both
- **Stability boundary**: May differ slightly

## Running the experiment

1. Save this configuration to `Inputs/uniform_service_times.toml`
2. Run: `./simulator_toml uniform_service_times`
3. Results will show performance across 8 arrival rates

## Advanced experiment: Distribution comparison

Create a pivot over both policy and distribution:

```toml
[[pivot]]
arrival.rate = [10, 30, 50, 70, 90, 110, 130, 150]

policy = ["fifo", "most server first", "back filling"]

# Define both distribution variants
[[pivot]]
service.distribution = ["uniform", "exponential"]
# Requires conditional parameter setting (advanced configuration)
```

This reveals how service time distribution interacts with scheduling policy choice.

## Key observations

- **Uniform reduces variance**: CV ≈ 0.29 versus 1.0 for exponential, leading to tighter confidence intervals
- **Exponential models memoryless service**: Remaining service time is independent of elapsed time
- **Uniform models bounded jobs**: Service duration falls within a known range

## Practical applications

Use uniform distributions when modelling:

- **Batch processing systems**: Jobs with estimated runtimes
- **Container orchestration**: Tasks with resource limits including time
- **Real-time systems**: Worst-case execution time bounds
- **Synthetic benchmarks**: Controlled variance for reproducibility
