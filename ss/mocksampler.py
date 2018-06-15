import numpy

class MockSampler(object):
    def __init__(self, r, sampling_target):
        self.r = r
        self.sampling_target = sampling_target

    @property
    def name(self):
        return self.__class__.__name__.replace('Sampler', '').lower()
        
    def generate_samples(self, fan_in):
        return max(1, sum([
            int(x) for x in numpy.rint(
            	self._generate_samples(fan_in))]))
        
    def _generate_samples(self, fan_in):
    	return [0]*fan_in