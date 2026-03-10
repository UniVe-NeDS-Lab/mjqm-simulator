//
// Created by Adityo Anggraito on 21/01/25.
//

#ifndef KILLSMART_H
#define KILLSMART_H

#include <map>
#include <unordered_set>

#include <mjqm-policies/policy.h>
#include <mjqm-utils/string.hpp>

class KillSmart final : public Policy {
public:
    KillSmart(const int w, const int servers, const int classes, const std::vector<unsigned int>& sizes, const int k, const int kill_threshold) :
        state_buf(classes), state_ser(classes), stopped_jobs(classes), ongoing_jobs(classes), freeservers(servers),
        servers(servers), w(w), sizes(sizes), violations_counter(0), service_jobs(0), waiting_jobs(0),
        stopped_size(0), max_stopped_size((k)*kill_threshold), after_kill(false), reach_max_stopped_size(false), kill_threshold(kill_threshold),
        max_kill_cycle(k-1), kill_cycle(0), no_killing(false), original_k(k), big_phase(0) {}
    void arrival(int c, int size, long int id) override;
    void departure(int c, int size, long int id) override;
    bool fit_jobs(std::unordered_map<long int, double> holdTime, double simTime) override { return false; };
    double get_overest_max() override { return 1.0; }
    const std::vector<int>& get_state_ser() override { return state_ser; }
    const std::vector<int>& get_state_buf() override { return state_buf; }
    const std::vector<std::list<long int>>& get_stopped_jobs() override { return stopped_jobs; }
    const std::vector<std::list<long int>>& get_ongoing_jobs() override { return ongoing_jobs; }
    int get_free_ser() override { return freeservers; }
    int get_window_size() override { return 0; }
    int get_w() const override { return w; }
    int get_violations_counter() override { return violations_counter; }
    void insert_completion(int size, double completion, long int id) override {};
    void reset_completion(double simtime) override {};
    bool prio_big() override { return false; }
    int get_state_ser_small() override { return -1; }
    ~KillSmart() override = default;
    std::unique_ptr<Policy> clone() const override {
        return std::make_unique<KillSmart>(w, servers, state_buf.size(), sizes, original_k, kill_threshold);
    }
    explicit operator std::string() const override {
        return "KillSmart(servers=" + std::to_string(servers) + ", classes=" + std::to_string(state_buf.size()) +
            ", sizes=(" + join(sizes.begin(), sizes.end()) + "), k="+ std::to_string(max_kill_cycle) +", v="+ std::to_string(kill_threshold) +")";
    }

private:
    std::list<std::tuple<int, int, long int>> buffer;
    std::unordered_set<long> restarted_jobs;
    std::list<std::tuple<int, int, long int>> mset; // list of jobs in service
    std::vector<int> state_buf;
    std::vector<int> state_ser;
    std::vector<std::list<long int>> stopped_jobs; // vector of list of ids
    std::vector<std::list<long int>> ongoing_jobs; // vector of list of ids
    int freeservers;
    int servers;
    const int w;
    const std::vector<unsigned int> sizes;
    std::map<double, int> completion_time;
    int violations_counter;

    int service_jobs;
    int waiting_jobs;
    bool after_kill;
    int stopped_size;
    int max_stopped_size;
    bool reach_max_stopped_size;
    int kill_threshold;
    int max_kill_cycle;
    int kill_cycle;
    bool no_killing;
    int original_k;
    int big_phase;

    void put_jobs_normally(bool treat_as_restart); 
    void flush_buffer() override;
};

#endif // KILLSMART_H
