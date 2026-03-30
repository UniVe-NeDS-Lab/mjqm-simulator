//
// Created by Marco Ciotola on 04/02/25.
//

#include <mjqm-policies/policies.h>
#include <mjqm-settings/toml_loader.h>
#include <mjqm-settings/toml_policies_loaders.h>
#include <mjqm-settings/toml_utils.h>
#include <cmath>    // std::floor
#include <numeric>  // std::accumulate

std::unique_ptr<Policy> smash_builder(const toml::table& data, const ExperimentConfig& conf) {
    const auto window = data.at_path("policy.window").value<unsigned int>().value_or(2);
    return std::make_unique<Smash>(window, conf.cores, conf.classes.size());
}

std::unique_ptr<Policy> fifo_builder(const toml::table&, const ExperimentConfig& conf) {
    // FIFO is a special case of Smash with window 1
    return std::make_unique<Smash>(1, conf.cores, conf.classes.size());
}

std::unique_ptr<Policy> server_filling_builder(const toml::table&, const ExperimentConfig& conf) {
    return std::make_unique<ServerFilling>(-1, conf.cores, conf.classes.size());
}

std::unique_ptr<Policy> server_filling_mem_builder(const toml::table&, const ExperimentConfig& conf) {
    return std::make_unique<ServerFillingMem>(-2, conf.cores, conf.classes.size());
}

std::unique_ptr<Policy> back_filling_builder(const toml::table&, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<BackFilling>(-3, conf.cores, n_classes, sizes);
}

std::unique_ptr<Policy> back_filling_imperfect_builder(const toml::table& data, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    const auto overestimate_max = data.at_path("policy.overest").value<double>().value_or(1.0);
    return std::make_unique<BackFillingImperfect>(-13, conf.cores, n_classes, sizes, overestimate_max);
}

std::unique_ptr<Policy> balanced_splitting_builder(const toml::table& data, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    std::vector<double> lambdas;
    std::vector<double> srv_times;
    for (const auto& cls : conf.classes) {
        lambdas.push_back(1. / cls.arrival_sampler->get_mean());
        srv_times.push_back(cls.service_sampler->get_mean());
    }
    const auto psi = data.at_path("policy.psi").value<double>().value_or(1.0);

    if (psi > 1.0) {
        std::vector<int> result(sizes.size());
        return std::make_unique<BalancedSplitting>(-18, conf.cores, n_classes, sizes, result, psi, conf.cores, 0);
    }

    std::vector<double> q(sizes.size());

    for (size_t i = 0; i < sizes.size(); ++i) {
        q[i] = static_cast<double>(sizes[i]) * lambdas[i] * srv_times[i];
    }

    double q_total = std::accumulate(q.begin(), q.end(), 0.0);

    std::vector<int> result(sizes.size());

    // compute floor(psi * (k/sizes[i]) * (q[i]/q_total)) * sizes[i]
    for (size_t i = 0; i < sizes.size(); ++i) {
        double val = psi * (static_cast<double>(conf.cores) / sizes[i]) * (q[i] / q_total);
        result[i] = static_cast<int>(std::floor(val) * sizes[i]);
    }

    for (size_t i = 0; i < sizes.size(); ++i) {
        std::cout << result[i] << std::endl;
    }

    int rsv_total = std::accumulate(result.begin(), result.end(), 0);

    return std::make_unique<BalancedSplitting>(-18, conf.cores, n_classes, sizes, result, psi, conf.cores-rsv_total, rsv_total);
}

std::unique_ptr<Policy> kill_smart_builder(const toml::table& data, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    const auto max_kill_cycle = data.at_path("policy.k").value<int>().value_or(10);
    const auto kill_threshold = data.at_path("policy.v").value<int>().value_or(1);
    //if (kill_threshold > max_stopped_size) {
    //    std::cerr << "v cannot be higher than k" << std::endl;
    //    return;
    //}
    return std::make_unique<KillSmart>(-16, conf.cores, n_classes, sizes, max_kill_cycle, kill_threshold);
}

std::unique_ptr<Policy> dual_kill_builder(const toml::table& data, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    const auto max_kill_cycle = data.at_path("policy.k").value<int>().value_or(10);
    const auto kill_threshold = data.at_path("policy.v").value<int>().value_or(1);
    //if (kill_threshold > max_stopped_size) {
    //    std::cerr << "v cannot be higher than k" << std::endl;
    //    return;
    //}
    return std::make_unique<DualKill>(-17, conf.cores, n_classes, sizes, max_kill_cycle, kill_threshold);
}

std::unique_ptr<Policy> quick_swap_builder(const toml::table& data, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    const auto threshold = data.at_path("policy.threshold").value<int>().value_or(1);
    return std::make_unique<QuickSwap>(-4, conf.cores, n_classes, sizes, threshold);
}

std::unique_ptr<Policy> first_fit_builder(const toml::table&, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<FirstFit>(-14, conf.cores, n_classes, sizes);
}

std::unique_ptr<Policy> lcfs_builder(const toml::table&, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<LCFS>(-19, conf.cores, n_classes, sizes);
}

std::unique_ptr<Policy> adaptive_msf_builder(const toml::table&, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<AdaptiveMSF>(-7, conf.cores, n_classes, sizes);
}

std::unique_ptr<Policy> static_msf_builder(const toml::table&, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<StaticMSF>(-8, conf.cores, n_classes, sizes);
}

std::unique_ptr<Policy> most_server_first_builder(const toml::table&, const ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<MostServerFirst>(0, conf.cores, n_classes, sizes);
}
