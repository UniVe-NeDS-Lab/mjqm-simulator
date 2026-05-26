//
// Created by Adityo Anggraito on 21/01/25.
//

#include <iostream>

#include <mjqm-policies/StaticMSF.h>

void StaticMSF::arrival(int c, int size, long int id) {
    if (this->current_class == -1) {
        this->current_class = c;
        this->prev_class = c;
    }
    state_buf[c]++;
    stopped_jobs[c].push_back(id);
    if (check_condition() == true && c != current_class) {
        change_turn();
    }

    while(state_buf[current_class] == 0) {
        change_turn();
    }
    flush_buffer();
}
void StaticMSF::departure(int c, int size, long int id) {
    state_ser[c]--;
    freeservers+=size;
    flush_buffer();
}

void StaticMSF::flush_buffer() {

    ongoing_jobs.clear();
    ongoing_jobs.resize(state_buf.size());

    //if (this->prev_class != this->current_class && state_ser[this->prev_class] > 0) {
    //    return;
    //}

    bool modified = true;
    while (modified && freeservers > 0) {
        modified = false;
        int i = this->current_class;
        auto it = stopped_jobs[i].begin();
        while (state_buf[i] != 0 && sizes[i] <= freeservers) {
            // Track FIFO violations: count waiting jobs in other classes
            for (int j = 0; j < static_cast<int>(state_buf.size()); ++j) {
                if (j != i && state_buf[j] > 0) {
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

    if (check_condition() == true) {
        change_turn();
    }
}

bool StaticMSF::check_condition() {
    for (int i = state_buf.size() - 1; i >= 0; --i) {
        if (i != current_class && state_ser[i] > 0) {
            return false;
        }
    }
    if (state_ser[current_class] <= ((servers/sizes[current_class])-1)) {
        return true;
    }
    return false;
}

void StaticMSF::change_turn() {
    int cc = this->current_class;
    this->current_class -= 1;
    if (this->current_class < 0){
        this->current_class = sizes.size()-1;
    }
    // skip to the next classes if it's empty
    while(state_buf[current_class] == 0 && cc != this->current_class) {
        this->current_class -= 1;
        if (this->current_class < 0){
            this->current_class = sizes.size()-1;
        }
    }
    if (this->current_class != cc) {
        this->prev_class = cc;
    }
}