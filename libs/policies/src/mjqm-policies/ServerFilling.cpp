//
// Created by Marco Ciotola on 21/01/25.
//

#include <tuple>

#include <mjqm-policies/ServerFilling.h>

void ServerFilling::arrival(int c, int size, long int id) {
    std::tuple<int, int, long int> e(c, size, id);
    this->buffer.push_back(e);
    state_buf[std::get<0>(e)]++;
    flush_buffer();
}
void ServerFilling::departure(int c, int size, long int id) {
    std::tuple<int, int, long int> e(c, size, id);
    state_ser[std::get<0>(e)]--;
    freeservers += std::get<1>(e);
    this->mset_coreNeed -= std::get<1>(e);
    auto it = mset.begin();
    while (it != mset.end()) {
        if (std::get<2>(e) == std::get<2>(*it)) {
            it = this->mset.erase(it);
        } else {
            ++it;
        }
    }
    // remove departing jobs
    this->ongoing_jobs[std::get<0>(e)].remove(std::get<2>(e));
    flush_buffer();
}
void ServerFilling::addToMset(const std::tuple<int, int, long int>& e) {
    auto it = mset.begin();
    int positions_skipped = 0;
    while (it != mset.end() && std::get<1>(e) <= std::get<1>(*it)) {
        ++it;
        ++positions_skipped;
    }
    // Track FIFO violations: this job is being placed ahead of positions_skipped jobs
    if (positions_skipped > 0) {
        violations_counter += positions_skipped;
    }
    mset.insert(it, e);
}
void ServerFilling::flush_buffer() {

    if (freeservers > 0) {
        auto it = buffer.begin();

        for (size_t i = 0; i < state_buf.size(); i++) {
            state_buf[i] += state_ser[i];
        }

        while (mset_coreNeed < servers && it != buffer.end()) {
            this->addToMset(*it);
            mset_coreNeed += std::get<1>(*it);
            it = buffer.erase(it);
        }

        freeservers = servers;
        state_ser.assign(state_buf.size(), 0);
        stopped_jobs.clear();
        ongoing_jobs.clear();
        stopped_jobs.resize(state_buf.size());
        ongoing_jobs.resize(state_buf.size());

        for (auto& elem : mset) {
            if (std::get<1>(elem) <= freeservers) {
                state_ser[std::get<0>(elem)]++;
                state_buf[std::get<0>(elem)]--;
                freeservers -= std::get<1>(elem);
                ongoing_jobs[std::get<0>(elem)].push_back(std::get<2>(elem));
            } else {
                stopped_jobs[std::get<0>(elem)].push_back(std::get<2>(elem));
            }
        }
    }
}
