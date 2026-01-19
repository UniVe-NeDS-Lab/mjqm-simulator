//
// Created by Marco Ciotola on 23/01/25.
//

#ifndef EXPERIMENT_STATS_H
#define EXPERIMENT_STATS_H

#include <functional>
#include <iostream>
#include <ostream>
#include <string>
#include <utility>
#include <variant>
#include <vector>

#include <mjqm-math/confidence_intervals.h>

typedef std::variant<Confidence_inter, bool, double, long, std::string> VariantStat;

class Stat {
private:
    std::string prefix;

public:
    const std::string name;
    const bool has_confidence_interval;
    VariantStat value;
    bool visible = true;

    Stat(std::string name, bool has_confidence_interval) :
        name{std::move(name)}, has_confidence_interval{has_confidence_interval} {}
    virtual ~Stat() = default;

    void prefix_with(std::string prefix) { this->prefix = std::move(prefix); }
    void add_headers(std::vector<std::string>& headers) const;
    virtual void finalise() {}
    VariantStat operator+(Stat const& that) const;
    virtual Stat& operator=(VariantStat const& value);
    virtual void clear() { value = "N/A"; }
};
std::ostream& operator<<(std::ostream& os, const Stat& m);

class CollectedStat : public Stat {
private:
    std::vector<double> repetition_values;

public:
    CollectedStat(std::string name, bool has_confidence_interval) : Stat(std::move(name), has_confidence_interval) {}
    ~CollectedStat() override = default;

    void collect(double value) {
        if (Stat::visible) {
            repetition_values.push_back(value);
        }
    }
    void finalise() override {
        if (!Stat::visible || repetition_values.empty()) {
            value = Confidence_inter{0, 0, 0};
        } else {
            value = compute_interval_student(repetition_values, 0.05);
        }
    }
    CollectedStat& operator=(VariantStat const& value) override {
        Stat::value = value;
        return *this;
    }
    void clear() override {
        repetition_values.clear();
        Stat::clear();
    }
};

class ClassStats {
public:
    const std::string name;
    CollectedStat occupancy_buf{"Queue", true};
    CollectedStat occupancy_ser{"Service", true};
    CollectedStat occupancy_system{"System", true};
    CollectedStat wait_time{"Waiting", true};
    CollectedStat wait_time_var{"Waiting Variance", true};
    CollectedStat throughput{"Throughput", true};
    CollectedStat resp_time{"RespTime", true};
    CollectedStat resp_time_var{"RespTime Variance", true};
    CollectedStat preemption_avg{"Preemption", true};
    CollectedStat seq_avg_len{"Sequence Length", true};
    CollectedStat seq_avg_dur{"Sequence Duration", true};
    CollectedStat seq_amount{"Sequence Amount", true};
    Stat warnings{"Stability Check", false};
    Stat lambda{"lambda", false};

    explicit ClassStats(const std::string& name) : name{name} {
        edit_stats([name](Stat& s) { s.prefix_with("T" + name); });
    }

    // visitors
    void edit_stats(const std::function<void(Stat&)>& editor) {
        editor(occupancy_buf);
        editor(occupancy_ser);
        editor(occupancy_system);
        editor(wait_time);
        editor(wait_time_var);
        editor(throughput);
        editor(resp_time);
        editor(resp_time_var);
        editor(preemption_avg);
        editor(seq_avg_len);
        editor(seq_avg_dur);
        editor(seq_amount);
        editor(warnings);
        editor(lambda);
    }

    void visit_stats(const std::function<void(const Stat&)>& visitor) const {
        visitor(occupancy_buf);
        visitor(occupancy_ser);
        visitor(occupancy_system);
        visitor(wait_time);
        visitor(wait_time_var);
        visitor(throughput);
        visitor(resp_time);
        visitor(resp_time_var);
        visitor(preemption_avg);
        visitor(seq_avg_len);
        visitor(seq_avg_dur);
        visitor(seq_amount);
        visitor(warnings);
        visitor(lambda);
    }

    // outputs
    void add_headers(std::vector<std::string>& headers) const;
    friend std::ostream& operator<<(std::ostream& os, ClassStats const& m);

    // visibility setters
    void set_computed_columns_visibility(bool visible);
    void set_column_visibility(const std::string& column, bool visible);
};

