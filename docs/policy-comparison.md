# Policy Comparison Guide

This guide explains how to systematically compare scheduling policies, interpret performance metrics, and conduct rigorous analysis of simulation results.

# Overview

Comparing scheduling policies requires understanding multiple performance dimensions: aggregate efficiency, per-class fairness, stability boundaries, and parameter sensitivity. This guide provides the methodology for conducting such comparisons, focusing on measurement techniques and interpretation frameworks rather than prescriptive recommendations.

This guide covers:

- Key performance metrics and their interpretation
- Comparison methodologies (aggregate vs per-class)
- Identifying stability boundaries
- Fairness analysis techniques
- Visualization and statistical methods

# Key performance metrics

## Response time

**Definition**: Total time from job arrival to completion (waiting time + service time).

**Interpretation**: Directly measures user-perceived performance. Response time includes both queueing delay and actual service duration, making it sensitive to both system load and service time characteristics.

**Usage in comparison**:
- Reveals overall system performance under load
- Shows policy behaviour as load increases
- Includes service time effects (large jobs naturally have longer response times)
- Use log-log plots to capture behaviour across load regimes

**What to look for**:
- Gradual increase indicates stable operation
- Sharp exponential growth signals approaching instability
- Compare slopes to assess sensitivity to load

## Waiting time

**Definition**: Time spent in queue before service begins (excludes service time).

**Interpretation**: Isolates queueing delay from service requirements, making it particularly sensitive to scheduling policy and system saturation. Pure indicator of scheduling efficiency.

**Usage in comparison**:
- Most sensitive metric for policy differentiation
- Eliminates service time confounding effects
- Critical for fairness assessment (compare per-class waiting times)
- Early indicator of saturation

**What to look for**:
- Per-class waiting time variance reveals fairness characteristics
- Super-linear growth indicates instability
- Compare absolute values and growth rates across policies

## Throughput

**Definition**: Rate at which jobs complete service.

**Interpretation**: In stable operation, throughput equals arrival rate (all arriving jobs are eventually served). Deviations indicate instability or insufficient simulation duration.

**Usage in comparison**:
- Verify stability: throughput should match arrival rate
- Per-class throughput reveals if some classes are starved
- Useful for identifying which classes dominate system load

**What to look for**:
- Throughput < arrival rate indicates instability or insufficient measurement duration
- Per-class throughput proportions should match arrival probabilities in stable operation
- Throughput ceiling indicates maximum sustainable load

## Queue length

**Definition**: Number of jobs waiting in buffer at a given time.

**Interpretation**: Direct indicator of congestion. Grows super-linearly as the system approaches capacity.

**Usage in comparison**:
- Early warning of approaching instability
- Visualize using log-log plots to detect super-linear growth
- Per-class queue lengths show if certain job sizes accumulate

**What to look for**:
- Linear growth: stable operation with increasing load
- Super-linear growth: approaching stability boundary
- Explosive growth: unstable regime
- Asymmetric per-class growth: potential fairness issues

## Utilization

**Definition**: Fraction of servers occupied by jobs in service.

**Interpretation**: Measures resource usage efficiency. Maximum sustainable utilization depends on policy mechanisms and workload characteristics.

**Usage in comparison**:
- Utilization at stability boundary reveals policy efficiency
- Low utilization with high waiting time indicates server fragmentation
- Compare maximum sustainable utilization across policies

## Kleinrock's Power Metric

**Definition**: $P(\lambda) = X(\lambda) / R(\lambda)$ where $X$ is throughput and $R$ is response time.

