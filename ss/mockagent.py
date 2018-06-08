
import math
import numpy

from ss.mockendpoint import MockEndpoint
from ss.mockexecution import MockExecution
from ss.mockreservoir import MockReservoir

class MockAgent(object):
    def __init__(self, r, sampling_target=10, reservoir_size=1000, bundle_span_counts=False): # seed=1234567
        self.r = r
        #self.r = numpy.random.RandomState(seed)

        self.reservoir_size = reservoir_size
        self.sampling_target = sampling_target
        
        self.completion_threshold = 1.00

        self.num_endpoints = int(self.r.uniform(5, 11))
        self.weights = self.r.uniform(0, 1, self.num_endpoints)
        self.weights /= sum(self.weights)

        # for scipy: lognorm(s=1.22, loc=0, scale=14)
        if bundle_span_counts is False:
            expected_span_count = int(max(8, self.r.lognormal(math.log(14), 1.22)))
            span_sigma = math.sqrt(expected_span_count) * math.log(expected_span_count) / 2 
            path_span_counts = self.r.normal(expected_span_count, span_sigma, self.num_endpoints)

        else:
            path_span_counts = self.r.lognormal(math.log(14), 1.22, self.num_endpoints)

        self.path_span_counts = [max(8, int(x)) for x in numpy.rint(path_span_counts)]
        self.span_count_estimate = numpy.mean(self.path_span_counts)
        self.span_count_variation = numpy.std(self.path_span_counts, ddof=1)

        self.endpoint_paths = [
            MockEndpoint(self.r, self.path_span_counts[i], self.weights[i])
                for i in range(self.num_endpoints)]

        self.cum_weights = numpy.cumsum(self.weights)

    def __repr__(self):
        return "\n\n".join([
            str(x) for x in sorted(
                self.endpoint_paths,
                key=lambda x: x.weight,
                reverse=True)])
    
    def montecarlo_simulate(self, run_index, num_harvests):
        results = [
            self.simulate_harvest(run_index)
                for i in range(0, num_harvests)]

        percent_traced = []
        choice_hist = numpy.zeros(self.num_endpoints)
        for result in results:
            complete_trace_count = 0

            for execution in result.reservoir:
                if execution.completed:
                    choice_hist[execution.endpoint_index] += 1
                    complete_trace_count += 1

            percent_traced.append(complete_trace_count / result.total_sampledTrue)

        s = sum(choice_hist)
        if s > 0:
            choice_hist /= s
        error_hist = (choice_hist - self.weights) ** 2

        header = "  %d, %.3f/%.3f, %.3E" % (
            run_index+1, numpy.mean(percent_traced), numpy.std(percent_traced), sum(error_hist))
        
        return header

    def simulate_harvest(self, fan_in):
        total_sampledTrue = sum([
            max(1, int(x)) for x in numpy.rint(
                self.r.normal(
                    self.sampling_target,
                    math.log(max(2, self.sampling_target)),
                    fan_in + 1))])

        try:
            endpoint_path_choices = self.r.uniform(0, 1, total_sampledTrue)
            priorities = self.r.uniform(0, 1, total_sampledTrue)
            completion_chance = self.r.uniform(0, 1, total_sampledTrue)
        except:
            import pdb
            pdb.set_trace()
            raise

        executions = []
        for i in range(0, total_sampledTrue):
            choice = endpoint_path_choices[i]
            priority = priorities[i]

            chosen_index = sum(choice > self.cum_weights)
            path = self.endpoint_paths[chosen_index]
            #is_completed = completion_chance[i] < self.completion_threshold
            is_completed = True

            e = MockExecution(
                self.r, chosen_index, is_completed,
                path.total_spans, priority)

            executions.append(e)

        return MockReservoir(self.reservoir_size, total_sampledTrue, executions)