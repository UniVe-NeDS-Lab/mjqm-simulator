# Extending the simulator

The MJQM simulator is designed as an extensible framework that allows users to customize and enhance its functionality without modifying core code. The modular architecture enables independent development of scheduling policies, probability distributions, and analysis tools.

## Getting started

Before implementing extensions, familiarize yourself with the simulator's architecture:

**[Project structure](extend/structure.md)**: Overview of the codebase organization, library dependencies, and key architectural components. Essential reading before making modifications.

## Main extension points

### [Policies](extend/policies.md)

Implement custom scheduling policies to test new algorithms or domain-specific strategies.

**What you can do**: Add new policies like priority-based scheduling, deadline-aware algorithms, or workload-specific optimizations.

**Difficulty**: Moderate (requires understanding queueing dynamics and C++ interfaces).

**Guide includes**: Complete implementation walkthrough using SMASH as example, interface documentation, loader configuration, and best practices.

### [Distributions](extend/distributions.md)

Add probability distributions for service times and inter-arrival times.

**What you can do**: Implement heavy-tailed distributions, empirical distributions from traces, or custom synthetic workloads.

**Difficulty**: Easy to moderate (mostly mathematical formulas and sampling algorithms).

**Guide includes**: Step-by-step implementation using Exponential as example, parameter handling, validation, and TOML integration.

### Statistics (coming soon)

Add custom performance metrics beyond the default response time, waiting time, and utilization.

**What you can do**: Track policy-specific metrics, compute percentiles, measure fairness indices, or calculate custom stability indicators.

**Difficulty**: Moderate (requires understanding simulation output pipeline).

### Output columns (coming soon)

Customize which configuration parameters and metrics appear in result files.

**What you can do**: Add derived columns, compute aggregate statistics, or format output for specific analysis tools.

**Difficulty**: Easy (mainly configuration work).

### Visualizations (coming soon)

Create custom plots and interactive dashboards for result analysis.

**What you can do**: Generate domain-specific visualizations, integrate with external plotting libraries, or create custom reports.

**Difficulty**: Easy to moderate (Python programming, matplotlib/plotly knowledge).

## Development workflow

1. **Read the structure guide**: Understand library organization and dependencies
2. **Choose your extension point**: Select policies, distributions, or another component
3. **Follow the implementation guide**: Use the detailed walkthroughs with working examples
4. **Build and test**: Use `./rebuild` to compile and verify your implementation
5. **Run experiments**: Test with small configurations before large parameter sweeps

## Quick reference

- **Adding a policy**: See [Policies guide](extend/policies.md)
- **Adding a distribution**: See [Distributions guide](extend/distributions.md)
- **Architecture overview**: See [Project structure](extend/structure.md)
- **Configuration syntax**: See [Running experiments](../run.md)
- **Result analysis**: See [Result analysis](../report.md)

## Community and contributions

The MJQM simulator is actively developed. When implementing extensions:

- Follow existing code patterns (documented in each guide)
- Maintain interface contracts (don't break existing APIs)
- Add tests for new functionality
- Update documentation when adding features

For questions or contributions, consult the project repository.
