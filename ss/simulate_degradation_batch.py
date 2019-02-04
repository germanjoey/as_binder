import os
import os.path
import re
import sys
import glob
import json
import numpy
import random

root_path = '/Users/jryan/Documents/as_binder'
sys.path.insert(0, root_path)

from ss.mockagent import MockAgent
from ss.mocksampler import MockSampler


num_runs = 1440
num_agents = 1000
reservoir_size = 1000
sampling_target = 10
sampler_types = ['adaptive', 'expbackoff']

srx = re.compile(r'(\d+)\.json')
sources = set()
for filename in glob.glob("%s/astudy/sources/*.json" % root_path):
    name = srx.findall(filename)[0]
    sources.add(name)

#already_done_ids = [
#    '4320443', '2416051', '2679406', '3625202', '4120950', '2155562', '828063',
#    '4320445', '3441996', '2690611', '2690626', '2416056', '252075']

#sources = [x for x in sources if str(x) not in already_done_ids]

#sources = set(['2638951', '4132727', '828085', '2350895', '2638956'])
sources = set(['2066188', '4120950', '2679406', '2155560'])

class RealDataSampler(MockSampler):
    def __init__(self, name, sampler_type, sampling_target):
        self._name = name
        self.sampling_target = sampling_target
        self._sampler_type = sampler_type
        self._counter = -1
        self._counts = {}

        for i in range(0, 10):
            with open('%s/astudy/counts/%s/%s/%d.json' % (root_path, name, sampler_type, i)) as f:
                self._counts[i] = json.load(f)

        self.max_len = len(self._counts[0])

    @property
    def name(self):
        return 'Account ' + self._name + ' ' + self._sampler_type

    def reset(self):
        self._counter = -1

    def _generate_samples(self, fan_in):
        self._counter += 1

        return [
            self._counts[x][self._counter % self.max_len]
            for x in range(0, fan_in)
        ]

def tune_samplers(a, b):
    for fan_in in a._counts:
        a_mean = sum(a._counts[fan_in])
        b_mean = sum(b._counts[fan_in])

        d = abs(a_mean - b_mean)
        t = a if a_mean > b_mean else b

        for _ in range(d):
            i = int(random.random() * a.max_len)
            t._counts[fan_in][i] -= 1


def simulate_for_reservoir(out_filename, num_runs, num_agents, reservoir_size,
                           sampling_target, sampler):
    r = numpy.random.RandomState(1234567)
    seeds = [int(x) for x in r.uniform(1, 999999999, num_agents)]
    
    with open(out_filename, 'w') as outfile:
        print(sampler.name, file=sys.stderr)
        
        for agent_id in range(num_agents):
            ir = numpy.random.RandomState(seeds[agent_id])
            
            ms = MockAgent(
                ir, sampler=sampler,
                reservoir_size=reservoir_size)

            outfile.write("for agent with %d endpoints with mean/std length %.3f/%.3f:" % (
                ms.num_endpoints, ms.span_count_estimate, ms.span_count_variation))
            outfile.write("\n")

            for fan_in in range(10):
                result = ms.montecarlo_simulate(fan_in, num_runs)
                outfile.write(result)
                outfile.write("\n")
                sampler.reset()

            outfile.write("\n")
            if (agent_id % 10) == 9:
                print("For sampler %s, reservoir size %d, and target %d, done with run %d" % (
                    sampler.name, reservoir_size,
                    sampler.sampling_target, agent_id), file=sys.stderr)
                
        print("", file=sys.stderr)

for name in sources:

    samplers = {}
    for sampler_type in sampler_types:
        samplers[sampler_type] = RealDataSampler(name, sampler_type, sampling_target)

    tune_samplers(*samplers.values())

    for sampler_type in sampler_types:
        results_path = "%s/ss/data_results/%s" % (root_path, sampler_type)
        if not os.path.isdir(results_path):
            os.makedirs(results_path)

        out_filename = '%s/%s.txt' % (results_path, name)
        simulate_for_reservoir(
            out_filename, num_runs, num_agents, reservoir_size,
            sampling_target, samplers[sampler_type])

