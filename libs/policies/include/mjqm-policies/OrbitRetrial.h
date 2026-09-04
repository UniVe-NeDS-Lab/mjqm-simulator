//
// Created by Adityo Anggraito on 21/01/25.
//

#ifndef ORBITRETRIAL_H
#define ORBITRETRIAL_H

#include <map>

#include <mjqm-policies/policy.h>
#include <mjqm-utils/string.hpp>

class OrbitRetrial final : public Policy {
public:
    OrbitRetrial(const int w, const int servers, const int classes, const std::vector<unsigned int>& sizes, const int r_max, const double sigma, const int retry_ind) :
        state_buf(classes), state_ser(classes), state_orb(classes), stopped_jobs(classes), ongoing_jobs(classes), freeservers(servers),
        servers(servers), w(w), sizes(sizes), violations_counter(0), r_max(r_max), freeorbits(r_max), sigma(sigma), retry_ind(retry_ind) {}
    void arrival(int c, int size, long int id) override;
    void departure(int c, int size, long int id) override;
    void retry() override;
    double get_sigma() override;
    bool fit_jobs(std::unordered_map<long int, double> holdTime, double simTime) override { return false; };
    double get_overest_max() override { return 1.0; }
    const std::vector<int>& get_state_ser() override { return state_ser; }
    const std::vector<int>& get_state_buf() override { return state_buf; }
    const std::vector<int>& get_state_orb() override { return state_orb; }
    const std::vector<std::list<long int>>& get_stopped_jobs() override { return stopped_jobs; }
    const std::vector<std::list<long int>>& get_ongoing_jobs() override { return ongoing_jobs; }
    int get_free_ser() override { return freeservers; }
    int get_window_size() override { return 0; }
    const std::vector<int> get_sequence_buffer() override { return {0, 0}; }
    int get_w() const override { return w; }
    int get_violations_counter() override { return violations_counter; }
    void insert_completion(int size, double completion, long int id) override {};
    void reset_completion(double simtime) override {};
    bool prio_big() override { return false; }
    int get_state_ser_small() override { return -1; }
    ~OrbitRetrial() override = default;
    std::unique_ptr<Policy> clone() const override {
        return std::make_unique<OrbitRetrial>(w, servers, state_buf.size(), sizes, r_max, sigma, retry_ind);
    }
    explicit operator std::string() const override {
        return "OrbitRetrial(orbit_size=" + std::to_string(r_max) + ", sigma=" + std::to_string(sigma) +  ", retry_ind=" + std::to_string(retry_ind) + 
            ", servers=" + std::to_string(servers) + ", classes=" + std::to_string(state_buf.size()) + ", sizes=(" + join(sizes.begin(), sizes.end()) + "))";
    }

private:
    std::list<std::tuple<int, int, long int>> buffer;
    std::list<std::tuple<int, int, long int>> orbit;
    std::vector<int> state_buf;
    std::vector<int> state_ser;
    std::vector<int> state_orb;
    std::vector<std::list<long int>> stopped_jobs; // vector of list of ids
    std::vector<std::list<long int>> ongoing_jobs; // vector of list of ids
    int freeservers;
    int servers;
    int freeorbits;
    const int w;
    const int r_max;
    const double sigma;
    const bool retry_ind;
    const std::vector<unsigned int> sizes;
    std::map<double, int> completion_time;
    int violations_counter;

    void flush_buffer() override;
};

#endif // ORBITRETRIAL_H
