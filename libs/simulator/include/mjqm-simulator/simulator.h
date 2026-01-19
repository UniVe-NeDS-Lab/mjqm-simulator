//
// Created by Marco Ciotola on 03/02/25.
//

#ifndef SIMULATOR_H
#define SIMULATOR_H

#include <algorithm>
#include <chrono>
#include <ctime>
#include <iostream>
#include <limits>
#include <list>
#include <numeric>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>
#include <random>

#include <mjqm-math/confidence_intervals.h>
#include <mjqm-math/mean_var.h>
#include <mjqm-policies/policy.h>
#include <mjqm-samplers/sampler.h>
#include <mjqm-simulator/experiment_stats.h>

#if __has_include("toml++/toml.h")
#include <mjqm-settings/toml_loader.h>
#endif

class Simulator {
public:
    Simulator(const std::vector<double>& l, const std::vector<double>& u, const std::vector<unsigned int>& sizes, int w,
              int servers, int sampling_method, std::string logfile_name, ExperimentStats& stats);

#if __has_include("toml++/toml.h")
    explicit Simulator(ExperimentConfig& conf);
#endif

    ~Simulator() = default;

    void reset_simulation() {
        simtime = 0.0;
        resample();
    }

    void reset_statistics() {
        for (auto& e : occupancy_ser)
            e = 0;
        for (auto& e : occupancy_buf)
            e = 0;
        for (auto& e : rawWaitingTime)
            e.clear();
        for (auto& e : rawResponseTime)
            e.clear();
        for (auto& e : completion)
            e = 0;
        for (auto& e : curr_job_seq)
            e = 0;
        for (auto& e : tot_job_seq)
            e = 0;
        for (auto& e : curr_job_seq_start)
            e -= simtime;
        for (auto& e : tot_job_seq_dur)
            e = 0;
        for (auto& e : job_seq_amount)
            e = 0;
        for (auto& e : preemption)
            e = 0;
        for (auto& e : rep_free_servers_distro)
            e = 0;
        for (auto& e : fel)
            e -= simtime;

        for (size_t i = 0; i < jobs_inservice.size(); ++i) {
            for (auto job = jobs_inservice[i].begin(); job != jobs_inservice[i].end(); ++job) {
                jobs_inservice[i][job->first] -= simtime;
            }
        }

        for (auto job_id = arrTime.begin(); job_id != arrTime.end(); ++job_id) {
            arrTime[job_id->first] -= simtime;
        }

        for (auto job_id = startSer.begin(); job_id != startSer.end(); ++job_id) {
            startSer[job_id->first] -= simtime;
        }

        phase_two_start -= simtime;
        phase_three_start -= simtime;

        policy->reset_completion(simtime);

        simtime = 0.0;
        waste = 0.0;
        viol = 0.0;
        occ = 0.0;
        windowSize.clear();
        phase_two_duration = 0;
        phase_three_duration = 0;
        idle_period = 0;
        viol_ctr = policy->get_violations_counter();
    }

