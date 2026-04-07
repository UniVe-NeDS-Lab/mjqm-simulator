---
title: Implementing Policies
tags:
  - developer-guide
  - policies
---

# Policies

New policy implementations need two parts: the policy class and the loader.

The policy class implements the scheduling logic and manages job queues and server state. It needs to be located in the [`mjqm-policies`](https://github.com/unive-neds-lab/mjqm-simulator/tree/main/libs/policies/include/mjqm-policies) folder of the `policies` library. The class consists of a header file (`.h`) defining the interface and a corresponding implementation file (`.cpp`) in the `src` directory.

The loader is a function to read the policy parameters from the [TOML](https://toml.io/en/) configuration file and creates the policy object. It is split into two parts: the declaration in `mjqm-settings/toml_policies_loaders.h` and the implementation in `mjqm-settings/toml_policies_loaders.cpp`. Additionally, the loader needs to be added to the `policy_builders` map at the end of the header file.

# Adding a new policy

If you want to add a new policy to the simulator, you need to follow these four (high-level) steps:

1. Create a new class in the `mjqm-policies` lib that extends the `Policy` interface and implements all required methods.
2. Add the new policy to the `mjqm-policies/policies.h` imports.
3. Add the new loader declaration to `mjqm-settings/toml_policies_loaders.h`, including it in the `policy_builders` map at the end.
4. Add the new loader implementation to `mjqm-settings/toml_policies_loaders.cpp`, taking care of validating the parameters and creating the new policy object.

Let's see an example of how to add a new policy to the simulator. We'll take the SMASH policy as an example, even though it's already implemented in the simulator.

## `Policy` interface

See [`policy.h`](https://github.com/unive-neds-lab/mjqm-simulator/blob/main/libs/policies/include/mjqm-policies/policy.h) for the full source.

The interface expects the following methods to be implemented:

- `void arrival(int c, int size, long int id)` - Called when a job arrives. Parameters are job class `c`, server requirement `size`, and unique job identifier `id`.
- `void departure(int c, int size, long int id)` - Called when a job completes service. Parameters are the same as arrival.
- `const std::vector<int>& get_state_ser()` - Returns the number of jobs in service for each class.
- `const std::vector<int>& get_state_buf()` - Returns the number of jobs waiting in the buffer for each class.
- `const std::vector<std::list<long int>>& get_stopped_jobs()` - Returns the IDs of jobs waiting in the buffer for each class.
- `const std::vector<std::list<long int>>& get_ongoing_jobs()` - Returns the IDs of jobs currently in service for each class.
- `int get_free_ser()` - Returns the number of currently idle servers.
- `int get_violations_counter()` - Returns the count of FIFO order violations (jobs admitted out of arrival order).
- `void flush_buffer()` - The core scheduling logic that attempts to admit jobs from the buffer to service.
- `std::unique_ptr<Policy> clone() const` - Creates a new instance of the policy with the same parameters for experiment replication.
- `explicit operator std::string() const` - Returns a string representation of the policy with its parameters.

Additional methods present in the interface (used by specific policies):

- `int get_window_size()` and `int get_w() const` - For window-based policies like SMASH.
- `void insert_completion(int size, double completion)` and `void reset_completion(double simtime)` - For reservation-based policies like Back Filling.
- `bool fit_jobs(std::unordered_map<long int, double> holdTime, double simTime)` - For policies requiring lookahead computation.
- `bool prio_big()` and `int get_state_ser_small()` - For size-priority policies.

> [!Note]
> Not all methods are used by all policies. Provide sensible default implementations (e.g., returning 0, -1, or false) for methods not relevant to your policy's logic.

## Create a new class

Policies consist of a header file defining the class interface and a source file implementing the scheduling logic.

> [!Note]
> Use the `MJQM_` prefix for include guards to avoid name clashes with other libraries.

We'll prepare both files for the SMASH policy.

### Header file

The header defines the class interface, state variables, and constructor.

```cpp
// libs/policies/include/mjqm-policies/Smash.h
#ifndef SMASH_H
#define SMASH_H

#include <mjqm-policies/policy.h>

class Smash : public Policy {
public:
    Smash(const int w, const int servers, const int classes);
    void arrival(int c, int size, long int id) override;
    void departure(int c, int size, long int id) override;
    const std::vector<int>& get_state_ser() override { return state_ser; }
    const std::vector<int>& get_state_buf() override { return state_buf; }
    const std::vector<std::list<long int>>& get_stopped_jobs() override { return stopped_jobs; }
    const std::vector<std::list<long int>>& get_ongoing_jobs() override { return ongoing_jobs; }
    int get_free_ser() override { return freeservers; }
    int get_w() const override { return w; }
    ~Smash() override = default;
    std::unique_ptr<Policy> clone() const override;
    explicit operator std::string() const override;

private:
    std::list<std::tuple<int, int, long int>> buffer;
    int servers;
    const int w;
    std::vector<int> state_buf;
    std::vector<int> state_ser;
    std::vector<std::list<long int>> stopped_jobs;
    std::vector<std::list<long int>> ongoing_jobs;
    int freeservers;
    int violations_counter;

    void flush_buffer() override;
};

#endif // SMASH_H
```

#### Fields

The policy class needs to maintain several pieces of state:

- **Buffer structure**: A `std::list<std::tuple<int, int, long int>>` storing waiting jobs as (class, size, id) tuples. Using a list allows efficient insertion and removal during scheduling.
- **State tracking**: Vectors tracking the number of jobs in buffer (`state_buf`) and in service (`state_ser`) for each class.
- **Job identifiers**: Vectors of lists storing job IDs for stopped (`stopped_jobs`) and ongoing (`ongoing_jobs`) jobs per class.
- **Server tracking**: `freeservers` tracks currently idle servers; `servers` stores the total system capacity.
- **Policy parameters**: `w` is the window size parameter controlling the lookahead depth.
- **Metrics**: `violations_counter` tracks FIFO order violations for statistics.

> [!Note]
> Organise state variables logically: buffer/queue structures, state counters, job tracking, resource counters, and policy-specific parameters.

#### Constructor and clone

The constructor initialises the policy with its parameters and allocates state vectors based on the number of job classes.

```cpp
Smash(const int w, const int servers, const int classes) :
    servers(servers), w(w), state_buf(classes), state_ser(classes),
    stopped_jobs(classes), ongoing_jobs(classes),
    freeservers(servers), violations_counter(0) {}
```

The `clone()` method creates a new instance with the same parameters for independent experiment replication:

```cpp
std::unique_ptr<Policy> clone() const override {
    return std::make_unique<Smash>(w, servers, state_buf.size());
}
```

> [!Note]
> The clone method should create a fresh instance with the same parameters but independent state. Use `state_buf.size()` to infer the number of classes rather than storing it separately.

#### String conversion

The string conversion operator provides a readable representation for logging and debugging:

```cpp
explicit operator std::string() const override {
    return "Smash(window=" + std::to_string(w) +
           ", servers=" + std::to_string(servers) +
           ", classes=" + std::to_string(state_buf.size()) + ")";
}
```

### Implementation file

The source file implements the scheduling logic.

```cpp
// libs/policies/src/mjqm-policies/Smash.cpp
#include <mjqm-policies/Smash.h>

void Smash::arrival(int c, int size, long int id) {
    std::tuple<int, int, long int> e(c, size, id);
    this->buffer.push_back(e);
    state_buf[c]++;
    flush_buffer();
}

void Smash::departure(int c, int size, long int id) {
    state_ser[c]--;
    freeservers += size;
    flush_buffer();
}

void Smash::flush_buffer() {
    ongoing_jobs.clear();
    ongoing_jobs.resize(state_buf.size());

    bool modified = true;
    while (modified && buffer.size() > 0 && freeservers > 0) {
        auto it = buffer.begin();
        auto max = buffer.end();
        int i = 0;
        modified = false;

        // Find largest feasible job within window
        while (it != buffer.end() && (i < w || w == 0)) {
            if (std::get<1>(*it) <= freeservers &&
                (max == buffer.end() || std::get<1>(*it) > std::get<1>(*max))) {
                max = it;
            }
            ++i;
            ++it;
        }

        // Admit the selected job
        if (max != buffer.end()) {
            freeservers -= std::get<1>(*max);
            state_buf[std::get<0>(*max)]--;
            state_ser[std::get<0>(*max)]++;
            ongoing_jobs[std::get<0>(*max)].push_back(std::get<2>(*max));
            if (buffer.begin() != max) {
                violations_counter++;
            }
            buffer.erase(max);
            modified = true;
        }
    }
}
```

#### Core methods

**`arrival()`**: Called when a job enters the system. The job is added to the end of the buffer, the buffer state counter is incremented, and `flush_buffer()` is called to attempt immediate admission.

**`departure()`**: Called when a job completes service. The service state counter is decremented, freed servers are returned to the pool, and `flush_buffer()` is called to admit waiting jobs.

**`flush_buffer()`**: The heart of the scheduling policy. This method:

1. Clears the `ongoing_jobs` tracking (it will be repopulated with newly admitted jobs)
2. Iterates while modifications are made and resources are available:
   - Scans the first `w` jobs in the buffer (or all jobs if `w=0`)
   - Identifies the largest job that fits in available servers
   - Admits that job by updating servers, state counters, and job lists
   - Tracks FIFO violations when jobs are admitted out of order
   - Removes the admitted job from the buffer
3. Repeats until no feasible jobs remain or servers are exhausted

> [!Note]
> The `flush_buffer()` method is called after both arrivals and departures, ensuring the policy continuously attempts to maximise server utilisation. Keep this method efficient as it's called frequently.

> [!Note]
> Clear and resize `ongoing_jobs` at the start of `flush_buffer()` to track only jobs admitted in the current scheduling event. The simulator uses this to trigger service completions.

## Make the class available

Now that we've defined the class, we need to make it available to the simulator.
Include it in the `policies.h` aggregator header, which is used wherever policies are needed.

```cpp
// libs/policies/include/mjqm-policies/policies.h
// ...
#include <mjqm-policies/Smash.h>
// ...
```

> [!Note]
> Keep the includes in alphabetical order for consistency.

## Implement the loader

The final piece to support our new policy is to implement the loader function.
This function should read the parameters from the TOML configuration file, validate them, update the configuration for output tracking, and create a new instance of the policy.

We also need to map the loader to the name to be used in the configuration file.

### Declare the loader

In the `toml_policies_loaders.h` header, we declare the loader as `{policy_name}_builder` with the same signature as the other loaders (defined at the top of the header as `policy_builder` type definition).

Then, we add it to the `policy_builders` map at the end of the header, with an all-lowercase, space-separated key.

```cpp
// libs/simulator/include/mjqm-settings/toml_policies_loaders.h
// ...
std::unique_ptr<Policy> smash_builder(toml::table& data, ExperimentConfig& conf);
// ...
inline static std::unordered_map<std::string_view, policy_builder> policy_builders = {
    // ...
    {"smash", smash_builder},
    // ...
};
```

> [!Note]
> Keep both the loader declaration and the map element in alphabetical order for consistency.

The key in the map will be used in the configuration file as follows:

```toml
# Simple form (no parameters)
policy = "smash"

# With parameters
policy.name = "smash"
policy.window = 5
```

### Implement the loader

Finally, we implement the loader function in the `toml_policies_loaders.cpp` file.
This function should read the parameters from the TOML table, validate them, update the configuration for result tracking, and create a new instance of the policy.

```cpp
// libs/simulator/src/mjqm-settings/toml_policies_loaders.cpp
#include <mjqm-policies/policies.h>
#include <mjqm-settings/toml_loader.h>
#include <mjqm-settings/toml_policies_loaders.h>

std::unique_ptr<Policy> smash_builder(toml::table& data, ExperimentConfig& conf) {
    const auto window = data.at_path("policy.window").value<unsigned int>().value_or(2);
    conf.toml.insert_or_assign("policy.name", "smash");
    conf.toml.insert_or_assign("policy.window", window);
    conf.stats.add_pivot_column("policy.window", window);
    return std::make_unique<Smash>(window, conf.cores, conf.classes.size());
}
```

The loader performs these steps:

1. **Extract parameters**: Use `data.at_path("policy.parameter_name")` to read parameters from the TOML configuration, providing defaults with `.value_or()`.
2. **Update configuration**: Insert the policy name and parameters into `conf.toml` to ensure they appear in output files for reproducibility.
3. **Register pivot columns**: Call `conf.stats.add_pivot_column()` for each parameter that should be varied across experiments. This enables parameter sweeps in the output.
4. **Construct policy**: Create and return the policy instance using `std::make_unique<PolicyClass>(parameters, conf.cores, conf.classes.size())`.

> [!Note]
> Always extract the number of classes from `conf.classes.size()` rather than requiring it as a parameter. The `conf.cores` field provides the total number of servers.

> [!Note]
> Some policies (like Most Server First variants) require job class sizes. Extract these using `conf.get_sizes(sizes)` which populates a `std::vector<unsigned int>` and returns the class count.

Example for a policy requiring class sizes:

```cpp
std::unique_ptr<Policy> most_server_first_builder(toml::table&, ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<MostServerFirst>(0, conf.cores, n_classes, sizes);
}
```

> [!Note]
> Policies without configurable parameters still need a builder function. Simply omit parameter extraction and use sensible defaults or special values (like the window ID integers used internally).

## Best practices

When implementing a new scheduling policy, follow these guidelines:

1. **Efficiency**: The `flush_buffer()` method is called frequently. Optimise for common cases and avoid unnecessary iterations.

2. **Correctness**: Ensure state counters (`state_buf`, `state_ser`, `freeservers`) remain consistent. Every job admission must decrement `state_buf`, increment `state_ser`, and decrement `freeservers` by the job size.

3. **Independence**: The `clone()` method must create fully independent instances. Don't share mutable state between policy instances.

4. **Tracking**: Populate `ongoing_jobs` with IDs of newly admitted jobs during each `flush_buffer()` call. The simulator uses this to schedule service completions.

5. **Violations**: Increment `violations_counter` when admitting jobs out of FIFO order (i.e., when the admitted job is not at the front of the buffer). This metric helps analyse fairness.

6. **Default methods**: Provide sensible defaults for interface methods not used by your policy (e.g., `get_window_size()` can return 0 or -1).

7. **Configuration**: Always update `conf.toml` with the policy name and parameters for reproducibility.

8. **Documentation**: Add your policy to `docs/user-guide/running.md` with a brief description of its behaviour and parameters.
