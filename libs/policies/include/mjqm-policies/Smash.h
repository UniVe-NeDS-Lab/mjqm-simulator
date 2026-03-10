//
// Created by Marco Ciotola on 21/01/25.
//

#ifndef SMASH_H
#define SMASH_H

#include <mjqm-policies/policy.h>

class Smash : public Policy {
public:
    Smash(const int w, const int servers, const int classes) :
        servers(servers), w(w), state_buf(classes), state_ser(classes), stopped_jobs(classes), ongoing_jobs(classes),
        freeservers(servers), violations_counter(0) {}
    void arrival(int c, int size, long int id) override;
    void departure(int c, int size, long int id) override;
    const std::vector<int>& get_state_ser() override { return state_ser; }
    const std::vector<int>& get_state_buf() override { return state_buf; }
    const std::vector<std::list<long int>>& get_stopped_jobs() override { return stopped_jobs; }
    const std::vector<std::list<long int>>& get_ongoing_jobs() override { return ongoing_jobs; }
    int get_free_ser() override { return freeservers; }
    int get_window_size() override { return 0; }
    int get_w() const override { return w; }
    int get_violations_counter() override { return violations_counter; }
    void insert_completion(int size, double completion, long int id) override {}
    bool fit_jobs(std::unordered_map<long int, double> holdTime, double simTime) override { return false; }
    double get_overest_max() override { return 1.0; }
    bool prio_big() override { return false; }
    int get_state_ser_small() override { return -1; }
    void reset_completion(double simtime) override {}
    ~Smash() override = default;
    std::unique_ptr<Policy> clone() const override { return std::make_unique<Smash>(w, servers, state_buf.size()); }
    explicit operator std::string() const override {
        return "Smash(window=" + std::to_string(w) + ", servers=" + std::to_string(servers) +
            ", classes=" + std::to_string(state_buf.size()) + ")";
    }

private:
    std::list<std::tuple<int, int, long int>> buffer;
    int servers;
    const int w;
    std::vector<int> state_buf;
    std::vector<int> state_ser;
    std::vector<std::list<long int>> stopped_jobs; // vector of list of ids
    std::vector<std::list<long int>> ongoing_jobs; // vector of list of ids
    int freeservers;
    int violations_counter;

    void flush_buffer() override;
};

#endif // SMASH_H