    void collect_run_statistics() {
        double totq = 0.0;
        for (auto& x : occupancy_buf) {
            x /= simtime;
            totq += x;
        }

        for (auto& x : occupancy_ser) {
            x /= simtime;
        }

        double utilisation = 0.0;
        std::list<double> totRawWaitingTime;
        std::list<double> totRawResponseTime;
        for (int i = 0; i < nclasses; i++) {
            ClassStats& class_stats = stats->for_class(i);

            class_stats.occupancy_buf.collect(occupancy_buf[i]);
            class_stats.occupancy_ser.collect(occupancy_ser[i]);
            class_stats.occupancy_system.collect(occupancy_buf[i] + occupancy_ser[i]);
            class_stats.throughput.collect((double)completion[i] / simtime);
            utilisation += occupancy_ser[i] * sizes[i];

            // waitingTime[i] = occupancy_buf[i] / throughput[i];
            auto wt_mean_var = mean_var(rawWaitingTime[i]);
            class_stats.wait_time.collect(wt_mean_var.first);
            class_stats.wait_time_var.collect(wt_mean_var.second);

            // responseTime[i] = (occupancy_buf[i]+occupancy_ser[i]) / throughput[i];
            auto rt_mean_var = mean_var(rawResponseTime[i]);
            class_stats.resp_time.collect(rt_mean_var.first);
            class_stats.resp_time_var.collect(rt_mean_var.second);

            totRawWaitingTime.insert(totRawWaitingTime.end(), rawWaitingTime[i].begin(), rawWaitingTime[i].end());
            totRawResponseTime.insert(totRawResponseTime.end(), rawResponseTime[i].begin(), rawResponseTime[i].end());

            class_stats.preemption_avg.collect((double)preemption[i] / (double)completion[i]);

            class_stats.seq_avg_len.collect((tot_job_seq[i] * 1.0) / job_seq_amount[i]);
            class_stats.seq_avg_dur.collect((tot_job_seq_dur[i] * 1.0) / job_seq_amount[i]);
            class_stats.seq_amount.collect(job_seq_amount[i]);
        }

        stats->window_size.collect(std::accumulate(windowSize.begin(), windowSize.end(), 0.0) / simtime);

        stats->wasted.collect(waste / simtime);
        stats->violations.collect(policy->get_violations_counter()-viol_ctr);
        stats->utilisation.collect(utilisation / n);
        stats->occupancy_tot.collect(totq);

        auto wt_mean_var = mean_var(totRawWaitingTime);
        stats->wait_tot.collect(wt_mean_var.first);
        stats->wait_var_tot.collect(wt_mean_var.second);

        auto rt_mean_var = mean_var(totRawResponseTime);
        stats->resp_tot.collect(rt_mean_var.first);
        stats->resp_var_tot.collect(rt_mean_var.second);

        stats->phase_two_dur.collect((phase_two_duration * 1.0) / simtime);
        stats->phase_three_dur.collect((phase_three_duration * 1.0) / job_seq_amount[1]);
        stats->idle_period_prob.collect((idle_period * 1.0) / simtime);
    }

