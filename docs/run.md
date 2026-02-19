# Running an experiment

After compiling the project, you can run an experiment by executing the `simulator_toml` binary with the name of the configuration file as the only argument.

The program expects the configuration file to be in the `Inputs` directory, where you can already find some simple configurations.

```sh
./simulator_toml my_awesome_experiment
```

> The program can accept additional parameters that will be discussed [later](#overriding-parameters-from-command-line).

After reading the configuration file, the program will start the simulation, and print the results to the `Results` directory.
Multiple files might be generated, depending on the parameters defining the experiment.

# Configuration file

To run a set of experiments, there are two main configurations that need to be set:

- The general simulation parameters, such as the number of runs, the policy,
  some default class configuration, etc.
- The classes of jobs that will be submitted to the system,
  including the distribution of the job service times,
  the distribution of the job inter-arrival times, and number of cores required.

These settings are defined in a single configuration file,
using the [TOML](https://toml.io/en/) format.

## Simulation parameters

```toml
identifier = "my_experiment" # optional
events = 30000000
repetitions = 40
cores = 2048
policy = "fifo"
```

- `identifier`: a string that will be used to identify the experiment.
  If unset, the filename (without extension) will be used.
- `events`: the number of events to simulate in each run.
- `repetitions`: the number of runs to perform.
- `cores`: the number of cores available in the system.
- `policy`: the scheduling policy to use. The available policies are described [later](#available-policies).
- `generator`: the random number generator to use, optional.
  Only `lecuyer` is supported at the moment, and its seed is hardcoded.

## Default arrival and service time distributions

Both the arrival and service time distributions are defined in the same way:

- `distribution`: the distribution to use.
- all the parameters needed by that distribution.
  Each distribution has its own set of required or optional parameters.
  The list of available distributions and their parameters is defined [later](#available-distributions).

Each value defined here, will be used as the default value for all the job classes in the system.
You can also partially define a distribution, requiring the job classes to define the missing parameters.

> ```toml
> [arrival]
> distribution = "exponential"
>
> [service]
> distribution = "exponential"
> lambda = 0.01
> ```
>
> In the quick example above, all the job classes will have an exponential distribution for both the arrival and service times, but they are required to define parameters only for the arrival distribution.

Each job class can override any single value defined here.

## Job class definition

- `name`: a string that will be used to identify the job class.
  If unset, the class will be identified by the number of its cores.
- `cores`: the number of cores required by the job class.
- `arrival` and `service`: the distribution of the job arrival and service times.
  The parameters are the same as the default distributions, and can be omitted if the default values are used.

### Examples

All the following examples define the same class with `name` set to `3`.

```toml
[[class]]
cores = 3
arrival = { distribution = "exponential", lambda = 0.01 }
service = { distribution = "exponential", lambda = 0.01 }
```

```toml
[[class]]
cores = 3
arrival.distribution = "exponential"
arrival.lambda = 0.01
service.distribution = "exponential"
service.lambda = 0.01
```

```toml
[[class]]
cores = 3
[arrival]
distribution = "exponential"
lambda = 0.01
[service]
distribution = "exponential"
lambda = 0.01
```

## Pivot values

To allow for testing multiple values of a parameter, you can define a set of pivot values.
Each set is defined by a `[[pivot]]` header, and then you can define the values similarly to the base values, with the addition of list support.

> ```toml
> [[pivot]]
> arrival.rate = [ 0.1, 0.2, 0.3 ]
> policy.name = "smash"
> policy.window = [ 1, 4, 8 ]
> ```
>
> This pivot will generate 9 different configurations, with all the possible combinations of the default arrival rate, and the SMASH window size.

## Output columns
You can find more information about the output columns in the [output_columns](output_columns.md) page.

## Available distributions

### Bounded pareto

- `distribution = "bounded pareto"`
- `alpha`: the shape parameter.
- `L`: the lower bound.
- `H`: the higher bound.
- `mean`: the mean of the distribution.

The `alpha` parameter is required, and must be greater than 0.
Then, you can either define the `L` and `H` parameters (with `H > L`), or the `mean` parameter.

### Deterministic

- `distribution = "deterministic"`
- `value`: the value of the distribution. Required. It can also be defined as `mean`.

### Exponential

- `distribution = "exponential"`
- `lambda`: the rate of the distribution. Required. It can also be defined as `rate`.
- `mean`: the mean of the distribution.

Either `lambda` or `mean` is required.

In addition, if used in the arrival distribution, you can define per each job class:

- `prob`: the probability of the job class.
  If defined for one class, it needs to be defined for every class.
  If their sum is not 1, they will be normalised.

### Fréchet

- `distribution = "frechet"`
- `alpha`: the shape parameter.
- `s`: the scale parameter.
- `m`: the location of the minimum. Default is 0.
- `mean`: the mean of the distribution.

The `alpha` parameter is required, and must be greater than 1 to ensure the mean is finite.
Then, you can either define the `s` parameter, or the `mean` parameter.

### Lognormal

- `distribution = "lognormal"`
- `mean`: the mean of the distribution. Required.

The standard deviation is fixed at $0.5 \times \mu$.

### Uniform

- `distribution = "uniform"`
- `min`/`a`: the lower bound.
- `max`/`b`: the upper bound.
- `mean`: the mean of the distribution.

Either the `min`/`max` pair, or `mean` is required.
If `mean` is defined, the `min` and `max` will be calculated as $0.5 \times \mu$ and $1.5 \times \mu$.

## Available policies

The following sections describe configuration syntax and basic behaviour for each policy. For detailed performance comparisons, stability analysis, and guidance on choosing the right policy for your workload, see the [Policy Comparison Guide](policy-comparison.md).

For complete configuration examples demonstrating policy usage, see the [Examples](examples/simple-heterogeneous.md) section.

### FIFO
- `policy = "fifo"`

Jobs are admitted strictly in arrival order. When the head-of-line job needs more servers than are free, the system blocks all subsequent admissions — even if smaller jobs could run on the idle servers. This head-of-line blocking can leave servers idle and reduce the maximum sustainable load. [Iliadis, 1991](https://doi.org/10.1002/dac.4510040302)

> **Note**: The FIFO policy is implemented as [SMASH](#smash) with a window size of 1.

### SMASH
- `policy.name = "smash"`
- `policy.window`: the window size. Default is 2.

SMASH (SMAll SHuffle) uses a bounded lookahead window to work around head-of-line blocking. At each scheduling event, the scheduler inspects the first `window` jobs in the queue and admits the largest feasible one. Admission repeats with the updated queue and remaining idle servers until no feasible job sits inside the window. With `window=1`, SMASH behaves identically to FIFO; larger windows give more scheduling freedom but weaken arrival-order guarantees. [Olliaro et al., 2026](https://doi.org/10.1109/TPDS.2026.3657959)

### Server filling
- `policy = "server filling memoryful"`.

Server Filling constructs a working set from running jobs plus queued jobs (added in FIFO order up to system capacity), then sorts the working set by descending server demand. All servers are released and jobs from the sorted working set are admitted in order. Running jobs that no longer fit after reallocation are preempted; their remaining service time is preserved for later resumption. [Grosof and Harchol-Balter, 2023](https://doi.org/10.1145/3584684.3597264)

### Back filling
- `policy = "back filling"`

When the head-of-line job cannot run, the scheduler computes a reservation — the earliest moment when enough servers will be released. Other queued jobs may be admitted, but only if they fit in the currently idle servers *and* their service completes before the reservation time. This prevents starvation of large jobs whilst still filling idle capacity. [Srinivasan et al., 2002](https://doi.org/10.1109/ICPPW.2002.1039773); [Mu'alem and Feitelson, 2001](https://doi.org/10.1109/71.932708)

### Most server first
- `policy = "most server first"`

At each scheduling event, the scheduler admits the largest feasible job in the queue (most servers required among those that fit), regardless of arrival order. Admission repeats until no feasible job remains. Under heavy load, small jobs tend to finish quickly because they fill narrow idle gaps left by large jobs. [Chen et al., 2025](https://arxiv.org/abs/2509.01893)

### Most server first w/ quick swap
- `policy.name = "quick swap"`
- `policy.threshold`: the threshold. Default is 1.

Quick Swap adds a freeze mechanism to Most Server First. When the number of free servers reaches `threshold` and no largest-class job is running but at least one is waiting, admissions are frozen until enough servers accumulate for that waiting job. A high threshold makes the freeze rare, keeping behaviour close to standard MSF; a low threshold triggers it more often, protecting large jobs at the cost of throughput. [Chen et al., 2025](https://arxiv.org/abs/2509.01893)

### Adaptive Most server first
- `policy = "adaptive msf"`

Adaptive MSF monitors class occupancy and triggers a "quick swap" when at least one class has jobs in service but none waiting, and simultaneously another class has jobs waiting but none in service. During a quick swap, only the largest waiting job is admitted and all other admissions are blocked. Normal operation resumes once that job enters service. [Chen et al., 2025](https://arxiv.org/abs/2509.01893)

### Static Most server first
- `policy = "static msf"`

Static MSF follows a fixed cycle that specifies the order in which job classes are served. When the number of jobs in service for class $i$ falls below $\lfloor N/d_i \rfloor$ (where $N$ is total servers), a "quick swap" is triggered: additional admissions are blocked and the scheduler moves to the next class in the cycle. The cycle repeats indefinitely. [Chen et al., 2025](https://arxiv.org/abs/2509.01893)

### First-Fit
- `policy = "first fit"`

First-Fit scans the queue from the head and admits the first job whose server requirement fits within available capacity. The scan repeats until no more jobs can be admitted. Unlike FIFO, it skips over infeasible jobs, but unlike SMASH or MSF, it does not reorder by size.

# Overriding parameters from command line

You can override any parameter defined in the configuration file from the command line.
The base syntax is simply `--path.to.parameter value value2 value3`, where `parameter` is the name of the parameter to override, and `value` (`value1`, `value2`) is (are) the new value(s).
They will override any value defined in the configuration file, including values defined in pivots.
If no pivot set is defined in the configuration file, you can consider the set of command line parameters as a pivot.

For example, if you have the following configuration file:

```toml
...
[arrival]
distribution = "exponential"
lambda = 0.01
...
```

You can override the `lambda` parameter from the command line:

```sh
./simulator_toml my_awesome_experiment --arrival.lambda 0.02
```

If you want to override the `lambda` parameter for a specific job class, you can use the class index to identify it:

```sh
./simulator_toml my_awesome_experiment --class.3.arrival.lambda 0.02
```

## Multiple pivots from command line

You can also define, directly from the command line, multiple sets of values, just like the `[[pivot]]` declaration in the configuration file.
To achieve that, you can use the `--pivot` argument separating the overrides.

For example, if you want to test two sets of values, this command line is equivalent to the following configuration extract:

```sh
./simulator_toml my_awesome_experiment --arrival.rate 0.1 0.2 0.3 --policy.name smash --policy.window 1 4 8 --pivot --arrival.rate 0.1 0.2 0.3 --policy "server filling" "back filling" "most server first"
```

```toml
[[pivot]]
arrival.rate = [ 0.1, 0.2, 0.3 ]
policy.name = "smash"
policy.window = [ 1, 4, 8 ]

[[pivot]]
arrival.rate = [ 0.1, 0.2, 0.3 ]
policy = [ "server filling", "back filling", "most server first" ]
```
