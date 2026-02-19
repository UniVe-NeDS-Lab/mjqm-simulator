# Simple heterogeneous workload

A basic example with 4 job classes requiring different numbers of cores, useful for initial testing and understanding policy behaviour.

## Configuration

```toml
identifier = "simple_heterogeneous"
events = 100000
repetitions = 20
cores = 16

# Use FIFO policy (can substitute with any policy)
policy = "fifo"

# All classes use exponential distributions
arrival.distribution = "exponential"
service.distribution = "exponential"
service.mean = 1

# Define job classes with different server requirements
[[class]]
cores = 1
arrival.prob = 0.4  # 40% of arrivals

[[class]]
cores = 2
arrival.prob = 0.3  # 30% of arrivals

[[class]]
cores = 4
arrival.prob = 0.2  # 20% of arrivals

[[class]]
cores = 8
arrival.prob = 0.1  # 10% of arrivals

# Sweep across arrival rates to observe performance
[[pivot]]
arrival.rate = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
```

## What this tests

- **Workload heterogeneity**: Jobs range from 1 to 8 cores (1:8 ratio)
- **Arrival distribution**: Small jobs dominate (40% are single-core), large jobs are rare (10% require 8 cores)
- **Service times**: Uniform mean of 1 time unit across all classes
- **Load range**: From light load (0.5 jobs/time) to moderate load (5.0 jobs/time)

## Expected behaviour

With 16 total cores and this workload:

- **Light load (λ=0.5-2.0)**: All policies should perform similarly with negligible waiting times
- **Moderate load (λ=3.0-4.0)**: Policies begin to differentiate; FIFO may show head-of-line blocking
- **Higher load (λ=5.0)**: Most policies approach capacity; expect visible performance differences

FIFO will experience head-of-line blocking when 8-core jobs arrive and fewer than 8 servers are available, even if smaller jobs could be accommodated.

## Running the experiment

1. Save this configuration to `Inputs/simple_heterogeneous.toml`
2. Run: `./simulator_toml simple_heterogeneous`
3. Results will be in `Results/simple_heterogeneous/`

## Try variations

- Change `policy` to compare different scheduling approaches
- Adjust `arrival.prob` values to test different workload mixes
- Modify `service.mean` per class to create service time heterogeneity
- Extend the `arrival.rate` array to explore stability boundaries
