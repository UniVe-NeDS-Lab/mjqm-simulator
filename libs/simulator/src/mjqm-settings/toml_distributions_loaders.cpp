//
// Created by Marco Ciotola on 04/02/25.
//

#include <unordered_map>

#include <mjqm-samplers/samplers.h>
#include <mjqm-settings/toml_distributions_loaders.h>

#include "mjqm-samplers/frechet.hpp"

#ifndef XOR
#define XOR(a, b) (!(a) != !(b))
#endif // XOR

bool load_bounded_pareto(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                         std::unique_ptr<DistributionSampler>* distribution // out
) {
    const std::string name = full_name(cls, use);
    const std::optional<double> alpha = distribution_parameter(data, cls, use, "alpha");
    const std::optional<double> mean = distribution_parameter(data, cls, use, "mean");
    const std::optional<double> rate = distribution_parameter(data, cls, use, "rate");
    const std::optional<double> l = distribution_parameter(data, cls, use, "l", "L", "min");
    const std::optional<double> h = distribution_parameter(data, cls, use, "h", "H", "max");
    const double prob = use == ARRIVAL ? distribution_parameter(data, cls, use, "prob").value_or(1.) : 100.;
    if (use == ARRIVAL) {
        if (l.has_value() && h.has_value() && prob < 2.){
            *distribution = BoundedPareto::with_range_and_prob(name, alpha.value(), l.value(), h.value(), prob);
            return true;
        }
        else if (prob < 2.) {
            *distribution = BoundedPareto::with_rate_and_prob(name, rate.value(), alpha.value(), prob);
            return true;
        }
    }
    if (!alpha.has_value() || !XOR(XOR(mean.has_value(), rate.has_value()), l.has_value() && h.has_value())) {
        print_error("Bounded pareto distribution at path "
                    << error_highlight(name) << " must have alpha defined, and either mean, rate or the l/h pair");
        return false;
    }
    if (mean.has_value()) {
        *distribution = BoundedPareto::with_mean(name, mean.value(), alpha.value());
        return true;
    }
    if (rate.has_value()) {
        *distribution = BoundedPareto::with_rate(name, rate.value(), alpha.value());
        return true;
    }
    if (l.value() <= 0. || h.value() <= l.value() || alpha.value() <= 0.) {
        print_error("Bounded pareto distribution at path " << error_highlight(name)
                                                           << " must have l > 0 and h > l and alpha > 0");
        return false;
    }
    *distribution = BoundedPareto::with_range(name, alpha.value(), l.value(), h.value());
    return true;
}

bool load_deterministic(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                        std::unique_ptr<DistributionSampler>* distribution // out
) {
    const std::string name = full_name(cls, use);
    const std::optional<double> value = distribution_parameter(data, cls, use, "value", "mean");
    const double prob = use == ARRIVAL ? distribution_parameter(data, cls, use, "prob").value_or(1.) : 100.;
    if (!value.has_value()) {
        print_error("Deterministic distribution at path " << error_highlight(name) << " must have value/mean defined");
        return false;
    }
    if (value.value() <= 0) {
        print_error("Deterministic distribution at path " << error_highlight(name) << " must have value > 0");
        return false;
    }
    if (use == ARRIVAL) {
        if (prob < 2.) {
            *distribution = Deterministic::with_prob(name, value.value(), prob);
            return true;
        }
    }
    *distribution = Deterministic::with_value(name, value.value());
    return true;
}

bool load_exponential(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                      std::unique_ptr<DistributionSampler>* distribution // out
) {
    const std::string name = full_name(cls, use);
    const std::optional<double> mean = distribution_parameter(data, cls, use, "mean");
    const std::optional<double> lambda = distribution_parameter(data, cls, use, "lambda", "rate");
    const double prob = use == ARRIVAL ? distribution_parameter(data, cls, use, "prob").value_or(1.) : 1.;
    if (mean.has_value() == lambda.has_value()) {
        print_error("Exponential distribution at path " << error_highlight(name)
                                                        << " must have exactly one of mean or lambda/rate defined");
        return false;
    }
    if (mean.has_value()) {
        *distribution = Exponential::with_mean(name, mean.value() / prob);
    } else {
        *distribution = Exponential::with_rate(name, lambda.value() * prob);
    }
    return true;
}

