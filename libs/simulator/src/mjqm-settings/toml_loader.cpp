//
// Created by Marco Ciotola on 30/01/25.
//

#include <ranges>
#include <string>
#include <unordered_map>
#include <variant>

#include <mjqm-policies/policies.h>
#include <mjqm-samplers/random_ecuyer.h>
#include <mjqm-settings/toml_distributions_loaders.h>
#include <mjqm-settings/toml_loader.h>
#include <mjqm-settings/toml_overrides.h>
#include <mjqm-settings/toml_policies_loaders.h>
#include <mjqm-settings/toml_utils.h>
#include <mjqm-simulator/simulator.h>

#include "RngStream.h"

using namespace std::string_literals;

constexpr auto CLASS_ROOT = "class";

unsigned int ExperimentConfig::get_sizes(std::vector<unsigned int>& sizes) const {
    sizes.reserve(classes.size());
    sizes.clear();
    for (const auto& class_config : classes) {
        sizes.push_back(class_config.cores);
    }
    return classes.size();
}

bool load_class_from_toml(const toml::table& data, const std::string& index, ExperimentConfig& conf) {
    const auto full_key = toml::path(CLASS_ROOT).append(index);
    unsigned int cores;
    const bool cores_ok = load_into(data, toml::path(full_key).append("cores").str(), cores);
    const std::string name =
        data.at_path(full_key).at_path("name").value<std::string>().value_or(std::to_string(cores));
    std::unique_ptr<DistributionSampler> arrival_sampler;
    std::unique_ptr<DistributionSampler> service_sampler;
    const bool arrival_ok = load_distribution(data, full_key.str(), ARRIVAL, &arrival_sampler);
    const bool service_ok = load_distribution(data, full_key.str(), SERVICE, &service_sampler);
    if (cores_ok && arrival_ok && service_ok) {
        conf.classes.emplace_back(name, cores, std::move(arrival_sampler), std::move(service_sampler));
        conf.stats.add_class(name);
        return true;
    }
    return false;
}

bool normalise_probs(toml::table& data) {
    std::unordered_map<std::string, double> arrival_probs;
    const size_t n_classes = data[CLASS_ROOT].as_array()->size();
    for (size_t index = 0; index < n_classes; ++index) {
        const auto key = "[" + std::to_string(index) + "]";
        const auto arrival_prob = data.at_path(CLASS_ROOT).at_path(key).at_path("arrival.prob").value<double>();
        if (arrival_prob.has_value()) {
            arrival_probs[key] = arrival_prob.value();
        }
    }
    if (!arrival_probs.empty()) {
        if (arrival_probs.size() == n_classes) {
            double sum = 0.0;
            for (const auto p : std::views::values(arrival_probs)) {
                sum += p;
            }
            if (sum == 1.) {
                return true;
            }
            for (auto& [key, p] : arrival_probs) {
                p /= sum;
                // fix values in-place so they can be correctly read by distribution builder
                auto path = toml::path(CLASS_ROOT).append(key).append("arrival.prob");
                overwrite_value(data, path, p);
            }
        } else {
            print_error("Not all classes have the prob property defined. Define it for none or for all.");
            return false;
        }
    }
    return true;
}

bool from_toml(const fs::path& input_file, ExperimentConfig& conf) {
    toml::table data = toml::parse_file(input_file.string());
    return from_toml(data, conf);
}

bool from_toml(toml::table& data, ExperimentConfig& conf) {
    bool ok = true;
    conf.toml = data;
    ok = ok && load_into(data, "identifier", conf.name);
    ok = ok && load_into(data, "events", conf.events);
    ok = ok && load_into(data, "repetitions", conf.repetitions);
    ok = ok && load_into(data, "cores", conf.cores);
    conf.policy_name =
        either_optional(data.at_path("policy").value<std::string>(), data.at_path("policy.name").value<std::string>())
            .value_or("smash"s);
    ok = ok && load_into(data, "generator", conf.generator, "lecuyer"s);
    if (conf.generator != "lecuyer") {
        print_error("Unsupported generator " << error_highlight(conf.generator));
        return false;
    }

    if (toml::array* classes = data.at_path(CLASS_ROOT).as_array()) {
        ok = normalise_probs(data) && ok;
        for (size_t index = 0; index < classes->size(); ++index) {
            ok = load_class_from_toml(data, "[" + std::to_string(index) + "]", conf) && ok;
            // keep going if one soft fails to show all errors
        }
        // sort classes by cores, or alphabetically by name if cores are equal
        std::ranges::sort(conf.classes, [](const ClassConfig& a, const ClassConfig& b) {
            if (a.cores == b.cores) {
                return a.name < b.name;
            }
            return a.cores < b.cores;
        });
    }

    if (!policy_builders.contains(conf.policy_name)) {
        print_error("Unsupported policy " << error_highlight(conf.policy_name));
        return false;
    }
    conf.policy = policy_builders.at(conf.policy_name)(data, conf);
    if (toml::array* columns = data.at_path("output.columns").as_array()) {
        for (const auto& column : *columns) {
            if (!column.value<std::string>().has_value()) {
                ok = false;
                // print_error("Column " << error_highlight(column) << " badly defined");
                continue;
            }
            auto column_str = column.value<std::string>().value();
            if (column_str == "*" || column_str == "-*") {
                conf.stats.set_computed_columns_visibility(column_str == "*");
                continue;
            }
            if (column_str.ends_with("]")) {
                if (column_str.ends_with("[*]")) {
                    conf.stats.set_class_column_visibility(column_str.substr(0, column_str.size() - 4));
                    continue;
                }
                if (auto class_start_at = column_str.find("[")) {
                    auto class_name = column_str.substr(class_start_at + 1, column_str.size() - class_start_at - 2);
                    conf.stats.set_class_column_visibility(column_str.substr(0, class_start_at - 1), class_name);
                    continue;
                }
                print_error("Column " << error_highlight(column_str) << " badly defined");
            }
            conf.stats.set_column_visibility(column_str);
        }
    }

    return ok;
}

