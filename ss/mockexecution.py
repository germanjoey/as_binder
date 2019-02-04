"""
class MockExecution(object):
    def __init__(self, r, endpoint_index, completed, path_spans, priority):
        self.r = r

        self.endpoint_index = endpoint_index
        self.priority = priority
        self.completed = completed
        self.path_spans = path_spans
        self.partial = False

        if self.completed is False:
            self.path_spans = self.r.poisson(path_spans)

    def __repr__(self):
        return "%s %s %s %s %s" % (
            self.endpoint_index, self.priority,
            self.path_spans, self.partial, self.completed)

    def mark_partial(self, spans_not_fitting_in_reservoir):
        self.partial = True
        self.completed = False
        self.path_spans -= spans_not_fitting_in_reservoir
"""

from collections import namedtuple

MockExecution = namedtuple('MockExecution', ['endpoint_index', 'completed', 'path_spans', 'priority'])
