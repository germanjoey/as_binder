
import sys
import numpy

from ss.mockagent import MockAgent
from ss.mocksampler import MockSampler

num_runs = 1000
num_agents = 100

#param_sets = [(100, 1), (100, 10), (1000, 10)]
param_sets = [(1000, 10)]

class UniformSampler(MockSampler):
    def _generate_samples(self, fan_in):
        return self.r.uniform(0, 2 * self.sampling_target, fan_in + 1)
        
class NormalSampler(MockSampler):
    def _generate_samples(self, fan_in):
        sigma = numpy.log(max(2, self.sampling_target))
        return self.r.normal(self.sampling_target, sigma, fan_in + 1)
        
def simulate_for_reservoir(num_runs, num_agents, reservoir_size,
                           sampling_target, sampler_class):
    
    r = numpy.random.RandomState(1234567)
    seeds = [int(x) for x in r.uniform(1, 999999999, num_agents)]
    sampler = sampler_class(r, sampling_target)
    
    out_filename = 'ss/degradation_results_%s_%d_%d.txt' % (
        sampler.name, reservoir_size, sampler.sampling_target)
    
    with open(out_filename, 'w') as outfile:
        #print(sampler.name, file=sys.stderr)
        
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

            outfile.write("\n")
            if (agent_id % 10) == 9:
                print("For sampler %s, reservoir size %d, and target %d, done with run %d" % (
                    sampler.name, reservoir_size,
                    sampler.sampling_target, agent_id), file=sys.stderr)
                
        print("", file=sys.stderr)

for sampler_class in [UniformSampler, NormalSampler]:
    for params in param_sets:
        simulate_for_reservoir(num_runs, num_agents, params[0], params[1], sampler_class)

        