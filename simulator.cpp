//  main.cpp
//  Simula_smash
//
//  Created by Andrea Marin on 13/10/23.
//

#include <filesystem>
#include <fstream>
#include <iostream>
#include <ranges>
#include <string>
#include <thread>
#include <vector>

#include <boost/asio/post.hpp>
#include <boost/asio/thread_pool.hpp>

#include <mjqm-settings/toml_loader.h>
#include <mjqm-simulator/experiment_stats.h>
#include <mjqm-simulator/simulator.h>

void run_simulation(ExperimentConfig& conf) {
    Simulator sim(conf);
    sim.reset_simulation();
    sim.reset_statistics();

    sim.simulate(conf.events, conf.repetitions);
    sim.produce_statistics(conf.stats);
    std::ofstream out_file = std::ofstream(conf.output_filename(), std::ios::app);
    out_file << conf.stats << "\n";
    out_file.close();
}

int main(int argc, char* argv[]) {
    bool wants_help = argc < 2;
    for (int i = 1; !wants_help && i < argc; ++i) {
        std::string arg(argv[i]);
        wants_help = (arg == "--help" || arg == "-h");
    }
    if (wants_help) {
        std::cout << "Usage: simulator <config> [--key value ...] [--pivot --key value ...]\n"
                  << "\n"
                  << "  <config>        Name of a TOML file under Inputs/ (with or without .toml)\n"
                  << "  --key value     Override a configuration parameter (in-memory only)\n"
                  << "  --pivot         Start a new parameter sweep; subsequent --key values\n"
                  << "                  define a separate experiment group\n"
                  << "\n"
                  << "The simulator loads the config, runs the specified number of events and\n"
                  << "repetitions, and writes CSV results to Results/<config_name>/.\n"
                  << "Progress is printed as \"Repetition N Done\" after each repetition.\n"
                  << "\n"
                  << "Documentation: https://unive-neds-lab.github.io/mjqm-simulator/\n";
        return 0;
    }

    std::string input_name(argv[1]);
    if (!input_name.ends_with(".toml")) {
        input_name += ".toml";
    }
    auto overrides = parse_overrides_from_args(argc, argv);
    fs::path input_file = fs::current_path() / "Inputs" / input_name;
    if (!fs::exists(input_file)) {
        std::cerr << "Error: configuration file not found: " << input_file << std::endl;
        return 1;
    }
    auto experiments = from_toml(input_file, overrides);
    if (experiments->empty()) {
        std::cerr << "The provided identifier doesn't generate any configuration" << std::endl;
        return 1;
    }

    for (const auto& experiment : *experiments) {
        if (!experiment.first) {
            std::cerr << "Error reading TOML file" << std::endl;
            return 1;
        }
    }

    boost::asio::thread_pool pool(std::thread::hardware_concurrency());

    for (const auto& [name, conf] : *experiments) {
        std::cout << conf << std::endl;
        fs::path out_file_path = conf.output_filename();
        fs::create_directories(out_file_path.parent_path());
        std::ofstream out_file = std::ofstream(out_file_path, std::ios::app);
        if (out_file.tellp() == 0) {
            std::vector<unsigned int> sizes;
            std::vector<std::string> headers{};
            conf.stats.add_headers(headers);
            // Write the headers to the CSV file
            for (const std::string& header : headers) {
                out_file << header << ";";
            }
            out_file << "\n";
        }
    }
    for (size_t i = 0; i < experiments->size(); ++i) {
        boost::asio::post(pool, [&conf = experiments->at(i).second] { run_simulation(conf); });
    }
    pool.join();
    std::cout << "All threads joined" << std::endl;

    return 0;
}
