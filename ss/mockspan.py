
import re

class MockSpan(object):
    def __init__(self, gvid, name, parent):
        self.gvid = str(gvid)
        self.name = name
        self.node_type = re.sub(r'\d', '' , name)
        self.parent = parent

        self.children = []
        self.mark_color = None
        self.times_seen = 0
        self.long_generic = False

        self.importance_score = 0
        if (self.node_type in ['root', 'dbcall', 'external']) or (self.long_generic):
            self.importance_score = 1
        
        if parent is not None:
            self.parent.add_child(self)

    @property
    def is_important(self):
        return self.importance_score == 1

    @property
    def is_unimportant(self):
        if ((self.mark_color == 'Red')
            or ((self.node_type == 'node')
                and (len(self.children) == 0)
                and (self.long_generic is False))):

            self.importance_score = 0
            return True

        return False

    def reset_seen_count(self):
        self.times_seen = 0
        
    def add_child(self, child):
        self.children.append(child)
        
    def count_spans(self):
        return 1 + sum([c.count_spans() for c in self.children])
        
    def count_important_children(self):
        initial = int(self.importance_score == 1)
        return initial + sum([c.count_important_children() for c in self.children])

    def count_nonprunable_spans(self):
        initial = int(self.mark_color == 'Green')
        return initial + sum([c.count_nonprunable_spans() for c in self.children])
        
    def mark_prunable_spans(self):
        if self.mark_color is not None:
            return self.mark_color

        if len(self.children) == 0:
            self.mark_color = 'Green'
            return
    
        all_green = True
        for child in self.children:
            child.mark_prunable_spans()
            if child.mark_color != 'Green':
                all_green = False

        self.mark_color = 'Red' if all_green is True else 'Green'

    def mark_seen(self):
        self.times_seen += 1
        
    #############################################################

    span_colors = {
        'root': '#FF00FF',
        'external': '#FF0000',
        'dbcall': '#00FF00',
        'call': '#666666',
        'node': '#000000',
        'Green': '#ceffe7',
        'Red': '#ffd6ce'
    }

    @property
    def fontcolor(self):
        return MockSpan.span_colors[self.node_type]

    @property
    def fillcolor(self):
        if self.mark_color is None:
            return '#ffffff'
        return MockSpan.span_colors[self.mark_color]

    def display_span(self, displayed_graph, show_importance):
        ic = ''
        if show_importance:
            ic = ' / %.3f' % self.importance_score
        
        displayed_graph.node(self.gvid,
                             self.name + ic,
                             style='filled',
                             fillcolor=self.fillcolor,
                             fontcolor=self.fontcolor)

        if self.parent is not None:
            displayed_graph.edge(self.parent.gvid, self.gvid)

        for child in self.children:
            child.display_span(displayed_graph, show_importance)