bool load_frechet(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                  std::unique_ptr<DistributionSampler>* distribution // out
) {
    const std::string name = full_name(cls, use);
    const std::optional<double> alpha = distribution_parameter(data, cls, use, "alpha");
    const std::optional<double> mean = distribution_parameter(data, cls, use, "mean");
    const std::optional<double> rate = distribution_parameter(data, cls, use, "rate");
    const std::optional<double> s = distribution_parameter(data, cls, use, "s");
    const double m = distribution_parameter(data, cls, use, "m").value_or(0.);
    if (!alpha.has_value() || !XOR(XOR(mean.has_value(), s.has_value()), rate.has_value())) {
        print_error("Fréchet distribution at path "
                    << error_highlight(name)
                    << " must have alpha defined, and either mean, rate or s, while m has default value 0");
        return false;
    }
    if (alpha.value() <= 1 || m < 0) {
        print_error("Fréchet distribution at path " << error_highlight(name) << " must have alpha > 1 and m >= 0");
        return false;
    }
    if (mean.has_value()) {
        *distribution = Frechet::with_mean(name, mean.value(), alpha.value(), m);
        return true;
    }
    if (rate.has_value()) {
        *distribution = Frechet::with_rate(name, rate.value(), alpha.value(), m);
        return true;
    }
    if (s.value() < 0) {
        print_error("Fréchet distribution at path " << error_highlight(name) << " must have s >= 0");
        return false;
    }
    *distribution = Frechet::with(name, alpha.value(), s.value(), m);
    return true;
}

bool load_lognormal(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                    std::unique_ptr<DistributionSampler>* distribution // out
) {
    const std::string name = full_name(cls, use);
    const std::optional<double> mean = distribution_parameter(data, cls, use, "mean");
    if (!mean.has_value()) {
        print_error("Lognormal distribution at path " << error_highlight(name) << " must have mean defined");
        return false;
    }
    *distribution = Lognormal::with_mean(name, mean.value());
    return true;
}

bool load_uniform(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                  std::unique_ptr<DistributionSampler>* distribution // out
) {
    const std::string name = full_name(cls, use);
    const std::optional<double> mean = distribution_parameter(data, cls, use, "mean");
    const std::optional<double> min = distribution_parameter(data, cls, use, "min", "a");
    const std::optional<double> max = distribution_parameter(data, cls, use, "max", "b");
    if (!XOR(mean.has_value(), min.has_value() && max.has_value())) {
        print_error("Uniform distribution at path "
                    << error_highlight(name)
                    << " must have either the pair of a/min and b/max defined, or mean defined");
        return false;
    }
    if (mean.has_value()) {
        if (mean.value() <= 0) {
            print_error("Uniform distribution at path " << error_highlight(name) << " must have mean > 0");
            return false;
        }
        *distribution = Uniform::with_mean(name, mean.value());
        return true;
    }
    if (min.value() <= 0 || min.value() >= max.value()) {
        print_error("Uniform distribution at path " << error_highlight(name) << " must have 0 < min < max");
        return false;
    }
    *distribution = Uniform::with_range(name, min.value(), max.value());
    return true;
}

bool load_distribution(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                       std::unique_ptr<DistributionSampler>* sampler // out
) {
    std::optional<std::string> type = distribution_parameter<std::string>(data, cls, use, "distribution");
    if (!type.has_value()) {
        print_error("Distribution type missing at path " << error_highlight(cls << "." << use));
        return false;
    }
    const std::string& distribution = type.value();
    if (!distribution_loaders.contains(distribution)) {
        print_error("Unsupported distribution " << error_highlight(distribution) << " at path "
                                                << error_highlight(cls << "." << use));
        return false;
    }
    return distribution_loaders.at(distribution)(data, cls, use, sampler);
}
