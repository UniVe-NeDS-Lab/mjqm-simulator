//
// Created by Marco Ciotola on 24/01/25.
//

#ifndef MJQM_SAMPLER_H
#define MJQM_SAMPLER_H

/// [interface]
#include <memory>
#include <string>

#include "RngStream.h"

class DistributionSampler {
protected:
    RngStream generator;

    inline double randU01() { return generator.RandU01(); }

public:
    const std::string name;

    explicit DistributionSampler(const std::string& name) : generator(name.data()), name(name) {}

    // operative methods
    virtual double sample() = 0;
    virtual double get_mean() const = 0;
    virtual double get_variance() const = 0;
    virtual double get_prob() const = 0;

    // factory methods
    virtual std::unique_ptr<DistributionSampler> clone(const std::string& name) const = 0;
    inline std::unique_ptr<DistributionSampler> clone() const { return clone(name); }

    virtual ~DistributionSampler() = default;
    explicit virtual operator std::string() const = 0;

    // compatibility layer to the standard library
    typedef double result_type;
    inline double operator()() { return sample(); }
};
/// [interface]

#endif // MJQM_SAMPLER_H
