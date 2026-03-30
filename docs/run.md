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

### Uniform

- `distribution = "uniform"`
- `min`/`a`: the lower bound.
- `max`/`b`: the upper bound.
- `mean`: the mean of the distribution.

Either the `min`/`max` pair, or `mean` is required.
If `mean` is defined, the `min` and `max` will be calculated as $0.5 \times \mu$ and $1.5 \times \mu$.

## Available policies

### FIFO
- `policy = "fifo"`

> **Note**: The FIFO policy is implemented as [SMASH](#smash) with a window size of 1.

### SMASH
- `policy.name = "smash"`
- `policy.window`: the window size. Default is 1.

### Server filling
- `policy = "server filling memoryful"`.

### Back filling
- `policy = "back filling"`

### Back filling imperfect
- `policy = "back filling imperfect"`
- `policy.overest`: Mean of positive gaussian random over-estimation.

### Balanced splitting
- `policy = "balanced splitting"`
- `policy.psi`: Variable for reserved servers partitioning.

### Most server first
- `policy = "most server first"`

### Most server first w/ quick swap
- `policy.name = "quick swap"`
- `policy.threshold`: the threshold. Default is 1.

### Kill smart
- `policy.name = "kill smart"`
- `policy.k`: max stopped size. Default is 10.
- `policy.v`: how many jobs to kill at once. Default is 1.

### Dual kill
- `policy.name = "dual kill"`
- `policy.k`: max stopped size. Default is 10.
- `policy.v`: how many jobs to kill at once. Default is 1.

### Adaptive Most server first
- `policy = "adaptive msf"`

### Static Most server first
- `policy = "static msf"`

### First-Fit
- `policy = "first fit"`

### LCFS
- `policy = "lcfs"`

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
