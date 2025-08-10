//
// Created by Marco Ciotola on 04/02/25.
//

#ifndef TOML_POLICIES_LOADERS_H
#define TOML_POLICIES_LOADERS_H

#include <unordered_map>

#include <mjqm-policies/policy.h>
#include <mjqm-settings/toml_loader.h>
#include <mjqm-settings/toml_utils.h>

typedef std::unique_ptr<Policy> (*policy_builder)(toml::table& data, ExperimentConfig& conf);

std::unique_ptr<Policy> smash_builder(toml::table& data, ExperimentConfig& conf);

std::unique_ptr<Policy> fifo_builder(toml::table& data, ExperimentConfig& conf);

std::unique_ptr<Policy> server_filling_builder(toml::table&, ExperimentConfig& conf);

std::unique_ptr<Policy> server_filling_mem_builder(toml::table&, ExperimentConfig& conf);

std::unique_ptr<Policy> back_filling_builder(toml::table&, ExperimentConfig& conf);

std::unique_ptr<Policy> quick_swap_builder(toml::table&, ExperimentConfig& conf);

std::unique_ptr<Policy> first_fit_builder(toml::table&, ExperimentConfig& conf);

std::unique_ptr<Policy> adaptive_msf_builder(toml::table&, ExperimentConfig& conf);

std::unique_ptr<Policy> static_msf_builder(toml::table&, ExperimentConfig& conf);

std::unique_ptr<Policy> most_server_first_builder(toml::table&, ExperimentConfig& conf);

inline static std::unordered_map<std::string_view, policy_builder> policy_builders = {
    {"fifo", fifo_builder},
    {"smash", smash_builder},
    {"server filling", server_filling_builder},
    {"server filling memoryful", server_filling_mem_builder},
    {"back filling", back_filling_builder},
    {"quick swap", quick_swap_builder},
    {"first fit", first_fit_builder},
    {"adaptive msf", adaptive_msf_builder},
    {"static msf", static_msf_builder},
    {"most server first", most_server_first_builder},
};

#endif // TOML_POLICIES_LOADERS_H
