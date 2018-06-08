
import math
import re
import pprint

import numpy

class MockEndpoint(object):
    def __init__(self, r, desired_span_count, weight=0):
        super(MockEndpoint, self).__init__()
        
        self.r = r
        self.weight = weight
        self.displayed_graph = None
        self.dbratio = 0.7

        self.desired_span_count = desired_span_count
        self.desired_depth = self.sub_sample(self.desired_span_count)
        self.desired_external_count = max(1,
            self.sub_sample(self.desired_span_count) - 1)

        self.base_graph = self.make_base_graph(
            self.desired_span_count,
            self.desired_depth)
        
        self.assign_externals(self.desired_external_count)
        self.total_spans = (self.actual_external_count
                            + self.sum_base_graph_nodes(
                               self.base_graph, include_links=True))
        
        self.pp = None
        
    def __repr__(self):
        self.pp = self.pp or pprint.PrettyPrinter(indent=4)

        infostring = "%s // %s %s // %s" % (
            self.weight,
            self.desired_span_count, self.total_base_nodes,
            self.desired_depth,
        )

        external_string = "%s // %s (%s/%s)" % (
            self.desired_external_count, self.actual_external_count,
            self.iinfo['ce'], self.iinfo['cd']
        )

        pps = self.pp.pformat(self.expanded_graph)
        return "%s\n%s\n%s" % (infostring, external_string, pps)

    def sub_sample(self, mean):
        if mean < 3:
            return 2
        return int(max(2, self.r.normal(math.log(mean) + 1, 0.5)))

    def allocate_spans(self, total_spans_remaining):
        if total_spans_remaining < 2:
            return [max(1, total_spans_remaining)]

        num_chunks = self.sub_sample(total_spans_remaining)
        allocation = numpy.abs(self.r.normal(0, 1, num_chunks))

        return [int(x)
            for x in numpy.rint(
                total_spans_remaining * allocation / sum(allocation)
            )]

    def make_base_graph(self, total_spans, total_layers):
        return self._make_base_graph(
            total_spans - 1, total_layers, total_layers)

    def _make_base_graph(self, total_spans_remaining, total_layers,
                         layers_remaining):
        if layers_remaining == 1:
            return [total_spans_remaining]

        allocation = self.allocate_spans(total_spans_remaining)
        ma = float(max(allocation))

        bonus = max(0, (
            layers_remaining - (total_layers-1)/2) / float(total_layers))
        deepening_probability = [bonus + x/ma for x in allocation]

        graph = []
        for i in range(0, len(allocation)):
            is_deepened = self.r.uniform(0, 1) < deepening_probability[i]
            
            if (allocation[i] > 2) and is_deepened:
                graph.append(
                    self._make_base_graph(
                        allocation[i] - 1,
                        total_layers,
                        layers_remaining - 1
                    ))
            else:
                graph.append(allocation[i])

        return graph

    def sum_base_graph_nodes(self, graph, include_links=False):
        total = 0

        for node in graph:
            if type(node) == list:
                total += self.sum_base_graph_nodes(
                    node, include_links=include_links)
                if include_links:
                    total += 1
            else:
                total += node

        return total

    def expand_graph_nodes(self, graph):
        expanded_graph = []

        for node in graph:
            if type(node) == list:
                expanded_graph.append(self.expand_graph_nodes(node))
            else:
                expanded_graph += ['node'] * node

        return expanded_graph

    def assign_externals(self, num_externals):
        self.total_base_nodes = self.sum_base_graph_nodes(self.base_graph)
        self.expanded_graph = self.expand_graph_nodes(self.base_graph)

        self.actual_external_count = min(
            int(self.total_base_nodes/2), 2*num_externals)
        external_locs = self.r.uniform(0, 1, self.total_base_nodes)

        aec = self.actual_external_count
        external_locs = numpy.argpartition(external_locs, -aec)[-aec:]

        self.iinfo = {x:0 for x in ['ci', 'cd', 'ce', 'cn']}
        self._assign_externals(external_locs, self.expanded_graph)

    def _assign_externals(self, external_locs, expanded_graph):
        for i in range(0, len(expanded_graph)):
            if expanded_graph[i] == 'node':
                if self.iinfo['ci'] in external_locs:
                    if self.r.uniform(0, 1) < self.dbratio:
                        expanded_graph[i] = 'dbcall' + str(self.iinfo['cd'])
                        self.iinfo['cd'] += 1

                    else:
                        expanded_graph[i] = 'external' + str(self.iinfo['ce'])
                        self.iinfo['ce'] += 1

                else:
                    expanded_graph[i] = 'node' + str(self.iinfo['cn'])
                    self.iinfo['cn'] += 1

                self.iinfo['ci'] += 1

            else:
                self._assign_externals(external_locs, expanded_graph[i])