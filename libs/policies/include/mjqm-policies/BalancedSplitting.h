//
// Created by Marco Ciotola on 21/01/25.
//

#ifndef BALANCEDSPLITTING_H
#define BALANCEDSPLITTING_H

#include <map>

#include <mjqm-policies/policy.h>
#include <mjqm-utils/string.hpp>
#include <numeric>  // std::accumulate

class BalancedSplitting final : public Policy {
public:
    BalancedSplitting(const int w, const int servers, const int classes, const std::vector<unsigned int>& sizes,
                      const std::vector<int> servers_rsv, double psi, int helpers, int reserved) :
        state_buf(classes), state_ser(classes), stopped_jobs(classes), ongoing_jobs(classes), freeservers(helpers),
        servers(servers), w(w), sizes(sizes), violations_counter(0), servers_rsv(servers_rsv), freeservers_rsv(servers_rsv), psi(psi),
        helpers(helpers) {}
    void arrival(int c, int size, long int id) override;
    void departure(int c, int size, long int id) override;
    bool fit_jobs(std::unordered_map<long int, double> holdTime, double simTime) override { return false; };
    const std::vector<int>& get_state_ser() override { return state_ser; }
    const std::vector<int>& get_state_buf() override { return state_buf; }
    const std::vector<std::list<long int>>& get_stopped_jobs() override { return stopped_jobs; }
    const std::vector<std::list<long int>>& get_ongoing_jobs() override { return ongoing_jobs; }
    int get_free_ser() override { return freeservers + std::accumulate(freeservers_rsv.begin(), freeservers_rsv.end(), 0);; }
    int get_window_size() override { return 0; }
    int get_w() const override { return w; }
    int get_violations_counter() override { return violations_counter; }
    double get_overest_max() override { return 1.0; }
    void insert_completion(int size, double completion, long int id) override {};
    void reset_completion(double simtime) override {};
    bool prio_big() override { return false; }
    int get_state_ser_small() override { return -1; }
    ~BalancedSplitting() override = default;
    std::unique_ptr<Policy> clone() const override {
        return std::make_unique<BalancedSplitting>(w, servers, state_buf.size(), sizes, servers_rsv, psi, helpers, reserved);
    }
    explicit operator std::string() const override {
        return "BalancedSplitting(servers=" + std::to_string(servers) + ", classes=" + std::to_string(state_buf.size()) +
            ", sizes=(" + join(sizes.begin(), sizes.end()) + "), psi="+ std::to_string(psi) +", helpers="+ std::to_string(freeservers) +")";
    }

private:
    std::list<std::tuple<int, int, long int>> buffer;
    std::list<std::tuple<int, int, long int>> mset; // list of jobs in service
    std::vector<int> state_buf;
    std::vector<int> state_ser;
    std::vector<std::list<long int>> stopped_jobs; // vector of list of ids
    std::vector<std::list<long int>> ongoing_jobs; // vector of list of ids
    int freeservers;
    int servers;
    int helpers;
    int reserved;
    const int w;
    const std::vector<unsigned int> sizes;
    const std::vector<double> lambdas;
    const std::vector<double> srv_times;
    double psi;
    std::map<double, int> completion_time;
    std::unordered_map<long int, double> completion_time_real;
    std::unordered_map<long int, bool> in_rsv;
    int violations_counter;

    std::vector<int> freeservers_rsv;
    std::vector<int> servers_rsv;

    double schedule_next() const;
    void flush_buffer() override;
};

#endif // BALANCEDSPLITTING_H
