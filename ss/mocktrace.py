
import pprint
import functools
import numpy

from ss.mockspan import MockSpan

import os
os.environ["PATH"] += os.pathsep + '/usr/local/Cellar/graphviz/2.40.1/bin/'

from graphviz import Digraph
from IPython.display import SVG

class MockTrace(object):
    important_types = ['root', 'external', 'dbcall', 'long_generics']
    
    def __init__(self, r, endpoint):
        self.r = r
        self.expanded_graph = endpoint.expanded_graph

        self.spans_by_name = {
            'root': MockSpan(0, 'root', None)
        }

        self.spans_by_type = {
            'root': set(['root']),
            'node': set(),
            'call': set(),
            'external': set(),
            'dbcall': set(),
            'long_generics': set(),
            'relevant': set()
        }

        self.gvid = 1
        self.fcount = 0
        self._convert_expanded_graph(self.spans_by_name['root'], self.expanded_graph)
        
        self.spans_by_category = {
            'unimportant': set(),
            'relevant': set(),
            'important': functools.reduce(
                lambda x, y: x | y, [
                self.spans_by_type[z] for z in MockTrace.important_types
            ])
        }

        self.pp = None
        self.displayed_graph = None
        
    def _convert_expanded_graph(self, current_parent, expanded_graph):
        for i in range(0, len(expanded_graph)):
            span = expanded_graph[i]
            name = span
            if type(span) != str:
                name = 'call' + str(self.fcount)
                self.fcount += 1

            s = MockSpan(self.gvid, name, current_parent)
            self.spans_by_name[name] = s
            self.spans_by_type[s.node_type].add(name)
            if s.long_generic:
                self.spans_by_type['long_generics'].add(name)

            self.gvid += 1

            if type(span) != str:
                self._convert_expanded_graph(self.spans_by_name[name], span)
        
    def count_spans(self):
        return self.spans_by_name['root'].count_spans()
    
    def count_nonprunable_spans(self):
        return self.spans_by_name['root'].count_nonprunable_spans()

    def mark_prunable_spans(self):
        self.spans_by_name['root'].mark_prunable_spans()
        self.spans_by_name['root'].mark_color = 'Green'
        
    #############################################################
    #   
    # first, assign 1s:
    #   dbs and externals get a 1
    #   "long segments" get a 1
    #   root gets a 1
    # 
    # next, assign 0s:
    #   non-long, non-db/ext leaves get 0
    #
    # next, count total spans, and then subtract off all the 1s so far
    # then count spans without a number so far
    # remaining spans will get an avg score of (remainders)/(total - 1s)
    # split that avg into 3 parts:
    #    a. 1/3 gifted directly
    #    b. 2/3 distributed based on which spans have the most '1s' children
    #

    def calculate_importance(self):
        self.mark_prunable_spans()

        total = self.spans_by_name['root'].count_spans()
        total_1s = len(self.spans_by_category['important'])

        total_0s = 0
        for span in self.spans_by_name.values():
            if span.is_unimportant:
                self.spans_by_category['unimportant'].add(span.name)
                total_0s += 1

        total_unassigned = total - total_1s - total_0s
        total_to_assign = float(total_unassigned / 2)
        total_to_distribute = (2.0/3.0) * total_to_assign
        
        if total_unassigned == 0:
            return
        
        baseline = (1.0/3.0) * total_to_assign / total_unassigned

        cic = 0 # cumulative_important_children
        weight_index = {}
        for name in self.spans_by_name:
            span = self.spans_by_name[name]
            if span.is_unimportant or span.is_important:
                continue

            ic = span.count_important_children()
            cic += ic
            weight_index[name] = ic

        sorted_order = sorted(
            weight_index.keys(),
            key=lambda x: weight_index[x],
            reverse=True)

        for name in sorted_order:
            self.spans_by_category['relevant'].add(name)
            span = self.spans_by_name[name]

            if cic > 0:
                fraction_share = weight_index[name] / cic
                weight_share = min(1 - baseline, fraction_share * total_to_distribute)

                cic -= weight_index[name]
                total_to_distribute -= weight_share
                span.importance_score = weight_share + baseline

    def display_graph(self, display_raw=False, show_importance=False):
        if display_raw:
            print("RAW FORM:\n")
            self.pp = self.pp or pprint.PrettyPrinter(indent=4)
            self.pp.pprint(self.expanded_graph)
        
        self.displayed_graph = Digraph()
        self.displayed_graph.attr(rankdir='LR', scale='0.5')

        self.spans_by_name['root'].display_span(self.displayed_graph, show_importance)
        display(SVG(self.displayed_graph.pipe(format='svg')))
        
    #############################################################
    
    def reset_seen_counts(self):
        for name in self.spans_by_name:
            self.spans_by_name[name].reset_seen_count()
    
    def simulate_secondary_sort(self, harvests, fraction_captured, random_factor):
        self.reset_seen_counts()
        
        finish_times = {}
        traces = {
            'full': set(self.spans_by_name.keys()),
            'basic': set(self.spans_by_category['important'])
        }
        traces['relevant'] = traces['basic'] | set(self.spans_by_category['relevant'])
        
        for i in range(0, harvests):
            if len(finish_times) == 3:
                return finish_times

            seen = self.simulate_harvest_clipping(fraction_captured, random_factor)

            for trace in traces:
                if trace in finish_times:
                    continue

                traces[trace] -= seen
                if len(traces[trace]) == 0:
                    finish_times[trace] = i

        for trace in traces:
            if trace not in finish_times:
                finish_times[trace] = harvests + 1

        return finish_times

    def simulate_harvest_clipping(self, fraction_captured, random_factor):
        sorted_spans = self.sort_spans_for_clipping(random_factor)
        num_captured = int(numpy.rint(fraction_captured * self.count_spans()))

        spans_captured = sorted_spans[0:num_captured]
        for name in spans_captured:
            self.spans_by_name[name].mark_seen()

        return set(spans_captured)

    def sort_spans_for_clipping(self, random_factor):
        ordered_spans = [
            (name, 1 + random_factor * self.r.uniform(0, 1))
                for name in self.spans_by_category['important']]

        for category in ['relevant', 'unimportant']:
            for name in self.spans_by_category[category]:
                span = self.spans_by_name[name]
                score = span.importance_score + random_factor * self.r.uniform(0, 1)
                ordered_spans.append((name, score))

        sorted_spans = sorted(ordered_spans, key=lambda x: x[1], reverse=True)
        return [y[0] for y in sorted_spans]