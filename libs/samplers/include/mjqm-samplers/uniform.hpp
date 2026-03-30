//
// Created by Marco Ciotola on 24/01/25.
//

#ifndef MJQM_SAMPLERS_UNIFORM_H
#define MJQM_SAMPLERS_UNIFORM_H

#include <cassert>
#include <cmath>
#include <memory>
#include <sstream>
#include <string>

#include <mjqm-samplers/sampler.h>

class Uniform : public DistributionSampler {
public:
    // descriptive parameters and statistics
    const double min;
    const double max;
    const double prob;
    const double mean = (min + max) / 2.;
    const double variance = pow(max - min, 2.) / 12.;

private:
    const double diff = max - min;

public:
    // operative methods
    inline double get_mean() const override { return mean; }
    inline double get_variance() const override { return variance; }
    inline double get_prob() const override { return prob; }
    inline double sample() override { return randU01() * diff + min; }

    // factory methods
    explicit Uniform(const std::string& name, const double min, const double max) :
        DistributionSampler(name), min(min), max(max), prob(1.) {
        assert(min > 0);
        assert(max > min);
    }

    static std::unique_ptr<DistributionSampler> with_mean(const std::string& name, double mean) {
        return std::make_unique<Uniform>(name, .5 * mean, 1.5 * mean);
    }

    static std::unique_ptr<DistributionSampler> with_range(const std::string& name, double min, double max) {
        return std::make_unique<Uniform>(name, min, max);
    }

    std::unique_ptr<DistributionSampler> clone(const std::string& name) const override {
        return std::make_unique<Uniform>(name, min, max);
    }

    // string conversion
    explicit operator std::string() const override {
        std::ostringstream oss;
        oss << "uniform (range (" << min << ", " << max << ") => mean=" << mean << " ; variance=" << variance << ")";
        return oss.str();
    }
};

#endif // MJQM_SAMPLERS_UNIFORM_H
