---
title: Architecture
tags:
  - developer-guide
---

# Architecture

This page describes the high-level architecture of the MJQM simulator: how components interact, how simulations are executed, and how randomness is managed across replications.

## Policy-based design

The simulator is built around a pluggable policy architecture. The core simulation engine (`Simulator`) orchestrates event processing, whilst the scheduling logic is delegated to a `Policy` object injected at construction time.

```
Simulator
  ├── Policy          (scheduling decisions)
  ├── Samplers[]      (arrival and service time generation)
  └── ExperimentStats (metric collection)
```

The `Policy` interface defines event handlers (`arrival`, `departure`) and state queries (`get_state_ser`, `get_state_buf`, `get_free_ser`). Each concrete policy implements the `flush_buffer()` method, which contains the core scheduling algorithm — deciding which queued jobs to admit when servers become available.

This design means adding a new scheduling policy requires no changes to the simulation engine itself. See [Implementing policies](policies.md) for a step-by-step guide.

## Event loop

The simulator uses a **future event list (FEL)** to drive the discrete-event simulation. The FEL contains one entry per job class for departures and one per class for arrivals (2 × *C* entries total, where *C* is the number of job classes).

Each iteration of the main loop:

1. Finds the earliest event in the FEL
2. Collects time-weighted statistics for the interval since the last event
3. Processes the event:
   - **Departure**: removes the completed job, frees servers, calls `policy->departure()`
   - **Arrival**: creates a new job, calls `policy->arrival()`
4. Advances simulation time
5. Resamples: generates new arrival/service times and updates the FEL

The policy's `flush_buffer()` is called after both arrivals and departures, ensuring the scheduler continuously attempts to fill idle servers.

## Parallel execution model

When a TOML configuration generates multiple experiment configurations (via `[[pivot]]` sweeps), the entry point (`simulator.cpp`) dispatches them to a **Boost.Asio thread pool** sized to the hardware concurrency. Each experiment runs independently with its own `Simulator` instance and `Policy` clone.

Within a single experiment, **replications run sequentially**. Between replications, statistics are reset but the system state (jobs in service, queue contents) is preserved to maintain continuity. Simulation time is reset to zero by adjusting all timestamps by the current time offset.

## RNG stream management

Reproducibility across replications is ensured by L'Ecuyer's **MRG32k3a** combined multiple recursive generator, accessed through the RngStreams library. Each `DistributionSampler` instance holds its own RNG stream, providing:

- **Independence**: streams for different distributions do not interfere
- **Reproducibility**: identical seeds produce identical sequences across runs
- **Parallelism safety**: each experiment gets its own set of streams via `clone()`

The `randU01()` method in the `DistributionSampler` base class wraps the stream, and concrete samplers transform the uniform variate into their target distribution (e.g., inverse transform for exponential, Box–Muller for lognormal).

## Configuration loading

The TOML configuration system uses a **builder map** pattern:

1. `toml_loader.cpp` parses the TOML file into a table
2. Pivot sections are expanded into the Cartesian product of all parameter combinations
3. For each configuration, `toml_policies_loaders.cpp` looks up the policy name in `policy_builders` and calls the corresponding builder function
4. Similarly, `toml_distributions_loaders.cpp` looks up distribution names in `distribution_loaders`

This indirection means new policies and distributions only need to register a builder function — no `switch` statements or conditional logic in the loader.

## Statistics collection

Statistics are collected at two levels:

- **Per-event**: time-weighted occupancy (buffer and server counts multiplied by the time interval) and raw waiting/response times stored per job
- **Per-replication**: means and variances computed from raw data, then fed into `Stat` objects that accumulate across replications
- **Final**: confidence intervals computed from the replication-level means using the Student's *t*-distribution

The `ExperimentStats` structure groups per-class statistics (`ClassStats`) and global aggregates (total waiting time, utilisation, wasted servers, FIFO violations). Output is written as semicolon-delimited CSV.
