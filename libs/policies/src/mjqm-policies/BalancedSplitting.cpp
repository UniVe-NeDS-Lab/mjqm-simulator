//
// Created by Adityo Anggraito on 21/01/25.
//

#include <iostream>

#include <mjqm-policies/BalancedSplitting.h>

void BalancedSplitting::arrival(int c, int size, long int id) {
    //std::cout << id << std::endl;
    std::tuple<int,int,long int> e(c,size,id);
    this->buffer.push_back(e);
    state_buf[std::get<0>(e)]++;
    flush_buffer();
}
void BalancedSplitting::departure(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    state_ser[std::get<0>(e)]--;
    if (in_rsv[id]) {
        freeservers_rsv[c] += std::get<1>(e);
    } else {
        freeservers+=std::get<1>(e);
    }
    in_rsv.erase(id);
    flush_buffer();
}

void BalancedSplitting::flush_buffer() {

    ongoing_jobs.clear();
    ongoing_jobs.resize(state_buf.size());

    //std::cout << freeservers << std::endl;
    int class_done = 0;
    std::vector<bool> class_done_list;
    for (int i = 0; i < state_buf.size(); i++) {
        if (state_buf[i] == 0 || freeservers_rsv[i] < sizes[i]) { 
            class_done++;
            class_done_list.push_back(true);
        } else {
            class_done_list.push_back(false);
        }
    }

    bool helpers_done = false;

    auto it = buffer.begin();
    while (it != buffer.end()) {
        if (class_done_list[std::get<0>(*it)] == false && freeservers_rsv[std::get<0>(*it)] >= std::get<1>(*it)) {
            freeservers_rsv[std::get<0>(*it)] -= std::get<1>(*it);
            state_ser[std::get<0>(*it)]++;
            state_buf[std::get<0>(*it)]--;
            ongoing_jobs[std::get<0>(*it)].push_back(std::get<2>(*it));
            in_rsv[std::get<2>(*it)] = true;
            it = buffer.erase(it);
        } else if (helpers_done == false && freeservers >= std::get<1>(*it)) {
            if (class_done_list[std::get<0>(*it)] == false) {
                class_done++;
                class_done_list[std::get<0>(*it)] = true;
            }
            freeservers -= std::get<1>(*it);
            state_ser[std::get<0>(*it)]++;
            state_buf[std::get<0>(*it)]--;
            ongoing_jobs[std::get<0>(*it)].push_back(std::get<2>(*it));
            in_rsv[std::get<2>(*it)] = false;
            it = buffer.erase(it);
        } else if (class_done_list[std::get<0>(*it)] == false) {
            class_done++;
            class_done_list[std::get<0>(*it)] = true;
            it++;
            if (helpers >= std::get<1>(*it)) { helpers_done = true; }
            if (class_done == sizes.size() && helpers_done) { break; }
        } else if (class_done == sizes.size() && helpers_done) {
            break;
        } else {
            it++;
            if (helpers >= std::get<1>(*it)) { helpers_done = true; }
        }
    }
        //it++;
        //state_buf[it->first] --;
    //std::cout << freeservers << std::endl;
}
