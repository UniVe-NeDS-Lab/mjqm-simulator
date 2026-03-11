//
// Created by Adityo Anggraito on 21/01/25.
//

#include <iostream>

#include <mjqm-policies/LCFS.h>

void LCFS::arrival(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    this->buffer.push_back(e);
    state_buf[std::get<0>(e)]++;
    flush_buffer();
}
void LCFS::departure(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    state_ser[std::get<0>(e)]--;
    freeservers+=std::get<1>(e);
    flush_buffer();
}

void LCFS::flush_buffer() {

    ongoing_jobs.clear();
    ongoing_jobs.resize(state_buf.size());

    if (freeservers > 0 && !buffer.empty()) {
        auto it = std::prev(buffer.end());
        //std::cout << freeservers << std::endl;
        while (freeservers > 0 && !buffer.empty()) {
            if (freeservers >= std::get<1>(*it)) {
                freeservers -= std::get<1>(*it);
                state_ser[std::get<0>(*it)]++;
                state_buf[std::get<0>(*it)]--;
                ongoing_jobs[std::get<0>(*it)].push_back(std::get<2>(*it));
                auto next_it = buffer.erase(it);
                if (buffer.empty() || next_it == buffer.begin()) break;
                it = std::prev(next_it); // continue backward safely
            } else {
                break;
            }
            //it++;
            //state_buf[it->first] --;
        }
        //std::cout << freeservers << std::endl;
    }
}