**Interpretation**: Balances throughput against delay. The arrival rate $\lambda^*$ maximising power represents the operational stability boundary: beyond this point, throughput grows slowly while delay grows super-linearly. [Kleinrock, 1979](https://ieeexplore.ieee.org/document/1174652)

**Usage in comparison**:
- Objective stability boundary identification
- Compare maximum power across policies
- Knee point in power curve indicates optimal operating point

**What to look for**:
- Peak power identifies stability boundary for each policy
- Higher peak power indicates better throughput-delay trade-off
- Sharp vs gradual decline reveals graceful vs abrupt degradation

# Comparison methodologies

## Aggregate comparison

**Approach**: Compare policies at identical arrival rates, examining system-wide averages.

**When to use**:
- Initial high-level comparison
- Identifying overall efficiency
- Determining stability boundaries
- Comparing policies at matched load

**Procedure**:
1. Define arrival rate sweep from light load to beyond expected stability
2. Run all policies at same arrival rates (use pivot configuration)
3. Plot metrics (waiting time, response time, utilization) vs arrival rate
4. Identify stability boundaries using Kleinrock's power metric

**Limitations**: May obscure per-class disparities; a policy with excellent aggregate metrics may severely disadvantage certain job classes.

## Per-class comparison

**Approach**: Disaggregate metrics by job class to reveal fairness characteristics.

**When to use**:
- Assessing fairness
- Understanding which classes benefit/suffer under each policy
- Designing workload-specific scheduling strategies
- Verifying all classes receive service

**Procedure**:
1. Select representative arrival rate (typically where most policies are stable but load is non-negligible)
2. Extract waiting time, response time, and throughput for each job class
3. Compare across policies for same class
4. Compare across classes for same policy
5. Quantify disparity using coefficient of variation or max/min ratios

**Key per-class metrics**:
- **Waiting time per class**: Reveals which classes wait longest
- **Response time per class**: Includes service time effects
- **Throughput per class**: Verify proportions match arrival probabilities
- **CV of waiting times**: Quantifies fairness (lower CV indicates more uniform treatment)
- **Max/min ratio**: Worst-treated vs best-treated class

## Fairness quantification

### Coefficient of variation (CV)

$$CV = \frac{\sigma}{\mu} = \frac{\text{Std. Dev. of per-class waiting times}}{\text{Mean waiting time}}$$

Lower CV values indicate more uniform treatment across job classes. As a rough guide: CV < 2 suggests uniform treatment, 2–4 moderate dispersion, and > 4 severe dispersion.

### Waiting time ratios

Compare worst-treated class to best-treated class:

$$\text{Ratio} = \frac{\max_i W_i}{\min_i W_i}$$

Higher ratios indicate greater disparity in treatment between different job classes.

# Identifying stability boundaries

## Kleinrock's Power Metric approach

**Method**: Compute power metric for each arrival rate and identify the peak.

**Procedure**:
1. For each policy, compute $P(\lambda) = X(\lambda) / R(\lambda)$ across all tested arrival rates
2. Find $\lambda^*$ where power is maximized: $\lambda^* = \arg\max_\lambda P(\lambda)$
3. Record corresponding utilization at $\lambda^*$

**Advantages**:
- Objective, algorithmic identification
- No subjective judgment required
- Balances throughput and delay
- Works across different workloads

## Visual identification

**Alternative method**: Plot waiting time vs arrival rate and identify exponential growth onset.

**Procedure**:
1. Plot mean waiting time vs arrival rate (log-log scale)
2. Identify where curve transitions from linear to super-linear
3. Mark this transition as stability boundary

**Challenges**:
- Subjective judgment required
- Transition may be gradual
- Requires dense sampling of arrival rates

# Theoretical policy properties

Different scheduling policies have inherent theoretical properties that affect their behavior:

## FIFO (First-In, First-Out)

**Theoretical properties**:
- Preserves strict arrival order
- Subject to head-of-line blocking: when the job at the head requires more servers than available, subsequent feasible jobs cannot be admitted
- In heterogeneous workloads with high variance in server requirements, head-of-line blocking can significantly limit achievable utilization

## SMASH (SMAll SHuffle)

**Theoretical properties**:
- Relaxes strict arrival order within a finite window
- Window size $w$ controls lookahead depth
- With $w=1$, behaves identically to FIFO
- Larger windows increase scheduling flexibility but may increase FIFO violations
- Bounded lookahead limits potential unfairness compared to unbounded reordering

## Back Filling

**Theoretical properties**:
- Maintains a reservation for the head-of-line job when it cannot be admitted
- Other jobs may be admitted only if they fit in idle servers *and* complete before the reservation time
- Prevents starvation of large jobs through the reservation mechanism

## Server Filling

**Theoretical properties**:
- Constructs a working set from running + queued jobs (FIFO order, up to system capacity), sorted by descending server demand
- Performs complete reallocation: releases all servers and reassigns from the sorted working set
- May preempt running jobs; remaining service time is preserved
- Does not preserve arrival order

## Most Server First

**Theoretical properties**:
- Prioritizes jobs requiring most servers among feasible jobs
- Does not preserve arrival order
- Designed to reduce server fragmentation
- No inherent fairness guarantees; may significantly disadvantage jobs with smaller server requirements

## Quick Swap, Adaptive MSF, Static MSF

**Theoretical properties**:
- Variants of Most Server First with conditional admission freezing
- Quick Swap: freezes admissions when free servers reach a threshold and no largest-class job is running but one is waiting; high threshold ≈ standard MSF, low threshold protects large jobs
- Adaptive MSF: freezes admissions when at least one class has jobs in service but none waiting and another class has jobs waiting but none in service
- Static MSF: follows a fixed class-serving cycle; triggers a freeze when class occupancy falls below $\lfloor N/d_i \rfloor$
- All inherit Most Server First's lack of inherent fairness guarantees

# Visualization strategies

## Log-log plots

**When to use**: Metrics spanning multiple orders of magnitude (waiting time, queue length).

**Advantages**:
- Reveals power-law relationships
- Captures behaviour from light to heavy load
- Identifies super-linear growth transitions

**What to plot**:
- Waiting time vs arrival rate
- Queue length vs arrival rate
- Response time vs arrival rate

**Interpretation**:
- Linear on log-log: polynomial relationship
- Upward curvature: super-linear growth (approaching instability)
- Sharp bend: stability boundary

## Linear plots with marked boundaries

**When to use**: Utilization, throughput, metrics with bounded ranges.

**Enhancements**:
- Vertical lines marking each policy's stability boundary
- Annotate with utilization percentage at boundary
- Use consistent colors/markers across plots

## Per-class comparisons

**Approach**: Bar charts or grouped scatter plots showing metrics for each class.

**X-axis**: Job class (often by server requirement)

**Y-axis**: Waiting time, response time, or throughput

**Grouping**: One group per policy

**What to look for**:
- Uniform bar heights: relatively uniform treatment
- Systematic patterns: certain classes consistently favored/disadvantaged
- Extreme disparities: large differences between classes

## Heatmaps

**Approach**: 2D heatmap with policies on one axis, metrics or classes on the other.

**Use cases**:
- Compare multiple metrics across policies
- Show per-class performance across policies
- Identify patterns in parameter sweeps

# Statistical considerations

## Replication

**Recommendation**: 20-40 independent replications per configuration.

**Why**:
- Provides confidence intervals for metrics
- Enables significance testing between policies
- Accounts for stochastic variability

## Simulation length

**Recommendation**: Sufficient events for steady-state convergence.

**Guidelines**:
- Start with 100,000 events minimum
- Increase for higher load conditions
- Increase for high variance workloads
- Very high variance: 1,000,000+ events may be needed

**Verification**: Plot metrics vs time to ensure convergence (should plateau).

## Confidence intervals

**Computation**: Standard error of mean across replications, 95% CI.

**Presentation**: Show error bars or confidence bands on plots.

**Interpretation**: Non-overlapping CIs indicate statistically significant differences.

# Practical workflow

## Step 1: Define experimental parameters

- **System capacity**: Number of cores
- **Job classes**: Server requirements, arrival probabilities, service time distributions
- **Arrival rate range**: From light load to beyond expected stability
- **Policies to compare**: Select representative policies

## Step 2: Configure pivot sweep

```toml
[[pivot]]
arrival.rate = [10, 20, 30, 40, 50, 60, 80, 100, 120, 150, 180, 200]

policy = [
    "fifo",
    "back filling",
    "server filling memoryful",
    "most server first",
    { name = "smash", window = 5 }
]
```

## Step 3: Run experiments

```sh
./simulator_toml policy_comparison
```

## Step 4: Identify stability boundaries

For each policy:
1. Load results
2. Compute Kleinrock's power metric: $P(\lambda) = X(\lambda) / R(\lambda)$
3. Find $\lambda^* = \arg\max P(\lambda)$
4. Record utilization at $\lambda^*$

## Step 5: Aggregate comparison

Plot for each metric:
- X-axis: Arrival rate (log scale)
- Y-axis: Metric value (log scale for waiting time, queue length)
- One line per policy
- Vertical lines at each policy's $\lambda^*$

## Step 6: Per-class analysis

Select arrival rate where most policies are stable:

1. Extract per-class waiting times for each policy
2. Plot grouped bar chart: classes on X-axis, waiting time on Y-axis, one group per policy
3. Compute fairness metrics (CV, max/min ratio)
4. Create fairness vs efficiency scatter plot

## Step 7: Interpret and select

**Questions to answer**:
- Which policy maximizes sustainable load for this workload?
- Which policy provides the most uniform per-class treatment for this workload?
- Is there a balanced option?
- How sensitive are results to parameter choices?

**Selection criteria**:
- Required fairness guarantees
- Maximum acceptable utilization
- Workload characteristics (heterogeneity, service time distribution)
- Operational constraints

# Advanced topics

## Parameter sensitivity

For policies with parameters (SMASH window, Quick Swap threshold), sweep parameter values:

```toml
[[pivot]]
policy.window = [1, 2, 5, 10, 20, 50]  # For SMASH
```

Plot performance vs parameter value to identify optimal settings for your workload.

## Workload characterization

Workload heterogeneity impacts policy performance. Characterize your workload using:

**Metrics**:
- Coefficient of variation of server requirements
- Range of server requirements (max/min ratio)
- Correlation between server requirements and service times

**Impact on policies**:
- Low heterogeneity: Head-of-line blocking less severe, policy choice matters less
- High heterogeneity: Head-of-line blocking significant, policy choice critical

## Multi-dimensional optimization

Create Pareto frontier showing trade-offs:

- **X-axis**: Maximum sustainable utilization (from stability analysis)
- **Y-axis**: Fairness metric (e.g., CV of per-class waiting times)
- Each point represents a policy or configuration

Policies on the frontier are optimal for some trade-off preference; interior points are dominated.

# Common pitfalls

## Insufficient simulation length

**Problem**: Results haven't reached steady state.

**Symptom**: Metrics still changing at end of simulation.

**Solution**: Increase `events` parameter, verify convergence by plotting metrics over time.

## Testing only light load

**Problem**: All policies perform similarly at low load.

**Symptom**: No performance differentiation observed.

**Solution**: Extend arrival rate sweep to higher loads, include rates beyond expected stability.

## Ignoring per-class metrics

**Problem**: Aggregate metrics hide fairness issues.

**Symptom**: Policy with best aggregate performance has extreme per-class disparities.

**Solution**: Always examine per-class waiting times, compute fairness metrics.

## Comparing at different loads

**Problem**: Comparing policies at their respective "optimal" loads.

**Symptom**: Unfair comparison (each policy at different utilization).

**Solution**: Compare at matched arrival rates, or at matched utilization levels.

## Over-interpreting small differences

**Problem**: Declaring significance without statistical testing.

**Symptom**: Choosing policy based on minor average differences within confidence intervals.

**Solution**: Use confidence intervals, increase replications, test statistical significance.

# Further reading

- `docs/run.md`: Policy configuration reference
- `docs/extend/policies.md`: Implementing custom policies
- `docs/report.md`: Result analysis and visualization tools
