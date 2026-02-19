//
// Created by Marco Ciotola on 21/01/25.
//

#include <mjqm-policies/MostServerFirst.h>

void MostServerFirst::arrival(int c, int size, long int id) {
    state_buf[c]++;
    stopped_jobs[c].push_back(id);
    flush_buffer();
}
void MostServerFirst::departure(int c, int size, long int id) {
    state_ser[c]--;
    freeservers += size;
    flush_buffer();
}
int MostServerFirst::get_state_ser_small() {
    int tot_small_ser = 0;
    for (int i = 0; i < servers - 1; i++) {
        tot_small_ser += state_ser[i];
    }
    return tot_small_ser;
}
void MostServerFirst::flush_buffer() {

    ongoing_jobs.clear();
    ongoing_jobs.resize(state_buf.size());

    bool modified = true;
    // bool zeros = std::all_of(state_buf, state_buf + state_buf.size(), [](bool elem){ return elem == 0; });
    while (modified && freeservers > 0) {
        modified = false;
        for (long i = state_buf.size() - 1; i >= 0; --i) {
            auto it = stopped_jobs[i].begin();
            while (state_buf[i] != 0 && sizes[i] <= freeservers) {
                // Track FIFO violations: count waiting jobs in smaller classes
                for (long j = 0; j < i; ++j) {
                    if (state_buf[j] > 0) {
                        violations_counter += state_buf[j];
                    }
                }
                state_buf[i]--;
                state_ser[i]++;
                ongoing_jobs[i].push_back(*it);
                it = stopped_jobs[i].erase(it);
                freeservers -= sizes[i];
                modified = true;
            }
        }
        // zeros = std::all_of(state_buf, state_buf + state_buf.size(), [](bool elem){ return elem == 0; });
    }
}
