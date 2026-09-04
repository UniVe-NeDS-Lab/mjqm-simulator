//
// Created by Adityo Anggraito on 21/01/25.
//

#include <iostream>

#include <mjqm-policies/Orbit.h>

void Orbit::arrival(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    this->buffer.push_back(e);
    state_buf[std::get<0>(e)]++;
    flush_buffer();
}
void Orbit::departure(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    state_ser[std::get<0>(e)]--;
    freeservers+=std::get<1>(e);
    flush_buffer();
}

void Orbit::flush_buffer() {

    ongoing_jobs.clear();
    ongoing_jobs.resize(state_buf.size());

   if (freeservers > 0 && (!orbit.empty() || !buffer.empty()) ) {
        auto it = orbit.begin();
        //std::cout << freeservers << std::endl;
        while (freeservers > 0 && it != orbit.end()) {
            if (freeservers >= std::get<1>(*it)) {
                freeservers -= std::get<1>(*it);
                freeorbits += 1;
                state_ser[std::get<0>(*it)]++;
                state_buf[std::get<0>(*it)]--;
                ongoing_jobs[std::get<0>(*it)].push_back(std::get<2>(*it));
                state_orb[std::get<0>(*it)]--;
                it = orbit.erase(it);
            } else {
                it++;
            }
        }

        it = buffer.begin();
        //std::cout << freeservers << std::endl;
        if (state_buf.size() == 2) {
            while (freeservers >= 0 && it != buffer.end()) {
                if (freeservers >= std::get<1>(*it)) {
                    freeservers -= std::get<1>(*it);
                    state_ser[std::get<0>(*it)]++;
                    state_buf[std::get<0>(*it)]--;
                    ongoing_jobs[std::get<0>(*it)].push_back(std::get<2>(*it));
                    it = buffer.erase(it);
                } else if (freeorbits > 0 && std::get<1>(*it) > 1) {
                    this->orbit.push_back(*it);
                    freeorbits -= 1;
                    state_orb[std::get<0>(*it)]++;
                    it = buffer.erase(it);
                } else {
                    break;
                }
            }
        } else {
            while (freeservers > 0 && it != buffer.end()) {
                if (freeservers >= std::get<1>(*it)) {
                    freeservers -= std::get<1>(*it);
                    state_ser[std::get<0>(*it)]++;
                    state_buf[std::get<0>(*it)]--;
                    ongoing_jobs[std::get<0>(*it)].push_back(std::get<2>(*it));
                    it = buffer.erase(it);
                } else if (freeorbits > 0) {
                    this->orbit.push_back(*it);
                    freeorbits -= 1;
                    state_orb[std::get<0>(*it)]++;
                    it = buffer.erase(it);
                } else {
                    break;
                }
            }
        }
    }
}
