//
// Created by Adityo Anggraito on 21/01/25.
//

#include <iostream>

#include <mjqm-policies/DualKill.h>

void DualKill::arrival(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    this->buffer.push_back(e);
    state_buf[std::get<0>(e)]++;
    waiting_jobs++;
    flush_buffer();
}
void DualKill::departure(int c, int size, long int id) {
    std::tuple<int,int,long int> e(c,size,id);
    service_jobs--;
    state_ser[std::get<0>(e)]--;
    freeservers+=std::get<1>(e);
    // remove departing jobs
    this->ongoing_jobs[std::get<0>(e)].remove(std::get<2>(e));
    restarted_jobs.erase(std::get<2>(e));

    flush_buffer();
}

void DualKill::put_jobs_normally(bool treat_as_restart) {
    auto it = buffer.begin();
    bool modified = true;
    //std::cout << freeservers << std::endl;
    while (freeservers > 0 && it != buffer.end() && modified == true) {
        if (freeservers >= std::get<1>(*it)) {
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

void DualKill::flush_buffer() {

    //ongoing_jobs[i].push_back(*it);
    //it = stopped_jobs[i].erase(it);
    int servers_occupied = servers - freeservers;
    if (service_jobs >=1 && servers_occupied <= kill_threshold  && servers_occupied <= (max_stopped_size-stopped_size) && kill_cycle < max_kill_cycle &&
        (!buffer.empty()) && std::get<1>(buffer.front()) > freeservers && no_killing == false &&
        ((kill_turn == 1 && (service_jobs == 1 && servers_occupied == servers)          && std::get<1>(buffer.front()) == sizes[0]) ||
         (kill_turn == 0 && (service_jobs == 1 && servers_occupied == servers) == false && std::get<1>(buffer.front()) == sizes[sizes.size()-1])) ) {
        /*if (kill_turn == 1) {
            std::cout << "service jobs: " << service_jobs << "; servers occupied: " << servers_occupied << std::endl;
        }
        if (service_jobs == 1 && servers_occupied == servers) {
            std::cerr << "killing big jobs?" << std::endl;
        }*/
        violations_counter++;
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
    }

    if (after_kill) {
        if (freeservers < servers) {
            std::cerr << "servers not empty -> " << freeservers << std::endl;
        } else{
            //std::cout << stopped_size << std::endl;
        }
        put_jobs_normally(false);
        //std::cout << freeservers << std::endl;
    }

    if (no_killing && restarted_jobs.empty() && stopped_size == 0) {
        no_killing = false;
    }

    bool empty_state = (service_jobs == 0 && waiting_jobs == 0);
    bool kill_wins = (service_jobs == 0 && (!buffer.empty()) && std::get<1>(buffer.front()) < stopped_size);
    if (reach_max_stopped_size || empty_state || kill_cycle == max_kill_cycle) {
        if (kill_turn == 1) {
            //std::cout << "reach max stopped size: " << reach_max_stopped_size << std::endl;
            //std::cout << "stopped size: " << stopped_size << std::endl;
            //std::cout << "kill cycle: " << kill_cycle << std::endl;
            //std::cout << "max kill cycle: " << max_kill_cycle << std::endl;
        }
        // not letting any jobs untill we have enough servers to accomodate stopped jobs
        if (max_stopped_size <= servers && freeservers < stopped_size) {
            //std::cerr << "why aint we kill em all? " << freeservers << std::endl;
            after_kill = false;
            return;
        } else {
            // put all stopped jobs back in action
            //std::cout <<  stopped_size <<std::endl;
            for (int i = 0; i < stopped_jobs.size(); i++) {
                for (auto it = stopped_jobs[i].begin(); it != stopped_jobs[i].end(); ) {
                    if (freeservers >= sizes[i] ) {
                        ongoing_jobs[i].push_back(*it);
                        restarted_jobs.insert(*it);
                        it = stopped_jobs[i].erase(it);

                        service_jobs++;
                        state_ser[i]++;
                        freeservers -= sizes[i];

                        stopped_size -= sizes[i];
                    } else {
                        it++;
                    }
                }
            }
            if (stopped_size == 0) {
                reach_max_stopped_size = false;
                kill_cycle = 0;
                kill_turn = (kill_turn-1)*(-1);
                //std::cout << "kill turn: " << kill_turn << std::endl;
            }
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
