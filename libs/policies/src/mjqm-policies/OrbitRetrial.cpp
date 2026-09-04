//
// Created by Adityo Anggraito on 21/01/25.
//

#include <iostream>

#include <mjqm-policies/OrbitRetrial.h>

void OrbitRetrial::arrival(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    this->buffer.push_back(e);
    state_buf[std::get<0>(e)]++;
    flush_buffer();
}
void OrbitRetrial::departure(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    state_ser[std::get<0>(e)]--;
    freeservers+=std::get<1>(e);
    flush_buffer();
}

void OrbitRetrial::retry() {
    auto job = orbit.front();  // get first element
    std::tuple<int,int,long int> e(std::get<0>(job),std::get<1>(job),std::get<2>(job));
    this->buffer.push_front(e);
    orbit.pop_front();
    state_orb[std::get<0>(e)]--;
    freeorbits += 1;
    flush_buffer();
}

double OrbitRetrial::get_sigma() {
    if (freeorbits == r_max) {
        return 0.0;
    }

    if (retry_ind == 0){
        return sigma;
    } else{
        return (sigma*(r_max-freeorbits));
    }
}

void OrbitRetrial::flush_buffer() {

    ongoing_jobs.clear();
    ongoing_jobs.resize(state_buf.size());

   if (freeservers > 0 && (!buffer.empty()) ) {
        auto it = buffer.begin();
        //std::cout << freeservers << std::endl;
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
