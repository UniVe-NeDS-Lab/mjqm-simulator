//
// Created by Marco Ciotola on 30/01/25.
//

#include <ranges>
#include <algorithm>
#include <numeric>
#include <string>
#include <unordered_map>
#include <unordered_set>
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

bool load_class_from_toml(const toml::table& data, const std::string& index, ExperimentConfig& conf,
                           bool skip_arrival = false) {
    const auto full_key = toml::path(CLASS_ROOT).append(index);
    unsigned int cores;
    const bool cores_ok = load_into(data, toml::path(full_key).append("cores").str(), cores);
    const std::string name =
        data.at_path(full_key).at_path("name").value<std::string>().value_or(std::to_string(cores));
    std::unique_ptr<DistributionSampler> arrival_sampler;
    std::unique_ptr<DistributionSampler> service_sampler;
    bool arrival_ok = true;
    if (!skip_arrival) {
        arrival_ok = load_distribution(data, full_key.str(), ARRIVAL, &arrival_sampler);
    }
    // arrival_sampler may be null when skip_arrival=true; Simulator constructor guards this
    const bool service_ok = load_distribution(data, full_key.str(), SERVICE, &service_sampler);
    if (cores_ok && arrival_ok && service_ok) {
        conf.classes.emplace_back(name, cores, std::move(arrival_sampler), std::move(service_sampler));
        conf.stats.add_class(name);
        return true;
    }
    return false;
}

bool normalise_probs(toml::table& data) {
    const auto* classes = data.at_path(CLASS_ROOT).as_array();
    const size_t n = classes ? classes->size() : 0;
    std::vector<std::optional<double>> raw(n);
    size_t n_present = 0;
    for (size_t i = 0; i < n; ++i) {
        const std::string key = "[" + std::to_string(i) + "]";
        raw[i] = data.at_path(CLASS_ROOT).at_path(key).at_path("arrival.prob").value<double>();
        if (raw[i].has_value()) ++n_present;
    }
    if (n_present == 0) return true;  // probs optional; skip normalisation
    if (n_present != n) {
        print_error("Not all classes have the prob property defined. Define it for none or for all.");
        return false;
    }
    bool ok = true;
    for (size_t i = 0; i < n; ++i) {
        if (raw[i].value() < 0.0) {
            print_error("arrival.prob for class " << i << " is negative (" << raw[i].value()
                        << "); all probabilities must be >= 0");
            ok = false;
        }
    }
    if (!ok) return false;
    double sum = 0.0;
    for (size_t i = 0; i < n; ++i) sum += raw[i].value();
    if (sum == 0.0) {
        print_error("arrival.prob values are all zero — at least one class must have a positive probability");
        return false;
    }
    // Threshold allows floating-point input approximation (e.g. 3 classes at 1/3 each
    // written as 0.3333 sum to 0.9999) while catching real omission/duplication errors.
    if (std::abs(sum - 1.0) > 0.001) {
        static bool warned = false;
        if (!warned) {
            std::cerr << "arrival.prob values sum to " << sum << ", normalising — a class may have been "
                      << (sum < 1.0 ? "omitted" : "duplicated") << "\n";
            warned = true;
        }
    }
    if (std::abs(sum - 1.0) <= 0.001) return true;  // already normalised within tolerance
    for (size_t i = 0; i < n; ++i) {
        // fix values in-place so they can be correctly read by load_shared_arrival_probs and the distribution builder
        const auto path = toml::path(CLASS_ROOT).append("[" + std::to_string(i) + "]").append("arrival.prob");
        overwrite_value(data, path, raw[i].value() / sum);
    }
    return true;
}

bool load_shared_arrival_probs(const toml::table& data, std::vector<double>& out_probs) {
    const auto* classes = data.at_path(CLASS_ROOT).as_array();
    const size_t n = classes->size(); // guaranteed non-null and non-empty by the caller (from_toml checks classes array)
    // normalise_probs has already validated and normalised the prob values in the TOML;
    // here we just read them out (or fall back to equal split if none were defined).
    size_t n_present = 0;
    out_probs.resize(n);
    for (size_t i = 0; i < n; ++i) {
        const std::string key = "[" + std::to_string(i) + "]";
        const auto val = data.at_path(CLASS_ROOT).at_path(key).at_path("arrival.prob").value<double>();
        if (val.has_value()) { out_probs[i] = val.value(); ++n_present; }
    }
    if (n_present == 0) {
        out_probs.assign(n, 1.0 / static_cast<double>(n));
        std::cerr << "arrival.prob not defined for any class; assuming equal split (1/" << n << " per class)\n";
    }
    return true;
}