class ExperimentStats {
    std::vector<Stat> pivot_values{};
    std::vector<Stat> custom_values{};

public:
    std::vector<ClassStats> class_stats{};
    CollectedStat wasted{"Wasted Servers", true};
    CollectedStat utilisation{"Utilisation", true};
    CollectedStat occupancy_tot{"Queue Total", true};
    CollectedStat wait_tot{"WaitTime Total", true};
    CollectedStat wait_var_tot{"WaitTime Variance", true};
    CollectedStat resp_tot{"RespTime Total", true};
    CollectedStat resp_var_tot{"RespTime Variance", true};
    CollectedStat window_size{"Window Size", true};
    CollectedStat violations{"FIFO Violations", true};
    CollectedStat timings_tot{"Run Duration", true};
    CollectedStat phase_two_dur{"Phase Two Duration", true};
    CollectedStat phase_three_dur{"Phase Three Duration", true};
    CollectedStat idle_period_prob{"Idle Period Probability", true};
    Stat warnings{"Stability Check", false};
    Stat lambda{"lambda", false};

    // visitors
    void edit_computed_stats(const std::function<void(Stat&)>& editor) {
        editor(wasted);
        editor(utilisation);
        editor(occupancy_tot);
        editor(wait_tot);
        editor(wait_var_tot);
        editor(resp_tot);
        editor(resp_var_tot);
        editor(window_size);
        editor(violations);
        editor(timings_tot);
        editor(phase_two_dur);
        editor(phase_three_dur);
        editor(idle_period_prob);
        editor(warnings);
        editor(lambda);
        for (auto& cs : class_stats) {
            cs.edit_stats(editor);
        }
    }

    void visit_computed_stats(const std::function<void(const Stat&)>& visitor) const {
        visitor(wasted);
        visitor(utilisation);
        visitor(occupancy_tot);
        visitor(wait_tot);
        visitor(wait_var_tot);
        visitor(resp_tot);
        visitor(resp_var_tot);
        visitor(window_size);
        visitor(violations);
        visitor(timings_tot);
        visitor(phase_two_dur);
        visitor(phase_three_dur);
        visitor(idle_period_prob);
        visitor(warnings);
        visitor(lambda);
        for (auto& cs : class_stats) {
            cs.visit_stats(visitor);
        }
    }
    void edit_all_stats(const std::function<void(Stat&)>& editor);
    void visit_all_stats(const std::function<void(const Stat&)>& visitor) const;

    void collect_class_stat(const std::function<CollectedStat&(ClassStats&)>& selector,
                            const std::vector<double>& values) {
        for (size_t i = 0; i < class_stats.size(); ++i) {
            selector(class_stats[i]).collect(values[i]);
        }
    }
    ClassStats& for_class(const size_t& i) { return std::ref(class_stats[i]); }

    // outputs
    friend std::ostream& operator<<(std::ostream& os, ExperimentStats const& m);
    void add_headers(std::vector<std::string>& headers, std::vector<unsigned int>& sizes) const;
    void add_headers(std::vector<std::string>& headers) const;
    std::vector<std::string> get_headers() const;

    // add elements
    ClassStats& add_class(const std::string& name) { return std::ref(class_stats.emplace_back(name)); }

    bool add_pivot_column(const std::string& name, const VariantStat& value) {
        pivot_values.emplace_back(name, false);
        pivot_values.back() = value;
        return true;
    }

    bool add_custom_column(const std::string& name, const VariantStat& value) {
        custom_values.emplace_back(name, false);
        custom_values.back() = value;
        return true;
    }

    // visibility setters
    void set_computed_columns_visibility(bool visible);

    void set_column_visibility(const std::string& column) {
        if (column.starts_with("-"))
            return set_column_visibility(column.substr(1), false);
        return set_column_visibility(column, true);
    }
    void set_column_visibility(const std::string& column, bool visible);

    void set_class_column_visibility(const std::string& column, const std::string& cls = "*") {
        if (column.starts_with("-"))
            return set_class_column_visibility(column.substr(1), false, cls);
        return set_class_column_visibility(column, true, cls);
    }
    void set_class_column_visibility(const std::string& column, bool visible, const std::string& cls = "*");
};

#endif // EXPERIMENT_STATS_H
