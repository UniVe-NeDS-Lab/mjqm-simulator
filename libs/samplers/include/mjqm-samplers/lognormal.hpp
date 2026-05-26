//
// Created by Adityo Anggraito on 27/02/25.
//

#ifndef MJQM_SAMPLERS_LOGNORMAL_H
#define MJQM_SAMPLERS_LOGNORMAL_H

#include <cmath>
#include <memory>
#include <sstream>
#include <string>

#include <mjqm-samplers/sampler.h>

class Lognormal : public DistributionSampler {
public:
    explicit Lognormal(const std::string& name, const double mean, const double variance) :
        DistributionSampler(name), mean(mean), variance(variance), prob(1.) {
        std::pair<double, double> res = compute_normal_params(mean);
        this->mu = res.first;
        this->sigma = res.second;
    }

private:
    // Compute normal distribution parameters from lognormal mean & assumed stddev
    std::pair<double, double> compute_normal_params(double mu_L) {
        double sigma_L = 0.5 * mu_L; // Assume stddev is 50% of the mean
        double sigma = std::sqrt(std::log(1 + (sigma_L * sigma_L) / (mu_L * mu_L)));
        double mu = std::log(mu_L) - (sigma * sigma) / 2.0;
        std::pair<double, double> res(mu, sigma);
        return res;
    }

public: // descriptive parameters and statistics
    const double mean;
    const double variance;
    double mu;
    double sigma;
    const double prob;

public:
    inline double get_mean() const override { return mean; }
    inline double get_variance() const override { return variance; }
    inline double get_prob() const override { return prob; }
    inline double sample() override {
        double u, v, s;
        do {
            u = (randU01() * 2.0) - 1.0; // transform to (-1,1)
            v = (randU01() * 2.0) - 1.0;
            s = u * u + v * v;
        } while (s >= 1.0 || s == 0.0);

        // Standard normal variable
        double z = u * std::sqrt(-2.0 * std::log(s) / s);

        // Convert to lognormal
        return std::exp(mu + sigma * z);
    }

    static std::unique_ptr<DistributionSampler> with_mean(const std::string& name, double mean) {
        return std::make_unique<Lognormal>(name, mean, pow(0.5 * mean, 2)); // Assume stddev is 50% of the mean
    }

    std::unique_ptr<DistributionSampler> clone(const std::string& name) const override {
        return std::make_unique<Lognormal>(name, mean, pow(0.5 * mean, 2)); // Assume stddev is 50% of the mean
    }

    explicit operator std::string() const override {
        std::ostringstream oss;
        oss << "lognormal (mean=" << mean << " ; variance=" << variance << ")";
        return oss.str();
    }
};

#endif // MJQM_SAMPLERS_LOGNORMAL_H
