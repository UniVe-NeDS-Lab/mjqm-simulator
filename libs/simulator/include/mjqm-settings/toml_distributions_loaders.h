//
// Created by Marco Ciotola on 04/02/25.
//

#ifndef TOML_DISTRIBUTIONS_LOADERS_H
#define TOML_DISTRIBUTIONS_LOADERS_H

#include <iostream>
#include <map>
#include <memory>
#include <string_view>
#include <unordered_map>

#include <mjqm-samplers/samplers.h>
#include <mjqm-settings/toml_utils.h>

enum distribution_use { ARRIVAL, SERVICE };
static const std::map<std::string_view, distribution_use> distribution_use_from_key = {{"arrival", ARRIVAL},
                                                                                       {"service", SERVICE}};
static const std::map<distribution_use, std::string> distribution_use_to_key = {{ARRIVAL, "arrival"},
                                                                                {SERVICE, "service"}};
inline std::ostream& operator<<(std::ostream& os, const distribution_use& use) {
    return os << distribution_use_to_key.at(use);
}

inline std::string full_name(const std::string_view& cls, const distribution_use& use) {
    return std::string(cls) + '.' + distribution_use_to_key.at(use);
}

typedef bool (*distribution_loader)(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                                    std::unique_ptr<DistributionSampler>* distribution // out
);

template <typename VAR_TYPE = double>
std::optional<VAR_TYPE> distribution_parameter(const toml::table& data, const std::string_view& cls,
                                               const distribution_use use, const std::string_view& param) {
    return either_optional<VAR_TYPE>(data.at_path(cls).at_path(distribution_use_to_key.at(use)).at_path(param),
                                     data.at_path(distribution_use_to_key.at(use)).at_path(param));
}

template <typename VAR_TYPE = double, typename... ALTS>
std::optional<VAR_TYPE> distribution_parameter(const toml::table& data, const std::string_view& cls,
                                               const distribution_use use, const std::string_view& param,
                                               const ALTS... alt_params) {
    auto opt_current = distribution_parameter<VAR_TYPE>(data, cls, use, param);
    if (opt_current.has_value()) {
        return opt_current;
    }
    return distribution_parameter<VAR_TYPE>(data, cls, use, alt_params...);
}

bool load_bounded_pareto(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                         std::unique_ptr<DistributionSampler>* distribution // out
);

bool load_deterministic(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                        std::unique_ptr<DistributionSampler>* distribution // out
);

bool load_exponential(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                      std::unique_ptr<DistributionSampler>* distribution // out
);

bool load_frechet(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                  std::unique_ptr<DistributionSampler>* distribution // out
);

bool load_lognormal(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                    std::unique_ptr<DistributionSampler>* distribution // out
);

bool load_uniform(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                  std::unique_ptr<DistributionSampler>* distribution // out
);

inline static std::unordered_map<std::string_view, distribution_loader> distribution_loaders = {
    {"exponential", load_exponential},
    {"deterministic", load_deterministic},
    {"bounded pareto", load_bounded_pareto},
    {"frechet", load_frechet},
    {"lognormal", load_lognormal},
    {"uniform", load_uniform},
};

bool load_distribution(const toml::table& data, const std::string_view& cls, const distribution_use& use,
                       std::unique_ptr<DistributionSampler>* sampler // out
);

// Load a distribution directly from a subtable that already contains the distribution parameters.
// Equivalent to load_distribution with cls="" and the subtable nested under the use key —
// makes the wrapper-table contract explicit rather than inline at every call site.
bool load_distribution_from_table(const toml::table& subtable, distribution_use use,
                                   std::unique_ptr<DistributionSampler>* out);

#endif // TOML_DISTRIBUTIONS_LOADERS_H
