---
title: High-Utilization Workload
tags:
  - examples
---

# High-utilization workload

Configuration for testing Back Filling under high load with heterogeneous job classes.

## Configuration

```toml
identifier = "high_utilization_backfilling"
events = 5000000
repetitions = 40
cores = 512

policy = "back filling"

arrival.distribution = "exponential"
service.distribution = "exponential"

# Small jobs with short service times
[[class]]
cores = 1
arrival.prob = 0.7
service.mean = 0.1

# Medium jobs
[[class]]
cores = 8
arrival.prob = 0.2
service.mean = 0.5

# Large jobs with long service times
[[class]]
cores = 64
arrival.prob = 0.1
service.mean = 2.0

# Test across wide range including beyond stability
[[pivot]]
arrival.rate = [50, 100, 150, 200, 250, 300, 350, 400]
```

## What this tests

- **High server capacity**: 512 cores allow testing at high absolute loads
- **Extreme heterogeneity**: 64:1 ratio between largest and smallest jobs
- **Service time correlation**: Larger jobs have proportionally longer service times (20× difference)
- **Aggressive load sweep**: From moderate (50 jobs/time) to potentially unstable (400 jobs/time)
- **Back Filling fairness**: Tests reservation mechanism under stress

## Why Back Filling?

Back Filling reserves capacity for the blocked head-of-line job, then admits smaller jobs only if they fit in idle servers and complete before the reservation time. This makes it a natural choice for workloads where large jobs would otherwise starve.

## Expected behaviour

### Low-moderate load (λ=50-150)

- All jobs served with reasonable waiting times
- Back Filling reservations rarely activated
- Small jobs fill idle-server gaps when their service fits before the reservation
- System operates well within capacity

### High load (λ=200-300)

- Waiting times increase, especially for large jobs
- Reservations frequently computed for 64-core jobs
- Small jobs extensively used as backfill
- Approaching stability boundary

### Very high load (λ=350-400)

- System may become unstable (depends on workload specifics)
- Queue lengths grow rapidly
- Large jobs experience significant delays despite reservations
- Utilization approaches 100%

## Key metrics to examine

- **Per-class waiting time**: Compare T1 vs T8 vs T64 to verify fairness
- **Utilization**: Should remain high (>85%) before instability
- **Queue length**: Monitor growth rate to identify saturation point
- **Response time**: Include service time effects (T64 has 20× longer service than T1)

## Running the experiment

1. Save this configuration to `Inputs/high_utilization_backfilling.toml`
2. Run: `./simulator high_utilization_backfilling`
3. **Note**: With 5M events and 40 repetitions across 8 arrival rates, this experiment will take substantial time (minutes to hours depending on hardware)

## Comparison experiment

Try running the same configuration with different policies:

```toml
[[pivot]]
arrival.rate = [50, 100, 150, 200, 250, 300, 350, 400]

policy = [
    "back filling",
    "fifo",
    "most server first",
    "server filling memoryful"
]
```

Compare per-class waiting times and stability boundaries across the four policies to observe how each handles the 64:1 heterogeneity.
