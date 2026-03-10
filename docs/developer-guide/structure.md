---
title: Project Structure
tags:
  - developer-guide
---

# Project structure

The simulator is organized as a modular C++ project with clear separation of concerns. New policies and distributions can be added without modifying core code.

The project follows the [Pitchfork Layout](https://api.csswg.org/bikeshed/?force=1&url=https://raw.githubusercontent.com/vector-of-bool/pitchfork/develop/data/spec.bs) convention for directory organisation.

## Design principles

The project follows these key principles:

- **Modularity**: Core components (policies, samplers, simulator engine) are separate libraries with well-defined interfaces
- **Extensibility**: New policies and distributions can be added without modifying core code
- **Header-only when appropriate**: Samplers use header-only implementation for compiler optimization
- **Explicit namespacing**: All library headers use `mjqm-{component}` prefixes to avoid name collisions

## Folder organisation

```treeview
mjqm-simulator
├── docs
├── Inputs
│   └── {your_and_default_input_files...}
├── libs
│   ├── policies
│   │   ├── include
│   │   │   └── mjqm-policies
│   │   │       ├── policies.h
│   │   │       ├── policy.h
│   │   │       └── {SpecificPolicy...}.h
│   │   ├── src
│   │   │   └── mjqm-policies
│   │   │       └── {SpecificPolicy...}.cpp
│   │   └── CMakeLists.txt
│   ├── samplers
│   │   ├── include
│   │   │   └── mjqm-samplers
│   │   │       ├── sampler.h
│   │   │       ├── samplers.h
│   │   │       └── {specific_sampler...}.hpp
│   │   └── CMakeLists.txt
│   ├── simulator
│   │   ├── include
│   │   │   ├── mjqm-settings
│   │   │   │   ├── loader.hpp
│   │   │   │   ├── toml_distributions_loaders.h
│   │   │   │   ├── toml_loader.h
│   │   │   │   ├── toml_overrides.h
│   │   │   │   ├── toml_policies_loaders.h
│   │   │   │   └── toml_utils.h
│   │   │   └── mjqm-simulator
│   │   │       ├── experiment.h
│   │   │       ├── experiment_stats.h
│   │   │       ├── simulator.h
│   │   │       └── stats.h
│   │   ├── src
│   │   │   ├── mjqm-settings
│   │   │   │   ├── toml_distributions_loaders.cpp
│   │   │   │   ├── toml_loader.cpp
│   │   │   │   ├── toml_overrides.cpp
│   │   │   │   ├── toml_policies_loaders.cpp
│   │   │   │   └── toml_utils.cpp
│   │   │   └── mjqm-simulator
│   │   │       └── experiment_stats.cpp
│   │   └── CMakeLists.txt
│   └── utils
│       ├── include
│       │   ├── mjqm-math
│       │   │   └── confidence_intervals.h
│       │   └── mjqm-utils
│       │       └── string.hpp
│       ├── src
│       │   └── mjqm-math
│       │       └── confidence_intervals.cpp
│       └── CMakeLists.txt
├── scripts
│   ├── convert_conf.py
│   ├── ensure_same_results.py
│   └── select-g++.sh
├── test
│   └── expected
│       └── {expected-output-files...}
├── CMakeLists.txt
├── CMakePresets.json
├── configure
├── README.md
├── rebuild
├── simula
├── simulator_smash.cpp
├── simulator_toml.cpp
└── toml_loader_test.cpp
```


The project is organized in the following way:

- `docs/`: Contains the documentation of the project.
- `Inputs/`: Contains the input files for the simulator. In the repository, only the input files for the tests are included.
- `libs/`: Contains the high level libraries used in the project.
    Each high level library has its own folder with the following structure:
    - `CMakeLists.txt`: Contains the CMake configuration for the library.
    - `include/`: Contains the header files of the library.
        This folder is organized in subfolders for each logical module of the library.
        The whole `include/` folder is included in the root `CMakeLists.txt`, so the headers are available to the whole project via names as `mjqm-{logical_module}/...`. This achieves explicit separation of our code from external libraries.
    - `src/`: Contains the source files of the library.
        Usually, each source file should be included in the `CMakeLists.txt` of the library.
- `libs/policies/`: Contains the specific policies used in the simulator.
    Each policy has its own header and source file. The latter should be included in the `CMakeLists.txt` `policies` target.
    The `policies.h` file includes all the policies headers files for easier inclusion.
- `libs/samplers/`: Contains the distributions implementation for sampling.
    Each sampler has its own header file that directly define the implementation.
    The `samplers.h` file includes all the samplers headers files for easier inclusion.
- `libs/simulator/`: Contains the actual simulator code and its settings loader.
    For a cleaner organization, the loaders for distributions and policies are separated.
- `libs/utils/`: Contains some string and math utilities.
- `scripts/`: Contains some scripts for solving small tasks running the project.
    - `convert_conf.py`: Converts the configuration files from the two-file logic to the TOML format.
    - `ensure_same_results.py`: Checks if the results of two simulations are the same.
- `test/expected/`: Contains the expected output files for the tests.

## Key architectural components

### Library dependencies

The libraries have the following dependency structure:

```
simulator (top-level application)
    ├── depends on: policies
    ├── depends on: samplers
    └── depends on: utils

policies
    └── depends on: (none, pure interface)

samplers
    └── depends on: (none, pure interface)

utils
    └── depends on: (none, pure utilities)
```

This dependency hierarchy ensures:
- Policies and samplers remain independent and reusable
- Core simulator can use any combination of policies and distributions
- Testing and development can proceed independently for each component

### Policy interface

All scheduling policies implement the `Policy` interface defined in `libs/policies/include/mjqm-policies/policy.h`. This interface defines:

- **Event handlers**: `arrival()` and `departure()` methods called by the simulator
- **State queries**: Methods to retrieve queue state, server usage, and job tracking
- **Scheduling logic**: `flush_buffer()` method containing the core scheduling algorithm

See [Policies](policies.md) for detailed implementation guidance.

### Distribution interface

All service time and inter-arrival time distributions implement the `DistributionSampler` interface in `libs/samplers/include/mjqm-samplers/sampler.h`. This interface defines:

- **Sampling**: `sample()` method to generate random variates
- **Statistics**: `get_mean()` and `get_variance()` for theoretical moments
- **Replication**: `clone()` method for independent experiment runs

See [Distributions](distributions.md) for detailed implementation guidance.

### Configuration loading

The TOML configuration system uses a loader pattern with builder functions:

- **Distribution loaders** (`toml_distributions_loaders.cpp`): Read distribution parameters, validate, construct sampler instances
- **Policy loaders** (`toml_policies_loaders.cpp`): Read policy parameters, validate, construct policy instances
- **Builder maps**: Map string keys (from config files) to builder functions

This pattern allows adding new policies and distributions by:
1. Implementing the interface
2. Adding a builder function
3. Registering in the builder map

No changes to core simulation engine required.

## Extension points

The simulator provides several extension points:

### 1. New scheduling policies

Add to `libs/policies/`:
- Create header and implementation files
- Implement `Policy` interface
- Add builder function to loaders
- Register in `policy_builders` map

See: [Implementing policies](policies.md)

### 2. New distributions

Add to `libs/samplers/`:
- Create header-only implementation
- Implement `DistributionSampler` interface
- Add loader function
- Register in `distribution_loaders` map

See: [Implementing distributions](distributions.md)

### 3. New statistics

Modify `libs/simulator/include/mjqm-simulator/experiment_stats.h` to:
- Add new statistic fields
- Update computation logic
- Modify output formatting

### 4. Custom analysis tools

Add Python scripts to `scripts/` directory:
- Use `load_experiment_data.py` module to read results
- Access dataframes with all simulation outputs
- Generate custom visualizations or analyses

## Building and development workflow

### Initial setup

```sh
./configure         # First time: configures CMake and Python environment
```

### Development cycle

```sh
# After modifying code
./rebuild           # Recompiles changed files

# After modifying code with detailed debugging
./rebuild --debug   # Rebuild with debug symbols

# After major changes (CMakeLists.txt, dependencies)
./configure --clean # Full rebuild from scratch
./rebuild
```

### Testing

```sh
./configure --test  # Configure and run tests
./rebuild --test    # Rebuild and run tests
```

Tests are defined in `CMakeLists.txt` and compare outputs against expected results in `test/expected/`.

## File naming conventions

- **Headers (`.h`)**: Interface declarations for non-template code
- **Headers (`.hpp`)**: Header-only implementations (samplers)
- **Source (`.cpp`)**: Implementation files
- **Config (`.toml`)**: Experiment configurations
- **Scripts (`.py`)**: Analysis and utility scripts

## Best practices for contributions

1. **Follow existing patterns**: Match the style of `Smash` policy or `Exponential` distribution
2. **Maintain independence**: Don't introduce dependencies between policies or samplers
3. **Document interfaces**: Add comments explaining parameters and behaviour
4. **Test thoroughly**: Add expected output files for new features
5. **Update documentation**: Add entries to this guide when extending the system
