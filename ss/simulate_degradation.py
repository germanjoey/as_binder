
import sys
import numpy
from ss.mockagent import MockAgent

r = numpy.random.RandomState(1234567)
num_runs = 1000
num_agents = 100

def simulate_for_reservoir(num_runs, num_agents, reservoir_size, sampling_target):
    out_filename = 'ss/degradation_results_%d_%d.txt' % (reservoir_size, sampling_target)

    with open(out_filename, 'w') as outfile:
        for agent_id in range(num_agents):
            ms = MockAgent(r, sampling_target=sampling_target, reservoir_size=reservoir_size)

            outfile.write("for agent with %d endpoints with mean/std length %.3f/%.3f:" % (
                ms.num_endpoints, ms.span_count_estimate, ms.span_count_variation))
            outfile.write("\n")

            for i in range(10):
                result = ms.montecarlo_simulate(i, num_runs)
                outfile.write(result)
                outfile.write("\n")

            outfile.write("\n")
            if (agent_id % 10) == 0:
                print("For reservoir size %d and target %d, done with run %d" % (
                    reservoir_size, sampling_target, agent_id), file=sys.stderr)
                
        print("", file=sys.stderr)
                

simulate_for_reservoir(num_runs, num_agents, 100, 1)
simulate_for_reservoir(num_runs, num_agents, 100, 10)
simulate_for_reservoir(num_runs, num_agents, 1000, 10)