    void simulate(unsigned long nevents, unsigned int repetitions = 1) {
        stats->edit_computed_stats([](Stat& s) { s.clear(); });
        double tot_lambda = 0.0;
        for (int i = 0; i < nclasses; ++i) {
            ClassStats& res = stats->class_stats.at(i);
            double lambda = 1. / this->arr_time_samplers[i]->get_mean();
            lambda = l[i];
            res.lambda = lambda;
            tot_lambda += lambda;
        }
        stats->lambda = tot_lambda;

        std::random_device rd;                  // Seed (non-deterministic if available)
        std::mt19937 gen(rd());                 // Mersenne Twister generator
        auto dist = std::uniform_real_distribution<double>(0.0, policy->get_overest_max());

        for (unsigned int rep = 0; rep < repetitions; rep++) {
            /*int buf_size = std::reduce(policy->get_state_buf().begin(), policy->get_state_buf().end());
            if (buf_size > 180000000) {
                break;
            }*/

            auto start = std::chrono::high_resolution_clock::now();
            reset_statistics();

            for (unsigned long k = 0; k < nevents; k++) {
                auto itmin = std::min_element(fel.begin(), fel.end());
                // std::cout << *itmin << std::endl;
                int pos = std::distance(fel.begin(), itmin);
                // std::cout << pos << std::endl;
                collect_statistics(pos);
                // std::cout << "collect" << std::endl;
                if (pos < nclasses) { // departure
                    // Remove jobs from in_service (they cannot be in preempted list)
                    jobs_inservice[pos].erase(job_fel[pos]);
                    rawWaitingTime[pos].push_back(waitTime[job_fel[pos]]);
                    rawResponseTime[pos].push_back(waitTime[job_fel[pos]] + holdTime[job_fel[pos]]);
                    arrTime.erase(job_fel[pos]);
                    startSer.erase(job_fel[pos]);
                    waitTime.erase(job_fel[pos]);
                    holdTime.erase(job_fel[pos]);
                    holdTimeDeclared.erase(job_fel[pos]);
                    // std::cout << "before dep" << std::endl;

                    //if (pos == 1) {
                    //    std::cout << "BIG JOB OUT " << *itmin << std::endl;
                    //}
                    policy->departure(pos, sizes[pos], job_fel[pos]);
                    last_ev_arr = false;
                    // std::cout << "dep" << std::endl;
                } else {
                    auto job_id = k + (nevents * rep);
                    if (this->w == -3) {
                        holdTime[job_id] = ser_time_samplers[pos - nclasses]->sample();
                        // std::cout << holdTime[job_id] << std::endl;
                    } else if (this->w == -13) {
                        double hold = ser_time_samplers[pos - nclasses]->sample();
                        //std::cout << hold << std::endl;
                        holdTime[job_id] = hold;
                        double overest = (ser_time_samplers[pos - nclasses]->sample())*policy->get_overest_max();
                        //double overest = hold*policy->get_overest_max();
                        //std::cout << overest << std::endl;
                        holdTimeDeclared[job_id] = hold + overest;
                        //std::cout << holdTimeDeclared[job_id] << std::endl;
                        //std::cout << "-------------------" << std::endl;
                        //std::cout << holdTime[job_id] << " " << holdTimeDeclared[job_id] << std::endl;
                    }
                    policy->arrival(pos - nclasses, sizes[pos - nclasses], job_id);
                    arrTime[job_id] = *itmin;
                    last_arr = pos-nclasses;
                    last_ev_arr = true;
                    // std::cout << "arr" << std::endl;
                }

                simtime = *itmin;

                resample();
                // std::cout << "resample" << std::endl;
                if (this->w == -3) {
                    bool added;
                    added = policy->fit_jobs(holdTime, simtime);
                    resample();
                    int idx = 0;
                    while (added) {
                        added = policy->fit_jobs(holdTime, simtime);
                        resample();
                        idx += 1;
                    }
                } else if (this->w == -13) {
                    bool added;
                    added = policy->fit_jobs(holdTimeDeclared, simtime);
                    resample();
                    int idx = 0;
                    while (added) {
                        added = policy->fit_jobs(holdTimeDeclared, simtime);
                        resample();
                        idx += 1;
                    }
                }
            }

            collect_run_statistics();

            auto end = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration_cast<std::chrono::seconds>(end - start).count();
            stats->timings_tot.collect(duration);

            std::cout << "Repetition " << std::to_string(rep) << " Done" << std::endl;
        }

        // outputFile.close();
        for (auto& x : rep_free_servers_distro) {
            x /= simtime;
        }
    }

    void produce_statistics(ExperimentStats& stats, const double confidence = 0.05) const {
        stats.edit_all_stats([](Stat& s) { s.finalise(); });
        bool any_warning = false;
        for (int i = 0; i < nclasses; ++i) {
            ClassStats& res = stats.class_stats.at(i);
            bool warning = 1.0 - std::get<Confidence_inter>(res.throughput.value).mean / l[i] > 0.05;
            res.warnings = warning;
            any_warning = any_warning || warning;
        }
        stats.warnings = any_warning;
    }

private:
    ExperimentStats* stats;
    const int nclasses;
    std::vector<double> l;
    std::vector<double> u;
    std::vector<std::unique_ptr<DistributionSampler>> ser_time_samplers;
    std::vector<std::unique_ptr<DistributionSampler>> arr_time_samplers;
    std::vector<unsigned int> sizes;
    std::vector<std::string> class_names;
    int n;
    int w = 1;
    bool debugMode;

    std::unique_ptr<Policy> policy;

    double simtime = 0.0;

    // overall statistics
    std::vector<double> rep_free_servers_distro;

    // statistics for single run
    std::vector<double> occupancy_buf;
    std::vector<double> occupancy_ser;
    std::vector<unsigned long> completion;
    std::vector<unsigned long> preemption;

    std::unordered_map<long int, double> arrTime;
    std::unordered_map<long int, double> startSer;
    std::unordered_map<long int, double> waitTime;
    std::unordered_map<long int, double> holdTime;
    std::unordered_map<long int, double> holdTimeDeclared;
    std::vector<std::list<double>> rawWaitingTime;
    std::vector<std::list<double>> rawResponseTime;

