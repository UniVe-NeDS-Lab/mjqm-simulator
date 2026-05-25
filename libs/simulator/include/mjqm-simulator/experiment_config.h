//
// Created by Marco Ciotola on 25/05/26.
//

#pragma once
#include <memory>
#include <vector>

#include <mjqm-samplers/sampler.h>

struct SharedArrival {
    std::unique_ptr<DistributionSampler> sampler;
    std::vector<double> class_probs; // normalised, one per class, same order as conf.classes
};
