//
// Created by Marco Ciotola on 04/02/25.
//

#include <mjqm-policies/policies.h>
#include <mjqm-settings/toml_loader.h>
#include <mjqm-settings/toml_policies_loaders.h>
#include <mjqm-settings/toml_utils.h>

std::unique_ptr<Policy> smash_builder(toml::table& data, ExperimentConfig& conf) {
    const auto window = data.at_path("policy.window").value<unsigned int>().value_or(2);
    conf.toml.insert_or_assign("policy.name", "smash");
    conf.toml.insert_or_assign("policy.window", window);
    conf.stats.add_pivot_column("policy.window", window);
    return std::make_unique<Smash>(window, conf.cores, conf.classes.size());
}

std::unique_ptr<Policy> fifo_builder(toml::table&, ExperimentConfig& conf) {
    // FIFO is a special case of Smash with window 1
    return std::make_unique<Smash>(1, conf.cores, conf.classes.size());
}

std::unique_ptr<Policy> server_filling_builder(toml::table&, ExperimentConfig& conf) {
    return std::make_unique<ServerFilling>(-1, conf.cores, conf.classes.size());
}

std::unique_ptr<Policy> server_filling_mem_builder(toml::table&, ExperimentConfig& conf) {
    return std::make_unique<ServerFillingMem>(-2, conf.cores, conf.classes.size());
}

std::unique_ptr<Policy> back_filling_builder(toml::table&, ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<BackFilling>(-3, conf.cores, n_classes, sizes);
}

std::unique_ptr<Policy> quick_swap_builder(toml::table& data, ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    const auto threshold = data.at_path("policy.threshold").value<int>().value_or(1);
    conf.toml.insert_or_assign("policy.name", "quick swap");
    conf.toml.insert_or_assign("policy.threshold", threshold);
    conf.stats.add_pivot_column("policy.threshold", threshold);
    return std::make_unique<QuickSwap>(-4, conf.cores, n_classes, sizes, threshold);
}

std::unique_ptr<Policy> first_fit_builder(toml::table&, ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<FirstFit>(-14, conf.cores, n_classes, sizes);
}

std::unique_ptr<Policy> adaptive_msf_builder(toml::table&, ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<AdaptiveMSF>(-7, conf.cores, n_classes, sizes);
}

std::unique_ptr<Policy> static_msf_builder(toml::table&, ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<StaticMSF>(-8, conf.cores, n_classes, sizes);
}

std::unique_ptr<Policy> most_server_first_builder(toml::table&, ExperimentConfig& conf) {
    std::vector<unsigned int> sizes;
    unsigned int n_classes = conf.get_sizes(sizes);
    return std::make_unique<MostServerFirst>(0, conf.cores, n_classes, sizes);
}