    std::list<double> windowSize;
    double idle_period;

    int viol_ctr;

    int last_arr = 0;
    bool last_ev_arr;

    double waste = 0.0;
    double viol = 0.0;
    double occ = 0.0;

    std::vector<double> curr_job_seq;
    std::vector<double> curr_job_seq_start;
    std::vector<double> tot_job_seq;
    std::vector<double> tot_job_seq_dur;
    std::vector<double> job_seq_amount;
    int last_job = -1;
    double phase_two_duration = 0;
    double phase_three_duration = 0;
    double phase_two_start = 0;
    double phase_three_start = 0;
    int curr_phase = 1;
    bool add_phase_two = false;

    std::vector<double> fel;
    std::vector<long int> job_fel;
    // std::vector<std::list<double>> fels;
    // std::list<int> job_ids;
    std::vector<std::unordered_map<long int, double>> jobs_inservice; //[id, time_end]
    std::vector<std::unordered_map<long int, double>> jobs_preempted; //[id, time_left]

    std::string logfile_name;

    void resample() {
        // add arrivals and departures
        if (this->w == -2 || this->w == -16 || this->w == -17) { // special blocks for serverFilling (memoryful)
            auto stopped_jobs = policy->get_stopped_jobs();
            auto ongoing_jobs = policy->get_ongoing_jobs();
            for (int i = 0; i < nclasses; i++) {
                if (last_ev_arr) {
                    fel[i + nclasses] = arr_time_samplers[(last_arr*nclasses)+i]->sample() + simtime;
                }
                
                /*if (fel[i + nclasses] <= simtime) { // only update arrival that is executed at the time
                    fel[i + nclasses] = arr_time_samplers[i]->sample() + simtime;
                }*/

                for (auto job_id : stopped_jobs[i]) {
                    if (jobs_inservice[i].contains(job_id)) { // If they are currently being served: stop them
                        if (this->w == -2) {
                            jobs_preempted[i][job_id] = jobs_inservice[i][job_id] - simtime; // Save the remaining service time
                        } else if (this->w == -16 || this->w == -17) {
                            jobs_preempted[i][job_id] = holdTime[job_id]; // Save the original whole service time
                        }
                        jobs_inservice[i].erase(job_id);
                        arrTime[job_id] = simtime;
                        preemption[i]++;
                        phase_two_duration += ((simtime - startSer[job_id])*sizes[i]);
                        job_seq_amount[0] += 1;
                    } else { // they were never even started
                        if ((this->w == -16 || this->w == -17) && waitTime.find(job_id) == waitTime.end() ) {
                            double sampled = ser_time_samplers[i]->sample();
                            waitTime[job_id] = simtime - arrTime[job_id];
                            holdTime[job_id] = sampled;
                            startSer[job_id] = simtime;

                            jobs_preempted[i][job_id] = holdTime[job_id];
                            arrTime[job_id] = simtime;
                            preemption[i]++;
                            phase_two_duration += ((simtime - startSer[job_id])*sizes[i]);
                            job_seq_amount[0] += 1;
                        }
                    }
                }

                long int fastest_job_id;
                double fastest_job_fel = std::numeric_limits<double>::max();
                for (auto job_id : ongoing_jobs[i]) {
                    if (!jobs_inservice[i].contains(job_id)) { // If they are NOT already in service
                        if (jobs_preempted[i].contains(job_id)) { // See if they were preempted: resume them
                            jobs_inservice[i][job_id] = jobs_preempted[i][job_id] + simtime;
                            jobs_preempted[i].erase(job_id);
                            waitTime[job_id] = simtime - arrTime[job_id] + waitTime[job_id];
                            phase_three_duration += (simtime - startSer[job_id]);
                            job_seq_amount[1] += 1;
                        } else { // or they are just new jobs about to be served for the first time: add them with new
                                 // service time
                            double sampled = ser_time_samplers[i]->sample();
                            //if (i == 1) {
                               // std::cout << "BIG JOB IN " << simtime << std::endl;
                                //std::cout << "---------------"<< std::endl;
                            //}
                            jobs_inservice[i][job_id] = sampled + simtime;
                            // rawWaitingTime[i].push_back(simtime-arrTime[job_id]);
                            // arrTime.erase(*job_id); //update waitingTime
                            waitTime[job_id] = simtime - arrTime[job_id];
                            holdTime[job_id] = sampled;
                            startSer[job_id] = simtime;
                        }

                        if (jobs_inservice[i][job_id] < fastest_job_fel) {
                            fastest_job_id = job_id;
                            fastest_job_fel = jobs_inservice[i][job_id];
                        }
                    } else { // They are already in service
                        if (jobs_inservice[i][job_id] < fastest_job_fel) {
                            fastest_job_id = job_id;
                            fastest_job_fel = jobs_inservice[i][job_id];
                        }
                    }
                }

                if (jobs_inservice[i].empty()) { // If no jobs in service for a given class
                    fel[i] = std::numeric_limits<double>::max();
                } else {
                    fel[i] = fastest_job_fel;
                    job_fel[i] = fastest_job_id;
                }
            }
        } else { // exponential distro can use the faster memoryless blocks
            auto ongoing_jobs = policy->get_ongoing_jobs();
            int pooled_i;
            for (int i = 0; i < nclasses; i++) {
                if (i < nclasses - 1) {
                    pooled_i = 0;
                } else {
                    pooled_i = 1;
                }

                /*if (fel[i + nclasses] <= simtime) { // only update arrival that is executed at the time
                    fel[i + nclasses] = arr_time_samplers[i]->sample() + simtime;
                }*/
               if (last_ev_arr) {
                    fel[i + nclasses] = arr_time_samplers[(last_arr*nclasses)+i]->sample() + simtime;
                }

                // std::cout << ongoing_jobs[i].size() << std::endl;
                for (long int job_id : ongoing_jobs[i]) {
                    double sampled;
                    if (this->w == -3) {
                        sampled = holdTime[job_id];
                        policy->insert_completion(this->sizes[i], sampled + simtime, job_id);
                    } else if (this->w == -13) {
                        sampled = holdTime[job_id];
                        policy->insert_completion(this->sizes[i], holdTimeDeclared[job_id] + simtime, job_id);
                    } else {
                        sampled = ser_time_samplers[i]->sample();
                    }
                    jobs_inservice[i][job_id] = sampled + simtime;
                    // rawWaitingTime[i].push_back();
                    waitTime[job_id] = simtime - arrTime[job_id];
                    holdTime[job_id] = sampled;
                    // arrTime.erase(job_id); //update waitingTime
                    if (jobs_inservice[i][job_id] < fel[i]) {
                        fel[i] = jobs_inservice[i][job_id];
                        job_fel[i] = job_id;
                    }
                }

                if (jobs_inservice[i].empty()) { // If no jobs in service for a given class
                    fel[i] = std::numeric_limits<double>::max();
                } else if (fel[i] <= simtime) {
                    fel[i] = std::numeric_limits<double>::max();
                    for (auto& job : jobs_inservice[i]) {
                        if (job.second < fel[i]) {
                            fel[i] = job.second;
                            job_fel[i] = job.first;
                        }
                    }
                }
            }
        }
    }

    void collect_statistics(int pos) {

        if (pos < nclasses)
            completion[pos]++;

        double delta = fel[pos] - simtime;
        int jobs_tot = 0;
        for (int i = 0; i < nclasses; i++) {
            int state_buf = policy->get_state_buf()[i];
            int state_ser = policy->get_state_ser()[i];
            occupancy_buf[i] += state_buf * delta;
            occupancy_ser[i] += state_ser * delta;
            jobs_tot += state_buf + state_ser;
        }
        if (jobs_tot == 0) {
            idle_period += delta;
        }
        unsigned int occ = 0;
        for (int i = 0; i < nclasses; i++) {
            occ += policy->get_state_ser()[i] * sizes[i];
        }
        waste += (n - occ) * delta;
        viol += policy->get_violations_counter() * delta;
        rep_free_servers_distro[policy->get_free_ser()] += delta;

        windowSize.push_back(policy->get_window_size() * delta);
    }
};

#endif // SIMULATOR_H
