import cProfile
import re
import sys
import numpy

root_path = '/Users/jryan/Documents/as_binder'
sys.path.insert(0, root_path)

from ss.mockagent import MockAgent
from ss.mocksampler import MockSampler

class UniformSampler(MockSampler):
    def _generate_samples(self, fan_in):
        return self.r.uniform(0, 2 * self.sampling_target, fan_in + 1)

sr = numpy.random.RandomState(987654321)
ir = numpy.random.RandomState(123456789)
sampler = UniformSampler(sr, 10)

def test_fan_in():
    for j in range(0, 10):
        ms = MockAgent(ir, sampler=sampler, reservoir_size=1000)
        
        for i in range(0, 10):
            ms.montecarlo_simulate(i+1, 1000)

cProfile.run('test_fan_in()', sort='tottime')