void from_toml(const std::unique_ptr<std::vector<std::pair<bool, ExperimentConfig>>>& experiments,
               const toml::table& data, const std::multimap<std::string, ConfigValue>& overrides = {}) {
    toml_overrides arguments_overrides(overrides);
    for (const auto override : arguments_overrides) {
        toml::table overridden_data(data);
        auto& [success, config] = experiments->emplace_back();
        for (const auto& [key, value] : override) {
            std::visit(
                [&](auto&& value) {
                    using T = std::decay_t<decltype(value)>;
                    overwrite_value<T>(overridden_data, key, value);
                    if constexpr (toml::is_table<T>) {
                        static_cast<toml::table>(value).for_each([&](auto&& inner_key, auto&& val) {
                            using T = std::decay_t<decltype(val)>;
                            if constexpr (is_override_value<T>) {
                                config.stats.add_pivot_column(std::string(toml::path(key) + inner_key), val.get());
                            }
                        });
                    } else {
                        config.stats.add_pivot_column(key, value);
                    }
                },
                value);
        }
        success = from_toml(overridden_data, config);
    }
}

std::unique_ptr<std::vector<std::pair<bool, ExperimentConfig>>>
from_toml(const toml::table& data, const std::vector<std::multimap<std::string, ConfigValue>>& arguments_overrides) {
    auto experiments = std::make_unique<std::vector<std::pair<bool, ExperimentConfig>>>();
    if (auto vars = data.at_path("pivot").as_array()) {
        for (auto& var : *vars) {
            auto file_overrides = parse_overrides_from_pivot(*var.as_table());
            if (arguments_overrides.empty()) {
                from_toml(experiments, data, file_overrides);
            } else {
                for (const auto& arg_pivot : arguments_overrides) {
                    from_toml(experiments, data, merge_overrides(file_overrides, arg_pivot));
                }
            }
        }
    }
    if (experiments->empty()) { // catch both no pivot and empty pivot list
        if (arguments_overrides.empty()) {
            from_toml(experiments, data);
        } else {
            for (const auto& arg_pivot : arguments_overrides) {
                from_toml(experiments, data, arg_pivot);
            }
        }
    }
    return experiments;
}

std::unique_ptr<std::vector<std::pair<bool, ExperimentConfig>>>
from_toml(const fs::path& input_file, const std::vector<std::multimap<std::string, ConfigValue>>& overrides) {
    toml::table data = toml::parse_file(input_file.string());
    return from_toml(data, overrides);
}

Simulator::Simulator(ExperimentConfig& conf) : nclasses(static_cast<int>(conf.classes.size())) {
    this->n = static_cast<int>(conf.cores);
    this->w = conf.policy->get_w(); // TODO should transform all branches that need it here into methods of the policies
    // this->rep_free_servers_distro = std::vector<double>(conf.cores + 1);
    this->fel.resize(nclasses * 2);
    this->job_fel.resize(nclasses * 2);
    this->jobs_inservice.resize(nclasses);
    this->jobs_preempted.resize(nclasses);
    this->curr_job_seq.resize(nclasses);
    this->tot_job_seq.resize(nclasses);
    this->curr_job_seq_start.resize(nclasses);
    this->tot_job_seq_dur.resize(nclasses);
    this->job_seq_amount.resize(nclasses);
    this->debugMode = false;
    this->policy = conf.policy->clone();
    this->stats = &conf.stats;

    occupancy_buf.resize(nclasses);
    occupancy_ser.resize(nclasses);
    completion.resize(nclasses);
    preemption.resize(nclasses);
    rawWaitingTime.resize(nclasses);
    rawResponseTime.resize(nclasses);
    waste = 0;
    viol = 0;
    occ = 0;

    auto lock = std::lock_guard(RNG_STREAMS_GENERATION_LOCK);
    RngStream::SetPackageSeed(MJQM_RANDOM_ECUYER_SEED);
    bool class_stats_missing = this->stats->class_stats.empty();
    for (const auto& cls : conf.classes) {
        if (class_stats_missing) {
            conf.stats.add_class(cls.name);
        }
        sizes.push_back(cls.cores);
        class_names.push_back(cls.name);
        arr_time_samplers.push_back(cls.arrival_sampler->clone());
        ser_time_samplers.push_back(cls.service_sampler->clone());
        l.push_back(1. / cls.arrival_sampler->get_mean());
    }
    // for debugging purposes, all simulations should print the same state of the RNG,
    // unless some distribution is deterministic only in some of them
    // RngStream(("After Last " + conf.output_filename()).data()).WriteStateFull();
}