bool validate_class_arrival_keys(const toml::table& data, size_t n) {
    static const std::unordered_set<std::string> allowed = {"prob"};
    for (size_t i = 0; i < n; ++i) {
        const auto arrival_path =
            toml::path(CLASS_ROOT).append("[" + std::to_string(i) + "]").append("arrival");
        const auto* arr = data.at_path(arrival_path).as_table();
        if (!arr) continue;
        for (const auto& [k, v] : *arr) {
            if (!allowed.contains(std::string(k))) {
                print_error(error_highlight(arrival_path.str() + "." + std::string(k))
                            << " is not allowed when arrival.mode = \"shared\"; "
                            << "only arrival.prob is permitted");
                return false;
            }
        }
    }
    return true;
}

bool load_shared_arrival(const toml::table& data, ExperimentConfig& conf) {
    auto result = std::make_unique<SharedArrival>();
    bool ok = load_shared_arrival_probs(data, result->class_probs);
    ok = load_distribution(data, "", ARRIVAL, &result->sampler) && ok; // cls="" → both lookup paths resolve to top-level arrival.*
    if (ok) conf.shared_arrival = std::move(result);
    return ok;
}

bool from_toml(const fs::path& input_file, ExperimentConfig& conf) {
    toml::table data = toml::parse_file(input_file.string());
    return from_toml(data, conf);
}

bool from_toml(toml::table& data, ExperimentConfig& conf) {
    bool ok = true;
    conf.toml = data;
    const auto mode_str = data.at_path("arrival.mode").value<std::string>();
    const bool is_arrival_shared = mode_str.has_value() && mode_str.value() == "shared";
    if (mode_str.has_value() && !is_arrival_shared && mode_str.value() != "independent") {
        print_error("Unsupported arrival.mode " << error_highlight(mode_str.value())
                    << "; expected \"independent\" or \"shared\"");
        return false;
    }
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
        if (is_arrival_shared) {
            const auto rho = data.at_path("arrival.autocorr").value<double>();
            if (rho.has_value() && rho.value() != 1.0) {
                print_error("arrival.mode = \"shared\" with arrival.autocorr is not yet supported");
                ok = false;
            }
            ok = validate_class_arrival_keys(data, classes->size()) && ok;
            ok = load_shared_arrival(data, conf) && ok;
            for (size_t index = 0; index < classes->size(); ++index) {
                ok = load_class_from_toml(data, "[" + std::to_string(index) + "]", conf,
                                          /*skip_arrival=*/true) && ok;
            }
        } else {
            for (size_t index = 0; index < classes->size(); ++index) {
                ok = load_class_from_toml(data, "[" + std::to_string(index) + "]", conf) && ok;
            }
        }
        // Sort classes by cores ascending (ties broken by name) so that internal arrays
        // (sizes[], ser_time_samplers[], l[]) are indexed smallest-to-largest. Policies such
        // as first-fit rely on this order to route jobs to the smallest fitting class.
        // The same permutation is applied to all parallel per-class arrays (classes, class_probs,
        // class_stats); when adding a new one, add a call to apply_permutation below.
        std::vector<size_t> order(conf.classes.size());
        std::iota(order.begin(), order.end(), 0);
        std::ranges::sort(order, [&](size_t a, size_t b) {
            const auto& ca = conf.classes[a];
            const auto& cb = conf.classes[b];
            return ca.cores != cb.cores ? ca.cores < cb.cores : ca.name < cb.name;
        });
        auto apply_permutation = [&order]<typename T>(std::vector<T>& v) {
            assert(v.size() == order.size()); // mismatched lengths → UB or wrong simulation results
            std::vector<T> out;
            out.reserve(order.size());
            for (size_t i : order) out.push_back(std::move(v[i]));
            v = std::move(out);
        };
        apply_permutation(conf.classes);
        if (conf.shared_arrival) apply_permutation(conf.shared_arrival->class_probs);
        apply_permutation(conf.stats.class_stats);
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

std::vector<std::vector<double>> buildP(std::vector<double> p, double rho) {
    // Normalize p
    double sum = 0;
    for (double x : p) sum += x;
    for (auto &x : p) x /= sum;

    int n = p.size();
    std::vector<std::vector<double>> P(n, std::vector<double>(n));

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            //P[i][j] = (1.0 - rho) * p[j];
            if (i == j) {
                P[i][j] = 1-((1-p[j])/rho);  // add stickiness
            } else {
                double pij = p[j]/(1-p[i]);
                double qii = 1-((1-p[i])/rho);
                P[i][j] = pij*(1-qii);
            }
        }
    }

    return P;
}

