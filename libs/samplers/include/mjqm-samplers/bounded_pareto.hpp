//
// Created by Marco Ciotola on 24/01/25.
//

#ifndef MJQM_SAMPLERS_BOUNDED_PARETO_H
#define MJQM_SAMPLERS_BOUNDED_PARETO_H

#include <cassert>
#include <cmath>
#include <memory>
#include <sstream>
#include <string>

#include <mjqm-samplers/sampler.h>

// Parameters
// L > 0 location (real)
// H > L location (real)
// α > 0 shape (real)

class BoundedPareto : public DistributionSampler {
public:
    // descriptive parameters and statistics
    const double l;
    const double h;
    const double alpha;
    const double prob;
    const double mean = alpha == 1.0 ? h * l / (h - l) * log(h / l)
                                   : (pow(l, alpha) / (1 - pow(l / h, alpha)) * alpha / (alpha - 1) *
                                      (1 / pow(l, alpha - 1) - 1 / pow(h, alpha - 1)));
    const double variance = alpha == 2.0 ? ((2 * pow(h, 2) * pow(l, 2)) / ((pow(h, 2) - pow(l, 2)))) * log(h / l)
                                       : (pow(l, alpha) / (1 - pow(l / h, alpha)) * alpha / (alpha - 2) *
                                          (1 / pow(l, alpha - 2) - 1 / pow(h, alpha - 2)));
    const double cv = sqrt(variance) / mean;

private:
    const double h_to_alpha = pow(h, alpha);
    const double l_to_alpha = pow(l, alpha);
    const double den = h_to_alpha * l_to_alpha;

public:
    // operative methods
    inline double get_mean() const override { return mean; }
    inline double get_variance() const override { return variance; }
    inline double get_prob() const override { return prob; }
    inline double sample() override {
        double u = randU01();
        double num = u * h_to_alpha - u * l_to_alpha - h_to_alpha;
        double frac = num / den;
        return pow(-frac, -1 / alpha);
    }

    // direct and indirect constructors
    explicit BoundedPareto(const std::string& name, double alpha, double l, double h) :
        DistributionSampler(name), l(l), h(h), alpha(alpha), prob(1.) {
        assert(l > 0.);
        assert(h > l);
        assert(alpha > 0.);
    }

    explicit BoundedPareto(const std::string& name, double alpha, double l, double h, double prob) :
        DistributionSampler(name), l(l), h(h), alpha(alpha), prob(prob) {
        assert(l > 0.);
        assert(h > l);
        assert(alpha > 0.);
    }

    static std::unique_ptr<DistributionSampler> with_rate(const std::string& name, double rate, double alpha) {
        return std::make_unique<BoundedPareto>(name, alpha, (12000.0 / 23999.0) / rate, 12000 / rate);
    }

    static std::unique_ptr<DistributionSampler> with_rate_and_prob(const std::string& name, double rate, double alpha, double prob) {
        return std::make_unique<BoundedPareto>(name, alpha, (12000.0 / 23999.0) / rate, 12000 / rate, prob);
    }

    static std::unique_ptr<DistributionSampler> with_mean(const std::string& name, double mean, double alpha) {
        return std::make_unique<BoundedPareto>(name, alpha, (12000.0 / 23999.0) * mean, 12000 * mean);
    }

    static std::unique_ptr<DistributionSampler> with_range(const std::string& name, double alpha, double l, double h) {
        return std::make_unique<BoundedPareto>(name, alpha, l, h);
    }

    static std::unique_ptr<DistributionSampler> with_range_and_prob(const std::string& name, double alpha, double l, double h, double prob) {
        return std::make_unique<BoundedPareto>(name, alpha, l, h, prob);
    }

    std::unique_ptr<DistributionSampler> clone(const std::string& name) const override {
        return std::make_unique<BoundedPareto>(name, alpha, l, h);
    }

    // string conversion
    explicit operator std::string() const override {
        std::ostringstream oss;
        oss << "bounded pareto (alpha=" << alpha << " ; l=" << l << " ; h=" << h << " => rate=" << 1.0/mean
            << " ; cv=" << cv << ")";
        return oss.str();
    }
};

#endif // MJQM_SAMPLERS_BOUNDED_PARETO_H
