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
    const double mean = raw_moment(alpha, l, h, 1);
    const double second_moment = raw_moment(alpha, l, h, 2);
    const double variance = second_moment - mean * mean;
    const double cv = sqrt(variance) / mean;

private:
    const double h_to_alpha = pow(h, alpha);
    const double l_to_alpha = pow(l, alpha);
    const double den = h_to_alpha * l_to_alpha;

    // E[X^k] = (L^α / D) · (α / (α−k)) · (L^{k−α} − H^{k−α}),  special case α = k
    [[nodiscard]] static double raw_moment(const double alpha, const double l, const double h, const int k) noexcept {
        const double kd = static_cast<double>(k);
        const double d = 1.0 - pow(l / h, alpha); // 1 − (L/H)^α
        const double norm = pow(l, alpha) / d; // L^α / D
        if (alpha == kd) {
            const double log_range = log(h / l); // ln(H/L)
            return kd * norm * log_range; // k · Lᵏ/D · ln(H/L)
        }
        const double moment_scale = alpha / (alpha - kd); // α / (α−k)
        const double range_term = pow(l, kd - alpha) - pow(h, kd - alpha); // L^{k−α} − H^{k−α}
        return norm * moment_scale * range_term;
    }

public:
    // operative methods
    inline double get_mean() const override { return mean; }
    inline double get_variance() const override { return variance; }

    inline double sample() override {
        double u = randU01();
        double num = u * h_to_alpha - u * l_to_alpha - h_to_alpha;
        double frac = num / den;
        return pow(-frac, -1 / alpha);
    }

    // direct and indirect constructors
    explicit BoundedPareto(const std::string& name, double alpha, double l, double h) :
        DistributionSampler(name), l(l), h(h), alpha(alpha) {
        assert(l > 0.);
        assert(h > l);
        assert(alpha > 0.);
    }

    static std::unique_ptr<DistributionSampler> with_rate(const std::string& name, double rate, double alpha) {
        return std::make_unique<BoundedPareto>(name, alpha, (12000.0 / 23999.0) / rate, 12000 / rate);
    }

    static std::unique_ptr<DistributionSampler> with_mean(const std::string& name, double mean, double alpha) {
        return std::make_unique<BoundedPareto>(name, alpha, (12000.0 / 23999.0) * mean, 12000 * mean);
    }

    static std::unique_ptr<DistributionSampler> with_range(const std::string& name, double alpha, double l, double h) {
        return std::make_unique<BoundedPareto>(name, alpha, l, h);
    }

    std::unique_ptr<DistributionSampler> clone(const std::string& name) const override {
        return std::make_unique<BoundedPareto>(name, alpha, l, h);
    }

    // string conversion
    explicit operator std::string() const override {
        std::ostringstream oss;
        oss << "bounded pareto (alpha=" << alpha << " ; l=" << l << " ; h=" << h
            << " => mean=" << mean << " ; variance=" << variance << " ; cv=" << cv << ")";
        return oss.str();
    }
};

#endif // MJQM_SAMPLERS_BOUNDED_PARETO_H