Simulator::Simulator(ExperimentConfig& conf)
    : nclasses(static_cast<int>(conf.classes.size())),
      is_arrival_shared(conf.shared_arrival != nullptr) {
    this->n = static_cast<int>(conf.cores);
    this->w = conf.policy->get_w(); // TODO should transform all branches that need it here into methods of the policies
    this->rep_free_servers_distro.resize(conf.cores + 1);
    this->fel.resize(nclasses * 2);
    // departure slots [0..nclasses-1]: overwritten by resample() before first use
    // arrival slot [nclasses]: zero-initialised so update_arrival_fel seeds on first resample()
    // slots [nclasses+1..2*nclasses-1]: max in shared mode (never selected by min_element); zero in independent mode
    if (is_arrival_shared && nclasses > 1) {
        std::fill(this->fel.begin() + nclasses + 1, this->fel.end(), std::numeric_limits<double>::max());
    }
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
    this->autocorr = false;

    occupancy_buf.resize(nclasses);
    occupancy_ser.resize(nclasses);
    completion.resize(nclasses);
    preemption.resize(nclasses);
    rawWaitingTime.resize(nclasses);
    rawResponseTime.resize(nclasses);
    /*autocorr_phase_times.resize(8);
    autocorr_phases.resize(8);
    autocorr_phase_time_list.resize(8);
    autocorr_residuals.resize(8);
    autocorr_residual_list.resize(8);*/
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
        ser_time_samplers.push_back(cls.service_sampler->clone());
        if (!conf.shared_arrival && cls.arrival_sampler) {
            arr_time_samplers.push_back(cls.arrival_sampler->clone());
            l.push_back(1. / cls.arrival_sampler->get_mean());
        } else {
            l.push_back(0.0); // placeholder; corrected below for shared_arrival mode
        }
        u.push_back(cls.service_sampler->get_mean());
    }
    //std::string autocorr = conf.toml.at_path("arrival.type").value<std::string>().value_or("standard");
    if (conf.shared_arrival) {
        this->shared_arrival_sampler = conf.shared_arrival->sampler->clone();
        this->shared_arrival_probs = conf.shared_arrival->class_probs;
        this->class_selection_stream.emplace("shared_arrival.class_selection");
        const double total_rate = 1.0 / shared_arrival_sampler->get_mean();
        for (int i = 0; i < nclasses; ++i) {
            l[i] = total_rate * shared_arrival_probs[i];
        }
    }
    double rho = conf.toml.at_path("arrival.autocorr").value<double>().value_or(1.0);
    if (rho == 1.0) { // iid identity; treat as if autocorr is absent
        return;
    }
    autocorr = true;
    std::vector<std::vector<double>> P = buildP(l, rho);
    arr_time_samplers.clear();
    int idx = 0;
    for (const auto &row : P) {
        int jdx = 0;
        for (double v : row) {
            //std::cout << v*conf.toml.at_path("arrival.rate").value<double>().value_or(1.0) << " ";
            arr_time_samplers.push_back(Exponential::with_rate("arrival_autocorr_"+idx+'.'+jdx, 
                                                                v*conf.toml.at_path("arrival.rate").value<double>().value_or(1.0)));
            jdx += 1;
        }
        //std::cout << "\n";
        idx += 1;
    }
    // for debugging purposes, all simulations should print the same state of the RNG,
    // unless some distribution is deterministic only in some of them
    // RngStream(("After Last " + conf.output_filename()).data()).WriteStateFull();
}
