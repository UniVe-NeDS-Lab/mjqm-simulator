//
// Created by Adityo Anggraito on 21/01/25.
//

#include <iostream>

#include <mjqm-policies/AdaptiveMSF.h>

void AdaptiveMSF::arrival(int c, int size, long int id) {
    state_buf[c]++;
    stopped_jobs[c].push_back(id);
    flush_buffer();
}
void AdaptiveMSF::departure(int c, int size, long int id) {
    state_ser[c]--;
    freeservers+=size;
    flush_buffer();
}

void AdaptiveMSF::flush_buffer() {

    ongoing_jobs.clear();
    ongoing_jobs.resize(state_buf.size());

    bool modified = true;
    int biggest_job = -1;
    //bool zeros = std::all_of(state_buf, state_buf + state_buf.size(), [](bool elem){ return elem == 0; });
    while (modified && freeservers > 0) {
        modified = false;
        for (int i = state_buf.size() - 1; i >= 0; --i) {
            if (switching_time == true && biggest_job < 0 && state_buf[i] > 0) {
                biggest_job = i;
            }
            if (switching_time == false || (switching_time == true && i == biggest_job)) {
                auto it = stopped_jobs[i].begin();
                while (state_buf[i] != 0 && sizes[i] <= freeservers) {
                    // Track FIFO violations: count waiting jobs in smaller classes
                    for (int j = 0; j < i; ++j) {
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
            if (switching_time == true && modified == true){
                switching_time = false;
            }
        }
        //zeros = std::all_of(state_buf, state_buf + state_buf.size(), [](bool elem){ return elem == 0; });
    }

    if (switching_time == false && check_condition() == true) {
        switching_time = true;
    }
}

bool AdaptiveMSF::check_condition() {
    bool all_buf = false;
    for (int i = state_buf.size() - 1; i >= 0; --i) {
        if (state_ser[i] > 0) {
            if (state_buf[i] > 0) {
                return false;
            }
        } 
        if (all_buf == false && state_buf[i] > 0) {
            if (state_ser[i] == 0) {
                all_buf = true;
            }
        }
    }
    return all_buf;
}
