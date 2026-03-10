//
// Created by Adityo Anggraito on 21/01/25.
//

#include <iostream>

#include <mjqm-policies/KillSmart.h>

void KillSmart::arrival(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    this->buffer.push_back(e);
    state_buf[std::get<0>(e)]++;
    waiting_jobs++;
    flush_buffer();
}
void KillSmart::departure(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    service_jobs--;
    state_ser[std::get<0>(e)]--;
    freeservers+=std::get<1>(e);
    // remove departing jobs
    this->ongoing_jobs[std::get<0>(e)].remove(std::get<2>(e));
    restarted_jobs.erase(std::get<2>(e));

    flush_buffer();
}

void KillSmart::put_jobs_normally(bool treat_as_restart) {
    auto it = buffer.begin();
    bool modified = true;
    //std::cout << freeservers << std::endl;
    while (freeservers > 0 && it != buffer.end() && modified == true) {
        if (freeservers >= std::get<1>(*it)) {
            if (std::get<1>(*it) == sizes[1] && sizes.size()==2) {
                big_phase += 1;
            }
            freeservers -= std::get<1>(*it);
            state_ser[std::get<0>(*it)]++;
            state_buf[std::get<0>(*it)]--;
            ongoing_jobs[std::get<0>(*it)].push_back(std::get<2>(*it));
            if (treat_as_restart) {
                restarted_jobs.insert(std::get<2>(*it));
            }
            service_jobs++;
            waiting_jobs--;
            it = buffer.erase(it);
            modified = true;
        } else {
            modified = false;
            it++;
        }
        //it++;
        //state_buf[it->first] --;
    }
}

void KillSmart::flush_buffer() {

    bool just_in = false;
    bool big_phase_cond = (big_phase < (max_kill_cycle+1) && sizes.size()==2) || (sizes.size() > 2);
    if (freeservers == servers and (!buffer.empty()) && std::get<1>(buffer.front()) == 1 && 
        reach_max_stopped_size == false && kill_cycle < max_kill_cycle && big_phase_cond) {
        put_jobs_normally(false);
        //std::cout << "SMALL EARLY " << servers-freeservers << std::endl;
        just_in = true;
    }
    //ongoing_jobs[i].push_back(*it);
    //it = stopped_jobs[i].erase(it);
    int servers_occupied = servers - freeservers;
    if (service_jobs >=1 && servers_occupied <= kill_threshold  && servers_occupied <= (max_stopped_size-stopped_size) && kill_cycle < max_kill_cycle &&
        (!buffer.empty()) && std::get<1>(buffer.front()) > freeservers && std::get<1>(buffer.front()) > servers_occupied && no_killing == false &&
        big_phase_cond) {
        // put all ongoing jobs into stopped
        //std::cout << "KILLING TIME" << std::endl;
        //std::cout << "BEFORE KILL " << servers-freeservers << std::endl;
        if (service_jobs == 1 && servers_occupied == servers) {
            std::cerr << "killing big jobs?" << std::endl;
        }
        if (just_in) {
            violations_counter++;
        }
        for (int i = 0; i < ongoing_jobs.size(); i++) {
            for (auto it = ongoing_jobs[i].begin(); it != ongoing_jobs[i].end(); ) {
                // kill jobs if killing it won't make us overflow
                if ((stopped_size + sizes[i]) <= max_stopped_size) {
                    //std::cout << "KILLED" << std::endl;
                    //std::cout << ongoing_jobs[i].size() << std::endl;
                    stopped_jobs[i].push_back(*it);
                    it = ongoing_jobs[i].erase(it);

                    service_jobs--;
                    state_ser[i]--;
                    freeservers += sizes[i];

                    stopped_size += sizes[i];
                } else {
                    std::cerr << "something should be killed here" << std::endl;
                    reach_max_stopped_size = true;
                    after_kill = true;
                    break;
                }
            }
        }
        if (stopped_size == max_stopped_size) {
            reach_max_stopped_size = true;
        } else if (stopped_size > max_stopped_size) {
            std::cerr << "killed bin overflows" << std::endl;
        }
        after_kill = true;
        kill_cycle += 1;
        //std::cout << "AFTER KILL " << servers-freeservers << std::endl;
    }

    if (after_kill) {
        if (freeservers < servers) {
            std::cerr << "servers not empty -> " << freeservers << std::endl;
        } else{
            //std::cout << stopped_size << std::endl;
        }
        put_jobs_normally(false);
        //std::cout << freeservers << std::endl;
        //std::cout << "BIG IN " << servers-freeservers << std::endl;
        //std::cout << "-------" << std::endl;
    }

    if (no_killing && restarted_jobs.empty()) {
        no_killing = false;
    }

    bool empty_state = (service_jobs == 0 && waiting_jobs == 0);
    bool kill_wins = (service_jobs == 0 && (!buffer.empty()) && std::get<1>(buffer.front()) < stopped_size);
    if (reach_max_stopped_size || (empty_state && stopped_size > 0) || kill_cycle == max_kill_cycle || (big_phase == (max_kill_cycle+1)&& sizes.size()==2)) {
        // not letting any jobs untill we have enough servers to accomodate stopped jobs
        //std::cout << kill_cycle << " " << stopped_size << std::endl;
        if (freeservers < stopped_size) {
            //std::cerr << "why aint we kill em all? " << freeservers << std::endl;
            after_kill = false;
            return;
        } else {
            // put all stopped jobs back in action
            //std::cout << "START " << stopped_size << "BOOL"<< empty_state << std::endl;
            for (int i = 0; i < stopped_jobs.size(); i++) {
                for (auto it = stopped_jobs[i].begin(); it != stopped_jobs[i].end(); ) {
                    ongoing_jobs[i].push_back(*it);
                    restarted_jobs.insert(*it);
                    it = stopped_jobs[i].erase(it);

                    service_jobs++;
                    state_ser[i]++;
                    freeservers -= sizes[i];

                    stopped_size -= sizes[i];
                }
            }
            if (stopped_size > 0) {
                std::cout << "AFTER " << stopped_size <<std::endl;
            }
            
            reach_max_stopped_size = false;
            kill_cycle = 0;
            big_phase = 0;
            no_killing = true;
            if (freeservers > 0) {
                put_jobs_normally(true);
            }
            if (waiting_jobs > 0 && std::get<1>(buffer.front()) == 1) {
                //std::cerr << "some small jobs left behind " << waiting_jobs << std::endl;
            }
        }
    } else {
        put_jobs_normally(false);
    }
    
    after_kill = false;
}
