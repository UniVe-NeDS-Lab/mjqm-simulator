//
// Created by Adityo Anggraito on 21/01/25.
//

#include <iostream>

#include <mjqm-policies/QuickSwap.h>

void QuickSwap::arrival(int c, int size, long int id) {
    state_buf[c]++;
    stopped_jobs[c].push_back(id);
    if (drops_below && big_priority == false && c == state_buf.size()-1 && state_ser[c] == 0 && state_ser[0] > 0) {
        big_priority = true;
    }
    flush_buffer();
}
void QuickSwap::departure(int c, int size, long int id) {
    state_ser[c]--;
    freeservers+=sizes[c];
    if (big_priority && c < state_buf.size()-1 && freeservers >= sizes[sizes.size()-1]) {
        big_priority = false;
        drops_below = false;
    }
    flush_buffer();
    if (big_priority == false && drops_below == false && c < state_buf.size()-1 && freeservers >= threshold && state_ser[state_ser.size()-1] == 0) {
        drops_below = true;
        if (state_buf[state_buf.size()-1] > 0) {
            big_priority = true;
            if (freeservers >= sizes[sizes.size()-1]) {
                std::cout << "masuk lwt bawah" << std::endl;
                big_priority = false;
                drops_below = false;
                flush_buffer();
            }
            
        }
    } 
}

void QuickSwap::flush_buffer() {

    ongoing_jobs.clear();
    ongoing_jobs.resize(state_buf.size());

    bool modified = true;
    //bool zeros = std::all_of(state_buf, state_buf + state_buf.size(), [](bool elem){ return elem == 0; });
    while (big_priority == false && modified && freeservers > 0) {
        modified = false;
        for (int i = state_buf.size() - 1; i >= 0; --i) {
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
        //zeros = std::all_of(state_buf, state_buf + state_buf.size(), [](bool elem){ return elem == 0; });
    }
}
