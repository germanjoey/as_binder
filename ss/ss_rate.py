from bqplot import LinearScale, OrdinalColorScale, ColorAxis, Axis, Lines, Scatter, Figure
from ipywidgets import HBox, VBox, SelectionSlider, jslink, jsdlink, Layout, IntText, Label

from ss.mockendpoint import MockEndpoint
from ss.mocktrace import MockTrace

import numpy

def plot_secondary_sort_results(
    r, length_options, fraction_spans_captured,
    max_harvests, trace_variations):

    ss_marks = {}
    cache = {}

    random_factor_names = ['None', 'Slight', 'Moderate', 'Full']
    random_factors = [0, 0.1, 0.5, 100]

    default_length = length_options[-1]
    default_rf_name = random_factor_names[1]
    default_random_factor = random_factors[1]

    ss_results = simulate_secondary_sorts(
        r, cache, default_length, fraction_spans_captured,
        trace_variations, max_harvests, default_random_factor)

    length_slider = SelectionSlider(
        options=length_options,
        value=default_length,
        description='Path Lengths'
    )

    rf_slider = SelectionSlider(
        options=random_factor_names,
        value=default_rf_name,
        description='Randomness'
    )

    calc_label = Label()

    def update_secondary_sorts(slider):
        length = length_slider.value
        rf_name = rf_slider.value
        rf = random_factors[random_factor_names.index(rf_name)]
        
        calc_label.value = "Calculating..."
        ss_results = simulate_secondary_sorts(
            r, cache, length, fraction_spans_captured,
            trace_variations, max_harvests, rf)

        for trace in ss_marks:
            ss_marks[trace].y = ss_results[trace]

        calc_label.value = ""

    length_slider.observe(update_secondary_sorts, names='value')
    rf_slider.observe(update_secondary_sorts, names='value')
    figure = generate_secondary_sort_figure(
        max_harvests, fraction_spans_captured, ss_results)

    for mark in figure.marks:
        ss_marks[mark.labels[0]] = mark

    display(
        VBox([
            HBox([length_slider, rf_slider]),
            HBox([calc_label], layout=Layout(margin='0 0 0 25%')),
            HBox([figure])
        ])
    )

def generate_secondary_sort_figure(ymax, xdata, trace_results):
    x_sc = LinearScale(min=0, max=1)
    y_sc = LinearScale(min=0, max=ymax)

    ax_x = Axis(label='Fraction of Spans Captured Per Harvest',
                 scale=x_sc, grid_lines='solid')

    ax_y = Axis(label='Average Number of Harvests to Obtain Trace',
                scale=y_sc, side='left', grid_lines='solid',
                orientation='vertical')

    ss_marks = {}
    marks = []
    traces = ['basic', 'relevant', 'full']
    colors = ['yellow', 'cyan', 'blue']
    details = list(zip(traces, colors))

    for detail in details:
        (trace, color) = detail

        mark = Lines(
            x=xdata,
            y=trace_results[trace],
            colors=[color],
            scales={'x': x_sc, 'y': y_sc},
            labels=[trace],
            enable_hover=True,
            display_legend=True)

        marks.append(mark)

    return Figure(marks=marks, axes=[ax_x, ax_y], title='Span Secondary Sorting')

def simulate_secondary_sorts(
    r, cache, length, fraction_spans_captured,
    trace_variations, max_harvests, rf):

    tag = '%s/%s/%s/%s/%s' % (length, fraction_spans_captured, trace_variations, max_harvests, rf)
    
    if tag in cache:
        return cache[tag]
    
    results = _simulate_secondary_sorts(
        r, length, fraction_spans_captured,
        trace_variations, max_harvests, rf)
    
    cache[tag] = results
    return results

def _simulate_secondary_sorts(
    r, length, fraction_spans_captured,
    trace_variations, max_harvests, rf):

    all_results = {}
    for f in fraction_spans_captured:
        all_results[f] = {
            'basic': [],
            'relevant': [],
            'full': []
        }
    
    for _ in range(0, trace_variations):
        mep = MockEndpoint(r, length)
        mept = MockTrace(r, mep)
        mept.calculate_importance()

        for f in fraction_spans_captured:
            run_results = mept.simulate_secondary_sort(max_harvests, f, rf)

            for key in run_results:
                all_results[f][key].append(run_results[key])

    rebuilt_results = {'basic': [], 'relevant': [], 'full': []}
    for f in all_results:
        for key in all_results[f]:
            rebuilt_results[key].append(numpy.mean(all_results[f][key]))

    return rebuilt_results