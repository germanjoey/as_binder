from operator import attrgetter

class MockReservoir(object):
    def byPriority(self):
        return x.priority

    def __init__(self, reservoir_size, sampledTrue_count, raw_results):
        self.reservoir_size = reservoir_size
        self.sampledTrue_count = sampledTrue_count
        self.raw_results = raw_results

        sorted_executions = sorted(
            raw_results,
            key=attrgetter('priority'),
            reverse=True)

        self.reservoir = []
        reservoir_space_remaining = self.reservoir_size
        for execution_path in sorted_executions:
            reservoir_space_remaining -= execution_path.path_spans

            if reservoir_space_remaining == 0:
                break

            elif reservoir_space_remaining < 0:
                #execution_path.mark_partial(-reservoir_space_remaining)
                break
                
            self.reservoir.append(execution_path)

    def __repr__(self):
        total_spans_sent = sum([x.path_spans for x in self.reservoir])
        header = "**%s %s\n  " % (self.sampledTrue_count, total_spans_sent)
        return header + "\n  ".join([str(x) for x in self.reservoir])