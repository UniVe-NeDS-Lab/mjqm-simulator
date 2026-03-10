---
title: Implementing Distributions
tags:
  - developer-guide
  - distributions
---

# Distributions

New distribution implementations need two parts: the sampler and the loader.

The sampler is a header-only class that generates random numbers following the distribution. It needs to be located in the [`mjqm-samplers`](https://github.com/unive-neds-lab/mjqm-simulator/tree/main/libs/samplers/include/mjqm-samplers) folder of the `samplers` library.

The loader is a function to read the distribution parameters from the [TOML](https://toml.io/en/) configuration file and creates the sampler object. It is split into two parts: the declaration in `mjqm-settings/toml_distributions_loader.h` and the implementation in `mjqm-settings/toml_distributions_loader.cpp`. Additionally, the loader needs to be added to the `distribution_loaders` map at the end of the header file.

# Adding a new distribution

If you want to add a new distribution to the simulator, you need to follow these four (high-level) steps:

1. Create a new class in the `mjqm-samplers` lib, that extends the `DistributionSampler` class and implements all required methods.
2. Add the new distribution to the `mjqm-samplers/samplers.h` imports.
3. Add the new loader declaration to `mjqm-settings/toml_distributions_loader.h`, including it in the `distribution_loaders` map at the end.
4. Add the new loader implementation to `mjqm-settings/toml_distributions_loader.cpp`, taking care of validating the parameters and creating the new distribution object.

Let's see an example of how to add a new distribution to the simulator. We'll take the exponential distribution as an example, even though it's already implemented in the simulator.

## `DistributionSampler` interface

See [`sampler.h`](https://github.com/unive-neds-lab/mjqm-simulator/blob/main/libs/samplers/include/mjqm-samplers/sampler.h) for the full source.

The interface expects the following methods to be implemented:

- a constructor that forwards the name of the distribution instance to the interface
  (the name is generated based on the job class during the loading from the TOML file)
- `double sample()` that generates a random number following the distribution
- `double get_mean() const` that returns the theoretical mean of the distribution
- `double get_variance() const` that returns the theoretical variance of the distribution
- `explicit operator std::string() const` that returns the name of the distribution, along with its parameters and its theoretical mean and variance.
- `std::unique_ptr<DistributionSampler> clone(const std::string& name) const` that builds a new instance of the distribution with the same parameters.

The interface offers the following protected method to be used by the implementing classes:

- `double randU01()` that generates a random number following the uniform distribution between 0 and 1. Internally this uses L'Ecuyer's MRG32k3a generator, which provides independent streams per experiment run. [L'Ecuyer, 1999](https://doi.org/10.1287/opre.47.1.159); [L'Ecuyer et al., 2002](https://doi.org/10.1287/opre.50.6.1073.358)

> [!Note]
> In order to achieve a more cohesive library, we define some good practices to follow when implementing a new distribution. Those will be discussed in each appropriate section using boxes like this one.

## Create a new class

As we are in a header-only library (`.hpp` extension), we need to define the class implementation in the header file.
This also allows the compiler to inline the methods and optimize binary.
The class will be surrounded by the usual `c++` include guards.

> [!Note]
> To avoid name clashes, use the `MJQM_SAMPLERS_` prefix for the include guards.

We can prepare the class skeleton extending the `DistributionSampler` interface.

```cpp
// libs/samplers/include/mjqm-samplers/exponential.hpp
#ifndef MJQM_SAMPLERS_EXPONENTIAL_H
#define MJQM_SAMPLERS_EXPONENTIAL_H

#include <mjqm-samplers/sampler.h>

class Exponential : public DistributionSampler {
    // ...
};

#endif // MJQM_SAMPLERS_EXPONENTIAL_H
```

#### Fields

We first define the constant fields to keep the distribution parameters in the class, along with the theoretical mean and variance.

In our case, for the exponential distribution, we only need to store the $\lambda$ parameter, `lambda`.
Then, we directly write the mean and variance formulas in their declarations. For readeability, we can use the `pow` function from the `cmath` library to compute the variance.

$$
\mu = \frac{1}{\lambda} \quad \text{and} \quad \sigma^2 = \frac{1}{\lambda^2}
$$

> [!Note]
> Declare theoretical mean and variance constant, and compute them just once.

```cpp
// libs/samplers/include/mjqm-samplers/exponential.hpp
// ...
#include <cmath>
// ...
class Exponential : public DistributionSampler {
public: // descriptive parameters and statistics
    const double lambda;
    const double mean = 1. / lambda;
    const double variance = 1. / pow(lambda, 2);
    // ...
};
```

#### Operative methods

Out of the methods defined abstract (pure virtual) by the `DistributionSampler` interface, the `sample` method is the main one that we need to implement, while the mean and variance getters are only required to provide them _by design_.

> [!Note]
> Inline all these methods in order to hint the compiler they could be optimised.

For sampling, we want to employ the `randU01()` method provided by the interface as random uniform 0-1 variable, so we use the formula

$$
X \sim \text{Exp}(\lambda) \quad \text{if} \quad X = -\log(U) / \lambda \quad \text{where} \quad U \sim \text{U}(0, 1)
$$

```cpp
// libs/samplers/include/mjqm-samplers/exponential.hpp
// ...
#include <cmath>
// ...
class Exponential : public DistributionSampler {
public: // operative methods
    inline double get_mean() const override { return mean; }
    inline double get_variance() const override { return variance; }
    inline double sample() override { return -log(randU01()) / lambda; }
    // ...
};
```

#### Constructors

The exponential distribution is defined by the single parameter $\lambda$, so we define the constructor to only receive this parameter (along with the name).

> [!Note]
> Only put the actual distribution parameters as constructor arguments, instead of some value(s) to compute them.

As different costructor variants, we can provide two idiomatic static methods: `with_rate` and `with_mean`, where the second one computes $\lambda = 1 / \mu$.

> [!Note]
> If some parameter can be computed from the `mean`, `rate`, or other pseudo-parameters, implement a static method `with_{param}` accepting the pseudo-parameters, along with other non-computable required parameters and the instance name. Return a new instance of the distribution as `std::unique_ptr<DistributionSampler>`.

Also, here we define the `clone` method required by the interface, which returns a new instance of the distribution with the same parameters.

> [!Note]
> Put as first parameter the [name mentioned above](#distributionsampler-interface) in the constructor and constructor-like methods, followed by distribution-specific parameters.

```cpp
// libs/samplers/include/mjqm-samplers/exponential.hpp
// ...
#include <memory>
// ...
class Exponential : public DistributionSampler {
public: // direct and indirect constructors
    explicit Exponential(const std::string& name, double lambda) :
    DistributionSampler(name), lambda(lambda) {}

    static std::unique_ptr<DistributionSampler> with_rate(const std::string& name, const double rate) {
        return std::make_unique<Exponential>(name, rate);
    }
    static std::unique_ptr<DistributionSampler> with_mean(const std::string& name, const double mean) {
        return std::make_unique<Exponential>(name, 1. / mean);
    }

    std::unique_ptr<DistributionSampler> clone(const std::string& name) const override {
        return std::make_unique<Exponential>(name, lambda);
    }
    // ...
};
```

#### String conversion

Finally, we define the `operator std::string` method, returning all the information about the distribution.

> [!Note]
> Follow the template: `distribution_name (param1=val.ue ; param2=val.ue => mean=get_mean() ; variance=get_variance())`

```cpp
// libs/samplers/include/mjqm-samplers/exponential.hpp
// ...
#include <sstream>
#include <string>
// ...
class Exponential : public DistributionSampler {
public: // string conversion
    explicit operator std::string() const override {
        std::ostringstream oss;
        oss << "Exponential (lambda=" << lambda << " => mean=" << mean << " ; variance=" << variance << ")";
        return oss.str();
    }
};
```

#### Result

The final class looks like the one present in the repository at [`libs/samplers/include/mjqm-samplers/exponential.hpp`](https://github.com/unive-neds-lab/mjqm-simulator/blob/main/libs/samplers/include/mjqm-samplers/exponential.hpp).

## Make the class available

Now that we defined the class, we need to make it available to the simulator.
In order to do so, include it in the `samplers.h` _aggregator_ header, that is the one used where distributions are needed.

```cpp
// libs/samplers/include/mjqm-samplers/samplers.h
// ...
#include <mjqm-samplers/exponential.hpp>
// ...
```

## Implement the loader

The final piece to support our new distribution is to implement the loader function.
This function should read the parameters from the TOML configuration file, validate them, and create a new instance of the distribution sampler.

We also need to map the loader to the name to be used in the configuration file.

#### Declare the loader

In the `toml_distributions_loader.h` header, we declare the loader as `load_{distribution_name}` with the same signature as the other loaders (also defined at the top of the header as `distribution_loader` type definition).

Then, we add it to the `distribution_loaders` map at the end of the header, with an all-lowercase, space-separated key without accents.

```cpp
// libs/settings/include/mjqm-settings/toml_distributions_loader.h
// ...
bool load_exponential(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                      std::unique_ptr<DistributionSampler>* distribution // out
);
// ...
inline static std::unordered_map<std::string, distribution_loader> distribution_loaders = {
    // ...
    {"exponential", load_exponential},
    // ...
};
```

> [!Note]
> Keep both the loader declaration and the map element in alphabetical order for consistency.

The key in the map will be used in the configuration file as follows:

```toml
# ...
arrival.distribution = "exponential"
# ...
```

#### Implement the loader

Finally, we implement the loader function in the `toml_distributions_loader.cpp` file.
As previously stated, this function should read the parameters from the TOML table, validate them, and create a new instance of the distribution sampler.

As a quick recap, the exponential distribution is defined by the single parameter $\lambda$, but depending on the usecase it could also be defined using the mean $\mu$, and it could also be accompanied by some probability of the class.

We also need to support default values for the parameters.
So, we could find any of the following configurations in the TOML file for the arrival distribution:

```toml
arrival.distribution = "exponential"
# using the rate
arrival.lambda = 0.1
arrival.rate = 0.1
# using the mean
arrival.mean = 10
# with additional probability or overrides per class
[[class]]
arrival.prob = 0.5
arrival.rate = 0.2
```

The same should be supported by the `service` key, with the exclusion of the `prob` key, that only has meaning for the **arrival** distribution.

To avoid confusion in which parameter to use, we do not allow to define both `lambda` and `mean`, as they are either redundant or incoherent.
Moreover, we can accept either `lambda` or `rate`, as they have the same meaning, preferring the first one.

Finally, we look for the `prob` configuration only for the arrival distribution configuration.

> [!Note]
> When all classes define the `prob` configuration, we already normalised them in a previous step to sum up to 1 (see [normalise_probs in toml_loader.cpp](https://github.com/unive-neds-lab/mjqm-simulator/blob/385d9955a5fec296544d9ed9ce7588c25d865ecf/libs/simulator/src/mjqm-settings/toml_loader.cpp#L104))

To easily and idiomatically read the parameters, without worrying either about how the TOML library works, or about default values, we can use the helper function `distribution_parameter`: it takes one or more keys to look for in the configuration, and returns the first one found, or `std::nullopt` if none is found.

```cpp
// libs/simulator/src/mjqm-settings/toml_distributions_loader.cpp
// ...
bool load_exponential(const toml::table& data, const std::string_view& cls, const distribution_use& use, std::unique_ptr<DistributionSampler>* distribution) {
    const std::string name = full_name(cls, use);
    const std::optional<double> mean = distribution_parameter(data, cls, use, "mean");
    const std::optional<double> lambda = distribution_parameter(data, cls, use, "lambda", "rate");
    const double prob = use == ARRIVAL ? distribution_parameter(data, cls, use, "prob").value_or(1.) : 1.;
    if (mean.has_value() == lambda.has_value()) {
        print_error("Exponential distribution at path " << error_highlight(name) << " must have exactly one of mean or lambda/rate defined");
        return false;
    }
    if (mean.has_value()) {
        *distribution = Exponential::with_mean(name, mean.value() / prob);
    } else {
        *distribution = Exponential::with_rate(name, lambda.value() * prob);
    }
    return true;
}
// ...
```

Some particular behaviours to pay attention to, in order to replicate them:
- the `name` variable is built using the `full_name` helper function, that returns the complete TOML path of the distribution for the current class.
- we ignore the `prob` key if the distribution is not an arrival distribution using a default value of 1.
- the parameters consistency is checked as soon as possible, returning `false` and printing an error if too many or too few values are defined.
- we use the idiomatic static _constructors_ when building the distribution.

> [!Note]
> When our loader returns `false`, the simulator won't start the experiments, but will try to parse the remaining configuration, printing all the errors found before exiting.
