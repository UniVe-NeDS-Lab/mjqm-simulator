//
// Created by Adityo Anggraito on 21/01/25.
//

#ifndef QUICKSWAP_H
#define QUICKSWAP_H

#include <map>

#include <mjqm-policies/policy.h>
#include <mjqm-utils/string.hpp>

class QuickSwap final : public Policy {
public:
    QuickSwap(const int w, const int servers, const int classes, const std::vector<unsigned int>& sizes, const int threshold) :
        state_buf(classes), state_ser(classes), stopped_jobs(classes), ongoing_jobs(classes), freeservers(servers),
        servers(servers), w(w), sizes(sizes), violations_counter(0), threshold(threshold), drops_below(false),
        big_priority(false) {}
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
    ~QuickSwap() override = default;
    std::unique_ptr<Policy> clone() const override {
        return std::make_unique<QuickSwap>(w, servers, state_buf.size(), sizes, threshold);
    }
    explicit operator std::string() const override {
        return "QuickSwap(servers=" + std::to_string(servers) + ", classes=" + std::to_string(state_buf.size()) +
            ", sizes=(" + join(sizes.begin(), sizes.end()) + "), threshold="+ std::to_string(threshold) +")";
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
    const int w;
    const std::vector<unsigned int> sizes;
    std::map<double, int> completion_time;
    int violations_counter;

    int threshold;
    bool drops_below;
    bool big_priority;

    void flush_buffer() override;
};

#endif // QUICKSWAP_H
